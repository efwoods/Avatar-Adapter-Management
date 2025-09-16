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
