# Question Intelligence System v2.0 - API Documentation

**Base URL**: `http://localhost:8002`

**CORS Enabled**: `http://localhost:5173`, `http://localhost:3000`

---

## 📋 API Endpoints Overview

### Domain Management
- `POST /domains/create` - Create new domain
- `GET /domains/{user_id}` - List all domains for user
- `DELETE /domains/{user_id}/{domain_name}` - Delete domain

### Syllabus Management
- `POST /domains/{user_id}/{domain_name}/syllabus` - Upload syllabus

### Books Management
- `POST /domains/{user_id}/{domain_name}/books` - Upload books

### Domain Status
- `GET /domains/{user_id}/{domain_name}/status` - Get domain setup status

### Evaluation
- `POST /evaluate` - Evaluate single question
- `POST /evaluate/pdf` - Evaluate questions from PDF

---

## 🔧 Detailed API Specifications

### 1. Create Domain

**Endpoint**: `POST /domains/create`

**Request Body** (JSON):
```json
{
  "user_id": "john_doe",
  "domain_name": "JAVA_PROGRAMMING"
}
```

**Response** (200 OK):
```json
{
  "message": "Domain created successfully",
  "user_id": "john_doe",
  "domain_name": "JAVA_PROGRAMMING",
  "path": "data/john_doe/JAVA_PROGRAMMING"
}
```

**Error Responses**:
- `500` - Internal server error

**Example (curl)**:
```bash
curl -X POST http://localhost:8002/domains/create \
  -H "Content-Type: application/json" \
  -d '{"user_id": "john_doe", "domain_name": "JAVA_PROGRAMMING"}'
```

---

### 2. List Domains

**Endpoint**: `GET /domains/{user_id}`

**Path Parameters**:
- `user_id` (string) - User identifier

**Response** (200 OK):
```json
{
  "domains": ["JAVA_PROGRAMMING", "OPERATING_SYSTEMS", "DBMS"]
}
```

**Example (curl)**:
```bash
curl http://localhost:8002/domains/john_doe
```

---

### 3. Delete Domain

**Endpoint**: `DELETE /domains/{user_id}/{domain_name}`

**Path Parameters**:
- `user_id` (string) - User identifier
- `domain_name` (string) - Domain name

**Response** (200 OK):
```json
{
  "message": "Domain deleted successfully",
  "user_id": "john_doe",
  "domain_name": "JAVA_PROGRAMMING"
}
```

**Error Responses**:
- `404` - Domain not found

**Example (curl)**:
```bash
curl -X DELETE http://localhost:8002/domains/john_doe/JAVA_PROGRAMMING
```

---

### 4. Upload Syllabus

**Endpoint**: `POST /domains/{user_id}/{domain_name}/syllabus`

**Path Parameters**:
- `user_id` (string) - User identifier
- `domain_name` (string) - Domain name

**Request Body** (multipart/form-data):
- `file` - Syllabus file (PDF or TXT)

**Response** (200 OK):
```json
{
  "message": "Syllabus uploaded successfully",
  "course_name": "Object Oriented Programming with Java",
  "units_count": 5,
  "co_count": 6
}
```

**Error Responses**:
- `400` - Invalid file type (only PDF/TXT allowed)
- `404` - Domain not found
- `500` - Processing error

**Example (curl)**:
```bash
curl -X POST http://localhost:8002/domains/john_doe/JAVA_PROGRAMMING/syllabus \
  -F "file=@syllabus.pdf"
```

---

### 5. Upload Books

**Endpoint**: `POST /domains/{user_id}/{domain_name}/books`

**Path Parameters**:
- `user_id` (string) - User identifier
- `domain_name` (string) - Domain name

**Request Body** (multipart/form-data):
- `files` - Multiple PDF files

**Response** (200 OK):
```json
{
  "message": "Books uploaded and indexed successfully",
  "books_uploaded": 3,
  "chunks_indexed": 2866
}
```

