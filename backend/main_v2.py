from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from contextlib import asynccontextmanager
import logging
import json
from pathlib import Path
from typing import List, Optional, Union
from pydantic import BaseModel

from services.model_registry import model_registry
from services.domain_validator import DomainValidator
from agent.orchestrator import AgentOrchestrator
import os
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── MongoDB ────────────────────────────────────────────────────────────────────
mongo_storage = None
if os.getenv("USE_MONGODB_STORAGE", "true").lower() == "true":
    try:
        from services.mongodb_storage import MongoDBStorage
        mongo_storage = MongoDBStorage(
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
            os.getenv("MONGODB_DB", "qn_evaluator")
        )
        logger.info(f"MongoDB storage initialized: {os.getenv('MONGODB_DB', 'qn_evaluator')}")
    except Exception as e:
        logger.warning(f"MongoDB storage failed: {e}")

# ── S3 (optional) ──────────────────────────────────────────────────────────────
storage_service = None
if os.getenv('AWS_ACCESS_KEY_ID'):
    try:
        from services.storage_service import StorageService
        storage_service = StorageService()
        logger.info("S3 storage service initialized")
    except ImportError as e:
        logger.warning(f"S3 storage not available: {e}")

# ── Global orchestrator ────────────────────────────────────────────────────────
orchestrator: AgentOrchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global orchestrator
    logger.info("Starting up Question Intelligence System...")
    try:
        if not mongo_storage:
            raise RuntimeError("MongoDB storage is required. Check MongoDB connection.")

        model_registry.load_all_models()

        orchestrator = AgentOrchestrator(mongo_storage)

        from services.mongodb_history_repository import MongoDBHistoryRepository
        orchestrator.init_history(MongoDBHistoryRepository(
            os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
            os.getenv("MONGODB_DB", "qn_evaluator")
        ))

        logger.info("System startup completed successfully (MongoDB-only mode)")
    except Exception as e:
        logger.error(f"Failed during startup: {e}")
        raise
    yield
    logger.info("Shutting down Question Intelligence System...")


