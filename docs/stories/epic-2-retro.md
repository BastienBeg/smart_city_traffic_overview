# Epic 2 Retrospective: Ingestion & Inference Pipeline

**Sprint Completed:** 2026-01-16  
**Facilitator:** Bob (Scrum Master)

---

## 📊 Epic Summary

| Metric | Value |
|--------|-------|
| Stories Completed | 4/4 |
| Total QA Gates | 4 PASS |
| Average Quality Score | 95+ |
| Critical Blockers | 0 |

---

## ✅ What Went Well

### 1. Clean Service Architecture
- **Camera Service** (`services/camera-service/`) implemented with robust reconnection logic
- **Inference Service** (`services/inference-service/`) properly decoupled with gRPC interface
- Clear separation of concerns between ingestion, inference, and event publishing

### 2. Strong Integration Patterns
- gRPC for sync frame transfer (low latency)
- Kafka for async event publishing (decoupled consumers)
- MediaMTX for RTSP restreaming (browser compatibility via WebRTC/HLS)

### 3. Infrastructure Readiness
- Kubernetes manifests follow Kustomize pattern (`base/` + `overlays/dev/`)
- Redpanda deployed and operational from Epic 1 foundation
- MediaMTX integrated for live stream viewing

### 4. Quality Assurance Excellence
- All stories passed QA gates on review
- Comprehensive unit tests with proper mocking
- Integration test script (`scripts/test-pipeline-integration.sh`) validates E2E flow

---

## ⚠️ Challenges Faced

| Story | Challenge | Resolution |
|-------|-----------|------------|
| 2.2 | FFmpeg process crash recovery | Added self-healing logic to restart FFmpeg subprocess |
| 2.3 | Missing type hints/docstrings | QA refactored to meet coding standards |
| 2.4 | Initial CONCERNS gate (integration incomplete) | Added docker-compose.yml and test script |

---

## 📈 Key Learnings

1. **Integration Testing is Critical**
   - Story 2.4 initially had CONCERNS due to incomplete E2E verification
   - Lesson: Include docker-compose integration tests as part of AC verification

2. **Standards Enforcement Works**
   - QA reviews caught missing docstrings and type hints
   - Refactoring during review maintains code quality

3. **Configuration via Environment Variables**
   - All services use env vars (`CAMERA_ID`, `SOURCE_URL`, `INFERENCE_FPS`, `KAFKA_BOOTSTRAP_SERVERS`)
   - Enables flexible deployment across environments

---

## 📋 Stories Delivered

| Story | Title | Status | Gate | Quality |
|-------|-------|--------|------|---------|
| [2.1](file:///c:/Users/basti/OneDrive/Bureau/code/antigravity/smart_city_overwiew/smart_city_traffic_overview/docs/stories/2.1.story.md) | Camera Service - Video Ingestion | Done | PASS | High |
| [2.2](file:///c:/Users/basti/OneDrive/Bureau/code/antigravity/smart_city_overwiew/smart_city_traffic_overview/docs/stories/2.2.story.md) | MediaMTX Restreaming | Done | PASS | High |
| [2.3](file:///c:/Users/basti/OneDrive/Bureau/code/antigravity/smart_city_overwiew/smart_city_traffic_overview/docs/stories/2.3.story.md) | Inference Service (YOLOv8) | Done | PASS | High |
| [2.4](file:///c:/Users/basti/OneDrive/Bureau/code/antigravity/smart_city_overwiew/smart_city_traffic_overview/docs/stories/2.4.story.md) | Pipeline Integration & Kafka Publishing | Done | PASS | 95 |

---

## 🔮 Recommendations for Epic 3

1. **Connection Pooling** - Story 2.4 recommended adding this for high-throughput scenarios
2. **Prometheus Metrics** - Add observability for production monitoring
3. **pytest Migration** - Migrate remaining `unittest` tests to `pytest` for consistency
4. **MediaMTX Liveness Probe** - Add to K8s deployment for resilience

---

## 🎯 Epic Goal Achievement

> **Goal:** Build the "Camera Manager" service to ingest video and the "Inference Service" to detect objects, connected via gRPC and Kafka.

**Status: ✅ ACHIEVED**

The complete ingestion and inference pipeline is operational:
- Video ingestion from RTSP streams or local files
- Live stream restreaming via MediaMTX
- YOLOv8 inference via gRPC
- Detection events published to Kafka (`events.detections`)
- End-to-end latency monitoring under 200ms

---

*Retrospective facilitated by Bob (Scrum Master) - 2026-01-16*
