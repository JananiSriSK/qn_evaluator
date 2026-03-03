# Current System Architecture

## High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (React + Vite)                       │
│                   http://localhost:5173                          │
│  • Domain Setup UI                                               │
│  • Question Evaluation UI (Single + PDF)                        │
│  • History Management UI                                         │
│  • Modal Popups (no browser alerts)                             │
└────────────────────────────┬────────────────────────────────────┘
                             │ REST API
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Backend (FastAPI)                             │
│                   http://localhost:8002                          │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                    main_v2.py                             │  │
│  │  • Domain CRUD endpoints                                  │  │
│  │  • Syllabus upload/download                               │  │
│  │  • Book upload (triggers auto-enrichment)                 │  │
│  │  • Single question evaluation                             │  │
│  │  • PDF batch evaluation                                   │  │
│  │  • History management                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│                             │                                     │
│         ┌───────────────────┼───────────────────┐                │
│         ▼                   ▼                   ▼                │
│  ┌─────────────┐   ┌──────────────┐   ┌──────────────┐         │
│  │   Domain    │   │  Evaluation  │   │  Enrichment  │         │
│  │   Manager   │   │   Service    │   │   Service    │         │
│  │             │   │              │   │  (Groq LLM)  │         │
│  └──────┬──────┘   └──────┬───────┘   └──────┬───────┘         │
│         │                  │                   │                 │
│         └──────────────────┼───────────────────┘                 │
│                            ▼                                     │
│                   ┌──────────────┐                              │
│                   │   MongoDB    │                              │
│                   │   Storage    │                              │
│                   └──────────────┘                              │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│              MongoDB Compass (localhost:27017)                   │
│              Database: qn_evaluator                              │
│                                                                   │
│  Collections:                                                    │
│  ├── domains (user_id, domain_name, created_at)                 │
│  ├── syllabus (syllabus_data, original_file_id, updated_at)     │
│  ├── books (filename, file_id, uploaded_at)                     │
│  ├── indexes (file_id, metadata[], chunks_count)                │
│  └── history (single_questions[], pdf_evaluations[])            │
│                                                                   │
│  GridFS (fs.files, fs.chunks):                                  │
│  ├── Syllabus files (PDF/TXT)                                   │
│  ├── Book PDFs                                                  │
│  └── FAISS index binaries                                       │
└─────────────────────────────────────────────────────────────────┘
```

## Complete Evaluation Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│  User Input: "Define inheritance with an example"               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 1: Unified Preprocessing                                   │
│  clean_question_text()                                           │
│                                                                   │
│  • Remove leading numbering (Q.1, 3., 16(a))                    │
│  • Remove Part A/B/C markers (start & end)                       │
│  • Remove bullets (•, ○, ■)                                      │
│  • Remove marks patterns (10 Marks, 2×5=10)                      │
│  • Unicode normalization (NFKC)                                  │
│  • Collapse whitespace                                           │
│                                                                   │
│  Output: "Define inheritance with an example"                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 2: FAISS Retrieval (Bi-Encoder)                           │
│  Model: all-MiniLM-L6-v2                                         │
│                                                                   │
│  • Embed question (384 dims)                                     │
│  • Search FAISS index                                            │
│  • Retrieve top 10 semantic chunks                               │
│  • From enriched book content                                    │
│                                                                   │
│  Output: 10 candidate chunks with book references                │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 3: Topic Matching (Hybrid Approach)                       │
│                                                                   │
│  3a. Bi-Encoder Candidate Selection                             │
│      • Embed question                                            │
│      • Match against enriched topics                             │
│      • topic_text = topic_name + enriched_subtopics              │
│      • Select top 10 candidates                                  │
│                                                                   │
│  3b. Cross-Encoder Reranking                                     │
│      Model: ms-marco-MiniLM-L-6-v2                               │
│      • Rerank 10 candidates                                      │
│      • Get raw logits                                            │
│      • Convert to probabilities: torch.sigmoid(logits)           │
│                                                                   │
│  3c. Relative Rank-Based Gating (NEW)                           │
│      Accept if ANY condition met:                                │
│      ├─► Margin rule: (best - second_best) ≥ 0.05               │
│      ├─► Dominance rule: best ≥ 1.5 × mean(all_probs)           │
│      └─► Retrieval support: best in top 3 bi-encoder            │
│                                                                   │
│      Reject ONLY if ALL fail:                                    │
│      └─► margin < 0.05 AND dominance fails AND prob < 0.01      │
│                                                                   │
│  Output: Matched topic "Inheritance" (Unit I: JAVA BASICS)       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 4: Bloom Taxonomy Classification                           │
│  Model: final_bloom_model (DistilBERT fine-tuned)               │
│                                                                   │
│  • Classify into BT1-BT6                                         │
│  • BT1: Remember (Define, List, State)                          │
│  • BT2: Understand (Explain, Describe)                          │
│  • BT3: Apply (Implement, Demonstrate)                          │
│  • BT4: Analyze (Compare, Differentiate)                        │
│  • BT5: Evaluate (Justify, Critique)                            │
│  • BT6: Create (Design, Develop)                                │
│  • Return confidence score                                       │
│                                                                   │
│  Output: BT1 (96% confidence)                                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  STEP 5: Course Outcome Mapping                                 │
│                                                                   │
│  • Map unit to CO (Unit I → CO1)                                │
│  • Return enriched subtopics                                     │
│  • Return relevant book chunks                                   │
│                                                                   │
│  Final Output:                                                   │
│  {                                                               │
│    "question": "Define inheritance with an example",             │
│    "unit": "I",                                                  │
│    "unit_title": "JAVA BASICS",                                 │
│    "topic": "Inheritance",                                       │
│    "bloom_level": "BT1",                                         │
│    "bloom_confidence": 0.96,                                     │
│    "course_outcomes": ["CO1"],                                   │
│    "subtopics": ["Class Hierarchy", "extends keyword", ...],    │
│    "out_of_syllabus": false                                     │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
```

