# classes/AdapterPersistenceManager.py

from core.logging import logger
import tempfile
import zipfile
from typing import Dict, Any, List
from datetime import datetime
import json

from fastapi import HTTPException
from botocore.exceptions import ClientError
import os
class AdapterPersistenceManager:
    """Manages persistence operations for LoRA adapters and training data"""
    
    def __init__(self, s3_client, settings, user_id: str, avatar_id: str):
        self.s3_client = s3_client
        self.settings = settings
        self.user_id = user_id
        self.avatar_id = avatar_id
        self.s3_bucket = settings.s3_bucket_name
        
    def _get_s3_adapter_path(self) -> str:
        """Get S3 path for adapters"""
        return f"users/{self.user_id}/avatars/{self.avatar_id}/adapters/"
    
    def _get_s3_training_data_path(self) -> str:
        """Get S3 path for training data"""
        return f"users/{self.user_id}/avatars/{self.avatar_id}/adapters/training_data/"
    
    def _get_s3_metadata_path(self) -> str:
        """Get S3 path for adapter metadata"""
        return f"users/{self.user_id}/avatars/{self.avatar_id}/adapters/metadata/"
    
    async def backup_adapters_to_s3(self, local_adapter_path: str) -> Dict[str, Any]:
        """Backup adapter files to S3"""
        try:
            if not os.path.exists(local_adapter_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Local adapter path not found: {local_adapter_path}"
                )
            
            # Create zip file of adapters
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(local_adapter_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, local_adapter_path)
                            zipf.write(file_path, arcname)
                
                # Upload to S3
                s3_key = f"{self._get_s3_adapter_path()}adapter_backup.zip"
                self.s3_client.upload_file(temp_file.name, self.s3_bucket, s3_key)
                
                # Create metadata
                metadata = {
                    "backup_type": "adapters",
                    "user_id": self.user_id,
                    "avatar_id": self.avatar_id,
                    "backup_timestamp": datetime.now().isoformat(),
                    "file_count": sum([len(files) for _, _, files in os.walk(local_adapter_path)]),
                    "backup_size_bytes": os.path.getsize(temp_file.name)
                }
                
                # Upload metadata
                metadata_key = f"{self._get_s3_adapter_path()}backup_metadata.json"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2),
                    ContentType='application/json'
                )
                
                # Cleanup temp file
                os.unlink(temp_file.name)
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error backing up adapters: {e}")
            raise
    
    async def backup_training_data_to_s3(self, local_training_data_path: str) -> Dict[str, Any]:
        """Backup training data to S3"""
        try:
            if not os.path.exists(local_training_data_path):
                raise HTTPException(
                    status_code=404,
                    detail=f"Local training data path not found: {local_training_data_path}"
                )
            
            # Create zip file of training data
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for root, dirs, files in os.walk(local_training_data_path):
                        for file in files:
                            file_path = os.path.join(root, file)
                            arcname = os.path.relpath(file_path, local_training_data_path)
                            zipf.write(file_path, arcname)
                
                # Upload to S3
                s3_key = f"{self._get_s3_training_data_path()}training_data_backup.zip"
                self.s3_client.upload_file(temp_file.name, self.s3_bucket, s3_key)
                
                # Create metadata
                metadata = {
                    "backup_type": "training_data",
                    "user_id": self.user_id,
                    "avatar_id": self.avatar_id,
                    "backup_timestamp": datetime.now().isoformat(),
                    "file_count": sum([len(files) for _, _, files in os.walk(local_training_data_path)]),
                    "backup_size_bytes": os.path.getsize(temp_file.name)
                }
                
                # Upload metadata
                metadata_key = f"{self._get_s3_training_data_path()}backup_metadata.json"
                self.s3_client.put_object(
                    Bucket=self.s3_bucket,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2),
                    ContentType='application/json'
                )
                
                # Cleanup temp file
                os.unlink(temp_file.name)
                
                return metadata
                
        except Exception as e:
            logger.error(f"Error backing up training data: {e}")
            raise
    
    async def restore_adapters_from_s3(self, local_adapter_path: str) -> None:
        """Restore adapter files from S3"""
        try:
            s3_key = f"{self._get_s3_adapter_path()}adapter_backup.zip"
            
            # Check if backup exists
            try:
                self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise HTTPException(
                        status_code=404,
                        detail=f"No adapter backup found for user {self.user_id}, avatar {self.avatar_id}"
                    )
                raise
            
            # Create local directory if it doesn't exist
            os.makedirs(local_adapter_path, exist_ok=True)
            
            # Download and extract
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                self.s3_client.download_file(self.s3_bucket, s3_key, temp_file.name)
                
                with zipfile.ZipFile(temp_file.name, 'r') as zipf:
                    zipf.extractall(local_adapter_path)
                
                # Cleanup temp file
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"Error restoring adapters: {e}")
            raise
    
    async def restore_training_data_from_s3(self, local_training_data_path: str) -> None:
        """Restore training data from S3"""
        try:
            s3_key = f"{self._get_s3_training_data_path()}training_data_backup.zip"
            
            # Check if backup exists
            try:
                self.s3_client.head_object(Bucket=self.s3_bucket, Key=s3_key)
            except ClientError as e:
                if e.response['Error']['Code'] == '404':
                    raise HTTPException(
                        status_code=404,
                        detail=f"No training data backup found for user {self.user_id}, avatar {self.avatar_id}"
                    )
                raise
            
            # Create local directory if it doesn't exist
            os.makedirs(local_training_data_path, exist_ok=True)
            
            # Download and extract
            with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_file:
                self.s3_client.download_file(self.s3_bucket, s3_key, temp_file.name)
                
                with zipfile.ZipFile(temp_file.name, 'r') as zipf:
                    zipf.extractall(local_training_data_path)
                
                # Cleanup temp file
                os.unlink(temp_file.name)
                
        except Exception as e:
            logger.error(f"Error restoring training data: {e}")
            raise
    
    async def list_adapter_backups(self) -> List[Dict[str, Any]]:
        """List available adapter backups"""
        backups = []
        
        try:
            # List adapter backups
            adapter_prefix = self._get_s3_adapter_path()
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=adapter_prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('adapter_backup.zip'):
                        # Try to get metadata
                        metadata_key = obj['Key'].replace('adapter_backup.zip', 'backup_metadata.json')
                        metadata = {}
                        try:
                            metadata_obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=metadata_key)
                            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                        except:
                            pass
                        
                        backups.append({
                            "type": "adapters",
                            "key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "metadata": metadata
                        })
            
            # List training data backups
            training_prefix = self._get_s3_training_data_path()
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=training_prefix
            )
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    if obj['Key'].endswith('training_data_backup.zip'):
                        # Try to get metadata
                        metadata_key = obj['Key'].replace('training_data_backup.zip', 'backup_metadata.json')
                        metadata = {}
                        try:
                            metadata_obj = self.s3_client.get_object(Bucket=self.s3_bucket, Key=metadata_key)
                            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                        except:
                            pass
                        
                        backups.append({
                            "type": "training_data",
                            "key": obj['Key'],
                            "size": obj['Size'],
                            "last_modified": obj['LastModified'].isoformat(),
                            "metadata": metadata
                        })
            
            return backups
            
        except Exception as e:
            logger.error(f"Error listing adapter backups: {e}")
            raise