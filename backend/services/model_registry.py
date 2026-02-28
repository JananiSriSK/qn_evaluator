import logging
import torch
from pathlib import Path
from sentence_transformers import SentenceTransformer, CrossEncoder
from transformers import AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)


class ModelRegistry:
    """Singleton registry for all ML models - load once, use everywhere"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._bi_encoder = None
            self._cross_encoder = None
            self._bloom_model = None
            self._bloom_tokenizer = None
            self._bloom_labels = {
                0: "BT1", 1: "BT2", 2: "BT3",
                3: "BT4", 4: "BT5", 5: "BT6"
            }
            ModelRegistry._initialized = True
    
    def load_all_models(self):
        """Load all models at startup"""
        logger.info("Loading all models into registry...")
        
        # Load bi-encoder
        logger.info("Loading bi-encoder (all-MiniLM-L6-v2)...")
        self._bi_encoder = SentenceTransformer("all-MiniLM-L6-v2")
        
        # Load cross-encoder
        logger.info("Loading cross-encoder (ms-marco-MiniLM-L-6-v2)...")
        self._cross_encoder = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        
        # Load Bloom model
        logger.info("Loading Bloom taxonomy classifier...")
        self._load_bloom_model()
        
        logger.info("✓ All models loaded successfully")
    
    def _load_bloom_model(self):
        """Load Bloom model from local path"""
        possible_paths = [
            Path("bloom/bloom_model_final/content/final_bloom_model"),
            Path("bloom/bloom_models/content/final_bloom_model")
        ]
        
        model_path = None
        for path in possible_paths:
            if path.exists():
                model_path = path
                break
        
        if model_path is None:
            logger.warning(f"Bloom model not found. Tried: {possible_paths}")
            return
        
        self._bloom_tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self._bloom_model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        self._bloom_model.eval()
    
    def get_bi_encoder(self):
        """Get bi-encoder model"""
        if self._bi_encoder is None:
            raise RuntimeError("Models not loaded. Call load_all_models() first")
        return self._bi_encoder
    
    def get_cross_encoder(self):
        """Get cross-encoder model"""
        if self._cross_encoder is None:
            raise RuntimeError("Models not loaded. Call load_all_models() first")
        return self._cross_encoder
    
    def get_bloom_model(self):
        """Get Bloom model and tokenizer"""
        if self._bloom_model is None or self._bloom_tokenizer is None:
            raise RuntimeError("Bloom model not loaded")
        return self._bloom_model, self._bloom_tokenizer
    
    def predict_bloom(self, question_text):
        """Predict Bloom taxonomy level"""
        if self._bloom_model is None or self._bloom_tokenizer is None:
            return {"bloom_level": "BT3", "confidence": 0.5}
        
        inputs = self._bloom_tokenizer(
            question_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        with torch.no_grad():
            outputs = self._bloom_model(**inputs)
            logits = outputs.logits
            probs = torch.softmax(logits, dim=1)[0]
            predicted_class = torch.argmax(logits, dim=1).item()
            confidence = probs[predicted_class].item()
        
        return {
            "bloom_level": self._bloom_labels.get(predicted_class, "BT3"),
            "confidence": round(confidence, 3)
        }


# Global singleton instance
model_registry = ModelRegistry()
