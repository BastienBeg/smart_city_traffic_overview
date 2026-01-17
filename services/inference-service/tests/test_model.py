import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
from src.model import InferenceModel

@pytest.fixture
def mock_yolo():
    with patch('src.model.YOLO') as mock:
        yield mock

def test_inference_model_init(mock_yolo):
    """Test that model initializes and loads YOLO."""
    model = InferenceModel("test_path.pt")
    mock_yolo.assert_called_with("test_path.pt")
    assert model.model is not None

def test_predict_success(mock_yolo):
    """Test successful prediction flow."""
    # Setup mock return values
    mock_instance = mock_yolo.return_value
    
    # Mock result object from ultralytics
    mock_result = MagicMock()
    mock_box = MagicMock()
    # Mock box attributes: xyxy, conf, cls
    mock_box.xyxy = np.array([[10, 20, 30, 40]])
    mock_box.conf = np.array([0.95])
    mock_box.cls = np.array([0])
    
    mock_result.boxes = [mock_box]
    mock_result.names = {0: "person"}
    
    mock_instance.return_value = [mock_result]
    
    model = InferenceModel()
    
    # Create fake image bytes
    fake_img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, encoded = cv2.imencode('.jpg', fake_img)
    img_bytes = encoded.tobytes()
    
    detections = model.predict(img_bytes)
    
    assert len(detections) == 1
    d = detections[0]
    assert d['x1'] == 10
    assert d['y1'] == 20
    assert d['confidence'] == 0.95
    assert d['class_name'] == "person"

def test_predict_invalid_image(mock_yolo):
    """Test prediction with invalid image bytes."""
    model = InferenceModel()
    detections = model.predict(b'not an image')
    assert detections == []
