from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class TriageItem(BaseModel):
    id: UUID
    image_path: str
    current_label: Optional[str]
    confidence: Optional[float]
    created_at: datetime
    camera_id: Optional[str]

class ValidationRequest(BaseModel):
    verified: bool
    correct_label: str

class ValidationResponse(BaseModel):
    success: bool
    updated_id: UUID
