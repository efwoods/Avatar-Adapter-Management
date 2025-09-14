## app/api/adapters.py
from fastapi import APIRouter, HTTPException
from typing import Optional, Dict
from classes.lora_manager import LoRAManager
from db.schema.models import TrainingRequest, AdapterConfig

router = APIRouter()
lora_manager = LoRAManager()

@router.post("/{user_id}/{avatar_id}/create")
async def create_adapter(user_id: str, avatar_id: str, adapter_name: str = "default") -> AdapterConfig:
    """Create a new adapter configuration"""
    try:
        config = await lora_manager.create_adapter_config(user_id, avatar_id, adapter_name)
        return config
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{user_id}/{avatar_id}/train")
async def train_adapter(user_id: str, avatar_id: str, training_params: Optional[Dict] = None):
    """Train a LoRA adapter"""
    try:
        adapter_key = await lora_manager.train_adapter(user_id, avatar_id, training_params)
        return {
            "message": "Adapter training completed successfully",
            "adapter_key": adapter_key
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{user_id}/{avatar_id}")
async def delete_adapter(user_id: str, avatar_id: str):
    """Delete an adapter"""
    try:
        await lora_manager.delete_adapter(user_id, avatar_id)
        return {"message": "Adapter deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
