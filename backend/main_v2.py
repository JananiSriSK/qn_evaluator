from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import shutil
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

from services.domain_manager import DomainManager
from services.evaluation_service import EvaluationService
from services.model_registry import model_registry
from services.domain_validator import DomainValidator
from services.pdf_parser import PDFQuestionParser
from services.report_generator import ReportGenerator
from services.history_service import HistoryService
from services.enrichment_service import EnrichmentService
import os
from dotenv import load_dotenv
import json

load_dotenv()

# Configure logging FIRST
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize MongoDB storage
mongo_storage = None
use_mongodb = os.getenv("USE_MONGODB_STORAGE", "true").lower() == "true"
if use_mongodb:
    try:
        from services.mongodb_storage import MongoDBStorage
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        mongo_db = os.getenv("MONGODB_DB", "qn_evaluator")
        mongo_storage = MongoDBStorage(mongo_uri, mongo_db)
        logger.info(f"MongoDB storage initialized: {mongo_db}")
    except Exception as e:
        logger.warning(f"MongoDB storage failed: {e}")
        logger.warning("Falling back to file storage")

# Initialize S3 storage service (optional - requires boto3)
storage_service = None
if os.getenv('AWS_ACCESS_KEY_ID'):
    try:
        from services.storage_service import StorageService
        storage_service = StorageService()
        logger.info("S3 storage service initialized")
    except ImportError as e:
        logger.warning(f"S3 storage not available: {e}")

