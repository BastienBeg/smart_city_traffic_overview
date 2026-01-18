"""Database module for Training Controller service.

Handles connection to PostgreSQL and queries for verified annotations.
"""

import logging
from typing import List
from uuid import UUID

from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel, Field

from src.config import settings

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(settings.database_url, echo=False, future=True)

# Async session factory
async_session_factory = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


class Annotation(SQLModel, table=True):
    """Mirror of the Annotation model from api-gateway for querying."""

    __tablename__ = "annotations"

    id: UUID = Field(primary_key=True)
    image_path: str
    label: str | None = None
    is_verified: bool = Field(default=False)
    used_for_training: bool = Field(default=False)


async def get_verified_unused_count() -> int:
    """Get count of verified annotations not yet used for training.

    Returns:
        int: Number of annotations where is_verified=True AND used_for_training=False.
    """
    async with async_session_factory() as session:
        result = await session.execute(
            select(func.count(Annotation.id)).where(
                Annotation.is_verified == True,  # noqa: E712
                Annotation.used_for_training == False  # noqa: E712
            )
        )
        count = result.scalar_one()
        logger.info(f"Found {count} verified annotations not used for training")
        return count


async def get_verified_unused_ids() -> List[UUID]:
    """Get IDs of verified annotations not yet used for training.

    Returns:
        List[UUID]: List of annotation IDs ready for training.
    """
    async with async_session_factory() as session:
        result = await session.execute(
            select(Annotation.id).where(
                Annotation.is_verified == True,  # noqa: E712
                Annotation.used_for_training == False  # noqa: E712
            )
        )
        ids = result.scalars().all()
        return list(ids)


async def mark_annotations_as_used(annotation_ids: List[UUID]) -> int:
    """Mark annotations as used for training.

    Args:
        annotation_ids: List of annotation UUIDs to mark as used.

    Returns:
        int: Number of annotations updated.
    """
    if not annotation_ids:
        return 0

    async with async_session_factory() as session:
        result = await session.execute(
            update(Annotation)
            .where(Annotation.id.in_(annotation_ids))
            .values(used_for_training=True)
        )
        await session.commit()
        updated_count = result.rowcount
        logger.info(f"Marked {updated_count} annotations as used for training")
        return updated_count
