# PM Request: Architecture Update (v1.2)
**To:** Architect Agent
**From:** PM Agent
**Date:** 2026-01-10

## Context
I have reviewed `docs/architecture.md` against the PRD and Frontend Spec. While the foundation is solid, we are missing critical backend details to support the **Active Learning Loop** (Triage) and the **MLOps Pipeline**.

Please update `docs/architecture.md` to include the specifications below.

## 1. MLOps & Retraining Pipeline
**Gap:** The specific mechanics of *how* retraining is triggered and orchestrated are missing. "ArgoCD" handles deployment, but not the training workflow.
**Requirement:** Add a dedicated section specifying:
*   **Training Controller:** A mechanism (e.g., K8s CronJob or Background Service) that checks if there are >50 new annotated images.
*   **Training Job:** A K8s Job definition (Docker Image: `sentinel-training:latest` with GPU support).
*   **Model Registry:** Models should be saved to MinIO at `s3://sentinel-models/v{n}/`.
*   **Deployment Trigger:** The pipeline must end with a "Git Commit" step (updating `values.yaml` with the new model version) to trigger ArgoCD.

## 2. Triage API Specification
**Gap:** The Frontend needs to fetch images to label and submit results.
**Requirement:** Add the following endpoints to the REST API Spec:
*   `GET /api/triage/queue`: Fetch a batch of pending images.
*   `POST /api/triage/{id}/validate`: Submit user annotation (True/False/Fixed Label).
*   `POST /api/pipeline/trigger` (Optional): Manually force a retraining run.

## 3. Data Models
**Gap:** Schemas are undefined for persistent storage.
**Requirement:** Add PostgreSQL schemas for:
*   `detections`: The raw events.
*   `annotations`: The user feedback (linked to a detection or frame).
*   `jobs`: History of training runs (status, accuracy metrics).

## 4. Recommendations
*   Keep the existing "Event Driven" style.
*   Ensure the "Triage Service" is logically placed (likely inside the `api-service` module or a small microservice).
