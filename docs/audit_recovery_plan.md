# Audit & Recovery Plan: Smart City Sentinel

## Objective
Reach a "True Done" state defined by:
1. **Video Proof**: Complete end-to-end demo recorded locally.
2. **Scale**: 10 simultaneous live cameras from the same city.
3. **No Mocks**: Full integration (RTSP -> Inference -> Kafka -> DB -> Frontend).
4. **Prod Environment**: Fully running on local Kubernetes cluster.

## Phase 1: Exhaustive Audit Checklist

### 1. Infrastructure & Deployment (The Foundation)
- [ ] **Kubernetes Cluster**: Verify status (nodes, health, resources).
- [ ] **ArgoCD**: Verify installation, app sync status, and repo connection.
- [ ] **Core Services**:
    - [ ] Redpanda: Verify reachability, topic creation, and persistence.
    - [ ] MinIO: Verify bucket creation, access policies, and persistence.
    - [ ] Database: Verify PostgreSQL schema migration and data persistence.
- [ ] **Helm/Kustomize**: Audit manifest validity and environment variable injection.

### 2. Service Layer (The Backend)
- [ ] **Camera Service**:
    - [ ] Does it handle RTSP reconnections gracefully?
    - [ ] Can it handle 10 concurrent streams on local hardware?
    - [ ] Memory leak check.
- [ ] **Inference Service**:
    - [ ] Throughput check (FPS per stream).
    - [ ] Latency check (Camera -> Detection).
- [ ] **Training Controller**:
    - [ ] Verify GitOps logic without mocking (dry-run against real repo).
- [ ] **API Gateway**:
    - [ ] Verify all endpoints map to real services (Identify mock routers).

### 3. Data Pipeline (The Flow)
- [ ] **Event Flow**: Verify `DetectionEvent` JSON structure matches Frontend expectations.
- [ ] **Storage**: Verify images are actually saved to MinIO and paths are correct in DB.
- [ ] **Lag**: specific measurement of end-to-end latency (Action to Screen).

### 4. Frontend (The Operator Experience)
- [ ] **Mock Hunt**: Grep for `MOCK_`, `faker`, hardcoded JSONs.
- [ ] **Video Player**: Stability check with HLS/WebRTC under load (10 streams).
- [ ] **Triage UI**: Verify "Validate" button actually hits the API and updates DB.
- [ ] **Dashboard**: Verify "Event Log" is driven by WebSocket/SSE, not loops.

### 5. Codebase Hygiene
- [ ] **Cleanup**: Identify unused files, scripts, and "experiment" folders.
- [ ] **Secrets**: Scan for hardcoded passwords/tokens.
- [ ] **Tests**: Audit *value* of tests (are they just testing mocks or real logic?).

## Phase 2: Remediation Plan (Draft)
*Will be populated after Audit Phase.*

1. **Infrastructure Fixes**: get the environment stable.
2. **De-Mocking**: rewire usage of real APIs.
3. **Performance Tuning**: Optimize for 10 streams.
4. **Integration Testing**: End-to-End verification.

## Phase 3: The "Golden Run"
1. **Scenario**: "Traffic Congestion Event"
2. **Setup**: 10 Live Streams.
3. **Action**: Detection -> Alert -> Triage -> Retrain Trigger.
4. **Proof**: Recorded Screen Capture.

---
**Next Step**: Execute Phase 1 Audit immediately.
