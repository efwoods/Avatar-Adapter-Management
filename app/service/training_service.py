# service/training_service.py

"""
Enhanced Training Service that works with centralized AdapterPersistenceManager
"""

import os
import json
import time
import asyncio
import tempfile
from typing import Dict, Any, List, Optional
from datetime import datetime

from core.logging import logger

class TrainingService:
    """Service for training LoRA adapters - now works with centralized persistence"""
    
    def __init__(self):
        self.default_training_params = {
            "learning_rate": 2e-4,
            "num_epochs": 3,
            "batch_size": 4,
            "gradient_accumulation_steps": 4,
            "warmup_steps": 100,
            "max_seq_length": 512,
            "save_steps": 500,
            "logging_steps": 10
        }
    
    async def train_lora_adapter(self, 
                                adapter_path: str, 
                                training_data_path: str, 
                                training_params: Dict[str, Any]) -> Dict[str, Any]:
        """Train a LoRA adapter with the provided training data"""
        
        start_time = time.time()
        
        try:
            # Validate inputs
            if not os.path.exists(adapter_path):
                raise ValueError(f"Adapter path does not exist: {adapter_path}")
            
            if not os.path.exists(training_data_path):
                raise ValueError(f"Training data path does not exist: {training_data_path}")
            
            # Merge training parameters
            params = self.default_training_params.copy()
            params.update(training_params)
            
            logger.info(f"Starting LoRA adapter training with params: {params}")
            
            # Get training files
            training_files = self._get_training_files(training_data_path)
            if not training_files:
                raise ValueError("No training files found")
            
            logger.info(f"Found {len(training_files)} training files")
            
            # Validate and prepare training data
            prepared_data = await self._prepare_training_data(training_files, params)
            
            # Simulate training process (replace with actual training logic)
            training_result = await self._simulate_training(
                adapter_path, 
                prepared_data, 
                params
            )
            
            end_time = time.time()
            training_duration = end_time - start_time
            
            # Update adapter with training results
            await self._update_adapter_post_training(
                adapter_path, 
                training_result, 
                training_files,
                training_duration
            )
            
            logger.info(f"Training completed in {training_duration:.2f} seconds")
            
            return {
                "success": True,
                "training_duration": training_duration,
                "training_files": [os.path.basename(f) for f in training_files],
                "training_params": params,
                "model_metrics": training_result.get("metrics", {}),
                "final_loss": training_result.get("final_loss", 0.0),
                "steps_completed": training_result.get("steps", 0),
                "message": "Training completed successfully"
            }
            
        except Exception as e:
            logger.error(f"Training failed: {e}")
            
            end_time = time.time()
            training_duration = end_time - start_time
            
            return {
                "success": False,
                "training_duration": training_duration,
                "error": str(e),
                "message": f"Training failed: {str(e)}"
            }

    async def train_with_persistence_manager(self,
                                           persistence_manager,
                                           training_params: Dict[str, Any]) -> Dict[str, Any]:
        """Train adapter using centralized persistence manager"""
        
        with tempfile.TemporaryDirectory() as temp_dir:
            local_adapter_path = os.path.join(temp_dir, "adapters")
            local_training_path = os.path.join(temp_dir, "training_data")
            
            try:
                # Get training files using centralized method
                training_files = await persistence_manager.get_training_files_for_training()
                if not training_files:
                    return {
                        "success": False,
                        "error": "No training files marked for training",
                        "message": "No training data available"
                    }
                
                logger.info(f"Found {len(training_files)} files marked for training")
                
                # Restore adapter using centralized method
                try:
                    await persistence_manager.restore_adapters_from_s3(local_adapter_path)
                    logger.info("Restored existing adapter from S3")
                except Exception as e:
                    if "404" in str(e):
                        logger.info("No existing adapter found, creating new one")
                        await persistence_manager.create_adapter()
                        await persistence_manager.restore_adapters_from_s3(local_adapter_path)
                    else:
                        raise
                
                # Download training files using persistence manager
                os.makedirs(local_training_path, exist_ok=True)
                downloaded_files = []
                
                for filename in training_files:
                    try:
                        # Get download info
                        download_info = await persistence_manager.get_training_file_download_url(filename)
                        
                        # Download file content (you'd implement actual download here)
                        # For now, we'll simulate having the files locally
                        local_file_path = os.path.join(local_training_path, filename)
                        
                        # This is where you'd actually download using the presigned URL
                        # For simulation, create a dummy file
                        with open(local_file_path, 'w') as f:
                            f.write(f"Training data for {filename}")
                        
                        downloaded_files.append(filename)
                        logger.info(f"Downloaded training file: {filename}")
                        
                    except Exception as e:
                        logger.warning(f"Failed to download training file {filename}: {e}")
                
                if not downloaded_files:
                    return {
                        "success": False,
                        "error": "Failed to download any training files",
                        "message": "Could not access training data"
                    }
                
                # Perform training
                training_result = await self.train_lora_adapter(
                    adapter_path=local_adapter_path,
                    training_data_path=local_training_path,
                    training_params=training_params
                )
                
                # Backup trained adapter using centralized method
                if training_result["success"]:
                    backup_metadata = await persistence_manager.backup_adapters_to_s3(local_adapter_path)
                    training_result["backup_metadata"] = backup_metadata
                
                return training_result
                
            except Exception as e:
                logger.error(f"Training with persistence manager failed: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "message": f"Training failed: {str(e)}"
                }
    
    def _get_training_files(self, training_data_path: str) -> List[str]:
        """Get list of training files from directory"""
        training_files = []
        
        if not os.path.exists(training_data_path):
            return training_files
        
        for filename in os.listdir(training_data_path):
            file_path = os.path.join(training_data_path, filename)
            if os.path.isfile(file_path):
                # Filter for text-based training files
                if filename.lower().endswith(('.txt', '.json', '.jsonl', '.csv')):
                    training_files.append(file_path)
        
        return training_files
    
    async def _prepare_training_data(self, training_files: List[str], params: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare and validate training data"""
        
        total_samples = 0
        total_tokens = 0
        file_info = []
        
        for file_path in training_files:
            try:
                file_size = os.path.getsize(file_path)
                
                # Estimate samples and tokens based on file type and size
                if file_path.endswith('.txt'):
                    # Estimate for text files
                    estimated_tokens = file_size // 4  # Rough estimate
                    estimated_samples = max(1, estimated_tokens // params.get('max_seq_length', 512))
                elif file_path.endswith(('.json', '.jsonl')):
                    # Count lines for JSON files
                    with open(file_path, 'r') as f:
                        lines = sum(1 for _ in f)
                    estimated_samples = lines
                    estimated_tokens = lines * params.get('max_seq_length', 512) // 2
                else:
                    estimated_samples = 1
                    estimated_tokens = file_size // 4
                
                file_info.append({
                    "path": file_path,
                    "filename": os.path.basename(file_path),
                    "size": file_size,
                    "estimated_samples": estimated_samples,
                    "estimated_tokens": estimated_tokens
                })
                
                total_samples += estimated_samples
                total_tokens += estimated_tokens
                
            except Exception as e:
                logger.warning(f"Could not process training file {file_path}: {e}")
        
        return {
            "files": file_info,
            "total_samples": total_samples,
            "total_tokens": total_tokens,
            "estimated_steps": max(1, total_samples // params.get('batch_size', 4))
        }
    
    async def _simulate_training(self, 
                                adapter_path: str, 
                                prepared_data: Dict[str, Any], 
                                params: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate the training process (replace with actual training implementation)"""
        
        total_steps = prepared_data["estimated_steps"] * params.get("num_epochs", 3)
        
        logger.info(f"Simulating training for {total_steps} steps")
        
        # Simulate training progress
        metrics_history = []
        
        for step in range(0, total_steps, max(1, total_steps // 10)):
            # Simulate some processing time
            await asyncio.sleep(0.1)
            
            # Simulate decreasing loss
            loss = 2.0 * (1 - step / total_steps) + 0.1
            
            metrics = {
                "step": step,
                "loss": loss,
                "learning_rate": params.get("learning_rate", 2e-4) * (1 - step / total_steps),
                "timestamp": datetime.now().isoformat()
            }
            
            metrics_history.append(metrics)
            
            if step % max(1, total_steps // 5) == 0:
                logger.info(f"Training step {step}/{total_steps}, loss: {loss:.4f}")
        
        # Generate final metrics
        final_metrics = {
            "final_loss": metrics_history[-1]["loss"] if metrics_history else 1.0,
            "steps": total_steps,
            "samples_processed": prepared_data["total_samples"],
            "tokens_processed": prepared_data["total_tokens"],
            "metrics_history": metrics_history[-5:],  # Keep last 5 entries
            "convergence": "good" if metrics_history[-1]["loss"] < 0.5 else "fair" if metrics_history else "poor"
        }
        
        return {
            "metrics": final_metrics,
            "final_loss": final_metrics["final_loss"],
            "steps": total_steps,
            "status": "completed"
        }
    
    async def _update_adapter_post_training(self, 
                                          adapter_path: str, 
                                          training_result: Dict[str, Any],
                                          training_files: List[str],
                                          training_duration: float) -> None:
        """Update adapter files after training"""
        
        # Update adapter config
        config_path = os.path.join(adapter_path, "adapter_config.json")
        
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            # Update training information
            config["status"] = "trained"
            config["last_training"] = datetime.now().isoformat()
            config["training_duration"] = training_duration
            config["training_files_used"] = [os.path.basename(f) for f in training_files]
            
            # Add training metrics
            if "training_metrics" not in config:
                config["training_metrics"] = {}
            
            config["training_metrics"]["latest"] = training_result.get("metrics", {})
            
            # Save updated config
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
        
        # Update adapter model file (simulate trained weights)
        model_path = os.path.join(adapter_path, "adapter_model.bin")
        
        # Create a more substantial model file to simulate trained weights
        model_data = {
            "model_state": "trained",
            "training_timestamp": datetime.now().isoformat(),
            "training_metrics": training_result.get("metrics", {}),
            "model_version": "1.0.0"
        }
        
        # Write binary data (in real implementation, this would be actual model weights)
        with open(model_path, 'wb') as f:
            # Write some dummy data to simulate a trained model
            dummy_weights = json.dumps(model_data).encode() * 100  # Make it larger
            f.write(dummy_weights)
        
        logger.info(f"Updated adapter post-training at {adapter_path}")
    
    async def validate_training_data_with_persistence(self, 
                                                    persistence_manager) -> Dict[str, Any]:
        """Validate training data using persistence manager"""
        
        try:
            # Get list of files marked for training
            training_files = await persistence_manager.get_training_files_for_training()
            
            if not training_files:
                return {
                    "valid": False, 
                    "error": "No files marked for training",
                    "training_files": []
                }
            
            # Get file information
            file_list = await persistence_manager.list_training_files(training_only=True)
            
            validation_results = []
            total_size = 0
            
            for file_info in file_list:
                file_result = {
                    "filename": file_info["filename"],
                    "size": file_info["file_size"],
                    "valid": True,
                    "issues": []
                }
                
                # Check file size
                if file_result["size"] == 0:
                    file_result["valid"] = False
                    file_result["issues"].append("File is empty")
                elif file_result["size"] > 100 * 1024 * 1024:  # 100MB limit
                    file_result["issues"].append("File is very large (>100MB)")
                
                # Basic content type validation
                if file_info["content_type"] and "text" not in file_info["content_type"].lower():
                    file_result["issues"].append("File may not be text-based")
                
                total_size += file_result["size"]
                validation_results.append(file_result)
            
            valid_files = [r for r in validation_results if r["valid"]]
            
            return {
                "valid": len(valid_files) > 0,
                "total_files": len(training_files),
                "valid_files": len(valid_files),
                "total_size": total_size,
                "files": validation_results,
                "summary": {
                    "has_valid_files": len(valid_files) > 0,
                    "total_size_mb": total_size / (1024 * 1024),
                    "recommended_training": len(valid_files) > 0 and total_size > 1024
                }
            }
            
        except Exception as e:
            logger.error(f"Error validating training data: {e}")
            return {
                "valid": False,
                "error": str(e),
                "training_files": []
            }
    
    async def get_training_recommendations_with_persistence(self, 
                                                          persistence_manager,
                                                          current_params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get training parameter recommendations based on data from persistence manager"""
        
        validation = await self.validate_training_data_with_persistence(persistence_manager)
        
        if not validation["valid"]:
            return {
                "recommended": False,
                "reason": "No valid training data found",
                "validation": validation
            }
        
        # Analyze data size and recommend parameters
        total_size_mb = validation["summary"]["total_size_mb"]
        valid_files = validation["valid_files"]
        
        recommendations = self.default_training_params.copy()
        
        # Adjust parameters based on data size
        if total_size_mb < 1:  # Very small dataset
            recommendations.update({
                "num_epochs": 5,
                "learning_rate": 1e-4,
                "batch_size": 2,
                "gradient_accumulation_steps": 8
            })
            difficulty = "small_dataset"
            
        elif total_size_mb < 10:  # Small dataset
            recommendations.update({
                "num_epochs": 4,
                "learning_rate": 2e-4,
                "batch_size": 4,
                "gradient_accumulation_steps": 4
            })
            difficulty = "medium_dataset"
            
        elif total_size_mb < 50:  # Medium dataset
            recommendations.update({
                "num_epochs": 3,
                "learning_rate": 3e-4,
                "batch_size": 8,
                "gradient_accumulation_steps": 2
            })
            difficulty = "large_dataset"
            
        else:  # Large dataset
            recommendations.update({
                "num_epochs": 2,
                "learning_rate": 5e-4,
                "batch_size": 16,
                "gradient_accumulation_steps": 1
            })
            difficulty = "very_large_dataset"
        
        # Estimate training time
        estimated_samples = validation["total_size"] // 100  # Rough estimate
        estimated_steps = (estimated_samples * recommendations["num_epochs"]) // recommendations["batch_size"]
        estimated_time_minutes = max(1, estimated_steps // 100)  # Very rough estimate
        
        return {
            "recommended": True,
            "difficulty": difficulty,
            "recommended_params": recommendations,
            "current_params": current_params or {},
            "estimates": {
                "training_steps": estimated_steps,
                "estimated_time_minutes": estimated_time_minutes,
                "estimated_samples": estimated_samples
            },
            "data_analysis": {
                "total_size_mb": total_size_mb,
                "file_count": valid_files,
                "data_quality": "good" if validation["summary"]["recommended_training"] else "limited"
            },
            "validation": validation
        }