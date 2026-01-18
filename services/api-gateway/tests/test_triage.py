
import pytest
from httpx import AsyncClient
from src.main import app
from src.models.annotations import Annotation
from uuid import uuid4
from sqlmodel import delete

# Mock dependencies if needed, or use a test DB
# For this environment, we'll try to use the existing DB init but maybe use SQLite for speed if possible,
# or just mock the session. Given it's integration tests, we want real DB if possible.
# But keeping it simple: Mocking might be safer if no DB is running.
# However, the code uses `get_session`. We can override that dependency.

from src.database import get_session
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

# Use an in-memory SQLite for testing to avoid Postgres dependency issues
# But Wait, the code uses `asyncpg` which is Postgres specific. 
# We should probably stick to mocking the session or using a testcontainers Postgres.
# For simplicity in this agent environment, I will MOCK the behavior or use a separate Router test.
# Let's try to override the dependency with a SQLite in-memory if compatible (likely not if PG specific SQL used, but code looks like standard SQLModel).
# Actually, `asyncpg` is for Postgres. `aiosqlite` is for SQLite.
# I will use `aiosqlite` for testing if I can, OR just mock the session functions.
# Mocking return values is safer/faster for logic verification.

from unittest.mock import MagicMock, AsyncMock

@pytest.fixture
def mock_session():
    session = AsyncMock(spec=AsyncSession)
    return session

@pytest.fixture
def client(mock_session):
    # Override dependency
    async def override_get_session():
        yield mock_session
    
    app.dependency_overrides[get_session] = override_get_session
    return AsyncClient(app=app, base_url="http://test")

@pytest.mark.asyncio
async def test_get_triage_queue_empty(client, mock_session):
    # Setup mock
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = []
    mock_session.execute.return_value = result_mock
    
    response = await client.get("/api/triage/queue")
    assert response.status_code == 200
    assert response.json() == []

@pytest.mark.asyncio
async def test_get_triage_queue_items(client, mock_session):
    # Setup mock
    annotation_id = str(uuid4())
    fake_annotation = Annotation(
        id=annotation_id,
        image_path="/tmp/img.jpg",
        label="car",
        is_verified=False,
        camera_id="cam1"
    )
    
    result_mock = MagicMock()
    result_mock.scalars.return_value.all.return_value = [fake_annotation]
    mock_session.execute.return_value = result_mock
    
    response = await client.get("/api/triage/queue")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["id"] == annotation_id
    assert data[0]["current_label"] == "car"

@pytest.mark.asyncio
async def test_validate_annotation_success(client, mock_session):
    annotation_id = str(uuid4())
    fake_annotation = Annotation(
        id=annotation_id,
        image_path="/tmp/img.jpg",
        label="car",
        is_verified=False
    )
    
    # Mock finding the annotation
    mock_session.get.return_value = fake_annotation
    
    payload = {
        "verified": True,
        "correct_label": "truck"
    }
    
    response = await client.post(f"/api/triage/{annotation_id}/validate", json=payload)
    
    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["updated_id"] == annotation_id
    
    # Verify updates
    assert fake_annotation.is_verified is True
    assert fake_annotation.label == "truck"
    # Verify commit called
    mock_session.commit.assert_awaited_once()

@pytest.mark.asyncio
async def test_validate_annotation_not_found(client, mock_session):
    # Mock return None
    mock_session.get.return_value = None
    
    annotation_id = str(uuid4())
    payload = {
        "verified": True,
        "correct_label": "truck"
    }
    
    response = await client.post(f"/api/triage/{annotation_id}/validate", json=payload)
    assert response.status_code == 404
