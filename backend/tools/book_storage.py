import logging
import numpy as np
import faiss
import json
import os
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class BookStorage:
    """Manages book chunks in separate FAISS indices"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.indices = {}  # course_name -> faiss index
        self.metadata = {}  # course_name -> list of metadata
    
    def add_book_chunks(self, course_name: str, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """Add book chunks to course-specific index"""
        if course_name not in self.indices:
            dimension = embeddings.shape[1]
            self.indices[course_name] = faiss.IndexFlatIP(dimension)
            self.metadata[course_name] = []
        
        # Ensure proper format and manual normalization
        embeddings = np.array(embeddings, dtype=np.float32)
        
        # Manual normalization to avoid FAISS issues
        for i in range(len(embeddings)):
            norm = np.linalg.norm(embeddings[i])
            if norm > 1e-8:
                embeddings[i] = embeddings[i] / norm
        
        # Add embeddings to index
        self.indices[course_name].add(embeddings)
        self.metadata[course_name].extend(metadata_list)
        
        logger.info(f"Added {len(embeddings)} book chunks for course: {course_name}")
    
    def get_all_chunks(self, course_name: str) -> List[str]:
        """Get all book chunks for a course"""
        if course_name not in self.metadata:
            return []
        return [meta["chunk_text"] for meta in self.metadata[course_name]]
    
    def save_book_index(self, course_name: str):
        """Save book index and metadata to disk"""
        if course_name not in self.indices:
            return
        
        # Save FAISS index
        index_path = os.path.join(self.storage_path, f"{course_name}_books.index")
        faiss.write_index(self.indices[course_name], index_path)
        
        # Save metadata
        metadata_path = os.path.join(self.storage_path, f"{course_name}_books_metadata.json")
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata[course_name], f, ensure_ascii=False, indent=2)
        
        logger.info(f"Saved book index for course: {course_name}")
    
    def load_book_index(self, course_name: str):
        """Load book index and metadata from disk"""
        index_path = os.path.join(self.storage_path, f"{course_name}_books.index")
        metadata_path = os.path.join(self.storage_path, f"{course_name}_books_metadata.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            # Load FAISS index
            self.indices[course_name] = faiss.read_index(index_path)
            
            # Load metadata
            with open(metadata_path, 'r', encoding='utf-8') as f:
                self.metadata[course_name] = json.load(f)
            
            logger.info(f"Loaded book index for course: {course_name}")
            return True
        
        return False