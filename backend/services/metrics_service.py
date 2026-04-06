import logging
import numpy as np
from typing import List, Dict
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

BLOOM_ORDER = ["BT1", "BT2", "BT3", "BT4", "BT5", "BT6"]
TOPIC_SIM_THRESHOLD = 0.7


class MetricsService:
    """Module 7: Evaluate pipeline accuracy using labeled ground truth data."""

    def __init__(self, evaluation_service):
        self.evaluation_service = evaluation_service

    @staticmethod
    def _bloom_strict(pred, true):
        try:    return int(pred[2]) == int(true[2])
        except: return pred.strip().upper() == true.strip().upper()

    @staticmethod
    def _bloom_relaxed(pred, true):
        try:    return abs(int(pred[2]) - int(true[2])) <= 1
        except: return pred.strip().upper() == true.strip().upper()

    @staticmethod
    def _topic_sim(pred, true, embedder):
        if not pred or not true:
            return False, 0.0
        e1 = embedder.encode([pred], convert_to_numpy=True, show_progress_bar=False)
        e2 = embedder.encode([true], convert_to_numpy=True, show_progress_bar=False)
        sim = float(cosine_similarity(e1, e2)[0][0])
        return sim >= TOPIC_SIM_THRESHOLD, round(sim, 4)

    @staticmethod
    def _f1(correct, total_pred, total_true):
        p = correct / total_pred if total_pred else 0.0
        r = correct / total_true if total_true else 0.0
        f = 2 * p * r / (p + r) if (p + r) else 0.0
        return round(p, 4), round(r, 4), round(f, 4)

    def run(self, user_id: str, domain_name: str, labeled_data: List[Dict]) -> Dict:
        total = len(labeled_data)
        if total == 0:
            return {"error": "Empty dataset"}

        from services.model_registry import model_registry
        embedder = model_registry.get_bi_encoder()

        b_strict = b_relaxed = t_correct = c_correct = 0
        topic_sims, bloom_confs = [], []
        details, errors = [], []

        for item in labeled_data:
            question   = item.get("question", "")
            true_topic = item.get("true_topic", "").strip()
            true_bloom = item.get("true_bloom", "").strip()
            true_co    = item.get("true_co", "").strip()

            try:
                res = self.evaluation_service.evaluate_question(user_id, domain_name, question)

                if res.get("error"):
                    raise ValueError(res["error"])

                pred_bloom = res.get("bloom_level", "")
                pred_topic = res.get("topic", "") or ""
                pred_co    = (res.get("course_outcomes") or [""])[0]
                bloom_conf = res.get("bloom_confidence")

                bs = self._bloom_strict(pred_bloom, true_bloom)  if true_bloom else False
                br = self._bloom_relaxed(pred_bloom, true_bloom) if true_bloom else False

                skip = not true_topic or not pred_topic or pred_topic.lower() == "out of syllabus"
                tc, tsim = (False, 0.0) if skip else self._topic_sim(pred_topic, true_topic, embedder)

                cc = pred_co.strip().upper() == true_co.strip().upper() if true_co else False

                if bs: b_strict  += 1
                if br: b_relaxed += 1
                if tc: t_correct += 1
                if cc: c_correct += 1

                topic_sims.append(tsim)
                if bloom_conf is not None:
                    bloom_confs.append(bloom_conf)

                details.append({
                    "question":          question[:100],
                    "true_bloom":        true_bloom,
                    "pred_bloom":        pred_bloom,
                    "bloom_correct":     br,
                    "bloom_strict":      bs,
                    "bloom_confidence":  bloom_conf,
                    "true_topic":        true_topic,
                    "pred_topic":        pred_topic,
                    "topic_similarity":  tsim,
                    "topic_correct":     tc,
                    "true_co":           true_co,
                    "pred_co":           pred_co,
                    "co_correct":        cc,
                })

            except Exception as e:
                logger.error(f"Error on '{question[:50]}': {e}")
                errors.append({"question": question[:80], "error": str(e)})

        n = (total - len(errors)) or 1

        # Precision / Recall / F1 (treating each question as a binary sample)
        bp, br_score, bf = self._f1(b_relaxed, n, n)   # bloom: pred=n, true=n (all have labels)
        tp, tr_score, tf = self._f1(t_correct, n, n)
        cp, cr_score, cf = self._f1(c_correct, n, n)

        sims = topic_sims or [0.0]

        report = {
            # ── flat summary so frontend can read directly ──
            "total_questions":        total,
            "evaluated":              n,

            # Accuracy
            "bloom_accuracy":         round(b_strict  / n, 4),
            "bloom_accuracy_relaxed": round(b_relaxed / n, 4),
            "topic_accuracy":         round(t_correct / n, 4),
            "co_accuracy":            round(c_correct / n, 4),

            # Similarity
            "avg_topic_similarity":   round(float(np.mean(sims)), 4),
            "min_topic_similarity":   round(float(np.min(sims)),  4),
            "max_topic_similarity":   round(float(np.max(sims)),  4),

            # Precision / Recall / F1
            "bloom_precision": bp,  "bloom_recall": br_score,  "bloom_f1": bf,
            "topic_precision": tp,  "topic_recall": tr_score,  "topic_f1": tf,
            "co_precision":    cp,  "co_recall":    cr_score,   "co_f1":   cf,

            # Counts
            "bloom_correct":   b_relaxed,  "bloom_incorrect": n - b_relaxed,
            "topic_correct":   t_correct,  "topic_incorrect": n - t_correct,
            "co_correct":      c_correct,  "co_incorrect":    n - c_correct,

            "details": details,
        }

        if bloom_confs:
            report["avg_bloom_confidence"] = round(float(np.mean(bloom_confs)), 4)
        if errors:
            report["errors"] = errors

        logger.info(f"Metrics done — bloom={report['bloom_accuracy_relaxed']}, topic={report['topic_accuracy']}, co={report['co_accuracy']}")
        return report
