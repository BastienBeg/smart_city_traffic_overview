"""Configuration module for Training Controller service.

Loads settings from environment variables with sensible defaults.
"""

import os
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Database configuration
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql+asyncpg://user:password@postgres:5432/smartcity"
    )

    # Training threshold - number of verified images before triggering training
    training_threshold: int = int(os.getenv("TRAINING_THRESHOLD", "50"))

    # Polling interval in seconds
    poll_interval_seconds: int = int(os.getenv("POLL_INTERVAL_SECONDS", "300"))

    # Kubernetes namespace for training jobs
    k8s_namespace: str = os.getenv("K8S_NAMESPACE", "default")

    # Training job container image (placeholder for Story 4.4)
    training_image: str = os.getenv(
        "TRAINING_IMAGE",
        "alpine:latest"  # Placeholder - will sleep for testing
    )

    # Git configuration for model promotion
    git_repo_url: str = os.getenv("GIT_REPO_URL", "")
    git_branch: str = os.getenv("GIT_BRANCH", "main")
    git_username: str = os.getenv("GIT_USERNAME", "Training Controller")
    git_email: str = os.getenv("GIT_EMAIL", "training-controller@smartcity.local")
    git_ssh_key_path: str = os.getenv("GIT_SSH_KEY_PATH", "")
    git_pat: str = os.getenv("GIT_PAT", "")
    model_config_path: str = os.getenv(
        "MODEL_CONFIG_PATH",
        "k8s/apps/inference-service/base/deployment.yaml"
    )

    # ArgoCD configuration (optional)
    argocd_server_url: str = os.getenv("ARGOCD_SERVER_URL", "")
    argocd_auth_token: str = os.getenv("ARGOCD_AUTH_TOKEN", "")
    argocd_app_name: str = os.getenv("ARGOCD_APP_NAME", "inference-service")

    # Feature flags
    enable_model_promotion: bool = os.getenv(
        "ENABLE_MODEL_PROMOTION", "true"
    ).lower() == "true"

    class Config:
        """Pydantic config."""

        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
