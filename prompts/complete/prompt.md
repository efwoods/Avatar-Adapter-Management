I need you to complete the adpater and training_data endpoint routes and use the persistence capabilities already defined in the code.

(base) linux-pc@pc:~/gh/projects/NeuralNexus/Avatar-Adapter-Management$ tree .
.
├── app
│   ├── api
│   │   ├── adapters.py
│   │   ├── __init__.py
│   │   ├── persistence.py
│   │   ├── __pycache__
│   │   │   ├── adapters.cpython-311.pyc
│   │   │   ├── __init__.cpython-311.pyc
│   │   │   ├── persistence.cpython-311.pyc
│   │   │   └── training_data.cpython-311.pyc
│   │   └── training_data.py
│   ├── classes
│   │   ├── AdapterPersistenceManager.py
│   │   ├── __init__.py
│   │   └── __pycache__
│   │       ├── AdapterPersistenceManager.cpython-311.pyc
│   │       ├── __init__.cpython-311.pyc
│   │       └── lora_manager.cpython-311.pyc
│   ├── core
│   │   ├── config.py
│   │   ├── __init__.py
│   │   ├── logging.py
│   │   └── __pycache__
│   │       ├── config.cpython-311.pyc
│   │       ├── __init__.cpython-311.pyc
│   │       └── logging.cpython-311.pyc
│   ├── db
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   └── __init__.cpython-311.pyc
│   │   └── schema
│   │       ├── __init__.py
│   │       ├── models.py
│   │       └── __pycache__
│   │           ├── __init__.cpython-311.pyc
│   │           └── models.cpython-311.pyc
│   ├── __init__.py
│   ├── main.py
│   ├── __pycache__
│   │   └── main.cpython-311.pyc
│   └── service
│       ├── __init__.py
│       ├── persistence_service.py
│       ├── __pycache__
│       │   ├── __init__.cpython-311.pyc
│       │   ├── persistence_service.cpython-311.pyc
│       │   ├── s3_service.cpython-311.pyc
│       │   └── training_service.cpython-311.pyc
│       ├── s3_service.py
│       └── training_service.py
├── docker-compose.yml
├── Dockerfile.dev
├── LICENSE
├── prompt.md
├── prompts
│   └── prompt.md
├── README.md
└── requirements.txt
----

## app/api/adapters.py
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict
from classes.lora_manager import LoRAManager
from db.schema.models import TrainingRequest, AdapterConfig

router = APIRouter()
lora_manager = LoRAManager()

@router.post("/{user_id}/{avatar_id}/create")
async def create_adapter(user_id: str, avatar_id: str, adapter_name: str = "default") -> AdapterConfig:
    """Create a new adapter configuration"""
    """
    The adapters need to be backed up to the following location:
    users/{user_id}/avatars/{avatar_id}/adapters/


    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """

@router.post("/{user_id}/{avatar_id}/train")
async def train_adapter(user_id: str, avatar_id: str, training_params: Optional[Dict] = None):
    """Train a LoRA adapter"""
    """    There is an individual metadata.json file that is used to determine if a file is used for model finetuning. 
    That file is located at: users/{user_id}/avatars/{avatar_id}/
    adapters/metadata/
     
    This endpoint should collect the training data as from the s3 bucket if the data is marked as to be used for training in the metadata.json file. It should then train the adapter and update the adapter in s3. If the adapter does not yet exist, it needs to be created, trained, and uploaded to s3. If there are no training documents, the adapter is uploaded to s3 untrained. 

    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """


@router.delete("/{user_id}/{avatar_id}")
async def delete_adapter(user_id: str, avatar_id: str):
    """Delete an adapter"""
    """
    The adapters need to be backed up to the following location:
    users/{user_id}/avatars/{avatar_id}/adapters/


    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """    

@router.get("/{user_id}/{avatar_id}")
async def get_adapter(user_id: str, avatar_id: str):
    """Get an adapter"""
    """This endpoint is used to retrieve an adapter. Another fastapi in a separate docker container will call this endpoint to retreive and eventually attach the adapter to a LLM. This endpoint needs to return the adapter from s3. If the adapter does not yet exist, the adapter needs to be created, backedup to s3, and returned.
    """
        """
    The adapters need to be backed up to the following location:
    users/{user_id}/avatars/{avatar_id}/adapters/


    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """
    
----

## app/api/training_data.py
from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
from service.s3_service import S3Service
from db.schema.models import S3UploadRequest, MetadataUpdate, TrainingDataMetadata

router = APIRouter()
s3_service = S3Service()

@router.post("/{user_id}/{avatar_id}/upload")
async def upload_training_data(
    user_id: str,
    avatar_id: str,
    file: UploadFile = File(...),
    use_for_training: bool = Query(True)
):
    """Upload training data file"""
    """When a file is uploaded, the metadata.json dict appends the filename: bool where a value of 'True' indicates that the file is used for model fine-tuning; True is the default value
    """
        """
    There is an individual metadata.json file that is used to determine if a file is used for model finetuning. 
    That file is located at: users/{user_id}/avatars/{avatar_id}/adapters/metadata/

    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """

