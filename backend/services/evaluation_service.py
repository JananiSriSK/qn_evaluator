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
        
        # Bi-encoder: score all topics
        question_emb = embedder.encode([question], convert_to_numpy=True, show_progress_bar=False)
        topic_texts = [t["topic_text"] for t in all_topics]
        topic_embs = embedder.encode(topic_texts, convert_to_numpy=True, show_progress_bar=False)
        
        question_norm = question_emb / np.linalg.norm(question_emb, axis=1, keepdims=True)
        topic_norms = topic_embs / np.linalg.norm(topic_embs, axis=1, keepdims=True)
        bi_scores = np.dot(question_norm, topic_norms.T)[0]  # cosine similarity for all topics
        
        # Cross-encoder: rerank top 10 candidates
        top_indices = np.argsort(bi_scores)[-10:][::-1]
        candidates = [all_topics[i] for i in top_indices]
        candidate_bi_scores = np.array([float(bi_scores[i]) for i in top_indices])
        
        pairs = [(question, c["topic_text"]) for c in candidates]
        cross_encoder.model.eval()
        with torch.no_grad():
            scores = cross_encoder.predict(pairs, convert_to_numpy=False, show_progress_bar=False)
            raw_logits = torch.tensor(scores) if not isinstance(scores, torch.Tensor) else scores
            sigmoid_probs = torch.sigmoid(raw_logits).cpu().numpy()
        
        # Normalize both scores to [0,1] range then blend
        bi_min, bi_max = candidate_bi_scores.min(), candidate_bi_scores.max()
        bi_norm = (candidate_bi_scores - bi_min) / (bi_max - bi_min + 1e-9)
        ce_min, ce_max = sigmoid_probs.min(), sigmoid_probs.max()
        ce_norm = (sigmoid_probs - ce_min) / (ce_max - ce_min + 1e-9)
        
        # Weight: if cross-encoder has meaningful spread (> 0.1), use 50/50; else trust bi-encoder more
        ce_spread = float(ce_max - ce_min)
        ce_weight = 0.5 if ce_spread > 0.1 else 0.2
        combined = ce_weight * ce_norm + (1 - ce_weight) * bi_norm
        
        sorted_indices = np.argsort(combined)[::-1]
        best_idx = sorted_indices[0]
        best_score = float(combined[best_idx])
        second_score = float(combined[sorted_indices[1]]) if len(sorted_indices) > 1 else 0.0
        score_margin = best_score - second_score
        
        # Use bi-encoder cosine similarity as the meaningful confidence metric
        best_bi_score = float(candidate_bi_scores[best_idx])  # raw cosine similarity [0,1]
        
        logger.info(f"Question: '{question}'")
        logger.info(f"Top 10 topics: {[c['topic_name'] for c in candidates]}")
        logger.info(f"Bi-encoder scores: {candidate_bi_scores.tolist()}")
        logger.info(f"Sigmoid probs: {sigmoid_probs.tolist()}, spread={ce_spread:.3f}")
        logger.info(f"Combined scores: {combined.tolist()}")
        logger.info(f"Best match: {candidates[best_idx]['topic_name']} (bi={best_bi_score:.3f}, margin={score_margin:.3f})")
        
        # Accept if bi-encoder cosine similarity is reasonable (> 0.2) or margin is clear
        accepted = best_bi_score >= 0.2 or score_margin >= 0.05
        
        if not accepted:
            logger.warning(f"REJECTED: bi_score={best_bi_score:.3f} < 0.2, margin={score_margin:.3f} < 0.05")
            return None, None, best_bi_score, score_margin
        
        best_topic = candidates[best_idx]
        logger.info(f"ACCEPTED: '{best_topic['topic_name']}' (bi={best_bi_score:.3f})")
        
        return best_topic, best_topic["unit_number"], best_bi_score, score_margin
    
    def map_to_syllabus(self, user_id, domain_name, question, top_chunks):
        """Map question to syllabus topic using topic-first classification"""
        syllabus = self.domain_manager.load_syllabus(user_id, domain_name)
        
        if not syllabus:
            return None
        
        # Global topic selection with cross-encoder
        best_topic, best_unit_num, confidence, dominance_ratio = self.select_best_topic_global(question, syllabus)
        
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
        
        cos = syllabus.get("course_outcomes", {})
        course_outcomes, co_confidence = self._match_cos(
            question, best_topic, cos,
            unit_number=best_topic["unit_number"],
            syllabus=syllabus,
        )

        # topic_confidence: bi-encoder cosine similarity boosted slightly by margin
        display_confidence = round(min(confidence + dominance_ratio * 0.3, 1.0), 3)

        return {
            "unit": best_topic["unit_number"],
            "unit_title": best_topic["unit_title"],
            "topic": best_topic["topic_name"],
            "topic_confidence": display_confidence,
            "course_outcomes": course_outcomes,
            "co_confidence": round(co_confidence, 3),
            "subtopics": best_topic["topic_data"].get("enriched_subtopics_from_books", [])[:5],
            "out_of_syllabus": False
        }
    

    
    def _match_cos(self, question, best_topic, cos: dict, unit_number: str = None, syllabus: dict = None):
        """Match question+topic to a CO using enriched descriptions and unit-constrained candidates.
        Returns ([best_co_key], similarity_score)."""
        if not cos:
            return [], 0.0

        embedder = model_registry.get_bi_encoder()

        # ── Build query ───────────────────────────────────────────────────────
        subtopics = best_topic["topic_data"].get("enriched_subtopics_from_books", [])
        query = question + ". " + best_topic["topic_name"]
        if subtopics:
            query += ". " + " ".join(subtopics[:5])

        # ── Build enriched CO descriptions from syllabus topics ───────────────
        # For each CO, append the topic names of its mapped unit so the
        # embedding space is grounded in concrete syllabus vocabulary.
        unit_topics_map: dict = {}   # unit_number → list of topic names
        if syllabus:
            for u in syllabus.get("units", []):
                unit_topics_map[u["unit_number"]] = [
                    t["topic_name"] for t in u.get("topics", [])
                ]

        # Build positional CO→unit map from syllabus order
        unit_list = [u["unit_number"] for u in (syllabus or {}).get("units", [])]
        co_unit_map = {f"CO{i+1}": unit_list[i] for i in range(len(unit_list))}

        co_keys = list(cos.keys())
        co_texts = []
        for k in co_keys:
            desc   = cos[k]
            mapped = co_unit_map.get(k, "")
            topics = unit_topics_map.get(mapped, [])
            # Append up to 8 topic keywords to the CO description
            enriched = desc + (" " + " ".join(topics[:8]) if topics else "")
            co_texts.append(enriched)

        # ── Unit-constrained candidate filtering ──────────────────────────────
        # Only consider COs whose mapped unit matches the predicted unit.
        # If that yields no candidates (e.g. more COs than units), fall back
        # to all COs.
        if unit_number and co_unit_map:
            candidate_indices = [
                i for i, k in enumerate(co_keys)
                if co_unit_map.get(k) == unit_number
            ]
        else:
            candidate_indices = list(range(len(co_keys)))

        if not candidate_indices:
            candidate_indices = list(range(len(co_keys)))

        # ── Semantic similarity within candidates ─────────────────────────────
        q_emb  = embedder.encode([query],    convert_to_numpy=True, show_progress_bar=False)
        c_embs = embedder.encode(co_texts,   convert_to_numpy=True, show_progress_bar=False)

        q_norm = q_emb  / np.linalg.norm(q_emb,  axis=1, keepdims=True)
        c_norm = c_embs / np.linalg.norm(c_embs, axis=1, keepdims=True)
        all_sims = np.dot(q_norm, c_norm.T)[0]

        # Restrict to candidate indices
        cand_sims = [(i, float(all_sims[i])) for i in candidate_indices]
        cand_sims.sort(key=lambda x: -x[1])

        best_idx  = cand_sims[0][0]
        best_sim  = cand_sims[0][1]
        second_sim = cand_sims[1][1] if len(cand_sims) > 1 else 0.0
        margin    = best_sim - second_sim

        logger.info(f"CO matching — unit={unit_number}, candidates={[co_keys[i] for i in candidate_indices]}")
        logger.info(f"CO sims: { {co_keys[i]: round(s,3) for i,s in cand_sims} }")
        logger.info(f"Best CO: {co_keys[best_idx]} (sim={best_sim:.3f}, margin={margin:.3f})")

        # ── Margin gating: if scores too close, trust unit mapping directly ───
        if margin < 0.03 and unit_number and co_unit_map:
            # Fall back to the CO that directly maps to this unit
            fallback = next((k for k, v in co_unit_map.items() if v == unit_number), None)
            if fallback and fallback in co_keys:
                logger.info(f"CO margin too small ({margin:.3f}) — falling back to unit-mapped CO: {fallback}")
                return [fallback], best_sim

        return [co_keys[best_idx]], best_sim

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
                "topic_confidence": syllabus_match.get("topic_confidence", 0),
                "course_outcomes": syllabus_match.get("course_outcomes", []),
                "co_confidence": syllabus_match.get("co_confidence", 0),
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
