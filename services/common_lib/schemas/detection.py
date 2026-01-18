from pydantic import BaseModel
from typing import Optional, List

class Detection(BaseModel):
    class_name: str
    confidence: float
    bbox: List[float]  # [x, y, w, h]
    track_id: Optional[int] = None

class DetectionEvent(BaseModel):
    camera_id: str
    timestamp: str
    frame_id: str
    detections: List[Detection]
    anomaly_type: Optional[str] = None
    image_url: Optional[str] = None
