# API Quick Reference Card

## 🚀 Base URL
```
http://localhost:8002
```

## 📋 All Endpoints

### Health Check
```http
GET /
```

### Domain Management
```http
POST   /domains/create
GET    /domains/{user_id}
DELETE /domains/{user_id}/{domain_name}
```

### Setup
```http
POST /domains/{user_id}/{domain_name}/syllabus
POST /domains/{user_id}/{domain_name}/books
GET  /domains/{user_id}/{domain_name}/status
```

### Evaluation
```http
POST /evaluate
POST /evaluate/pdf
```

---

## 🔥 Quick Examples

### JavaScript/Fetch

```javascript
// 1. Create Domain
await fetch('http://localhost:8002/domains/create', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ user_id: 'john', domain_name: 'JAVA' })
});

// 2. Upload Syllabus
const formData = new FormData();
formData.append('file', syllabusFile);
await fetch('http://localhost:8002/domains/john/JAVA/syllabus', {
  method: 'POST',
  body: formData
});

// 3. Upload Books
const formData = new FormData();
bookFiles.forEach(f => formData.append('files', f));
await fetch('http://localhost:8002/domains/john/JAVA/books', {
  method: 'POST',
  body: formData
});

// 4. Check Status
const res = await fetch('http://localhost:8002/domains/john/JAVA/status');
const status = await res.json();
// { syllabus_uploaded: true, books_uploaded: true, ... }

// 5. Evaluate Question
await fetch('http://localhost:8002/evaluate', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    user_id: 'john',
    domain_name: 'JAVA',
    question: 'What is polymorphism?'
  })
});
```

### Python/Requests

```python
import requests

# 1. Create Domain
requests.post('http://localhost:8002/domains/create', json={
    'user_id': 'john',
    'domain_name': 'JAVA'
})

# 2. Upload Syllabus
files = {'file': open('syllabus.pdf', 'rb')}
requests.post('http://localhost:8002/domains/john/JAVA/syllabus', files=files)

# 3. Upload Books
files = [
    ('files', open('book1.pdf', 'rb')),
    ('files', open('book2.pdf', 'rb'))
]
requests.post('http://localhost:8002/domains/john/JAVA/books', files=files)

# 4. Check Status
r = requests.get('http://localhost:8002/domains/john/JAVA/status')
print(r.json())

# 5. Evaluate Question
requests.post('http://localhost:8002/evaluate', json={
    'user_id': 'john',
    'domain_name': 'JAVA',
    'question': 'What is polymorphism?'
})
```

### cURL

```bash
# 1. Create Domain
curl -X POST http://localhost:8002/domains/create \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","domain_name":"JAVA"}'

# 2. Upload Syllabus
curl -X POST http://localhost:8002/domains/john/JAVA/syllabus \
  -F "file=@syllabus.pdf"

# 3. Upload Books
curl -X POST http://localhost:8002/domains/john/JAVA/books \
  -F "files=@book1.pdf" \
  -F "files=@book2.pdf"

# 4. Check Status
curl http://localhost:8002/domains/john/JAVA/status

# 5. Evaluate Question
curl -X POST http://localhost:8002/evaluate \
  -H "Content-Type: application/json" \
  -d '{"user_id":"john","domain_name":"JAVA","question":"What is polymorphism?"}'
```

---

## 📊 Response Formats

### Success (200)
```json
{
  "message": "...",
  "data": { ... }
}
```

### Error (400/404/500)
```json
{
  "error": "Error type",
  "details": "Detailed message"
}
```

### Evaluation Result
```json
{
  "question": "...",
  "unit": "Unit I",
  "topic": "Polymorphism",
  "course_outcomes": ["CO1"],
  "bloom_level": "BT2",
  "bloom_confidence": 0.63,
  "subtopics": [...],
  "relevant_chunks": [...]
}
```

---

## ⚡ Status Codes

| Code | Meaning |
|------|---------|
| 200 | Success |
| 400 | Bad request (invalid input, missing dependencies) |
| 404 | Resource not found |
| 500 | Internal server error |

---

## 🎯 Frontend Flow

```
Login → Create Domain → Upload Syllabus → Upload Books → 
Check Status (poll) → Evaluate Questions
```

---

## 🧪 Test Server

```bash
cd backend
python test_api.py
```

---

## 📖 Full Documentation

See `API_DOCUMENTATION.md` for complete specs.
