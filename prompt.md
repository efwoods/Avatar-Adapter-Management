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

## Directory Structure

.
├── .github
│   └── workflows
│       └── deploy.yml # This is used in the github actions to build the docker image and save it in docker hub. This github actions will then use the docker hub image in google cloud run and run the container in google cloud run.
├── .gitignore
├── app
│   ├── api # This holds api routes. Each route is included in main.py
│   │   └── __init__.py
│   ├── classes # These hold class definitions
│   │   └── __init__.py 
│   ├── core # This holds settings and configuration options
│   │   └── __init__.py
│   ├── db # This holds the database instance and class
│   │   ├── __init__.py
│   │   └── schema # this holds pydantic models
│   │       └── __init__.py
│   ├── __init__.py
│   ├── models # This holds huggingface models
│   │   └── __init__.py
│   └── service # This holds utility functions and function definitions used in the other files
│       └── __init__.py
├── docker-compose.yml # This is used to hot-reload and local dev testing (Dockerfile.dev)
├── Dockerfile.dev # This is used for the local dev testing image
├── Dockerfile # This is used for the production image in the google deploy script
├── prompt.md
├── README.md
└── requirements.txt

## S3_persistence Structure:
This is the S3 Persistence Structure
users/{user_id}/
├── vectorstore/                   # User-level vectorstore (chroma_db)
├── avatars/{avatar_id}/
│   ├── vectorstore_data/          # Avatar-specific context data (preprocessed);
|   ├── vectorstore_metadata/ There is a meta datafile dictionary of booleans determining if each vectorstore_data object is used for training
│   ├── adapters/                  # QLoRA adapter files (the actual Adapter is stored here)
│   ├── adapters/training_data/    # Training data for fine-tuning (preprocessed for the LoRA Adapter); 
│   ├── adapters/metadata/    # There is a meta datafile dictionary of booleans determining if each adapters/training_data object is used for training.
|   ├── media/audio/               # Processed audio (audio only of the target avatar speaking)
|   ├── media/original             # Unprocessed, original media for a specific avatar (audio/video/images/documents)
|   ├── media/original/video               # Original video 
|   ├── media/original/text                # Original text documents 
|   ├── media/original/audio               # Original audio  
|   └── media/original/images
|── image/                         # User-level personal image
|── *{other_potential_user_level_folders}  # Other potential user-level folders such as billing & account information
