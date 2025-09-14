# FastAPI LoRA Adapter Management System

## app/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from api import adapters, training_data, persistence

from fastapi.responses import RedirectResponse, Response

app = FastAPI(
    title="LoRA Adapter Management API",
    description="API for managing LoRA adapters with S3 storage",
    version="1.0.0"
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
    return {"status": "healthy"}

# @app.get("/")
# async def root():
#     return {"message": "LoRA Adapter Management API", "version": "1.0.0"}

@app.get("/", tags=["📖 Documentation"])
async def root(request: Request):
    return RedirectResponse(url=f"{request.scope.get('root_path', '')}/docs")
