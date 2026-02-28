"""
History service for storing and retrieving evaluation history
"""

from datetime import datetime
import logging
from .history_repository import FileHistoryRepository

logger = logging.getLogger(__name__)


class HistoryService:
    """Manage evaluation history for users"""
    
    def __init__(self, repository=None, base_path="data"):
        self.repository = repository or FileHistoryRepository(base_path)
    
    def load_history(self, user_id):
        return self.repository.load_history(user_id)
    
    def save_history(self, user_id, history):
        self.repository.save_history(user_id, history)
    
    def add_single_question(self, user_id, domain_name, question, result):
        """Add single question evaluation to history"""
        history = self.load_history(user_id)
        
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().isoformat(),
            "domain_name": domain_name,
            "question": question,
            "unit": result.get("unit"),
            "unit_title": result.get("unit_title"),
            "topic": result.get("topic"),
            "bloom_level": result.get("bloom_level"),
            "course_outcomes": result.get("course_outcomes", []),
            "out_of_syllabus": result.get("out_of_syllabus", False)
        }
        
        history["single_questions"].insert(0, entry)
        history["single_questions"] = history["single_questions"][:100]
        
        self.save_history(user_id, history)
        return entry["id"]
    
    def add_pdf_evaluation(self, user_id, domain_name, filename, total_questions, results, pdf_path=None, docx_path=None):
        """Add PDF evaluation to history"""
        history = self.load_history(user_id)
        
        entry = {
            "id": datetime.now().strftime("%Y%m%d%H%M%S%f"),
            "timestamp": datetime.now().isoformat(),
            "domain_name": domain_name,
            "filename": filename,
            "total_questions": total_questions,
            "results": results,
            "pdf_report_path": pdf_path,
            "docx_report_path": docx_path
        }
        
        history["pdf_evaluations"].insert(0, entry)  # Most recent first
        
        # Keep only last 50 entries
        history["pdf_evaluations"] = history["pdf_evaluations"][:50]
        
        self.save_history(user_id, history)
        return entry["id"]
    
    def get_history(self, user_id):
        """Get user's complete history"""
        return self.load_history(user_id)
    
    def delete_single_question(self, user_id, question_id):
        """Delete a single question from history"""
        history = self.load_history(user_id)
        history["single_questions"] = [e for e in history["single_questions"] if e.get("id") != question_id]
        self.save_history(user_id, history)
        return True
    
    def delete_pdf_evaluation(self, user_id, eval_id):
        """Delete a PDF evaluation from history"""
        history = self.load_history(user_id)
        history["pdf_evaluations"] = [e for e in history["pdf_evaluations"] if e.get("id") != eval_id]
        self.save_history(user_id, history)
        return True
    
    def clear_all_history(self, user_id):
        """Clear all history for user"""
        self.save_history(user_id, {"single_questions": [], "pdf_evaluations": []})
        return True
