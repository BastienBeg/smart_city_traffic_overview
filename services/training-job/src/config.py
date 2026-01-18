"""Configuration settings for the Training Job."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Training job configuration from environment variables."""

    # MinIO Configuration
    minio_endpoint: str = "minio:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_secure: bool = False
    minio_bucket_datasets: str = "datasets"
    minio_bucket_models: str = "models"

    # Training Configuration
    training_epochs: int = 50
    training_batch_size: int = 16
    training_image_size: int = 640
    training_patience: int = 10
    training_device: str = "auto"  # "auto", "cpu", "cuda", or device id

    # Validation Configuration
    validation_split: float = 0.2
    min_map_improvement: float = 0.0  # Minimum mAP improvement to accept model

    # Paths
    data_dir: str = "/tmp/training_data"
    output_dir: str = "/tmp/training_output"

    class Config:
        """Pydantic settings configuration."""

        env_prefix = ""
        case_sensitive = False


settings = Settings()
