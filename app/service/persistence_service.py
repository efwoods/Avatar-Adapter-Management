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
