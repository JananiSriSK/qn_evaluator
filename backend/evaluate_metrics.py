"""
CLI Metrics Evaluator — full diagnostic output for developers.
Usage:
    python evaluate_metrics.py --user_id 1 --domain JAVA_PROGRAMMING --file labeled.json
"""
import argparse
import json
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))


def main():
    parser = argparse.ArgumentParser(description="Full pipeline metrics evaluation")
    parser.add_argument("--user_id",  required=True)
    parser.add_argument("--domain",   required=True)
    parser.add_argument("--file",     required=True, help="Path to labeled JSON dataset")
    args = parser.parse_args()

    with open(args.file) as f:
        labeled_data = json.load(f)

    print(f"\n{'='*60}")
    print(f"  Question Intelligence System — Pipeline Metrics")
    print(f"{'='*60}")
    print(f"  User:    {args.user_id}")
    print(f"  Domain:  {args.domain}")
    print(f"  Dataset: {len(labeled_data)} questions")
    print(f"{'='*60}\n")

    # Bootstrap services
    from dotenv import load_dotenv
    load_dotenv()
    from services.model_registry import model_registry
    model_registry.load_all_models()

    from services.mongodb_storage import MongoDBStorage
    mongo = MongoDBStorage(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        os.getenv("MONGODB_DB", "qn_evaluator")
    )
    from services.evaluation_service import EvaluationService
    from services.metrics_service import MetricsService
    eval_svc    = EvaluationService("data", mongo_storage=mongo)
    metrics_svc = MetricsService(eval_svc)

    print("Running evaluation pipeline...\n")
    report = metrics_svc.run(args.user_id, args.domain, labeled_data)

    if "error" in report:
        print(f"ERROR: {report['error']}")
        return

    n = report["evaluated"]
    print(f"Evaluated: {n} / {report['total_questions']} questions")
    if report.get("errors"):
        print(f"Failed:    {len(report['errors'])} questions\n")

    # ── Accuracy ──────────────────────────────────────────────────────────────
    print(f"{'─'*40}")
    print("  ACCURACY METRICS")
    print(f"{'─'*40}")
    print(f"  Bloom Accuracy (strict)    : {_pct(report['bloom_accuracy'])}")
    print(f"  Bloom Accuracy (±1 relaxed): {_pct(report['bloom_accuracy_relaxed'])}")
    print(f"  Topic Accuracy             : {_pct(report['topic_accuracy'])}")
    print(f"  CO Accuracy                : {_pct(report['co_accuracy'])}")
    if report.get("avg_bloom_confidence") is not None:
        print(f"  Avg Bloom Confidence       : {report['avg_bloom_confidence']:.3f}")

    # ── Similarity ────────────────────────────────────────────────────────────
    print(f"\n{'─'*40}")
    print("  TOPIC SIMILARITY")
    print(f"{'─'*40}")
    print(f"  Average : {report['avg_topic_similarity']:.3f}")
    print(f"  Minimum : {report['min_topic_similarity']:.3f}")
    print(f"  Maximum : {report['max_topic_similarity']:.3f}")

    # ── Error counts ──────────────────────────────────────────────────────────
    print(f"\n{'─'*40}")
    print("  CORRECT / INCORRECT COUNTS")
    print(f"{'─'*40}")
    for cat, ck, ik in [
        ("Bloom (relaxed)", "bloom_correct", "bloom_incorrect"),
        ("Topic",           "topic_correct", "topic_incorrect"),
        ("CO",              "co_correct",    "co_incorrect"),
    ]:
        c, i = report.get(ck, 0), report.get(ik, 0)
        bar  = _bar(c, c + i)
        print(f"  {cat:<18}: {c:>3} correct  {i:>3} incorrect  {bar}")

    # ── Confusion matrix (Bloom) ──────────────────────────────────────────────
    details = report.get("details", [])
    if details:
        confusion: dict = {}
        for d in details:
            tb, pb = d.get("true_bloom", "?"), d.get("pred_bloom", "?")
            if tb and pb and tb != pb:
                key = f"{tb} → {pb}"
                confusion[key] = confusion.get(key, 0) + 1

        if confusion:
            print(f"\n{'─'*40}")
            print("  BLOOM CONFUSION (mismatches only)")
            print(f"{'─'*40}")
            for k, v in sorted(confusion.items(), key=lambda x: -x[1]):
                print(f"  {k}: {v}")

        # ── CO confusion ──────────────────────────────────────────────────────
        co_conf: dict = {}
        for d in details:
            tc, pc = d.get("true_co", "?"), d.get("pred_co", "?")
            if tc and pc and tc != pc:
                key = f"{tc} → {pc}"
                co_conf[key] = co_conf.get(key, 0) + 1

        if co_conf:
            print(f"\n{'─'*40}")
            print("  CO CONFUSION (mismatches only)")
            print(f"{'─'*40}")
            for k, v in sorted(co_conf.items(), key=lambda x: -x[1]):
                print(f"  {k}: {v}")

        # ── Per-question breakdown ─────────────────────────────────────────────
        print(f"\n{'─'*40}")
        print("  PER-QUESTION BREAKDOWN")
        print(f"{'─'*40}")
        for i, d in enumerate(details, 1):
            b_sym = "✓" if d.get("bloom_correct") else "✗"
            t_sym = "✓" if d.get("topic_correct") else "✗"
            c_sym = "✓" if d.get("co_correct")    else "✗"
            sim   = d.get("topic_similarity", 0.0)
            print(f"\n  [{i}] {d['question'][:70]}")
            print(f"       Bloom : {d.get('true_bloom','?')} → {d.get('pred_bloom','?')} {b_sym}")
            print(f"       Topic : {d.get('true_topic','?')!r} → {d.get('pred_topic','?')!r}  sim={sim:.2f} {t_sym}")
            print(f"       CO    : {d.get('true_co','?')} → {d.get('pred_co','?')} {c_sym}")

    print(f"\n{'='*60}\n")


def _pct(v):
    return f"{round((v or 0) * 100, 1)}%"

def _bar(correct, total, width=20):
    if not total:
        return ""
    filled = round((correct / total) * width)
    return f"[{'█' * filled}{'░' * (width - filled)}] {round(correct/total*100)}%"


if __name__ == "__main__":
    main()
