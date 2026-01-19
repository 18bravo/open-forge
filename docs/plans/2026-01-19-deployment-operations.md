# Gate 9: Deployment & Operations Plan

**Date:** 2026-01-19
**Status:** In Progress
**Target Gate:** Gate 9 (Post-LangChain Integration)

---

## Executive Summary

This plan prepares Open Forge for production deployment with Kubernetes infrastructure, CI/CD automation, comprehensive monitoring, and complete documentation. The goal is production-readiness with enterprise-grade reliability.

---

## Work Packages

### WP1: Kubernetes Infrastructure

**Duration:** 1-2 weeks
**Dependencies:** None

#### Deliverables

1. **Kubernetes Manifests** (`infrastructure/kubernetes/`)
   - Namespace definitions (open-forge-dev, open-forge-staging, open-forge-prod)
   - Deployments for all services (API, UI, Dagster, Langflow)
   - Services (ClusterIP, LoadBalancer)
   - Ingress configurations with TLS
   - ConfigMaps and Secrets templates
   - PersistentVolumeClaims for PostgreSQL, Redis, MinIO

2. **Helm Charts** (`infrastructure/helm/open-forge/`)
   - Main chart with subcharts for each component
   - values.yaml for each environment
   - Chart.yaml with dependencies
   - Helper templates (_helpers.tpl)

3. **Kustomize Overlays** (`infrastructure/kustomize/`)
   - Base configuration
   - Environment overlays (dev, staging, prod)
   - Patches for environment-specific settings

#### Key Files

```
infrastructure/
├── kubernetes/
│   ├── namespaces.yaml
│   ├── api/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   ├── ui/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── ingress.yaml
│   ├── dagster/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   ├── langflow/
│   │   ├── deployment.yaml
│   │   └── service.yaml
│   └── databases/
│       ├── postgres-statefulset.yaml
│       ├── redis-deployment.yaml
│       └── minio-statefulset.yaml
├── helm/
│   └── open-forge/
│       ├── Chart.yaml
│       ├── values.yaml
│       ├── values-dev.yaml
│       ├── values-staging.yaml
│       ├── values-prod.yaml
│       └── templates/
└── kustomize/
    ├── base/
    └── overlays/
        ├── dev/
        ├── staging/
        └── prod/
```

---

### WP2: CI/CD Pipeline

**Duration:** 1 week
**Dependencies:** WP1 (partial)

#### Deliverables

1. **GitHub Actions Workflows** (`.github/workflows/`)
   - `ci.yml` - Run tests on PR
   - `build.yml` - Build Docker images
   - `deploy-dev.yml` - Deploy to dev on main push
   - `deploy-staging.yml` - Deploy to staging on release candidate
   - `deploy-prod.yml` - Deploy to prod on release tag
   - `security-scan.yml` - Dependency and container scanning

2. **Dockerfile Optimizations**
   - Multi-stage builds for smaller images
   - Layer caching optimization
   - Non-root user configuration

3. **Container Registry Configuration**
   - GitHub Container Registry (ghcr.io) setup
   - Image tagging strategy (semver + sha)

#### Key Files

```
.github/
├── workflows/
│   ├── ci.yml
│   ├── build.yml
│   ├── deploy-dev.yml
│   ├── deploy-staging.yml
│   ├── deploy-prod.yml
│   └── security-scan.yml
├── actions/
│   └── setup-env/
│       └── action.yml
└── CODEOWNERS

infrastructure/docker/
├── Dockerfile.api
├── Dockerfile.ui
├── Dockerfile.dagster
└── Dockerfile.langflow
```

---

### WP3: Monitoring Stack

**Duration:** 1 week
**Dependencies:** WP1

#### Deliverables

1. **Prometheus Configuration**
   - ServiceMonitor definitions
   - PrometheusRule for alerting
   - Recording rules for performance
   - Scrape configs for all services

2. **Grafana Dashboards**
   - System Overview dashboard
   - API Performance dashboard
   - Agent Execution dashboard
   - Pipeline Execution dashboard
   - Database Performance dashboard

3. **Alertmanager Configuration**
   - Alert routing rules
   - Notification channels (Slack, PagerDuty, email)
   - Silence and inhibition rules

4. **Application Metrics**
   - Custom Prometheus metrics in API
   - Agent execution metrics
   - Pipeline run metrics

#### Key Files

```
infrastructure/monitoring/
├── prometheus/
│   ├── prometheus.yaml
│   ├── rules/
│   │   ├── api-alerts.yaml
│   │   ├── agent-alerts.yaml
│   │   └── pipeline-alerts.yaml
│   └── servicemonitors/
├── grafana/
│   ├── dashboards/
│   │   ├── overview.json
│   │   ├── api-performance.json
│   │   ├── agent-execution.json
│   │   └── pipeline-execution.json
│   └── provisioning/
└── alertmanager/
    └── alertmanager.yaml
```

