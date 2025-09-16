# api/persistence.py

"""
Streamlined Adapter Persistence API router - now only handles backup/restore operations
All CRUD operations are handled through the main adapters and training_data APIs
"""
from fastapi import APIRouter, HTTPException, status

from db.schema.models import (
    AdapterBackupResponse, 
    AdapterListBackupsResponse, 
    AdapterRestoreResponse,
)

from service.persistence_service import get_adapter_persistence_manager
from core.logging import logger

router = APIRouter()

@router.post("/adapters/backup/{avatar_id}",
    response_model=AdapterBackupResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Backup adapters to S3",
    description="Create a backup of LoRA adapter files and upload to S3"
)
async def backup_adapters_to_s3(
    avatar_id: str,
    local_adapter_path: str
):
    """Backup adapter files to S3 - typically used internally by the system"""
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

@router.post("/adapters/restore/{avatar_id}",
    response_model=AdapterRestoreResponse,
    summary="Restore adapters from S3",
    description="Restore LoRA adapter files from S3 backup"
)
async def restore_adapters_from_s3(
    avatar_id: str,
    local_adapter_path: str
):
    """Restore adapter files from S3 - typically used internally by the system"""
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

@router.get("/adapters/backups/{avatar_id}",
    response_model=AdapterListBackupsResponse,
    summary="List available adapter backups",
    description="List all available adapter backups for the avatar"
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

@router.get("/adapters/status/{avatar_id}",
    summary="Get adapter persistence status",
    description="Get the status of S3 connectivity and adapter backup information"
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
        adapter_backup_exists = await manager.adapter_exists()
        
        return {
            "s3_status": s3_status,
            "s3_bucket": manager.s3_bucket,
            "adapter_backup_path": f"s3://{manager.s3_bucket}/{manager._get_s3_adapter_path()}",
            "training_data_backup_path": f"s3://{manager.s3_bucket}/{manager._get_s3_training_data_path()}",
            "adapter_backup_exists": adapter_backup_exists,
            "user_id": manager.user_id,
            "avatar_id": avatar_id
        }
    except Exception as e:
        logger.error(f"Error getting adapter persistence status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get adapter persistence status: {str(e)}"
        )