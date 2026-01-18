from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from uuid import UUID
from datetime import datetime

from src.database import get_session
from src.models.annotations import Annotation
from services.common_lib.schemas.triage import TriageItem, ValidationRequest, ValidationResponse

router = APIRouter(prefix="/api/triage", tags=["triage"])

@router.get("/queue", response_model=List[TriageItem])
async def get_triage_queue(
    limit: int = 10,
    session: AsyncSession = Depends(get_session)
):
    """
    Get a batch of unverified detections for triage.
    """
    statement = select(Annotation).where(Annotation.is_verified == False).limit(limit)
    result = await session.execute(statement)
    annotations = result.scalars().all()
    
    return [
        TriageItem(
            id=ann.id,
            image_path=ann.image_path,
            current_label=ann.label,
            confidence=None, # Storing confidence in annotation table might be useful later, for now None or fetch from detection relation
            created_at=ann.created_at,
            camera_id=ann.camera_id
        ) for ann in annotations
    ]

@router.post("/{id}/validate", response_model=ValidationResponse)
async def validate_annotation(
    id: UUID,
    validation: ValidationRequest,
    session: AsyncSession = Depends(get_session)
):
    """
    Submit human validation for a detection.
    """
    annotation = await session.get(Annotation, id)
    if not annotation:
        raise HTTPException(status_code=404, detail="Annotation not found")
    
    annotation.is_verified = True
    annotation.label = validation.correct_label
    annotation.updated_at = datetime.utcnow()
    
    session.add(annotation)
    await session.commit()
    await session.refresh(annotation)
    
    return ValidationResponse(success=True, updated_id=annotation.id)
