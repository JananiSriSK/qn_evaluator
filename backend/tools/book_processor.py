import logging
from typing import List, Dict, Any
import fitz  # PyMuPDF
import io
from transformers import AutoTokenizer

logger = logging.getLogger(__name__)

class BookProcessor:
    """Processes reference books for knowledge augmentation"""
    
    def __init__(self):
        self.tokenizer = None
    
    def load_tokenizer(self):
        """Load tokenizer for text chunking"""
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes"""
        try:
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text() + "\n"
            doc.close()
            return text.strip()
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            return ""
    
    def chunk_text(self, text: str, max_tokens: int = 512) -> List[str]:
        """Chunk text into manageable pieces"""
        if not self.tokenizer:
            self.load_tokenizer()
        
        # Split by paragraphs first
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        chunks = []
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Check if adding this paragraph exceeds token limit
            test_chunk = current_chunk + "\n\n" + paragraph if current_chunk else paragraph
            tokens = self.tokenizer.encode(test_chunk, add_special_tokens=False)
            
            if len(tokens) <= max_tokens:
                current_chunk = test_chunk
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk)
                current_chunk = paragraph
        
        # Add final chunk
        if current_chunk:
            chunks.append(current_chunk)
        
        return chunks