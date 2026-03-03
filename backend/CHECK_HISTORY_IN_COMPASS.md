# How to Check History in MongoDB Compass

## 📋 Step-by-Step Guide

### 1. Open MongoDB Compass
- Launch MongoDB Compass application
- Connect to: `mongodb://localhost:27017/`

### 2. Navigate to History Collection
```
Databases → qn_evaluator → Collections → history
```

### 3. View Your History
**Query to see user 1's history:**
```javascript
{ user_id: "1" }
```

**Click "Find" button**

### 4. What You'll See

```javascript
{
  _id: ObjectId("..."),
  user_id: "1",
  data: {
    single_questions: [
      {
        id: "20260228164530123456",
        timestamp: "2026-02-28T16:45:30.123456",
        domain_name: "OPERATING SYSTEM",
        question: "What is process scheduling?",
        unit: "II",
        unit_title: "PROCESS MANAGEMENT",
        topic: "Process Scheduling",
        bloom_level: "BT2",
        course_outcomes: ["CO2"],
        out_of_syllabus: false
      },
      // ... more questions
    ],
    pdf_evaluations: [
      {
        id: "20260228165000789012",
        timestamp: "2026-02-28T16:50:00.789012",
        domain_name: "OPERATING SYSTEM",
        filename: "question_paper.pdf",
        total_questions: 50,
        results: [
          {
            question_number: "1",
            part: "Part A",
            question: "Define operating system",
            unit: "I",
            topic: "Introduction to OS",
            bloom_level: "BT1",
            course_outcomes: ["CO1"],
            out_of_syllabus: false
          },
          // ... 49 more questions
        ]
      },
      // ... more PDF evaluations
    ]
  },
  updated_at: ISODate("2026-02-28T16:50:00.789Z")
}
```

---

## 🧪 Test History Storage

### Step 1: Evaluate a Question in UI
1. Open UI: http://localhost:5173
2. Go to "Evaluate Question"
3. Enter question: "What is process scheduling?"
4. Click "Evaluate"

### Step 2: Check in Compass
1. Refresh `history` collection in Compass
2. Query: `{ user_id: "1" }`
3. Expand `data.single_questions` array
4. You should see your question! ✅

### Step 3: Evaluate a PDF
1. In UI, go to "Evaluate PDF"
2. Upload a question paper PDF
3. Wait for evaluation to complete

### Step 4: Check PDF Evaluation in Compass
1. Refresh `history` collection
2. Query: `{ user_id: "1" }`
3. Expand `data.pdf_evaluations` array
4. You should see your PDF evaluation with all results! ✅

---

## 🔍 Useful Queries in Compass

### View all single questions:
```javascript
{ user_id: "1" }
// Then expand: data → single_questions
```

### View all PDF evaluations:
```javascript
{ user_id: "1" }
// Then expand: data → pdf_evaluations
```

### Count total questions evaluated:
```javascript
// In Aggregations tab:
[
  { $match: { user_id: "1" } },
  { $project: { 
      total: { $size: "$data.single_questions" }
  }}
]
```

### View questions from specific domain:
```javascript
// In Aggregations tab:
[
  { $match: { user_id: "1" } },
  { $unwind: "$data.single_questions" },
  { $match: { "data.single_questions.domain_name": "OPERATING SYSTEM" } }
]
```

---

## 📊 History Structure

```javascript
{
  user_id: "1",                    // User identifier
  data: {
    single_questions: [            // Array of individual questions
      {
        id: "unique_id",           // Question ID
        timestamp: "ISO date",     // When evaluated
        domain_name: "OS",         // Subject
        question: "text",          // Question text
        unit: "II",                // Matched unit
        topic: "topic name",       // Matched topic
        bloom_level: "BT2",        // Bloom taxonomy
        course_outcomes: ["CO2"],  // Course outcomes
        out_of_syllabus: false     // Syllabus match
      }
    ],
    pdf_evaluations: [             // Array of PDF evaluations
      {
        id: "unique_id",           // Evaluation ID
        timestamp: "ISO date",     // When evaluated
        domain_name: "OS",         // Subject
        filename: "paper.pdf",     // PDF filename
        total_questions: 50,       // Question count
        results: [...]             // All question results
      }
    ]
  },
  updated_at: ISODate("...")       // Last update time
}
```

---

## ✅ Verification Checklist

After evaluating questions in UI:

- [ ] Open MongoDB Compass
- [ ] Connect to localhost:27017
- [ ] Navigate to `qn_evaluator` → `history`
- [ ] Query: `{ user_id: "1" }`
- [ ] See `data.single_questions` array with your questions
- [ ] See `data.pdf_evaluations` array with your PDF evaluations
- [ ] Check `updated_at` timestamp is recent

---

## 🆘 Troubleshooting

**No history collection?**
- Evaluate at least one question in UI first
- Collection is created automatically on first save

**Empty history?**
- Check backend logs for errors
- Verify MongoDB is running
- Ensure `USE_MONGODB_STORAGE=true` in .env

**Old history not showing?**
- Run migration: `python migrate_to_mongodb.py 1`
- This moves history.json to MongoDB

---

## 💡 Pro Tips

1. **Export history:**
   - In Compass, click "Export Collection"
   - Choose JSON format
   - Save as backup

2. **Clear history:**
   - Delete document: `{ user_id: "1" }`
   - Or use UI "Clear History" button

3. **View recent evaluations:**
   - History is sorted by timestamp (newest first)
   - First item in array = most recent

4. **Search by question text:**
```javascript
{
  user_id: "1",
  "data.single_questions.question": { $regex: "scheduling", $options: "i" }
}
```

---

**Status:** ✅ History now saves to MongoDB automatically!
