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