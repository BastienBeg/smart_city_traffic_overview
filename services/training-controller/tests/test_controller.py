"""Unit tests for Training Controller logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

# Patch settings before importing main
with patch.dict('os.environ', {
    'DATABASE_URL': 'postgresql+asyncpg://test:test@localhost/test',
    'TRAINING_THRESHOLD': '50',
    'POLL_INTERVAL_SECONDS': '10'
}):
    from src.main import check_and_trigger_training
    from src.config import settings


@pytest.fixture
def mock_db():
    """Mock database functions."""
    with patch('src.main.get_verified_unused_count') as mock_count, \
         patch('src.main.get_verified_unused_ids') as mock_ids, \
         patch('src.main.mark_annotations_as_used') as mock_mark:
        yield {
            'get_count': mock_count,
            'get_ids': mock_ids,
            'mark_used': mock_mark
        }


@pytest.fixture
def mock_k8s():
    """Mock Kubernetes functions."""
    with patch('src.main.is_training_job_active') as mock_active, \
         patch('src.main.create_training_job') as mock_create:
        yield {
            'is_active': mock_active,
            'create_job': mock_create
        }


@pytest.mark.asyncio
async def test_no_trigger_when_job_running(mock_db, mock_k8s):
    """Test that no new job is triggered when one is already running."""
    mock_k8s['is_active'].return_value = True

    result = await check_and_trigger_training()

    assert result is False
    mock_db['get_count'].assert_not_called()
    mock_k8s['create_job'].assert_not_called()


@pytest.mark.asyncio
async def test_no_trigger_below_threshold(mock_db, mock_k8s):
    """Test that no job is triggered when annotation count is below threshold."""
    mock_k8s['is_active'].return_value = False
    mock_db['get_count'].return_value = 30  # Below threshold of 50

    result = await check_and_trigger_training()

    assert result is False
    mock_k8s['create_job'].assert_not_called()


@pytest.mark.asyncio
async def test_trigger_at_threshold(mock_db, mock_k8s):
    """Test that job is triggered when annotation count reaches threshold."""
    mock_k8s['is_active'].return_value = False
    mock_db['get_count'].return_value = 50  # Exactly at threshold
    mock_db['get_ids'].return_value = [uuid4() for _ in range(50)]
    mock_k8s['create_job'].return_value = "sentinel-training-20260118-120000"
    mock_db['mark_used'].return_value = 50

    result = await check_and_trigger_training()

    assert result is True
    mock_k8s['create_job'].assert_called_once_with(annotation_count=50)
    mock_db['mark_used'].assert_called_once()


@pytest.mark.asyncio
async def test_trigger_above_threshold(mock_db, mock_k8s):
    """Test that job is triggered when annotation count exceeds threshold."""
    mock_k8s['is_active'].return_value = False
    mock_db['get_count'].return_value = 75  # Above threshold
    annotation_ids = [uuid4() for _ in range(75)]
    mock_db['get_ids'].return_value = annotation_ids
    mock_k8s['create_job'].return_value = "sentinel-training-20260118-120000"
    mock_db['mark_used'].return_value = 75

    result = await check_and_trigger_training()

    assert result is True
    mock_k8s['create_job'].assert_called_once_with(annotation_count=75)
    mock_db['mark_used'].assert_called_once_with(annotation_ids)


@pytest.mark.asyncio
async def test_no_mark_on_job_creation_failure(mock_db, mock_k8s):
    """Test that annotations are not marked if job creation fails."""
    mock_k8s['is_active'].return_value = False
    mock_db['get_count'].return_value = 60
    mock_db['get_ids'].return_value = [uuid4() for _ in range(60)]
    mock_k8s['create_job'].return_value = None  # Job creation failed

    result = await check_and_trigger_training()

    assert result is False
    mock_db['mark_used'].assert_not_called()
