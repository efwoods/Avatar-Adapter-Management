"""
LoRA Manager for handling LoRA adapter operations
"""

import os
import json
import tempfile
from typing import Dict, Any, Optional, List
from datetime import datetime

from core.logging import logger

class LoRAManager:
    """Manages LoRA adapter creation, training, and deployment"""
    
    def __init__(self):
        self.default_config = {
            "target_modules": ["q_proj", "v_proj", "k_proj", "o_proj"],
            "r": 16,
            "lora_alpha": 32,
            "lora_dropout": 0.1,
            "bias": "none",
            "task_type": "CAUSAL_LM"
        }
    
    def create_adapter_config(self, 
                            user_id: str, 
                            avatar_id: str, 
                            adapter_name: str = "default",
                            custom_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Create a new adapter configuration"""
        
        config = self.default_config.copy()
        if custom_config:
            config.update(custom_config)
        
        adapter_config = {
            "adapter_name": adapter_name,
            "user_id": user_id,
            "avatar_id": avatar_id,
            "created_at": datetime.now().isoformat(),
            "version": "1.0.0",
            "status": "untrained",
            "lora_config": config,
            "training_history": [],
            "model_info": {
                "base_model": "microsoft/DialoGPT-medium",  # Default base model
                "model_type": "gpt2"
            }
        }
        
        logger.info(f"Created adapter config for {user_id}/{avatar_id}")
        return adapter_config
    
    def validate_adapter_structure(self, adapter_path: str) -> bool:
        """Validate that an adapter has the correct structure"""
        required_files = [
            "adapter_config.json",
            "adapter_model.bin"
        ]
        
        if not os.path.exists(adapter_path):
            return False
        
        for required_file in required_files:
            file_path = os.path.join(adapter_path, required_file)
            if not os.path.exists(file_path):
                logger.warning(f"Missing required file: {required_file}")
                return False
        
        return True
    
    def create_empty_adapter(self, adapter_path: str, config: Dict[str, Any]) -> None:
        """Create an empty adapter structure"""
        os.makedirs(adapter_path, exist_ok=True)
        
        # Create adapter config file
        config_path = os.path.join(adapter_path, "adapter_config.json")
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Create empty adapter model file (placeholder)
        model_path = os.path.join(adapter_path, "adapter_model.bin")
        with open(model_path, 'wb') as f:
            f.write(b"")  # Empty placeholder
        
        # Create LoRA specific config
        lora_config_path = os.path.join(adapter_path, "adapter_config.json")
        lora_config = {
            "peft_type": "LORA",
            "auto_mapping": None,
            "base_model_name_or_path": config.get("model_info", {}).get("base_model", ""),
            "bias": config["lora_config"]["bias"],
            "fan_in_fan_out": False,
            "inference_mode": True,
            "init_lora_weights": True,
            "layers_pattern": None,
            "layers_to_transform": None,
            "lora_alpha": config["lora_config"]["lora_alpha"],
            "lora_dropout": config["lora_config"]["lora_dropout"],
            "modules_to_save": None,
            "r": config["lora_config"]["r"],
            "revision": None,
            "target_modules": config["lora_config"]["target_modules"],
            "task_type": config["lora_config"]["task_type"]
        }
        
        with open(lora_config_path, 'w') as f:
            json.dump(lora_config, f, indent=2)
        
        logger.info(f"Created empty adapter structure at {adapter_path}")
    
    def load_adapter_config(self, adapter_path: str) -> Optional[Dict[str, Any]]:
        """Load adapter configuration from path"""
        config_path = os.path.join(adapter_path, "adapter_config.json")
        
        if not os.path.exists(config_path):
            logger.warning(f"No adapter config found at {config_path}")
            return None
        
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            return config
        except Exception as e:
            logger.error(f"Error loading adapter config: {e}")
            return None
    
    def update_adapter_status(self, adapter_path: str, status: str, additional_info: Optional[Dict] = None) -> bool:
        """Update adapter status in config"""
        config = self.load_adapter_config(adapter_path)
        if not config:
            return False
        
        config["status"] = status
        config["last_updated"] = datetime.now().isoformat()
        
        if additional_info:
            config.update(additional_info)
        
        config_path = os.path.join(adapter_path, "adapter_config.json")
        try:
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error updating adapter config: {e}")
            return False
    
    def get_adapter_info(self, adapter_path: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive adapter information"""
        if not self.validate_adapter_structure(adapter_path):
            return None
        
        config = self.load_adapter_config(adapter_path)
        if not config:
            return None
        
        # Get file sizes
        model_path = os.path.join(adapter_path, "adapter_model.bin")
        model_size = os.path.getsize(model_path) if os.path.exists(model_path) else 0
        
        # Count training files if available
        training_history = config.get("training_history", [])
        
        return {
            "config": config,
            "model_size_bytes": model_size,
            "is_trained": config.get("status") == "trained",
            "training_count": len(training_history),
            "last_training": training_history[-1].get("timestamp") if training_history else None,
            "structure_valid": True
        }
    
    def prepare_for_training(self, adapter_path: str, training_files: List[str]) -> Dict[str, Any]:
        """Prepare adapter for training"""
        config = self.load_adapter_config(adapter_path)
        if not config:
            raise ValueError("Invalid adapter configuration")
        
        # Update status
        self.update_adapter_status(adapter_path, "preparing_for_training", {
            "training_files": training_files,
            "preparation_timestamp": datetime.now().isoformat()
        })
        
        return {
            "adapter_path": adapter_path,
            "config": config,
            "training_files": training_files,
            "status": "ready_for_training"
        }
    
    def finalize_training(self, adapter_path: str, training_result: Dict[str, Any]) -> Dict[str, Any]:
        """Finalize adapter after training"""
        config = self.load_adapter_config(adapter_path)
        if not config:
            raise ValueError("Invalid adapter configuration")
        
        # Add to training history
        training_entry = {
            "timestamp": datetime.now().isoformat(),
            "result": training_result,
            "files_used": training_result.get("training_files", []),
            "training_params": training_result.get("training_params", {})
        }
        
        if "training_history" not in config:
            config["training_history"] = []
        config["training_history"].append(training_entry)
        
        # Update status
        final_status = "trained" if training_result.get("success", False) else "training_failed"
        
        additional_info = {
            "last_training": training_entry["timestamp"],
            "training_result": training_result
        }
        
        self.update_adapter_status(adapter_path, final_status, additional_info)
        
        return {
            "status": final_status,
            "training_entry": training_entry,
            "adapter_path": adapter_path
        }