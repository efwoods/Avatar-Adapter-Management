# api/training_data.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional

from service.persistence_service import get_adapter_persistence_manager
from db.schema.models import MetadataUpdate, TrainingDataMetadata
from core.logging import logger

router = APIRouter()

@router.post("/{user_id}/{avatar_id}/upload")
async def upload_training_data(
    user_id: str,
    avatar_id: str,
    file: UploadFile = File(...),
    use_for_training: bool = Query(True)
):
    """Upload training data file"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Read file content
        file_content = await file.read()
        
        # Use centralized upload method
        result = await persistence_manager.upload_training_file(
            filename=file.filename,
            file_content=file_content,
            content_type=file.content_type or 'application/octet-stream',
            use_for_training=use_for_training
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error uploading training data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to upload training data: {str(e)}")

@router.get("/{user_id}/{avatar_id}/list")
async def list_training_data(
    user_id: str,
    avatar_id: str,
    training_only: Optional[bool] = Query(None)
) -> List[TrainingDataMetadata]:
    """List training data files with optional filtering"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized list method
        files_list = await persistence_manager.list_training_files(training_only)
        
        # Convert to TrainingDataMetadata objects
        return [
            TrainingDataMetadata(
                filename=f["filename"],
                use_for_training=f["use_for_training"],
                file_size=f["file_size"],
                last_modified=f["last_modified"],
                content_type=f["content_type"],
                upload_timestamp=f["upload_timestamp"],
                s3_key=f["s3_key"]
            ) for f in files_list
        ]
        
    except Exception as e:
        logger.error(f"Error listing training data: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to list training data: {str(e)}")

@router.put("/{user_id}/{avatar_id}/{file_name}/training-flag")
async def update_training_flag(
    user_id: str,
    avatar_id: str,
    file_name: str,
    update: MetadataUpdate
):
    """Update whether a file should be used for training"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized update method
        result = await persistence_manager.update_training_flag(
            filename=file_name,
            use_for_training=update.use_for_training
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error updating training flag: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update training flag: {str(e)}")

@router.delete("/{user_id}/{avatar_id}/{file_name}")
async def delete_training_file(user_id: str, avatar_id: str, file_name: str):
    """Delete a specific training file"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized delete method
        result = await persistence_manager.delete_training_file(file_name)
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting training file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete training file: {str(e)}")

@router.get("/{user_id}/{avatar_id}/download/{file_name}")
async def download_training_file(user_id: str, avatar_id: str, file_name: str):
    """Download a specific training data file"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized download URL generation
        result = await persistence_manager.get_training_file_download_url(file_name)
        
        return result
        
    except Exception as e:
        logger.error(f"Error downloading training file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download training file: {str(e)}")

@router.get("/{user_id}/{avatar_id}/metadata")
async def get_training_metadata(user_id: str, avatar_id: str):
    """Get the complete training metadata for an avatar"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Get metadata using centralized method
        metadata = await persistence_manager._get_training_metadata()
        
        # Count files by training status
        training_files = sum(1 for use_training in metadata.values() if use_training)
        non_training_files = len(metadata) - training_files
        
        return {
            "status": "found" if metadata else "not_found",
            "user_id": user_id,
            "avatar_id": avatar_id,
            "metadata": metadata,
            "summary": {
                "total_files": len(metadata),
                "training_files": training_files,
                "non_training_files": non_training_files
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting training metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training metadata: {str(e)}")

@router.delete("/{user_id}/{avatar_id}/non-training-files")
async def delete_non_training_files(user_id: str, avatar_id: str):
    """Delete all files not marked for training"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized method
        result = await persistence_manager.delete_non_training_files()
        
        return result
        
    except Exception as e:
        logger.error(f"Error deleting non-training files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete non-training files: {str(e)}")