@router.get("/{user_id}/{avatar_id}/list")
async def list_training_data(
    user_id: str,
    avatar_id: str,
    training_only: Optional[bool] = Query(None)
) -> List[TrainingDataMetadata]:
    """List training data files with optional filtering"""
        """
    There is an individual metadata.json file that is used to determine if a file is used for model finetuning. 
    That file is located at: users/{user_id}/avatars/{avatar_id}/adapters/metadata/

    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """

@router.put("/{user_id}/{avatar_id}/{file_name}/training-flag")
async def update_training_flag(
    user_id: str,
    avatar_id: str,
    file_name: str,
    update: MetadataUpdate
):
    """Update whether a file should be used for training"""
    """
    There is an individual metadata.json file that is used to determine if a file is used for model finetuning. 
    That file is located at: users/{user_id}/avatars/{avatar_id}/adapters/metadata/

    ## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information

    """

@router.delete("/{user_id}/{avatar_id}/non-training-files")
async def delete_non_training_files(user_id: str, avatar_id: str):
    """Delete all files not marked for training"""


@router.delete("/{user_id}/{avatar_id}/{file_name}")
async def delete_training_file(user_id: str, avatar_id: str, file_name: str):
    """Delete a specific training file"""
---

#service/persistence_service.py
from fastapi import HTTPException
from classes import AdapterPersistenceManager
from core.logging import logger
from core.config import settings

# Global variables to hold managers
s3_client_instance = None

def get_s3_client():
    """Dependency function that returns the global S3 client instance"""
    if s3_client_instance is None:
        raise HTTPException(500, "S3 client not initialized")
    return s3_client_instance


def get_adapter_persistence_manager(avatar_id: str) -> AdapterPersistenceManager:
    """Get adapter persistence manager instance with dynamic user_id from environment"""
    user_id = settings.USER_ID
    
    if not user_id:
        logger.error("USER_ID setting is required")
        raise HTTPException(
            status_code=500,
            detail="USER_ID environment variable is required but not set"
        )
    
    return AdapterPersistenceManager(
        s3_client=get_s3_client(),
        settings=settings,
        user_id=user_id,
        avatar_id=avatar_id
    )


---

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

---

# FastAPI LoRA Adapter Management System
## app/main.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from contextlib import asynccontextmanager
import uvicorn
import boto3

from core.config import settings

# Import your existing routers
from api import adapters, training_data, persistence
from core.logging import logger
from service.persistence_service import (
    s3_client_instance, 
    get_s3_client, 
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global s3_client_instance
    
    # Startup
    logger.info("Application startup - Initializing S3 and settings")
    
    # Get settings and validate required fields
    # settings are initialized on startup

    user_id = settings.USER_ID
    if not user_id:
        logger.error("USER_ID setting is required")
        raise RuntimeError("USER_ID setting is required")
    
    logger.info(f"Starting Adapter Management API for user: {user_id}")
    logger.info(f"App: LoRA Adapter Management API v1.0.0")
    
    # Validate required settings
    if not settings.s3_bucket_name:
        logger.error("S3_BUCKET_NAME is required")
        raise RuntimeError("S3_BUCKET_NAME environment variable is required")
    
    # Initialize S3 client with error handling
    try:
        s3_client = boto3.client(
            's3',
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
            region_name=settings.aws_region
        )
        # Test S3 connection
        s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        logger.info(f"S3 connection successful to bucket: {settings.s3_bucket_name}")
        s3_client_instance = s3_client
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        raise RuntimeError(f"S3 initialization failed: {e}")
    
    logger.info(f"Adapter persistence configured for user: {user_id}")
    logger.info(f"S3 bucket: {settings.s3_bucket_name}")
    
    yield
    
    # Shutdown
    logger.info("Application shutdown - Cleaning up resources")
    s3_client_instance = None
    logger.info("Cleanup completed")

app = FastAPI(
    title="LoRA Adapter Management API",
    description="API for managing LoRA adapters with S3 storage",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(adapters.router, prefix="/adapters", tags=["adapters"])
app.include_router(training_data.router, prefix="/training-data", tags=["training-data"])
app.include_router(persistence.router, prefix="/persistence", tags=["persistence"])

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        s3_client = get_s3_client()
        
        # Test S3 connection
        s3_status = "connected"
        try:
            s3_client.head_bucket(Bucket=settings.s3_bucket_name)
        except Exception:
            s3_status = "disconnected"
        
        return {
            "status": "healthy",
            "s3_status": s3_status,
            "s3_bucket": settings.s3_bucket_name,
            "user_id": settings.USER_ID
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/", tags=["📖 Documentation"])
async def root(request: Request):
    return RedirectResponse(url=f"{request.scope.get('root_path', '')}/docs")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)