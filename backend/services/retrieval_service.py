import faiss
from .model_registry import model_registry
from .domain_manager import DomainManager


class RetrievalService:
    """FAISS-based retrieval service for domain-specific queries"""
    
    def __init__(self, base_path="data", mongo_storage=None):
        # Pass embedder and mongo_storage to domain manager
        embedder = model_registry.get_bi_encoder()
        self.domain_manager = DomainManager(base_path, embedder=embedder, mongo_storage=mongo_storage)
    
    def retrieve_candidates(self, user_id, domain_name, query, top_k=20):
        """Retrieve candidate chunks using FAISS"""
        index, metadata = self.domain_manager.load_index(user_id, domain_name)
        
        if index is None or metadata is None:
            return []
        
        # Use shared bi-encoder
        bi_encoder = model_registry.get_bi_encoder()
        embedding = bi_encoder.encode(
            [query],
            convert_to_numpy=True,
            show_progress_bar=False
        ).astype("float32")
        
        faiss.normalize_L2(embedding)
        
        # Search
        distances, indices = index.search(embedding, top_k)
        
        candidates = []
        for idx in indices[0]:
            if idx < len(metadata):
                candidates.append(metadata[idx])
        
        return candidates
    
    def rerank(self, query, candidates, final_k=10):
        """Rerank candidates using cross-encoder"""
        if not candidates:
            return []
        
        # Use shared cross-encoder
        cross_encoder = model_registry.get_cross_encoder()
        pairs = [(query, c["text"]) for c in candidates]
        scores = cross_encoder.predict(pairs)
        
        for i, score in enumerate(scores):
            candidates[i]["score"] = float(score)
        
        candidates.sort(key=lambda x: x["score"], reverse=True)
        
        return candidates[:final_k]
    
    def retrieve(self, user_id, domain_name, query, top_k=10):
        """Full retrieval pipeline"""
        candidates = self.retrieve_candidates(user_id, domain_name, query, top_k=30)
        return self.rerank(query, candidates, final_k=top_k)