## Syllabus Enrichment Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  User uploads syllabus.txt                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Parse Syllabus                                                  │
│  • Extract units (I, II, III, IV, V)                            │
│  • Extract topics per unit                                       │
│  • Extract course outcomes (CO1-CO5)                             │
│  • Save to MongoDB (syllabus collection)                         │
│  • Save original file to GridFS                                  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  User uploads books (PDFs)                                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Build FAISS Index                                               │
│  • Chunk books (180 words, 40 overlap)                          │
│  • Embed chunks with bi-encoder                                  │
│  • Build FAISS IndexFlatIP                                       │
│  • Serialize to bytes                                            │
│  • Save to MongoDB GridFS                                        │
│  • Save metadata to indexes collection                           │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  AUTO-TRIGGER: Syllabus Enrichment                              │
│  EnrichmentService.enrich_syllabus_data()                        │
│                                                                   │
│  For each topic in syllabus:                                     │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │ 1. Retrieve top 30 chunks (bi-encoder)                     │ │
│  │ 2. Rerank to top 10 (cross-encoder)                        │ │
│  │ 3. Generate 5-7 subtopics (Groq LLM)                       │ │
│  │    Model: llama-3.3-70b-versatile                          │ │
│  │    Prompt: "Generate subtopics for [topic] based on..."    │ │
│  │ 4. Add to topic:                                            │ │
│  │    • enriched_subtopics_from_books: [...]                  │ │
│  │    • source_references: [{chunk_id, book, page}]           │ │
│  └────────────────────────────────────────────────────────────┘ │
│                                                                   │
│  Save enriched syllabus back to MongoDB                          │
└─────────────────────────────────────────────────────────────────┘
```

## PDF Question Parsing

```
┌─────────────────────────────────────────────────────────────────┐
│  User uploads question_paper.pdf                                 │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PDFQuestionParser.split_questions()                             │
│                                                                   │
│  • Extract text from PDF (PyMuPDF)                               │
│  • Detect Part A/B/C boundaries                                  │
│  • Split by question numbers (1., Q2, Question 3)                │
│  • Remove trailing "Part B/C" markers                            │
│  • Remove leading "Part B/C" markers                             │
│  • Handle OR questions: 19(a), 19(b)                             │
│  • Pass raw text to evaluation                                   │
│                                                                   │
│  Output: [                                                       │
│    {number: "1", text: "...", part: "Part A"},                  │
│    {number: "10", text: "... Part B", part: "Part B"},          │
│    ...                                                           │
│  ]                                                               │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  EvaluationService.clean_question_text()                         │
│  (Unified preprocessing - removes "Part B" from text)            │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  Evaluate each question through pipeline                         │
│  Save results to MongoDB history                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Model Registry

