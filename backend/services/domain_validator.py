from fastapi import HTTPException
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class DomainValidator:
    """Validate domain exists and is properly initialized"""
    
    @staticmethod
    def validate_domain(user_id: str, domain_name: str, base_path: str = "data"):
        """
        Validate domain has all required components
        Raises HTTPException if validation fails
        """
        domain_path = Path(base_path) / user_id / domain_name
        
        # Check domain exists
        if not domain_path.exists():
            logger.warning(f"Domain not found: {user_id}/{domain_name}")
            raise HTTPException(
                status_code=404,
                detail={
                    "error": "Domain not found",
                    "message": f"Domain '{domain_name}' does not exist for user '{user_id}'",
                    "action": "Create domain first using /api/domain/create"
                }
            )
        
        # Check syllabus
        syllabus_file = domain_path / "syllabus.json"
        if not syllabus_file.exists():
            logger.warning(f"Syllabus missing for: {user_id}/{domain_name}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Domain not initialized",
                    "message": "Syllabus file missing",
                    "action": "Upload syllabus using /api/domain/create"
                }
            )
        
        # Check vector database
        vector_db_path = domain_path / "vector_db"
        faiss_index = vector_db_path / "faiss_index.bin"
        metadata_file = vector_db_path / "metadata.json"
        
        if not faiss_index.exists() or not metadata_file.exists():
            logger.warning(f"Vector DB missing for: {user_id}/{domain_name}")
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Domain not initialized",
                    "message": "Vector database not built. Upload books first.",
                    "action": "Add books using /api/domain/add-books"
                }
            )
        
        logger.info(f"✓ Domain validated: {user_id}/{domain_name}")
        return True
