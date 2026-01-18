"""Unit tests for validator module."""

import os
from unittest.mock import MagicMock, patch

import pytest

# Patch settings before importing
with patch.dict(os.environ, {
    "MINIO_ENDPOINT": "localhost:9000",
    "MINIO_ACCESS_KEY": "test",
    "MINIO_SECRET_KEY": "test",
    "OUTPUT_DIR": "/tmp/test_output",
    "MIN_MAP_IMPROVEMENT": "0.0",
}):
    from src.validator import ModelValidator, ValidationResult


@pytest.fixture
def mock_minio():
    """Mock MinIO client."""
    with patch("src.validator.Minio") as mock_class:
        mock_client = MagicMock()
        mock_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def validator(mock_minio, tmp_path):
    """Create ModelValidator with mocked MinIO."""
    with patch("src.validator.settings") as mock_settings:
        mock_settings.minio_endpoint = "localhost:9000"
        mock_settings.minio_access_key = "test"
        mock_settings.minio_secret_key = "test"
        mock_settings.minio_secure = False
        mock_settings.minio_bucket_models = "models"
        mock_settings.output_dir = str(tmp_path)
        mock_settings.min_map_improvement = 0.0

        yield ModelValidator()


class TestValidationResult:
    """Tests for ValidationResult dataclass."""

    def test_validation_result_creation(self):
        """Test creating a validation result."""
        result = ValidationResult(
            map50=0.85,
            map50_95=0.65,
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )

        assert result.map50 == 0.85
        assert result.map50_95 == 0.65
        assert result.improved is True  # default


class TestModelValidator:
    """Tests for ModelValidator class."""

    def test_validate_model(self, validator):
        """Test model validation extracts correct metrics."""
        # Mock model and validation results
        mock_model = MagicMock()
        mock_results = MagicMock()
        mock_results.results_dict = {
            "metrics/mAP50(B)": 0.85,
            "metrics/mAP50-95(B)": 0.65,
            "metrics/precision(B)": 0.9,
            "metrics/recall(B)": 0.8,
        }
        mock_results.__len__ = lambda x: 100
        mock_model.val.return_value = mock_results

        result = validator.validate_model(mock_model, "/tmp/data.yaml")

        assert result.map50 == 0.85
        assert result.map50_95 == 0.65
        assert result.precision == 0.9
        assert result.recall == 0.8

    def test_get_previous_metrics_no_versions(self, validator, mock_minio):
        """Test getting previous metrics when no versions exist."""
        mock_minio.list_objects.return_value = []

        result = validator.get_previous_metrics()

        assert result is None

    def test_compare_models_no_previous(self, validator):
        """Test comparison when no previous model exists."""
        current = ValidationResult(
            map50=0.85,
            map50_95=0.65,
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )

        result = validator.compare_models(current, None)

        assert result is True

    def test_compare_models_improved(self, validator):
        """Test comparison when current model is better."""
        current = ValidationResult(
            map50=0.90,
            map50_95=0.70,
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )
        previous = {"map50_95": 0.65}

        result = validator.compare_models(current, previous)

        assert result is True

    def test_compare_models_not_improved(self, validator):
        """Test comparison when current model is worse but min_improvement is 0."""
        current = ValidationResult(
            map50=0.80,
            map50_95=0.60,
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )
        previous = {"map50_95": 0.65}

        # With default min_map_improvement=0, even worse models pass
        result = validator.compare_models(current, previous)

        # The improvement is -0.05, which is >= 0 (the default min_map_improvement)
        # Since -0.05 < 0, this should return False
        assert result is False

    def test_should_early_stop_no_previous(self, validator):
        """Test early stopping with no previous model."""
        current = ValidationResult(
            map50=0.85,
            map50_95=0.65,
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )

        result = validator.should_early_stop(current, None)

        assert result is False

    def test_should_early_stop_significant_degradation(self, validator):
        """Test early stopping triggers on significant degradation."""
        current = ValidationResult(
            map50=0.50,
            map50_95=0.40,  # Much worse
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )
        previous = {"map50_95": 0.65}  # Was 0.65, now 0.40 = 38% drop

        result = validator.should_early_stop(current, previous)

        assert result is True

    def test_should_early_stop_minor_degradation(self, validator):
        """Test early stopping does not trigger on minor degradation."""
        current = ValidationResult(
            map50=0.83,
            map50_95=0.63,  # Slightly worse
            precision=0.9,
            recall=0.8,
            validation_images=100,
            timestamp="2026-01-18T00:00:00",
        )
        previous = {"map50_95": 0.65}  # Was 0.65, now 0.63 = 3% drop

        result = validator.should_early_stop(current, previous)

        assert result is False
