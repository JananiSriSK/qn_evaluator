# Architecture Diagram - Question Intelligence System

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Frontend (React)                         │
│                     http://localhost:5173                        │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             │ HTTP Requests
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend (FastAPI)                           │
│                     http://localhost:8002                        │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    main_v2.py                             │  │
│  │  • Domain management                                      │  │
│  │  • Syllabus endpoints                                     │  │
│  │  • Book upload endpoints                                  │  │
│  │  • Evaluation endpoints                                   │  │
│  │  • History endpoints                                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   Domain    │   │  Evaluation  │   │  Enrichment  │         │
│  │   Manager   │   │   Service    │   │   Service    │         │
│  └─────────────┘   └──────────────┘   └──────────────┘         │
│         │                   │                   │                │
│         └───────────────────┼───────────────────┘                │
│                             ▼                                     │
│                    ┌──────────────┐                              │
│                    │   MongoDB    │                              │
│                    │   Storage    │                              │
│                    └──────────────┘                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    MongoDB Compass                               │
│                  mongodb://localhost:27017                       │
│                                                                   │
│  Database: qn_evaluator                                          │
│  ├── domains (domain metadata)                                   │
│  ├── syllabus (parsed JSON + GridFS file refs)                  │
│  ├── books (GridFS file refs)                                   │
│  ├── indexes (FAISS binary + metadata)                          │
│  └── history (evaluation history)                               │
│                                                                   │
│  GridFS: fs.files, fs.chunks                                    │
│  ├── Syllabus PDFs/TXT                                          │
│  ├── Book PDFs                                                  │
│  └── FAISS index binaries                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Complete Evaluation Pipeline

```
User uploads question
         │
         ▼
┌────────────────────────────────────────┐
│  1. Unified Preprocessing              │
│     clean_question_text()              │
│     • Remove numbering (Q.1, 3., 16a)  │
│     • Remove Part A/B/C markers        │
│     • Remove bullets, marks            │
│     • Unicode normalization            │
│     • Collapse whitespace              │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  2. FAISS Retrieval                    │
│     • Bi-encoder embedding             │
│     • Top 10 semantic chunks           │
│     • From enriched book content       │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  3. Topic Matching (Hybrid)            │
│     • Bi-encoder: Top 10 candidates    │
│     • Cross-encoder: Rerank            │
│     • Sigmoid probability conversion   │
│     • Relative rank-based gating:      │
│       - Margin rule (≥0.05)            │
│       - Dominance rule (1.5x mean)     │
│       - Retrieval support (top 3)      │
│     • Match against enriched topics    │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  4. Bloom Classification               │
│     • Fine-tuned DistilBERT            │
│     • BT1-BT6 prediction               │
│     • Confidence score                 │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  5. Course Outcome Mapping             │
│     • Unit → CO mapping                │
│     • Return enriched subtopics        │
│     • Return relevant chunks           │
└────────────────────────────────────────┘
```

## Syllabus Upload & Enrichment Flow

### Upload & Enrichment (MongoDB)
```
User uploads syllabus.txt + books
         │
         ▼
┌────────────────────────────────────────┐
│  POST /domains/{user_id}/{domain}/     │
│       syllabus                          │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  domain_manager.save_syllabus()        │
│                                         │
│  1. Parse text to JSON                 │
│     → Extract units, topics, COs       │
│                                         │
│  2. Save to MongoDB                    │
│     → syllabus collection              │
│     → GridFS for original file         │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  POST /domains/{user_id}/{domain}/     │
│       books                             │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  domain_manager.add_books()            │
│                                         │
│  1. Save PDFs to MongoDB GridFS        │
│                                         │
│  2. Build FAISS index                  │
│     → Chunk books (180 words)          │
│     → Embed with bi-encoder            │
│     → Serialize FAISS to bytes         │
│     → Save to MongoDB GridFS           │
│                                         │
│  3. Auto-trigger enrichment            │
└────────────────┬───────────────────────┘
                 │
                 ▼
┌────────────────────────────────────────┐
│  enrichment_service.enrich_syllabus()  │
│                                         │
│  For each topic:                       │
│  1. Retrieve top 30 chunks (bi-enc)    │
│  2. Rerank to top 10 (cross-enc)       │
│  3. Generate 5-7 subtopics (Groq LLM)  │
│  4. Save enriched syllabus to MongoDB  │
└────────────────────────────────────────┘
```

## MongoDB Storage Architecture

### Collections Schema
```
domains
├── user_id: "1"
├── domain_name: "JAVA PROG"
└── created_at: ISODate

syllabus
├── user_id: "1"
├── domain_name: "JAVA PROG"
├── syllabus_data: {
│   course_name: "...",
│   units: [{
│     unit_number: "I",
│     unit_title: "JAVA BASICS",
│     topics: [{
│       topic_name: "Inheritance",
│       enriched_subtopics_from_books: [...],
│       source_references: [...]
│     }]
│   }]
│ }
├── original_file_id: ObjectId (GridFS)
├── original_filename: "syllabus.txt"
└── updated_at: ISODate

books
├── user_id: "1"
├── domain_name: "JAVA PROG"
├── filename: "java_book.pdf"
├── file_id: ObjectId (GridFS)
└── uploaded_at: ISODate

indexes
├── user_id: "1"
├── domain_name: "JAVA PROG"
├── file_id: ObjectId (GridFS - FAISS binary)
├── metadata: [{chunk_id, book_name, page, text}]
├── chunks_count: 6500
└── updated_at: ISODate

history
├── user_id: "1"
├── data: {
│   single_questions: [...],
│   pdf_evaluations: [...]
│ }
└── updated_at: ISODate
```

