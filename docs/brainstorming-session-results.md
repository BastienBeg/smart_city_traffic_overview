# Brainstorming Session Results

**Session Date:** 2026-01-09
**Facilitator:** Business Analyst Mary
**Participant:** User

## Executive Summary

**Topic:** MLOps & Deep Learning Portfolio Project
**Session Goals:** Progressive exploration (Broad -> Narrow) to find a project with heavy MLOps, Visuals, and Active Learning components.
**Techniques Used:** Progressive Flow
**Total Ideas Generated:** TBD

---

## Technique Sessions

### 1. Divergent Phase: Domain Exploration
    *   *Feasibility:* Lower quality public data (often staged).

### Selection
**Selected Domain:** **Urban/Smart City Traffic Anomaly Detection**
*   **Rationale:** Perfect balance of "Wow" factor (visual dashboard, live feeds), MLOps complexity (managing video streams), and data availability (KITTI/CityFlow).

---

### 2. Convergent Phase: Project Definition
**Description:** Defining the specific mechanics, tech stack, and user flow for the Smart City Sentinel project.

**Refined Feature Set:**

    *   *Fallback:* If live streams are unstable, use "Simulated Live" (looping HD traffic footage) that *behaves* exactly like a live RTSP stream to the system. This ensures the demo works even if the internet is down.

2.  **Infrastructure (The Full K8s Portfolio Piece):**
    *   **Scope:** Everything runs on Kubernetes (Minikube/K3s).
    *   **Cluster Management:** Pods auto-scale based on simulated traffic load.
    *   **Services:**
        *   `Frontend`: Next.js Dashboard (User Interface).
        *   `Backend`: FastAPI/Go (API Gateway).
        *   `Inference`: KServe or Seldon Core (Serving the Model).
        *   `Stream Processors`: Individual Pods consuming camera feeds.
        *   `Monitoring`: Prometheus/Grafana (Cluster health) + MLflow (Model metrics).

3.  **Feature Logic: City & Camera Management:**
    *   **Dynamic Provisioning:** A UI panel to "Add City" or "Add Camera".
    *   **Result:** Backend dynamically provisions a new K8s Deployment for that camera stream.
    *   **Archive:** Option to "Stop Recording" archives video segments to MinIO/S3.

4.  **The Active Learning Loop (Automated & Reliable):**
    *   **Trigger:** Model confidence < 0.6 -> Save frame to "Triage Queue".
    *   **Human Step:** User annotates image in UI (or integrated tool like Label Studio).
    *   **Automation:**
        1.  Once 50 new images are labeled, a **GitLab CI/GitHub Action** is triggered.
        2.  Job: Retrain model (Transfer Learning) -> Validate -> Push to Registry.
        3.  K8s performs a "Canary Deployment" of the new model.

### 3. Tech Stack Recommendations (CV Boosters)
*To maximize portfolio impact without over-engineering:*

*   **Kafka / Redpanda:** Use for the *Event Bus*. Camera pods produce "FrameEvents", Inference pods consume them, Alert pods consume "AnomalyEvents".
    *   *Why:* Essential for modern high-throughput data pipelines.
*   **Terraform:** Use to spin up the underlying infrastructure (even if it's just local Kind/Minikube configs or a cloud demo).
    *   *Why:* Shows "Infrastructure as Code" mastery.
*   **MinIO:** Self-hosted S3-compatible storage for the video archives and datasets.
    *   *Why:* Shows you know how to handle Object Storage in a cloud-native way.
*   **ArgoCD:** For GitOps deployment (Proposed).
    *   *Why:* The gold standard for K8s CD.

### 4. Action Plan
*   **Next Step:** Handover to **Product Manager (PM) Agent**.
*   **Goal:** Create a formal `docs/prd.md` based on this results document.
*   **Why:** The PM will transform these "Brainstorming Notes" into a structured "Product Requirements Document" that defines the exact User Stories and Acceptance Criteria for the Architect to build.
