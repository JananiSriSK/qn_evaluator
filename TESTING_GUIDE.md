# QUICK TESTING GUIDE

## Start the System

### Backend
```bash
cd backend
python main_v2.py
```
Server runs on: http://localhost:8002

### Frontend
```bash
cd frontend
npm run dev
```
App runs on: http://localhost:5173

---

## Test Scenarios

### 1. Topic-First Classification Test

**Test Questions:**
- "Explain JSON data format" → Should map to correct unit/topic
- "What is Hibernate framework?" → Should map to correct unit/topic
- "Describe Spring Boot" → Should map to correct unit/topic

**Expected:**
- Unit derived from best matching topic (not chunk frequency)
- Cross-encoder scores visible in backend logs
- Correct unit and topic assignment

---

### 2. Out of Syllabus Detection Test

**In-Syllabus Questions (should NOT be marked out of syllabus):**
- "Explain JSON"
- "What is Hibernate?"
- "Describe Spring framework"

**Out-of-Syllabus Questions (should be marked out of syllabus):**
- "Explain Python programming"
- "What is machine learning?"
- "Describe React hooks"

**Expected:**
- In-syllabus: topic_score >= 0.30 OR retrieval_score >= 0.30
- Out-of-syllabus: topic_score < 0.30 AND retrieval_score < 0.30
- Yellow highlight for out-of-syllabus in UI

---

### 3. Report Type Test

**Steps:**
1. Upload a question paper PDF
2. Wait for evaluation to complete
3. Select "Mapping Only (Q.No, CO, BL)" from dropdown
4. Click "Download PDF"
5. Verify PDF has 3 columns: Q.No | CO | BL
6. Select "With Questions (Q.No, Question, CO, BL)" from dropdown
7. Click "Download PDF"
8. Verify PDF has 4 columns: Q.No | Question | CO | BL

**Expected:**
- Dropdown shows both options
- Mapping report: 3 columns only
- Question paper report: 4 columns with question text

---

### 4. History Feature Test

**Steps:**
1. Evaluate a single question
2. Navigate to History page (sidebar)
3. Verify question appears in "Single Questions" tab
4. Upload and evaluate a PDF
5. Switch to "PDF Evaluations" tab
6. Verify PDF evaluation appears

**Expected:**
- History page accessible from sidebar
- Two tabs: "Single Questions" and "PDF Evaluations"
- Timestamps, domain, questions visible
- Out-of-syllabus questions highlighted

---

## Backend Logs to Check

### Topic Selection Logs
```
INFO - Top 5 topics (bi-encoder): ['Topic1', 'Topic2', ...]
INFO - Cross-encoder scores: [0.85, 0.72, ...]
INFO - Selected: TopicName (score: 0.85)
```

### Out of Syllabus Logs
```
WARNING - Out of syllabus: topic_score=0.25, retrieval_score=0.28
```

---

## API Testing with curl

### Test Single Question Evaluation
```bash
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "domain_name": "Java",
    "question": "Explain JSON data format"
  }'
```

### Test History Retrieval
```bash
curl http://localhost:8002/history/test_user
```

### Test Report Generation
```bash
curl -X POST http://localhost:8002/report/generate \
  -H "Content-Type: application/json" \
  -d '{
    "domain_name": "Java",
    "results": [...],
    "format": "pdf",
    "type": "mapping"
  }'
```

---

## Verification Checklist

### Topic-First Classification
- [ ] Unit is derived from topic (check logs)
- [ ] Cross-encoder reranking happens (check logs)
- [ ] Correct unit/topic assignment

### Out of Syllabus Detection
- [ ] JSON questions: IN-SYLLABUS
- [ ] Hibernate questions: IN-SYLLABUS
- [ ] Spring questions: IN-SYLLABUS
- [ ] Python questions: OUT OF SYLLABUS
- [ ] Dual threshold check (both < 0.30)

### Report Types
- [ ] Dropdown visible in UI
- [ ] "Mapping Only" generates 3-column report
- [ ] "With Questions" generates 4-column report
- [ ] Both PDF and DOCX work

### History Feature
- [ ] Single questions tracked
- [ ] PDF evaluations tracked
- [ ] History page displays correctly
- [ ] Timestamps and metadata correct
- [ ] Out-of-syllabus highlighted

---

## Common Issues & Solutions

### Issue: Cross-encoder not reranking
**Solution:** Check model_registry.py - ensure cross-encoder is loaded

### Issue: History not saving
**Solution:** Check file permissions on data/{user_id}/ directory

### Issue: Report type not working
**Solution:** Verify frontend sends "type" parameter in request

### Issue: Out of syllabus detection too strict
**Solution:** Verify threshold is 0.30 (not 0.35) in evaluation_service.py

---

## Performance Benchmarks

### Expected Response Times
- Single question evaluation: 1-2 seconds
- PDF evaluation (20 questions): 20-40 seconds
- History retrieval: < 100ms
- Report generation: < 500ms

### Memory Usage
- Backend: ~1.1 GB (with models loaded)
- Frontend: ~50 MB

---

## Success Criteria

✅ **Topic-First Classification**
- Unit correctly derived from topic
- Cross-encoder scores in logs
- No unit frequency voting

✅ **Out of Syllabus Detection**
- JSON/Hibernate/Spring: IN-SYLLABUS
- Python: OUT OF SYLLABUS
- Dual threshold enforced

✅ **Report Types**
- Both report types generate correctly
- UI dropdown works
- Correct column counts

✅ **History Feature**
- All evaluations tracked
- History page functional
- Data persists across sessions

---

## Next Steps After Testing

1. Test with real syllabus and question papers
2. Verify accuracy improvements
3. Monitor backend logs for any errors
4. Collect user feedback on new features
5. Fine-tune thresholds if needed (currently 0.30)

---

## Support

If issues arise:
1. Check backend logs for errors
2. Verify all files were updated correctly
3. Restart both backend and frontend
4. Clear browser cache
5. Check data/{user_id}/ directory structure
