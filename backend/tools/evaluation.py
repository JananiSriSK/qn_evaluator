import numpy as np
import logging
from typing import List, Dict, Any, Tuple
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

logger = logging.getLogger(__name__)

class EvaluationTool:
    """Evaluates questions against course content using semantic similarity"""
    
    def __init__(self, embedding_tool=None):
        self.tokenizer = None
        self.model = None
        self.embedding_tool = embedding_tool
    
    def load_model(self):
        """Load LLM for explanation generation only"""
        if self.tokenizer is None:
            logger.info("Loading flan-t5-small for explanation generation...")
            self.tokenizer = AutoTokenizer.from_pretrained("google/flan-t5-small")
            self.model = AutoModelForSeq2SeqLM.from_pretrained("google/flan-t5-small")
            logger.info("Explanation model loaded successfully")
    

    def _generate_explanation(self, question: str, course_name: str, 
                             is_in_syllabus: bool, matched_subtopic: str = None) -> str:
        """Generate LLM explanation for scope decision (explanation only, no decision making)"""
        try:
            if self.tokenizer is None or self.model is None:
                logger.warning("LLM model not loaded, using fallback explanation")
                if is_in_syllabus:
                    return "The question aligns with foundational concepts explicitly covered in the selected syllabus unit."
                else:
                    return "The question relates to concepts outside the core topics covered in the syllabus."
            
            if is_in_syllabus:
                prompt = f"Explain why this question aligns with the course syllabus. Question: {question}. Course: {course_name}. Matched content: {matched_subtopic}. Provide 1-2 sentences in academic tone."
            else:
                prompt = f"Explain why this question is outside the scope of the course syllabus. Question: {question}. Course: {course_name}. Provide 1-2 sentences in academic tone."
            
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=100,
                num_beams=2,
                temperature=0.7,
                do_sample=False
            )
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Error generating explanation: {e}")
            if is_in_syllabus:
                return "The question aligns with foundational concepts explicitly covered in the selected syllabus unit."
            else:
                return "The question relates to concepts outside the core topics covered in the syllabus."
    

    
    def _validate_with_books(self, question_embedding: np.ndarray, course_name: str, 
                           unit_title: str, book_storage) -> bool:
        """Validate question scope using reference books for the matched unit"""
        if not book_storage:
            logger.info("Book validation skipped: No book storage available")
            return True  # No books available, skip validation
        
        # Extract unit number from unit title (e.g., "UNIT I" -> 1)
        unit_number = None
        if "UNIT" in unit_title.upper():
            try:
                roman_to_int = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6}
                for roman, num in roman_to_int.items():
                    if roman in unit_title.upper():
                        unit_number = num
                        break
            except:
                pass
        
        if unit_number is None:
            logger.info(f"Book validation skipped: Cannot extract unit number from '{unit_title}'")
            return True  # Cannot determine unit number, skip validation
        
        # Search book chunks for this specific unit
        book_results = book_storage.search_book_chunks(course_name, question_embedding, unit_number, k=5)
        
        if not book_results:
            logger.info(f"Book validation skipped: No book content found for course '{course_name}' unit {unit_number}")
            return True  # No book content for this unit, skip validation
        
        # Check if question has semantic alignment with book content
        BOOK_SIMILARITY_THRESHOLD = 0.4
        max_book_similarity = max([result["score"] for result in book_results])
        
        logger.info(f"Book validation: max similarity = {max_book_similarity:.3f}, threshold = {BOOK_SIMILARITY_THRESHOLD}")
        
        return max_book_similarity >= BOOK_SIMILARITY_THRESHOLD
    
    def _generate_enhanced_explanation(self, prompt: str) -> str:
        try:
            if self.tokenizer is None or self.model is None:
                return "Enhanced explanation unavailable due to model loading issues."
            
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=150,
                num_beams=2,
                do_sample=False
            )
            explanation = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            return explanation.strip()
        except Exception as e:
            logger.error(f"Error generating enhanced explanation: {e}")
            return "Enhanced explanation unavailable due to processing error."
    
    def find_best_co_match(self, question: str, question_embedding: np.ndarray, 
                          search_results: List[Dict[str, Any]], course_name: str, 
                          book_storage=None, faiss_storage=None) -> Dict[str, Any]:
        """
        CORRECTED: Unit-conditioned CO selection with domain validation
        """
        SIMILARITY_THRESHOLD = 0.3
        
        # If no FAISS results → OUT OF SYLLABUS
        if not search_results:
            return {
                "out_of_syllabus": True,
                "reason": "No matching content found in course syllabus",
                "similarity_score": 0.0
            }
        
        # Get best-matched unit from FAISS (handle both canonical and densified metadata)
        top_match = search_results[0]
        matched_unit_title = top_match["metadata"]["unit_title"]
        faiss_similarity = top_match["score"]
        
        # Extract subtopic text (handle different metadata structures)
        if "subtopic" in top_match["metadata"]:
            # Canonical processing: single subtopic string
            subtopic_text = top_match["metadata"]["subtopic"]
        elif "syllabus_subtopics" in top_match["metadata"]:
            # Densified processing: list of subtopics
            subtopics_list = top_match["metadata"]["syllabus_subtopics"]
            if isinstance(subtopics_list, list) and subtopics_list:
                subtopic_text = subtopics_list[0]  # Use first subtopic for validation
            else:
                subtopic_text = str(subtopics_list)
        else:
            subtopic_text = "Unknown subtopic"
        
        # Debug output
        logger.info(f"Question: {question}")
        logger.info(f"Matched subtopic: {subtopic_text}")
        logger.info(f"FAISS similarity: {faiss_similarity:.3f}")
        
        # Primary scope decision based on FAISS similarity
        SIMILARITY_THRESHOLD = 0.3
        if faiss_similarity < SIMILARITY_THRESHOLD:
            return {
                "out_of_syllabus": True,
                "reason": "Question content not found in course syllabus",
                "similarity_score": round(faiss_similarity, 3)
            }
        
        # BOOK-GROUNDED SCOPE VALIDATION (if books available)
        if book_storage:
            logger.info(f"Attempting book validation for course '{course_name}', unit '{matched_unit_title}'")
            if not self._validate_with_books(question_embedding, course_name, matched_unit_title, book_storage):
                logger.info("Book validation FAILED - marking as OUT_OF_SYLLABUS")
                return {
                    "out_of_syllabus": True,
                    "reason": "Question not validated by reference book content",
                    "similarity_score": round(faiss_similarity, 3)
                }
            else:
                logger.info("Book validation PASSED - proceeding to CO selection")
        else:
            logger.info("No book storage available - skipping book validation")
        
        # Get course outcomes for CO selection
        if faiss_storage:
            course_outcomes = faiss_storage.get_course_outcomes(course_name)
        else:
            course_outcomes = []
            
        if not course_outcomes:
            return {
                "out_of_syllabus": True,
                "reason": "Course outcomes not found",
                "similarity_score": round(faiss_similarity, 3)
            }
        
        # UNIT-CONDITIONED CO SELECTION: Filter COs by unit content alignment
        unit_relevant_cos = []
        
        # Use matched subtopic for CO-unit alignment
        unit_embedding = self.embedding_tool.generate_embeddings([subtopic_text])[0]
        
        for co in course_outcomes:
            co_embedding = self.embedding_tool.generate_embeddings([co.description])[0]
            
            # Check if CO semantically aligns with matched unit
            co_unit_similarity = np.dot(co_embedding, unit_embedding)
            if co_unit_similarity > 0.4:  # CO must be relevant to unit
                unit_relevant_cos.append(co)
        
        # If no COs align with unit, return indeterminate result
        if not unit_relevant_cos:
            return {
                "out_of_syllabus": False,
                "predicted_co": "CO could not be confidently determined",
                "matched_unit": matched_unit_title,
                "matched_subtopic": subtopic_text,
                "similarity_score": round(faiss_similarity, 3)
            }
        
        # Select best CO from unit-relevant COs only
        co_descriptions = [co.description for co in unit_relevant_cos]
        co_embeddings = self.embedding_tool.generate_embeddings(co_descriptions)
        
        # Find best CO using semantic similarity with question
        similarities = np.dot(co_embeddings, question_embedding)
        best_co_idx = np.argmax(similarities)
        best_co = unit_relevant_cos[best_co_idx]
        
        return {
            "out_of_syllabus": False,
            "predicted_co": f"{best_co.id}: {best_co.description}",
            "matched_unit": matched_unit_title,
            "matched_subtopic": subtopic_text,
            "similarity_score": round(faiss_similarity, 3)
        }