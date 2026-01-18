"""Unit tests for Kubernetes Job manager."""

import pytest
from unittest.mock import MagicMock, patch
from kubernetes.client.rest import ApiException


# Patch settings and k8s config before importing
with patch.dict('os.environ', {
    'K8S_NAMESPACE': 'test-namespace',
    'TRAINING_IMAGE': 'alpine:test'
}):
    with patch('kubernetes.config.load_incluster_config', side_effect=Exception):
        with patch('kubernetes.config.load_kube_config'):
            from src.k8s_manager import (
                is_training_job_active,
                create_training_job,
                TRAINING_JOB_LABEL
            )


@pytest.fixture
def mock_batch_api():
    """Mock Kubernetes BatchV1Api."""
    with patch('src.k8s_manager._get_k8s_client') as mock:
        api = MagicMock()
        mock.return_value = api
        yield api


def test_no_active_jobs(mock_batch_api):
    """Test detection when no training jobs are running."""
    mock_batch_api.list_namespaced_job.return_value.items = []

    result = is_training_job_active()

    assert result is False
    mock_batch_api.list_namespaced_job.assert_called_once()


def test_active_job_detected(mock_batch_api):
    """Test detection of an active training job."""
    mock_job = MagicMock()
    mock_job.metadata.name = "sentinel-training-20260118-120000"
    mock_job.status.active = 1
    mock_job.status.succeeded = None
    mock_job.status.failed = None

    mock_batch_api.list_namespaced_job.return_value.items = [mock_job]

    result = is_training_job_active()

    assert result is True


def test_completed_job_not_active(mock_batch_api):
    """Test that completed jobs are not considered active."""
    mock_job = MagicMock()
    mock_job.metadata.name = "sentinel-training-old"
    mock_job.status.active = None
    mock_job.status.succeeded = 1
    mock_job.status.failed = None

    mock_batch_api.list_namespaced_job.return_value.items = [mock_job]

    result = is_training_job_active()

    assert result is False


def test_api_error_assumes_active(mock_batch_api):
    """Test that API errors result in assuming a job is active (safe behavior)."""
    mock_batch_api.list_namespaced_job.side_effect = ApiException("API error")

    result = is_training_job_active()

    # Should return True to be safe
    assert result is True


def test_create_training_job_success(mock_batch_api):
    """Test successful job creation."""
    mock_batch_api.create_namespaced_job.return_value = MagicMock()

    result = create_training_job(annotation_count=50)

    assert result is not None
    assert result.startswith("sentinel-training-")
    mock_batch_api.create_namespaced_job.assert_called_once()


def test_create_training_job_failure(mock_batch_api):
    """Test job creation failure."""
    mock_batch_api.create_namespaced_job.side_effect = ApiException("Failed")

    result = create_training_job(annotation_count=50)

    assert result is None