app = FastAPI(
    title="Question Intelligence System",
    description="Domain-based question evaluation with Bloom taxonomy",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Request models ─────────────────────────────────────────────────────────────

class CreateDomainRequest(BaseModel):
    user_id: str
    domain_name: str

class EvaluateRequest(BaseModel):
    user_id: str
    domain_name: str
    question: str

class ReportRequest(BaseModel):
    domain_name: str
    results: list
    format: str
    type: str = "mapping"
    meta: Union[dict, None] = None

    model_config = {"arbitrary_types_allowed": True}

# ── Helpers ────────────────────────────────────────────────────────────────────

def calculate_difficulty(bloom_level: str) -> float:
    return {"BT1": 0.15, "BT2": 0.30, "BT3": 0.50, "BT4": 0.70, "BT5": 0.85, "BT6": 1.00}.get(bloom_level, 0.5)

def calculate_strength(question: str) -> float:
    q_lower = question.lower()
    words = question.split()
    score = 0.5
    if len(words) < 5:
        score -= 0.3
    if any(q_lower.startswith(s) for s in ['what is', 'define', 'list', 'name', 'state']):
        score -= 0.25
    if any(v in q_lower for v in ['compare', 'differentiate', 'analyze', 'evaluate', 'justify', 'explain', 'discuss', 'examine', 'assess', 'critique']):
        score += 0.25
    if any(t in q_lower for t in ['algorithm', 'architecture', 'implement', 'design', 'optimize', 'structure', 'protocol', 'mechanism', 'framework', 'paradigm']):
        score += 0.15
    if 8 <= len(words) <= 30:
        score += 0.15
    elif len(words) > 30:
        score += 0.05
    if any(i in q_lower for i in [' and ', ' or ', ' with ', ' using ']):
        score += 0.10
    return max(0.0, min(1.0, score))

# ── Health ─────────────────────────────────────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "ok", "message": "Question Intelligence System v2.0 is running"}

# ── Domain ─────────────────────────────────────────────────────────────────────

@app.post("/domains/create")
async def create_domain(request: CreateDomainRequest):
    try:
        orchestrator.create_domain(request.user_id, request.domain_name.strip())
        return {"message": "Domain created successfully", "user_id": request.user_id, "domain_name": request.domain_name.strip()}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to create domain", "details": str(e)})

@app.get("/domains/{user_id}")
async def list_domains(user_id: str):
    try:
        return {"domains": orchestrator.list_domains(user_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to list domains", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}")
async def delete_domain(user_id: str, domain_name: str):
    try:
        orchestrator.delete_domain(user_id, domain_name)
        return {"message": "Domain deleted successfully", "user_id": user_id, "domain_name": domain_name}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete domain", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/status")
async def get_domain_status(user_id: str, domain_name: str):
    try:
        return orchestrator.get_domain_status(user_id, domain_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to get status", "details": str(e)})

# ── Syllabus ───────────────────────────────────────────────────────────────────

@app.post("/domains/{user_id}/{domain_name}/syllabus")
async def upload_syllabus(user_id: str, domain_name: str, file: UploadFile = File(...)):
    try:
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail={"error": "Only PDF or TXT files allowed"})
        file_bytes = await file.read()
        syllabus, index_rebuilt = orchestrator.upload_syllabus(user_id, domain_name, file_bytes, file.filename)
        return {
            "message": "Syllabus uploaded and index rebuilt successfully" if index_rebuilt else "Syllabus uploaded successfully",
            "course_name": syllabus["course_name"],
            "units_count": len(syllabus["units"]),
            "co_count": len(syllabus["course_outcomes"]),
            "index_rebuilt": index_rebuilt
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to upload syllabus", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}/syllabus")
async def delete_syllabus(user_id: str, domain_name: str):
    try:
        orchestrator.delete_syllabus(user_id, domain_name)
        return {"message": "Syllabus deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete syllabus", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/syllabus/view")
async def view_syllabus(user_id: str, domain_name: str):
    try:
        syllabus = orchestrator.view_syllabus(user_id, domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        return syllabus
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to view syllabus", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/files/syllabus")
async def download_syllabus_file(user_id: str, domain_name: str):
    try:
        file_bytes, filename = orchestrator.get_syllabus_file(user_id, domain_name)
        if file_bytes:
            return Response(content=file_bytes, media_type='application/octet-stream',
                            headers={"Content-Disposition": f"attachment; filename={filename}"})
        syllabus = orchestrator.view_syllabus(user_id, domain_name)
        if syllabus:
            return Response(content=json.dumps(syllabus, indent=2).encode('utf-8'),
                            media_type='application/json',
                            headers={"Content-Disposition": "attachment; filename=syllabus.json", "X-Fallback": "true"})
        raise HTTPException(status_code=404, detail={"error": "Syllabus file not found"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to download syllabus", "details": str(e)})

# ── Books ──────────────────────────────────────────────────────────────────────

@app.post("/domains/{user_id}/{domain_name}/books")
async def upload_books(user_id: str, domain_name: str, files: List[UploadFile] = File(...)):
    try:
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail={"error": "Only PDF files allowed"})

        temp_files = []
        for book in files:
            temp_path = Path(book.filename)
            temp_path.write_bytes(await book.read())
            temp_files.append(temp_path)

        success, chunks_count = orchestrator.upload_books(user_id, domain_name, temp_files)

        for f in temp_files:
            f.unlink(missing_ok=True)

        if not success:
            raise HTTPException(status_code=400, detail={"error": "Failed to build index"})

        return {"message": "Books uploaded and indexed successfully", "books_uploaded": len(files), "chunks_indexed": chunks_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to upload books", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}/books/{book_name}")
async def delete_book(user_id: str, domain_name: str, book_name: str):
    try:
        orchestrator.delete_book(user_id, domain_name, book_name)
        return {"message": "Book deleted and index rebuilt"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete book", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/files/books/{book_name}")
async def download_book_file(user_id: str, domain_name: str, book_name: str):
    try:
        book_path = Path("data") / user_id / domain_name / "books" / book_name
        if not book_path.exists():
            raise HTTPException(status_code=404, detail={"error": "Book not found"})
        return FileResponse(book_path, filename=book_name)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to download book", "details": str(e)})

# ── Index ──────────────────────────────────────────────────────────────────────

@app.post("/domains/{user_id}/{domain_name}/rebuild")
async def rebuild_index(user_id: str, domain_name: str):
    try:
        syllabus = orchestrator.view_syllabus(user_id, domain_name)
        if not syllabus:
            raise HTTPException(status_code=400, detail={"error": "Syllabus not found. Upload syllabus first."})
        if not orchestrator.list_books(user_id, domain_name):
            raise HTTPException(status_code=400, detail={"error": "No books found. Upload books first."})

        success, chunks_count = orchestrator.rebuild_index(user_id, domain_name)
        if not success:
            raise HTTPException(status_code=500, detail={"error": "Failed to rebuild index"})

        return {"message": "Index rebuilt and syllabus enriched successfully", "chunks_indexed": chunks_count}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to rebuild index", "details": str(e)})

# ── Evaluation ─────────────────────────────────────────────────────────────────

@app.post("/evaluate/preview")
async def evaluate_preview(request: EvaluateRequest):
    try:
        bloom_result = model_registry.predict_bloom(request.question)
        return {
            "bloom_level": bloom_result["bloom_level"],
            "classification_confidence": bloom_result["confidence"],
            "difficulty_score": calculate_difficulty(bloom_result["bloom_level"]),
            "strength_score": calculate_strength(request.question),
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Preview evaluation failed", "details": str(e)})

@app.post("/evaluate")
async def evaluate_question(request: EvaluateRequest):
    try:
        return orchestrator.evaluate_question(request.user_id, request.domain_name, request.question)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Evaluation failed", "details": str(e)})

@app.post("/evaluate/pdf")
async def evaluate_pdf(user_id: str = Form(...), domain_name: str = Form(...), file: UploadFile = File(...)):
    try:
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail={"error": "Only PDF files allowed"})

        pdf_bytes = await file.read()
        eval_id, total_questions, results = orchestrator.evaluate_pdf(user_id, domain_name, file.filename, pdf_bytes)
        return {"eval_id": eval_id, "total_questions": total_questions, "results": results}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "PDF evaluation failed", "details": str(e)})

# ── Report ─────────────────────────────────────────────────────────────────────

@app.post("/report/generate")
async def generate_report(request: ReportRequest):
    try:
        if request.format not in ("pdf", "docx"):
            raise HTTPException(status_code=400, detail={"error": "Invalid format. Use 'pdf' or 'docx'"})
        file_path = orchestrator.generate_report(request.domain_name, request.results, request.format, request.type, request.meta)
        media_type = "application/pdf" if request.format == "pdf" else "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        return FileResponse(file_path, media_type=media_type, filename=f"report_{request.domain_name}.{request.format}")
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Report generation failed", "details": str(e)})

# ── History ────────────────────────────────────────────────────────────────────

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    try:
        return orchestrator.get_history(user_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to get history", "details": str(e)})

@app.delete("/history/{user_id}/single/{question_id}")
async def delete_single_question(user_id: str, question_id: str):
    try:
        orchestrator.delete_single_question(user_id, question_id)
        return {"message": "Question deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete question", "details": str(e)})

@app.delete("/history/{user_id}/pdf/{eval_id}")
async def delete_pdf_evaluation(user_id: str, eval_id: str):
    try:
        orchestrator.delete_pdf_evaluation(user_id, eval_id)
        return {"message": "PDF evaluation deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to delete PDF evaluation", "details": str(e)})

