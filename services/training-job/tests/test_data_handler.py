"""Unit tests for data_handler module."""

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
    "DATA_DIR": "/tmp/test_data",
}):
    from src.data_handler import DataHandler, prepare_training_data


@pytest.fixture
def mock_minio():
    """Mock MinIO client."""
    with patch("src.data_handler.Minio") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def data_handler(mock_minio, tmp_path):
    """Create DataHandler with mocked MinIO and temp directory."""
    with patch("src.data_handler.settings") as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "test"
        mock_settings.minio_secret_key = "test"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_datasets = "datasets"
        mock_settings.data_dir = str(tmp_path / "data")
        mock_settings.validation_split = 0.2

        handler = DataHandler()
        handler.data_dir = tmp_path / "data"
        yield handler


class TestDataHandler:
    """Tests for DataHandler class."""

    def test_prepare_data_directory(self, data_handler):
        """Test that prepare_data_directory creates correct structure."""
        result = data_handler.prepare_data_directory()

        assert result.exists()
        assert (result / "images" / "train").exists()
        assert (result / "images" / "val").exists()
        assert (result / "labels" / "train").exists()
        assert (result / "labels" / "val").exists()

    def test_download_dataset(self, data_handler, mock_minio, tmp_path):
        """Test downloading images from MinIO."""
        # Setup mock
        mock_obj = MagicMock()
        mock_obj.object_name = "training/image1.jpg"
        mock_minio.list_objects.return_value = [mock_obj]

        # Prepare directory
        data_handler.prepare_data_directory()

        # Mock fget_object to create the file
        def create_file(bucket, obj_name, local_path):
            Path(local_path).touch()

        mock_minio.fget_object.side_effect = create_file

        # Test
        count = data_handler.download_dataset()

        assert count == 1
        mock_minio.list_objects.assert_called_once()
        mock_minio.fget_object.assert_called_once()

    def test_download_annotations(self, data_handler, mock_minio, tmp_path):
        """Test downloading and converting annotations."""
        # Setup mock
        mock_obj = MagicMock()
        mock_obj.object_name = "annotations/verified/ann1.json"
        mock_minio.list_objects.return_value = [mock_obj]

        # Prepare directory
        data_handler.prepare_data_directory()

        # Mock fget_object to create annotation file
        def create_annotation(bucket, obj_name, local_path):
            annotation = {
                "image_id": "image1.jpg",
                "class_id": 0,
                "bbox": [0.5, 0.5, 0.1, 0.1]
            }
            with open(local_path, "w") as f:
                json.dump(annotation, f)

        mock_minio.fget_object.side_effect = create_annotation

        # Test
        count = data_handler.download_annotations()

        assert count == 1
        # Check label file was created
        label_path = data_handler.data_dir / "labels" / "train" / "image1.txt"
        assert label_path.exists()
        with open(label_path) as f:
            content = f.read()
        assert "0 0.5 0.5 0.1 0.1" in content

    def test_split_data(self, data_handler, tmp_path):
        """Test splitting data into train/val sets."""
        # Prepare directory and create test images
        data_handler.prepare_data_directory()
        train_images = data_handler.data_dir / "images" / "train"

        # Create 10 test images
        for i in range(10):
            (train_images / f"image{i}.jpg").touch()
            # Create corresponding label
            label_path = data_handler.data_dir / "labels" / "train" / f"image{i}.txt"
            label_path.write_text("0 0.5 0.5 0.1 0.1")

        # Test split with 20% validation
        train_count, val_count = data_handler.split_data(val_ratio=0.2)

        assert train_count == 8
        assert val_count == 2

        # Check files were moved
        val_images = list((data_handler.data_dir / "images" / "val").glob("*.jpg"))
        assert len(val_images) == 2

    def test_create_dataset_yaml(self, data_handler):
        """Test creating YOLO dataset configuration."""
        data_handler.prepare_data_directory()

        yaml_path = data_handler.create_dataset_yaml(["person", "car"])

        assert yaml_path.exists()
        content = yaml_path.read_text()
        assert "person" in content
        assert "car" in content
        assert "train: images/train" in content
        assert "val: images/val" in content


class TestPrepareTrainingData:
    """Tests for prepare_training_data function."""

    def test_prepare_training_data_orchestration(self, mock_minio, tmp_path):
        """Test full data preparation workflow."""
        with patch("src.data_handler.settings") as mock_settings:
            mock_settings.minio_endpoint = "localhost:9000"
            mock_settings.minio_access_key = "test"
            mock_settings.minio_secret_key = "test"
            mock_settings.minio_secure = False
            mock_settings.minio_bucket_datasets = "datasets"
            mock_settings.data_dir = str(tmp_path / "data")
            mock_settings.validation_split = 0.2

            # Mock list_objects to return some images
            mock_img = MagicMock()
            mock_img.object_name = "training/img1.jpg"
            mock_minio.list_objects.return_value = [mock_img]

            def create_file(bucket, obj_name, local_path):
                Path(local_path).touch()

            mock_minio.fget_object.side_effect = create_file

            handler = DataHandler()
            handler.data_dir = tmp_path / "data"

            yaml_path, count = prepare_training_data(handler)

            assert yaml_path.exists()
            assert count == 1
