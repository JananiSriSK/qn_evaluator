# MongoDB Storage Setup

## Quick Setup (5 minutes)

### 1. Install MongoDB & pymongo
```bash
# Install pymongo
pip install pymongo

# MongoDB should already be installed if you have Compass
```

### 2. Start MongoDB (if not running)
```bash
# Windows - MongoDB should auto-start with Compass
# Or manually: mongod --dbpath C:\data\db

# Check if running: Open MongoDB Compass and connect to localhost:27017
```

### 3. Migrate Existing Data
```bash
cd backend
python migrate_to_mongodb.py 1
```

### 4. Verify in MongoDB Compass
1. Open MongoDB Compass
2. Connect to: `mongodb://localhost:27017/`
3. Database: `qn_evaluator`
4. Collections:
   - `syllabus` - Syllabus JSON + original files
   - `books` - Book PDFs
   - `indexes` - FAISS indexes + metadata
   - `history` - Evaluation history
   - `fs.files` & `fs.chunks` - GridFS (large files)

### 5. Start Backend
```bash
python main_v2.py
```

## What's Stored in MongoDB

### Syllabus Collection
```json
{
  "user_id": "1",
  "domain_name": "OPERATING SYSTEM",
  "syllabus_data": { /* parsed JSON */ },
  "original_file_id": ObjectId("..."),  // GridFS reference
  "original_filename": "syllabus.txt",
  "updated_at": ISODate("...")
}
```

### Books Collection
```json
{
  "user_id": "1",
  "domain_name": "OPERATING SYSTEM",
  "filename": "temp_OS-book.pdf",
  "file_id": ObjectId("..."),  // GridFS reference
  "uploaded_at": ISODate("...")
}
```

### Indexes Collection
```json
{
  "user_id": "1",
  "domain_name": "OPERATING SYSTEM",
  "file_id": ObjectId("..."),  // FAISS index in GridFS
  "metadata": [ /* chunk metadata */ ],
  "chunks_count": 6430,
  "updated_at": ISODate("...")
}
```

### History Collection
```json
{
  "user_id": "1",
  "data": {
    "single_questions": [...],
    "pdf_evaluations": [...]
  },
  "updated_at": ISODate("...")
}
```

## Benefits

✅ **No local files** - Everything in database
✅ **Easy backup** - MongoDB dump/restore
✅ **Scalable** - Works with multiple servers
✅ **GridFS** - Handles large files (books, indexes)
✅ **Compass UI** - Visual database management

## Configuration

Edit `backend/.env`:
```env
USE_MONGODB_STORAGE=true
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB=qn_evaluator
```

## Troubleshooting

**"No module named 'pymongo'"**
```bash
pip install pymongo
```

**"Connection refused"**
- Start MongoDB service
- Open MongoDB Compass to verify it's running

**"Migration failed"**
- Check MongoDB is running
- Verify data/1 folder exists
- Check logs for specific error

## Testing

```bash
# Test MongoDB connection
python -c "from pymongo import MongoClient; print(MongoClient('mongodb://localhost:27017/').server_info())"

# Migrate data
python migrate_to_mongodb.py 1

# Start backend
python main_v2.py

# Test syllabus download
curl http://localhost:8002/domains/1/OPERATING%20SYSTEM/files/syllabus
```

## Fallback

If MongoDB fails, system automatically falls back to local file storage (data/ folder).
