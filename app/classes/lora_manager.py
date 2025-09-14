
## app/classes/lora_manager.py
from typing import Optional, Dict, List
from service.s3_service import S3Service
from service.training_service import LoRATrainingService
from db.schema.models import AdapterConfig, TrainingDataMetadata
from datetime import datetime

class LoRAManager:
    def __init__(self):
        self.s3_service = S3Service()
        self.training_service = LoRATrainingService()

    async def create_adapter_config(self, user_id: str, avatar_id: str, adapter_name: str) -> AdapterConfig:
        """Create a new adapter configuration"""
        config = AdapterConfig(
            user_id=user_id,
            avatar_id=avatar_id,
            adapter_name=adapter_name,
            created_at=datetime.utcnow(),
            training_status="not_trained"
        )
        return config

    async def train_adapter(self, user_id: str, avatar_id: str, training_params: Optional[Dict] = None) -> str:
        """Train a LoRA adapter for a specific avatar"""
        try:
            # Download training files
            training_files = await self.s3_service.download_training_files(user_id, avatar_id)
            
            if not training_files:
                raise Exception("No training files found for this avatar")

            # Train the adapter
            adapter_data = await self.training_service.train_adapter(
                user_id, avatar_id, training_files, training_params
            )

            # Upload trained adapter to S3
            adapter_key = await self.s3_service.upload_adapter(user_id, avatar_id, adapter_data)
            
            return adapter_key
        except Exception as e:
            raise Exception(f"Training failed: {str(e)}")

    async def delete_adapter(self, user_id: str, avatar_id: str):
        """Delete an adapter and its training data"""
        # This would delete the adapter from S3
        # Implementation depends on your specific requirements
        pass
