"""
Adapter Persistence API router for S3 backup and restore operations
"""
from fastapi import APIRouter, HTTPException, Depends, status
from typing import List, Optional, Dict, Any
import logging
import json
import zipfile
import os
import tempfile
from pathlib import Path
import boto3
from botocore.exceptions import ClientError
from datetime import datetime

logger = logging.getLogger(__name__)
router = APIRouter()

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
                    status_code=status.HTTP_404_NOT_FOUND,
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
                    status_code=status.HTTP_404_NOT_FOUND,
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
                        status_code=status.HTTP_404_NOT_FOUND,
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
                        status_code=status.HTTP_404_NOT_FOUND,
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

def get_adapter_persistence_manager(user_id: str, avatar_id: str) -> AdapterPersistenceManager:
    """Get adapter persistence manager instance"""
    from main import get_s3_client, get_settings
    return AdapterPersistenceManager(
        s3_client=get_s3_client(),
        settings=get_settings(),
        user_id=user_id,
        avatar_id=avatar_id
    )

# Response models
from pydantic import BaseModel

class AdapterBackupResponse(BaseModel):
    success: bool
    message: str
    backup_info: Dict[str, Any]

class AdapterRestoreResponse(BaseModel):
    success: bool
    message: str

class AdapterListBackupsResponse(BaseModel):
    backups: List[Dict[str, Any]]
    count: int

# Routes
@router.post("/adapters/backup/{user_id}/{avatar_id}",
    response_model=AdapterBackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Backup adapters to S3",
    description="Create a backup of LoRA adapter files and upload to S3"
)
async def backup_adapters_to_s3(
    user_id: str,
    avatar_id: str,
    local_adapter_path: str
):
    """Backup adapter files to S3"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        backup_info = await manager.backup_adapters_to_s3(local_adapter_path)
        
        return AdapterBackupResponse(
            success=True,
            message=f"Successfully backed up adapters for user {user_id}, avatar {avatar_id}",
            backup_info=backup_info
        )
    except Exception as e:
        logger.error(f"Error backing up adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backup adapters: {str(e)}"
        )

@router.post("/adapters/training-data/backup/{user_id}/{avatar_id}",
    response_model=AdapterBackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Backup training data to S3",
    description="Create a backup of adapter training data and upload to S3"
)
async def backup_training_data_to_s3(
    user_id: str,
    avatar_id: str,
    local_training_data_path: str
):
    """Backup training data to S3"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        backup_info = await manager.backup_training_data_to_s3(local_training_data_path)
        
        return AdapterBackupResponse(
            success=True,
            message=f"Successfully backed up training data for user {user_id}, avatar {avatar_id}",
            backup_info=backup_info
        )
    except Exception as e:
        logger.error(f"Error backing up training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backup training data: {str(e)}"
        )

@router.post("/adapters/restore/{user_id}/{avatar_id}",
    response_model=AdapterRestoreResponse,
    summary="Restore adapters from S3",
    description="Restore LoRA adapter files from S3 backup"
)
async def restore_adapters_from_s3(
    user_id: str,
    avatar_id: str,
    local_adapter_path: str
):
    """Restore adapter files from S3"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        await manager.restore_adapters_from_s3(local_adapter_path)
        
        return AdapterRestoreResponse(
            success=True,
            message=f"Successfully restored adapters for user {user_id}, avatar {avatar_id}"
        )
    except Exception as e:
        logger.error(f"Error restoring adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore adapters: {str(e)}"
        )

@router.post("/adapters/training-data/restore/{user_id}/{avatar_id}",
    response_model=AdapterRestoreResponse,
    summary="Restore training data from S3",
    description="Restore adapter training data from S3 backup"
)
async def restore_training_data_from_s3(
    user_id: str,
    avatar_id: str,
    local_training_data_path: str
):
    """Restore training data from S3"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        await manager.restore_training_data_from_s3(local_training_data_path)
        
        return AdapterRestoreResponse(
            success=True,
            message=f"Successfully restored training data for user {user_id}, avatar {avatar_id}"
        )
    except Exception as e:
        logger.error(f"Error restoring training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore training data: {str(e)}"
        )

