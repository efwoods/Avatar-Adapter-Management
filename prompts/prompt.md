Why am I getting this error if I am calling get_adapter that creates the code but I don't get the error if I call the create endpoint to create the adapter in the same way? get_adapter works if I call the create_adapter route first to create an adapter.

2025-09-24 18:18:43,379 - INFO - No existing adapter found for user default, avatar test_avatar_id, creating new one
2025-09-24 18:18:45,201 - WARNING - Some parameters are on the meta device because they were offloaded to the cpu and disk.
2025-09-24 18:18:45,743 - ERROR - Error creating adapter: Cannot copy out of meta tensor; no data!
2025-09-24 18:18:45,744 - ERROR - Error getting adapter: 500: Failed to create adapter: Cannot copy out of meta tensor; no data!
INFO:     172.29.0.4:53486 - "GET /adapters/default/test_avatar_id HTTP/1.1" 500 Internal Server Error


----


@router.post("/{user_id}/{avatar_id}/create")
async def create_adapter(
    user_id: str, 
    avatar_id: str, 
) -> AdapterConfig:
    """Create a new adapter configuration"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Use centralized create method
        result = await persistence_manager.create_adapter()
        
        return AdapterConfig(
            user_id=user_id,
            avatar_id=avatar_id,
            status=result["status"],
            created_at=datetime.now(),
            s3_path=result["s3_path"],
            metadata=result.get("metadata")
        )
            
    except Exception as e:
        logger.error(f"Error creating adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create adapter: {str(e)}")



----


@router.get("/{user_id}/{avatar_id}")
async def get_adapter(user_id: str, avatar_id: str):
    """Get an adapter - returns adapter file for download or creates new one if doesn't exist"""
    try:
        persistence_manager = get_adapter_persistence_manager(avatar_id)
        
        # Check if adapter exists using centralized method
        if not await persistence_manager.adapter_exists():
            logger.info(f"No existing adapter found for user {user_id}, avatar {avatar_id}, creating new one")
            result = await persistence_manager.create_adapter()
        
        # Download adapter backup
        adapter_key = f"{persistence_manager._get_s3_adapter_path()}adapter_backup.zip"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.zip') as temp_file:
            persistence_manager.s3_client.download_file(
                persistence_manager.s3_bucket,
                adapter_key,
                temp_file.name
            )
            
            # Get adapter metadata
            try:
                metadata_key = f"{persistence_manager._get_s3_adapter_path()}backup_metadata.json"
                metadata_obj = persistence_manager.s3_client.get_object(
                    Bucket=persistence_manager.s3_bucket,
                    Key=metadata_key
                )
                metadata = json.loads(metadata_obj['Body'].read().decode('utf-8'))
            except:
                metadata = {}
            
            logger.info(f"Retrieved adapter for user {user_id}, avatar {avatar_id}")
            
            return FileResponse(
                path=temp_file.name,
                filename=f"adapter_{user_id}_{avatar_id}.zip",
                media_type="application/zip",
                headers={
                    "X-Adapter-Metadata": json.dumps(metadata),
                    "X-User-ID": user_id,
                    "X-Avatar-ID": avatar_id
                }
            )
        
    except Exception as e:
        logger.error(f"Error getting adapter: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get adapter: {str(e)}")
----



    async def create_adapter(self, model_name: str = "meta-llama/Llama-3.2-1B-Instruct") -> Dict[str, Any]:
        """Create and save a new LoRA adapter configuration and weights."""
        try:
            adapter_path = self._get_s3_adapter_path()

            # Check if adapter already exists
            if await self.adapter_exists():
                logger.info(f"Adapter already exists for user {self.user_id}, avatar {self.avatar_id}")
                return {
                    "status": "existing",
                    "message": "Adapter already exists",
                    "s3_path": adapter_path
                }

            # Create new adapter locally then upload
            with tempfile.TemporaryDirectory() as temp_dir:
                local_adapter_path = os.path.join(temp_dir, "adapters")
                os.makedirs(local_adapter_path, exist_ok=True)

                # Initialize adapter metadata
                adapter_config = {
                    "avatar_id": self.avatar_id,
                    "created_at": datetime.now().isoformat(),
                    "version": "1.0.0",
                    "status": "untrained",
                    "training_history": [],
                    "model_name": model_name
                }

                # Save adapter metadata
                config_path = os.path.join(local_adapter_path, "adapter_metadata.json")
                with open(config_path, "w") as f:
                    json.dump(adapter_config, f, indent=2)

                # Load base model and tokenizer
                model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    device_map="auto", 
                    token=self.HF_TOKEN
                )
                tokenizer = AutoTokenizer.from_pretrained(model_name, token=self.HF_TOKEN)
                tokenizer.pad_token = tokenizer.eos_token

                # Prepare model for training
                model = prepare_model_for_kbit_training(model)

                # Create LoRA config
                lora_config = LoraConfig(
                    r=16,
                    lora_alpha=32,
                    target_modules=["q_proj", "v_proj"],
                    lora_dropout=0.1,
                    bias="none",
                    task_type="CAUSAL_LM"
                )

                # Attach and initialize LoRA adapter
                peft_model = get_peft_model(model, lora_config)

                # Save untrained adapter
                peft_model.save_pretrained(local_adapter_path)

                # Backup to S3
                backup_metadata = await self.backup_adapters_to_s3(local_adapter_path)

                logger.info(f"Created and backed up new adapter for user {self.user_id}, avatar {self.avatar_id}")

                return {
                    "status": "created",
                    "message": "Adapter created successfully",
                    "s3_path": adapter_path,
                    "metadata": backup_metadata
                }

        except Exception as e:
            logger.error(f"Error creating adapter: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to create adapter: {str(e)}")

