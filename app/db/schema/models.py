
## app/db/schema/models.py
from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime

class TrainingDataMetadata(BaseModel):
    file_key: str
    use_for_training: bool = True
    upload_timestamp: datetime
    file_size: Optional[int] = None
    content_type: Optional[str] = None

class AdapterConfig(BaseModel):
    user_id: str
    avatar_id: str
    adapter_name: str
    created_at: datetime
    last_trained: Optional[datetime] = None
    training_status: str = "not_trained"  # not_trained, training, completed, failed

class TrainingRequest(BaseModel):
    user_id: str
    avatar_id: str
    training_params: Optional[Dict] = None

class S3UploadRequest(BaseModel):
    user_id: str
    avatar_id: str
    file_name: str
    use_for_training: bool = True

class MetadataUpdate(BaseModel):
    use_for_training: bool
