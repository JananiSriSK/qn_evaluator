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
    

    
    def _generate_enhanced_explanation(self, prompt: str) -> str:
        """Generate enhanced explanation using book context"""
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
        Clean FAISS-only evaluation - NO LLM gates
        """
        SIMILARITY_THRESHOLD = 0.3  # Lowered from 0.7 - was too restrictive
        
        # If no FAISS results → OUT OF SYLLABUS
        if not search_results:
            return {
                "out_of_syllabus": True,
                "reason": "No matching content found in course syllabus",
                "similarity_score": 0.0
            }
        
        # Get best-matched unit from FAISS
        top_match = search_results[0]
        matched_unit_title = top_match["metadata"]["unit_title"]
        matched_content = top_match["metadata"].get("subtopic", "Unknown content")
        similarity_score = top_match["score"]
        
        # Threshold-based scope decision (NO LLM)
        if similarity_score < SIMILARITY_THRESHOLD:
            return {
                "out_of_syllabus": True,
                "reason": "Question similarity below syllabus threshold",
                "similarity_score": round(similarity_score, 3)
            }
        
        # Get course outcomes for CO selection
        if faiss_storage:
            course_outcomes = faiss_storage.get_course_outcomes(course_name)
        else:
            course_outcomes = []
            
        if not course_outcomes:
            return {
                "out_of_syllabus": True,
                "reason": "Course outcomes not found",
                "similarity_score": round(similarity_score, 3)
            }
        
        # Select CO by semantic similarity between question and CO descriptions
        co_descriptions = [co.description for co in course_outcomes]
        co_embeddings = self.embedding_tool.generate_embeddings(co_descriptions)
        
        # Find best CO using semantic similarity
        similarities = np.dot(co_embeddings, question_embedding)
        best_co_idx = np.argmax(similarities)
        best_co = course_outcomes[best_co_idx]
        
        return {
            "out_of_syllabus": False,
            "predicted_co": f"{best_co.id}: {best_co.description}",
            "matched_unit": matched_unit_title,
            "matched_subtopic": matched_content,
            "similarity_score": round(similarity_score, 3)
        }