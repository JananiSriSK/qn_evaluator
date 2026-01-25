from pydantic import BaseModel
from typing import List, Optional

class CourseOutcome(BaseModel):
    """Course Outcome model"""
    id: str
    description: str

class SyllabusUnit(BaseModel):
    """Syllabus unit model"""
    unit_number: int
    title: str
    content: str

class IngestCourseRequest(BaseModel):
    """Request model for course ingestion"""
    course_name: str
    syllabus: List[SyllabusUnit]
    course_outcomes: List[CourseOutcome]

class IngestCourseResponse(BaseModel):
    """Response model for course ingestion"""
    message: str
    course_name: str
    units_processed: int
    embeddings_stored: int

class EvaluateQuestionRequest(BaseModel):
    """Request model for question evaluation"""
    course_name: str
    question: str

class EvaluateQuestionResponse(BaseModel):
    """Response model for question evaluation"""
    out_of_syllabus: bool = False
    reason: Optional[str] = None
    predicted_co: Optional[str] = None
    matched_unit: Optional[str] = None
    matched_subtopic: Optional[str] = None
    similarity_score: Optional[float] = None

class SubtopicSuggestionRequest(BaseModel):
    """Request model for subtopic suggestion"""
    course_name: str
    unit_title: str
    unit_content: str

class SubtopicSuggestionResponse(BaseModel):
    """Response model for subtopic suggestion"""
    unit: str
    suggested_subtopics: List[str]

class SubtopicConfirmationRequest(BaseModel):
    """Request model for subtopic confirmation and ingestion"""
    course_name: str
    unit_title: str
    final_subtopics: List[str]
    course_outcomes: List[CourseOutcome]

class SubtopicConfirmationResponse(BaseModel):
    """Response model for subtopic confirmation"""
    message: str
    unit: str
    subtopics_processed: int
    embeddings_stored: int

class ProcessBookRequest(BaseModel):
    """Request model for book processing"""
    course_name: str
    book_name: str
    # PDF file will be handled separately in FastAPI

class ProcessBookResponse(BaseModel):
    """Response model for book processing"""
    message: str
    book_name: str
    chunks_processed: int
    units_mapped: int