```
┌─────────────────────────────────────────────────────────────────┐
│  Bi-Encoder (Semantic Retrieval)                                │
│  all-MiniLM-L6-v2                                                │
│  • 384 dimensions                                                │
│  • Fast cosine similarity search                                 │
│  • Used for: FAISS retrieval, topic candidate selection          │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Cross-Encoder (Reranking)                                       │
│  ms-marco-MiniLM-L-6-v2                                          │
│  • Trained on MS MARCO passage ranking                           │
│  • Produces raw logits (can be negative)                         │
│  • NEW: Sigmoid probability conversion                           │
│  • NEW: Relative rank-based gating                               │
│  • Used for: Topic matching refinement                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Bloom Classifier                                                │
│  final_bloom_model (DistilBERT fine-tuned)                       │
│  • 6-class classification (BT1-BT6)                              │
│  • Fine-tuned on academic questions dataset                      │
│  • Softmax confidence scores                                     │
│  • Used for: Bloom taxonomy prediction                           │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Enrichment LLM                                                  │
│  Groq: llama-3.3-70b-versatile                                   │
│  • Temperature: 0.3 (deterministic)                              │
│  • Max tokens: 500                                               │
│  • Generates 5-7 subtopics per topic                             │
│  • Used for: Syllabus enrichment                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Key Improvements Implemented

### 1. MongoDB-Only Storage
- **Before**: Mixed local files + MongoDB
- **After**: All data in MongoDB + GridFS
- **Benefit**: Consistent storage, no sync issues

### 2. Relative Rank-Based Gating
- **Before**: Absolute threshold (raw_logit < -2.0)
- **After**: Sigmoid + margin/dominance/retrieval rules
- **Benefit**: Higher recall, fewer false "Out of Syllabus"

### 3. Unified Preprocessing
- **Before**: Double cleaning (PDF parser + evaluation)
- **After**: Single clean_question_text() in evaluation
- **Benefit**: Consistent preprocessing, no text corruption

### 4. Auto-Enrichment
- **Before**: Manual enrichment script
- **After**: Auto-triggered on book upload
- **Benefit**: Always up-to-date enriched subtopics

### 5. UI Improvements
- **Before**: Browser alert()/confirm()
- **After**: Modal component popups
- **Benefit**: Better UX, consistent styling

### 6. Part Marker Removal
- **Before**: "Part B" appeared in questions
- **After**: Removed from both start and end
- **Benefit**: Clean question text

## Performance Metrics

```
Operation                    Time
─────────────────────────────────────
MongoDB save syllabus        ~50ms
MongoDB save book (10MB)     ~200ms
MongoDB save FAISS (50MB)    ~500ms
MongoDB load index           ~300ms

Single question eval         ~550ms
├─ Preprocessing             ~5ms
├─ FAISS retrieval           ~50ms
├─ Cross-encoder rerank      ~300ms
└─ Bloom classification      ~200ms

PDF batch (50 questions)     ~28s
├─ PDF parsing               ~500ms
└─ Evaluation (50×550ms)     ~27.5s

Syllabus enrichment          ~5min
├─ Retrieve candidates       ~30s
├─ Rerank                    ~1min
└─ Groq LLM generation       ~3.5min
```

## Technology Stack

```
Backend:
├── FastAPI (web framework)
├── PyMongo (MongoDB driver)
├── GridFS (large file storage)
├── PyMuPDF (PDF parsing)
├── sentence-transformers (embeddings)
├── faiss-cpu (vector search)
├── torch (deep learning)
├── transformers (Bloom model)
└── groq (LLM API)

Frontend:
├── React 18
├── Vite (build tool)
├── Axios (HTTP client)
└── CSS modules

Database:
└── MongoDB 7.0 (local/Atlas)
```