# Global services
domain_manager = None
evaluation_service = None
history_service = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models at startup"""
    global domain_manager, evaluation_service, history_service
    
    logger.info("Starting up Question Intelligence System...")
    try:
        # Load all models once
        model_registry.load_all_models()
        
        # Initialize MongoDB storage (required)
        if not mongo_storage:
            raise RuntimeError("MongoDB storage is required. Check MongoDB connection.")
        
        # Initialize services with MongoDB
        embedder = model_registry.get_bi_encoder()
        domain_manager = DomainManager("data", embedder=embedder, mongo_storage=mongo_storage)
        evaluation_service = EvaluationService("data", mongo_storage=mongo_storage)
        
        # Initialize history service with MongoDB
        from services.mongodb_history_repository import MongoDBHistoryRepository
        mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
        mongo_db = os.getenv("MONGODB_DB", "qn_evaluator")
        history_service = HistoryService(repository=MongoDBHistoryRepository(mongo_uri, mongo_db))
        
        logger.info("System startup completed successfully (MongoDB-only mode)")
    except Exception as e:
        logger.error(f"Failed to load models during startup: {e}")
        raise
    yield
    logger.info("Shutting down Question Intelligence System...")

# Initialize FastAPI app
app = FastAPI(
    title="Question Intelligence System",
    description="Domain-based question evaluation with Bloom taxonomy",
    version="2.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request models
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
    format: str  # 'pdf' or 'docx'
    type: str = "mapping"  # 'mapping' or 'question_paper'

@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Question Intelligence System v2.0 is running"}

# ============ DOMAIN MANAGEMENT APIs ============

@app.post("/domains/create")
async def create_domain(request: CreateDomainRequest):
    """Create domain directory structure"""
    try:
        domain_name = request.domain_name.strip()
        mongo_storage.create_domain(request.user_id, domain_name)
        
        return {
            "message": "Domain created successfully",
            "user_id": request.user_id,
            "domain_name": domain_name
        }
    except Exception as e:
        logger.error(f"Error creating domain: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to create domain", "details": str(e)})

@app.get("/domains/{user_id}")
async def list_domains(user_id: str):
    """List all domains for user"""
    try:
        domains = mongo_storage.list_domains(user_id)
        return {"domains": domains}
    except Exception as e:
        logger.error(f"Error listing domains: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to list domains", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}")
async def delete_domain(user_id: str, domain_name: str):
    """Delete entire domain"""
    try:
        mongo_storage.delete_domain(user_id, domain_name)
        return {
            "message": "Domain deleted successfully",
            "user_id": user_id,
            "domain_name": domain_name
        }
    except Exception as e:
        logger.error(f"Error deleting domain: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to delete domain", "details": str(e)})

# ============ SYLLABUS APIs ============

@app.post("/domains/{user_id}/{domain_name}/syllabus")
async def upload_syllabus(
    user_id: str,
    domain_name: str,
    file: UploadFile = File(...)
):
    """Upload and parse syllabus (PDF or TXT) to MongoDB"""
    try:
        if not file.filename.endswith(('.pdf', '.txt')):
            raise HTTPException(status_code=400, detail={"error": "Only PDF or TXT files allowed"})
        
        file_bytes = await file.read()
        
        # Parse and save to MongoDB
        syllabus = domain_manager.save_syllabus(user_id, domain_name, file_bytes, file.filename)
        
        # Check if books exist - if yes, rebuild index
        book_names = mongo_storage.list_books(user_id, domain_name)
        if book_names:
            logger.info("Syllabus updated - rebuilding FAISS index")
            embedder = model_registry.get_bi_encoder()
            success = domain_manager.build_vector_db(user_id, domain_name, embedder)
            
            if success:
                return {
                    "message": "Syllabus uploaded and index rebuilt successfully",
                    "course_name": syllabus["course_name"],
                    "units_count": len(syllabus["units"]),
                    "co_count": len(syllabus["course_outcomes"]),
                    "index_rebuilt": True
                }
        
        return {
            "message": "Syllabus uploaded successfully",
            "course_name": syllabus["course_name"],
            "units_count": len(syllabus["units"]),
            "co_count": len(syllabus["course_outcomes"]),
            "index_rebuilt": False
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading syllabus: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to upload syllabus", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}/syllabus")
async def delete_syllabus(user_id: str, domain_name: str):
    """Delete syllabus from MongoDB"""
    try:
        mongo_storage.delete_syllabus(user_id, domain_name)
        return {"message": "Syllabus deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting syllabus: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to delete syllabus", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/syllabus/view")
async def view_syllabus(user_id: str, domain_name: str):
    """View syllabus JSON content"""
    try:
        syllabus = domain_manager.load_syllabus(user_id, domain_name)
        if not syllabus:
            raise HTTPException(status_code=404, detail={"error": "Syllabus not found"})
        return syllabus
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error viewing syllabus: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to view syllabus", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/files/syllabus")
async def download_syllabus_file(user_id: str, domain_name: str):
    """Download original syllabus file (PDF/TXT) or fallback to JSON"""
    try:
        # Try MongoDB first
        if mongo_storage:
            file_bytes, filename = mongo_storage.get_syllabus_file(user_id, domain_name)
            if file_bytes:
                return FileResponse(
                    path=None,
                    content=file_bytes,
                    filename=filename,
                    media_type='application/octet-stream'
                )
            # Fallback to JSON
            syllabus = mongo_storage.get_syllabus(user_id, domain_name)
            if syllabus:
                import io
                json_bytes = json.dumps(syllabus, indent=2).encode('utf-8')
                from fastapi.responses import Response
                return Response(
                    content=json_bytes,
                    media_type='application/json',
                    headers={
                        "Content-Disposition": "attachment; filename=syllabus.json",
                        "X-Fallback": "true"
                    }
                )
        
        # File-based fallback
        domain_path = Path("data") / user_id / domain_name
        for file in domain_path.iterdir():
            if file.is_file() and file.stem.lower() == 'syllabus' and file.suffix.lower() in ['.pdf', '.txt']:
                return FileResponse(file, filename=file.name, media_type='application/octet-stream')
        
        # Return JSON fallback
        syllabus_json = domain_path / "syllabus.json"
        if syllabus_json.exists():
            return FileResponse(
                syllabus_json, 
                filename="syllabus.json",
                media_type='application/json',
                headers={"X-Fallback": "true"}
            )
        
        raise HTTPException(status_code=404, detail={"error": "Syllabus file not found"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading syllabus: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to download syllabus", "details": str(e)})

@app.get("/domains/{user_id}/{domain_name}/files/books/{book_name}")
async def download_book_file(user_id: str, domain_name: str, book_name: str):
    """Download book PDF file"""
    try:
        book_path = Path("data") / user_id / domain_name / "books" / book_name
        
        if not book_path.exists():
            raise HTTPException(status_code=404, detail={"error": "Book not found"})
        
        return FileResponse(book_path, filename=book_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading book: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to download book", "details": str(e)})

# ============ BOOKS APIs ============

@app.post("/domains/{user_id}/{domain_name}/books")
async def upload_books(
    user_id: str,
    domain_name: str,
    files: List[UploadFile] = File(...)
):
    """Upload multiple books to MongoDB and build FAISS index"""
    try:
        # Validate files
        for file in files:
            if not file.filename.endswith('.pdf'):
                raise HTTPException(status_code=400, detail={"error": "Only PDF files allowed"})
        
        # Save temporarily
        temp_files = []
        for book in files:
            temp_path = Path(f"{book.filename}")
            with open(temp_path, "wb") as f:
                f.write(await book.read())
            temp_files.append(temp_path)
        
        # Get embedder
        embedder = model_registry.get_bi_encoder()
        
        # Add books and build index (saves to MongoDB)
        success = domain_manager.add_books(user_id, domain_name, temp_files, embedder)
        
        # Get updated metadata
        index, metadata = domain_manager.load_index(user_id, domain_name)
        chunks_count = len(metadata) if metadata else 0
        
        # Cleanup
        for temp_file in temp_files:
            temp_file.unlink()
        
        if not success:
            raise HTTPException(status_code=400, detail={"error": "Failed to build index"})
        
        # Enrich syllabus if it exists
        syllabus = domain_manager.load_syllabus(user_id, domain_name)
        if syllabus and index and metadata:
            try:
                logger.info("Starting syllabus enrichment after book upload...")
                enrichment_service = EnrichmentService()
                cross_encoder = model_registry.get_cross_encoder()
                
                # Enrich and save back to MongoDB
                enriched_syllabus = enrichment_service.enrich_syllabus_data(
                    syllabus, index, metadata, embedder, cross_encoder
                )
                mongo_storage.save_syllabus(user_id, domain_name, enriched_syllabus)
                logger.info("✓ Enrichment completed and saved to MongoDB")
            except Exception as e:
                logger.warning(f"Enrichment failed (non-critical): {e}")
        
        return {
            "message": "Books uploaded and indexed successfully",
            "books_uploaded": len(files),
            "chunks_indexed": chunks_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading books: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to upload books", "details": str(e)})

@app.delete("/domains/{user_id}/{domain_name}/books/{book_name}")
async def delete_book(user_id: str, domain_name: str, book_name: str):
    """Delete a book from MongoDB and rebuild index"""
    try:
        mongo_storage.delete_book(user_id, domain_name, book_name)
        
        # Rebuild index
        embedder = model_registry.get_bi_encoder()
        domain_manager.build_vector_db(user_id, domain_name, embedder)
        
        return {"message": "Book deleted and index rebuilt"}
    except Exception as e:
        logger.error(f"Error deleting book: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to delete book", "details": str(e)})

# ============ DOMAIN STATUS APIs ============

@app.get("/domains/{user_id}/{domain_name}/status")
async def get_domain_status(user_id: str, domain_name: str):
    """Get domain setup status from MongoDB"""
    try:
        status = mongo_storage.get_domain_status(user_id, domain_name)
        
        # Get evaluated papers from history
        history = history_service.get_history(user_id)
        evaluated_papers = [
            {
                "id": e.get("id"),
                "filename": e.get("filename"),
                "timestamp": e.get("timestamp"),
                "total_questions": e.get("total_questions")
            }
            for e in history.get("pdf_evaluations", [])
            if e.get("domain_name") == domain_name
        ]
        
        status["evaluated_papers"] = evaluated_papers
        return status
    except Exception as e:
        logger.error(f"Error getting domain status: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to get status", "details": str(e)})

@app.post("/domains/{user_id}/{domain_name}/rebuild")
async def rebuild_index(user_id: str, domain_name: str):
    """Rebuild FAISS index from existing syllabus and books, then enrich syllabus"""
    try:
        logger.info(f"Manual rebuild triggered for {user_id}/{domain_name}")
        
        # Validate domain exists
        domain_path = Path("data") / user_id / domain_name
        if not domain_path.exists():
            raise HTTPException(status_code=404, detail={"error": "Domain not found"})
        
        # Check syllabus exists
        syllabus = domain_manager.load_syllabus(user_id, domain_name)
        if not syllabus:
            raise HTTPException(status_code=400, detail={"error": "Syllabus not found. Upload syllabus first."})
        
        # Check books exist
        books_path = domain_path / "books"
        if not books_path.exists() or not list(books_path.glob("*.pdf")):
            raise HTTPException(status_code=400, detail={"error": "No books found. Upload books first."})
        
        logger.info("Starting FAISS index rebuild...")
        embedder = model_registry.get_bi_encoder()
        success = domain_manager.build_vector_db(user_id, domain_name, embedder)
        
        if not success:
            raise HTTPException(status_code=500, detail={"error": "Failed to rebuild index"})
        
        # Get updated metadata
        index, metadata = domain_manager.load_index(user_id, domain_name)
        chunks_count = len(metadata) if metadata else 0
        
        logger.info(f"Index rebuilt successfully: {chunks_count} chunks")
        
        # Enrich syllabus with subtopics
        try:
            logger.info("Starting syllabus enrichment...")
            enrichment_service = EnrichmentService()
            cross_encoder = model_registry.get_cross_encoder()
            
            syllabus_path = domain_path / "syllabus.json"
            enrichment_service.enrich_syllabus(
                syllabus_path, index, metadata, embedder, cross_encoder
            )
            logger.info("✓ Enrichment completed")
        except Exception as e:
            logger.warning(f"Enrichment failed (non-critical): {e}")
        
        return {
            "message": "Index rebuilt and syllabus enriched successfully",
            "chunks_indexed": chunks_count
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error rebuilding index: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to rebuild index", "details": str(e)})

# ============ EVALUATION APIs ============

@app.post("/evaluate/preview")
async def evaluate_preview(request: EvaluateRequest):
    """Lightweight preview evaluation - Bloom, difficulty, and strength"""
    try:
        bloom_result = model_registry.predict_bloom(request.question)
        
        # Calculate difficulty (Bloom-based)
        difficulty_score = calculate_difficulty(bloom_result["bloom_level"])
        
        # Calculate strength (question quality)
        strength_score = calculate_strength(request.question)
        
        return {
            "bloom_level": bloom_result["bloom_level"],
            "classification_confidence": bloom_result["confidence"],
            "difficulty_score": difficulty_score,
            "strength_score": strength_score
        }
    except Exception as e:
        logger.error(f"Error in preview evaluation: {e}")
        raise HTTPException(status_code=500, detail={"error": "Preview evaluation failed", "details": str(e)})

def calculate_difficulty(bloom_level: str) -> float:
    """Calculate difficulty score based on Bloom's Taxonomy level
    
    Returns: float between 0.0 and 1.0
    """
    bloom_map = {
        "BT1": 0.15,  # Remember
        "BT2": 0.30,  # Understand
        "BT3": 0.50,  # Apply
        "BT4": 0.70,  # Analyze
        "BT5": 0.85,  # Evaluate
        "BT6": 1.00   # Create
    }
    return bloom_map.get(bloom_level, 0.5)

def calculate_strength(question: str) -> float:
    """Calculate question strength based on quality indicators
    
    Measures: specificity, domain richness, cognitive depth
    Returns: float between 0.0 and 1.0
    """
    q_lower = question.lower()
    words = question.split()
    word_count = len(words)
    
    # Base score
    score = 0.5
    
    # Penalize very short questions
    if word_count < 5:
        score -= 0.3
    
    # Penalize vague starters
    vague_starters = ['what is', 'define', 'list', 'name', 'state']
    if any(q_lower.startswith(starter) for starter in vague_starters):
        score -= 0.25
    
    # Reward analytical verbs
    analytical_verbs = ['compare', 'differentiate', 'analyze', 'evaluate', 'justify', 
                        'explain', 'discuss', 'examine', 'assess', 'critique']
    if any(verb in q_lower for verb in analytical_verbs):
        score += 0.25
    
    # Reward domain-specific technical terms
    technical_indicators = ['algorithm', 'architecture', 'implement', 'design', 'optimize',
                           'structure', 'protocol', 'mechanism', 'framework', 'paradigm',
                           'methodology', 'technique', 'approach', 'strategy']
    if any(term in q_lower for term in technical_indicators):
        score += 0.15
    
    # Reward adequate length (8-30 words is good)
    if 8 <= word_count <= 30:
        score += 0.15
    elif word_count > 30:
        score += 0.05  # Slight reward for detailed questions
    
    # Reward multi-concept questions (presence of 'and', 'or', conjunctions)
    multi_concept_indicators = [' and ', ' or ', ' with ', ' using ']
    if any(indicator in q_lower for indicator in multi_concept_indicators):
        score += 0.10
    
    # Clamp between 0 and 1
    return max(0.0, min(1.0, score))

@app.post("/evaluate")
async def evaluate_question(request: EvaluateRequest):
    """Evaluate single question"""
    try:
        # Validate domain
        try:
            DomainValidator.validate_domain(request.user_id, request.domain_name)
        except FileNotFoundError as e:
            if "syllabus.json" in str(e):
                raise HTTPException(status_code=400, detail={"error": "Missing syllabus", "details": "Please upload syllabus first"})
            elif "faiss_index.bin" in str(e):
                raise HTTPException(status_code=400, detail={"error": "Missing FAISS index", "details": "Please upload books first"})
            else:
                raise HTTPException(status_code=404, detail={"error": "Domain not found"})
        
        result = evaluation_service.evaluate_question(
            request.user_id,
            request.domain_name,
            request.question
        )
        
        # Add to history
        history_service.add_single_question(
            request.user_id,
            request.domain_name,
            request.question,
            result
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating question: {e}")
        raise HTTPException(status_code=500, detail={"error": "Evaluation failed", "details": str(e)})

@app.post("/evaluate/pdf")
async def evaluate_pdf(
    user_id: str = Form(...),
    domain_name: str = Form(...),
    file: UploadFile = File(...)
):
    """Evaluate multiple questions from PDF"""
    try:
        # Validate domain
        try:
            DomainValidator.validate_domain(user_id, domain_name)
        except FileNotFoundError as e:
            if "syllabus.json" in str(e):
                raise HTTPException(status_code=400, detail={"error": "Missing syllabus"})
            elif "faiss_index.bin" in str(e):
                raise HTTPException(status_code=400, detail={"error": "Missing FAISS index"})
            else:
                raise HTTPException(status_code=404, detail={"error": "Domain not found"})
        
        # Validate file
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail={"error": "Only PDF files allowed"})
        
        # Extract questions
        pdf_bytes = await file.read()
        text = PDFQuestionParser.extract_text_from_pdf(pdf_bytes)
        questions = PDFQuestionParser.split_questions(text)
        
        logger.info(f"Extracted {len(questions)} questions from PDF: {file.filename}")
        
        # Evaluate each
        results = []
        for q in questions:
            try:
                # Question text is already cleaned by PDFQuestionParser
                # EvaluationService will apply unified cleaning again
                result = evaluation_service.evaluate_question(
                    user_id, domain_name, q["text"]
                )
                results.append({
                    "question_number": q["number"],
                    "part": q.get("part", "Part A"),
                    "question": result["question"],
                    "unit": result.get("unit"),
                    "unit_title": result.get("unit_title"),
                    "topic": result.get("topic"),
                    "course_outcomes": result.get("course_outcomes", []),
                    "bloom_level": result["bloom_level"],
                    "bloom_confidence": result["bloom_confidence"],
                    "out_of_syllabus": result.get("out_of_syllabus", False),
                    "subtopics": result.get("subtopics", []),
                    "relevant_chunks": result.get("relevant_chunks", [])
                })
            except Exception as e:
                logger.error(f"Error evaluating question {q['number']}: {e}")
                results.append({
                    "question_number": q["number"],
                    "part": q.get("part", "Part A"),
                    "question": q["text"][:100],
                    "error": str(e)
                })
        
        # Add to history with results
        eval_id = history_service.add_pdf_evaluation(
            user_id,
            domain_name,
            file.filename,
            len(questions),
            results
        )
        
        return {
            "eval_id": eval_id,
            "total_questions": len(questions),
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error evaluating PDF: {e}")
        raise HTTPException(status_code=500, detail={"error": "PDF evaluation failed", "details": str(e)})

# ============ REPORT GENERATION APIs ============

@app.post("/report/generate")
async def generate_report(request: ReportRequest):
    """Generate downloadable report (PDF or DOCX)
    
    Args:
        format: 'pdf' or 'docx'
        type: 'mapping' (Q.No, CO, BL) or 'question_paper' (Q.No, Question, CO, BL)
    """
    try:
        if request.format == 'pdf':
            file_path = ReportGenerator.generate_pdf(request.domain_name, request.results, request.type)
            return FileResponse(file_path, media_type='application/pdf', filename=f"report_{request.domain_name}.pdf")
        elif request.format == 'docx':
            file_path = ReportGenerator.generate_docx(request.domain_name, request.results, request.type)
            return FileResponse(file_path, media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document', filename=f"report_{request.domain_name}.docx")
        else:
            raise HTTPException(status_code=400, detail={"error": "Invalid format. Use 'pdf' or 'docx'"})
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(status_code=500, detail={"error": "Report generation failed", "details": str(e)})

# ============ HISTORY APIs ============

@app.get("/history/{user_id}")
async def get_history(user_id: str):
    """Get user's evaluation history"""
    try:
        history = history_service.get_history(user_id)
        return history
    except Exception as e:
        logger.error(f"Error getting history: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to get history", "details": str(e)})

