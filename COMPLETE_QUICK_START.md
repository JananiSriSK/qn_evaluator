# Question Intelligence System - Complete Quick Start Guide

## 🚀 System Overview

**Backend**: FastAPI (Python) - Port 8002
**Frontend**: React + Vite - Port 5173
**Architecture**: Domain-based multi-user system with Bloom taxonomy classification

---

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- 2GB RAM minimum (for ML models)

---

## ⚡ Quick Start (5 Minutes)

### Step 1: Start Backend

```bash
cd backend
python main_v2.py
```

Wait for: `System startup completed successfully`

Backend running at: `http://localhost:8002`

### Step 2: Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Frontend running at: `http://localhost:5173`

### Step 3: Use the System

1. Open `http://localhost:5173`
2. Login with any user ID (e.g., "john_doe")
3. Click "+ Create Domain"
4. Enter domain name (e.g., "JAVA_PROGRAMMING")
5. Upload syllabus (PDF or TXT)
6. Upload books (multiple PDFs)
7. Wait for indexing (~30 seconds)
8. Click "Go to Evaluation"
9. Enter question and evaluate!

---

## 📁 Project Structure

```
qn_evaluator_2/
├── backend/
│   ├── services/           # Core services
│   │   ├── model_registry.py      # Singleton model loader
│   │   ├── domain_manager.py      # Domain & FAISS management
│   │   ├── evaluation_service.py  # Evaluation pipeline
│   │   └── retrieval_service.py   # FAISS retrieval
│   ├── bloom/              # Bloom taxonomy model
│   ├── data/               # User domains
│   │   └── {user_id}/
│   │       └── {domain_name}/
│   │           ├── syllabus.json
│   │           ├── books/
│   │           └── vector_db/
│   ├── main_v2.py          # FastAPI server
│   └── test_api.py         # API tests
│
└── frontend/
    ├── src/
    │   ├── components/
    │   │   ├── DomainSetup.jsx
    │   │   ├── EvaluationResult.jsx
    │   │   └── FileUpload.jsx
    │   ├── pages/
    │   │   ├── Login.jsx
    │   │   ├── Dashboard.jsx
    │   │   └── Evaluate.jsx
    │   ├── services/
    │   │   └── api-v2.js
    │   └── App.jsx
    └── package.json
```

---

## 🔧 Backend Details

### Key Features
- Domain-based architecture (multi-user support)
- FAISS vector indexing for book retrieval
- Bloom taxonomy classification (BT1-BT6)
- Syllabus parsing (PDF/TXT)
- Cross-encoder reranking
- Model registry (single load optimization)

### API Endpoints
```
GET    /                                          # Health check
POST   /domains/create                            # Create domain
GET    /domains/{user_id}                         # List domains
POST   /domains/{user_id}/{domain}/syllabus      # Upload syllabus
POST   /domains/{user_id}/{domain}/books         # Upload books
GET    /domains/{user_id}/{domain}/status        # Get status
POST   /evaluate                                  # Evaluate question
POST   /evaluate/pdf                              # Batch evaluate
```

