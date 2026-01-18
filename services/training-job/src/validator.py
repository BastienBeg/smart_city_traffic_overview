"""Validation and metrics calculation for trained models.

This module handles model validation on held-out test sets and computes
mAP metrics to evaluate model performance.
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from minio import Minio
from minio.error import S3Error

from src.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of model validation."""

    map50: float  # mAP@0.5
    map50_95: float  # mAP@0.5:0.95
    precision: float
    recall: float
    validation_images: int
    timestamp: str
    improved: bool = True


class ModelValidator:
    """Validates trained models and compares against previous versions."""

    def __init__(
        self,
        minio_client: Optional[Minio] = None,
    ) -> None:
        """Initialize the validator.

        Args:
            minio_client: Optional MinIO client for retrieving previous metrics.
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

    def validate_model(
        self,
        model: Any,
        data_yaml: Path,
    ) -> ValidationResult:
        """Run validation on a trained model.

        Args:
            model: Trained YOLO model instance.
            data_yaml: Path to dataset.yaml configuration.

        Returns:
            ValidationResult with computed metrics.
        """
        logger.info("Running model validation...")

        # Run validation using Ultralytics API
        results = model.val(data=str(data_yaml))

        # Extract metrics
        metrics = results.results_dict

        result = ValidationResult(
            map50=metrics.get("metrics/mAP50(B)", 0.0),
            map50_95=metrics.get("metrics/mAP50-95(B)", 0.0),
            precision=metrics.get("metrics/precision(B)", 0.0),
            recall=metrics.get("metrics/recall(B)", 0.0),
            validation_images=len(results),
            timestamp=datetime.utcnow().isoformat(),
        )

        logger.info(
            f"Validation complete: mAP@0.5={result.map50:.4f}, "
            f"mAP@0.5:0.95={result.map50_95:.4f}"
        )
        return result

    def get_previous_metrics(self) -> Optional[dict[str, Any]]:
        """Retrieve metrics from the previous model version.

        Returns:
            Previous model metrics or None if not found.
        """
        try:
            # List model versions to find the latest
            objects = list(
                self.minio_client.list_objects(
                    self.models_bucket, prefix="sentinel-yolo/", recursive=False
                )
            )

            if not objects:
                logger.info("No previous model versions found")
                return None

            # Find latest version (format: v1, v2, etc.)
            versions = []
            for obj in objects:
                version_str = obj.object_name.rstrip("/").split("/")[-1]
                if version_str.startswith("v"):
                    try:
                        versions.append(int(version_str[1:]))
                    except ValueError:
                        continue

            if not versions:
                return None

            latest_version = max(versions)
            metrics_path = f"sentinel-yolo/v{latest_version}/metadata.json"

            # Download metrics
            temp_path = Path(settings.output_dir) / "prev_metadata.json"
            temp_path.parent.mkdir(parents=True, exist_ok=True)

            self.minio_client.fget_object(
                self.models_bucket, metrics_path, str(temp_path)
            )

            with open(temp_path, "r") as f:
                metrics = json.load(f)

            logger.info(f"Retrieved previous metrics from v{latest_version}")
            return metrics

        except S3Error as e:
            logger.warning(f"Could not retrieve previous metrics: {e}")
            return None

    def compare_models(
        self,
        current: ValidationResult,
        previous: Optional[dict[str, Any]],
    ) -> bool:
        """Compare current model against previous version.

        Args:
            current: Current model validation results.
            previous: Previous model metrics.

        Returns:
            True if current model is better or if no previous exists.
        """
        if previous is None:
            logger.info("No previous model to compare - accepting current")
            return True

        prev_map = previous.get("map50_95", 0.0)
        improvement = current.map50_95 - prev_map

        if improvement >= settings.min_map_improvement:
            logger.info(
                f"Model improved: mAP {prev_map:.4f} -> {current.map50_95:.4f} "
                f"(+{improvement:.4f})"
            )
            return True
        else:
            logger.warning(
                f"Model did not improve: mAP {prev_map:.4f} -> {current.map50_95:.4f} "
                f"({improvement:+.4f})"
            )
            return False

    def should_early_stop(
        self,
        current: ValidationResult,
        previous: Optional[dict[str, Any]],
    ) -> bool:
        """Determine if training should stop due to performance degradation.

        Args:
            current: Current model validation results.
            previous: Previous model metrics.

        Returns:
            True if model performance has degraded significantly.
        """
        if previous is None:
            return False

        prev_map = previous.get("map50_95", 0.0)

        # Stop if performance dropped by more than 5%
        degradation_threshold = 0.05
        if prev_map > 0 and (prev_map - current.map50_95) / prev_map > degradation_threshold:
            logger.warning(
                f"Early stopping: performance degraded by more than {degradation_threshold*100}%"
            )
            return True

        return False
