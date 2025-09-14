
## app/service/s3_service.py
import boto3
import json
import io
from typing import List, Dict, Optional, Tuple
from botocore.exceptions import ClientError
from core.config import settings
from db.schema.models import TrainingDataMetadata
from datetime import datetime

class S3Service:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        self.bucket_name = settings.s3_bucket_name

    def _get_training_data_prefix(self, user_id: str, avatar_id: str) -> str:
        return f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"

    def _get_metadata_prefix(self, user_id: str, avatar_id: str) -> str:
        return f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"

    def _get_adapter_prefix(self, user_id: str, avatar_id: str) -> str:
        return f"users/{user_id}/avatars/{avatar_id}/adapters/"

    async def upload_training_data(self, user_id: str, avatar_id: str, file_name: str, 
                                 file_content: bytes, use_for_training: bool = True) -> str:
        """Upload training data file to S3"""
        file_key = f"{self._get_training_data_prefix(user_id, avatar_id)}{file_name}"
        
        try:
            # Upload file
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=file_key,
                Body=file_content
            )
            
            # Update metadata
            await self._update_file_metadata(user_id, avatar_id, file_name, use_for_training, len(file_content))
            
            return file_key
        except ClientError as e:
            raise Exception(f"Failed to upload file: {str(e)}")

    async def _update_file_metadata(self, user_id: str, avatar_id: str, file_name: str, 
                                  use_for_training: bool, file_size: int):
        """Update metadata for a training data file"""
        metadata_key = f"{self._get_metadata_prefix(user_id, avatar_id)}metadata.json"
        
        try:
            # Get existing metadata
            metadata = await self._get_metadata(user_id, avatar_id)
            
            # Update metadata for this file
            metadata[file_name] = {
                "use_for_training": use_for_training,
                "upload_timestamp": datetime.utcnow().isoformat(),
                "file_size": file_size
            }
            
            # Save updated metadata
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=metadata_key,
                Body=json.dumps(metadata, indent=2)
            )
        except Exception as e:
            print(f"Warning: Failed to update metadata: {str(e)}")

    async def _get_metadata(self, user_id: str, avatar_id: str) -> Dict:
        """Get metadata dictionary for an avatar's training data"""
        metadata_key = f"{self._get_metadata_prefix(user_id, avatar_id)}metadata.json"
        
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=metadata_key)
            return json.loads(response['Body'].read().decode('utf-8'))
        except ClientError:
            return {}  # Return empty dict if metadata doesn't exist

    async def update_training_flag(self, user_id: str, avatar_id: str, file_name: str, use_for_training: bool):
        """Update the training flag for a specific file"""
        metadata = await self._get_metadata(user_id, avatar_id)
        
        if file_name in metadata:
            metadata[file_name]["use_for_training"] = use_for_training
        else:
            metadata[file_name] = {
                "use_for_training": use_for_training,
                "upload_timestamp": datetime.utcnow().isoformat()
            }
        
        metadata_key = f"{self._get_metadata_prefix(user_id, avatar_id)}metadata.json"
        self.s3_client.put_object(
            Bucket=self.bucket_name,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2)
        )

    async def list_training_files(self, user_id: str, avatar_id: str, training_only: Optional[bool] = None) -> List[TrainingDataMetadata]:
        """List training data files with optional filtering"""
        prefix = self._get_training_data_prefix(user_id, avatar_id)
        metadata = await self._get_metadata(user_id, avatar_id)
        
        try:
            response = self.s3_client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            files = []
            
            for obj in response.get('Contents', []):
                file_key = obj['Key']
                file_name = file_key.split('/')[-1]
                
                if file_name in metadata:
                    file_metadata = metadata[file_name]
                    use_for_training = file_metadata.get("use_for_training", True)
                    
                    # Apply filter if specified
                    if training_only is True and not use_for_training:
                        continue
                    elif training_only is False and use_for_training:
                        continue
                    
                    files.append(TrainingDataMetadata(
                        file_key=file_key,
                        use_for_training=use_for_training,
                        upload_timestamp=datetime.fromisoformat(file_metadata.get("upload_timestamp", datetime.utcnow().isoformat())),
                        file_size=obj['Size']
                    ))
            
            return files
        except ClientError as e:
            raise Exception(f"Failed to list files: {str(e)}")

    async def download_training_files(self, user_id: str, avatar_id: str) -> List[Tuple[str, bytes]]:
        """Download all files marked for training"""
        files = await self.list_training_files(user_id, avatar_id, training_only=True)
        downloaded_files = []
        
        for file_metadata in files:
            try:
                response = self.s3_client.get_object(Bucket=self.bucket_name, Key=file_metadata.file_key)
                file_content = response['Body'].read()
                file_name = file_metadata.file_key.split('/')[-1]
                downloaded_files.append((file_name, file_content))
            except ClientError as e:
                print(f"Failed to download {file_metadata.file_key}: {str(e)}")
        
        return downloaded_files

    async def upload_adapter(self, user_id: str, avatar_id: str, adapter_data: bytes):
        """Upload trained adapter to S3"""
        adapter_key = f"{self._get_adapter_prefix(user_id, avatar_id)}adapter.safetensors"
        
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=adapter_key,
                Body=adapter_data
            )
            return adapter_key
        except ClientError as e:
            raise Exception(f"Failed to upload adapter: {str(e)}")

    async def delete_non_training_files(self, user_id: str, avatar_id: str):
        """Delete all files not marked for training"""
        files = await self.list_training_files(user_id, avatar_id, training_only=False)
        deleted_files = []
        
        for file_metadata in files:
            try:
                self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_metadata.file_key)
                deleted_files.append(file_metadata.file_key)
            except ClientError as e:
                print(f"Failed to delete {file_metadata.file_key}: {str(e)}")
        
        return deleted_files

    async def delete_training_file(self, user_id: str, avatar_id: str, file_name: str):
        """Delete a specific training file"""
        file_key = f"{self._get_training_data_prefix(user_id, avatar_id)}{file_name}"
        
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_key)
            
            # Update metadata
            metadata = await self._get_metadata(user_id, avatar_id)
            if file_name in metadata:
                del metadata[file_name]
                metadata_key = f"{self._get_metadata_prefix(user_id, avatar_id)}metadata.json"
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2)
                )
        except ClientError as e:
            raise Exception(f"Failed to delete file: {str(e)}")
