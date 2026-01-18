# Epic 2: Ingestion & Inference Pipeline

**Status: ✅ COMPLETE**

**Goal:** Build the "Camera Manager" service to ingest video and the "Inference Service" to detect objects, connected via gRPC and Kafka.

## Story 2.1: Camera Service - Video Ingestion ✓
**As a** Backend Developer,
**I want** a service that can connect to both RTSP streams and local video files,
**So that** I can process video regardless of the source type (Live Camera or Simulation).

**Acceptance Criteria:**
- [x] Service `camera-service` created in Python.
- [x] Accepts configuration for `source_url` (RTSP or File path) and `camera_id`.
- [x] Uses OpenCV to read frames reliably (implementation must handle reconnections/EOF).
- [x] Dockerfile optimized for video libraries (minimal size).

## Story 2.2: MediaMTX Restreaming ✓
**As a** Frontend Developer,
**I want** the Camera Service to push video to a localized MediaMTX server,
**So that** I can view the stream in the browser via WebRTC/HLS with low latency.

**Acceptance Criteria:**
- [x] `camera-service` pushes stream to `rtsp://mediamtx:8554/{cam_id}` via FFmpeg subprocess or GStreamer.
- [x] MediaMTX sidecar or service is reachable.
- [x] Verify stream is viewable via VLC (RTSP) or Browser (HLS/WebRTC).

## Story 2.3: Inference Service (YOLOv8) ✓
**As a** ML Engineer,
**I want** a dedicated microservice running YOLOv8,
**So that** I can decouple heavy inference loading from the camera ingestion logic and scale them independently.

**Acceptance Criteria:**
- [x] Service `inference-service` created in Python (using Ultralytics or ONNX Runtime).
- [x] Exposes a gRPC endpoint: `Detect(frame_bytes) -> Detections`.
- [x] Loads `yolov8n.pt` (Nano) model by default for performance.
- [x] Returns bounding boxes, detected classes, and confidence scores.

## Story 2.4: Pipeline Integration & Kafka Publishing ✓
**As a** System Architect,
**I want** the Camera Service to send frames to Inference and publish results to Kafka,
**So that** the system reacts to events in real-time.

**Acceptance Criteria:**
- [x] `camera-service` samples frames at configurable FPS (e.g., 5 FPS) for inference.
- [x] `camera-service` sends sampled frame to `inference-service` via gRPC.
- [x] `inference-service` receives result, formats it as `DetectionEvent` (JSON), and publishes to `events.detections` Kafka topic.
- [x] End-to-End Latency from "Frame Capture" to "Kafka Publish" is monitored and under 200ms.

---

**Epic Completed:** 2026-01-16  
**Retrospective:** [epic-2-retro.md](file:///c:/Users/basti/OneDrive/Bureau/code/antigravity/smart_city_overwiew/smart_city_traffic_overview/docs/stories/epic-2-retro.md)

