from pymongo import MongoClient
from gridfs import GridFS
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class MongoDBStorage:
    """Store all user data in MongoDB instead of local files"""
    
    def __init__(self, uri="mongodb://localhost:27017/", db_name="qn_evaluator"):
        self.client = MongoClient(uri)
        self.db = self.client[db_name]
        self.fs = GridFS(self.db)  # For storing large files (books, FAISS indexes)
        
        # Collections
        self.users = self.db.users
        self.domains = self.db.domains
        self.syllabus = self.db.syllabus
        self.books = self.db.books
        self.indexes = self.db.indexes
        self.history = self.db.history
    
    # ============ SYLLABUS ============
    
    def save_syllabus(self, user_id: str, domain_name: str, syllabus_data: dict, original_file: bytes = None, filename: str = None):
        """Save syllabus JSON and original file"""
        doc = {
            "user_id": user_id,
            "domain_name": domain_name,
            "syllabus_data": syllabus_data,
            "updated_at": datetime.utcnow()
        }
        
        # Store original file in GridFS if provided
        if original_file and filename:
            file_id = self.fs.put(original_file, filename=filename, user_id=user_id, domain_name=domain_name)
            doc["original_file_id"] = file_id
            doc["original_filename"] = filename
        
        result = self.syllabus.update_one(
            {"user_id": user_id, "domain_name": domain_name},
            {"$set": doc},
            upsert=True
        )
        
        if not result.acknowledged:
            logger.error(f"MongoDB write failed → collection=syllabus, user_id={user_id}, domain={domain_name}")
            raise RuntimeError("Failed to save syllabus to MongoDB")
        
        logger.info(f"MongoDB write → collection=syllabus, user_id={user_id}, domain={domain_name}")
    
    def get_syllabus(self, user_id: str, domain_name: str):
        """Get syllabus JSON"""
        doc = self.syllabus.find_one({"user_id": user_id, "domain_name": domain_name})
        return doc["syllabus_data"] if doc else None
    
    def get_syllabus_file(self, user_id: str, domain_name: str):
        """Get original syllabus file"""
        doc = self.syllabus.find_one({"user_id": user_id, "domain_name": domain_name})
        if doc and "original_file_id" in doc:
            file = self.fs.get(doc["original_file_id"])
            return file.read(), doc["original_filename"]
        return None, None
    
    def delete_syllabus(self, user_id: str, domain_name: str):
        """Delete syllabus"""
        doc = self.syllabus.find_one({"user_id": user_id, "domain_name": domain_name})
        if doc and "original_file_id" in doc:
            self.fs.delete(doc["original_file_id"])
        self.syllabus.delete_one({"user_id": user_id, "domain_name": domain_name})
    
    # ============ BOOKS ============
    
    def save_book(self, user_id: str, domain_name: str, book_file: bytes, filename: str):
        """Save book PDF to GridFS"""
        file_id = self.fs.put(book_file, filename=filename, user_id=user_id, domain_name=domain_name, type="book")
        
        result = self.books.insert_one({
            "user_id": user_id,
            "domain_name": domain_name,
            "filename": filename,
            "file_id": file_id,
            "uploaded_at": datetime.utcnow()
        })
        
        if not result.acknowledged:
            logger.error(f"MongoDB write failed → collection=books, user_id={user_id}, domain={domain_name}, file={filename}")
            raise RuntimeError("Failed to save book to MongoDB")
        
        logger.info(f"MongoDB write → collection=books, user_id={user_id}, domain={domain_name}, file={filename}")
        return file_id
    
    def get_book(self, user_id: str, domain_name: str, filename: str):
        """Get book PDF"""
        doc = self.books.find_one({"user_id": user_id, "domain_name": domain_name, "filename": filename})
        if doc:
            file = self.fs.get(doc["file_id"])
            return file.read()
        return None
    
    def list_books(self, user_id: str, domain_name: str):
        """List all books for domain"""
        return [doc["filename"] for doc in self.books.find({"user_id": user_id, "domain_name": domain_name})]
    
    def delete_book(self, user_id: str, domain_name: str, filename: str):
        """Delete book"""
        doc = self.books.find_one({"user_id": user_id, "domain_name": domain_name, "filename": filename})
        if doc:
            self.fs.delete(doc["file_id"])
            self.books.delete_one({"_id": doc["_id"]})
    
    # ============ FAISS INDEX ============
    
    def save_index(self, user_id: str, domain_name: str, index_bytes: bytes, metadata: list):
        """Save FAISS index and metadata"""
        # Store index in GridFS
        file_id = self.fs.put(index_bytes, filename="faiss_index.bin", user_id=user_id, domain_name=domain_name, type="index")
        
        result = self.indexes.update_one(
            {"user_id": user_id, "domain_name": domain_name},
            {"$set": {
                "file_id": file_id,
                "metadata": metadata,
                "chunks_count": len(metadata),
                "updated_at": datetime.utcnow()
            }},
            upsert=True
        )
        
        if not result.acknowledged:
            logger.error(f"MongoDB write failed → collection=indexes, user_id={user_id}, domain={domain_name}")
            raise RuntimeError("Failed to save index to MongoDB")
        
        logger.info(f"MongoDB write → collection=indexes, user_id={user_id}, domain={domain_name}, chunks={len(metadata)}")
    
    def get_index(self, user_id: str, domain_name: str):
        """Get FAISS index and metadata"""
        doc = self.indexes.find_one({"user_id": user_id, "domain_name": domain_name})
        if doc:
            file = self.fs.get(doc["file_id"])
            return file.read(), doc["metadata"]
        return None, None
    
    def delete_index(self, user_id: str, domain_name: str):
        """Delete FAISS index"""
        doc = self.indexes.find_one({"user_id": user_id, "domain_name": domain_name})
        if doc:
            self.fs.delete(doc["file_id"])
            self.indexes.delete_one({"_id": doc["_id"]})
    
    # ============ DOMAINS ============
    
    def list_domains(self, user_id: str):
        """List all domains for user"""
        return list(self.domains.distinct("domain_name", {"user_id": user_id}))
    
    def create_domain(self, user_id: str, domain_name: str):
        """Create domain entry"""
        domain_name = domain_name.strip()
        
        result = self.domains.update_one(
            {"user_id": user_id, "domain_name": domain_name},
            {"$set": {"created_at": datetime.utcnow()}},
            upsert=True
        )
        
        if not result.acknowledged:
            logger.error(f"MongoDB write failed → collection=domains, user_id={user_id}, domain={domain_name}")
            raise RuntimeError("Failed to create domain in MongoDB")
        
        logger.info(f"MongoDB write → collection=domains, user_id={user_id}, domain={domain_name}")
    
    def delete_domain(self, user_id: str, domain_name: str):
        """Delete entire domain"""
        # Delete syllabus
        self.delete_syllabus(user_id, domain_name)
        
        # Delete books
        for filename in self.list_books(user_id, domain_name):
            self.delete_book(user_id, domain_name, filename)
        
        # Delete index
        self.delete_index(user_id, domain_name)
        
        # Delete domain entry
        self.domains.delete_one({"user_id": user_id, "domain_name": domain_name})
    
    def get_domain_status(self, user_id: str, domain_name: str):
        """Get domain status"""
        syllabus_doc = self.syllabus.find_one({"user_id": user_id, "domain_name": domain_name})
        index_doc = self.indexes.find_one({"user_id": user_id, "domain_name": domain_name})
        books = self.list_books(user_id, domain_name)
        
        return {
            "syllabus_uploaded": syllabus_doc is not None,
            "syllabus_file": syllabus_doc.get("original_filename") if syllabus_doc else None,
            "books_uploaded": len(books) > 0,
            "books": books,
            "index_ready": index_doc is not None,
            "chunks_count": index_doc.get("chunks_count", 0) if index_doc else 0
        }
    
    # ============ HISTORY ============
    
    def save_history(self, user_id: str, history_data: dict):
        """Save evaluation history"""
        self.history.update_one(
            {"user_id": user_id},
            {"$set": {"data": history_data, "updated_at": datetime.utcnow()}},
            upsert=True
        )
    
    def get_history(self, user_id: str):
        """Get evaluation history"""
        doc = self.history.find_one({"user_id": user_id})
        return doc["data"] if doc else {"single_questions": [], "pdf_evaluations": []}
