"""MinIO data handler for downloading training datasets and annotations.

This module handles all interactions with MinIO for retrieving training data.
It downloads images and converts verified annotations to YOLO format.
"""

import json
import logging
import os
import shutil
from pathlib import Path
from typing import Optional

from minio import Minio
from minio.error import S3Error

from src.config import settings

logger = logging.getLogger(__name__)


class DataHandler:
    """Handles dataset download and preparation from MinIO."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        secure: Optional[bool] = None,
    ) -> None:
        """Initialize the MinIO client.

        Args:
            endpoint: MinIO server endpoint. Defaults to settings.
            access_key: MinIO access key. Defaults to settings.
            secret_key: MinIO secret key. Defaults to settings.
            secure: Use HTTPS. Defaults to settings.
        """
        self.client = Minio(
            endpoint=endpoint or settings.minio_endpoint,
            access_key=access_key or settings.minio_access_key,
            secret_key=secret_key or settings.minio_secret_key,
            secure=secure if secure is not None else settings.minio_secure,
        )
        self.datasets_bucket = settings.minio_bucket_datasets
        self.data_dir = Path(settings.data_dir)

    def prepare_data_directory(self) -> Path:
        """Prepare the local data directory structure for YOLO training.

        Creates the following structure:
            data_dir/
            ├── images/
            │   ├── train/
            │   └── val/
            └── labels/
                ├── train/
                └── val/

        Returns:
            Path to the data directory.
        """
        # Clean existing directory
        if self.data_dir.exists():
            shutil.rmtree(self.data_dir)

        # Create YOLO-compatible structure
        for split in ["train", "val"]:
            (self.data_dir / "images" / split).mkdir(parents=True, exist_ok=True)
            (self.data_dir / "labels" / split).mkdir(parents=True, exist_ok=True)

        logger.info(f"Prepared data directory at {self.data_dir}")
        return self.data_dir

    def download_dataset(self, prefix: str = "training/") -> int:
        """Download training images from MinIO.

        Args:
            prefix: Object prefix to filter images in the bucket.

        Returns:
            Number of images downloaded.
        """
        image_count = 0

        try:
            objects = self.client.list_objects(
                self.datasets_bucket, prefix=prefix, recursive=True
            )

            for obj in objects:
                if obj.object_name.endswith((".jpg", ".jpeg", ".png")):
                    local_path = self.data_dir / "images" / "train" / Path(
                        obj.object_name
                    ).name
                    self.client.fget_object(
                        self.datasets_bucket, obj.object_name, str(local_path)
                    )
                    image_count += 1
                    logger.debug(f"Downloaded image: {obj.object_name}")

        except S3Error as e:
            logger.error(f"Failed to download dataset: {e}")
            raise

        logger.info(f"Downloaded {image_count} training images")
        return image_count

    def download_annotations(self, prefix: str = "annotations/verified/") -> int:
        """Download verified annotations and convert to YOLO format.

        Annotations are expected to be in JSON format with the structure:
        {
            "image_id": "image_name.jpg",
            "class_id": 0,
            "bbox": [x_center, y_center, width, height]  # normalized
        }

        Args:
            prefix: Object prefix to filter annotations in the bucket.

        Returns:
            Number of annotations downloaded.
        """
        annotation_count = 0

        try:
            objects = self.client.list_objects(
                self.datasets_bucket, prefix=prefix, recursive=True
            )

            for obj in objects:
                if obj.object_name.endswith(".json"):
                    # Download annotation file to temp location
                    temp_path = self.data_dir / "temp_annotation.json"
                    self.client.fget_object(
                        self.datasets_bucket, obj.object_name, str(temp_path)
                    )

                    # Parse and convert to YOLO format
                    with open(temp_path, "r") as f:
                        annotation = json.load(f)

                    image_name = annotation.get("image_id", "")
                    if not image_name:
                        logger.warning(f"Annotation missing image_id: {obj.object_name}")
                        continue

                    # Create YOLO label file
                    label_name = Path(image_name).stem + ".txt"
                    label_path = self.data_dir / "labels" / "train" / label_name

                    # YOLO format: class_id x_center y_center width height
                    class_id = annotation.get("class_id", 0)
                    bbox = annotation.get("bbox", [0.5, 0.5, 0.1, 0.1])

                    # Append to label file (multiple annotations per image)
                    with open(label_path, "a") as f:
                        f.write(f"{class_id} {bbox[0]} {bbox[1]} {bbox[2]} {bbox[3]}\n")

                    annotation_count += 1
                    logger.debug(f"Processed annotation: {obj.object_name}")

                    # Clean up temp file
                    temp_path.unlink()

        except S3Error as e:
            logger.error(f"Failed to download annotations: {e}")
            raise

        logger.info(f"Processed {annotation_count} verified annotations")
        return annotation_count

    def split_data(self, val_ratio: float = 0.2) -> tuple[int, int]:
        """Split downloaded data into training and validation sets.

        Args:
            val_ratio: Fraction of data to use for validation.

        Returns:
            Tuple of (train_count, val_count).
        """
        train_images_dir = self.data_dir / "images" / "train"
        val_images_dir = self.data_dir / "images" / "val"
        train_labels_dir = self.data_dir / "labels" / "train"
        val_labels_dir = self.data_dir / "labels" / "val"

        # Get all training images
        images = list(train_images_dir.glob("*.*"))
        total = len(images)
        val_count = int(total * val_ratio)

        # Move validation images and their labels
        for img_path in images[:val_count]:
            # Move image
            shutil.move(str(img_path), str(val_images_dir / img_path.name))

            # Move corresponding label if it exists
            label_name = img_path.stem + ".txt"
            label_path = train_labels_dir / label_name
            if label_path.exists():
                shutil.move(str(label_path), str(val_labels_dir / label_name))

        train_count = total - val_count
        logger.info(f"Split data: {train_count} train, {val_count} validation")
        return train_count, val_count

    def create_dataset_yaml(self, class_names: Optional[list[str]] = None) -> Path:
        """Create YOLO dataset configuration file.

        Args:
            class_names: List of class names. Defaults to ['object'].

        Returns:
            Path to the created YAML file.
        """
        if class_names is None:
            class_names = ["person", "vehicle", "bicycle"]  # Default Sentinel classes

        yaml_content = f"""# Sentinel Training Dataset
path: {self.data_dir}
train: images/train
val: images/val

# Classes
names:
"""
        for i, name in enumerate(class_names):
            yaml_content += f"  {i}: {name}\n"

        yaml_path = self.data_dir / "dataset.yaml"
        with open(yaml_path, "w") as f:
            f.write(yaml_content)

        logger.info(f"Created dataset YAML at {yaml_path}")
        return yaml_path


def prepare_training_data(
    data_handler: Optional[DataHandler] = None,
) -> tuple[Path, int]:
    """Prepare training data by downloading from MinIO.

    Args:
        data_handler: Optional DataHandler instance. Creates one if not provided.

    Returns:
        Tuple of (dataset_yaml_path, total_images).
    """
    if data_handler is None:
        data_handler = DataHandler()

    # Prepare directory structure
    data_handler.prepare_data_directory()

    # Download data
    image_count = data_handler.download_dataset()
    data_handler.download_annotations()

    # Split into train/val
    train_count, val_count = data_handler.split_data(
        val_ratio=settings.validation_split
    )

    # Create dataset config
    yaml_path = data_handler.create_dataset_yaml()

    logger.info(
        f"Training data prepared: {train_count} train, {val_count} val images"
    )
    return yaml_path, image_count