**Error Responses**:
- `400` - Invalid file type (only PDF allowed)
- `404` - Domain not found
- `500` - Processing error

**Example (curl)**:
```bash
curl -X POST http://localhost:8002/domains/john_doe/JAVA_PROGRAMMING/books \
  -F "files=@book1.pdf" \
  -F "files=@book2.pdf" \
  -F "files=@book3.pdf"
```

**Note**: This endpoint builds/rebuilds the FAISS index. Processing time depends on number and size of books.

---

### 6. Get Domain Status

**Endpoint**: `GET /domains/{user_id}/{domain_name}/status`

**Path Parameters**:
- `user_id` (string) - User identifier
- `domain_name` (string) - Domain name

**Response** (200 OK):
```json
{
  "syllabus_uploaded": true,
  "books_uploaded": true,
  "index_ready": true,
  "chunks_count": 2866
}
```

**Error Responses**:
- `404` - Domain not found

**Example (curl)**:
```bash
curl http://localhost:8002/domains/john_doe/JAVA_PROGRAMMING/status
```

**Frontend Usage**: Use this to show setup progress:
- ❌ Setup incomplete (syllabus_uploaded: false)
- ❌ Setup incomplete (books_uploaded: false)
- ✅ Ready for evaluation (both true)

---

### 7. Evaluate Single Question

**Endpoint**: `POST /evaluate`

**Request Body** (JSON):
```json
{
  "user_id": "john_doe",
  "domain_name": "JAVA_PROGRAMMING",
  "question": "Explain why multiple inheritance is not applicable in Java?"
}
```

**Response** (200 OK):
```json
{
  "question": "Explain why multiple inheritance is not applicable in Java?",
  "unit": "Unit I",
  "topic": "Inheritance",
  "course_outcomes": ["CO1"],
  "bloom_level": "BT2",
  "bloom_confidence": 0.63,
  "subtopics": [
    "Multiple inheritance in Java",
    "Diamond problem in inheritance",
    "Interface-based multiple inheritance"
  ],
  "relevant_chunks": [
    {
      "chunk_id": 145,
      "book_name": "Java_Complete_Reference.pdf",
      "page": 23,
      "text": "Java does not support multiple inheritance...",
      "score": 0.89
    }
  ]
}
```

**Error Responses**:
- `400` - Missing syllabus or FAISS index
  ```json
  {
    "error": "Missing syllabus",
    "details": "Please upload syllabus first"
  }
  ```
- `404` - Domain not found
- `500` - Evaluation failed

**Example (curl)**:
```bash
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "john_doe",
    "domain_name": "JAVA_PROGRAMMING",
    "question": "What is polymorphism?"
  }'
```

---

### 8. Evaluate Questions from PDF

**Endpoint**: `POST /evaluate/pdf`

**Request Body** (multipart/form-data):
- `user_id` (string) - User identifier
- `domain_name` (string) - Domain name
- `file` - PDF file containing questions

**Response** (200 OK):
```json
{
  "total_questions": 5,
  "results": [
    {
      "question_number": 1,
      "question": "What is polymorphism in Java?",
      "unit": "Unit I",
      "topic": "Polymorphism",
      "course_outcomes": ["CO1"],
      "bloom_level": "BT1",
      "bloom_confidence": 0.78,
      "subtopics": ["Runtime polymorphism", "Compile-time polymorphism"],
      "relevant_chunks": [...]
    },
    {
      "question_number": 2,
      "question": "Explain exception handling...",
      "unit": "Unit III",
      "topic": "Exception Handling",
      "course_outcomes": ["CO3"],
      "bloom_level": "BT2",
      "bloom_confidence": 0.65,
      "subtopics": [...],
      "relevant_chunks": [...]
    }
  ]
}
```

**Error Responses**:
- `400` - Invalid file type or missing syllabus/index
- `404` - Domain not found
- `500` - Processing error

