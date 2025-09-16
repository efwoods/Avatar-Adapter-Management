# classes/AdapterPersistenceManager.py

from core.logging import logger
import tempfile
import zipfile
from typing import Dict, Any, List, Optional
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

    async def adapter_exists(self) -> bool:
        """Check if adapter exists"""
        try:
            adapter_key = f"{self._get_s3_adapter_path()}adapter_backup.zip"
            self.s3_client.head_object(
                Bucket=self.s3_bucket,
                Key=adapter_key
            )
            return True
        except Exception as e:
            logger.debug(f"Adapter check failed (this is normal for new adapters): {e}")
            return False

    async def create_adapter(self, adapter_name: str = "default") -> Dict[str, Any]:
        """Create a new adapter configuration"""
        try:
            adapter_path = self._get_s3_adapter_path()
            
            # Check if adapter already exists
            if await self.adapter_exists():
                logger.info(f"Adapter already exists for user {self.user_id}, avatar {self.avatar_id}")
                return {
                    "status": "existing",
                    "message": "Adapter already exists",
                    "s3_path": adapter_path
                }
            
            # Create new adapter locally then upload
            with tempfile.TemporaryDirectory() as temp_dir:
                local_adapter_path = os.path.join(temp_dir, "adapters")
                os.makedirs(local_adapter_path, exist_ok=True)
                
                # Initialize empty adapter structure
                adapter_config = {
                    "adapter_name": adapter_name,
                    "user_id": self.user_id,
                    "avatar_id": self.avatar_id,
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "status": "untrained",
                    "training_history": []
                }
                
                # Save adapter config
                config_path = os.path.join(local_adapter_path, "adapter_config.json")
                with open(config_path, 'w') as f:
                    json.dump(adapter_config, f, indent=2)
                
                # Create placeholder adapter files
                lora_structure = {
                    "adapter_model.bin": b"",  # Placeholder for actual adapter weights
                    "adapter_config.json": json.dumps({
                        "target_modules": ["q_proj", "v_proj"],
                        "r": 16,
                        "lora_alpha": 32,
                        "lora_dropout": 0.1
                    }).encode()
                }
                
                for filename, content in lora_structure.items():
                    file_path = os.path.join(local_adapter_path, filename)
                    with open(file_path, 'wb') as f:
                        f.write(content)
                
                # Backup to S3
                backup_metadata = await self.backup_adapters_to_s3(local_adapter_path)
                
                logger.info(f"Created and backed up new adapter for user {self.user_id}, avatar {self.avatar_id}")
                
                return {
                    "status": "created",
                    "message": "Adapter created successfully",
                    "s3_path": adapter_path,
                    "metadata": backup_metadata
                }
                
        except Exception as e:
            logger.error(f"Error creating adapter: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create adapter: {str(e)}")

    async def get_adapter_info(self) -> Dict[str, Any]:
        """Get adapter information"""
        try:
            adapter_path = self._get_s3_adapter_path()
            
            if not await self.adapter_exists():
                return {
                    "status": "not_found",
                    "user_id": self.user_id,
                    "avatar_id": self.avatar_id,
                    "message": "Adapter does not exist"
                }
            
            # Get adapter metadata
            metadata_key = f"{adapter_path}backup_metadata.json"
            try:
                metadata_obj = self.s3_client.get_object(
                    Bucket=self.s3_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            except:
                metadata = {}
            
            # Try to get adapter config
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    local_adapter_path = os.path.join(temp_dir, "adapters")
                    await self.restore_adapters_from_s3(local_adapter_path)
                    
                    config_path = os.path.join(local_adapter_path, "adapter_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            adapter_config = json.load(f)
                        metadata["adapter_config"] = adapter_config
            except:
                pass
            
            return {
                "status": "found",
                "user_id": self.user_id,
                "avatar_id": self.avatar_id,
                "metadata": metadata
            }
            
        except Exception as e:
            logger.error(f"Error getting adapter info: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to get adapter info: {str(e)}")

    async def delete_adapter(self) -> Dict[str, Any]:
        """Delete an adapter and all related data"""
        try:
            adapter_path = self._get_s3_adapter_path()
            
            # List all objects with the adapter prefix
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=adapter_path
            )
            
            if 'Contents' not in response:
                raise HTTPException(
                    status_code=404,
                    detail=f"No adapter found for user {self.user_id}, avatar {self.avatar_id}"
                )
            
            # Delete all adapter-related objects
            objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
            
            if objects_to_delete:
                self.s3_client.delete_objects(
                    Bucket=self.s3_bucket,
                    Delete={'Objects': objects_to_delete}
                )
                
                logger.info(f"Deleted {len(objects_to_delete)} adapter objects for user {self.user_id}, avatar {self.avatar_id}")
            
            return {
                "status": "success",
                "message": f"Adapter deleted for user {self.user_id}, avatar {self.avatar_id}",
                "deleted_objects": len(objects_to_delete)
            }
            
        except Exception as e:
            logger.error(f"Error deleting adapter: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to delete adapter: {str(e)}")

    # Training data methods
    async def upload_training_file(self, filename: str, file_content: bytes, 
                                 content_type: str = 'application/octet-stream',
                                 use_for_training: bool = True) -> Dict[str, Any]:
        """Upload a training data file"""
        try:
            training_data_path = self._get_s3_training_data_path()
            
            # Upload file to S3
            file_key = f"{training_data_path}{filename}"
            
            self.s3_client.put_object(
                Bucket=self.s3_bucket,
                Key=file_key,
                Body=file_content,
                ContentType=content_type,
                Metadata={
                    'user_id': self.user_id,
                    'avatar_id': self.avatar_id,
                    'upload_timestamp': datetime.now().isoformat(),
                    'original_filename': filename,
                    'use_for_training': str(use_for_training)
                }
            )
            
            # Update metadata.json
            await self._update_training_metadata(filename, use_for_training)
            
            logger.info(f"Uploaded training file {filename} for user {self.user_id}, avatar {self.avatar_id}")
            
            return {
                "status": "success",
                "message": f"File {filename} uploaded successfully",
                "file_size": len(file_content),
                "use_for_training": use_for_training,
                "s3_key": file_key
            }
            
        except Exception as e:
            logger.error(f"Error uploading training data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to upload training data: {str(e)}")

    async def list_training_files(self, training_only: Optional[bool] = None) -> List[Dict[str, Any]]:
        """List training data files with optional filtering"""
        try:
            training_data_path = self._get_s3_training_data_path()
            
            # Get metadata
            training_metadata = await self._get_training_metadata()
            
            # List files in training data directory
            response = self.s3_client.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix=training_data_path
            )
            
            files_list = []
            
            if 'Contents' in response:
                for obj in response['Contents']:
                    # Skip directory-like objects
                    if obj['Key'].endswith('/'):
                        continue
                    
                    filename = os.path.basename(obj['Key'])
                    use_for_training = training_metadata.get(filename, False)
                    
                    # Apply training_only filter
                    if training_only is not None:
                        if training_only and not use_for_training:
                            continue
                        elif not training_only and use_for_training:
                            continue
                    
                    # Get file metadata from S3 object metadata
                    try:
                        head_response = self.s3_client.head_object(
                            Bucket=self.s3_bucket,
                            Key=obj['Key']
                        )
                        file_metadata = head_response.get('Metadata', {})
                    except:
                        file_metadata = {}
                    
                    files_list.append({
                        "filename": filename,
                        "use_for_training": use_for_training,
                        "file_size": obj['Size'],
                        "last_modified": obj['LastModified'],
                        "content_type": file_metadata.get('content-type', 'unknown'),
                        "upload_timestamp": file_metadata.get('upload_timestamp'),
                        "s3_key": obj['Key']
                    })
            
            logger.info(f"Listed {len(files_list)} training data files for user {self.user_id}, avatar {self.avatar_id}")
            
            return files_list
            
        except Exception as e:
            logger.error(f"Error listing training data: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to list training data: {str(e)}")

    async def get_training_files_for_training(self) -> List[str]:
        """Get list of files marked for training"""
        try:
            training_metadata = await self._get_training_metadata()
            return [filename for filename, use_for_training in training_metadata.items() if use_for_training]
        except Exception as e:
            logger.warning(f"Error getting training files: {e}")
            return []

    # Helper methods
    async def _get_training_metadata(self) -> Dict[str, bool]:
        """Get training metadata from S3"""
        metadata_key = f"{self._get_s3_metadata_path()}metadata.json"
        
        try:
            metadata_obj = self.s3_client.get_object(
                Bucket=self.s3_bucket,
                Key=metadata_key
            )
            return json.loads(metadata_obj['Body'].read().decode('utf-8'))
        except:
            return {}

    async def _update_training_metadata(self, filename: str, use_for_training: bool) -> None:
        """Update training metadata for a specific file"""
        metadata = await self._get_training_metadata()
        metadata[filename] = use_for_training
        
        metadata_key = f"{self._get_s3_metadata_path()}metadata.json"
        self.s3_client.put_object(
            Bucket=self.s3_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )