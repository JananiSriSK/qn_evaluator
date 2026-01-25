# Question Intelligence System - Backend

Agent-based system for syllabus-aware Course Outcome (CO) mapping using lightweight models.

## Architecture

```
backend/
├── agent/orchestrator.py      # Main workflow coordinator
├── tools/                     # Specialized processing tools
│   ├── enrichment.py         # flan-t5-small for topic inference
│   ├── embedder.py           # e5-small-v2 for embeddings
│   ├── faiss_storage.py      # FAISS vector storage
│   └── evaluation.py         # Question-CO evaluation
├── models/schemas.py         # Pydantic data models
├── services/preprocessing.py # Text normalization
└── storage/                  # FAISS indices and metadata
```

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Run the server:
```bash
python main.py
```

## API Usage

### POST /ingest-course

Automatically processes course data through the complete pipeline:

```json
{
  "course_name": "Data Structures",
  "syllabus": [
    {
      "unit_number": 1,
      "title": "Arrays and Linked Lists",
      "content": "Introduction to arrays, dynamic arrays, singly linked lists, doubly linked lists"
    }
  ],
  "course_outcomes": [
    {
      "id": "CO1",
      "description": "Understand fundamental data structures"
    }
  ]
}
```

### POST /evaluate-question

Evaluates questions against course content to predict Course Outcomes:

```json
{
  "course_name": "Data Structures",
  "question": "Explain the implementation of a stack using arrays"
}
```

Response:
```json
{
  "predicted_co": "CO1: Understand fundamental data structures",
  "relevance_score": 0.85,
  "matched_unit": "Stacks and Queues",
  "matched_syllabus_context": "Stack operations, queue operations..."
}
```

## Workflow

**Course Ingestion:**
1. **Text Preprocessing**: Normalizes syllabus content
2. **Content Enrichment**: Uses flan-t5-small to infer subtopics
3. **Embedding Generation**: Creates vectors using e5-small-v2
4. **Vector Storage**: Stores in FAISS with CO mapping metadata

**Assisted Subtopic Ingestion:**
1. **Subtopic Suggestion**: Uses flan-t5-small to suggest subtopics for each unit
2. **Professor Review**: Allows editing/confirmation of suggested subtopics
3. **Semantic CO Mapping**: Maps each subtopic to most relevant CO automatically
4. **Granular Storage**: Stores each subtopic as individual semantic chunk

**Question Evaluation:**
1. **Question Preprocessing**: Normalizes question text
2. **Embedding Generation**: Creates question vector using e5-small-v2
3. **Similarity Search**: Finds relevant syllabus content in FAISS
4. **CO Prediction**: Infers most relevant Course Outcome using semantic alignment

## Models Used

- **flan-t5-small**: Topic enrichment (inference only)
- **e5-small-v2**: Text embeddings
- **FAISS**: Local vector storage (CPU-only)

All models are loaded once at startup for efficiency.