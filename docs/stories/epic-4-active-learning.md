# Epic 4: Active Learning Loop

**Goal:** Implement the automated feedback loop where human verification triggers model retraining and deployment.

## Story 4.1: Triage API
**As a** Backend Developer,
**I want** an API to retrieve unverified detections and submit human corrections,
**So that** the frontend can present a "Triage Queue" to the operator.

**Acceptance Criteria:**
- [x] Endpoint `GET /api/triage` returns next batch of unverified images from `annotations` table/MinIO.
- [x] Endpoint `POST /api/triage/{id}` accepts validation (`verified: true/false`, `correct_label: "..."`).
- [x] Database schema updated for `annotations` table.

## Story 4.2: Triage Station UI
**As a** Triage Specialist,
**I want** a dedicated interface to rapidly validate images using keyboard shortcuts,
**So that** I can process hundreds of images per hour.

**Acceptance Criteria:**
- [x] New Page `/triage` in the Dashboard.
- [x] Large image display with bounding box overlay.
- [x] Keyboard Controls: Left (No), Right (Yes), Skip (Down).
- [x] Progress bar showing "Images remaining to trigger retrain".

## Story 4.3: Training Controller Logic
**As a** MLOps Engineer,
**I want** a background service that monitors the annotation count,
**So that** it can automatically trigger the retraining job when enough data is collected.

**Acceptance Criteria:**
- [x] Service `training-controller` created.
- [x] Periodically polls DB for count of `verified` annotations.
- [x] If Count > Threshold (e.g. 50), triggers K8s Job `sentinel-training`.
- [x] Prevents concurrent training jobs.

## Story 4.4: Training Job (Docker + Script)
**As a** Data Scientist,
**I want** a Docker container that fine-tunes YOLOv8 on the new dataset,
**So that** the model improves over time.

**Acceptance Criteria:**
- [x] Docker image `sentinel-training` created with PyTorch/Ultralytics.
- [x] Script `train.py`:
    - [x] Downloads dataset + new annotations from MinIO.
    - [x] Runs `yolo train`.
    - [x] Validates mAP on held-out test set.
    - [x] Uploads new `.pt` and `.onnx` model to MinIO (`v{N+1}`).

## Story 4.5: Model Promotion (GitOps Update)
**As a** System Architect,
**I want** the Training Controller to update the deployment configuration automatically upon success,
**So that** the new model goes live without manual intervention.

**Acceptance Criteria:**
- [x] `training-controller` clones the git repo.
- [x] Updates `k8s/apps/values.yaml` (or similar) with `model_version: v{N+1}`.
- [x] Commits and Pushes changes to the `main` branch.
- [x] Verify ArgoCD detects the change and rolls out the Inference Service.
