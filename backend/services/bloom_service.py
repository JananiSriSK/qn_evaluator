import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
from pathlib import Path


class BloomService:
    """Bloom Taxonomy Level Classifier"""
    
    _instance = None
    _model = None
    _tokenizer = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if self._model is None:
            self.load_model()
    
    def load_model(self):
        """Load Bloom model once at startup"""
        # Try multiple possible paths
        possible_paths = [
            Path("bloom/bloom_model_final/content/final_bloom_model"),
            Path("backend/bloom/bloom_model_final/content/final_bloom_model"),
            Path("bloom/bloom_models/content/final_bloom_model")
        ]
        
        model_path = None
        for path in possible_paths:
            if path.exists():
                model_path = path
                break
        
        if model_path is None:
            raise FileNotFoundError(f"Bloom model not found. Tried: {possible_paths}")
        
        self._tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        self._model = AutoModelForSequenceClassification.from_pretrained(str(model_path))
        self._model.eval()
        
        # Label mapping
        self.label_map = {
            0: "BT1",  # Remember
            1: "BT2",  # Understand
            2: "BT3",  # Apply
            3: "BT4",  # Analyze
            4: "BT5",  # Evaluate
            5: "BT6"   # Create
        }
    
    def predict_bloom(self, question_text):
        """Predict Bloom taxonomy level for question"""
        if self._model is None or self._tokenizer is None:
            self.load_model()
        
        # Tokenize
        inputs = self._tokenizer(
            question_text,
            return_tensors="pt",
            truncation=True,
            max_length=512,
            padding=True
        )
        
        # Predict
        with torch.no_grad():
            outputs = self._model(**inputs)
            logits = outputs.logits
            predicted_class = torch.argmax(logits, dim=1).item()
        
        bloom_level = self.label_map.get(predicted_class, "BT3")
        
        return {
            "bloom_level": bloom_level,
            "confidence": torch.softmax(logits, dim=1)[0][predicted_class].item()
        }


# Singleton instance
bloom_service = BloomService()
