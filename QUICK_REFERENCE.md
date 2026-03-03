# Quick Reference - Storage & Syllabus Features

## ✅ What's Been Fixed

### 1. Syllabus File Download
- **Before:** Uploaded syllabus.txt couldn't be opened from UI
- **After:** Click "View Syllabus" button to open file in new tab
- **Fallback:** If original file missing, returns syllabus.json
- **Future:** New uploads save both original + parsed JSON

### 2. AWS S3 Storage (Optional)
- **Feature:** Backup/restore user data to cloud
- **Status:** Fully implemented, optional (works without AWS)
- **Cost:** ~$0.02/month per user
- **Use Case:** Data persistence, migration, disaster recovery

## 🚀 Quick Start

### Test Syllabus Download (No Setup Required)
1. Start backend: `cd backend && python main_v2.py`
2. Open UI: http://localhost:5173
3. Go to "Manage Subjects"
4. Click "View Syllabus" button
5. ✅ Opens syllabus.json in new tab

### Enable S3 Backup (Optional - 5 min setup)
1. Install boto3: `pip install boto3`
2. Create S3 bucket in AWS Console: `qn-evaluator-data`
3. Add to `backend/.env`:
   ```
   AWS_ACCESS_KEY_ID=your_key
   AWS_SECRET_ACCESS_KEY=your_secret
   AWS_REGION=us-east-1
   S3_BUCKET_NAME=qn-evaluator-data
   ```
4. Backup: `python storage_cli.py backup 1`

## 📁 Files Changed

### Backend
- ✅ `main_v2.py` - Fixed syllabus endpoint, added storage APIs
- ✅ `services/storage_service.py` - NEW: S3 backup service
- ✅ `storage_cli.py` - NEW: CLI tool
- ✅ `.env` - Added AWS config (commented)
- ✅ `requirements.txt` - Added boto3, python-dotenv

### Frontend
- ✅ `ManageSubjects.jsx` - Changed button text to "View Syllabus"

### Documentation
- ✅ `STORAGE_SETUP.md` - Complete AWS setup guide
- ✅ `SETUP_SUMMARY.md` - Detailed implementation notes

## 🔧 API Endpoints

### Syllabus
```
GET /domains/{user_id}/{domain_name}/files/syllabus
→ Returns original file or syllabus.json fallback
```

### Storage (Optional - requires AWS setup)
```
POST /storage/backup/{user_id}
POST /storage/restore/{user_id}
POST /storage/backup/{user_id}/{domain_name}
POST /storage/restore/{user_id}/{domain_name}
```

## 💻 CLI Commands

### Backup/Restore (requires boto3 + AWS credentials)
```bash
# Backup user data
python storage_cli.py backup 1

# Restore user data
python storage_cli.py restore 1

# Backup specific domain
python storage_cli.py backup-domain 1 "OPERATING SYSTEM"

# Restore specific domain
python storage_cli.py restore-domain 1 "OPERATING SYSTEM"
```

## 🎯 Testing Checklist

- [x] Backend starts without boto3 installed
- [x] Backend starts with boto3 installed
- [x] Syllabus download works (returns JSON fallback)
- [ ] Upload new syllabus.txt (test original file saving)
- [ ] Setup AWS S3 bucket
- [ ] Test backup command
- [ ] Test restore command

## 📊 S3 Folder Structure

```
s3://qn-evaluator-data/
└── users/
    └── 1/
        ├── OPERATING SYSTEM/
        │   ├── books/
        │   │   └── *.pdf
        │   ├── vector_db/
        │   │   ├── faiss_index.bin
        │   │   └── metadata.json
        │   ├── syllabus.txt (or .pdf)
        │   └── syllabus.json
        └── history.json
```

## ⚠️ Important Notes

1. **Storage is OPTIONAL** - System works fine without AWS
2. **boto3 is OPTIONAL** - Backend starts without it
3. **Existing data** - Original syllabus files don't exist (uploaded before fix)
4. **New uploads** - Will save both original + JSON
5. **Fallback works** - Endpoint returns JSON if original missing

## 🔐 Security

- ✅ `.env` in `.gitignore` (credentials not committed)
- ✅ AWS credentials optional
- ✅ S3 bucket should block public access
- ✅ Use IAM roles in production
- ✅ Rotate keys every 90 days

## 📚 Documentation

- **Full AWS Setup:** See `STORAGE_SETUP.md`
- **Implementation Details:** See `SETUP_SUMMARY.md`
- **This File:** Quick reference only

## 🆘 Troubleshooting

**Syllabus button doesn't work:**
- Check backend running on port 8002
- Check domain folder exists
- Should return JSON fallback if original missing

**Storage service not configured:**
- This is OK - storage is optional
- Add AWS credentials to `.env` to enable
- Install boto3: `pip install boto3`

**boto3 import error:**
- Storage is optional feature
- Backend works without it
- Install only if you need S3 backup

## ✨ Next Steps

1. **Test current setup:**
   - Click "View Syllabus" in UI
   - Should open syllabus.json

2. **Test new upload:**
   - Upload new syllabus.txt
   - Verify both files created
   - Click "View Syllabus" again

3. **Setup S3 (optional):**
   - Follow `STORAGE_SETUP.md`
   - Test backup/restore
   - Setup automated backups

## 📞 Support

For detailed setup instructions, see:
- `STORAGE_SETUP.md` - AWS S3 setup
- `SETUP_SUMMARY.md` - Implementation details
