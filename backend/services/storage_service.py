try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    boto3 = None
    ClientError = Exception

import os
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """AWS S3 storage service for user data backup and sync"""
    
    def __init__(self):
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 not installed. Install with: pip install boto3")
        
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('S3_BUCKET_NAME', 'qn-evaluator-data')
    
    def upload_folder(self, local_path: Path, s3_prefix: str):
        """Upload entire folder to S3
        
        Args:
            local_path: Local folder path (e.g., data/1)
            s3_prefix: S3 prefix (e.g., users/1)
        """
        uploaded_files = []
        
        for file_path in local_path.rglob('*'):
            if file_path.is_file():
                # Calculate relative path
                relative_path = file_path.relative_to(local_path)
                s3_key = f"{s3_prefix}/{relative_path}".replace('\\', '/')
                
                try:
                    self.s3_client.upload_file(
                        str(file_path),
                        self.bucket_name,
                        s3_key
                    )
                    uploaded_files.append(s3_key)
                    logger.info(f"✓ Uploaded: {s3_key}")
                except ClientError as e:
                    logger.error(f"✗ Failed to upload {file_path}: {e}")
        
        return uploaded_files
    
    def download_folder(self, s3_prefix: str, local_path: Path):
        """Download entire folder from S3
        
        Args:
            s3_prefix: S3 prefix (e.g., users/1)
            local_path: Local destination path (e.g., data/1)
        """
        local_path.mkdir(parents=True, exist_ok=True)
        downloaded_files = []
        
        try:
            paginator = self.s3_client.get_paginator('list_objects_v2')
            pages = paginator.paginate(Bucket=self.bucket_name, Prefix=s3_prefix)
            
            for page in pages:
                if 'Contents' not in page:
                    continue
                
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    # Remove prefix to get relative path
                    relative_path = s3_key[len(s3_prefix):].lstrip('/')
                    local_file = local_path / relative_path
                    
                    # Create parent directories
                    local_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    try:
                        self.s3_client.download_file(
                            self.bucket_name,
                            s3_key,
                            str(local_file)
                        )
                        downloaded_files.append(str(local_file))
                        logger.info(f"✓ Downloaded: {local_file}")
                    except ClientError as e:
                        logger.error(f"✗ Failed to download {s3_key}: {e}")
            
            return downloaded_files
        except ClientError as e:
            logger.error(f"Failed to list objects: {e}")
            return []
    
    def sync_user_data(self, user_id: str, direction: str = 'upload'):
        """Sync user data folder with S3
        
        Args:
            user_id: User ID (e.g., '1')
            direction: 'upload' or 'download'
        """
        local_path = Path('data') / user_id
        s3_prefix = f'users/{user_id}'
        
        if direction == 'upload':
            if not local_path.exists():
                raise FileNotFoundError(f"Local path not found: {local_path}")
            return self.upload_folder(local_path, s3_prefix)
        elif direction == 'download':
            return self.download_folder(s3_prefix, local_path)
        else:
            raise ValueError("direction must be 'upload' or 'download'")
    
    def backup_domain(self, user_id: str, domain_name: str):
        """Backup specific domain to S3"""
        local_path = Path('data') / user_id / domain_name
        s3_prefix = f'users/{user_id}/{domain_name}'
        
        if not local_path.exists():
            raise FileNotFoundError(f"Domain not found: {local_path}")
        
        return self.upload_folder(local_path, s3_prefix)
    
    def restore_domain(self, user_id: str, domain_name: str):
        """Restore specific domain from S3"""
        local_path = Path('data') / user_id / domain_name
        s3_prefix = f'users/{user_id}/{domain_name}'
        
        return self.download_folder(s3_prefix, local_path)
