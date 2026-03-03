# AWS S3 Storage Setup Guide

## Overview
The storage service provides automatic backup and restore functionality for user data folders to AWS S3. This ensures data persistence and enables easy migration between environments.

## Setup Instructions

### 1. Create AWS S3 Bucket

1. Log in to AWS Console
2. Navigate to S3 service
3. Click "Create bucket"
4. Bucket name: `qn-evaluator-data` (or your preferred name)
5. Region: `us-east-1` (or your preferred region)
6. Block all public access: ✅ (recommended)
7. Click "Create bucket"

### 2. Create IAM User with S3 Access

1. Navigate to IAM service
2. Click "Users" → "Add users"
3. Username: `qn-evaluator-storage`
4. Access type: ✅ Programmatic access
5. Attach policy: `AmazonS3FullAccess` (or create custom policy below)
6. Copy the Access Key ID and Secret Access Key

**Custom Policy (Recommended - Least Privilege):**
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::qn-evaluator-data",
        "arn:aws:s3:::qn-evaluator-data/*"
      ]
    }
  ]
}
```

### 3. Configure Backend Environment

Edit `backend/.env` file:

```env
# AWS S3 Storage Configuration
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_REGION=us-east-1
S3_BUCKET_NAME=qn-evaluator-data
```

### 4. Install Dependencies

```bash
cd backend
pip install boto3
```

## Usage

### CLI Commands

**Backup entire user data:**
```bash
python storage_cli.py backup 1
```

**Restore entire user data:**
```bash
python storage_cli.py restore 1
```

**Backup specific domain:**
```bash
python storage_cli.py backup-domain 1 "OPERATING SYSTEM"
```

**Restore specific domain:**
```bash
python storage_cli.py restore-domain 1 "OPERATING SYSTEM"
```

### API Endpoints

**Backup user data:**
```bash
POST http://localhost:8002/storage/backup/1
```

**Restore user data:**
```bash
POST http://localhost:8002/storage/restore/1
```

**Backup specific domain:**
```bash
POST http://localhost:8002/storage/backup/1/OPERATING%20SYSTEM
```

**Restore specific domain:**
```bash
POST http://localhost:8002/storage/restore/1/OPERATING%20SYSTEM
```

## S3 Folder Structure

```
qn-evaluator-data/
└── users/
    └── 1/
        ├── OPERATING SYSTEM/
        │   ├── books/
        │   │   ├── temp_Operating-systems-text-book.pdf
        │   │   └── temp_Operating-System-Concepts.pdf
        │   ├── vector_db/
        │   │   ├── faiss_index.bin
        │   │   └── metadata.json
        │   ├── syllabus.txt
        │   └── syllabus.json
        ├── JAVA_PROGRAMMING/
        │   └── ...
        └── history.json
```

## Automated Backup Strategy

### Option 1: Backup on Domain Changes
Add automatic backup after critical operations in `main_v2.py`:

```python
# After syllabus upload
if storage_service:
    storage_service.backup_domain(user_id, domain_name)

# After books upload
if storage_service:
    storage_service.backup_domain(user_id, domain_name)
```

### Option 2: Scheduled Backups
Use cron job (Linux/Mac) or Task Scheduler (Windows):

**Linux/Mac cron:**
```bash
# Backup every day at 2 AM
0 2 * * * cd /path/to/backend && python storage_cli.py backup 1
```

**Windows Task Scheduler:**
1. Open Task Scheduler
2. Create Basic Task
3. Trigger: Daily at 2:00 AM
4. Action: Start a program
5. Program: `python`
6. Arguments: `storage_cli.py backup 1`
7. Start in: `C:\path\to\backend`

## Cost Estimation

**AWS S3 Pricing (us-east-1):**
- Storage: $0.023 per GB/month
- PUT requests: $0.005 per 1,000 requests
- GET requests: $0.0004 per 1,000 requests

**Example for user with 2 subjects:**
- Data size: ~500 MB (books + indexes)
- Monthly storage cost: ~$0.01
- Monthly backup cost (daily): ~$0.01
- **Total: ~$0.02/month per user**

## Troubleshooting

**Error: "Storage service not configured"**
- Ensure AWS credentials are set in `.env` file
- Restart the backend server after adding credentials

**Error: "Access Denied"**
- Check IAM user has correct S3 permissions
- Verify bucket name matches in `.env`

**Error: "Bucket does not exist"**
- Create the S3 bucket in AWS Console
- Ensure bucket name matches `S3_BUCKET_NAME` in `.env`

## Security Best Practices

1. ✅ Never commit `.env` file to git
2. ✅ Use IAM roles instead of access keys (for EC2/ECS deployments)
3. ✅ Enable S3 bucket versioning for data recovery
4. ✅ Enable S3 bucket encryption at rest
5. ✅ Use least privilege IAM policies
6. ✅ Rotate access keys regularly (every 90 days)

## Migration Guide

**Moving from local to cloud:**
```bash
# 1. Setup AWS credentials
# 2. Backup existing data
python storage_cli.py backup 1

# 3. On new server, restore data
python storage_cli.py restore 1
```

## Monitoring

Check S3 bucket in AWS Console:
1. Navigate to S3 → `qn-evaluator-data`
2. View folder structure under `users/`
3. Check file sizes and last modified dates
4. Enable S3 metrics for detailed monitoring
