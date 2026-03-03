from pymongo import MongoClient
from datetime import datetime


class MongoDBHistoryRepository:
    """MongoDB-based history storage"""
    
    def __init__(self, uri="mongodb://localhost:27017/", db_name="qn_evaluator"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.history = self.db.history
    
    def load_history(self, user_id):
        """Load history from MongoDB"""
        doc = self.history.find_one({"user_id": user_id})
        if doc:
            return doc.get("data", {"single_questions": [], "pdf_evaluations": []})
        return {"single_questions": [], "pdf_evaluations": []}
    
    def save_history(self, user_id, history_data):
        """Save history to MongoDB"""
        self.history.update_one(
            {"user_id": user_id},
            {"$set": {"data": history_data, "updated_at": datetime.utcnow()}},
            upsert=True
        )
