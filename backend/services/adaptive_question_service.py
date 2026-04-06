import logging
import os
import numpy as np
from collections import Counter
from typing import List, Dict, Optional
from groq import Groq
from sklearn.metrics.pairwise import cosine_similarity as cos_sim

logger = logging.getLogger(__name__)

BLOOM_ORDER = ["BT1", "BT2", "BT3", "BT4", "BT5", "BT6"]
BLOOM_LABELS = {
    "BT1": "Remember", "BT2": "Understand", "BT3": "Apply",
    "BT4": "Analyze",  "BT5": "Evaluate",   "BT6": "Create",
}
BLOOM_VERBS = {
    "BT1": "Define, List, Recall, State",
    "BT2": "Explain, Describe, Summarize, Illustrate",
    "BT3": "Implement, Develop, Apply, Demonstrate, Write",
    "BT4": "Compare, Analyze, Differentiate, Examine, Contrast",
    "BT5": "Evaluate, Justify, Critique, Assess, Argue",
    "BT6": "Design, Create, Construct, Formulate",
}
HIGHER_ORDER = {"BT4", "BT5", "BT6"}
CO_UNDERREP_THRESHOLD = 2


class AdaptiveQuestionService:
    """Module 8: Detect gaps and generate/guide targeted questions."""

    def __init__(self, groq_api_key=None):
        api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found")
        self.groq = Groq(api_key=api_key)

    # ── Public entry point ────────────────────────────────────────────────────

    def analyze_and_generate(
        self,
        results: List[Dict],
        syllabus: Dict,
        index=None,
        metadata: List[Dict] = None,
        embedder=None,
        cross_encoder=None,
    ) -> Dict:
        # Pass embedder so CO→unit mapping can use semantic similarity
        gaps              = self._detect_gaps(results, syllabus, embedder)
        replacement_count = self._replacement_count(results)

        bloom_gaps = [g for g in gaps if g["gap_type"] == "bloom_gap"]
        co_gaps    = [g for g in gaps if g["gap_type"] == "co_gap"]
        unit_gaps  = [g for g in gaps if g["gap_type"] == "unit_gap"]

        co_suggestions   = self._generate_for_co_gaps(co_gaps, syllabus, index, metadata, embedder, cross_encoder)
        bloom_guidance   = self._guidance_for_bloom_gaps(bloom_gaps, syllabus)
        unit_suggestions = self._generate_for_unit_gaps(unit_gaps, syllabus, index, metadata, embedder, cross_encoder)

        return {
            "gaps":               [{"type": g["gap_type"], "message": g["reason"]} for g in gaps],
            "replacement_count":  replacement_count,
            "bloom_guidance":     bloom_guidance,
            "suggested_questions": self._dedup(co_suggestions + unit_suggestions),
        }

    # ── CO → Unit mapping (semantic) ──────────────────────────────────────────

    @staticmethod
    def _build_co_unit_map(syllabus: Dict, embedder=None) -> Dict[str, str]:
        """
        Map each CO description to its most semantically similar unit.
        Uses bi-encoder cosine similarity between CO text and
        (unit title + topic names). Falls back to positional order.
        """
        cos_dict: Dict[str, str] = syllabus.get("course_outcomes", {})
        units: List[Dict]        = syllabus.get("units", [])

        if not cos_dict or not units:
            return {}

        unit_numbers = [u["unit_number"] for u in units]

        if embedder is not None:
            try:
                # Rich unit text: title + all topic names
                unit_texts = []
                for u in units:
                    topic_names = " ".join(t["topic_name"] for t in u.get("topics", []))
                    unit_texts.append(f"{u['unit_title']} {topic_names}".strip())

                co_keys  = list(cos_dict.keys())
                co_texts = [cos_dict[k] for k in co_keys]

                co_embs   = embedder.encode(co_texts,   convert_to_numpy=True, show_progress_bar=False)
                unit_embs = embedder.encode(unit_texts, convert_to_numpy=True, show_progress_bar=False)

                # sims shape: (n_cos, n_units)
                sims = cos_sim(co_embs, unit_embs)

                mapping = {}
                for i, co_key in enumerate(co_keys):
                    best_idx = int(np.argmax(sims[i]))
                    mapping[co_key] = unit_numbers[best_idx]
                    logger.info(
                        f"CO→Unit (semantic): {co_key} → Unit {unit_numbers[best_idx]} "
                        f"(sim={sims[i][best_idx]:.3f})"
                    )
                return mapping

            except Exception as e:
                logger.warning(f"Semantic CO→unit mapping failed, using positional fallback: {e}")

        # Positional fallback: CO1→unit[0], CO2→unit[1], …, extras→last unit
        mapping = {}
        for i, co_key in enumerate(sorted(cos_dict.keys())):
            mapping[co_key] = unit_numbers[min(i, len(unit_numbers) - 1)]
        logger.info(f"CO→Unit (positional fallback): {mapping}")
        return mapping

    # ── Gap detection ─────────────────────────────────────────────────────────

    def _detect_gaps(self, results: List[Dict], syllabus: Dict, embedder=None) -> List[Dict]:
        gaps      = []
        total     = len(results)
        all_units = {u["unit_number"]: u["unit_title"] for u in syllabus.get("units", [])}
        all_cos   = set(syllabus.get("course_outcomes", {}).keys())

        # ── Bloom distribution ────────────────────────────────────────────────
        bloom_counts = {b: 0 for b in BLOOM_ORDER}
        for r in results:
            bl = r.get("bloom_level") or r.get("bloom", "")
            if bl in bloom_counts:
                bloom_counts[bl] += 1

        low_count    = bloom_counts["BT1"] + bloom_counts["BT2"]
        higher_count = sum(bloom_counts[b] for b in HIGHER_ORDER)
        weakest      = self._weakest_unit(results, all_units)

        # Imbalance gap — too many low-level questions
        if total > 0 and low_count / total > 0.6:
            gaps.append({
                "gap_type": "bloom_gap", "target": "BT4+",
                "reason": f"Too many low-level (BT1/BT2) questions — {low_count}/{total} are recall/understanding level",
                "target_bloom": "BT4", "target_unit": weakest,
            })

        # Per-missing-level gaps for BT4, BT5, BT6
        for level in ["BT4", "BT5", "BT6"]:
            if bloom_counts[level] == 0:
                label = BLOOM_LABELS[level]
                # Skip BT4 imbalance duplicate — only add if not already covered by imbalance gap
                if level == "BT4" and total > 0 and low_count / total > 0.6:
                    continue
                gaps.append({
                    "gap_type": "bloom_gap", "target": level,
                    "reason": f"No {level} ({label}) questions present — paper lacks {label.lower()}-level thinking",
                    "target_bloom": level, "target_unit": weakest,
                })

        # ── Unit coverage ─────────────────────────────────────────────────────
        covered_units = {r.get("unit") for r in results if r.get("unit")}
        for unit_num, unit_title in all_units.items():
            if unit_num not in covered_units:
                gaps.append({
                    "gap_type": "unit_gap", "target": f"Unit {unit_num}",
                    "reason": f"Unit {unit_num} ({unit_title}) has no questions in the paper",
                    "target_bloom": "BT2", "target_unit": unit_num,
                })

        # ── CO coverage — single top CO per question ──────────────────────────
        co_counts: Counter = Counter()
        for r in results:
            cos = r.get("course_outcomes") or []
            top_co = cos[0] if cos else r.get("co", "")
            if top_co and top_co in all_cos:
                co_counts[top_co] += 1

        # Semantic CO→unit mapping (uses embedder when available)
        co_unit_map = self._build_co_unit_map(syllabus, embedder)

        for co in sorted(all_cos):
            count    = co_counts.get(co, 0)
            unit_num = co_unit_map.get(co, next(iter(all_units), "I"))

            if count == 0:
                gaps.append({
                    "gap_type": "co_gap", "target": co,
                    "reason": f"{co} not represented in the question paper",
                    "target_bloom": "BT3", "target_unit": unit_num, "target_co": co,
                })
            elif count < CO_UNDERREP_THRESHOLD:
                gaps.append({
                    "gap_type": "co_gap", "target": co,
                    "reason": f"{co} underrepresented — only {count} question(s) mapped",
                    "target_bloom": "BT4", "target_unit": unit_num, "target_co": co,
                })

        return gaps

    # ── CO gap → auto-generate ────────────────────────────────────────────────

    def _generate_for_co_gaps(self, gaps, syllabus, index, metadata, embedder, cross_encoder):
        all_units = {u["unit_number"]: u for u in syllabus.get("units", [])}
        all_cos   = syllabus.get("course_outcomes", {})
        subject   = self._subject(syllabus)
        suggested = []

        for gap in gaps:
            target_unit  = gap.get("target_unit") or next(iter(all_units), "I")
            target_bloom = gap.get("target_bloom", "BT3")
            target_co    = gap.get("target_co", "")

            unit_data    = all_units.get(target_unit, {})
            unit_title   = unit_data.get("unit_title", "")
            topics, subs = self._unit_topics(unit_data)
            book_ctx     = self._retrieve_chunks(topics[:2], index, metadata, embedder, cross_encoder)
            co_desc      = all_cos.get(target_co, "")

            prompt   = self._co_prompt(subject, target_unit, unit_title, topics, subs,
                                       target_bloom, target_co, co_desc, book_ctx, gap["reason"])
            question = self._call_groq(prompt)
            if question:
                suggested.append({
                    "unit": target_unit, "bloom": target_bloom,
                    "question": question, "addresses": gap["reason"],
                    "co": target_co, "gap_type": "co_gap",
                })

        return suggested

    # ── Unit gap → auto-generate ──────────────────────────────────────────────

    def _generate_for_unit_gaps(self, gaps, syllabus, index, metadata, embedder, cross_encoder):
        all_units = {u["unit_number"]: u for u in syllabus.get("units", [])}
        subject   = self._subject(syllabus)
        suggested = []

        for gap in gaps:
            target_unit  = gap.get("target_unit") or next(iter(all_units), "I")
            target_bloom = gap.get("target_bloom", "BT2")
            unit_data    = all_units.get(target_unit, {})
            unit_title   = unit_data.get("unit_title", "")
            topics, subs = self._unit_topics(unit_data)
            book_ctx     = self._retrieve_chunks(topics[:2], index, metadata, embedder, cross_encoder)

            prompt   = self._unit_prompt(subject, target_unit, unit_title, topics, subs,
                                         target_bloom, book_ctx, gap["reason"])
            question = self._call_groq(prompt)
            if question:
                suggested.append({
                    "unit": target_unit, "bloom": target_bloom,
                    "question": question, "addresses": gap["reason"],
                    "gap_type": "unit_gap",
                })

        return suggested

    # ── Bloom gap → guidance only ─────────────────────────────────────────────

    def _guidance_for_bloom_gaps(self, gaps, syllabus) -> List[Dict]:
        all_units = {u["unit_number"]: u for u in syllabus.get("units", [])}
        guidance  = []

        for gap in gaps:
            target_bloom = gap.get("target_bloom", "BT4")
            target_unit  = gap.get("target_unit") or next(iter(all_units), "I")
            unit_data    = all_units.get(target_unit, {})
            topics, _    = self._unit_topics(unit_data)

            guidance.append({
                "gap_message":       gap["reason"],
                "target_bloom":      target_bloom,
                "target_unit":       target_unit,
                "unit_title":        unit_data.get("unit_title", ""),
                "suggested_verbs":   BLOOM_VERBS.get(target_bloom, ""),
                "example_structure": self._bloom_example(target_bloom, topics),
                "gap_type":          "bloom_gap",
            })

        return guidance

    def _bloom_example(self, bloom: str, topics: List[str]) -> str:
        topic = topics[0] if topics else "the concept"
        return {
            "BT3": f"Implement a program demonstrating {topic} with a practical example.",
            "BT4": f"Compare {topic} with an alternative approach and analyze the trade-offs.",
            "BT5": f"Evaluate the effectiveness of {topic} and justify when it should be preferred.",
            "BT6": f"Design a system that incorporates {topic} to solve a real-world problem.",
        }.get(bloom, f"Apply {bloom} cognitive level to {topic}.")

    # ── Prompts ───────────────────────────────────────────────────────────────

    def _co_prompt(self, subject, unit, unit_title, topics, subs, bloom, co, co_desc, book_ctx, reason):
        topic_line  = ", ".join(topics) if topics else "core concepts"
        sub_line    = f"\n- Key subtopics: {', '.join(subs[:6])}" if subs else ""
        co_line     = f"\n- Course Outcome: {co} — {co_desc}" if co_desc else f"\n- Course Outcome: {co}"
        book_line   = f"\n\nRelevant book content (ground your question in these):\n{book_ctx}" if book_ctx else ""
        bloom_label = BLOOM_LABELS.get(bloom, "Apply")
        verbs       = BLOOM_VERBS.get(bloom, "")

        return f"""You are an expert exam question setter for {subject}.

Generate ONE concise university exam question (1-2 sentences max):

- Subject: {subject}
- Unit: {unit} — {unit_title}
- Topics: {topic_line}{sub_line}
- Bloom Level: {bloom} ({bloom_label}) — use verbs: {verbs}{co_line}
- Gap: {reason}{book_line}

Rules:
1. Use ONLY real {subject} concepts — name actual classes, APIs, frameworks (e.g. ArrayList, HttpServlet, JDBC, HashMap)
2. Start with one of the Bloom action verbs listed above
3. Must belong to Unit {unit} ({unit_title})
4. No generic phrases like "two systems", "different approaches", "a program"
5. Keep it to ONE clear exam question — not a paragraph
6. Return ONLY the question text — no numbering, no prefix"""

    def _unit_prompt(self, subject, unit, unit_title, topics, subs, bloom, book_ctx, reason):
        topic_line  = ", ".join(topics) if topics else "core concepts"
        sub_line    = f"\n- Key subtopics: {', '.join(subs[:6])}" if subs else ""
        book_line   = f"\n\nRelevant book content:\n{book_ctx}" if book_ctx else ""
        bloom_label = BLOOM_LABELS.get(bloom, "Understand")
        verbs       = BLOOM_VERBS.get(bloom, "")

        return f"""Generate ONE concise university exam question (1-2 sentences) for {subject}:

- Unit: {unit} — {unit_title}
- Topics: {topic_line}{sub_line}
- Bloom Level: {bloom} ({bloom_label}) — use verbs: {verbs}
- Gap: {reason}{book_line}

Rules: Use specific {subject} concepts. No generic phrasing. ONE clear question only. Return ONLY the question text."""

    # ── Groq call ─────────────────────────────────────────────────────────────

    def _call_groq(self, prompt: str) -> Optional[str]:
        try:
            resp = self.groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.3,
                max_tokens=80,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Groq call failed: {e}")
            return None

    # ── Chunk retrieval ───────────────────────────────────────────────────────

    def _retrieve_chunks(self, topics, index, metadata, embedder, cross_encoder, top_k=5) -> str:
        if not topics or index is None or not metadata or embedder is None:
            return ""
        try:
            import faiss
            query = " ".join(topics)
            emb   = embedder.encode([query], convert_to_numpy=True, show_progress_bar=False).astype("float32")
            faiss.normalize_L2(emb)
            _, idxs    = index.search(emb, min(30, len(metadata)))
            candidates = [metadata[i] for i in idxs[0] if i < len(metadata)]
            if cross_encoder and candidates:
                scores = cross_encoder.predict([(query, c["text"]) for c in candidates])
                for i, s in enumerate(scores):
                    candidates[i]["_s"] = float(s)
                candidates.sort(key=lambda x: x.get("_s", 0), reverse=True)
            return "\n".join(f"- {c['text'][:250]}" for c in candidates[:top_k])
        except Exception as e:
            logger.warning(f"Chunk retrieval failed: {e}")
            return ""

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _subject(syllabus: Dict) -> str:
        return (syllabus.get("subject_name") or syllabus.get("course_name")
                or syllabus.get("domain_name", "the subject"))

    @staticmethod
    def _unit_topics(unit_data: Dict):
        topics, subs = [], []
        for t in unit_data.get("topics", [])[:6]:
            topics.append(t["topic_name"])
            subs.extend(t.get("enriched_subtopics_from_books", [])[:3])
        return topics, subs

    @staticmethod
    def _dedup(suggestions: List[Dict]) -> List[Dict]:
        seen, unique = set(), []
        for q in suggestions:
            txt = q.get("question", "")
            if txt and txt not in seen:
                unique.append(q)
                seen.add(txt)
        return unique

    @staticmethod
    def _replacement_count(results: List[Dict]) -> int:
        total = len(results)
        if not total:
            return 0
        low = sum(1 for r in results
                  if (r.get("bloom_level") or r.get("bloom", "")) in ("BT1", "BT2"))
        return max(0, low - int(total * 0.4))

    def _weakest_unit(self, results: List[Dict], all_units: Dict) -> Optional[str]:
        unit_bloom: Dict[str, List[int]] = {}
        for r in results:
            unit = r.get("unit")
            bl   = r.get("bloom_level") or r.get("bloom", "")
            if unit and bl and len(bl) >= 3:
                try:
                    unit_bloom.setdefault(unit, []).append(int(bl[2]))
                except ValueError:
                    pass
        if unit_bloom:
            return min(unit_bloom, key=lambda u: sum(unit_bloom[u]) / len(unit_bloom[u]))
        counts = Counter(r.get("unit") for r in results if r.get("unit"))
        return counts.most_common(1)[0][0] if counts else next(iter(all_units), "I")
