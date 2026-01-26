from sentence_transformers import SentenceTransformer
import numpy as np
import logging

logger = logging.getLogger(__name__)

class EmbeddingTool:
    """Generates embeddings using intfloat/e5-small-v2"""
    
    def __init__(self):
        self.model = None
    
    def load_model(self):
        """Load e5-small-v2 embedding model"""
        logger.info("Loading e5-small-v2 embedding model...")
        self.model = SentenceTransformer('intfloat/e5-small-v2')
        logger.info("Embedding model loaded successfully")
    
    def generate_embeddings(self, texts: list) -> np.ndarray:
        """Generate embeddings for list of texts"""
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        # Add query prefix for e5 model (recommended by model authors)
        prefixed_texts = [f"query: {text}" for text in texts]
        
        embeddings = self.model.encode(prefixed_texts, convert_to_numpy=True, normalize_embeddings=True)
        logger.debug(f"Generated embeddings for {len(texts)} texts")
        
        return embeddings