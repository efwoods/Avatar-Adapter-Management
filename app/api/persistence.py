# api/persistence.py

"""
Adapter Persistence API router for S3 backup and restore operations
Modified to support dynamic user ID from environment variable
"""
from fastapi import APIRouter, HTTPException, Depends, status

from db.schema.models import (
    AdapterBackupResponse, 
    AdapterListBackupsResponse, 
    AdapterRestoreResponse,
)

from service.persistence_service import get_adapter_persistence_manager
from core.logging import logger

router = APIRouter()

# Routes - all using the dependency from service.py
@router.post("/adapters/backup/{avatar_id}",
    response_model=AdapterBackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Backup adapters to S3",
    description="Create a backup of LoRA adapter files and upload to S3 (user_id from environment)"
)
async def backup_adapters_to_s3(
    avatar_id: str,
    local_adapter_path: str
):
    """Backup adapter files to S3"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        backup_info = await manager.backup_adapters_to_s3(local_adapter_path)
        
        return AdapterBackupResponse(
            success=True,
            message=f"Successfully backed up adapters for user {manager.user_id}, avatar {avatar_id}",
            backup_info=backup_info
        )
    except Exception as e:
        logger.error(f"Error backing up adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backup adapters: {str(e)}"
        )

@router.post("/adapters/training-data/backup/{avatar_id}",
    response_model=AdapterBackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Backup training data to S3",
    description="Create a backup of adapter training data and upload to S3 (user_id from environment)"
)
async def backup_training_data_to_s3(
    avatar_id: str,
    local_training_data_path: str
):
    """Backup training data to S3"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        backup_info = await manager.backup_training_data_to_s3(local_training_data_path)
        
        return AdapterBackupResponse(
            success=True,
            message=f"Successfully backed up training data for user {manager.user_id}, avatar {avatar_id}",
            backup_info=backup_info
        )
    except Exception as e:
        logger.error(f"Error backing up training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to backup training data: {str(e)}"
        )

@router.post("/adapters/restore/{avatar_id}",
    response_model=AdapterRestoreResponse,
    summary="Restore adapters from S3",
    description="Restore LoRA adapter files from S3 backup (user_id from environment)"
)
async def restore_adapters_from_s3(
    avatar_id: str,
    local_adapter_path: str
):
    """Restore adapter files from S3"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        await manager.restore_adapters_from_s3(local_adapter_path)
        
        return AdapterRestoreResponse(
            success=True,
            message=f"Successfully restored adapters for user {manager.user_id}, avatar {avatar_id}"
        )
    except Exception as e:
        logger.error(f"Error restoring adapters: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore adapters: {str(e)}"
        )

@router.post("/adapters/training-data/restore/{avatar_id}",
    response_model=AdapterRestoreResponse,
    summary="Restore training data from S3",
    description="Restore adapter training data from S3 backup (user_id from environment)"
)
async def restore_training_data_from_s3(
    avatar_id: str,
    local_training_data_path: str
):
    """Restore training data from S3"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        await manager.restore_training_data_from_s3(local_training_data_path)
        
        return AdapterRestoreResponse(
            success=True,
            message=f"Successfully restored training data for user {manager.user_id}, avatar {avatar_id}"
        )
    except Exception as e:
        logger.error(f"Error restoring training data: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restore training data: {str(e)}"
        )

@router.get("/adapters/backups/{avatar_id}",
    response_model=AdapterListBackupsResponse,
    summary="List available adapter backups",
    description="List all available adapter and training data backups for the avatar (user_id from environment)"
)
async def list_adapter_backups(
    avatar_id: str
):
    """List available adapter backups"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
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

@router.delete("/adapters/backup/{avatar_id}",
    summary="Delete adapter backup from S3",
    description="Delete adapter backup from S3 (user_id from environment)"
)
async def delete_adapter_backup(
    avatar_id: str,
    backup_type: str = "adapters"  # "adapters" or "training_data"
):
    """Delete adapter backup from S3"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        
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
            "message": f"Successfully deleted {backup_type} backup for user {manager.user_id}, avatar {avatar_id}"
        }
    except Exception as e:
        logger.error(f"Error deleting adapter backup: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete adapter backup: {str(e)}"
        )

@router.get("/adapters/status/{avatar_id}",
    summary="Get adapter persistence status",
    description="Get the status of S3 connectivity and adapter backup information (user_id from environment)"
)
async def get_adapter_persistence_status(
    avatar_id: str
):
    """Get adapter persistence status"""
    try:
        
        manager = get_adapter_persistence_manager(avatar_id)
        
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
            "user_id": manager.user_id,
            "avatar_id": avatar_id
        }
    except Exception as e:
        logger.error(f"Error getting adapter persistence status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get adapter persistence status: {str(e)}"
        )