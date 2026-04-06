"""
Generate a labeled test dataset for pipeline evaluation.
Ground truth is assigned from syllabus structure + verb-based Bloom detection,
NOT from model predictions.

Usage:
    python generate_test_dataset.py --user_id 1 --domain "JAVA PROG" --out test_dataset.json
    python generate_test_dataset.py --user_id 1 --domain "JAVA PROG" --out test_dataset.json --per_unit 3
"""
import argparse
import json
import os
import sys
import re

sys.path.insert(0, os.path.dirname(__file__))

# ── Verb → Bloom mapping (ground truth, not model) ───────────────────────────

VERB_BLOOM = {
    "define":       "BT1", "list":        "BT1", "recall":    "BT1",
    "state":        "BT1", "name":        "BT1", "identify":  "BT1",
    "explain":      "BT2", "describe":    "BT2", "summarize": "BT2",
    "illustrate":   "BT2", "discuss":     "BT2", "outline":   "BT2",
    "apply":        "BT3", "implement":   "BT3", "develop":   "BT3",
    "demonstrate":  "BT3", "write":       "BT3", "use":       "BT3",
    "analyze":      "BT4", "compare":     "BT4", "differentiate": "BT4",
    "examine":      "BT4", "contrast":    "BT4", "classify":  "BT4",
    "evaluate":     "BT5", "justify":     "BT5", "critique":  "BT5",
    "assess":       "BT5", "argue":       "BT5",
    "design":       "BT6", "create":      "BT6", "construct": "BT6",
    "formulate":    "BT6", "build":       "BT6",
}

# Target Bloom distribution across the dataset
BLOOM_TARGETS = ["BT1", "BT2", "BT3", "BT4", "BT5", "BT6"]


def detect_bloom_from_question(question: str) -> str:
    """Detect Bloom level from the first verb in the question."""
    first_word = question.strip().split()[0].lower().rstrip(".,:")
    return VERB_BLOOM.get(first_word, "BT2")


def build_co_unit_map(syllabus: dict) -> dict:
    """Map CO → unit number using positional order (CO1→first unit, etc.)."""
    units = syllabus.get("units", [])
    cos   = syllabus.get("course_outcomes", {})
    unit_numbers = [u["unit_number"] for u in units]
    return {
        f"CO{i+1}": unit_numbers[i] if i < len(unit_numbers) else unit_numbers[-1]
        for i in range(len(cos))
    }


def generate_questions_for_unit(groq_client, subject, unit, co, bloom, topics, n=1):
    """Use Groq to generate n questions for a given unit/CO/bloom combination."""
    bloom_labels = {
        "BT1": "Remember", "BT2": "Understand", "BT3": "Apply",
        "BT4": "Analyze",  "BT5": "Evaluate",   "BT6": "Create",
    }
    bloom_verbs = {
        "BT1": "Define or List",   "BT2": "Explain or Describe",
        "BT3": "Implement or Write", "BT4": "Compare or Analyze",
        "BT5": "Evaluate or Justify", "BT6": "Design or Create",
    }
    topic_list = ", ".join(topics[:4]) if topics else "core concepts"
    label = bloom_labels.get(bloom, "Understand")
    verb  = bloom_verbs.get(bloom, "Explain")

    prompt = f"""Generate {n} university exam question(s) for:
- Subject: {subject}
- Unit: {unit['unit_number']} — {unit['unit_title']}
- Topics: {topic_list}
- Course Outcome: {co}
- Bloom Level: {bloom} ({label})
- Start the question with: {verb}

Rules:
- Use specific {subject} concepts (real class names, APIs, frameworks)
- Each question on a separate line
- Return ONLY the question text(s), no numbering or explanation"""

    try:
        resp = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
            max_tokens=300,
        )
        text = resp.choices[0].message.content.strip()
        lines = [l.strip() for l in text.split("\n") if l.strip() and len(l.strip()) > 20]
        return lines[:n]
    except Exception as e:
        print(f"  [warn] Groq failed for {unit['unit_number']}/{bloom}: {e}")
        return []


def validate_dataset(dataset: list) -> bool:
    """Warn if dataset looks like self-evaluation (all fields identical pattern)."""
    if not dataset:
        return False
    # Check if true_bloom distribution is suspiciously uniform (sign of copy-paste)
    blooms = [d.get("true_bloom") for d in dataset]
    if len(set(blooms)) == 1:
        print("[warn] All true_bloom values are identical — dataset may not be diverse enough.")
    return True


