# api/adapters.py - Final Simplified Version

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse
from typing import Optional, Dict, Any
import tempfile
import json
from datetime import datetime

from db.schema.models import TrainingRequest, AdapterConfig
from service.persistence_service import get_adapter_persistence_manager
from service.training_service import TrainingService
from core.logging import logger

router = APIRouter()
training_service = TrainingService()

@router.post("/{user_id}/{avatar_id}/create")
async def create_adapter(
    user_id: str, 
    avatar_id: str, 
    adapter_name: str = "default"
) -> AdapterConfig:
    """Create a new adapter configuration"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized create method
        result = await persistence_manager.create_adapter(adapter_name)
        
        return AdapterConfig(
            user_id=user_id,
            avatar_id=avatar_id,
            adapter_name=adapter_name,
            status=result["status"],
            created_at=datetime.now(),
            s3_path=result["s3_path"],
            metadata=result.get("metadata")
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
    """Train a LoRA adapter using centralized persistence manager"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use enhanced training service with persistence manager
        result = await training_service.train_with_persistence_manager(
            persistence_manager=persistence_manager,
            training_params=training_params or {}
        )
        
        return {
            "status": "success" if result["success"] else "failed",
            "message": result["message"],
            "training_result": result
        }
            
    except Exception as e:
        logger.error(f"Error training adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to train adapter: {str(e)}")

@router.delete("/{user_id}/{avatar_id}")
async def delete_adapter(user_id: str, avatar_id: str):
    """Delete an adapter"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized delete method
        result = await persistence_manager.delete_adapter()
        return result
        
    except Exception as e:
        logger.error(f"Error deleting adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete adapter: {str(e)}")

@router.get("/{user_id}/{avatar_id}")
async def get_adapter(user_id: str, avatar_id: str):
    """Get an adapter - returns adapter file for download or creates new one if doesn't exist"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Check if adapter exists using centralized method
        if not await persistence_manager.adapter_exists():
            logger.info(f"No existing adapter found for user {user_id}, avatar {avatar_id}, creating new one")
            await persistence_manager.create_adapter()
        
        # Download adapter backup
        adapter_key = f"{persistence_manager._get_s3_adapter_path()}adapter_backup.zip"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            persistence_manager.s3_client.download_file(
                persistence_manager.s3_bucket,
                adapter_key,
                temp_file.name
            )
            
            # Get adapter metadata
            try:
                metadata_key = f"{persistence_manager._get_s3_adapter_path()}backup_metadata.json"
                metadata_obj = persistence_manager.s3_client.get_object(
                    Bucket=persistence_manager.s3_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            except:
                metadata = {}
            
            logger.info(f"Retrieved adapter for user {user_id}, avatar {avatar_id}")
            
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
        logger.error(f"Error getting adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get adapter: {str(e)}")

@router.get("/{user_id}/{avatar_id}/info")
async def get_adapter_info(user_id: str, avatar_id: str):
    """Get adapter information without downloading the file"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized info method
        return await persistence_manager.get_adapter_info()
        
    except Exception as e:
        logger.error(f"Error getting adapter info: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get adapter info: {str(e)}")

@router.get("/{user_id}/{avatar_id}/training-recommendations")
async def get_training_recommendations(user_id: str, avatar_id: str):
    """Get training parameter recommendations based on available data"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use enhanced training service with persistence manager
        recommendations = await training_service.get_training_recommendations_with_persistence(
            persistence_manager=persistence_manager
        )
        
        return recommendations
        
    except Exception as e:
        logger.error(f"Error getting training recommendations: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training recommendations: {str(e)}")

@router.get("/{user_id}/{avatar_id}/validate-training-data")
async def validate_training_data(user_id: str, avatar_id: str):
    """Validate training data for an avatar"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use enhanced training service with persistence manager
        validation = await training_service.validate_training_data_with_persistence(
            persistence_manager=persistence_manager
        )
        
        return validation
        
    except Exception as e:
        logger.error(f"Error validating training data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to validate training data: {str(e)}")