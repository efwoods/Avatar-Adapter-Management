"""
S3 Service for handling S3 operations
"""

import json
import tempfile
from typing import Dict, Any, List, Optional, BinaryIO
from datetime import datetime
import os

from botocore.exceptions import ClientError
from core.logging import logger
from core.config import settings

class S3Service:
    """Service for S3 operations"""
    
    def __init__(self):
        self.bucket_name = settings.s3_bucket_name
        self._s3_client = None
    
    @property
    def s3_client(self):
        """Get S3 client from global instance"""
        from service.persistence_service import get_s3_client
        if self._s3_client is None:
            self._s3_client = get_s3_client()
        return self._s3_client
    
    def upload_file(self, 
                   file_content: bytes, 
                   s3_key: str, 
                   content_type: str = 'application/octet-stream',
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload file content to S3"""
        
        try:
            extra_args = {
                'ContentType': content_type
            }
            
            if metadata:
                extra_args['Metadata'] = metadata
            
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=s3_key,
                Body=file_content,
                **extra_args
            )
            
            logger.info(f"Uploaded file to S3: {s3_key}")
            
            return {
                "success": True,
                "s3_key": s3_key,
                "bucket": self.bucket_name,
                "size": len(file_content),
                "upload_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to upload file to S3: {e}")
            raise
    
    def download_file(self, s3_key: str) -> bytes:
        """Download file content from S3"""
        
        try:
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            content = response['Body'].read()
            logger.info(f"Downloaded file from S3: {s3_key}")
            
            return content
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                raise FileNotFoundError(f"File not found in S3: {s3_key}")
            else:
                logger.error(f"Failed to download file from S3: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to download file from S3: {e}")
            raise
    
    def delete_file(self, s3_key: str) -> bool:
        """Delete file from S3"""
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            logger.info(f"Deleted file from S3: {s3_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file from S3: {e}")
            raise
    
    def delete_files(self, s3_keys: List[str]) -> Dict[str, Any]:
        """Delete multiple files from S3"""
        
        try:
            if not s3_keys:
                return {"deleted": 0, "errors": []}
            
            # Prepare objects for deletion
            objects = [{'Key': key} for key in s3_keys]
            
            response = self.s3_client.delete_objects(
                Bucket=self.bucket_name,
                Delete={'Objects': objects}
            )
            
            deleted = response.get('Deleted', [])
            errors = response.get('Errors', [])
            
            logger.info(f"Deleted {len(deleted)} files from S3")
            
            return {
                "deleted": len(deleted),
                "errors": errors,
                "deleted_keys": [obj['Key'] for obj in deleted]
            }
            
        except Exception as e:
            logger.error(f"Failed to delete files from S3: {e}")
            raise
    
    def list_files(self, 
                  prefix: str, 
                  max_keys: int = 1000) -> List[Dict[str, Any]]:
        """List files in S3 with given prefix"""
        
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_keys
            )
            
            files = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip directory-like objects
                    if obj['Key'].endswith('/'):
                        continue
                    
                    files.append({
                        'key': obj['Key'],
                        'filename': os.path.basename(obj['Key']),
                        'size': obj['Size'],
                        'last_modified': obj['LastModified'],
                        'etag': obj['ETag'].strip('"')
                    })
            
            logger.info(f"Listed {len(files)} files with prefix: {prefix}")
            
            return files
            
        except Exception as e:
            logger.error(f"Failed to list files from S3: {e}")
            raise
    
    def file_exists(self, s3_key: str) -> bool:
        """Check if file exists in S3"""
        
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            return True
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return False
            else:
                logger.error(f"Error checking file existence: {e}")
                raise
        except Exception as e:
            logger.error(f"Error checking file existence: {e}")
            raise
    
    def get_file_metadata(self, s3_key: str) -> Dict[str, Any]:
        """Get file metadata from S3"""
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=s3_key
            )
            
            return {
                'key': s3_key,
                'filename': os.path.basename(s3_key),
                'size': response['ContentLength'],
                'last_modified': response['LastModified'],
                'content_type': response.get('ContentType', 'unknown'),
                'etag': response['ETag'].strip('"'),
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                raise FileNotFoundError(f"File not found in S3: {s3_key}")
            else:
                logger.error(f"Failed to get file metadata: {e}")
                raise
        except Exception as e:
            logger.error(f"Failed to get file metadata: {e}")
            raise
    
    def generate_presigned_url(self, 
                              s3_key: str, 
                              expiration: int = 3600,
                              method: str = 'get_object') -> str:
        """Generate presigned URL for file access"""
        
        try:
            url = self.s3_client.generate_presigned_url(
                method,
                Params={'Bucket': self.bucket_name, 'Key': s3_key},
                ExpiresIn=expiration
            )
            
            logger.info(f"Generated presigned URL for: {s3_key}")
            return url
            
        except Exception as e:
            logger.error(f"Failed to generate presigned URL: {e}")
            raise
    
    def copy_file(self, source_key: str, destination_key: str) -> Dict[str, Any]:
        """Copy file within S3 bucket"""
        
        try:
            copy_source = {
                'Bucket': self.bucket_name,
                'Key': source_key
            }
            
            self.s3_client.copy_object(
                CopySource=copy_source,
                Bucket=self.bucket_name,
                Key=destination_key
            )
            
            logger.info(f"Copied file in S3: {source_key} -> {destination_key}")
            
            return {
                "success": True,
                "source_key": source_key,
                "destination_key": destination_key,
                "copy_time": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to copy file in S3: {e}")
            raise
    
    def upload_json(self, 
                   data: Dict[str, Any], 
                   s3_key: str,
                   metadata: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Upload JSON data to S3"""
        
        json_content = json.dumps(data, indent=2, default=str).encode('utf-8')
        
        return self.upload_file(
            file_content=json_content,
            s3_key=s3_key,
            content_type='application/json',
            metadata=metadata
        )
    
    def download_json(self, s3_key: str) -> Dict[str, Any]:
        """Download and parse JSON from S3"""
        
        try:
            content = self.download_file(s3_key)
            return json.loads(content.decode('utf-8'))
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON from S3: {e}")
            raise ValueError(f"Invalid JSON content in file: {s3_key}")
        except Exception as e:
            logger.error(f"Failed to download JSON from S3: {e}")
            raise
    
    def create_backup(self, 
                     local_path: str, 
                     s3_prefix: str,
                     include_metadata: bool = True) -> Dict[str, Any]:
        """Create backup of local directory to S3"""
        
        if not os.path.exists(local_path):
            raise ValueError(f"Local path does not exist: {local_path}")
        
        uploaded_files = []
        total_size = 0
        
        try:
            # Walk through local directory
            for root, dirs, files in os.walk(local_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    relative_path = os.path.relpath(local_file_path, local_path)
                    s3_key = f"{s3_prefix.rstrip('/')}/{relative_path}".replace('\\', '/')
                    
                    # Read and upload file
                    with open(local_file_path, 'rb') as f:
                        file_content = f.read()
                    
                    file_metadata = None
                    if include_metadata:
                        stat = os.stat(local_file_path)
                        file_metadata = {
                            'original_path': local_file_path,
                            'backup_timestamp': datetime.now().isoformat(),
                            'file_size': str(len(file_content)),
                            'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                        }
                    
                    result = self.upload_file(
                        file_content=file_content,
                        s3_key=s3_key,
                        metadata=file_metadata
                    )
                    
                    uploaded_files.append({
                        'local_path': local_file_path,
                        'relative_path': relative_path,
                        's3_key': s3_key,
                        'size': len(file_content)
                    })
                    
                    total_size += len(file_content)
            
            # Create backup metadata
            backup_metadata = {
                'backup_type': 'directory',
                'source_path': local_path,
                's3_prefix': s3_prefix,
                'backup_timestamp': datetime.now().isoformat(),
                'file_count': len(uploaded_files),
                'total_size': total_size,
                'files': uploaded_files
            }
            
            # Upload backup metadata
            metadata_key = f"{s3_prefix.rstrip('/')}/backup_metadata.json"
            self.upload_json(backup_metadata, metadata_key)
            
            logger.info(f"Created backup: {len(uploaded_files)} files, {total_size} bytes")
            
            return backup_metadata
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def restore_backup(self, 
                      s3_prefix: str, 
                      local_path: str,
                      overwrite: bool = False) -> Dict[str, Any]:
        """Restore backup from S3 to local directory"""
        
        # Create local directory
        os.makedirs(local_path, exist_ok=True)
        
        try:
            # Get backup metadata
            metadata_key = f"{s3_prefix.rstrip('/')}/backup_metadata.json"
            backup_metadata = self.download_json(metadata_key)
            
            restored_files = []
            
            for file_info in backup_metadata.get('files', []):
                s3_key = file_info['s3_key']
                relative_path = file_info['relative_path']
                local_file_path = os.path.join(local_path, relative_path)
                
                # Create directory if needed
                local_dir = os.path.dirname(local_file_path)
                if local_dir:
                    os.makedirs(local_dir, exist_ok=True)
                
                # Check if file exists and handle overwrite
                if os.path.exists(local_file_path) and not overwrite:
                    logger.warning(f"Skipping existing file: {local_file_path}")
                    continue
                
                # Download and restore file
                file_content = self.download_file(s3_key)
                
                with open(local_file_path, 'wb') as f:
                    f.write(file_content)
                
                restored_files.append({
                    's3_key': s3_key,
                    'local_path': local_file_path,
                    'size': len(file_content)
                })
            
            logger.info(f"Restored backup: {len(restored_files)} files")
            
            return {
                'success': True,
                'restored_files': restored_files,
                'backup_metadata': backup_metadata,
                'restore_timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise