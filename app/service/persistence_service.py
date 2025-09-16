# service/persistence_service.py

import boto3
from fastapi import HTTPException
from classes.AdapterPersistenceManager import AdapterPersistenceManager
from core.logging import logger
from core.config import settings

# Global variables to hold managers
s3_client_instance = None

def initialize_s3_client():
    """Initialize S3 client - called during app startup"""
    global s3_client_instance
    
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
        return s3_client
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        raise RuntimeError(f"S3 initialization failed: {e}")

def get_s3_client():
    """Dependency function that returns the global S3 client instance"""
    global s3_client_instance
    
    if s3_client_instance is None:
        # Try to initialize if not already done
        logger.warning("S3 client not initialized, attempting to initialize now")
        try:
            return initialize_s3_client()
        except Exception as e:
            logger.error(f"Failed to initialize S3 client on demand: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"S3 client not initialized: {str(e)}"
            )
    
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
    
    # Get S3 client with proper error handling
    s3_client = get_s3_client()
    
    return AdapterPersistenceManager(
        s3_client=s3_client,
        settings=settings,
        user_id=user_id,
        avatar_id=avatar_id
    )