# Smart City Sentinel Product Requirements Document (PRD)

| Date | Version | Description | Author |
| :--- | :--- | :--- | :--- |
| 2026-01-09 | v1.0 | Initial Draft based on Brainstorming Session | PM Agent |

## 1. Goals and Background Context

### 1.1 Goals
*   **Showcase MLOps Mastery:** Demonstrate a complete, end-to-end machine learning lifecycle including deployment, monitoring, and automated retraining.
*   **Visual Impact:** Create a "Wow" factor with a real-time, visually engaging dashboard displaying live (or simulated) traffic analysis.
*   **Active Learning Loop:** Implement a fully automated pipeline where human feedback triggers model retraining and deployment without manual intervention.
### 1.1 Goals
*   **Showcase MLOps Mastery:** Demonstrate a complete, end-to-end machine learning lifecycle including deployment, monitoring, and automated retraining.
*   **Visual Impact:** Create a "Wow" factor with a real-time, visually engaging dashboard displaying live (or simulated) traffic analysis.
*   **Active Learning Loop:** Implement a fully automated pipeline where human feedback triggers model retraining and deployment without manual intervention.
*   **Source Agnostic Ingestion:** The architecture handles Live RTSP streams and Recorded File streams identically. This allows for robust demos (offline mode) and scalability testing (adding fake cameras alongside real ones) without code changes.
*   **Cloud Native:** Utilize a full Kubernetes-native stack (Minikube/K3s) with GitOps principles.

### 1.2 Background Context
The "Smart City Sentinel" project is designed as a high-impact portfolio piece. It addresses the domain of smart city management, specifically traffic anomaly detection (accidents, congestion, wrong-way drivers). The core problem is processing real-time video feeds to identify disparate events and managing the lifecycle of the models that do this detection.
Unlike simple "notebook" projects, this system simulates a production environment. It handles potential network instability (using simulated live streams), manages high-throughput data with Kafka, and ensures model reliability through automated retraining pipelines.

## 2. Requirements

### 2.1 Functional Requirements (FR)
*   **FR1:** The system must ingest video streams from **any standard source** (RTSP URL for live, HTTP/File URL for simulation).
*   **FR2:** The system must detect vehicles and anomalies (e.g., stopped cars, collisions) using a Deep Learning model (e.g., YOLOv8).
*   **FR3:** The system must display real-time video feeds with collecting bounding boxes and anomaly alerts on a web dashboard.
*   **FR4:** The system must allow users to view "Triage" images (low confidence detections) and annotate them.
*   **FR5:** The system must automatically trigger a re-training pipeline when a threshold of new annotations (e.g., 50 images) is reached.
*   **FR6:** The system must automatically deploy the new model version using a canary or rolling update strategy after successful training.
*   **FR7:** The system must archive video segments of detected anomalies to object storage (MinIO).
*   **FR8:** The system must allow adding cameras by simply providing a connection string (RTSP or File Path), treating both inputs identically.

### 2.2 Non-Functional Requirements (NFR)
*   **NFR1:** The system must run entirely on a local Kubernetes cluster (Minikube or K3s).
*   **NFR2:** The architecture must be resilient to "camera" failures (simulating network drops).
*   **NFR3:** The UI must be responsive and capable of displaying at least 4 simultaneous low-latency video streams.
*   **NFR4:** All major infrastructure components must be defined as Code (Terraform/Helm).
*   **NFR5:** The system should use GitOps (ArgoCD) for deployment state synchronization.

## 3. User Interface Design Goals

### 3.1 Overall UX Vision
**Style:** "Cyberpunk Control Center" mixed with "Modern SaaS". Dark mode, high contrast, neon accents for alerts (Red) and healthy statuses (Green).
**Feel:** Professional, dense with information but organized. The user should feel like a city operator.

### 3.2 Key Screens
1.  **Mission Control (Dashboard):** Grid of live camera feeds. Real-time scrolling log of events. System health status gauges (CPU, Memory, Kafka lag).
2.  **Camera Management:** Map view or List view to add/remove simulated cameras.
3.  **Triage Station:** specialized interface for rapid image annotation (Yes/No/Correct Label). Progress bar showing "Images until next Retrain".
4.  **MLOps Pipeline View:** Visual representation of the model lifecycle status (Training -> Validating -> Deploying).

### 3.3 Target Platforms
*   **Web Desktop:** Optimised for large screens (1080p+).

## 4. Technical Assumptions

*   **Repository Structure:** Monorepo (Simpler for portfolio coordination).
*   **Service Architecture:** Microservices on Kubernetes.
    *   *Frontend:* Next.js
    *   *Backend:* FastAPI (Python) or Go
    *   *ML Inference:* KServe or Seldon Core
    *   *Message Bus:* Kafka (or Redpanda)
    *   *Storage:* MinIO (Object), PostgreSQL (Metadata)
*   **Testing:**
    *   Unit tests for backend logic.
    *   Integration tests for the Kafka <-> Service flow.
*   **Infrastructure:** Terraform for local K8s provisioning, Helm for app charts.

## 5. Epic List

*   **Epic 1: Foundation & Core Infrastructure**
    *   *Goal:* Establish the Kubernetes cluster, GitOps setup (ArgoCD), Message Bus (Redpanda/Kafka), and Object Storage (MinIO). Deploy a "Hello World" service to prove the pipeline.
*   **Epic 2: Ingestion & Inference Pipeline**
    *   *Goal:* Build the "Camera Manager" service that can consume both **Live RTSP URLs** and **Local File Loops**. Implement the YOLOv8 inference engine and publish "DetectionEvents" to Kafka.
*   **Epic 3: Mission Control Frontend**
    *   *Goal:* Create the Next.js visual dashboard to consume real-time events and stream video (WebRTC or HLS). Identify anomalies visually.
*   **Epic 4: Active Learning Loop**
    *   *Goal:* Implement the "Triage" UI, the data collection mechanism, and the automated CI/CD job to retrain and redeploy the model.

## 6. Next Steps

### UX Expert Prompt
> "Review the 'Mission Control' and 'Triage Station' concepts. detailed wireframes are not needed, but a high-fidelity component guide for the dark-mode dashboard is required. Focus on how to display multiple video streams without overwhelming the browser."

### Architect Prompt
> "Design the Microservices architecture for Kubernetes. Specific focus on:
> 1. How video frames flow from 'Camera Pod' -> 'Inference' -> 'Frontend' (should we use WebRTC or MJPEG?).
> 2. The Kafka topic schema for DetectionEvents.
> 3. The ArgoCD + CI/CD configuration for the automatic model rollout."
