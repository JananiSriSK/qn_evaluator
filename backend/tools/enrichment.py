from transformers import T5ForConditionalGeneration, T5Tokenizer
import logging

logger = logging.getLogger(__name__)

class EnrichmentTool:
    """Uses flan-t5-small to infer subtopics from syllabus content"""
    
    def __init__(self):
        self.model = None
        self.tokenizer = None
    
    def load_model(self):
        """Load flan-t5-small model for inference"""
        logger.info("Loading flan-t5-small model...")
        self.tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-small")
        self.model = T5ForConditionalGeneration.from_pretrained("google/flan-t5-small")
        logger.info("Flan-T5 model loaded successfully")
    
    def enrich_content(self, content: str) -> str:
        """Enrich syllabus content by inferring related subtopics"""
        if not self.model or not self.tokenizer:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Create prompt for subtopic inference
        prompt = f"List key subtopics for this syllabus content: {content}"
        
        # Tokenize and generate
        inputs = self.tokenizer(prompt, return_tensors="pt", max_length=512, truncation=True)
        
        outputs = self.model.generate(
            inputs.input_ids,
            max_length=150,
            num_return_sequences=1,
            temperature=0.7,
            do_sample=True
        )
        
        # Decode response
        enriched = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Combine original content with enriched subtopics
        combined_content = f"{content} | Subtopics: {enriched}"
        logger.debug(f"Enriched content generated for: {content[:50]}...")
        
        return combined_content