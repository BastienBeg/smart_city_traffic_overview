"""Kubernetes Job manager for Training Controller service.

Handles checking for active training jobs and dispatching new ones.
"""

import logging
from datetime import datetime
from typing import Optional, Tuple

from kubernetes import client, config
from kubernetes.client.rest import ApiException

from src.config import settings

logger = logging.getLogger(__name__)

# Job labels for identification
TRAINING_JOB_LABEL = "app=sentinel-training"
TRAINING_JOB_APP_LABEL = "sentinel-training"

# Track processed jobs to avoid re-promoting
_processed_jobs: set = set()


def _get_k8s_client() -> client.BatchV1Api:
    """Get Kubernetes BatchV1 API client.

    Tries in-cluster config first, falls back to kubeconfig.

    Returns:
        BatchV1Api: Kubernetes batch API client.
    """
    try:
        config.load_incluster_config()
        logger.info("Loaded in-cluster Kubernetes config")
    except config.ConfigException:
        try:
            config.load_kube_config()
            logger.info("Loaded kubeconfig from default location")
        except config.ConfigException as e:
            logger.error(f"Failed to load Kubernetes config: {e}")
            raise

    return client.BatchV1Api()


def is_training_job_active() -> bool:
    """Check if a training job is currently running.

    Returns:
        bool: True if an active training job exists, False otherwise.
    """
    try:
        batch_api = _get_k8s_client()
        jobs = batch_api.list_namespaced_job(
            namespace=settings.k8s_namespace,
            label_selector=TRAINING_JOB_LABEL
        )

        for job in jobs.items:
            # Check if job is still active (not completed or failed)
            if job.status.active and job.status.active > 0:
                logger.info(
                    f"Active training job found: {job.metadata.name}"
                )
                return True

            # Check if job is not yet completed
            if job.status.succeeded is None and job.status.failed is None:
                logger.info(
                    f"Pending training job found: {job.metadata.name}"
                )
                return True

        logger.info("No active training jobs found")
        return False

    except ApiException as e:
        logger.error(f"Failed to check for active jobs: {e}")
        # In case of API error, assume a job might be running to be safe
        return True


def get_completed_training_job() -> Optional[Tuple[str, bool]]:
    """Get a recently completed training job that hasn't been processed.

    Returns:
        Optional[Tuple[str, bool]]: Tuple of (job_name, succeeded) or None.
    """
    try:
        batch_api = _get_k8s_client()
        jobs = batch_api.list_namespaced_job(
            namespace=settings.k8s_namespace,
            label_selector=TRAINING_JOB_LABEL
        )

        for job in jobs.items:
            job_name = job.metadata.name

            # Skip already processed jobs
            if job_name in _processed_jobs:
                continue

            # Check if job completed successfully
            if job.status.succeeded and job.status.succeeded > 0:
                _processed_jobs.add(job_name)
                logger.info(f"Found completed successful job: {job_name}")
                return (job_name, True)

            # Check if job failed
            if job.status.failed and job.status.failed > 0:
                _processed_jobs.add(job_name)
                logger.warning(f"Found completed failed job: {job_name}")
                return (job_name, False)

        return None

    except ApiException as e:
        logger.error(f"Failed to check for completed jobs: {e}")
        return None


def create_training_job(annotation_count: int) -> Optional[str]:
    """Create a new Kubernetes training job.

    Args:
        annotation_count: Number of annotations being used for training (for logging).

    Returns:
        Optional[str]: Job name if created successfully, None otherwise.
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    job_name = f"sentinel-training-{timestamp}"

    job_manifest = client.V1Job(
        api_version="batch/v1",
        kind="Job",
        metadata=client.V1ObjectMeta(
            name=job_name,
            namespace=settings.k8s_namespace,
            labels={
                "app": TRAINING_JOB_APP_LABEL,
                "annotation-count": str(annotation_count)
            }
        ),
        spec=client.V1JobSpec(
            ttl_seconds_after_finished=3600,  # Clean up after 1 hour
            backoff_limit=2,
            template=client.V1PodTemplateSpec(
                metadata=client.V1ObjectMeta(
                    labels={"app": TRAINING_JOB_APP_LABEL}
                ),
                spec=client.V1PodSpec(
                    restart_policy="Never",
                    containers=[
                        client.V1Container(
                            name="training",
                            image=settings.training_image,
                            # Placeholder command - sleeps to simulate training
                            command=["sh", "-c", "echo 'Training with annotations...'; sleep 60; echo 'Training complete'"],
                            resources=client.V1ResourceRequirements(
                                requests={"memory": "256Mi", "cpu": "100m"},
                                limits={"memory": "512Mi", "cpu": "500m"}
                            ),
                            env=[
                                client.V1EnvVar(
                                    name="ANNOTATION_COUNT",
                                    value=str(annotation_count)
                                )
                            ]
                        )
                    ]
                )
            )
        )
    )

    try:
        batch_api = _get_k8s_client()
        batch_api.create_namespaced_job(
            namespace=settings.k8s_namespace,
            body=job_manifest
        )
        logger.info(
            f"Created training job '{job_name}' with {annotation_count} annotations"
        )
        return job_name

    except ApiException as e:
        logger.error(f"Failed to create training job: {e}")
        return None
