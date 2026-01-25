import re
import logging

logger = logging.getLogger(__name__)

class TextPreprocessor:
    """Handles text normalization and cleaning"""
    
    def normalize_text(self, text: str) -> str:
        """Normalize text by cleaning and standardizing format"""
        # Remove extra whitespace and normalize
        text = re.sub(r'\s+', ' ', text.strip())
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s\.\,\;\:\-\(\)]', '', text)
        logger.debug(f"Normalized text: {text[:100]}...")
        return text
    
    def prepare_syllabus_content(self, unit_title: str, unit_content: str) -> str:
        """Prepare syllabus content for processing"""
        combined = f"{unit_title}: {unit_content}"
        return self.normalize_text(combined)