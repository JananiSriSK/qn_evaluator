import logging
from typing import List
from models.schemas import SyllabusUnit, CourseOutcome
from tools.enrichment import EnrichmentTool
from tools.embedder import EmbeddingTool
from tools.faiss_storage import FAISSStorage
from tools.evaluation import EvaluationTool
from tools.subtopic_suggestion import SubtopicSuggestionTool
from tools.co_normalization import CourseOutcomeNormalizationTool
from tools.book_processor import BookProcessor
from tools.book_storage import BookStorage
from tools.syllabus_preprocessor import SyllabusPreprocessor
from services.preprocessing import TextPreprocessor
import numpy as np

logger = logging.getLogger(__name__)

class AgentOrchestrator:
    """Orchestrates the course ingestion workflow using various tools"""
    
    def __init__(self, storage_path: str):
        # Initialize tools
        self.enrichment_tool = EnrichmentTool()
        self.embedding_tool = EmbeddingTool()
        self.faiss_storage = FAISSStorage(storage_path)
        self.evaluation_tool = EvaluationTool(self.embedding_tool)
        self.subtopic_tool = SubtopicSuggestionTool()
        self.co_normalization_tool = CourseOutcomeNormalizationTool()
        self.book_processor = BookProcessor()
        self.book_storage = BookStorage(storage_path)
        self.preprocessor = TextPreprocessor()
        self.syllabus_preprocessor = SyllabusPreprocessor()
        
        # Track if models are loaded
        self.models_loaded = False
    
    def _extract_atomic_subtopics(self, syllabus_text: str) -> List[str]:
        """Extract atomic subtopics from syllabus text using delimiters
        FAISS vectors represent atomic syllabus subtopics, not full units
        """
        # Split by common delimiters
        delimiters = ['–', '-', ';']
        subtopics = [syllabus_text]
        
        for delimiter in delimiters:
            new_subtopics = []
            for subtopic in subtopics:
                new_subtopics.extend(subtopic.split(delimiter))
            subtopics = new_subtopics
        
        # Clean and filter subtopics
        cleaned_subtopics = []
        for subtopic in subtopics:
            cleaned = subtopic.strip()
            if cleaned and len(cleaned) > 2:  # Non-empty and meaningful
                cleaned_subtopics.append(cleaned)
        
        return cleaned_subtopics if len(cleaned_subtopics) > 0 else []
    

    
    def load_models(self):
        """Load all models at startup"""
        if not self.models_loaded:
            logger.info("Loading all models...")
            self.enrichment_tool.load_model()
            self.embedding_tool.load_model()
            self.subtopic_tool.load_model()
            self.co_normalization_tool.load_model()
            self.evaluation_tool.load_model()
            self.book_processor.load_tokenizer()
            self.models_loaded = True
            logger.info("All models loaded successfully")
    
    def process_course(self, course_name: str, syllabus: List[SyllabusUnit], 
                      course_outcomes: List[CourseOutcome]) -> dict:
        """Process complete course ingestion workflow"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Starting course processing for: {course_name}")
        
        # Step 1: Preprocess and enrich syllabus content
        enriched_contents = []
        metadata_list = []
        
        for unit in syllabus:
            # Preprocess content
            normalized_content = self.preprocessor.prepare_syllabus_content(
                unit.title, unit.content
            )
            
            # Enrich content using flan-t5
            enriched_content = self.enrichment_tool.enrich_content(normalized_content)
            enriched_contents.append(enriched_content)
            
            # Prepare metadata for each unit
            for co in course_outcomes:
                metadata_list.append({
                    "course_name": course_name,
                    "unit_number": unit.unit_number,
                    "unit_title": unit.title,
                    "course_outcome_id": co.id,
                    "course_outcome_description": co.description,
                    "content": enriched_content
                })
        
        # Step 2: Generate embeddings
        # Create content list for embedding (one per CO-unit combination)
        embedding_texts = []
        for unit in syllabus:
            normalized_content = self.preprocessor.prepare_syllabus_content(
                unit.title, unit.content
            )
            enriched_content = self.enrichment_tool.enrich_content(normalized_content)
            
            for co in course_outcomes:
                # Combine unit content with CO for context-aware embedding
                combined_text = f"{enriched_content} [CO: {co.description}]"
                embedding_texts.append(combined_text)
        
        embeddings = self.embedding_tool.generate_embeddings(embedding_texts)
        
        # Step 3: Store in FAISS
        self.faiss_storage.add_embeddings(embeddings, metadata_list)
        self.faiss_storage.save_index(course_name)
        
        logger.info(f"Course processing completed for: {course_name}")
        
        return {
            "units_processed": len(syllabus),
            "embeddings_stored": len(embeddings),
            "course_outcomes_mapped": len(course_outcomes)
        }
    
    def evaluate_question(self, course_name: str, question: str) -> dict:
        """Evaluate question against course content to predict CO"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Starting question evaluation for course: {course_name}")
        
        # Step 1: Preprocess question
        normalized_question = self.preprocessor.normalize_text(question)
        
        # Step 2: Generate question embedding
        question_embedding = self.embedding_tool.generate_embeddings([normalized_question])[0]
        
        # Step 3: Search similar content in FAISS
        search_results = self.faiss_storage.search_similar(
            question_embedding, course_name, k=10
        )
        
        # Step 4: Evaluate and find best CO match with book enhancement
        self.book_storage.load_book_index(course_name)  # Load if exists
        
        # Debug: Check if course outcomes exist
        logger.info(f"Course outcomes in memory: {len(self.faiss_storage.course_outcomes.get(course_name, []))}")
        
        # Ensure FAISS storage loads the course index and outcomes
        self.faiss_storage.load_index(course_name)
        
        # Debug: Check if course outcomes loaded from disk
        logger.info(f"Course outcomes after load: {len(self.faiss_storage.course_outcomes.get(course_name, []))}")
        
        evaluation_result = self.evaluation_tool.find_best_co_match(
            question, question_embedding, search_results, course_name, self.book_storage, self.faiss_storage
        )
        
        logger.info(f"Question evaluation completed for course: {course_name}")
        return evaluation_result
    
    def process_reference_book(self, course_name: str, book_name: str, pdf_bytes: bytes, 
                              syllabus: List[SyllabusUnit]) -> dict:
        """Process reference book and map chunks to syllabus units"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Processing reference book '{book_name}' for course: {course_name}")
        
        # Extract text from PDF
        book_text = self.book_processor.extract_text_from_pdf(pdf_bytes)
        if not book_text:
            raise ValueError("Could not extract text from PDF")
        
        # Chunk text
        chunks = self.book_processor.chunk_text(book_text)
        if not chunks:
            raise ValueError("No text chunks generated from PDF")
        
        # Generate embeddings for chunks
        chunk_embeddings = self.embedding_tool.generate_embeddings(chunks)
        
        # Generate embeddings for syllabus units (for mapping)
        unit_texts = [f"{unit.title}: {unit.content}" for unit in syllabus]
        unit_embeddings = self.embedding_tool.generate_embeddings(unit_texts)
        
        # Map each chunk to best matching syllabus unit
        metadata_list = []
        for i, chunk in enumerate(chunks):
            # Find best matching unit using cosine similarity
            similarities = np.dot(unit_embeddings, chunk_embeddings[i])
            best_unit_idx = np.argmax(similarities)
            best_unit = syllabus[best_unit_idx]
            
            metadata_list.append({
                "course_name": course_name,
                "unit_number": best_unit.unit_number,
                "unit_title": best_unit.title,
                "book_name": book_name,
                "chunk_text": chunk
            })
        
        # Store in book FAISS index
        self.book_storage.add_book_chunks(course_name, chunk_embeddings, metadata_list)
        self.book_storage.save_book_index(course_name)
        
        logger.info(f"Processed {len(chunks)} chunks from book '{book_name}'")
        
        return {
            "book_name": book_name,
            "chunks_processed": len(chunks),
            "units_mapped": len(set(m["unit_number"] for m in metadata_list))
        }
    
    def process_course_direct(self, course_name: str, syllabus: List[SyllabusUnit], 
                             course_outcomes: List[CourseOutcome]) -> dict:
        """Process course - store ONLY unit content in FAISS"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Starting direct course processing for: {course_name}")
        
        total_subtopics = 0
        
        for unit in syllabus:
            # Extract atomic subtopics from unit content
            atomic_subtopics = self._extract_atomic_subtopics(unit.content)
            
            if len(atomic_subtopics) == 0:
                continue
                
            # Generate embeddings for subtopics
            subtopic_embeddings = self.embedding_tool.generate_embeddings(atomic_subtopics)
            
            # Store ONLY unit metadata (NO CO attachment)
            metadata_list = []
            for i, subtopic in enumerate(atomic_subtopics):
                metadata_list.append({
                    "course_name": course_name,
                    "unit_number": unit.unit_number,
                    "unit_title": unit.title,
                    "subtopic": subtopic
                })
            
            # Store embeddings in FAISS
            if len(subtopic_embeddings) > 0:
                self.faiss_storage.add_embeddings(np.array(subtopic_embeddings), metadata_list)
                total_subtopics += len(atomic_subtopics)
                
                logger.info(f"Processed unit {unit.unit_number}: {len(atomic_subtopics)} subtopics")
        
        # Store course outcomes separately for later CO selection
        self.faiss_storage.store_course_outcomes(course_name, course_outcomes)
        self.faiss_storage.save_index(course_name)
        
        logger.info(f"Direct course processing completed for: {course_name}")
        
        return {
            "units_processed": len(syllabus),
            "subtopics_processed": total_subtopics,
            "embeddings_stored": total_subtopics
        }
    
    def process_course_canonical(self, course_name: str, syllabus_text: str, 
                                course_outcomes: List[CourseOutcome]) -> dict:
        """CANONICAL course processing with syllabus normalization"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Starting canonical course processing for: {course_name}")
        
        # Step 1: CANONICAL PREPROCESSING - normalize syllabus format
        normalized_units = self.syllabus_preprocessor.normalize_syllabus(syllabus_text)
        logger.info(f"Normalized syllabus into {len(normalized_units)} units")
        
        # Step 2: Process normalized units
        total_subtopics = 0
        
        for unit in normalized_units:
            # Extract atomic subtopics from unit content
            atomic_subtopics = self._extract_atomic_subtopics(unit.content)
            
            if len(atomic_subtopics) == 0:
                continue
                
            # Generate embeddings for subtopics
            subtopic_embeddings = self.embedding_tool.generate_embeddings(atomic_subtopics)
            
            # Store ONLY unit metadata (NO CO attachment)
            metadata_list = []
            for subtopic in atomic_subtopics:
                metadata_list.append({
                    "course_name": course_name,
                    "unit_number": unit.unit_number,
                    "unit_title": unit.title,
                    "subtopic": subtopic
                })
            
            # Store embeddings in FAISS
            if len(subtopic_embeddings) > 0:
                self.faiss_storage.add_embeddings(np.array(subtopic_embeddings), metadata_list)
                total_subtopics += len(atomic_subtopics)
                
                logger.info(f"Processed unit {unit.unit_number}: {len(atomic_subtopics)} subtopics")
        
        # Store course outcomes separately for later CO selection
        self.faiss_storage.store_course_outcomes(course_name, course_outcomes)
        self.faiss_storage.save_index(course_name)
        
        logger.info(f"Canonical course processing completed for: {course_name}")
        
        return {
            "units_processed": len(normalized_units),
            "subtopics_processed": total_subtopics,
            "embeddings_stored": total_subtopics
        }
    
    def suggest_subtopics(self, course_name: str, unit_title: str, unit_content: str) -> List[str]:
        """Generate subtopic suggestions for a syllabus unit"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Generating subtopic suggestions for unit: {unit_title}")
        
        # Preprocess unit content
        normalized_content = self.preprocessor.normalize_text(unit_content)
        
        # Generate subtopic suggestions using LLM
        subtopics = self.subtopic_tool.suggest_subtopics(
            course_name, unit_title, normalized_content
        )
        
        logger.info(f"Generated {len(subtopics)} subtopics for unit: {unit_title}")
        return subtopics
    
    def process_subtopics(self, course_name: str, unit_title: str, 
                         subtopics: List[str], course_outcomes: List[CourseOutcome]) -> dict:
        """Process confirmed subtopics and store with CO mapping"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Processing {len(subtopics)} subtopics for unit: {unit_title}")
        
        # Step 1: Generate CO embeddings for semantic matching
        co_descriptions = [co.description for co in course_outcomes]
        co_embeddings = self.embedding_tool.generate_embeddings(co_descriptions)
        
        # Step 2: Process each subtopic
        metadata_list = []
        subtopic_embeddings = []
        
        for subtopic in subtopics:
            # Normalize subtopic text
            normalized_subtopic = self.preprocessor.normalize_text(subtopic)
            
            # Generate embedding for subtopic
            subtopic_embedding = self.embedding_tool.generate_embeddings([normalized_subtopic])[0]
            subtopic_embeddings.append(subtopic_embedding)
            
            # Find best matching CO using semantic similarity
            similarities = np.dot(co_embeddings, subtopic_embedding)
            best_co_idx = np.argmax(similarities)
            best_co = course_outcomes[best_co_idx]
            
            # Create metadata for this subtopic
            metadata_list.append({
                "course_name": course_name,
                "unit_title": unit_title,
                "subtopic": normalized_subtopic,
                "course_outcome_id": best_co.id,
                "course_outcome_description": best_co.description,
                "content": normalized_subtopic  # Use subtopic as content
            })
            
            logger.debug(f"Mapped subtopic '{subtopic[:50]}...' to {best_co.id}")
        
        # Step 3: Store embeddings in FAISS
        if len(subtopic_embeddings) > 0:
            embeddings_array = np.array(subtopic_embeddings)
            self.faiss_storage.add_embeddings(embeddings_array, metadata_list)
            self.faiss_storage.save_index(course_name)
        
        logger.info(f"Subtopic processing completed for unit: {unit_title}")
        
        return {
            "subtopics_processed": len(subtopics),
            "embeddings_stored": len(subtopic_embeddings)
        }