---

### WP4: Documentation

**Duration:** 1 week
**Dependencies:** None (can run in parallel)

#### Deliverables

1. **API Documentation**
   - OpenAPI spec generation
   - API reference (Swagger UI)
   - Authentication guide
   - Rate limiting documentation

2. **User Guides**
   - Getting Started guide
   - Engagement workflow guide
   - Ontology design guide
   - Pipeline creation guide

3. **Deployment Runbooks**
   - Installation guide
   - Upgrade procedures
   - Backup and restore
   - Troubleshooting guide

4. **Developer Documentation**
   - Architecture overview
   - Contributing guide
   - Local development setup
   - Testing guide

#### Key Files

```
docs/
├── api/
│   ├── openapi.yaml
│   └── authentication.md
├── guides/
│   ├── getting-started.md
│   ├── engagement-workflow.md
│   ├── ontology-design.md
│   └── pipeline-creation.md
├── runbooks/
│   ├── installation.md
│   ├── upgrade.md
│   ├── backup-restore.md
│   └── troubleshooting.md
└── development/
    ├── architecture.md
    ├── contributing.md
    ├── local-setup.md
    └── testing.md
```

---

### WP5: Security Hardening

**Duration:** 1 week
**Dependencies:** WP1, WP2

#### Deliverables

1. **Secrets Management**
   - External Secrets Operator configuration
   - Vault integration (optional)
   - Secret rotation procedures

2. **Network Policies**
   - Pod-to-pod communication rules
   - Egress restrictions
   - Namespace isolation

3. **RBAC Configuration**
   - Service accounts per component
   - Role and RoleBinding definitions
   - ClusterRole for monitoring

4. **Security Scanning**
   - Container image scanning (Trivy)
   - Dependency scanning (Dependabot)
   - SAST integration

#### Key Files

```
infrastructure/security/
├── network-policies/
│   ├── api-network-policy.yaml
│   ├── database-network-policy.yaml
│   └── default-deny.yaml
├── rbac/
│   ├── service-accounts.yaml
│   ├── roles.yaml
│   └── rolebindings.yaml
├── secrets/
│   └── external-secrets.yaml
└── scanning/
    └── trivy-config.yaml
```

---

### WP6: Performance Optimization

**Duration:** 1 week
**Dependencies:** WP1, WP3

#### Deliverables

1. **Resource Tuning**
   - CPU/Memory requests and limits
   - HorizontalPodAutoscaler configurations
   - PodDisruptionBudgets

2. **Caching Layer**
   - Redis caching for API responses
   - Session caching
   - Query result caching

3. **Connection Pooling**
   - PgBouncer for PostgreSQL
   - Redis connection pooling
   - HTTP keep-alive tuning

4. **Load Testing**
   - k6 load test scripts
   - Performance baselines
   - Capacity planning documentation

#### Key Files

```
infrastructure/performance/
├── autoscaling/
│   ├── api-hpa.yaml
│   ├── dagster-hpa.yaml
│   └── pdb.yaml
├── caching/
│   └── redis-config.yaml
├── pooling/
│   └── pgbouncer.yaml
└── load-tests/
    ├── k6/
    │   ├── api-load.js
    │   └── pipeline-load.js
    └── baselines.md
```

---

## Timeline

```
Week:  1     2     3     4     5     6
       │     │     │     │     │     │
WP1:   ████████████░░░░░░░░░░░░░░░░░░  K8s Infrastructure
WP2:   ░░░░████████░░░░░░░░░░░░░░░░░░  CI/CD Pipeline
WP3:   ░░░░░░░░████████░░░░░░░░░░░░░░  Monitoring Stack
WP4:   ████████████████░░░░░░░░░░░░░░  Documentation
WP5:   ░░░░░░░░░░░░████████░░░░░░░░░░  Security Hardening
WP6:   ░░░░░░░░░░░░░░░░████████░░░░░░  Performance
INT:   ░░░░░░░░░░░░░░░░░░░░████████░░  Integration Testing
       │     │     │     │     │     │
       G8────────────────────G9──────  Gates
```

---

## Success Criteria

| Metric | Target |
|--------|--------|
| Deployment time (push to prod) | < 15 minutes |
| System uptime | 99.9% |
| P95 API latency | < 200ms |
| Alert response time | < 5 minutes |
| Documentation coverage | 100% of public APIs |
| Security scan pass rate | 100% critical/high |

---

## Parallel Execution Strategy

**Phase 1 (Concurrent):**
- WP1: Kubernetes Infrastructure
- WP4: Documentation

**Phase 2 (After WP1):**
- WP2: CI/CD Pipeline
- WP3: Monitoring Stack

**Phase 3 (After WP2):**
- WP5: Security Hardening
- WP6: Performance Optimization
