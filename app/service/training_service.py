
## app/service/training_service.py
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM, TrainingArguments, Trainer
from peft import get_peft_model, LoraConfig, TaskType, PeftModel
from datasets import Dataset
from typing import List, Tuple, Dict, Optional
import json
import tempfile
import os
from core.config import settings

class LoRATrainingService:
    def __init__(self):
        self.base_model_name = settings.base_model_name
        self.tokenizer = None
        self.model = None

    def _load_base_model(self):
        """Load the base model and tokenizer"""
        if self.tokenizer is None:
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model_name)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token

        if self.model is None:
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model_name,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None
            )

    def _prepare_dataset(self, training_files: List[Tuple[str, bytes]]) -> Dataset:
        """Prepare training dataset from files"""
        texts = []
        
        for file_name, file_content in training_files:
            try:
                # Assume text files for simplicity
                content = file_content.decode('utf-8')
                
                if file_name.endswith('.json'):
                    # Handle JSON files
                    data = json.loads(content)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'text' in item:
                                texts.append(item['text'])
                            elif isinstance(item, str):
                                texts.append(item)
                    elif isinstance(data, dict) and 'text' in data:
                        texts.append(data['text'])
                else:
                    # Handle plain text files
                    texts.append(content)
            except Exception as e:
                print(f"Error processing {file_name}: {str(e)}")
                continue

        # Tokenize the texts
        def tokenize_function(examples):
            return self.tokenizer(
                examples["text"],
                truncation=True,
                padding="max_length",
                max_length=512,
                return_tensors="pt"
            )

        dataset = Dataset.from_dict({"text": texts})
        tokenized_dataset = dataset.map(tokenize_function, batched=True)
        
        return tokenized_dataset

    async def train_adapter(self, user_id: str, avatar_id: str, training_files: List[Tuple[str, bytes]], 
                          training_params: Optional[Dict] = None) -> bytes:
        """Train a LoRA adapter"""
        self._load_base_model()
        
        # Prepare dataset
        dataset = self._prepare_dataset(training_files)
        
        if len(dataset) == 0:
            raise Exception("No valid training data found")

        # LoRA configuration
        lora_config = LoraConfig(
            r=16,
            lora_alpha=32,
            target_modules=["q_proj", "v_proj"],
            lora_dropout=0.1,
            bias="none",
            task_type=TaskType.CAUSAL_LM,
        )

        # Apply LoRA to the model
        model = get_peft_model(self.model, lora_config)

        # Training arguments
        default_training_args = {
            "output_dir": "./temp_training_output",
            "overwrite_output_dir": True,
            "num_train_epochs": 3,
            "per_device_train_batch_size": 4,
            "gradient_accumulation_steps": 2,
            "warmup_steps": 10,
            "logging_steps": 10,
            "save_strategy": "epoch",
            "evaluation_strategy": "no",
            "learning_rate": 5e-4,
            "fp16": torch.cuda.is_available(),
            "push_to_hub": False,
        }
        
        # Override with custom params if provided
        if training_params:
            default_training_args.update(training_params)

        training_args = TrainingArguments(**default_training_args)

        # Custom data collator for causal language modeling
        def data_collator(features):
            batch = self.tokenizer.pad(
                features,
                padding=True,
                return_tensors="pt"
            )
            batch["labels"] = batch["input_ids"].clone()
            return batch

        # Create trainer
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            data_collator=data_collator,
        )

        # Train the model
        trainer.train()

        # Save the adapter
        with tempfile.TemporaryDirectory() as temp_dir:
            adapter_path = os.path.join(temp_dir, "adapter")
            model.save_pretrained(adapter_path)
            
            # Read the adapter files and return as bytes
            # For simplicity, we'll save the adapter_model.safetensors file
            adapter_file = os.path.join(adapter_path, "adapter_model.safetensors")
            if os.path.exists(adapter_file):
                with open(adapter_file, "rb") as f:
                    return f.read()
            else:
                raise Exception("Adapter training completed but adapter file not found")
