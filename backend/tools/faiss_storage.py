import faiss
import numpy as np
import json
import os
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class FAISSStorage:
    """Handles FAISS vector storage and metadata management"""
    
    def __init__(self, storage_path: str):
        self.storage_path = storage_path
        self.index = None
        self.metadata = []
        self.dimension = 384  # e5-small-v2 embedding dimension
        self.course_outcomes = {}  # Store course outcomes separately
        
        # Ensure storage directory exists
        os.makedirs(storage_path, exist_ok=True)
    
    def initialize_index(self):
        """Initialize FAISS index for vector storage"""
        self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
        logger.info(f"FAISS index initialized with dimension {self.dimension}")
    
    def add_embeddings(self, embeddings: np.ndarray, metadata_list: List[Dict[str, Any]]):
        """Add embeddings and metadata to FAISS index"""
        if self.index is None:
            self.initialize_index()
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(embeddings)
        
        # Add to index
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(metadata_list)
        
        logger.info(f"Added {len(embeddings)} embeddings to FAISS index")
    
    def store_course_outcomes(self, course_name: str, course_outcomes: List[Any]):
        """Store course outcomes separately for CO selection"""
        self.course_outcomes[course_name] = course_outcomes
    
    def get_course_outcomes(self, course_name: str) -> List[Any]:
        """Get course outcomes for CO selection"""
        return self.course_outcomes.get(course_name, [])
    
    def save_index(self, course_name: str):
        """Save FAISS index and metadata to disk"""
        # Clean course name for file paths
        clean_course_name = course_name.strip()
        
        index_path = os.path.join(self.storage_path, f"{clean_course_name}_index.faiss")
        metadata_path = os.path.join(self.storage_path, f"{clean_course_name}_metadata.json")
        co_path = os.path.join(self.storage_path, f"{clean_course_name}_cos.json")
        
        # Save FAISS index
        faiss.write_index(self.index, index_path)
        
        # Save metadata
        with open(metadata_path, 'w') as f:
            json.dump(self.metadata, f, indent=2)
        
        # Save course outcomes
        cos_data = []
        if course_name in self.course_outcomes:
            for co in self.course_outcomes[course_name]:
                cos_data.append({"id": co.id, "description": co.description})
        with open(co_path, 'w') as f:
            json.dump(cos_data, f, indent=2)
        
        logger.info(f"FAISS index and metadata saved for course: {course_name}")
        logger.info(f"Saved {len(cos_data)} course outcomes to {co_path}")
    
    def load_index(self, course_name: str):
        """Load existing FAISS index and metadata"""
        # Clean course name for file paths
        clean_course_name = course_name.strip()
        
        index_path = os.path.join(self.storage_path, f"{clean_course_name}_index.faiss")
        metadata_path = os.path.join(self.storage_path, f"{clean_course_name}_metadata.json")
        co_path = os.path.join(self.storage_path, f"{clean_course_name}_cos.json")
        
        if os.path.exists(index_path) and os.path.exists(metadata_path):
            self.index = faiss.read_index(index_path)
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            # Load course outcomes
            if os.path.exists(co_path):
                with open(co_path, 'r') as f:
                    cos_data = json.load(f)
                    from models.schemas import CourseOutcome
                    self.course_outcomes[course_name] = [CourseOutcome(id=co["id"], description=co["description"]) for co in cos_data]
                    logger.info(f"Loaded {len(cos_data)} course outcomes for course: {course_name}")
            else:
                logger.warning(f"Course outcomes file not found: {co_path}")
            
            logger.info(f"Loaded existing index for course: {course_name}")
            return True
        return False
    
    def search_similar(self, query_embedding: np.ndarray, course_name: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in course-specific FAISS index
        Course scope is a hard boundary. No cross-course retrieval is allowed.
        """
        # Hard course scoping: load ONLY the specified course index
        if not self.load_index(course_name):
            logger.warning(f"Hard boundary enforced: No FAISS index found for course: {course_name}")
            return []  # Return empty for out-of-syllabus detection
        
        if self.index is None or len(self.metadata) == 0:
            logger.warning(f"Hard boundary enforced: Empty FAISS index for course: {course_name}")
            return []  # Return empty for out-of-syllabus detection
        
        # Normalize query embedding for cosine similarity
        query_embedding = query_embedding.reshape(1, -1)
        faiss.normalize_L2(query_embedding)
        
        # Search for k most similar vectors within this course only
        scores, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx != -1 and idx < len(self.metadata):  # Valid index
                results.append({
                    "score": float(score),
                    "metadata": self.metadata[idx]
                })
        
        logger.debug(f"Found {len(results)} similar vectors for course: {course_name}")
        return results