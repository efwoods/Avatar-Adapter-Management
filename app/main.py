# app/main.py

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse, Response
from contextlib import asynccontextmanager

from core.config import settings
# Import your existing routers
from api import adapters, training_data, persistence
from core.logging import logger
from service.persistence_service import (
    initialize_s3_client,
    get_s3_client,
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Application startup - Initializing S3 and settings")
    
    # Validate required settings first
    user_id = settings.USER_ID
    if not user_id:
        logger.error("USER_ID setting is required")
        raise RuntimeError("USER_ID setting is required")

    logger.info(f"Starting Adapter Management API for user: {user_id}")
    logger.info(f"App: LoRA Adapter Management API v1.0.0")
    
    if not settings.s3_bucket_name:
        logger.error("S3_BUCKET_NAME is required")
        raise RuntimeError("S3_BUCKET_NAME environment variable is required")
    
    # Initialize S3 client using the service function
    try:
        s3_client = initialize_s3_client()
        logger.info(f"Adapter persistence configured for user: {user_id}")
        logger.info(f"S3 bucket: {settings.s3_bucket_name}")
    except Exception as e:
        logger.error(f"Failed to initialize S3 client during startup: {e}")
        raise RuntimeError(f"S3 initialization failed: {e}")
        
    yield
    
    # Shutdown
    logger.info("Application shutdown - Cleaning up resources")
    # The s3_client_instance will be cleaned up automatically
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
        except Exception as e:
            s3_status = f"disconnected: {str(e)}"
        
        return {
            "status": "healthy",
            "s3_status": s3_status,
            "s3_bucket": settings.s3_bucket_name,
            "user_id": settings.USER_ID
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "error": str(e)
        }

@app.get("/", tags=["📖 Documentation"])
async def root(request: Request):
    return RedirectResponse(url=f"{request.scope.get('root_path', '')}/docs")
