from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import os
from models.schemas import (IngestCourseRequest, IngestCourseResponse, 
                           EvaluateQuestionRequest, EvaluateQuestionResponse,
                           SubtopicSuggestionRequest, SubtopicSuggestionResponse,
                           SubtopicConfirmationRequest, SubtopicConfirmationResponse,
                           ProcessBookRequest, ProcessBookResponse)
from agent.orchestrator import AgentOrchestrator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from test_routes import test_router

from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all models at startup"""
    logger.info("Starting up Question Intelligence System...")
    try:
        orchestrator.load_models()
        logger.info("System startup completed successfully")
    except Exception as e:
        logger.error(f"Failed to load models during startup: {e}")
        raise
    yield
    logger.info("Shutting down Question Intelligence System...")

# Initialize FastAPI app
app = FastAPI(
    title="Question Intelligence System",
    description="Agent-based system for syllabus-aware CO mapping",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize orchestrator
STORAGE_PATH = os.path.join(os.path.dirname(__file__), "storage")
orchestrator = AgentOrchestrator(STORAGE_PATH)

# Include test routes
app.include_router(test_router)



@app.get("/")
async def root():
    """Health check endpoint"""
    return {"status": "ok", "message": "Question Intelligence System is running"}

@app.post("/ingest-course", response_model=IngestCourseResponse)
async def ingest_course(request: IngestCourseRequest):
    """
    Ingest course data with automatic processing:
    1. Normalize syllabus text
    2. Enrich content with subtopics using flan-t5-small
    3. Generate embeddings using e5-small-v2
    4. Store in FAISS with CO mapping metadata
    """
    try:
        logger.info(f"Received course ingestion request for: {request.course_name}")
        
        # Validate input
        if not request.syllabus:
            raise HTTPException(status_code=400, detail="Syllabus cannot be empty")
        if not request.course_outcomes:
            raise HTTPException(status_code=400, detail="Course outcomes cannot be empty")
        
        # Convert syllabus units to text for canonical processing
        syllabus_text_parts = []
        for unit in request.syllabus:
            unit_text = f"UNIT {unit.unit_number} {unit.title}\n{unit.content}"
            syllabus_text_parts.append(unit_text)
        syllabus_text = "\n\n".join(syllabus_text_parts)
        
        # Process course through orchestrator with canonical processing
        result = orchestrator.process_course_canonical(
            course_name=request.course_name,
            syllabus_text=syllabus_text,
            course_outcomes=request.course_outcomes
        )
        
        logger.info(f"Course ingestion completed for: {request.course_name}")
        
        return IngestCourseResponse(
            message="Course processed successfully with atomic subtopic decomposition",
            course_name=request.course_name,
            units_processed=result["units_processed"],
            embeddings_stored=result["embeddings_stored"]
        )
        
    except Exception as e:
        logger.error(f"Error during course ingestion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/evaluate-question", response_model=EvaluateQuestionResponse)
async def evaluate_question(request: EvaluateQuestionRequest):
    """
    Evaluate question against course content to predict Course Outcome:
    1. Normalize question text
    2. Generate embedding using e5-small-v2
    3. Search similar syllabus content in course-specific FAISS index
    4. Infer most relevant CO using semantic alignment OR detect out-of-syllabus
    """
    try:
        logger.info(f"Received question evaluation request for course: {request.course_name}")
        
        # Validate input
        if not request.question.strip():
            raise HTTPException(status_code=400, detail="Question cannot be empty")
        
        # Evaluate question through orchestrator with course-scoped retrieval
        result = orchestrator.evaluate_question(
            course_name=request.course_name,
            question=request.question
        )
        
        # Handle out-of-syllabus detection
        if result.get("out_of_syllabus", False):
            logger.info(f"Hard boundary enforced: Out-of-syllabus for course: {request.course_name}")
            return EvaluateQuestionResponse(
                out_of_syllabus=True,
                reason=result["reason"],
                similarity_score=result.get("similarity_score"),
                domain_similarity=result.get("domain_similarity")
            )
        
        # Normal CO prediction response
        logger.info(f"Question evaluation completed for course: {request.course_name}")
        return EvaluateQuestionResponse(
            out_of_syllabus=False,
            predicted_co=result["predicted_co"],
            matched_unit=result["matched_unit"],
            matched_subtopic=result["matched_subtopic"],
            similarity_score=result["similarity_score"]
        )
        
    except Exception as e:
        logger.error(f"Error during question evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/suggest-subtopics", response_model=SubtopicSuggestionResponse)
async def suggest_subtopics(request: SubtopicSuggestionRequest):
    """
    Generate subtopic suggestions for a syllabus unit using LLM:
    1. Use flan-t5-small to suggest relevant subtopics
    2. Return suggestions for professor review/editing
    """
    try:
        logger.info(f"Received subtopic suggestion request for unit: {request.unit_title}")
        
        # Generate subtopic suggestions through orchestrator
        suggested_subtopics = orchestrator.suggest_subtopics(
            course_name=request.course_name,
            unit_title=request.unit_title,
            unit_content=request.unit_content
        )
        
        logger.info(f"Subtopic suggestion completed for unit: {request.unit_title}")
        
        return SubtopicSuggestionResponse(
            unit=request.unit_title,
            suggested_subtopics=suggested_subtopics
        )
        
    except Exception as e:
        logger.error(f"Error during subtopic suggestion: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/confirm-subtopics", response_model=SubtopicConfirmationResponse)
async def confirm_subtopics(request: SubtopicConfirmationRequest):
    """
    Process confirmed subtopics and store with automatic CO mapping:
    1. Generate embeddings for each subtopic
    2. Map subtopics to COs using semantic similarity
    3. Store in FAISS for question evaluation
    """
    try:
        logger.info(f"Received subtopic confirmation for unit: {request.unit_title}")
        
        # Validate input
        if not request.final_subtopics:
            raise HTTPException(status_code=400, detail="Final subtopics cannot be empty")
        if not request.course_outcomes:
            raise HTTPException(status_code=400, detail="Course outcomes cannot be empty")
        
        # Process subtopics through orchestrator
        result = orchestrator.process_subtopics(
            course_name=request.course_name,
            unit_title=request.unit_title,
            subtopics=request.final_subtopics,
            course_outcomes=request.course_outcomes
        )
        
        logger.info(f"Subtopic confirmation completed for unit: {request.unit_title}")
        
        return SubtopicConfirmationResponse(
            message="Subtopics processed and stored successfully",
            unit=request.unit_title,
            subtopics_processed=result["subtopics_processed"],
            embeddings_stored=result["embeddings_stored"]
        )
        
    except Exception as e:
        logger.error(f"Error during subtopic confirmation: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/process-book", response_model=ProcessBookResponse)
async def process_book(course_name: str = Form(...), book_name: str = Form(...), file: UploadFile = File(...)):
    """
    Process reference book PDF and map to syllabus units:
    1. Extract text from PDF
    2. Chunk text automatically
    3. Map chunks to syllabus units using embeddings
    4. Store in separate book FAISS index
    """
    try:
        logger.info(f"Received book processing request: {book_name} for course: {course_name}")
        
        # Validate file type
        if not file.filename.endswith('.pdf'):
            raise HTTPException(status_code=400, detail="Only PDF files are supported")
        
        # Read PDF bytes
        pdf_bytes = await file.read()
        if not pdf_bytes:
            raise HTTPException(status_code=400, detail="Empty PDF file")
        
        # Process book through orchestrator
        result = orchestrator.process_reference_book(
            course_name=course_name,
            book_name=book_name,
            pdf_bytes=pdf_bytes,
            syllabus=[]  # Will be loaded from storage if needed
        )
        
        logger.info(f"Book processing completed for: {book_name}")
        
        return ProcessBookResponse(
            message="Book processed successfully",
            book_name=result["book_name"],
            chunks_processed=result["chunks_processed"],
            units_mapped=result.get("chunks_available_for_densification", 0)
        )
        
    except Exception as e:
        logger.error(f"Error during book processing: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.post("/evaluate-system", response_model=dict)
async def evaluate_system_performance(course_name: str):
    """
    Run comprehensive system evaluation with predefined test cases
    Returns detailed metrics including accuracy, precision, recall, F1-score
    """
    try:
        logger.info(f"Starting system evaluation for course: {course_name}")
        
        from tools.system_evaluator import SystemEvaluator
        evaluator = SystemEvaluator(orchestrator)
        
        # Run comprehensive evaluation
        evaluation_results = evaluator.run_comprehensive_evaluation(course_name)
        
        logger.info(f"System evaluation completed for course: {course_name}")
        return evaluation_results
        
    except Exception as e:
        logger.error(f"Error during system evaluation: {e}")
        raise HTTPException(status_code=500, detail=f"Evaluation error: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Question Intelligence System server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)