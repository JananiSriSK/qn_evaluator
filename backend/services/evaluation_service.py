from .retrieval_service import RetrievalService
from .model_registry import model_registry
from .domain_manager import DomainManager
import numpy as np
import torch
import logging
import re
import unicodedata

logger = logging.getLogger(__name__)

# Relative rank-based gating thresholds
MARGIN_THRESHOLD = 0.05
MIN_PROB_THRESHOLD = 0.01
DOMINANCE_RATIO = 1.5


class EvaluationService:
    """Complete evaluation pipeline"""
    
    def __init__(self, base_path="data", mongo_storage=None):
        self.retrieval = RetrievalService(base_path, mongo_storage=mongo_storage)
        # Pass embedder and mongo_storage to domain manager
        embedder = model_registry.get_bi_encoder()
        self.domain_manager = DomainManager(base_path, embedder=embedder, mongo_storage=mongo_storage)
    
    @staticmethod
    def clean_question_text(question: str) -> str:
        """Unified preprocessing for both single and batch evaluation"""
        raw_question = question
        
        # Normalize Unicode
        question = unicodedata.normalize('NFKC', question)
        
        # Remove leading numbering: "3.", "16(a)", "Q.1", etc.
        question = re.sub(r'^\s*(?:Q\.?\s*)?\d+\s*[\.)\(]?\s*[a-z]?[\)]?\s+', '', question, flags=re.IGNORECASE)
        
        # Remove standalone (a), (b), (c) markers at start
        question = re.sub(r'^\s*\([a-z]\)\s+', '', question, flags=re.IGNORECASE)
        
        # Remove bullets
        question = re.sub(r'^\s*[•●○■□▪▫]\s+', '', question)
        
        # Remove marks patterns
        question = re.sub(r'\(\d+\s*[×x]\s*\d+\s*=\s*\d+\s*Marks?\)', '', question, flags=re.IGNORECASE)
        question = re.sub(r'\d+\s*Marks?\b', '', question, flags=re.IGNORECASE)
        
        # Remove Part A/B/C markers (at start and end)
        question = re.sub(r'^\s*Part\s+[A-C]\s*[:\-]?\s*', '', question, flags=re.IGNORECASE)
        question = re.sub(r'\s+Part\s+[A-C]\s*$', '', question, flags=re.IGNORECASE)
        
        # Collapse multiple spaces/newlines into single space
        question = re.sub(r'[\s\n\r]+', ' ', question)
        
        # Strip leading/trailing whitespace
        question = question.strip()
        
        logger.info(f"RAW QUESTION: '{raw_question}'")
        logger.info(f"CLEANED QUESTION: '{question}'")
        return question
    
    def select_best_topic_global(self, question, syllabus):
        """Select best topic using enriched subtopics for better matching"""
        embedder = model_registry.get_bi_encoder()
        cross_encoder = model_registry.get_cross_encoder()
        
        # Collect all topics with enriched text
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
        
        # Build enriched topic_text for cross-encoder
        for topic in all_topics:
            enriched = topic["topic_data"].get("enriched_subtopics_from_books", [])
            if enriched:
                topic["topic_text"] = topic["topic_name"] + ". " + " ".join(enriched)
            else:
                topic["topic_text"] = topic["topic_name"]
        
        # Bi-encoder: get top 10 candidates
        question_emb = embedder.encode([question], convert_to_numpy=True, show_progress_bar=False)
        topic_texts = [t["topic_text"] for t in all_topics]
        topic_embs = embedder.encode(topic_texts, convert_to_numpy=True, show_progress_bar=False)
        
        question_norm = question_emb / np.linalg.norm(question_emb, axis=1, keepdims=True)
        topic_norms = topic_embs / np.linalg.norm(topic_embs, axis=1, keepdims=True)
        similarities = np.dot(question_norm, topic_norms.T)[0]
        
        top_indices = np.argsort(similarities)[-10:][::-1]
        candidates = [all_topics[i] for i in top_indices]
        
        # Cross-encoder: rerank with relative rank-based gating
        pairs = [(question, c["topic_text"]) for c in candidates]
        
        cross_encoder.model.eval()
        with torch.no_grad():
            scores = cross_encoder.predict(pairs, convert_to_numpy=False, show_progress_bar=False)
            raw_logits = torch.tensor(scores) if not isinstance(scores, torch.Tensor) else scores
            sigmoid_probs = torch.sigmoid(raw_logits).cpu().numpy()
        
        sorted_indices = np.argsort(sigmoid_probs)[::-1]
        best_idx = sorted_indices[0]
        best_prob = float(sigmoid_probs[best_idx])
        second_best_prob = float(sigmoid_probs[sorted_indices[1]]) if len(sorted_indices) > 1 else 0.0
        prob_margin = best_prob - second_best_prob
        mean_prob = float(np.mean(sigmoid_probs))
        dominance_ratio = best_prob / mean_prob if mean_prob > 0 else 0.0
        
        # Relative rank-based acceptance
        if prob_margin >= MARGIN_THRESHOLD:
            decision_reason = "margin"
            accepted = True
        elif dominance_ratio >= DOMINANCE_RATIO:
            decision_reason = "dominance"
            accepted = True
        elif best_idx < 3:
            decision_reason = "retrieval_support"
            accepted = True
        elif best_prob < MIN_PROB_THRESHOLD:
            decision_reason = "rejected"
            accepted = False
        else:
            decision_reason = "weak_accept"
            accepted = True
        
        logger.info(f"Question: '{question}'")
        logger.info(f"Top 10 topics: {[c['topic_name'] for c in candidates]}")
        logger.info(f"Raw logits: {raw_logits.cpu().numpy().tolist()}")
        logger.info(f"Sigmoid probs: {sigmoid_probs.tolist()}")
        logger.info(f"Best match: {candidates[best_idx]['topic_name']} (prob: {best_prob:.3f})")
        logger.info(f"Second best prob: {second_best_prob:.3f}, Margin: {prob_margin:.3f}")
        logger.info(f"Mean prob: {mean_prob:.3f}, Dominance ratio: {dominance_ratio:.2f}")
        logger.info(f"Decision: {decision_reason} (accepted={accepted})")
        
        if not accepted:
            logger.warning(f"REJECTED: margin={prob_margin:.3f} < {MARGIN_THRESHOLD}, dominance={dominance_ratio:.2f} < {DOMINANCE_RATIO}, prob={best_prob:.3f} < {MIN_PROB_THRESHOLD}")
            return None, None, best_prob
        
        best_topic = candidates[best_idx]
        logger.info(f"ACCEPTED: Selected topic '{best_topic['topic_name']}' via {decision_reason}")
        
        return best_topic, best_topic["unit_number"], best_prob
    
    def map_to_syllabus(self, user_id, domain_name, question, top_chunks):
        """Map question to syllabus topic using topic-first classification"""
        syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
        
        if not syllabus:
            return None
        
        # Global topic selection with cross-encoder
        best_topic, best_unit_num, confidence = self.select_best_topic_global(question, syllabus)
        
        if not best_topic:
            logger.warning(f"OUT OF SYLLABUS: confidence={confidence:.3f}")
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
        
        # 0. Clean question text (unified preprocessing)
        question = self.clean_question_text(question)
        logger.info(f"Evaluating cleaned question: '{question}'")
        
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
