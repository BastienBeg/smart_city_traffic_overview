export type EventType = "detection" | "anomaly" | "alert" | "system";

export interface Detection {
  class: string;
  confidence: number;
  bbox: [number, number, number, number]; // [x, y, w, h] - likely normalized 0-1 based on typical YOLO/ONNX usage, but description says "normalized or px". We will assume normalized for canvas scaling.
  track_id?: number | string;
}

export interface DetectionEvent {
  id: string; // unique event id
  timestamp: Date;
  cameraId: string; // "camera_id" in architecture, mapped to camelCase for TS conventions if we transform, or keep snake_case if raw. Let's use camelCase for internal app usage and transform ingress if needed.
  cameraName?: string; // Optional, might need lookup
  eventType: EventType;
  message?: string; // Human readable summary
  
  // Raw data from backend (optional, populated for detail view)
  detections?: Detection[];
  imageUrl?: string;
}

export interface SystemMetricEvent {
  id: string;
  timestamp: Date;
  eventType: "system";
  metricType: "cpu_usage" | "memory_usage" | "kafka_lag";
  value: number; // percentage for CPU/Mem, ms or messages for lag
  unit: string; // "%", "MB", "GW", "ms"
  status: "healthy" | "warning" | "critical";
  message?: string;
}

export type AppEvent = DetectionEvent | SystemMetricEvent;
