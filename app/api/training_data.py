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
    try:
        file_content = await file.read()
        file_key = await s3_service.upload_training_data(
            user_id, avatar_id, file.filename, file_content, use_for_training
        )
        
        return {
            "message": "File uploaded successfully",
            "file_key": file_key,
            "use_for_training": use_for_training
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{user_id}/{avatar_id}/list")
async def list_training_data(
    user_id: str,
    avatar_id: str,
    training_only: Optional[bool] = Query(None)
) -> List[TrainingDataMetadata]:
    """List training data files with optional filtering"""
    try:
        files = await s3_service.list_training_files(user_id, avatar_id, training_only)
        return files
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{user_id}/{avatar_id}/{file_name}/training-flag")
async def update_training_flag(
    user_id: str,
    avatar_id: str,
    file_name: str,
    update: MetadataUpdate
):
    """Update whether a file should be used for training"""
    try:
        await s3_service.update_training_flag(user_id, avatar_id, file_name, update.use_for_training)
        return {"message": f"Training flag updated for {file_name}"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{avatar_id}/non-training-files")
async def delete_non_training_files(user_id: str, avatar_id: str):
    """Delete all files not marked for training"""
    try:
        deleted_files = await s3_service.delete_non_training_files(user_id, avatar_id)
        return {
            "message": f"Deleted {len(deleted_files)} non-training files",
            "deleted_files": deleted_files
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{avatar_id}/{file_name}")
async def delete_training_file(user_id: str, avatar_id: str, file_name: str):
    """Delete a specific training file"""
    try:
        await s3_service.delete_training_file(user_id, avatar_id, file_name)
        return {"message": f"File {file_name} deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
