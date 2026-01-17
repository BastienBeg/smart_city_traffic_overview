import numpy as np
import cv2
from ultralytics import YOLO
from typing import List, Dict, Any, Union

class InferenceModel:
    """
    Wrapper around YOLOv8 model for object detection.

    Attributes:
        model (YOLO): The loaded YOLOv8 model.
    """

    def __init__(self, model_path: str = "yolov8n.pt") -> None:
        """
        Initialize the InferenceModel.

        Args:
            model_path (str): Path to the YOLO model weights. Defaults to "yolov8n.pt".
        """
        print(f"Loading YOLO model from {model_path}...")
        self.model = YOLO(model_path)
        print("Model loaded successfully.")

    def predict(self, image_bytes: bytes) -> List[Dict[str, Union[float, int, str]]]:
        """
        Run inference on the provided image bytes.

        Args:
            image_bytes (bytes): Raw image data (e.g., JPEG/PNG bytes).

        Returns:
            List[Dict[str, Union[float, int, str]]]: List of detections, where each detection is a dictionary containing:
                - x1, y1, x2, y2 (float): Bounding box coordinates.
                - confidence (float): Detection confidence score.
                - class_id (int): Class ID.
                - class_name (str): Human-readable class name.
        """
        # Convert bytes to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

        if image is None:
            print("Failed to decode image")
            return []

        results = self.model(image, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # box.xyxy is [x1, y1, x2, y2]
                coords = box.xyxy[0].tolist()
                conf = box.conf[0].item()
                cls_id = int(box.cls[0].item())
                # Get class name if available
                # ultralytics result.names is a dict {id: name}
                cls_name = result.names[cls_id] if result.names and cls_id in result.names else str(cls_id)

                detections.append({
                    "x1": coords[0],
                    "y1": coords[1],
                    "x2": coords[2],
                    "y2": coords[3],
                    "confidence": conf,
                    "class_id": cls_id,
                    "class_name": cls_name
                })
        return detections
