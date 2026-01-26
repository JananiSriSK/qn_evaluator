import numpy as np
import logging
from typing import List, Dict, Any
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class UnitDensifier:
    """Densifies syllabus units with relevant book chunks"""
    
    def __init__(self, embedding_tool):
        self.embedding_tool = embedding_tool
        self.BOOK_UNIT_THRESHOLD = 0.4  # Minimum similarity to attach chunk to unit
        self.CHUNK_SIMILARITY_THRESHOLD = 0.8  # Threshold for clustering similar chunks
        self.SYLLABUS_WEIGHT = 0.7  # Weight for syllabus content
        self.BOOK_WEIGHT = 0.3  # Weight for book content
    
    def match_chunks_to_units(self, book_chunks: List[str], syllabus_units: List[Dict]) -> Dict[int, List[str]]:
        """Match book chunks to syllabus units with threshold filtering"""
        if not book_chunks or not syllabus_units:
            return {}
        
        # Generate embeddings
        chunk_embeddings = self.embedding_tool.generate_embeddings(book_chunks)
        unit_texts = [f"{unit['title']}: {unit['content']}" for unit in syllabus_units]
        unit_embeddings = self.embedding_tool.generate_embeddings(unit_texts)
        
        # Match chunks to units
        unit_chunks = {}
        for i, chunk_embedding in enumerate(chunk_embeddings):
            similarities = np.dot(unit_embeddings, chunk_embedding)
            best_unit_idx = np.argmax(similarities)
            best_similarity = similarities[best_unit_idx]
            
            # Only attach if similarity exceeds threshold
            if best_similarity >= self.BOOK_UNIT_THRESHOLD:
                unit_number = syllabus_units[best_unit_idx]['unit_number']
                if unit_number not in unit_chunks:
                    unit_chunks[unit_number] = []
                unit_chunks[unit_number].append(book_chunks[i])
                
                logger.debug(f"Attached chunk to unit {unit_number} (similarity: {best_similarity:.3f})")
        
        return unit_chunks
    
    def deduplicate_chunks(self, chunks: List[str]) -> List[str]:
        """Remove redundant chunks using clustering"""
        if len(chunks) <= 1:
            return chunks
        
        # Generate embeddings for chunks
        chunk_embeddings = self.embedding_tool.generate_embeddings(chunks)
        
        # Calculate similarity matrix
        similarity_matrix = cosine_similarity(chunk_embeddings)
        
        # Convert to distance matrix (1 - similarity)
        distance_matrix = 1 - similarity_matrix
        
        # Cluster similar chunks
        clustering = AgglomerativeClustering(
            n_clusters=None,
            distance_threshold=1 - self.CHUNK_SIMILARITY_THRESHOLD,
            linkage='average'
        )
        cluster_labels = clustering.fit_predict(distance_matrix)
        
        # Keep one representative from each cluster (closest to centroid)
        unique_chunks = []
        for cluster_id in np.unique(cluster_labels):
            cluster_indices = np.where(cluster_labels == cluster_id)[0]
            
            if len(cluster_indices) == 1:
                unique_chunks.append(chunks[cluster_indices[0]])
            else:
                # Find chunk closest to cluster centroid
                cluster_embeddings = chunk_embeddings[cluster_indices]
                centroid = np.mean(cluster_embeddings, axis=0)
                
                distances = [np.linalg.norm(emb - centroid) for emb in cluster_embeddings]
                closest_idx = cluster_indices[np.argmin(distances)]
                unique_chunks.append(chunks[closest_idx])
        
        logger.info(f"Deduplicated {len(chunks)} chunks to {len(unique_chunks)}")
        return unique_chunks
    
    def create_densified_embedding(self, syllabus_subtopics: List[str], book_chunks: List[str]) -> np.ndarray:
        """Create weighted combination of syllabus and book embeddings"""
        # Generate syllabus embedding (average of subtopics)
        if syllabus_subtopics:
            syllabus_embeddings = self.embedding_tool.generate_embeddings(syllabus_subtopics)
            syllabus_avg = np.mean(syllabus_embeddings, axis=0)
        else:
            syllabus_avg = np.zeros(384, dtype=np.float32)
        
        # Generate book embedding (average of chunks)
        if book_chunks:
            book_embeddings = self.embedding_tool.generate_embeddings(book_chunks)
            book_avg = np.mean(book_embeddings, axis=0)
        else:
            book_avg = np.zeros(384, dtype=np.float32)
        
        # Weighted combination
        densified_embedding = (
            self.SYLLABUS_WEIGHT * syllabus_avg + 
            self.BOOK_WEIGHT * book_avg
        )
        
        # Normalize
        norm = np.linalg.norm(densified_embedding)
        if norm > 0:
            densified_embedding = densified_embedding / norm
        
        # CRITICAL FIXES for FAISS compatibility
        densified_embedding = np.asarray(densified_embedding, dtype=np.float32)
        densified_embedding = np.ascontiguousarray(densified_embedding)
        
        return densified_embedding