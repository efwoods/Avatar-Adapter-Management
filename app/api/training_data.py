# api/training_data.py

from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import List, Optional
import json
import os
from datetime import datetime

from service.s3_service import S3Service
from service.persistence_service import get_adapter_persistence_manager
from db.schema.models import S3UploadRequest, MetadataUpdate, TrainingDataMetadata
from core.logging import logger

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
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        
        # Upload file to S3
        file_key = f"{training_data_path}{file.filename}"
        
        # Read file content
        file_content = await file.read()
        
        # Upload to S3
        persistence_manager.s3_client.put_object(
            Bucket=persistence_manager.s3_bucket,
            Key=file_key,
            Body=file_content,
            ContentType=file.content_type or 'application/octet-stream',
            Metadata={
                'user_id': user_id,
                'avatar_id': avatar_id,
                'upload_timestamp': datetime.now().isoformat(),
                'original_filename': file.filename,
                'use_for_training': str(use_for_training)
            }
        )
        
        # Update metadata.json
        metadata_key = f"{metadata_path}metadata.json"
        
        # Get existing metadata or create new
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
        except:
            metadata = {}
        
        # Update metadata for this file
        metadata[file.filename] = use_for_training
        
        # Upload updated metadata
        persistence_manager.s3_client.put_object(
            Bucket=persistence_manager.s3_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Uploaded training file {file.filename} for user {user_id}, avatar {avatar_id}")
        
        return {
            "status": "success",
            "message": f"File {file.filename} uploaded successfully",
            "file_size": len(file_content),
            "use_for_training": use_for_training,
            "s3_key": file_key
        }
        
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
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        
        # Get metadata
        metadata_key = f"{metadata_path}metadata.json"
        training_metadata = {}
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            training_metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.warning(f"No training metadata found: {e}")
        
        # List files in training data directory
        response = persistence_manager.s3_client.list_objects_v2(
            Bucket=persistence_manager.s3_bucket,
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
                    head_response = persistence_manager.s3_client.head_object(
                        Bucket=persistence_manager.s3_bucket,
                        Key=obj['Key']
                    )
                    file_metadata = head_response.get('Metadata', {})
                except:
                    file_metadata = {}
                
                files_list.append(TrainingDataMetadata(
                    filename=filename,
                    use_for_training=use_for_training,
                    file_size=obj['Size'],
                    last_modified=obj['LastModified'],
                    content_type=file_metadata.get('content-type', 'unknown'),
                    upload_timestamp=file_metadata.get('upload_timestamp'),
                    s3_key=obj['Key']
                ))
        
        logger.info(f"Listed {len(files_list)} training data files for user {user_id}, avatar {avatar_id}")
        
        return files_list
        
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
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        
        # Check if file exists
        file_key = f"{training_data_path}{file_name}"
        try:
            persistence_manager.s3_client.head_object(
                Bucket=persistence_manager.s3_bucket,
                Key=file_key
            )
        except:
            raise HTTPException(
                status_code=404,
                detail=f"Training data file {file_name} not found"
            )
        
        # Get existing metadata
        metadata_key = f"{metadata_path}metadata.json"
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
        except:
            metadata = {}
        
        # Update metadata for this file
        old_value = metadata.get(file_name, False)
        metadata[file_name] = update.use_for_training
        
        # Upload updated metadata
        persistence_manager.s3_client.put_object(
            Bucket=persistence_manager.s3_bucket,
            Key=metadata_key,
            Body=json.dumps(metadata, indent=2),
            ContentType='application/json'
        )
        
        logger.info(f"Updated training flag for {file_name}: {old_value} -> {update.use_for_training}")
        
        return {
            "status": "success",
            "message": f"Training flag updated for {file_name}",
            "filename": file_name,
            "old_value": old_value,
            "new_value": update.use_for_training
        }
        
    except Exception as e:
        logger.error(f"Error updating training flag: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to update training flag: {str(e)}")

@router.delete("/{user_id}/{avatar_id}/{file_name}")
async def delete_training_file(user_id: str, avatar_id: str, file_name: str):
    """Delete a specific training file"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        
        # Check if file exists
        file_key = f"{training_data_path}{file_name}"
        try:
            persistence_manager.s3_client.head_object(
                Bucket=persistence_manager.s3_bucket,
                Key=file_key
            )
        except:
            raise HTTPException(
                status_code=404,
                detail=f"Training data file {file_name} not found"
            )
        
        # Delete the file
        persistence_manager.s3_client.delete_object(
            Bucket=persistence_manager.s3_bucket,
            Key=file_key
        )
        
        # Update metadata by removing the file entry
        metadata_key = f"{metadata_path}metadata.json"
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            # Remove file from metadata
            if file_name in metadata:
                del metadata[file_name]
                
                # Upload updated metadata
                persistence_manager.s3_client.put_object(
                    Bucket=persistence_manager.s3_bucket,
                    Key=metadata_key,
                    Body=json.dumps(metadata, indent=2),
                    ContentType='application/json'
                )
        except Exception as e:
            logger.warning(f"Could not update metadata after file deletion: {e}")
        
        logger.info(f"Deleted training file {file_name} for user {user_id}, avatar {avatar_id}")
        
        return {
            "status": "success",
            "message": f"Training file {file_name} deleted successfully",
            "filename": file_name
        }
        
    except Exception as e:
        logger.error(f"Error deleting training file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete training file: {str(e)}")

@router.get("/{user_id}/{avatar_id}/download/{file_name}")
async def download_training_file(user_id: str, avatar_id: str, file_name: str):
    """Download a specific training data file"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 path
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        file_key = f"{training_data_path}{file_name}"
        
        # Check if file exists
        try:
            head_response = persistence_manager.s3_client.head_object(
                Bucket=persistence_manager.s3_bucket,
                Key=file_key
            )
        except:
            raise HTTPException(
                status_code=404,
                detail=f"Training data file {file_name} not found"
            )
        
        # Generate presigned URL for download
        try:
            download_url = persistence_manager.s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': persistence_manager.s3_bucket, 'Key': file_key},
                ExpiresIn=3600  # 1 hour
            )
            
            return {
                "status": "success",
                "filename": file_name,
                "download_url": download_url,
                "expires_in": 3600,
                "file_size": head_response['ContentLength'],
                "last_modified": head_response['LastModified'].isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating presigned URL: {e}")
            raise HTTPException(
                status_code=500,
                detail="Failed to generate download URL"
            )
        
    except Exception as e:
        logger.error(f"Error downloading training file: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to download training file: {str(e)}")

@router.get("/{user_id}/{avatar_id}/metadata")
async def get_training_metadata(user_id: str, avatar_id: str):
    """Get the complete training metadata for an avatar"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 path
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        metadata_key = f"{metadata_path}metadata.json"
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            
            # Count files by training status
            training_files = sum(1 for use_training in metadata.values() if use_training)
            non_training_files = len(metadata) - training_files
            
            return {
                "status": "found",
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
            if "404" in str(e) or "Not Found" in str(e):
                return {
                    "status": "not_found",
                    "user_id": user_id,
                    "avatar_id": avatar_id,
                    "message": "No training metadata found",
                    "metadata": {},
                    "summary": {
                        "total_files": 0,
                        "training_files": 0,
                        "non_training_files": 0
                    }
                }
            else:
                raise
        
    except Exception as e:
        logger.error(f"Error getting training metadata: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get training metadata: {str(e)}")

@router.delete("/{user_id}/{avatar_id}/non-training-files")
async def delete_non_training_files(user_id: str, avatar_id: str):
    """Delete all files not marked for training"""
    try:
        # Get persistence manager
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Define S3 paths
        training_data_path = f"users/{user_id}/avatars/{avatar_id}/adapters/training_data/"
        metadata_path = f"users/{user_id}/avatars/{avatar_id}/adapters/metadata/"
        
        # Get metadata
        metadata_key = f"{metadata_path}metadata.json"
        training_metadata = {}
        
        try:
            metadata_obj = persistence_manager.s3_client.get_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key
            )
            training_metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
        except Exception as e:
            logger.warning(f"No training metadata found: {e}")
            return {
                "status": "success",
                "message": "No metadata found, no files to delete",
                "deleted_files": []
            }
        
        # List files in training data directory
        response = persistence_manager.s3_client.list_objects_v2(
            Bucket=persistence_manager.s3_bucket,
            Prefix=training_data_path
        )
        
        files_to_delete = []
        deleted_files = []
        
        if 'Contents' in response:
            for obj in response['Contents']:
                # Skip directory-like objects
                if obj['Key'].endswith('/'):
                    continue
                
                filename = os.path.basename(obj['Key'])
                use_for_training = training_metadata.get(filename, False)
                
                # If not marked for training, mark for deletion
                if not use_for_training:
                    files_to_delete.append({'Key': obj['Key']})
                    deleted_files.append(filename)
        
        # Delete files
        if files_to_delete:
            persistence_manager.s3_client.delete_objects(
                Bucket=persistence_manager.s3_bucket,
                Delete={'Objects': files_to_delete}
            )
            
            # Update metadata by removing deleted files
            updated_metadata = {
                filename: use_for_training 
                for filename, use_for_training in training_metadata.items()
                if filename not in deleted_files
            }
            
            # Upload updated metadata
            persistence_manager.s3_client.put_object(
                Bucket=persistence_manager.s3_bucket,
                Key=metadata_key,
                Body=json.dumps(updated_metadata, indent=2),
                ContentType='application/json'
            )
        
        logger.info(f"Deleted {len(deleted_files)} non-training files for user {user_id}, avatar {avatar_id}")
        
        return {
            "status": "success",
            "message": f"Deleted {len(deleted_files)} files not marked for training",
            "deleted_files": deleted_files
        }
        
    except Exception as e:
        logger.error(f"Error deleting non-training files: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to delete non-training files: {str(e)}")