@app.delete("/history/{user_id}/clear")
async def clear_all_history(user_id: str):
    try:
        orchestrator.clear_all_history(user_id)
        return {"message": "All history cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to clear history", "details": str(e)})

@app.get("/history/{user_id}/pdf/{eval_id}")
async def get_pdf_evaluation_results(user_id: str, eval_id: str):
    try:
        history = orchestrator.get_history(user_id)
        for ev in history.get("pdf_evaluations", []):
            if ev.get("id") == eval_id:
                return ev
        raise HTTPException(status_code=404, detail={"error": "Evaluation not found"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Failed to get evaluation", "details": str(e)})

# ── Metrics & Adaptive Generation ────────────────────────────────────────────

class MetricsRequest(BaseModel):
    user_id: str
    domain_name: str
    labeled_data: list

class AdaptiveRequest(BaseModel):
    user_id: str
    domain_name: str
    results: list

class BloomGenerateRequest(BaseModel):
    user_id: str
    domain_name: str
    target_bloom: str
    target_unit: str

class RegenerateRequest(BaseModel):
    user_id: str
    domain_name: str
    unit: str
    bloom: str
    co: Union[str, None] = None
    gap_message: str = ""

class ReplaceQuestionRequest(BaseModel):
    question_index: int
    new_question: str
    new_bloom: str
    new_co: Union[str, None] = None
    new_unit: Union[str, None] = None

@app.post("/metrics/evaluate")
async def evaluate_metrics(request: MetricsRequest):
    """Module 7: Run pipeline on labeled data and return accuracy metrics"""
    try:
        report = orchestrator.run_metrics(request.user_id, request.domain_name, request.labeled_data)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Metrics evaluation failed", "details": str(e)})

@app.post("/adaptive/generate")
async def adaptive_generate(request: AdaptiveRequest):
    """Module 8: Detect gaps and generate/guide questions"""
    try:
        result = orchestrator.generate_adaptive_questions(request.results, request.user_id, request.domain_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Adaptive generation failed", "details": str(e)})

@app.post("/adaptive/generate_bloom")
async def generate_bloom_question(request: BloomGenerateRequest):
    """Generate a single higher-order question for a Bloom gap on demand"""
    try:
        from services.adaptive_question_service import AdaptiveQuestionService
        from services.domain_manager import DomainManager
        dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
        syllabus = dm.load_syllabus(request.user_id, request.domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        index, metadata = dm.load_index(request.user_id, request.domain_name)
        svc = AdaptiveQuestionService()
        gap = {
            "gap_type": "bloom_gap", "target": request.target_bloom,
            "reason": f"Generate a {request.target_bloom} question for Unit {request.target_unit}",
            "target_bloom": request.target_bloom, "target_unit": request.target_unit,
        }
        questions = svc._generate_for_unit_gaps(
            [gap], syllabus, index, metadata,
            model_registry.get_bi_encoder(), model_registry.get_cross_encoder()
        )
        return {"question": questions[0]["question"] if questions else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/adaptive/regenerate")
async def regenerate_question(request: RegenerateRequest):
    """Regenerate a single suggested question"""
    try:
        from services.adaptive_question_service import AdaptiveQuestionService
        from services.domain_manager import DomainManager
        dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
        syllabus = dm.load_syllabus(request.user_id, request.domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        index, metadata = dm.load_index(request.user_id, request.domain_name)
        svc = AdaptiveQuestionService()
        gap = {
            "gap_type": "co_gap" if request.co else "unit_gap",
            "target": request.co or f"Unit {request.unit}",
            "reason": request.gap_message,
            "target_bloom": request.bloom,
            "target_unit": request.unit,
            "target_co": request.co,
        }
        fn = svc._generate_for_co_gaps if request.co else svc._generate_for_unit_gaps
        questions = fn(
            [gap], syllabus, index, metadata,
            model_registry.get_bi_encoder(), model_registry.get_cross_encoder()
        )
        return {"question": questions[0]["question"] if questions else None}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/adaptive/replace-question")
async def replace_question(request: ReplaceQuestionRequest):
    """Validate and confirm a question replacement — returns the replacement data for frontend to apply"""
    try:
        if not request.new_question or not request.new_question.strip():
            raise HTTPException(status_code=400, detail={"error": "new_question is required"})
        return {
            "status": "success",
            "question_index": request.question_index,
            "new_question":   request.new_question.strip(),
            "new_bloom":      request.new_bloom,
            "new_co":         request.new_co,
            "new_unit":       request.new_unit,
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── Paper Generation ─────────────────────────────────────────────────────────

class PartConfig(BaseModel):
    part: str
    marks_per_question: int
    question_count: int

class SlotSpec(BaseModel):
    q_no: int
    part: str
    marks: int
    unit: str
    unit_title: str
    topic: str
    bloom: str
    co: Optional[str] = None

class SlotPartConfig(BaseModel):
    part: str
    marks_per_question: int
    slots: list[SlotSpec]

class BuildSlotsRequest(BaseModel):
    user_id: str
    domain_name: str
    parts: list[PartConfig]

class GeneratePaperRequest(BaseModel):
    user_id: str
    domain_name: str
    parts: list[SlotPartConfig]

class RegenerateQuestionRequest(BaseModel):
    user_id: str
    domain_name: str
    slot: SlotSpec

@app.post("/generate/slots")
async def build_slots(request: BuildSlotsRequest):
    try:
        from services.paper_generator_service import PaperGeneratorService
        from services.domain_manager import DomainManager
        dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
        syllabus = dm.load_syllabus(request.user_id, request.domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        svc = PaperGeneratorService()
        return svc.build_slots(syllabus, [p.model_dump() for p in request.parts])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/generate/paper")
async def generate_paper(request: GeneratePaperRequest):
    try:
        from services.paper_generator_service import PaperGeneratorService
        from services.domain_manager import DomainManager
        dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
        syllabus = dm.load_syllabus(request.user_id, request.domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        svc = PaperGeneratorService()
        return svc.generate_paper(syllabus, [p.model_dump() for p in request.parts])
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.post("/generate/question")
async def regenerate_single_question(request: RegenerateQuestionRequest):
    try:
        from services.paper_generator_service import PaperGeneratorService
        from services.domain_manager import DomainManager
        dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
        syllabus = dm.load_syllabus(request.user_id, request.domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        svc = PaperGeneratorService()
        question = svc.regenerate_question(syllabus, request.slot.model_dump())
        return {"question": question}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

class ExportPaperRequest(BaseModel):
    paper: dict
    format: str
    user_id: Optional[str] = None
    domain_name: Optional[str] = None
    meta: Optional[dict] = None

@app.post("/generate/export")
async def export_paper(request: ExportPaperRequest):
    try:
        from services.paper_generator_service import PaperGeneratorService
        from services.domain_manager import DomainManager
        svc = PaperGeneratorService()
        fmt = request.format.lower()
        meta = dict(request.meta or {})

        # Auto-populate COs from syllabus if not provided
        if not meta.get("cos") and request.user_id and request.domain_name:
            try:
                dm = DomainManager("data", embedder=model_registry.get_bi_encoder(), mongo_storage=mongo_storage)
                syllabus = dm.load_syllabus(request.user_id, request.domain_name)
                if syllabus:
                    cos_dict = syllabus.get("course_outcomes", {})
                    meta["cos"] = [{"id": k, "text": v} for k, v in sorted(cos_dict.items())]
                    meta["co_map"] = {}  # identity — CO column prints the key as-is
                    if not meta.get("course_title"):
                        meta["course_title"] = syllabus.get("course_name", "")
            except Exception:
                pass

        name = (meta.get("exam_name") or request.paper.get('course_name', 'paper')).replace(' ', '_')
        if fmt == "pdf":
            data = svc.export_pdf(request.paper, meta)
            media_type = "application/pdf"
            filename = f"{name}.pdf"
        elif fmt == "docx":
            data = svc.export_docx(request.paper, meta)
            media_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            filename = f"{name}.docx"
        else:
            raise HTTPException(status_code=400, detail={"error": "format must be pdf or docx"})
        return Response(content=data, media_type=media_type,
                        headers={"Content-Disposition": f"attachment; filename={filename}"})
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── Paper History ─────────────────────────────────────────────────────────────

class SavePaperRequest(BaseModel):
    user_id: str
    domain_name: str
    paper: dict
    meta: dict  # exam_name, date, duration, co_map

@app.post("/generate/save")
async def save_paper(request: SavePaperRequest):
    try:
        from datetime import datetime
        doc = {
            "user_id": request.user_id,
            "domain_name": request.domain_name,
            "paper": request.paper,
            "meta": request.meta,
            "timestamp": datetime.utcnow().isoformat(),
            "exam_name": request.meta.get("exam_name", "Untitled"),
        }
        result = mongo_storage.db["generated_papers"].insert_one(doc)
        return {"id": str(result.inserted_id), "message": "Paper saved"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/generate/history/{user_id}")
async def get_paper_history(user_id: str):
    try:
        from bson import ObjectId
        docs = list(mongo_storage.db["generated_papers"].find({"user_id": user_id}, {"paper": 0}).sort("timestamp", -1))
        for d in docs:
            d["id"] = str(d.pop("_id"))
        return {"papers": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.get("/generate/history/{user_id}/{paper_id}")
async def get_saved_paper(user_id: str, paper_id: str):
    try:
        from bson import ObjectId
        doc = mongo_storage.db["generated_papers"].find_one({"_id": ObjectId(paper_id), "user_id": user_id})
        if not doc:
            raise HTTPException(status_code=404, detail={"error": "Paper not found"})
        doc["id"] = str(doc.pop("_id"))
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

@app.delete("/generate/history/{user_id}/{paper_id}")
async def delete_saved_paper(user_id: str, paper_id: str):
    try:
        from bson import ObjectId
        mongo_storage.db["generated_papers"].delete_one({"_id": ObjectId(paper_id), "user_id": user_id})
        return {"message": "Deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": str(e)})

# ── Storage/Backup ─────────────────────────────────────────────────────────────

@app.post("/storage/backup/{user_id}")
async def backup_user_data(user_id: str):
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured"})
    try:
        uploaded = storage_service.sync_user_data(user_id, direction='upload')
        return {"message": "User data backed up successfully", "user_id": user_id, "files_uploaded": len(uploaded)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Backup failed", "details": str(e)})

@app.post("/storage/restore/{user_id}")
async def restore_user_data(user_id: str):
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured"})
    try:
        downloaded = storage_service.sync_user_data(user_id, direction='download')
        return {"message": "User data restored successfully", "user_id": user_id, "files_downloaded": len(downloaded)}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Restore failed", "details": str(e)})

@app.post("/storage/backup/{user_id}/{domain_name}")
async def backup_domain(user_id: str, domain_name: str):
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured"})
    try:
        uploaded = storage_service.backup_domain(user_id, domain_name)
        return {"message": "Domain backed up successfully", "user_id": user_id, "domain_name": domain_name, "files_uploaded": len(uploaded)}
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Backup failed", "details": str(e)})

@app.post("/storage/restore/{user_id}/{domain_name}")
async def restore_domain(user_id: str, domain_name: str):
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured"})
    try:
        downloaded = storage_service.restore_domain(user_id, domain_name)
        return {"message": "Domain restored successfully", "user_id": user_id, "domain_name": domain_name, "files_downloaded": len(downloaded)}
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "Restore failed", "details": str(e)})


if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Question Intelligence System server...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
