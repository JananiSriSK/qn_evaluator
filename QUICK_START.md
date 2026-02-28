# Quick Start Guide - Refactored System

## Prerequisites
```bash
pip install -r backend/requirements_v2.txt
```

## Step 1: Migrate Existing Data
```bash
cd backend
python migrate.py
```

**Output:**
```
Migrating to: backend/data/default_user/JAVA_PROGRAMMING
✓ Syllabus copied
✓ Book copied: core-and-advanced-java-black-book-*.pdf
✓ Book copied: Java - How to Program 10th Ed-*.pdf
✓ Book copied: java_new.pdf
✓ FAISS index copied
✓ Metadata copied

✓ Migration complete!
Domain: default_user/JAVA_PROGRAMMING
```

## Step 2: Test the System
```bash
python test_new_system.py
```

**Expected Output:**
```
================================================================================
TESTING NEW DOMAIN-BASED ARCHITECTURE
================================================================================

1. Initializing services...

2. Checking domain: default_user/JAVA_PROGRAMMING
   ✓ Course: JAVA PROGRAMMING
   ✓ Units: 5
   ✓ COs: ['CO1', 'CO2', 'CO3', 'CO4', 'CO5', 'CO6']

3. Checking FAISS index...
   ✓ Index loaded: 2866 vectors
   ✓ Metadata: 2866 chunks

4. Testing Bloom classifier...
   ✓ Bloom Level: BT2
   ✓ Confidence: 0.876

5. Testing full evaluation pipeline...
   Question: explain why multiple inheritance is not applicable in java?

   RESULTS:
   ✓ Bloom Level: BT2
   ✓ Unit: I - JAVA BASICS
   ✓ Topic: Inheritance
   ✓ Course Outcomes: ['CO1']
      CO1: Implement Object-Oriented concepts of Java programming.

   Relevant Subtopics:
      - Inheritance Basics
      - Superclass Subclass
      - Types of Inheritance

   Top Relevant Chunks:
      1. java_new.pdf... (Page 17)
         18 | P a g e o For Code Reusability. Types of inheritance in java...
      2. core-and-advanced-java-black-book-... (Page 122)
         Let's learn about inheritance in Java in the next section...

================================================================================
✓ ALL TESTS PASSED!
================================================================================
```

## Step 3: Start the Server
```bash
python main_v2.py
```

**Server:** `http://localhost:8001`

## API Usage Examples

### 1. Create New Domain
```bash
curl -X POST "http://localhost:8001/api/domain/create" \
  -F "user_id=user123" \
  -F "domain_name=PYTHON_PROGRAMMING" \
  -F "syllabus_file=@syllabus.pdf"
```

### 2. Add Books to Domain
```bash
curl -X POST "http://localhost:8001/api/domain/add-books" \
  -F "user_id=user123" \
  -F "domain_name=PYTHON_PROGRAMMING" \
  -F "books=@book1.pdf" \
  -F "books=@book2.pdf"
```

### 3. Evaluate Question
```bash
curl -X POST "http://localhost:8001/api/evaluate" \
  -F "user_id=default_user" \
  -F "domain_name=JAVA_PROGRAMMING" \
  -F "question=explain why multiple inheritance is not applicable in java?"
```

**Response:**
```json
{
  "question": "explain why multiple inheritance is not applicable in java?",
  "bloom_level": "BT2",
  "bloom_confidence": 0.876,
  "unit": "I",
  "unit_title": "JAVA BASICS",
  "topic": "Inheritance",
  "course_outcomes": ["CO1"],
  "subtopics": [
    "Inheritance Basics",
    "Superclass Subclass",
    "Types of Inheritance",
    "Single Inheritance",
    "Multilevel Inheritance"
  ],
  "relevant_chunks": [...]
}
```

### 4. Get Domain Info
```bash
curl "http://localhost:8001/api/domain/info?user_id=default_user&domain_name=JAVA_PROGRAMMING"
```

## Troubleshooting

### Issue: Bloom model not found
**Solution:** Ensure model exists at:
```
backend/bloom/bloom_model_final/content/final_bloom_model/
```

### Issue: Domain not found
**Solution:** Run migration script:
```bash
python backend/migrate.py
```

### Issue: FAISS index not built
**Solution:** Add books to domain:
```bash
# Books must be in backend/data/{user_id}/{domain_name}/books/
python -c "from services.domain_manager import DomainManager; dm = DomainManager(); dm.build_vector_db('user_id', 'domain_name')"
```

## Architecture Overview

```
Request → FastAPI → EvaluationService
                         ↓
                    ┌────┴────┐
                    ↓         ↓
            RetrievalService  BloomService
                    ↓              ↓
              DomainManager    Bloom Model
                    ↓
              FAISS Index
```

## Key Features

✅ **Domain Isolation** - Each domain has independent index
✅ **Bloom Integration** - Automatic taxonomy classification
✅ **Syllabus Mapping** - Intelligent topic matching
✅ **Multi-format Support** - PDF and TXT syllabus
✅ **Scalable** - Add unlimited books per domain
✅ **Fast** - FAISS vector search with reranking

## Next Steps

1. Test with your own questions
2. Create new domains for different courses
3. Integrate with frontend
4. Add authentication for multi-user support
