# api/adapters.py

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import os
import tempfile
import json
from datetime import datetime

from classes.lora_manager import LoRAManager
from db.schema.models import TrainingRequest, AdapterConfig
from service.persistence_service import get_adapter_persistence_manager
from service.training_service import TrainingService
from service.s3_service import S3Service
from core.logging import logger

router = APIRouter()
lora_manager = LoRAManager()
training_service = TrainingService()
s3_service = S3Service()

@router.post("/{user_id}/{avatar_id}/create")
async def create_adapter(
    user_id: str, 
    avatar_id: str, 
    adapter_name: str = "default"
) -> AdapterConfig:
    """Create a new adapter configuration"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Check if adapter already exists
        adapter_path = f"users/{user_id}/avatars/{avatar_id}/adapters/"
        
        try:
            # Try to list existing adapters
            response = persistence_manager.s3_client.list_objects_v2(
                Bucket=persistence_manager.s3_bucket,
                Prefix=adapter_path
            )
            
            if 'Contents' in response and any(obj['Key'].endswith('adapter_backup.zip') for obj in response['Contents']):
                logger.info(f"Adapter already exists for user {user_id}, avatar {avatar_id}")
                # Return existing adapter config
                return AdapterConfig(
                    user_id=user_id,
                    avatar_id=avatar_id,
                    adapter_name=adapter_name,
                    status="existing",
                    created_at=datetime.now(),
                    s3_path=adapter_path
                )
        except Exception as e:
            logger.warning(f"Error checking existing adapter: {e}")
        
        # Create new adapter locally
        with tempfile.TemporaryDirectory() as temp_dir:
            local_adapter_path = os.path.join(temp_dir, "adapters")
            os.makedirs(local_adapter_path, exist_ok=True)
            
            # Initialize empty adapter structure
            adapter_config = {
                "adapter_name": adapter_name,
                "user_id": user_id,
                "avatar_id": avatar_id,
                "created_at": datetime.now().isoformat(),
                "version": "1.0.0",
                "status": "untrained",
                "training_history": []
            }
            
            # Save adapter config
            config_path = os.path.join(local_adapter_path, "adapter_config.json")
            with open(config_path, 'w') as f:
                json.dump(adapter_config, f, indent=2)
            
            # Create placeholder adapter files (LoRA specific structure)
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
            backup_metadata = await persistence_manager.backup_adapters_to_s3(local_adapter_path)
            
            logger.info(f"Created and backed up new adapter for user {user_id}, avatar {avatar_id}")
            
            return AdapterConfig(
                user_id=user_id,
                avatar_id=avatar_id,
                adapter_name=adapter_name,
                status="created",
                created_at=datetime.now(),
                s3_path=adapter_path,
                metadata=backup_metadata
            )
            
    except Exception as e:
        logger.error(f"Error creating adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create adapter: {str(e)}")

@router.post("/{user_id}/{avatar_id}/train")
async def train_adapter(
    user_id: str, 
    avatar_id: str, 
    training_params: Optional[Dict] = None
):
    """Train a LoRA adapter"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Get metadata to determine which files to use for training
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        metadata_key = f"{metadata_path}metadata.json"
        
        training_files = []
        try:
            # Get training metadata
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            # Filter files marked for training
            training_files = [filename for filename, use_for_training in metadata.items() if use_for_training]
            logger.info(f"Found {len(training_files)} files marked for training")
            
        except Exception as e:
            logger.warning(f"No training metadata found: {e}. Proceeding without training data.")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            local_adapter_path = os.path.join(temp_dir, "adapters")
            local_training_path = os.path.join(temp_dir, "training_data")
            os.makedirs(local_adapter_path, exist_ok=True)
            os.makedirs(local_training_path, exist_ok=True)
            
            # Restore existing adapter or create new one
            try:
                await persistence_manager.restore_adapters_from_s3(local_adapter_path)
                logger.info("Restored existing adapter from S3")
            except HTTPException as e:
                if e.status_code == 404:
                    # Create new adapter if none exists
                    logger.info("No existing adapter found, creating new one")
                    await create_adapter(user_id, avatar_id)
                    await persistence_manager.restore_adapters_from_s3(local_adapter_path)
                else:
                    raise
            
            # Download training data if available
            if training_files:
                training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
                
                for filename in training_files:
                    try:
                        file_key = f"{training_data_path}{filename}"
                        local_file_path = os.path.join(local_training_path, filename)
                        
                        persistence_manager.s3_client.download_file(
                            persistence_manager.s3_bucket,
                            file_key,
                            local_file_path
                        )
                        logger.info(f"Downloaded training file: {filename}")
                    except Exception as e:
                        logger.warning(f"Failed to download training file {filename}: {e}")
            
            # Train the adapter
            if training_files and os.listdir(local_training_path):
                try:
                    # Use training service to train the adapter
                    training_result = await training_service.train_lora_adapter(
                        adapter_path=local_adapter_path,
                        training_data_path=local_training_path,
                        training_params=training_params or {}
                    )
                    
                    # Update adapter config with training info
                    config_path = os.path.join(local_adapter_path, "adapter_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            adapter_config = json.load(f)
                        
                        adapter_config.update({
                            "status": "trained",
                            "last_training": datetime.now().isoformat(),
                            "training_files_used": training_files,
                            "training_result": training_result
                        })
                        
                        # Add to training history
                        if "training_history" not in adapter_config:
                            adapter_config["training_history"] = []
                        
                        adapter_config["training_history"].append({
                            "timestamp": datetime.now().isoformat(),
                            "files_used": training_files,
                            "training_params": training_params,
                            "result": training_result
                        })
                        
                        with open(config_path, 'w') as f:
                            json.dump(adapter_config, f, indent=2)
                    
                    logger.info(f"Successfully trained adapter for user {user_id}, avatar {avatar_id}")
                    
                except Exception as e:
                    logger.error(f"Training failed: {e}")
                    # Update status to indicate training failure
                    config_path = os.path.join(local_adapter_path, "adapter_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            adapter_config = json.load(f)
                        adapter_config["status"] = "training_failed"
                        adapter_config["last_error"] = str(e)
                        with open(config_path, 'w') as f:
                            json.dump(adapter_config, f, indent=2)
            else:
                logger.info("No training data available, uploading untrained adapter")
                # Update status to untrained
                config_path = os.path.join(local_adapter_path, "adapter_config.json")
                if os.path.exists(config_path):
                    with open(config_path, 'r') as f:
                        adapter_config = json.load(f)
                    adapter_config["status"] = "untrained"
                    adapter_config["last_updated"] = datetime.now().isoformat()
                    with open(config_path, 'w') as f:
                        json.dump(adapter_config, f, indent=2)
            
            # Backup trained/updated adapter to S3
            backup_metadata = await persistence_manager.backup_adapters_to_s3(local_adapter_path)
            
            return {
                "status": "success",
                "message": f"Adapter training completed for user {user_id}, avatar {avatar_id}",
                "training_files_used": training_files,
                "backup_metadata": backup_metadata
            }
            
    except Exception as e:
        logger.error(f"Error training adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to train adapter: {str(e)}")

@router.delete("/{user_id}/{avatar_id}")
async def delete_adapter(user_id: str, avatar_id: str):
    """Delete an adapter"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths to delete
        adapter_path = f"users/{user_id}/avatars/{avatar_id}/adapters/"
        
        # List all objects with the adapter prefix
        response = persistence_manager.s3_client.list_objects_v2(
            Bucket=persistence_manager.s3_bucket,
            Prefix=adapter_path
        )
        
        if 'Contents' not in response:
            raise HTTPException(
                status_code=404,
                detail=f"No adapter found for user {user_id}, avatar {avatar_id}"
            )
        
        # Delete all adapter-related objects
        objects_to_delete = [{'Key': obj['Key']} for obj in response['Contents']]
        
        if objects_to_delete:
            persistence_manager.s3_client.delete_objects(
                Bucket=persistence_manager.s3_bucket,
                Delete={'Objects': objects_to_delete}
            )
            
            logger.info(f"Deleted {len(objects_to_delete)} adapter objects for user {user_id}, avatar {avatar_id}")
        
        return {
            "status": "success",
            "message": f"Adapter deleted for user {user_id}, avatar {avatar_id}",
            "deleted_objects": len(objects_to_delete)
        }
        
    except Exception as e:
        logger.error(f"Error deleting adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete adapter: {str(e)}")

@router.get("/{user_id}/{avatar_id}")
async def get_adapter(user_id: str, avatar_id: str):
    """Get an adapter - returns adapter file for download or creates new one if doesn't exist"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Check if adapter exists
        adapter_path = f"users/{user_id}/avatars/{avatar_id}/adapters/"
        adapter_key = f"{adapter_path}adapter_backup.zip"
        
        try:
            # Check if adapter exists in S3
            persistence_manager.s3_client.head_object(
                Bucket=persistence_manager.s3_bucket,
                Key=adapter_key
            )
            
            # Adapter exists, download and return
            with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                persistence_manager.s3_client.download_file(
                    persistence_manager.s3_bucket,
                    adapter_key,
                    temp_file.name
                )
                
                # Get adapter metadata
                try:
                    metadata_key = f"{adapter_path}backup_metadata.json"
                    metadata_obj = persistence_manager.s3_client.get_object(
                        Bucket=persistence_manager.s3_bucket,
                        Key=metadata_key
                    )
                    metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
                except:
                    metadata = {}
                
                logger.info(f"Retrieved existing adapter for user {user_id}, avatar {avatar_id}")
                
                # Return file response for download
                return FileResponse(
                    path=temp_file.name,
                    filename=f"adapter_{user_id}_{avatar_id}.zip",
                    media_type="application/zip",
                    headers={
                        "X-Adapter-Metadata": json.dumps(metadata),
                        "X-User-ID": user_id,
                        "X-Avatar-ID": avatar_id
                    }
                )
                
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                # Adapter doesn't exist, create new one
                logger.info(f"No existing adapter found for user {user_id}, avatar {avatar_id}, creating new one")
                
                # Create new adapter
                adapter_config = await create_adapter(user_id, avatar_id)
                
                # Now retrieve the newly created adapter
                with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
                    persistence_manager.s3_client.download_file(
                        persistence_manager.s3_bucket,
                        adapter_key,
                        temp_file.name
                    )
                    
                    return FileResponse(
                        path=temp_file.name,
                        filename=f"adapter_{user_id}_{avatar_id}.zip",
                        media_type="application/zip",
                        headers={
                            "X-Adapter-Status": "newly_created",
                            "X-User-ID": user_id,
                            "X-Avatar-ID": avatar_id
                        }
                    )
            else:
                raise
        
    except Exception as e:
        logger.error(f"Error getting adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get adapter: {str(e)}")

@router.get("/{user_id}/{avatar_id}/info")
async def get_adapter_info(user_id: str, avatar_id: str):
    """Get adapter information without downloading the file"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Get adapter metadata
        adapter_path = f"users/{user_id}/avatars/{avatar_id}/adapters/"
        metadata_key = f"{adapter_path}backup_metadata.json"
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            # Also try to get adapter config if available
            try:
                with tempfile.TemporaryDirectory() as temp_dir:
                    local_adapter_path = os.path.join(temp_dir, "adapters")
                    await persistence_manager.restore_adapters_from_s3(local_adapter_path)
                    
                    config_path = os.path.join(local_adapter_path, "adapter_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, 'r') as f:
                            adapter_config = json.load(f)
                        metadata["adapter_config"] = adapter_config
            except:
                pass
            
            return {
                "status": "found",
                "user_id": user_id,
                "avatar_id": avatar_id,
                "metadata": metadata
            }
            
        except Exception as e:
            if "404" in str(e) or "Not Found" in str(e):
                return {
                    "status": "not_found",
                    "user_id": user_id,
                    "avatar_id": avatar_id,
                    "message": "Adapter does not exist"
                }
            else:
                raise
        
    except Exception as e:
        logger.error(f"Error getting adapter info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get adapter info: {str(e)}")