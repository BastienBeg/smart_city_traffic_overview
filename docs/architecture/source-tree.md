# Project Source Tree Structure

This document defines the **Target** directory structure for the **Smart City Sentinel** monorepo. It serves as the blueprint for development.
**Note to Agents:** If a directory listed here does not exist, you **MUST** create it when implementing a related feature. Do not create empty folders prematurely, but ALWAYS follow this structure when adding new files.

## Root Directory Overview

```text
smart-city-sentinel/
├── .bmad-core/             # Agent definitions, tasks, and core configuration
├── .github/                # GitHub Actions workflows (CI/CD)
├── docs/                   # Project documentation (Architectural, Product, Standards)
├── infra/                  # Infrastructure as Code (Terraform)
├── k8s/                    # Kubernetes Manifests (Helm/Kustomize/Raw)
├── scripts/                # Utility scripts (local dev, setup, db migrations)
└── services/               # Microservices Source Code (One directory per service)
```

## Detailed Directory Definitions

### 1. Services (`services/`)
Each subdirectory corresponds to a deployable unit or shared library.

*   `services/api-gateway/` - **FastAPI** backend.
    *   `src/main.py`: Entry point.
    *   `src/routers/`: API endpoints (cameras, events).
*   `services/camera-service/` - **Python** service for ingestion.
    *   `src/stream.py`: OpenCV/FFmpeg logic for RTSP/File handling.
*   `services/inference-service/` - **Python** YOLOv8 Wrapper.
    *   `src/model.py`: ONNX Runtime / Ultralytics wrapper.
    *   `protos/`: gRPC definitions for frame transfer.
*   `services/training-controller/` - **Python** Service.
    *   `src/monitor.py`: Watches DB/MinIO for trigger conditions.
    *   `src/k8s_manager.py`: Triggers the K8s Job.
*   `services/training-job/` - **Python** Ephemeral Job (Dockerized).
    *   `train.py`: The script that actually runs `yolo train`.
*   `services/web-dashboard/` - **Next.js** Frontend.
    *   `app/`: App Router pages (Dashboard, Triage).
    *   `components/`: Reusable UI (VideoPlayer, EventLog).
*   `services/common-lib/` - **Python** Shared Library.
    *   `schemas/`: Shared Pydantic models (DetectionEvent).
    *   `utils/`: Shared loggers or Kafka wrappers.
*   `services/hello-world/` - (Temporary) Verification service.

**Standard Service Structure:**
```text
services/<service-name>/
├── src/ (or app/)          # Source code
├── tests/                  # Unit and Integration tests
├── Dockerfile              # Production Dockerfile
├── requirements.txt        # (Python) Dependencies
└── package.json            # (Node) Dependencies
```

### 2. Kubernetes Manifests (`k8s/`)
Follows a GitOps structure compatible with ArgoCD.

*   `k8s/apps/` - Application manifests (Helm Charts or Raw YAML).
    *   `k8s/apps/<service-name>/base/`: Deployment, Service, ConfigMap.
    *   `k8s/apps/<service-name>/overlays/`: Environment patches.
*   `k8s/infra/` - Infrastructure components.
    *   `k8s/infra/redpanda/`: Helm Chart values for Message Bus.
    *   `k8s/infra/minio/`: Helm Chart values for Object Storage.
    *   `k8s/infra/postgres/`: Database manifests.
    *   `k8s/infra/argocd/`: GitOps controller setup.
*   `k8s/jobs/` - CronJobs or One-off Jobs.
    *   `k8s/jobs/training-job.yaml`: Template for the retraining job.

### 3. Documentation (`docs/`)
*   `docs/architecture/` - Technical specifications.
*   `docs/stories/` - Agile user stories (Epics 1-4).
*   `docs/qa/` - Quality Assurance plans.
*   `docs/prd.md` - Product Requirements Document.
*   `docs/architecture.md` - High-level system architecture.

### 4. Infrastructure (`infra/`)
Terraform configuration for provisioning the underlying cluster resources.

*   `infra/main.tf` - Entry point (Minikube/K3s provisioning or Cloud).
*   `infra/variables.tf` - Configurable inputs.

---

## Epic to Source Mapping

This table certifies that every Epic's functionality has a specific home in the source tree.

| Epic | Functionality | Primary Source Directory | Supporting Infrastructure |
| :--- | :--- | :--- | :--- |
| **Epic 1** | **Foundation** | `services/hello-world/` | `infra/`, `k8s/infra/` (Redpanda, MinIO, ArgoCD) |
| **Epic 2** | **Ingestion** | `services/camera-service/` | `k8s/apps/camera-service/` |
| **Epic 2** | **Inference** | `services/inference-service/` | `k8s/apps/inference-service/`, `services/common-lib/` |
| **Epic 3** | **Frontend (Dashboard)** | `services/web-dashboard/` | `services/api-gateway/`, `k8s/apps/web-dashboard/` |
| **Epic 3** | **Real-time API** | `services/api-gateway/` | `k8s/apps/api-gateway/` |
| **Epic 4** | **Triage API** | `services/api-gateway/` | `k8s/infra/postgres/` |
| **Epic 4** | **Active Learning Logic** | `services/training-controller/` | `k8s/apps/training-controller/` |
| **Epic 4** | **Retraining Job** | `services/training-job/` | `k8s/jobs/training-job.yaml` |
