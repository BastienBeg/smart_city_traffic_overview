from sqlmodel import SQLModel, Field
from typing import Optional
from uuid import UUID, uuid4
from datetime import datetime

class Annotation(SQLModel, table=True):
    __tablename__ = "annotations"

    id: UUID = Field(default_factory=uuid4, primary_key=True)
    detection_id: Optional[UUID] = Field(default=None, nullable=True)
    image_path: str
    label: Optional[str] = None
    is_verified: bool = Field(default=False)
    used_for_training: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    camera_id: Optional[str] = None