@app.delete("/history/{user_id}/single/{question_id}")
async def delete_single_question(user_id: str, question_id: str):
    """Delete a single question from history"""
    try:
        success = history_service.delete_single_question(user_id, question_id)
        return {"message": "Question deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting question: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to delete question", "details": str(e)})

@app.delete("/history/{user_id}/pdf/{eval_id}")
async def delete_pdf_evaluation(user_id: str, eval_id: str):
    """Delete a PDF evaluation from history"""
    try:
        success = history_service.delete_pdf_evaluation(user_id, eval_id)
        return {"message": "PDF evaluation deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting PDF evaluation: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to delete PDF evaluation", "details": str(e)})

@app.delete("/history/{user_id}/clear")
async def clear_all_history(user_id: str):
    """Clear all history for user"""
    try:
        success = history_service.clear_all_history(user_id)
        return {"message": "All history cleared successfully"}
    except Exception as e:
        logger.error(f"Error clearing history: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to clear history", "details": str(e)})

@app.get("/history/{user_id}/pdf/{eval_id}")
async def get_pdf_evaluation_results(user_id: str, eval_id: str):
    """Get detailed results for a PDF evaluation"""
    try:
        history = history_service.get_history(user_id)
        for eval in history.get("pdf_evaluations", []):
            if eval.get("id") == eval_id:
                return eval
        raise HTTPException(status_code=404, detail={"error": "Evaluation not found"})
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting PDF evaluation: {e}")
        raise HTTPException(status_code=500, detail={"error": "Failed to get evaluation", "details": str(e)})

