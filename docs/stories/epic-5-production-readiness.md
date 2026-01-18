# Epic 5: Production Readiness & Portfolio Demo

**Goal:** Achieve a fully functional, production-quality system deployable on Kubernetes with 10+ simultaneous camera feeds, zero mocks, and a recorded video demonstration.

**Exit Criteria:**
- [ ] All services deployed and healthy in Kubernetes
- [ ] 10 live camera feeds streaming simultaneously
- [ ] End-to-end pipeline working (Detection → Event → UI)
- [ ] Triage → Retrain loop tested
- [ ] Video proof recorded

---

## Story 5.0: K8s Manifest Scaffolding ⚠️ PREREQUISITE
**Agent:** `/architect` + `/dev`

**As a** DevOps Engineer,
**I want** all missing Kubernetes manifests created,
**So that** the application can be deployed to the cluster.

**Blocking Issues Identified by Architect:**
| Gap | Description |
|-----|-------------|
| 4 Missing K8s Manifests | api-gateway, camera-service, training-controller, web-dashboard |
| No PostgreSQL in K8s | DB deployment manifest missing |
| No web-dashboard Dockerfile | Frontend cannot be containerized |

**Acceptance Criteria:**
- [ ] PostgreSQL StatefulSet + Service manifest created (`k8s/infra/postgresql/`)
- [ ] MinIO added to infra kustomization (already exists but not linked)
- [ ] K8s Deployment manifests for:
    - [ ] `k8s/apps/api-gateway/`
    - [ ] `k8s/apps/camera-service/`
    - [ ] `k8s/apps/training-controller/`
    - [ ] `k8s/apps/web-dashboard/`
- [ ] Dockerfile created for `services/web-dashboard/Dockerfile`
- [ ] Ingress controller manifest added for external access
- [ ] All manifests pass `kustomize build` validation

**Estimated Effort:** 11 Story Points

**Tasks:**
1. `/architect`: Design manifest structure and ConfigMaps
2. `/dev`: Create PostgreSQL StatefulSet with PVC
3. `/dev`: Create Deployment + Service for each app service
4. `/dev`: Create web-dashboard Dockerfile (Next.js production build)
5. `/dev`: Add Ingress routes for dashboard and API
6. `/qa`: Validate with `kustomize build k8s/`

---

## Story 5.1: Infrastructure Deployment & Health Check
**Agent:** `/dev`
**Prereq:** Story 5.0 done

**As a** DevOps Engineer,
**I want** all core infrastructure deployed and healthy in Kubernetes,
**So that** the application services have a stable foundation.

**Acceptance Criteria:**
- [ ] ArgoCD installed and syncing the root application
- [ ] Redpanda running with `events.detections` topic created
- [ ] MinIO running with buckets: `sentinel-models`, `sentinel-clips`, `sentinel-datasets`
- [ ] PostgreSQL running with schema initialized
- [ ] All pods in `Running` state with no CrashLoopBackOff

**Tasks:**
1. Apply ArgoCD and root application
2. Verify infrastructure pods
3. Create required topics/buckets
4. Run DB migration

---

## Story 5.2: Service Deployment Validation
**Agent:** `/dev`
**Prereq:** Story 5.1 done

**As a** Backend Developer,
**I want** all application services deployed correctly,
**So that** the system can process video streams.

**Acceptance Criteria:**
- [ ] `camera-service` deployment ready
- [ ] `inference-service` deployment ready (with YOLO model loaded)
- [ ] `api-gateway` deployment ready (endpoints accessible)
- [ ] `training-controller` deployment ready
- [ ] `web-dashboard` deployment ready (frontend accessible)
- [ ] MediaMTX sidecar/deployment ready

**Tasks:**
1. Build and push Docker images (local registry or Docker Hub)
2. Apply app manifests via ArgoCD
3. Verify pod logs for startup errors
4. Test service connectivity

---

## Story 5.3: De-Mocking Backend APIs
**Agent:** `/dev` + `/qa`
**Prereq:** Story 5.2 done

**As a** System Architect,
**I want** all mock data removed from production code,
**So that** the system uses real data flows.

**✅ Positive Finding:** Architect confirmed backend APIs already use real DB queries.

**Remaining Checks:**
- [ ] Camera list comes from configuration/DB (not hardcoded)
- [ ] WebSocket events come from Kafka (not fake timers)
- [ ] Frontend API client points to real endpoints

**Audit Files:**
- `services/api-gateway/src/routers/cameras.py`
- `services/web-dashboard/src/lib/api.ts`

---

## Story 5.4: Frontend Real Data Integration
**Agent:** `/dev`
**Prereq:** Story 5.3 done

**As a** Frontend Developer,
**I want** the dashboard to consume real backend data,
**So that** the UI reflects actual system state.

**Acceptance Criteria:**
- [ ] API base URL configured for K8s service (via env var or Ingress)
- [ ] Camera grid shows real MediaMTX streams
- [ ] Event log displays real Kafka events via WebSocket
- [ ] Triage UI loads real unverified detections
- [ ] Map shows cameras from real configuration

---

## Story 5.5: 10-Camera Stress Test
**Agent:** `/dev` + `/qa`
**Prereq:** Stories 5.1-5.4 done

**As a** Performance Engineer,
**I want** to verify the system handles 10 simultaneous camera feeds,
**So that** the demo is impressive and stable.

