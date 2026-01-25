from transformers import T5ForConditionalGeneration, T5Tokenizer
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

class CourseOutcomeNormalizationTool:
    """Normalizes Course Outcome descriptions into concept-focused representations for better semantic matching"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load flan-t5-small model for inference"""
        logger.info("Loading flan-t5-small model for CO normalization...")
        self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
        self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
        logger.info("CO normalization model loaded successfully")
    
    def normalize_course_outcomes(self, course_outcomes: List[Dict]) -> List[Dict]:
        """Normalize CO descriptions to concept-focused representations"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        logger.info(f"Normalizing {len(course_outcomes)} Course Outcomes...")
        
        normalized_cos = []
        for co in course_outcomes:
            original_description = co["description"]
            
            # Create prompt for CO normalization
            prompt = f"""Remove implementation verbs, tool-specific phrases, and application details from this Course Outcome. Keep only core academic concepts and learning intent. Make it concise and concept-focused:

"{original_description}"

Normalized concept:"""
            
            # Tokenize and generate
            inputs = self.tokenizer(prompt, return_tensors="pt", max_length=200, truncation=True)
            
            outputs = self.model.generate(
                inputs.input_ids,
                max_length=80,
                num_return_sequences=1,
                temperature=0.3,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )
            
            # Decode normalized description
            normalized_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
            normalized_description = self._clean_normalized_text(normalized_text, original_description)
            
            # Store both original and normalized
            normalized_co = {
                "id": co["id"],
                "description": original_description,  # Keep original for display
                "normalized_description": normalized_description  # Use for embeddings
            }
            normalized_cos.append(normalized_co)
            
            logger.debug(f"CO {co['id']}: '{original_description[:50]}...' -> '{normalized_description}'")
        
        logger.info("CO normalization completed")
        return normalized_cos
    
    def _clean_normalized_text(self, generated_text: str, original_text: str) -> str:
        """Clean and validate normalized text"""
        # Remove prompt echoes and clean up
        cleaned = generated_text.strip()
        
        # If generation failed or is too short, create a fallback
        if len(cleaned) < 10 or cleaned.lower() in original_text.lower():
            # Simple fallback: extract key concepts from original
            words = original_text.split()
            key_concepts = [w for w in words if len(w) > 4 and w.lower() not in 
                          ['design', 'implement', 'using', 'tool', 'application', 'real', 'time']]
            cleaned = ' '.join(key_concepts[:8])  # Take first 8 meaningful words
        
        return cleaned[:100]  # Limit length