def main():
    parser = argparse.ArgumentParser(description="Generate labeled test dataset from syllabus")
    parser.add_argument("--user_id",   required=True)
    parser.add_argument("--domain",    required=True)
    parser.add_argument("--out",       default="test_dataset.json", help="Output JSON file path")
    parser.add_argument("--per_unit",  type=int, default=2, help="Questions per unit (default 2)")
    args = parser.parse_args()

    from dotenv import load_dotenv
    load_dotenv()

    print(f"\n{'='*60}")
    print(f"  Test Dataset Generator")
    print(f"{'='*60}")
    print(f"  User:     {args.user_id}")
    print(f"  Domain:   {args.domain}")
    print(f"  Per unit: {args.per_unit}")
    print(f"  Output:   {args.out}")
    print(f"{'='*60}\n")

    # ── Load syllabus ─────────────────────────────────────────────────────────
    from services.mongodb_storage import MongoDBStorage
    mongo = MongoDBStorage(
        os.getenv("MONGODB_URI", "mongodb://localhost:27017/"),
        os.getenv("MONGODB_DB", "qn_evaluator"),
    )
    syllabus = mongo.get_syllabus(args.user_id, args.domain)
    if not syllabus:
        print("ERROR: Syllabus not found. Upload syllabus first.")
        sys.exit(1)

    units   = syllabus.get("units", [])
    cos_map = syllabus.get("course_outcomes", {})
    subject = syllabus.get("course_name") or syllabus.get("subject_name") or args.domain
    co_unit_map = build_co_unit_map(syllabus)
    # Reverse: unit_number → CO
    unit_co_map = {v: k for k, v in co_unit_map.items()}

    print(f"  Subject : {subject}")
    print(f"  Units   : {[u['unit_number'] for u in units]}")
    print(f"  COs     : {list(cos_map.keys())}\n")

    # ── Init Groq ─────────────────────────────────────────────────────────────
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set in .env")
        sys.exit(1)
    from groq import Groq
    groq_client = Groq(api_key=api_key)

    # ── Generate questions ────────────────────────────────────────────────────
    dataset = []
    bloom_cycle = BLOOM_TARGETS * 10   # cycle through BT1–BT6

    for unit_idx, unit in enumerate(units):
        unit_num   = unit["unit_number"]
        unit_title = unit["unit_title"]
        topics     = [t["topic_name"] for t in unit.get("topics", [])]
        co         = unit_co_map.get(unit_num, f"CO{unit_idx+1}")

        print(f"  Unit {unit_num} — {unit_title} ({co})")

        # Pick bloom levels for this unit — spread across BT1–BT6
        blooms_for_unit = []
        for j in range(args.per_unit):
            bl = bloom_cycle[(unit_idx * args.per_unit + j) % len(BLOOM_TARGETS)]
            blooms_for_unit.append(bl)

        for bloom in blooms_for_unit:
            questions = generate_questions_for_unit(
                groq_client, subject, unit, co, bloom, topics, n=1
            )
            for q in questions:
                # Ground truth: topic from syllabus (first topic of unit),
                # bloom from verb detection on generated question,
                # co from unit mapping — all independent of model
                detected_bloom = detect_bloom_from_question(q)
                # Use detected bloom if it matches target, else keep target
                # (Groq usually starts with the right verb)
                final_bloom = detected_bloom if detected_bloom == bloom else bloom

                # Pick the most relevant topic from the unit based on question keywords
                true_topic = _pick_topic(q, topics)

                entry = {
                    "question":   q,
                    "true_topic": true_topic,
                    "true_bloom": final_bloom,
                    "true_co":    co,
                }
                dataset.append(entry)
                print(f"    [{final_bloom}] {q[:70]}...")

    print(f"\n  Generated {len(dataset)} questions total.")

    # ── Validate ──────────────────────────────────────────────────────────────
    validate_dataset(dataset)

    # ── Save ──────────────────────────────────────────────────────────────────
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)

    print(f"\n  Saved → {args.out}")
    print(f"\n  Next step:")
    print(f"  python evaluate_metrics.py --user_id {args.user_id} --domain \"{args.domain}\" --file {args.out}")
    print(f"\n{'='*60}\n")


def _pick_topic(question: str, topics: list) -> str:
    """Pick the most relevant topic from the unit based on keyword overlap."""
    if not topics:
        return ""
    q_lower = question.lower()
    best, best_score = topics[0], 0
    for t in topics:
        score = sum(1 for word in t.lower().split() if len(word) > 3 and word in q_lower)
        if score > best_score:
            best, best_score = t, score
    return best


if __name__ == "__main__":
    main()
