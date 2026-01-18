# Epic 1: Foundation & Core Infrastructure

**Goal:** Establish the Kubernetes cluster, GitOps setup (ArgoCD), Message Bus (Redpanda/Kafka), and Object Storage (MinIO). Deploy a "Hello World" service to prove the pipeline.

## Story 1.1: Infrastructure Setup (K8s & ArgoCD)
**As a** DevOps Engineer,
**I want** to provision a local Kubernetes cluster and install ArgoCD,
**So that** I have a GitOps-ready environment for deploying my microservices.

**Acceptance Criteria:**
- [ ] Local K8s cluster (Minikube or K3s) is running and stable.
- [ ] ArgoCD is installed in the `argocd` namespace.
- [ ] `docs/architecture/source-tree.md` is updated to reflect the infra structure.
- [ ] A root `Application` (App of Apps) is configured in ArgoCD pointing to `k8s/`.

## Story 1.2: Message Bus Deployment (Redpanda)
**As a** Backend Developer,
**I want** a high-performance Kafka-compatible event bus,
**So that** services can publish and subscribe to detection events with low latency.

**Acceptance Criteria:**
- [ ] Redpanda installed via Helm Chart (managed by ArgoCD).
- [ ] Accessible internally at `redpanda.redpanda.svc.cluster.local:9093`.
- [ ] Topic `events.detections` is automatically created with appropriate retention policy (e.g., 1 hour or 1GB).
- [ ] "Internal Console" (Redpanda Console) is available for debugging topics.

## Story 1.3: Object Storage Deployment (MinIO)
**As a** ML Engineer,
**I want** a local S3-compatible object storage system,
**So that** I can archive anomaly video clips and manage model artifacts.

**Acceptance Criteria:**
- [ ] MinIO installed via Helm Chart (managed by ArgoCD).
- [ ] Buckets created: `sentinel-models`, `sentinel-clips`, `sentinel-datasets`.
- [ ] Access Keys/Secrets stored in K8s Secrets (`minio-creds`).
- [ ] MinIO Console accessible via port-forward.

## Story 1.4: Hello World Pipeline Verification
**As a** Developer,
**I want** to deploy a simple "Hello World" service via the full GitOps pipeline,
**So that** I can verify that ArgoCD, the container registry, and the cluster networking are working correctly before building complex services.

**Acceptance Criteria:**
- [ ] A simple HTTP service (e.g., Nginx or Python echo) defined in `services/hello-world`.
- [ ] K8s manifests created in `k8s/apps/hello-world`.
- [ ] Service deployed via ArgoCD.
- [ ] Endpoint accessible via Ingress or Port-Forward returning "200 OK".