**Example (curl)**:
```bash
curl -X POST http://localhost:8002/evaluate/pdf \
  -F "user_id=john_doe" \
  -F "domain_name=JAVA_PROGRAMMING" \
  -F "file=@questions.pdf"
```

---

## 🔄 Frontend Integration Flow

### 1. User Login
```javascript
// Store user_id in state/context
const userId = "john_doe";
```

### 2. Create Domain
```javascript
const response = await fetch('http://localhost:8002/domains/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    domain_name: "JAVA_PROGRAMMING"
  })
});
```

### 3. Upload Syllabus
```javascript
const formData = new FormData();
formData.append('file', syllabusFile);

const response = await fetch(
  `http://localhost:8002/domains/${userId}/JAVA_PROGRAMMING/syllabus`,
  { method: 'POST', body: formData }
);
```

### 4. Upload Books
```javascript
const formData = new FormData();
bookFiles.forEach(file => formData.append('files', file));

const response = await fetch(
  `http://localhost:8002/domains/${userId}/JAVA_PROGRAMMING/books`,
  { method: 'POST', body: formData }
);
```

### 5. Check Status (Polling)
```javascript
const checkStatus = async () => {
  const response = await fetch(
    `http://localhost:8002/domains/${userId}/JAVA_PROGRAMMING/status`
  );
  const status = await response.json();
  
  if (status.syllabus_uploaded && status.books_uploaded) {
    // Ready for evaluation
    setSetupComplete(true);
  }
};
```

### 6. Evaluate Question
```javascript
const response = await fetch('http://localhost:8002/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: userId,
    domain_name: "JAVA_PROGRAMMING",
    question: userQuestion
  })
});

const result = await response.json();
// Display result.unit, result.bloom_level, etc.
```

---

## ⚠️ Error Handling

All errors return structured JSON:

```json
{
  "error": "Error type",
  "details": "Detailed error message"
}
```

**HTTP Status Codes**:
- `200` - Success
- `400` - Bad request (invalid input, missing dependencies)
- `404` - Resource not found (domain doesn't exist)
- `500` - Internal server error

**Frontend Error Handling**:
```javascript
try {
  const response = await fetch(endpoint, options);
  
  if (!response.ok) {
    const error = await response.json();
    
    if (response.status === 400) {
      // Show user-friendly message
      alert(error.details || error.error);
    } else if (response.status === 404) {
      // Redirect to domain creation
      navigate('/create-domain');
    } else {
      // Generic error
      alert('Something went wrong. Please try again.');
    }
    return;
  }
  
  const data = await response.json();
  // Process success
} catch (err) {
  console.error('Network error:', err);
  alert('Unable to connect to server');
}
```

---

## 🚀 Testing

Run the test suite:
```bash
cd backend
python test_api.py
```

This will test all endpoints and verify:
- Domain creation/deletion
- Syllabus upload and parsing
- Books upload and indexing
- Question evaluation
- Error handling

---

## 📊 Performance Notes

- **Model Loading**: All models load once at startup (~5-10 seconds)
- **Syllabus Upload**: < 1 second
- **Books Upload**: ~2-5 seconds per book (depends on size)
- **FAISS Indexing**: ~10-30 seconds for 3 books (2866 chunks)
- **Single Question Evaluation**: ~1-2 seconds
- **PDF Evaluation**: ~1-2 seconds per question

**Memory Usage**: ~1.1 GB (optimized with model registry)

---

## 🔐 Security Notes

- No authentication implemented (add JWT/OAuth for production)
- File uploads validated (only PDF/TXT allowed)
- Path traversal prevented (uses Path library)
- CORS restricted to localhost (update for production)

---

## 📝 Next Steps for Frontend

1. Implement user authentication
2. Create domain management UI
3. Build file upload components with progress bars
4. Design evaluation result display
5. Add PDF batch evaluation UI
6. Implement domain switching
7. Add export functionality (CSV/PDF reports)