# ============ STORAGE/BACKUP APIs ============

@app.post("/storage/backup/{user_id}")
async def backup_user_data(user_id: str):
    """Backup entire user data folder to S3"""
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured. Set AWS credentials in .env"})
    
    try:
        uploaded_files = storage_service.sync_user_data(user_id, direction='upload')
        return {
            "message": f"User data backed up successfully",
            "user_id": user_id,
            "files_uploaded": len(uploaded_files)
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error backing up user data: {e}")
        raise HTTPException(status_code=500, detail={"error": "Backup failed", "details": str(e)})

@app.post("/storage/restore/{user_id}")
async def restore_user_data(user_id: str):
    """Restore entire user data folder from S3"""
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured. Set AWS credentials in .env"})
    
    try:
        downloaded_files = storage_service.sync_user_data(user_id, direction='download')
        return {
            "message": f"User data restored successfully",
            "user_id": user_id,
            "files_downloaded": len(downloaded_files)
        }
    except Exception as e:
        logger.error(f"Error restoring user data: {e}")
        raise HTTPException(status_code=500, detail={"error": "Restore failed", "details": str(e)})

@app.post("/storage/backup/{user_id}/{domain_name}")
async def backup_domain(user_id: str, domain_name: str):
    """Backup specific domain to S3"""
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured. Set AWS credentials in .env"})
    
    try:
        uploaded_files = storage_service.backup_domain(user_id, domain_name)
        return {
            "message": f"Domain backed up successfully",
            "user_id": user_id,
            "domain_name": domain_name,
            "files_uploaded": len(uploaded_files)
        }
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail={"error": str(e)})
    except Exception as e:
        logger.error(f"Error backing up domain: {e}")
        raise HTTPException(status_code=500, detail={"error": "Backup failed", "details": str(e)})

@app.post("/storage/restore/{user_id}/{domain_name}")
async def restore_domain(user_id: str, domain_name: str):
    """Restore specific domain from S3"""
    if not storage_service:
        raise HTTPException(status_code=503, detail={"error": "Storage service not configured. Set AWS credentials in .env"})
    
    try:
        downloaded_files = storage_service.restore_domain(user_id, domain_name)
        return {
            "message": f"Domain restored successfully",
            "user_id": user_id,
            "domain_name": domain_name,
            "files_downloaded": len(downloaded_files)
        }
    except Exception as e:
        logger.error(f"Error restoring domain: {e}")
        raise HTTPException(status_code=500, detail={"error": "Restore failed", "details": str(e)})

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Question Intelligence System server...")
    uvicorn.run(app, host="0.0.0.0", port=8002)
