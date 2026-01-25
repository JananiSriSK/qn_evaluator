from transformers import T5ForConditionalGeneration, T5Tokenizer
import logging
from typing import List

logger = logging.getLogger(__name__)

class SubtopicSuggestionTool:
    """Uses flan-t5-small to suggest subtopics for syllabus units"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load flan-t5-small model for inference"""
        logger.info("Loading flan-t5-small model for subtopic suggestion...")
        self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
        self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
        logger.info("Subtopic suggestion model loaded successfully")
    
    def suggest_subtopics(self, course_name: str, unit_title: str, unit_content: str) -> List[str]:
        """Generate subtopic suggestions for a syllabus unit"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        logger.info(f"Decomposing syllabus for unit: {unit_title}")
        
        # Create prompt for semantic decomposition and normalization
        prompt = f"""Course: {course_name}
Unit: {unit_title}
Syllabus: {unit_content}

Decompose the given syllabus text into atomic, teachable subtopics. The syllabus may already contain detailed content. Break it into smaller, conceptually independent subtopics. Rewrite each subtopic in clean academic language. Do not copy the input structure or return one long sentence. Only include topics implied by the syllabus. List each subtopic on a separate line:"""
        
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=300, truncation=True)
        
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=150,
            num_return_sequences=1,
            temperature=0.6,
            do_sample=True,
            pad_token_id=self.tokenizer.eos_token_id
        )
        
        # Decode response
        generated_text = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        logger.info(f"LLM decomposed: {generated_text}")
        
        # Parse subtopics from generated text
        subtopics = self._parse_subtopics(generated_text)
        
        logger.info(f"Final atomic subtopics: {subtopics}")
        return subtopics
    
    def _parse_subtopics(self, generated_text: str) -> List[str]:
        """Parse subtopics from LLM generated text"""
        # Split by newlines primarily, then other delimiters as fallback
        lines = generated_text.split('\n')
        if len(lines) < 2:
            lines = generated_text.replace(';', '\n').replace(',', '\n').split('\n')
        
        subtopics = []
        for line in lines:
            line = line.strip()
            # Remove numbering and bullet points
            line = line.lstrip('0123456789.-• ')
            # Filter meaningful atomic subtopics
            if line and len(line) > 8 and not line.lower().startswith(('course:', 'unit:', 'syllabus:')):
                subtopics.append(line)
        
        return subtopics