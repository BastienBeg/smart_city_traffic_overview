"""Main training script for YOLOv8 fine-tuning.

This is the entry point for the training job. It orchestrates:
1. Dataset preparation from MinIO
2. YOLOv8 fine-tuning using Ultralytics
3. Model validation
4. Export and upload to MinIO

Usage:
    python -m src.train
"""

import logging
import sys
from pathlib import Path

from ultralytics import YOLO

from src.config import settings
from src.data_handler import DataHandler, prepare_training_data
from src.model_uploader import ModelUploader, export_and_upload
from src.validator import ModelValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def run_training(data_yaml: Path) -> YOLO:
    """Run YOLOv8 training.

    Args:
        data_yaml: Path to dataset.yaml configuration file.

    Returns:
        Trained YOLO model.
    """
    logger.info("Initializing YOLOv8 model for training...")

    # Initialize model (start from pretrained weights)
    model = YOLO("yolov8n.pt")

    logger.info(
        f"Starting training: epochs={settings.training_epochs}, "
        f"batch={settings.training_batch_size}, "
        f"imgsz={settings.training_image_size}"
    )

    # Run training
    model.train(
        data=str(data_yaml),
        epochs=settings.training_epochs,
        batch=settings.training_batch_size,
        imgsz=settings.training_image_size,
        patience=settings.training_patience,
        device=settings.training_device if settings.training_device != "auto" else None,
        project=str(Path(settings.output_dir) / "runs"),
        name="train",
        exist_ok=True,
        verbose=True,
    )

    logger.info("Training completed successfully")
    return model


def main() -> int:
    """Main entry point for the training job.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("=" * 60)
    logger.info("Sentinel Training Job Starting")
    logger.info("=" * 60)

    try:
        # Step 1: Prepare training data from MinIO
        logger.info("Step 1/4: Preparing training data...")
        data_handler = DataHandler()
        data_yaml, image_count = prepare_training_data(data_handler)

        if image_count == 0:
            logger.error("No training images found - aborting")
            return 1

        # Step 2: Run training
        logger.info("Step 2/4: Running YOLOv8 training...")
        model = run_training(data_yaml)

        # Step 3: Validate model
        logger.info("Step 3/4: Validating trained model...")
        validator = ModelValidator()
        validation_result = validator.validate_model(model, data_yaml)

        # Check for early stopping condition
        previous_metrics = validator.get_previous_metrics()
        if validator.should_early_stop(validation_result, previous_metrics):
            logger.warning("Early stopping triggered - model not uploaded")
            return 1

        # Compare with previous model
        improved = validator.compare_models(validation_result, previous_metrics)
        validation_result.improved = improved

        if not improved and settings.min_map_improvement > 0:
            logger.warning("Model did not improve - skipping upload")
            return 1

        # Step 4: Export and upload
        logger.info("Step 4/4: Exporting and uploading model...")
        uploader = ModelUploader()
        success, version = export_and_upload(
            model, validation_result, image_count, uploader
        )

        if not success:
            logger.error("Failed to upload model")
            return 1

        logger.info("=" * 60)
        logger.info(f"Training Job Completed Successfully - Model v{version}")
        logger.info(f"  mAP@0.5:     {validation_result.map50:.4f}")
        logger.info(f"  mAP@0.5:0.95: {validation_result.map50_95:.4f}")
        logger.info(f"  Images Used:  {image_count}")
        logger.info("=" * 60)

        return 0

    except Exception as e:
        logger.exception(f"Training job failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
