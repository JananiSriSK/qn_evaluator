"""
History repository abstraction supporting file-based and MongoDB storage
"""

import json
from pathlib import Path
from datetime import datetime
from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class HistoryRepository(ABC):
    """Abstract history storage interface"""
    
    @abstractmethod
    def load_history(self, user_id):
        pass
    
    @abstractmethod
    def save_history(self, user_id, history):
        pass


class FileHistoryRepository(HistoryRepository):
    """File-based history storage"""
    
    def __init__(self, base_path="data"):
        self.base_path = Path(base_path)
    
    def get_history_path(self, user_id):
        user_path = self.base_path / user_id
        user_path.mkdir(parents=True, exist_ok=True)
        return user_path / "history.json"
    
    def load_history(self, user_id):
        history_path = self.get_history_path(user_id)
        if not history_path.exists():
            return {"single_questions": [], "pdf_evaluations": []}
        try:
            with open(history_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading history: {e}")
            return {"single_questions": [], "pdf_evaluations": []}
    
    def save_history(self, user_id, history):
        history_path = self.get_history_path(user_id)
        try:
            with open(history_path, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving history: {e}")


class MongoHistoryRepository(HistoryRepository):
    """MongoDB-based history storage"""
    
    def __init__(self, connection_string="mongodb://localhost:27017/", db_name="question_intelligence"):
        try:
            from pymongo import MongoClient
            self.client = MongoClient(connection_string)
            self.db = self.client[db_name]
            self.collection = self.db.history
        except ImportError:
            logger.error("pymongo not installed. Install with: pip install pymongo")
            raise
        except Exception as e:
            logger.error(f"MongoDB connection failed: {e}")
            raise
    
    def load_history(self, user_id):
        try:
            doc = self.collection.find_one({"user_id": user_id})
            if doc:
                return {
                    "single_questions": doc.get("single_questions", []),
                    "pdf_evaluations": doc.get("pdf_evaluations", [])
                }
            return {"single_questions": [], "pdf_evaluations": []}
        except Exception as e:
            logger.error(f"Error loading history from MongoDB: {e}")
            return {"single_questions": [], "pdf_evaluations": []}
    
    def save_history(self, user_id, history):
        try:
            self.collection.update_one(
                {"user_id": user_id},
                {"$set": {
                    "user_id": user_id,
                    "single_questions": history.get("single_questions", []),
                    "pdf_evaluations": history.get("pdf_evaluations", []),
                    "updated_at": datetime.now().isoformat()
                }},
                upsert=True
            )
        except Exception as e:
            logger.error(f"Error saving history to MongoDB: {e}")