### Models Loaded
- Bi-encoder: `sentence-transformers/all-MiniLM-L6-v2`
- Cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2`
- Bloom classifier: Custom fine-tuned model

### Memory Usage
~1.1 GB (optimized with model registry)

---

## 🎨 Frontend Details

### Pages
1. **Login** (`/login`)
   - User ID input
   - localStorage persistence

2. **Dashboard** (`/dashboard`)
   - Domain list sidebar
   - Create domain modal
   - Domain setup panel
   - Status tracking

3. **Evaluate** (`/evaluate`)
   - Single question evaluation
   - PDF batch evaluation
   - Result visualization

### Components
- **DomainSetup**: Upload syllabus/books, track status
- **FileUpload**: Reusable file upload component
- **EvaluationResult**: Display evaluation results

### Styling
- Inline styles (no CSS framework)
- Clean academic design
- Color-coded Bloom levels
- Responsive layout

---

## 📊 Evaluation Response Format

```json
{
  "question": "What is polymorphism?",
  "unit": "Unit I",
  "topic": "Polymorphism",
  "course_outcomes": ["CO1"],
  "bloom_level": "BT1",
  "bloom_confidence": 0.78,
  "subtopics": [
    "Runtime polymorphism",
    "Compile-time polymorphism"
  ],
  "relevant_chunks": [
    {
      "chunk_id": 145,
      "book_name": "Java_Complete_Reference.pdf",
      "page": 23,
      "text": "Polymorphism allows...",
      "score": 0.89
    }
  ]
}
```

---

## 🧪 Testing

### Backend API Tests
```bash
cd backend
python test_api.py
```

Expected: 9/9 tests pass

### Manual Testing Flow
1. Create domain
2. Upload syllabus
3. Upload books
4. Check status (should show ready)
5. Evaluate question
6. Verify result has all fields

---

## 🔍 Troubleshooting

### Backend Issues

**Port 8002 already in use**
```bash
# Windows
netstat -ano | findstr :8002
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8002 | xargs kill -9
```

**Models not loading**
- Check internet connection (first run downloads models)
- Ensure 2GB+ RAM available
- Check `backend.log` for errors

**FAISS index build fails**
- Verify PDF files are valid
- Check disk space
- Ensure books directory has PDFs

### Frontend Issues

**npm install fails**
```bash
rm -rf node_modules package-lock.json
npm install
```

**CORS errors**
- Verify backend is running on port 8002
- Check `main_v2.py` CORS configuration
- Clear browser cache

**API calls fail**
- Check `src/services/api-v2.js` base URL
- Verify backend is running
- Check browser console for errors

---

## 📈 Performance Tips

### Backend
- Models load once at startup (~10 seconds)
- FAISS indexing: ~10-30 seconds for 3 books
- Question evaluation: ~1-2 seconds
- PDF evaluation: ~1-2 seconds per question

### Frontend
- Initial load: < 1 second
- File uploads: Depends on file size
- API calls: < 2 seconds typically

---

## 🔐 Security Notes

### Current Implementation
- No authentication (localStorage only)
- CORS restricted to localhost
- File type validation
- Path traversal prevention

### Production Requirements
- Add JWT/OAuth authentication
- Implement rate limiting
- Add file size limits
- Enable HTTPS
- Update CORS for production domain
- Add input sanitization
- Implement user roles/permissions

---

## 📝 Common Use Cases

### 1. Single Question Evaluation
```
Login → Dashboard → Select Domain → Evaluate →
Enter Question → View Result
```

### 2. Batch PDF Evaluation
```
Login → Dashboard → Select Domain → Evaluate →
Upload PDF → View All Results
```

### 3. New Course Setup
```
Login → Dashboard → Create Domain →
Upload Syllabus → Upload Books →
Wait for Indexing → Start Evaluating
```

### 4. Multiple Domains
```
Login → Dashboard → Create Domain 1 → Setup →
Create Domain 2 → Setup →
Switch between domains in Evaluate page
```

---

## 🎯 System Capabilities

### Bloom Taxonomy Classification
- BT1: Remember
- BT2: Understand
- BT3: Apply
- BT4: Analyze
- BT5: Evaluate
- BT6: Create

### Syllabus Mapping
- Automatic unit detection
- Topic extraction
- Course outcome mapping (CO1-CO5)
- Subtopic generation

### Book Retrieval
- FAISS vector search
- Cross-encoder reranking
- Top-K relevant chunks
- Similarity scoring

---

## 📚 Documentation

- **Backend API**: `backend/API_DOCUMENTATION.md`
- **API Quick Reference**: `backend/API_QUICK_REFERENCE.md`
- **Step 1 Summary**: `STEP_1.6_SUMMARY.md`
- **Step 2 Summary**: `backend/STEP_2_SUMMARY.md`
- **Step 3 Summary**: `frontend/STEP_3_SUMMARY.md`
- **Frontend README**: `frontend/FRONTEND_README.md`

---

## 🎉 Success Indicators

✅ Backend starts without errors
✅ Frontend loads at localhost:5173
✅ Can login and see dashboard
✅ Can create domain
✅ Can upload syllabus
✅ Can upload books
✅ Status shows "Ready"
✅ Can evaluate questions
✅ Results display correctly
✅ No console errors

---

## 🆘 Support

### Check Logs
- Backend: `backend/backend.log`
- Frontend: Browser console (F12)

### Common Commands
```bash
# Backend
cd backend
python main_v2.py

# Frontend
cd frontend
npm run dev

# Test Backend
cd backend
python test_api.py

# Build Frontend
cd frontend
npm run build
```

---

## 🚀 You're Ready!

The system is now fully operational. Start by logging in and creating your first domain!

**Happy Evaluating! 🎓**