**Acceptance Criteria:**
- [ ] 10 public RTSP/HLS streams configured
- [ ] All 10 streams visible in Dashboard grid
- [ ] Inference runs on all 10 without OOM
- [ ] Latency < 3 seconds capture → display
- [ ] No pod crashes after 10 minutes

**Camera Sources:**
- Iowa DOT / Caltrans public streams
- Fallback: Local video loop via MediaMTX

---

## Story 5.6: End-to-End Pipeline Test
**Agent:** `/qa`
**Prereq:** Story 5.5 done

**As a** QA Engineer,
**I want** to verify the complete data flow,
**So that** we have confidence for the demo.

**Test Scenario:**
1. Camera → Inference → Detection
2. Kafka → API Gateway → WebSocket → Frontend
3. Low-confidence → Triage Queue
4. Human validates → Annotation stored
5. Threshold → Training triggered
6. GitOps → Model promoted

---

## Story 5.7: Codebase Cleanup
**Agent:** `/dev`
**Can run in parallel**

**As a** Developer,
**I want** a clean, professional repository,
**So that** it's portfolio-ready.

**Acceptance Criteria:**
- [ ] Remove unused/temp files
- [ ] Remove debug print statements
- [ ] `.gitignore` covers all artifacts
- [ ] `README.md` with setup instructions
- [ ] No committed secrets

---

## Story 5.8: Video Demo Recording
**Agent:** User (Manual)
**Prereq:** All stories done

**Demo Script:**
1. **Intro (30s):** Architecture overview
2. **Dashboard (60s):** 10 cameras, live detections
3. **Map (30s):** Geospatial camera view
4. **Triage (60s):** Keyboard-driven validation
5. **Training (30s):** Job trigger demo
6. **GitOps (30s):** ArgoCD sync
7. **Outro (15s):** Summary

---

## Execution Order (Updated)

| Step | Story | Agent | Prereqs |
|------|-------|-------|---------|
| 1 | **5.0** | `/architect` + `/dev` | Cluster access |
| 2 | 5.1 | `/dev` | 5.0 done |
| 3 | 5.2 | `/dev` | 5.1 done |
| 4 | 5.3 | `/dev` + `/qa` | 5.2 done |
| 5 | 5.4 | `/dev` | 5.3 done |
| 6 | 5.7 | `/dev` | Parallel |
| 7 | 5.5 | `/dev` + `/qa` | 5.1-5.4 done |
| 8 | 5.6 | `/qa` | 5.5 done |
| 9 | 5.8 | User | All done |

---

## Quick Reference: Agent Commands

```bash
# Story 5.0 - Create missing manifests
@[/architect] Design K8s manifest structure for Story 5.0
@[/dev] Implement Story 5.0 - Create K8s manifests and Dockerfiles

# Story 5.1 - Deploy infrastructure
@[/dev] Implement Story 5.1 - Deploy and verify infrastructure

# And so on...
```

---

**Status:** Updated with Architect recommendations (2026-01-18)
**Next Action:** Start Story 5.0 with `/dev`

---

## Story 5.0 - QA Results

### Review Date: 2026-01-18

### Reviewed By: Quinn (Test Architect)

### Code Quality Assessment

**Overall: EXCELLENT** - All required K8s manifests have been created following Kubernetes best practices:

- **PostgreSQL StatefulSet**: Properly configured with PVC (5Gi), liveness/readiness probes, secrets, and init scripts via ConfigMap
- **All App Deployments**: api-gateway, camera-service, training-controller, web-dashboard created with appropriate resource limits, environment variables, and probes
- **Ingress Controller**: Proper path-based routing for dashboard (/), API (/api), and streams (/stream)
- **Dockerfile**: Multi-stage Next.js build with non-root user (security best practice)

### Acceptance Criteria Validation

| AC | Status | Notes |
|----|--------|-------|
| PostgreSQL StatefulSet + Service | ✅ | `k8s/infra/postgresql/` with PVC |
| MinIO added to kustomization | ✅ | Linked in `k8s/infra/kustomization.yaml` |
| api-gateway manifest | ✅ | `k8s/apps/api-gateway/base/` |
| camera-service manifest | ✅ | `k8s/apps/camera-service/base/` |
| training-controller manifest | ✅ | Includes RBAC (ServiceAccount, Role, RoleBinding) |
| web-dashboard manifest | ✅ | `k8s/apps/web-dashboard/base/` |
| Dockerfile for web-dashboard | ✅ | Multi-stage, non-root user |
| Ingress manifest | ✅ | NGINX routes for all services |
| Kustomize build validation | ✅ | All app manifests pass validation |

### Compliance Check

- Coding Standards: ✅ Consistent YAML formatting and labeling
- Project Structure: ✅ Follows `k8s/apps/<service>/base/` and `k8s/infra/` conventions
- Security: ✅ Secrets used for credentials, non-root container user
- All ACs Met: ✅ All 8 acceptance criteria satisfied

### Security Review

- ✅ Database credentials stored in Kubernetes Secrets
- ✅ MinIO credentials via SecretKeyRef
- ✅ Non-root user in web-dashboard Dockerfile
- ✅ RBAC properly scoped for training-controller

### Observations (Non-Blocking)

- [ ] Consider adding NetworkPolicies for service isolation (future enhancement)
- [ ] Consider adding PodDisruptionBudgets for production HA
- [ ] `image: xxx:latest` tags should be replaced with specific versions for production

### Gate Status

**Gate: PASS** → `docs/qa/gates/5.0-k8s-manifest-scaffolding.yml`

### Recommended Status

✅ **Ready for Done** - All acceptance criteria met, manifests validated
