"""
Storage Management CLI
Backup and restore user data to/from AWS S3

Usage:
    python storage_cli.py backup 1                    # Backup user 1 data
    python storage_cli.py restore 1                   # Restore user 1 data
    python storage_cli.py backup-domain 1 "JAVA"      # Backup specific domain
    python storage_cli.py restore-domain 1 "JAVA"     # Restore specific domain
"""

import sys
from pathlib import Path
from services.storage_service import StorageService
from dotenv import load_dotenv
import os

load_dotenv()


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    
    # Check AWS credentials
    if not os.getenv('AWS_ACCESS_KEY_ID'):
        print("❌ AWS credentials not configured!")
        print("Add AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY to .env file")
        sys.exit(1)
    
    storage = StorageService()
    command = sys.argv[1]
    user_id = sys.argv[2]
    
    try:
        if command == 'backup':
            print(f"📤 Backing up user {user_id} data to S3...")
            files = storage.sync_user_data(user_id, direction='upload')
            print(f"✅ Backup complete! {len(files)} files uploaded")
            
        elif command == 'restore':
            print(f"📥 Restoring user {user_id} data from S3...")
            files = storage.sync_user_data(user_id, direction='download')
            print(f"✅ Restore complete! {len(files)} files downloaded")
            
        elif command == 'backup-domain':
            if len(sys.argv) < 4:
                print("Usage: python storage_cli.py backup-domain USER_ID DOMAIN_NAME")
                sys.exit(1)
            domain_name = sys.argv[3]
            print(f"📤 Backing up {domain_name} for user {user_id}...")
            files = storage.backup_domain(user_id, domain_name)
            print(f"✅ Backup complete! {len(files)} files uploaded")
            
        elif command == 'restore-domain':
            if len(sys.argv) < 4:
                print("Usage: python storage_cli.py restore-domain USER_ID DOMAIN_NAME")
                sys.exit(1)
            domain_name = sys.argv[3]
            print(f"📥 Restoring {domain_name} for user {user_id}...")
            files = storage.restore_domain(user_id, domain_name)
            print(f"✅ Restore complete! {len(files)} files downloaded")
            
        else:
            print(f"❌ Unknown command: {command}")
            print(__doc__)
            sys.exit(1)
            
    except FileNotFoundError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
