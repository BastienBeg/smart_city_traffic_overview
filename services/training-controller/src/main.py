"""Main entry point for Training Controller service.

Implements a polling loop that monitors verified annotation count
and triggers training jobs when the threshold is reached.
"""

import asyncio
import logging
import sys

from src.config import settings
from src.database import (
    get_verified_unused_count,
    get_verified_unused_ids,
    mark_annotations_as_used
)
from src.k8s_manager import (
    is_training_job_active,
    create_training_job,
    get_completed_training_job
)
from src.git_promoter import promote_model_async
from src.argocd_client import trigger_argocd_sync_async

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


async def check_and_trigger_training() -> bool:
    """Check annotation count and trigger training if threshold is met.

    Returns:
        bool: True if training was triggered, False otherwise.
    """
    # Step 1: Check if a training job is already running
    if is_training_job_active():
        logger.info("Training already in progress, skipping trigger")
        return False

    # Step 2: Get count of verified, unused annotations
    count = await get_verified_unused_count()

    if count < settings.training_threshold:
        logger.info(
            f"Annotation count ({count}) below threshold "
            f"({settings.training_threshold}), skipping trigger"
        )
        return False

    # Step 3: Threshold reached - trigger training
    logger.info(
        f"Triggering training with {count} new images "
        f"(threshold: {settings.training_threshold})"
    )

    # Get the IDs for marking
    annotation_ids = await get_verified_unused_ids()

    # Create the K8s job
    job_name = create_training_job(annotation_count=count)

    if job_name:
        # Mark annotations as used for training
        await mark_annotations_as_used(annotation_ids)
        logger.info(f"Training job '{job_name}' triggered successfully")
        return True
    else:
        logger.error("Failed to create training job")
        return False


async def check_and_promote_model() -> None:
    """Check for completed training jobs and promote the model if successful."""
    completed_job = get_completed_training_job()

    if not completed_job:
        return

    job_name, succeeded = completed_job

    if not succeeded:
        logger.warning(f"Training job {job_name} did not succeed, skipping promotion")
        return

    # Extract version from job metadata or generate new one
    # Job labels contain version info from training-job
    new_version = extract_model_version(job_name)

    if not new_version:
        logger.warning("Could not determine model version from job, skipping promotion")
        return

    logger.info(f"Training job {job_name} completed, promoting model to {new_version}")

    # Promote the model via GitOps
    try:
        success = await promote_model_async(new_version)

        if success:
            logger.info(f"Model {new_version} promoted successfully via GitOps")

            # Optionally trigger ArgoCD sync
            await trigger_argocd_sync_async()
        else:
            logger.error(f"Failed to promote model {new_version}")

    except Exception as e:
        logger.exception(f"Error during model promotion: {e}")


def extract_model_version(job_name: str) -> str | None:
    """Extract or generate model version from training job name.

    Args:
        job_name: The training job name.

    Returns:
        str | None: The model version string (e.g., 'v2') or None.
    """
    # Job name format: sentinel-training-YYYYMMDD-HHMMSS
    # We derive the version from the timestamp
    try:
        # Extract timestamp part and use as version identifier
        parts = job_name.split("-")
        if len(parts) >= 3:
            date_part = parts[2]  # YYYYMMDD
            time_part = parts[3] if len(parts) > 3 else "000000"  # HHMMSS
            return f"v{date_part}{time_part}"
    except Exception as e:
        logger.warning(f"Failed to extract version from job name: {e}")

    return None


async def polling_loop() -> None:
    """Main polling loop that runs indefinitely."""
    logger.info(
        f"Starting Training Controller with threshold={settings.training_threshold}, "
        f"poll_interval={settings.poll_interval_seconds}s"
    )

    while True:
        try:
            # Check for completed jobs and promote model
            await check_and_promote_model()

            # Check if we should trigger new training
            await check_and_trigger_training()

        except Exception as e:
            logger.exception(f"Error in training controller loop: {e}")

        logger.info(
            f"Sleeping for {settings.poll_interval_seconds} seconds..."
        )
        await asyncio.sleep(settings.poll_interval_seconds)


def main() -> None:
    """Entry point for the service."""
    logger.info("Training Controller starting...")
    try:
        asyncio.run(polling_loop())
    except KeyboardInterrupt:
        logger.info("Training Controller stopped by user")
    except Exception as e:
        logger.exception(f"Training Controller crashed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
