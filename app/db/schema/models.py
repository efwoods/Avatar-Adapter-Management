
## app/db/schema/models.py
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
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


### Persistence.py Models

# Response models
class AdapterBackupResponse(BaseModel):
    success: bool
    message: str
    backup_info: Dict[str, Any]

class AdapterRestoreResponse(BaseModel):
    success: bool
    message: str

class AdapterListBackupsResponse(BaseModel):
    backups: List[Dict[str, Any]]
    count: int


###
# Add these model definitions to your existing db/schema/models.py file

from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

class AdapterConfig(BaseModel):
    """Configuration for LoRA adapter"""
    user_id: str
    avatar_id: str
    adapter_name: str
    status: str  # "created", "training", "trained", "existing", "untrained", "training_failed"
    created_at: datetime
    s3_path: str
    metadata: Optional[Dict[str, Any]] = None
    last_updated: Optional[datetime] = None

class TrainingRequest(BaseModel):
    """Request model for training operations"""
    user_id: str
    avatar_id: str
    training_params: Optional[Dict[str, Any]] = None
    force_retrain: bool = False

class S3UploadRequest(BaseModel):
    """Request model for S3 uploads"""
    user_id: str
    avatar_id: str
    file_path: str
    content_type: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

class MetadataUpdate(BaseModel):
    """Request model for updating metadata"""
    use_for_training: bool

class TrainingDataMetadata(BaseModel):
    """Metadata for training data files"""
    filename: str
    use_for_training: bool
    file_size: int
    last_modified: datetime
    content_type: str
    upload_timestamp: Optional[str] = None
    s3_key: str

class AdapterStatus(BaseModel):
    """Status information for an adapter"""
    user_id: str
    avatar_id: str
    exists: bool
    status: str
    last_training: Optional[datetime] = None
    training_files_count: int = 0
    file_size: Optional[int] = None
    created_at: Optional[datetime] = None

class TrainingResult(BaseModel):
    """Result of a training operation"""
    status: str
    message: str
    training_files_used: List[str]
    training_duration: Optional[float] = None
    model_metrics: Optional[Dict[str, float]] = None
    backup_metadata: Optional[Dict[str, Any]] = None

class FileUploadResponse(BaseModel):
    """Response for file upload operations"""
    status: str
    message: str
    filename: str
    file_size: int
    s3_key: str
    use_for_training: bool

class DeleteResponse(BaseModel):
    """Response for delete operations"""
    status: str
    message: str
    deleted_items: List[str]
    deleted_count: int

class DownloadResponse(BaseModel):
    """Response for download operations"""
    status: str
    filename: str
    download_url: str
    expires_in: int
    file_size: int
    last_modified: str