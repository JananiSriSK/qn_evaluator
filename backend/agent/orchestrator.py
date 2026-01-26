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
from tools.unit_densifier import UnitDensifier
from tools.validation_tester import ValidationTester
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
        self.unit_densifier = UnitDensifier(self.embedding_tool)
        self.validation_tester = ValidationTester(self.embedding_tool)
        
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
    
    def _create_concept_focused_domain_embedding(self, normalized_units, course_name):
        """Create domain embedding from atomic concepts only"""
        
        # Extract all atomic subtopics across units
        all_concepts = []
        for unit in normalized_units:
            all_concepts.extend(self._extract_atomic_subtopics(unit.content))
        
        # Remove duplicates
        all_concepts = list(set(all_concepts))
        
        # Create DISCRIMINATIVE domain text with technical specificity
        course_domain_text = (
            f"Academic course: {course_name}. "
            f"Technical concepts and topics: {', '.join(all_concepts)}. "
            f"Subject domain: computer science operating systems."
        )
        
        # Generate and store domain embedding
        domain_embedding = self.embedding_tool.generate_embeddings([course_domain_text])[0]
        self.faiss_storage.store_course_domain_embedding(course_name, domain_embedding)
        
        logger.info(f"Generated domain embedding norm: {np.linalg.norm(domain_embedding):.3f}")
        logger.info(f"Created concept-focused domain embedding with {len(all_concepts)} concepts")
        
        # VALIDATION TEST: Test domain gate with negative samples
        validation_result = self.validation_tester.test_cross_domain_rejection(course_name, domain_embedding)
        logger.info(f"Domain validation test - Rejection rate: {validation_result['rejection_rate']} (passed: {validation_result['validation_passed']})")
        
        if not validation_result['validation_passed']:
            logger.warning(f"Domain gate validation FAILED - rejection rate too low: {validation_result['rejection_rate']}")
        
        return domain_embedding
    
    def _process_with_densification(self, normalized_units, course_outcomes, course_name, book_chunks):
        """Process units with book-based densification"""
        total_subtopics = 0
        
        # Map book chunks to units using UnitDensifier
        unit_data = [{
            'unit_number': unit.unit_number,
            'title': unit.title,
            'content': unit.content
        } for unit in normalized_units]
        
        unit_book_chunks = self.unit_densifier.match_chunks_to_units(book_chunks, unit_data)
        
        for unit in normalized_units:
            # Extract atomic subtopics from unit content
            atomic_subtopics = self._extract_atomic_subtopics(unit.content)
            
            if len(atomic_subtopics) == 0:
                continue
            
            # Get relevant book chunks for this unit
            unit_chunks = unit_book_chunks.get(unit.unit_number, [])
            
            # Deduplicate book chunks
            if unit_chunks:
                unit_chunks = self.unit_densifier.deduplicate_chunks(unit_chunks)
            
            # Create densified embedding using UnitDensifier
            densified_embedding = self.unit_densifier.create_densified_embedding(
                atomic_subtopics, unit_chunks
            )
            
            # Store one embedding per subtopic (not per unit)
            for subtopic in atomic_subtopics:
                metadata = {
                    "course_name": course_name,
                    "unit_number": unit.unit_number,
                    "unit_title": unit.title,
                    "subtopic": subtopic,
                    "book_chunks_count": len(unit_chunks),
                    "densified": True
                }
                
                # CORRECT: Safe FAISS embedding format
                embedding_matrix = densified_embedding.reshape(1, -1).astype(np.float32)
                
                # Defensive assertions
                assert embedding_matrix.dtype == np.float32
                assert embedding_matrix.ndim == 2
                assert embedding_matrix.flags['C_CONTIGUOUS']
                
                self.faiss_storage.add_embeddings(embedding_matrix, [metadata])
                total_subtopics += 1
            
            logger.info(f"Densified unit {unit.unit_number}: {len(atomic_subtopics)} subtopics + {len(unit_chunks)} book chunks")
        
        # Store course outcomes separately
        self.faiss_storage.store_course_outcomes(course_name, course_outcomes)
        self.faiss_storage.save_index(course_name)
        
        return {
            "units_processed": len(normalized_units),
            "subtopics_processed": total_subtopics,
            "embeddings_stored": total_subtopics,
            "densified": True
        }
    

    
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
        logger.info(f"Question embedding norm: {np.linalg.norm(question_embedding):.3f}")
        
        # Step 2.5: COURSE DOMAIN GATE (BEFORE FAISS)
        try:
            logger.info("---- DOMAIN GATE DEBUG ----")
            logger.info(f"Question: {question}")
            logger.info(f"Question embedding shape: {question_embedding.shape}")
            
            # Load domain embedding
            self.faiss_storage.load_index(course_name)
            domain_embedding = self.faiss_storage.get_course_domain_embedding(course_name)
            
            logger.info(f"Domain embedding exists: {domain_embedding is not None}")
            if domain_embedding is not None:
                logger.info(f"Domain embedding shape: {domain_embedding.shape}")
                logger.info(f"Domain embedding norm: {np.linalg.norm(domain_embedding):.3f}")
            
            if domain_embedding is not None:
                # Compute cosine similarity (embeddings already normalized)
                domain_similarity = np.dot(question_embedding, domain_embedding)
                
                logger.info(f"Computed DOMAIN similarity: {domain_similarity:.3f}")
                logger.info(f"DOMAIN GATE: similarity = {domain_similarity:.3f}")
                
                DOMAIN_THRESHOLD = 0.75  # STRICTER: Raised from 0.55 to prevent false positives
                if domain_similarity < DOMAIN_THRESHOLD:
                    logger.info("DOMAIN GATE FAILED — STOPPING EVALUATION")
                    logger.info(f"DOMAIN GATE FAILED: {domain_similarity:.3f} < {DOMAIN_THRESHOLD}")
                    logger.info("---------------------------")
                    return {
                        "out_of_syllabus": True,
                        "reason": "Question outside course domain",
                        "similarity_score": round(domain_similarity, 3),
                        "domain_similarity": round(domain_similarity, 3)
                    }
                logger.info(f"DOMAIN GATE PASSED: {domain_similarity:.3f} >= {DOMAIN_THRESHOLD}")
            else:
                logger.info("WARNING: No domain embedding found - skipping domain gate")
                logger.info("Course needs to be re-ingested to generate domain embedding")
            
            logger.info("---------------------------")
            
        except Exception as e:
            logger.error(f"DOMAIN GATE ERROR: {e}")
            logger.info("Proceeding without domain gate due to error")
            logger.info("---------------------------")
        
        # Step 3: Search similar content in FAISS (ONLY AFTER DOMAIN GATE PASSES)
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
        """Process reference book and store chunks in FAISS"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Processing reference book '{book_name}' for course: {course_name}")
        
        # Extract text from PDF
        book_text = self.book_processor.extract_text_from_pdf(pdf_bytes)
        if not book_text or len(book_text.strip()) == 0:
            logger.error(f"PDF text extraction failed for '{book_name}' - no text extracted")
            raise ValueError(f"Could not extract text from PDF '{book_name}'")
        
        logger.info(f"Extracted {len(book_text)} characters from PDF '{book_name}'")
        
        # Chunk text
        chunks = self.book_processor.chunk_text(book_text)
        if not chunks or len(chunks) == 0:
            logger.error(f"Text chunking failed for '{book_name}' - no chunks generated")
            raise ValueError(f"No text chunks generated from PDF '{book_name}'")
        
        logger.info(f"Generated {len(chunks)} chunks from book '{book_name}'")
        
        # Generate embeddings and metadata for all chunks
        chunk_embeddings = self.embedding_tool.generate_embeddings(chunks)
        chunk_metadata = []
        
        for i, chunk in enumerate(chunks):
            chunk_metadata.append({
                "course_name": course_name,
                "book_name": book_name,
                "chunk_index": i,
                "chunk_text": chunk
            })
        
        # Store in BookStorage
        embeddings_array = np.array(chunk_embeddings)
        self.book_storage.add_book_chunks(course_name, embeddings_array, chunk_metadata)
        self.book_storage.save_book_index(course_name)
        
        logger.info(f"Stored {len(chunks)} book chunks for course: {course_name}")
        
        return {
            "book_name": book_name,
            "chunks_processed": len(chunks),
            "chunks_stored": len(chunks)
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
        
        # Step 2: Generate concept-focused domain embedding
        self._create_concept_focused_domain_embedding(normalized_units, course_name)
        
        # Step 2.5: Check for existing book data and create densified embeddings if available
        book_available = self.book_storage.load_book_index(course_name)
        if book_available:
            logger.info("Book data found - creating densified embeddings")
            book_chunks = self.book_storage.get_all_chunks(course_name)
            return self._process_with_densification(normalized_units, course_outcomes, course_name, book_chunks)
        else:
            logger.info("No book data - using syllabus-only embeddings")
        
        # Step 3: Process normalized units
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
    
    def process_course_densified(self, course_name: str, syllabus_text: str, 
                                course_outcomes: List[CourseOutcome], book_chunks: List[str] = None) -> dict:
        """Process course with densified units (syllabus + book content)"""
        if not self.models_loaded:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        logger.info(f"Starting densified course processing for: {course_name}")
        
        # Step 1: Normalize syllabus
        normalized_units = self.syllabus_preprocessor.normalize_syllabus(syllabus_text)
        logger.info(f"Normalized syllabus into {len(normalized_units)} units")
        
        # Step 2: Match book chunks to units (if provided)
        unit_book_chunks = {}
        if book_chunks:
            unit_data = [{
                'unit_number': unit.unit_number,
                'title': unit.title,
                'content': unit.content
            } for unit in normalized_units]
            
            unit_book_chunks = self.unit_densifier.match_chunks_to_units(book_chunks, unit_data)
            logger.info(f"Matched book chunks to {len(unit_book_chunks)} units")
        
        # Step 3: Process each unit with densification
        total_units = 0
        densified_embeddings = []
        metadata_list = []
        
        for unit in normalized_units:
            # Extract syllabus subtopics
            syllabus_subtopics = self._extract_atomic_subtopics(unit.content)
            
            # Get book chunks for this unit
            book_chunks_for_unit = unit_book_chunks.get(unit.unit_number, [])
            
            # Deduplicate book chunks
            if book_chunks_for_unit:
                book_chunks_for_unit = self.unit_densifier.deduplicate_chunks(book_chunks_for_unit)
            
            # Create densified embedding
            densified_embedding = self.unit_densifier.create_densified_embedding(
                syllabus_subtopics, book_chunks_for_unit
            )
            
            densified_embeddings.append(densified_embedding)
            metadata_list.append({
                "course_name": course_name,
                "unit_number": unit.unit_number,
                "unit_title": unit.title,
                "syllabus_subtopics": syllabus_subtopics,
                "book_chunks_count": len(book_chunks_for_unit)
            })
            
            total_units += 1
            logger.info(f"Densified unit {unit.unit_number}: {len(syllabus_subtopics)} subtopics + {len(book_chunks_for_unit)} book chunks")
        
        # Step 4: Store densified embeddings in FAISS
        if densified_embeddings:
            self.faiss_storage.add_embeddings(np.array(densified_embeddings), metadata_list)
        
        # Store course outcomes separately
        self.faiss_storage.store_course_outcomes(course_name, course_outcomes)
        self.faiss_storage.save_index(course_name)
        
        logger.info(f"Densified course processing completed for: {course_name}")
        
        return {
            "units_processed": total_units,
            "embeddings_stored": len(densified_embeddings),
            "book_chunks_used": sum(len(chunks) for chunks in unit_book_chunks.values()) if unit_book_chunks else 0
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