## Cross-Encoder Gating (Improved)

### Old: Absolute Threshold (Unstable)
```
Raw logit → Reject if < -2.0
Problem: MS MARCO model produces highly negative logits
         for short topic labels
```

### New: Relative Rank-Based Gating
```
Raw logits → torch.sigmoid → probabilities

Accept if ANY:
├─► Margin rule: (best - second_best) ≥ 0.05
├─► Dominance rule: best ≥ 1.5 × mean(all)
└─► Retrieval support: best in top 3 bi-encoder

Reject ONLY if:
    margin < 0.05 AND
    dominance fails AND
    best_prob < 0.01

Result: High recall for syllabus domain filtering
```

## PDF Question Parsing

### Unified Preprocessing
```
PDF → split_questions()
  ├─► Extract raw text
  ├─► Detect Part A/B/C boundaries
  ├─► Split by question numbers
  ├─► Remove trailing "Part B/C" markers
  └─► Pass to EvaluationService

EvaluationService.clean_question_text()
  ├─► Remove leading numbering
  ├─► Remove Part markers (start & end)
  ├─► Remove bullets, marks
  ├─► Unicode normalization
  └─► Return cleaned text

No double-cleaning, consistent preprocessing
```

## API Endpoints Map

### Domain Management
```
POST   /domains/create
       → Create domain in MongoDB

GET    /domains/{user_id}
       → List domains from MongoDB

DELETE /domains/{user_id}/{domain}
       → Delete domain + all data from MongoDB
```

### Syllabus Management
```
POST   /domains/{user_id}/{domain}/syllabus
       → Upload & parse to MongoDB
       → Triggers index rebuild if books exist

GET    /domains/{user_id}/{domain}/syllabus/view
       → View parsed JSON from MongoDB

GET    /domains/{user_id}/{domain}/files/syllabus
       → Download from MongoDB GridFS

DELETE /domains/{user_id}/{domain}/syllabus
       → Delete from MongoDB
```

### Book Management
```
POST   /domains/{user_id}/{domain}/books
       → Upload to MongoDB GridFS
       → Build FAISS index
       → Auto-trigger enrichment

DELETE /domains/{user_id}/{domain}/books/{name}
       → Delete from MongoDB
       → Rebuild index
```

### Evaluation
```
POST   /evaluate
       → Single question evaluation

POST   /evaluate/pdf
       → Batch PDF evaluation
       → Unified preprocessing
```

### History
```
GET    /history/{user_id}
       → Get from MongoDB

DELETE /history/{user_id}/single/{id}
DELETE /history/{user_id}/pdf/{id}
DELETE /history/{user_id}/clear
       → Delete from MongoDB
```

## Model Registry

```
┌────────────────────────────────────────┐
│  Bi-Encoder (Retrieval)                │
│  all-MiniLM-L6-v2                      │
│  • 384 dimensions                      │
│  • Fast semantic search                │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Cross-Encoder (Reranking)             │
│  ms-marco-MiniLM-L-6-v2                │
│  • Sigmoid probability conversion      │
│  • Relative rank-based gating          │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Bloom Classifier                      │
│  final_bloom_model (DistilBERT)        │
│  • BT1-BT6 classification              │
│  • Fine-tuned on academic questions    │
└────────────────────────────────────────┘

┌────────────────────────────────────────┐
│  Enrichment LLM                        │
│  Groq: llama-3.3-70b-versatile         │
│  • Subtopic generation                 │
│  • 5-7 subtopics per topic             │
└────────────────────────────────────────┘
```

## Performance Characteristics

### MongoDB Operations
```
Save syllabus: ~50ms
Save book (10MB): ~200ms
Save FAISS index (50MB): ~500ms
Load index: ~300ms
```

### Evaluation Operations
```
Single question: ~550ms
├─► Preprocessing: ~5ms
├─► FAISS retrieval: ~50ms
├─► Cross-encoder: ~300ms
└─► Bloom classification: ~200ms

PDF (50 questions): ~28s
```

### Enrichment Operations
```
Enrich syllabus (30 topics): ~5min
├─► Retrieve candidates: ~30s
├─► Rerank: ~1min
└─► Groq LLM generation: ~3.5min
```

## Error Handling

### MongoDB Write Verification
```
Every write operation:
├─► result.acknowledged check
├─► Log success/failure
└─► Raise exception if failed

Ensures data consistency
```

### Evaluation Fallbacks
```
Topic matching fails
└─► Return "Out of Syllabus"
    ├─► unit: null
    ├─► topic: "Out of Syllabus"
    └─► out_of_syllabus: true

Enrichment fails
└─► Use raw chunk text as subtopics
    (non-critical, system continues)
```

## Security & Configuration

```
.env file (not committed)
├── MONGODB_URI=mongodb://localhost:27017/
├── MONGODB_DB=qn_evaluator
├── GROQ_API_KEY=...
└── USE_MONGODB_STORAGE=true (enforced)

MongoDB
├── Local development: localhost:27017
├── Production: MongoDB Atlas
└── GridFS for large files (>16MB)
```

## Deployment Architecture

### Current: Local Development
```
✓ MongoDB local instance
✓ FastAPI backend (port 8002)
✓ React frontend (port 5173)
✓ All data in MongoDB
✗ No cloud backup
```

### Future: Production
```
✓ MongoDB Atlas (cloud)
✓ EC2/ECS deployment
✓ S3 for model files
✓ CloudFront for frontend
✓ Automated backups
```
