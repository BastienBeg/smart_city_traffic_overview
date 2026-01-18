"""Model export and upload to MinIO.

This module handles exporting trained models to .pt and .onnx formats
and uploading them with versioning to MinIO object storage.
"""

import json
import logging
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from minio import Minio
from minio.error import S3Error

from src.config import settings
from src.validator import ValidationResult

logger = logging.getLogger(__name__)


class ModelUploader:
    """Handles model export and upload to MinIO with versioning."""

    def __init__(
        self,
        minio_client: Optional[Minio] = None,
    ) -> None:
        """Initialize the uploader.

        Args:
            minio_client: Optional MinIO client. Creates one if not provided.
        """
        if minio_client is None:
            self.minio_client = Minio(
                endpoint=settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
        else:
            self.minio_client = minio_client
        self.models_bucket = settings.minio_bucket_models
        self.output_dir = Path(settings.output_dir)

    def get_next_version(self) -> int:
        """Determine the next model version number.

        Returns:
            Next version number (e.g., 2 if v1 exists).
        """
        try:
            objects = list(
                self.minio_client.list_objects(
                    self.models_bucket, prefix="sentinel-yolo/", recursive=False
                )
            )

            versions = []
            for obj in objects:
                version_str = obj.object_name.rstrip("/").split("/")[-1]
                if version_str.startswith("v"):
                    try:
                        versions.append(int(version_str[1:]))
                    except ValueError:
                        continue

            if versions:
                next_version = max(versions) + 1
                logger.info(f"Found existing versions, next will be v{next_version}")
                return next_version
            else:
                logger.info("No existing versions found, starting with v1")
                return 1

        except S3Error as e:
            logger.warning(f"Could not check existing versions: {e}, starting with v1")
            return 1

    def export_model(
        self,
        model: Any,
        version: int,
    ) -> tuple[Path, Path]:
        """Export model to .pt and .onnx formats.

        Args:
            model: Trained YOLO model instance.
            version: Model version number.

        Returns:
            Tuple of (pt_path, onnx_path).
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Export PyTorch format
        pt_path = self.output_dir / f"sentinel-yolo-v{version}.pt"
        model.save(str(pt_path))
        logger.info(f"Exported PyTorch model to {pt_path}")

        # Export ONNX format
        onnx_path = self.output_dir / f"sentinel-yolo-v{version}.onnx"
        model.export(format="onnx", imgsz=settings.training_image_size)

        # Move exported ONNX to our naming convention
        default_onnx = self.output_dir / "best.onnx"
        if default_onnx.exists():
            default_onnx.rename(onnx_path)
        logger.info(f"Exported ONNX model to {onnx_path}")

        return pt_path, onnx_path

    def create_metadata(
        self,
        version: int,
        validation_result: ValidationResult,
        image_count: int,
        training_config: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Create metadata for the model version.

        Args:
            version: Model version number.
            validation_result: Validation metrics.
            image_count: Number of training images used.
            training_config: Optional training configuration.

        Returns:
            Metadata dictionary.
        """
        metadata = {
            "version": version,
            "training_date": datetime.utcnow().isoformat(),
            "image_count": image_count,
            **asdict(validation_result),
            "training_config": training_config or {
                "epochs": settings.training_epochs,
                "batch_size": settings.training_batch_size,
                "image_size": settings.training_image_size,
                "device": settings.training_device,
            },
        }
        return metadata

    def upload_model(
        self,
        pt_path: Path,
        onnx_path: Path,
        metadata: dict[str, Any],
        version: int,
    ) -> bool:
        """Upload model files and metadata to MinIO.

        Args:
            pt_path: Path to .pt model file.
            onnx_path: Path to .onnx model file.
            metadata: Model metadata dictionary.
            version: Model version number.

        Returns:
            True if upload successful.
        """
        try:
            # Ensure bucket exists
            if not self.minio_client.bucket_exists(self.models_bucket):
                self.minio_client.make_bucket(self.models_bucket)
                logger.info(f"Created bucket: {self.models_bucket}")

            version_prefix = f"sentinel-yolo/v{version}"

            # Upload PyTorch model
            pt_object = f"{version_prefix}/model.pt"
            self.minio_client.fput_object(
                self.models_bucket,
                pt_object,
                str(pt_path),
                content_type="application/octet-stream",
            )
            logger.info(f"Uploaded {pt_object}")

            # Upload ONNX model
            onnx_object = f"{version_prefix}/model.onnx"
            self.minio_client.fput_object(
                self.models_bucket,
                onnx_object,
                str(onnx_path),
                content_type="application/octet-stream",
            )
            logger.info(f"Uploaded {onnx_object}")

            # Upload metadata
            metadata_path = self.output_dir / "metadata.json"
            with open(metadata_path, "w") as f:
                json.dump(metadata, f, indent=2)

            metadata_object = f"{version_prefix}/metadata.json"
            self.minio_client.fput_object(
                self.models_bucket,
                metadata_object,
                str(metadata_path),
                content_type="application/json",
            )
            logger.info(f"Uploaded {metadata_object}")

            # Update 'latest' symlink (copy to latest/)
            for obj_name, local_path in [
                ("latest/model.pt", pt_path),
                ("latest/model.onnx", onnx_path),
                ("latest/metadata.json", metadata_path),
            ]:
                # Reupload to latest/
                self.minio_client.fput_object(
                    self.models_bucket,
                    f"sentinel-yolo/{obj_name}",
                    str(local_path),
                )
            logger.info("Updated 'latest' symlinks")

            return True

        except S3Error as e:
            logger.error(f"Failed to upload model: {e}")
            return False


def export_and_upload(
    model: Any,
    validation_result: ValidationResult,
    image_count: int,
    uploader: Optional[ModelUploader] = None,
) -> tuple[bool, int]:
    """Export a trained model and upload to MinIO.

    Args:
        model: Trained YOLO model.
        validation_result: Validation metrics.
        image_count: Number of training images.
        uploader: Optional ModelUploader instance.

    Returns:
        Tuple of (success, version).
    """
    if uploader is None:
        uploader = ModelUploader()

    # Get next version
    version = uploader.get_next_version()

    # Export model
    pt_path, onnx_path = uploader.export_model(model, version)

    # Create metadata
    metadata = uploader.create_metadata(version, validation_result, image_count)

    # Upload to MinIO
    success = uploader.upload_model(pt_path, onnx_path, metadata, version)

    if success:
        logger.info(f"Successfully uploaded model v{version}")
    else:
        logger.error(f"Failed to upload model v{version}")

    return success, version
