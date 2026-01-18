"""Unit tests for model_uploader module."""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Patch settings before importing
with patch.dict(os.environ, {
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "test",
    "MINIO_SECRET_KEY": "test",
    "OUTPUT_DIR": "/tmp/test_output",
}):
    from src.model_uploader import ModelUploader, export_and_upload
    from src.validator import ValidationResult


@pytest.fixture
def mock_minio():
    """Mock MinIO client."""
    with patch("src.model_uploader.Minio") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        mock_client.bucket_exists.return_value = True
        yield mock_client


@pytest.fixture
def uploader(mock_minio, tmp_path):
    """Create ModelUploader with mocked MinIO."""
    with patch("src.model_uploader.settings") as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "test"
        mock_settings.minio_secret_key = "test"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_models = "models"
        mock_settings.output_dir = str(tmp_path)
        mock_settings.training_epochs = 50
        mock_settings.training_batch_size = 16
        mock_settings.training_image_size = 640
        mock_settings.training_device = "cpu"

        up = ModelUploader()
        up.output_dir = tmp_path
        yield up


@pytest.fixture
def validation_result():
    """Create sample validation result."""
    return ValidationResult(
        map50=0.85,
        map50_95=0.65,
        precision=0.9,
        recall=0.8,
        validation_images=100,
        timestamp="2026-01-18T00:00:00",
        improved=True,
    )


class TestModelUploader:
    """Tests for ModelUploader class."""

    def test_get_next_version_no_existing(self, uploader, mock_minio):
        """Test version incrementing with no existing versions."""
        mock_minio.list_objects.return_value = []

        version = uploader.get_next_version()

        assert version == 1

    def test_get_next_version_with_existing(self, uploader, mock_minio):
        """Test version incrementing with existing versions."""
        mock_v1 = MagicMock()
        mock_v1.object_name = "sentinel-yolo/v1/"
        mock_v2 = MagicMock()
        mock_v2.object_name = "sentinel-yolo/v2/"
        mock_minio.list_objects.return_value = [mock_v1, mock_v2]

        version = uploader.get_next_version()

        assert version == 3

    def test_get_next_version_handles_non_numeric(self, uploader, mock_minio):
        """Test version incrementing ignores non-numeric versions."""
        mock_v1 = MagicMock()
        mock_v1.object_name = "sentinel-yolo/v1/"
        mock_latest = MagicMock()
        mock_latest.object_name = "sentinel-yolo/latest/"
        mock_minio.list_objects.return_value = [mock_v1, mock_latest]

        version = uploader.get_next_version()

        assert version == 2

    def test_create_metadata(self, uploader, validation_result):
        """Test metadata creation."""
        metadata = uploader.create_metadata(
            version=1,
            validation_result=validation_result,
            image_count=500,
        )

        assert metadata["version"] == 1
        assert metadata["image_count"] == 500
        assert metadata["map50"] == 0.85
        assert metadata["map50_95"] == 0.65
        assert "training_config" in metadata

    def test_upload_model(self, uploader, mock_minio, tmp_path):
        """Test uploading model files to MinIO."""
        # Create dummy model files
        pt_path = tmp_path / "model.pt"
        onnx_path = tmp_path / "model.onnx"
        pt_path.write_bytes(b"dummy pt content")
        onnx_path.write_bytes(b"dummy onnx content")

        metadata = {"version": 1, "map50": 0.85}

        success = uploader.upload_model(pt_path, onnx_path, metadata, version=1)

        assert success is True
        # Check fput_object was called for pt, onnx, metadata, and latest copies
        assert mock_minio.fput_object.call_count >= 3

    def test_upload_model_creates_bucket(self, uploader, mock_minio, tmp_path):
        """Test that upload creates bucket if it doesn't exist."""
        mock_minio.bucket_exists.return_value = False

        pt_path = tmp_path / "model.pt"
        onnx_path = tmp_path / "model.onnx"
        pt_path.write_bytes(b"dummy")
        onnx_path.write_bytes(b"dummy")

        uploader.upload_model(pt_path, onnx_path, {}, version=1)

        mock_minio.make_bucket.assert_called_once_with("models")


class TestExportAndUpload:
    """Tests for export_and_upload function."""

    def test_export_and_upload_success(self, mock_minio, tmp_path, validation_result):
        """Test full export and upload workflow."""
        with patch("src.model_uploader.settings") as mock_settings:
            mock_settings.minio_endpoint = "localhost:9000"
            mock_settings.minio_access_key = "test"
            mock_settings.minio_secret_key = "test"
            mock_settings.minio_secure = False
            mock_settings.minio_bucket_models = "models"
            mock_settings.output_dir = str(tmp_path)
            mock_settings.training_image_size = 640
            mock_settings.training_epochs = 50
            mock_settings.training_batch_size = 16
            mock_settings.training_device = "cpu"

            mock_minio.list_objects.return_value = []
            mock_minio.bucket_exists.return_value = True

            # Mock model
            mock_model = MagicMock()
            mock_model.save = MagicMock()
            mock_model.export = MagicMock()

            # Create expected files that model.save/export would create
            def mock_save(path):
                Path(path).write_bytes(b"pt")

            def mock_export(*args, **kwargs):
                (tmp_path / "best.onnx").write_bytes(b"onnx")

            mock_model.save.side_effect = mock_save
            mock_model.export.side_effect = mock_export

            uploader = ModelUploader()
            uploader.output_dir = tmp_path

            success, version = export_and_upload(
                mock_model, validation_result, 500, uploader
            )

            assert success is True
            assert version == 1
