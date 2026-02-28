from .retrieval_service import RetrievalService
from .model_registry import model_registry
from .domain_manager import DomainManager
import numpy as np
import logging

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD = 0.15


class EvaluationService:
    """Complete evaluation pipeline"""
    
    def __init__(self, base_path="data"):
        self.retrieval = RetrievalService(base_path)
        # Pass embedder from registry to domain manager
        embedder = model_registry.get_bi_encoder()
        self.domain_manager = DomainManager(base_path, embedder=embedder)
    
    def select_best_topic_global(self, question, syllabus):
        """Select best topic using simple cross-encoder scoring (no softmax)"""
        embedder = model_registry.get_bi_encoder()
        cross_encoder = model_registry.get_cross_encoder()
        
        # Collect all topics
        all_topics = []
        for unit in syllabus["units"]:
            for topic in unit["topics"]:
                all_topics.append({
                    "unit_number": unit["unit_number"],
                    "unit_title": unit["unit_title"],
                    "topic_name": topic["topic_name"],
                    "topic_data": topic
                })
        
        if not all_topics:
            return None, None, 0.0
        
        # Bi-encoder: get top 10 candidates
        question_emb = embedder.encode([question], convert_to_numpy=True, show_progress_bar=False)
        topic_texts = [t["topic_name"] for t in all_topics]
        topic_embs = embedder.encode(topic_texts, convert_to_numpy=True, show_progress_bar=False)
        
        question_norm = question_emb / np.linalg.norm(question_emb, axis=1, keepdims=True)
        topic_norms = topic_embs / np.linalg.norm(topic_embs, axis=1, keepdims=True)
        similarities = np.dot(question_norm, topic_norms.T)[0]
        
        top_indices = np.argsort(similarities)[-10:][::-1]
        candidates = [all_topics[i] for i in top_indices]
        
        # Cross-encoder: rerank (NO SOFTMAX)
        pairs = [(question, c["topic_name"]) for c in candidates]
        scores = cross_encoder.predict(pairs)
        
        best_idx = np.argmax(scores)
        best_score = float(scores[best_idx])
        
        logger.info(f"Top 10 topics: {[c['topic_name'] for c in candidates]}")
        logger.info(f"Cross-encoder scores: {scores.tolist()}")
        logger.info(f"Best score: {best_score:.3f}")
        
        if best_score < CONFIDENCE_THRESHOLD:
            logger.warning(f"Low confidence ({best_score:.3f}) - marking as out of syllabus")
            return None, None, best_score
        
        best_topic = candidates[best_idx]
        logger.info(f"Selected: {best_topic['topic_name']}")
        
        return best_topic, best_topic["unit_number"], best_score
    
    def map_to_syllabus(self, user_id, domain_name, question, top_chunks):
        """Map question to syllabus topic using topic-first classification"""
        syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
        
        if not syllabus:
            return None
        
        # Global topic selection with cross-encoder
        best_topic, best_unit_num, confidence = self.select_best_topic_global(question, syllabus)
        
        if not best_topic or confidence < CONFIDENCE_THRESHOLD:
            logger.warning(f"Out of syllabus: confidence={confidence:.3f}")
            return {
                "unit": None,
                "unit_title": None,
                "topic": "Out of Syllabus",
                "course_outcomes": [],
                "subtopics": [],
                "out_of_syllabus": True
            }
        
        # Map COs based on unit number
        unit_map = {"I": 1, "II": 2, "III": 3, "IV": 4, "V": 5, "VI": 6, "VII": 7, "VIII": 8}
        unit_int = unit_map.get(best_unit_num, 1)
        co_key = f"CO{unit_int}"
        cos = syllabus.get("course_outcomes", {})
        course_outcomes = [co_key] if co_key in cos else []
        
        return {
            "unit": best_topic["unit_number"],
            "unit_title": best_topic["unit_title"],
            "topic": best_topic["topic_name"],
            "course_outcomes": course_outcomes,
            "subtopics": best_topic["topic_data"].get("enriched_subtopics_from_books", [])[:5],
            "out_of_syllabus": False
        }
    

    
    def evaluate_question(self, user_id, domain_name, question):
        """Complete evaluation pipeline"""
        
        # 1. Retrieve relevant chunks
        chunks = self.retrieval.retrieve(user_id, domain_name, question, top_k=10)
        
        if not chunks:
            return {
                "error": "No relevant content found",
                "question": question
            }
        
        # 2. Map to syllabus
        syllabus_match = self.map_to_syllabus(user_id, domain_name, question, chunks)
        
        # 3. Predict Bloom level
        bloom_result = model_registry.predict_bloom(question)
        
        # 4. Build response
        result = {
            "question": question,
            "bloom_level": bloom_result["bloom_level"],
            "bloom_confidence": bloom_result["confidence"]
        }
        
        if syllabus_match:
            result.update({
                "unit": syllabus_match.get("unit"),
                "unit_title": syllabus_match.get("unit_title"),
                "topic": syllabus_match.get("topic"),
                "course_outcomes": syllabus_match.get("course_outcomes", []),
                "subtopics": syllabus_match.get("subtopics", []),
                "out_of_syllabus": syllabus_match.get("out_of_syllabus", False),
                "relevant_chunks": [
                    {
                        "book": chunk["book_name"],
                        "page": chunk["page"],
                        "text": chunk["text"][:200]
                    }
                    for chunk in chunks[:3]
                ]
            })
        else:
            result["warning"] = "Could not map to syllabus topic"
            result["relevant_chunks"] = [
                {
                    "book": chunk["book_name"],
                    "page": chunk["page"],
                    "text": chunk["text"][:200]
                }
                for chunk in chunks[:3]
            ]
        
        return result
