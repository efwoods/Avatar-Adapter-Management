# Purpose:
This api endpoint is used to manage lora configs and train and update the config. This is cost effective rather than having any updates occur on a gpu inference endpoint. 


# Features: 
I am using a base model of https://huggingface.co/meta-llama/Llama-3.2-1B-Instruct
I am storing the adapters per user per avatar in s3 storage.
I need a fast api to handle the creation, deletion, training of LoRA adapters.
I need a fast api to handle the s3 upload, s3 deletion, s3 update, and s3 listing of LoRA adapters training data.
When I upload an s3 training_data object, I need associated metadata that is a boolean flag of whether or not this is to be used for fine-tuning. 
I need to be able to update whether or not an s3 training_data is used for fine-tuning. 
I need to be able to download all s3 objects that are used for fine-tuning. 
I need to be able to train using objects that are downloaded for fine-tuning. 
I need to be able to save the adapters after they are trained (overwrite the adapter in s3 storage).
I need to be able to delete all objects that are not used for model fine-tuning. 
All objects are set to be used for model fine-tuning as a default value. 
I need to be able to list every document that is available but only used for training.
I need to be able to list every document that is available.
I need to be able to list every document that is available not not used for training.
I need to be able to run this fast api as a docker container with a docker-compose.yml that hot-reloads for development purposes.
I need to download data that is specific to the avatar to train the avatar (adapter training data is stored in avatar/{avatar_id}/adapters/training_data/*)

This is the s3 persistence structure:

# S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed)
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter)
|   └── media/                     # Unprocessed media for a specific avatar (audio/video/images/documents)
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information



# Code Tree:
.
├── app
│   ├── api
│   ├── core
│   ├── main.py
│   └── service
├── docker-compose.yml
├── Dockerfile.dev
├── LICENSE
├── prompt.md
└── README.md
