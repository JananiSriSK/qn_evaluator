# Question Intelligence System

AI-powered question paper evaluator with Bloom taxonomy classification, RAG-based topic matching, and automated CO mapping.

## 🚀 Features

- **Two-Stage RAG Pipeline**: Bi-encoder + cross-encoder for accurate topic matching
- **Bloom Taxonomy Classification**: Fine-tuned DeBERTa-v3 (85% accuracy)
- **Syllabus Enrichment**: Groq LLM-powered subtopic generation
- **FAISS Indexing**: Fast semantic search over 3700+ book chunks
- **PDF Parser**: State-machine based question extraction with Part A/B/C detection
- **CO Mapping**: Automated Course Outcome assignment
- **MongoDB Storage**: Domain-based data management

## 📋 Prerequisites

- Python 3.8+
- Node.js 16+ (for frontend)
- MongoDB 4.4+
- Git LFS (optional, for large files)

## 🛠️ Installation

### 1. Clone Repository

```bash
git clone https://github.com/JananiSriSK/qn_evaluator.git
cd qn_evaluator_2
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup environment variables
cp .env.example .env
# Edit .env and add your GROQ_API_KEY and MongoDB URI
```

### 3. Download Models

**DeBERTa-v3 Bloom Model** (Required):
```bash
# Download from your model hosting service
# Place in: backend/bloom/bloom_model_final/content/final_bloom_model/
```

The model should contain:
- `config.json`
- `model.safetensors`
- `tokenizer.json`
- `vocab.txt`

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Start Backend Server

```bash
cd backend
python main_v2.py
```

Server runs on: `http://localhost:8002`

## 📁 Project Structure

```
qn_evaluator_2/
├── backend/
│   ├── services/              # Core services
│   │   ├── domain_manager.py
│   │   ├── evaluation_service.py
│   │   ├── retrieval_service.py
│   │   ├── model_registry.py
│   │   └── enrichment_service.py
│   ├── bloom/                 # DeBERTa-v3 model (not in repo)
│   ├── data/                  # User data (not in repo)
│   ├── main_v2.py            # FastAPI server
│   └── requirements.txt
├── frontend/
│   └── src/
├── architecture/              # Draw.io diagrams
├── .gitignore
├── .env.example
└── README.md
```

## 🎯 Usage

### 1. Create Domain

```bash
POST /domains/create
{
  "user_id": "user123",
  "domain_name": "JAVA_PROGRAMMING"
}
```

### 2. Upload Syllabus

```bash
POST /domains/{user_id}/{domain_name}/syllabus
Files: syllabus.pdf or syllabus.txt
```

### 3. Upload Books

```bash
POST /domains/{user_id}/{domain_name}/books
Files: book1.pdf, book2.pdf, ...
```

### 4. Evaluate Question

```bash
POST /evaluate
{
  "user_id": "user123",
  "domain_name": "JAVA_PROGRAMMING",
  "question": "Explain inheritance in Java"
}
```

**Response:**
```json
{
  "question": "Explain inheritance in Java",
  "bloom_level": "BT2",
  "bloom_confidence": 0.847,
  "unit": "I",
  "unit_title": "JAVA BASICS",
  "topic": "Inheritance",
  "course_outcomes": ["CO1"],
  "subtopics": ["Single Inheritance", "Multilevel Inheritance", ...],
  "relevant_chunks": [...]
}
```

## 🏗️ Architecture

### Module 1: Knowledge Base Setup
- Syllabus parsing (PDF/TXT)
- Book chunking (180 words, 40 overlap)
- FAISS IndexFlatIP (CPU-based)
- MongoDB GridFS storage

### Module 2: Question Input & Preprocessing
- PDF parser with Part A/B/C detection
- OR-question splitting
- Unified text cleaning

### Module 3: RAG Retrieval & Topic Matching
- **Stage 1**: Bi-encoder (all-MiniLM-L6-v2) → Top 10 candidates
- **Stage 2**: Cross-encoder (ms-marco-MiniLM-L-6-v2) → Rerank
- **Stage 3**: Relative rank gating (margin, dominance, retrieval support)

### Module 4: Bloom Classification
- Fine-tuned DeBERTa-v3-base
- 6-class classification (BT1-BT6)
- Softmax confidence scoring

### Module 5: Scoring & Output
- Difficulty score (Bloom-based)
- Strength score (linguistic heuristics)
- CO mapping (Unit → Course Outcome)
- JSON/PDF/DOCX export

## 📊 Performance Metrics

| Metric | Value |
|--------|-------|
| Bloom Accuracy | 85% |
| Avg Confidence | 84.7% |
| Avg Latency | 187ms |
| FAISS Chunks | 3700+ |
| Syllabus Alignment | High (with gating) |

## 🔧 Configuration

### Environment Variables

```bash
# Required
GROQ_API_KEY=your_groq_api_key
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=qn_evaluator

# Optional
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret
```

### Model Paths

Update in `backend/services/model_registry.py`:
```python
possible_paths = [
    Path("bloom/bloom_model_final/content/final_bloom_model"),
    Path("your/custom/path")
]
```

## 🧪 Testing

```bash
cd backend
python test_new_system.py
```

## 📝 API Documentation

Full API docs available at: `http://localhost:8002/docs` (Swagger UI)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Authors

- **Janani Sri SK** - [GitHub](https://github.com/JananiSriSK)

## 🙏 Acknowledgments

- Sentence-BERT for embeddings
- Groq for LLM inference
- MongoDB for storage
- FAISS for vector search
