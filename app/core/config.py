## app/core/config.py
import os
from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # AWS Configuration
    aws_access_key_id: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    aws_secret_access_key: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")
    aws_region: str = os.getenv("AWS_REGION", "us-east-1")
    s3_bucket_name: str = os.getenv("S3_BUCKET_NAME", "lora-adapters-bucket")
    
    # Model Configuration
    base_model_name: str = "meta-llama/Llama-3.2-1B-Instruct"
    
    # API Configuration
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    
    USER_ID: str
    HF_TOKEN: str
    
    class Config:
        env_file = ".env"

settings = Settings()
