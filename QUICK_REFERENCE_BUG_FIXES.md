# QUICK REFERENCE - CRITICAL BUG FIXES

## What Changed?

### 1. Cross-Encoder Threshold: 0.5 (NOT 0.30)
```python
if best_score < 0.5:  # Cross-encoder logits, not cosine similarity
    return "Out of Syllabus"
```

### 2. Filter Generic Topics
```python
if len(topic_name.split()) < 2:  # Skip "Basics", "Multitier", etc.
    continue
```

### 3. No Forced Selection
```python
if not best_topic:  # Don't assign random topic
    return "Out of Syllabus"
```

### 4. PDF Word Wrapping
```python
col_widths = [40, 250, 60, 60]  # Fixed widths
Paragraph(question_text, cell_style)  # Wrap in Paragraph
```

### 5. Only Cross-Encoder for Detection
```python
# REMOVED: bi-encoder threshold check
# ONLY: cross-encoder threshold (0.5)
```

---

## Testing Quick Commands

### Test In-Syllabus (should work)
```bash
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","domain_name":"Java","question":"Explain JSON"}'
```
**Expected**: `out_of_syllabus: false`, cross-encoder score >= 0.5

### Test Out-of-Syllabus (should fail)
```bash
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"test","domain_name":"Java","question":"Explain Python"}'
```
**Expected**: `out_of_syllabus: true`, cross-encoder score < 0.5

---

## Log Patterns to Look For

### Success (In-Syllabus)
```
INFO - Cross-encoder scores: [0.85, 0.72, 0.65, 0.58, 0.45]
INFO - Best score: 0.85
INFO - Selected: JSON Data Format
```

### Out-of-Syllabus
```
INFO - Cross-encoder scores: [0.35, 0.28, 0.22, 0.18, 0.12]
INFO - Best score: 0.35
WARNING - Cross-encoder score too low (0.35) - marking as out of syllabus
WARNING - Out of syllabus: cross-encoder score=0.35
```

### Generic Topics Filtered
```
# Topics like "Basics", "Multitier" won't appear in candidate list
INFO - Top 5 topics (bi-encoder): ['JSON Data Format', 'XML Processing', ...]
# NOT: ['Basics', 'Multitier', ...]
```

---

## Key Differences from Before

| Aspect | Before | After |
|--------|--------|-------|
| Threshold | 0.30 (wrong) | 0.5 (correct) |
| Detection | Bi-encoder + Cross-encoder | Cross-encoder only |
| Generic Topics | Included | Filtered out |
| Forced Selection | Yes | No |
| PDF Wrapping | Truncated | Full text wrapped |

---

## Files Changed

1. `backend/services/evaluation_service.py`
   - Cross-encoder threshold: 0.5
   - Filter topics: >= 2 words
   - No forced selection
   - Remove bi-encoder check

2. `backend/services/report_generator.py`
   - Paragraph wrapping
   - Fixed column widths: [40, 250, 60, 60]
   - Word wrap enabled

---

## Restart & Test

```bash
# Backend
cd backend
python main_v2.py

# Frontend
cd frontend
npm run dev

# Test
# 1. Evaluate "Explain JSON" → Should be IN-SYLLABUS
# 2. Evaluate "Explain Python" → Should be OUT-OF-SYLLABUS
# 3. Generate PDF → Should wrap long questions
# 4. Check logs → Cross-encoder scores visible
```

---

## Success Indicators

✅ Cross-encoder scores in logs (0.0 to 1.0 range)
✅ Threshold 0.5 enforced
✅ Generic topics not in candidate list
✅ Out-of-syllabus when score < 0.5
✅ PDF reports show full question text
✅ No truncation in PDFs

---

## Common Issues

**Issue**: Still seeing generic topics
**Fix**: Check syllabus parsing - ensure topics are loaded correctly

**Issue**: Wrong threshold applied
**Fix**: Verify evaluation_service.py has `if best_score < 0.5:`

**Issue**: PDF still truncating
**Fix**: Ensure using Paragraph() wrapper, not plain strings

**Issue**: Bi-encoder still used
**Fix**: Check map_to_syllabus() - should only check cross-encoder score

---

## Quick Verification

```python
# In backend logs, you should see:
# ✅ "Cross-encoder scores: [...]"
# ✅ "Best score: X.XX"
# ✅ "Cross-encoder score too low" when < 0.5
# ❌ NOT: "Low retrieval score"
# ❌ NOT: "topic_score=0.XX, retrieval_score=0.XX"
```

All fixes are minimal, focused, and production-ready! 🚀
