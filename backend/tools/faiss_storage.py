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
        self.course_domain_embeddings = {}  # Store course domain embeddings
        
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
        
        # Ensure FAISS-compatible format
        embeddings = np.asarray(embeddings, dtype=np.float32)
        embeddings = np.ascontiguousarray(embeddings)
        
        # Defensive assertions
        assert embeddings.dtype == np.float32
        assert embeddings.ndim == 2
        assert embeddings.flags['C_CONTIGUOUS']
        
        # Manual normalization to avoid FAISS issues
        for i in range(len(embeddings)):
            norm = np.linalg.norm(embeddings[i])
            if norm > 1e-8:
                embeddings[i] = embeddings[i] / norm
        
        # Add to index without FAISS normalization
        self.index.add(embeddings)
        
        # Store metadata
        self.metadata.extend(metadata_list)
        
        logger.info(f"Added {len(embeddings)} embeddings to FAISS index")
    
    def store_course_domain_embedding(self, course_name: str, domain_embedding: np.ndarray):
        """Store course domain embedding for semantic gate validation"""
        self.course_domain_embeddings[course_name] = domain_embedding
    
    def get_course_domain_embedding(self, course_name: str) -> np.ndarray:
        """Get course domain embedding for semantic gate validation"""
        return self.course_domain_embeddings.get(course_name, None)
    
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
        
        # Save course domain embedding
        domain_embedding_path = os.path.join(self.storage_path, f"{clean_course_name}_domain.npy")
        if course_name in self.course_domain_embeddings:
            np.save(domain_embedding_path, self.course_domain_embeddings[course_name])
            logger.info(f"Saved course domain embedding for: {course_name}")
        
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
            
            # Load course domain embedding
            domain_embedding_path = os.path.join(self.storage_path, f"{clean_course_name}_domain.npy")
            if os.path.exists(domain_embedding_path):
                self.course_domain_embeddings[course_name] = np.load(domain_embedding_path)
                logger.info(f"Loaded course domain embedding for: {course_name}")
            
            logger.info(f"Loaded existing index for course: {course_name}")
            return True
        return False
    
    def search_similar(self, query_embedding: np.ndarray, course_name: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search for similar vectors in course-specific FAISS index
        STRICT course isolation - NO cross-course contamination allowed
        """
        # STRICT course scoping: load ONLY the specified course index
        if not self.load_index(course_name):
            logger.warning(f"STRICT ISOLATION: No FAISS index found for course: {course_name}")
            return []  # Return empty for out-of-syllabus detection
        
        if self.index is None or len(self.metadata) == 0:
            logger.warning(f"STRICT ISOLATION: Empty FAISS index for course: {course_name}")
            return []  # Return empty for out-of-syllabus detection
        
        # VALIDATE: All metadata belongs to this course only
        for i, meta in enumerate(self.metadata):
            if meta.get("course_name", "").strip() != course_name.strip():
                logger.error(f"COURSE CONTAMINATION DETECTED: Index for '{course_name}' contains data from '{meta.get('course_name')}'")
                raise ValueError(f"Course isolation violated: {course_name} index contaminated")
        
        # Manual normalization for query embedding
        query_embedding = query_embedding.reshape(1, -1).astype(np.float32)
        norm = np.linalg.norm(query_embedding)
        if norm > 1e-8:
            query_embedding = query_embedding / norm
        
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