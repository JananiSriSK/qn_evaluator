import logging

logger = logging.getLogger(__name__)


class DomainValidator:
    """Validate domain exists and is properly initialized using MongoDB"""
    
    @staticmethod
    def validate_domain(user_id: str, domain_name: str, base_path: str = "data", mongo_storage=None):
        if mongo_storage is None:
            # Import here to avoid circular imports
            from services.mongodb_storage import MongoDBStorage
            import os
            mongo_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")
            mongo_db = os.getenv("MONGODB_DB", "qn_evaluator")
            mongo_storage = MongoDBStorage(mongo_uri, mongo_db)
        
        # Check domain exists
        domains = mongo_storage.list_domains(user_id)
        if domain_name not in domains:
            logger.warning(f"Domain not found in MongoDB: {user_id}/{domain_name}")
            raise FileNotFoundError(f"Domain '{domain_name}' not found")
        
        # Check syllabus
        syllabus = mongo_storage.get_syllabus(user_id, domain_name)
        if not syllabus:
            logger.warning(f"Syllabus missing in MongoDB: {user_id}/{domain_name}")
            raise FileNotFoundError(f"syllabus.json not found")
        
        # Check FAISS index
        index_bytes, metadata = mongo_storage.get_index(user_id, domain_name)
        if not index_bytes:
            logger.warning(f"FAISS index missing in MongoDB: {user_id}/{domain_name}")
            raise FileNotFoundError(f"faiss_index.bin not found")
        
        logger.info(f"✓ Domain validated (MongoDB): {user_id}/{domain_name}")
        return True