@router.get("/adapters/backups/{user_id}/{avatar_id}",
    response_model=AdapterListBackupsResponse,
    summary="List available adapter backups",
    description="List all available adapter and training data backups for the user/avatar in S3"
)
async def list_adapter_backups(
    user_id: str,
    avatar_id: str
):
    """List available adapter backups"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        backups = await manager.list_adapter_backups()
        
        return AdapterListBackupsResponse(
            backups=backups,
            count=len(backups)
        )
    except Exception as e:
        logger.error(f"Error listing adapter backups: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list adapter backups: {str(e)}"
        )

@router.delete("/adapters/backup/{user_id}/{avatar_id}",
    summary="Delete adapter backup from S3",
    description="Delete adapter backup from S3"
)
async def delete_adapter_backup(
    user_id: str,
    avatar_id: str,
    backup_type: str = "adapters"  # "adapters" or "training_data"
):
    """Delete adapter backup from S3"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        
        if backup_type == "adapters":
            backup_key = f"{manager._get_s3_adapter_path()}adapter_backup.zip"
            metadata_key = f"{manager._get_s3_adapter_path()}backup_metadata.json"
        elif backup_type == "training_data":
            backup_key = f"{manager._get_s3_training_data_path()}training_data_backup.zip"
            metadata_key = f"{manager._get_s3_training_data_path()}backup_metadata.json"
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="backup_type must be 'adapters' or 'training_data'"
            )
        
        # Delete from S3
        manager.s3_client.delete_object(
            Bucket=manager.s3_bucket,
            Key=backup_key
        )
        manager.s3_client.delete_object(
            Bucket=manager.s3_bucket,
            Key=metadata_key
        )
        
        return {
            "success": True, 
            "message": f"Successfully deleted {backup_type} backup for user {user_id}, avatar {avatar_id}"
        }
    except Exception as e:
        logger.error(f"Error deleting adapter backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete adapter backup: {str(e)}"
        )

@router.get("/adapters/status/{user_id}/{avatar_id}",
    summary="Get adapter persistence status",
    description="Get the status of S3 connectivity and adapter backup information"
)
async def get_adapter_persistence_status(
    user_id: str,
    avatar_id: str
):
    """Get adapter persistence status"""
    try:
        manager = get_adapter_persistence_manager(user_id, avatar_id)
        
        # Test S3 connectivity
        s3_status = "connected"
        try:
            manager.s3_client.head_bucket(Bucket=manager.s3_bucket)
        except Exception:
            s3_status = "disconnected"
        
        # Check if backups exist
        adapter_backup_exists = False
        training_data_backup_exists = False
        
        try:
            manager.s3_client.head_object(
                Bucket=manager.s3_bucket,
                Key=f"{manager._get_s3_adapter_path()}adapter_backup.zip"
            )
            adapter_backup_exists = True
        except:
            pass
        
        try:
            manager.s3_client.head_object(
                Bucket=manager.s3_bucket,
                Key=f"{manager._get_s3_training_data_path()}training_data_backup.zip"
            )
            training_data_backup_exists = True
        except:
            pass
        
        return {
            "s3_status": s3_status,
            "s3_bucket": manager.s3_bucket,
            "adapter_backup_path": f"s3://{manager.s3_bucket}/{manager._get_s3_adapter_path()}",
            "training_data_backup_path": f"s3://{manager.s3_bucket}/{manager._get_s3_training_data_path()}",
            "adapter_backup_exists": adapter_backup_exists,
            "training_data_backup_exists": training_data_backup_exists,
            "user_id": user_id,
            "avatar_id": avatar_id
        }
    except Exception as e:
        logger.error(f"Error getting adapter persistence status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get adapter persistence status: {str(e)}"
        )