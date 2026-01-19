# Installation Guide

This runbook provides step-by-step instructions for installing Open Forge in various environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Docker Compose Installation](#docker-compose-installation)
- [Kubernetes Installation](#kubernetes-installation)
- [Helm Chart Installation](#helm-chart-installation)
- [Post-Installation Configuration](#post-installation-configuration)
- [Verification](#verification)

---

## Prerequisites

### Hardware Requirements

| Environment | CPU | Memory | Storage |
|-------------|-----|--------|---------|
| Development | 4 cores | 8 GB | 50 GB |
| Staging | 8 cores | 16 GB | 100 GB |
| Production | 16+ cores | 32+ GB | 500+ GB SSD |

### Software Requirements

| Software | Version | Purpose |
|----------|---------|---------|
| Docker | 24.0+ | Container runtime |
| Docker Compose | 2.20+ | Local orchestration |
| kubectl | 1.28+ | Kubernetes CLI |
| Helm | 3.12+ | Kubernetes package manager |
| Python | 3.11+ | Backend services |
| Node.js | 18+ | Frontend build |

### Required Credentials

- **Anthropic API Key**: Required for AI agents
- **Container Registry**: Access to pull images (if using private registry)

---

## Docker Compose Installation

The quickest way to get started for development and small deployments.

### Step 1: Clone Repository

```bash
git clone https://github.com/18bravo/open-forge.git
cd open-forge
```

### Step 2: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit configuration
nano .env
```

Required environment variables:

```bash
# .env
ENVIRONMENT=production
DEBUG=false

# Database
DB_HOST=postgres
DB_PORT=5432
DB_USER=foundry
DB_PASSWORD=<strong-password>
DB_NAME=foundry

# Redis
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_PASSWORD=<redis-password>

# MinIO/S3
S3_ENDPOINT=http://minio:9000
S3_ACCESS_KEY=<access-key>
S3_SECRET_KEY=<secret-key>

# Iceberg
ICEBERG_CATALOG_URI=http://iceberg-rest:8181
ICEBERG_WAREHOUSE=s3://foundry-lake/warehouse

# LLM
ANTHROPIC_API_KEY=<your-anthropic-key>
DEFAULT_LLM_MODEL=claude-sonnet-4-20250514

# Observability
OTLP_ENDPOINT=http://jaeger:4317
SERVICE_NAME=open-forge
```

### Step 3: Start Services

```bash
# Start all services
docker compose -f infrastructure/docker/docker-compose.yml up -d

# Check status
docker compose -f infrastructure/docker/docker-compose.yml ps
```

### Step 4: Initialize Database

```bash
# Run migrations
docker compose -f infrastructure/docker/docker-compose.yml exec api \
  python -m alembic upgrade head

# Create initial admin user
docker compose -f infrastructure/docker/docker-compose.yml exec api \
  python scripts/create_admin.py
```

### Step 5: Verify Installation

```bash
# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/health/ready

# Test infrastructure
make infra-test
```

---

## Kubernetes Installation

For production deployments with high availability.

### Step 1: Create Namespace

```bash
kubectl create namespace open-forge
```

### Step 2: Create Secrets

```bash
# Create secrets for credentials
kubectl create secret generic open-forge-secrets \
  --namespace open-forge \
  --from-literal=DB_PASSWORD=<db-password> \
  --from-literal=REDIS_PASSWORD=<redis-password> \
  --from-literal=S3_ACCESS_KEY=<s3-access-key> \
  --from-literal=S3_SECRET_KEY=<s3-secret-key> \
  --from-literal=ANTHROPIC_API_KEY=<anthropic-key>
```

### Step 3: Deploy PostgreSQL

```yaml
# infrastructure/kubernetes/postgres.yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: postgres
  namespace: open-forge
spec:
  serviceName: postgres
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
        - name: postgres
          image: apache/age:latest
          ports:
            - containerPort: 5432
          env:
            - name: POSTGRES_USER
              value: foundry
            - name: POSTGRES_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: DB_PASSWORD
            - name: POSTGRES_DB
              value: foundry
          volumeMounts:
            - name: postgres-data
              mountPath: /var/lib/postgresql/data
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "2"
  volumeClaimTemplates:
    - metadata:
        name: postgres-data
      spec:
        accessModes: ["ReadWriteOnce"]
        storageClassName: fast-ssd
        resources:
          requests:
            storage: 100Gi
---
apiVersion: v1
kind: Service
metadata:
  name: postgres
  namespace: open-forge
spec:
  ports:
    - port: 5432
  selector:
    app: postgres
```

```bash
kubectl apply -f infrastructure/kubernetes/postgres.yaml
```

### Step 4: Deploy Redis

```yaml
# infrastructure/kubernetes/redis.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: open-forge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
        - name: redis
          image: redis:7-alpine
          ports:
            - containerPort: 6379
          command:
            - redis-server
            - --requirepass
            - $(REDIS_PASSWORD)
            - --appendonly
            - "yes"
          env:
            - name: REDIS_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: REDIS_PASSWORD
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis
  namespace: open-forge
spec:
  ports:
    - port: 6379
  selector:
    app: redis
```

```bash
kubectl apply -f infrastructure/kubernetes/redis.yaml
```

### Step 5: Deploy API Server

```yaml
# infrastructure/kubernetes/api.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: open-forge
spec:
  replicas: 3
  selector:
    matchLabels:
      app: api
  template:
    metadata:
      labels:
        app: api
    spec:
      containers:
        - name: api
          image: ghcr.io/18bravo/open-forge-api:latest
          ports:
            - containerPort: 8000
          envFrom:
            - configMapRef:
                name: open-forge-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: DB_PASSWORD
            - name: ANTHROPIC_API_KEY
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: ANTHROPIC_API_KEY
          livenessProbe:
            httpGet:
              path: /health/live
              port: 8000
            initialDelaySeconds: 10
            periodSeconds: 10
          readinessProbe:
            httpGet:
              path: /health/ready
              port: 8000
            initialDelaySeconds: 5
            periodSeconds: 5
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1"
---
apiVersion: v1
kind: Service
metadata:
  name: api
  namespace: open-forge
spec:
  ports:
    - port: 8000
  selector:
    app: api
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: api-ingress
  namespace: open-forge
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
    - hosts:
        - api.openforge.example.com
      secretName: api-tls
  rules:
    - host: api.openforge.example.com
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: api
                port:
                  number: 8000
```

```bash
kubectl apply -f infrastructure/kubernetes/api.yaml
```

### Step 6: Deploy Dagster

```yaml
# infrastructure/kubernetes/dagster.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagster-webserver
  namespace: open-forge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dagster-webserver
  template:
    metadata:
      labels:
        app: dagster-webserver
    spec:
      containers:
        - name: dagster-webserver
          image: ghcr.io/18bravo/open-forge-dagster:latest
          command: ["dagster-webserver", "-h", "0.0.0.0", "-p", "3000"]
          ports:
            - containerPort: 3000
          envFrom:
            - configMapRef:
                name: dagster-config
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagster-daemon
  namespace: open-forge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: dagster-daemon
  template:
    metadata:
      labels:
        app: dagster-daemon
    spec:
      containers:
        - name: dagster-daemon
          image: ghcr.io/18bravo/open-forge-dagster:latest
          command: ["dagster-daemon", "run"]
          envFrom:
            - configMapRef:
                name: dagster-config
          resources:
            requests:
              memory: "512Mi"
              cpu: "250m"
```

```bash
kubectl apply -f infrastructure/kubernetes/dagster.yaml
```

---

## Helm Chart Installation

The recommended approach for production Kubernetes deployments.

### Step 1: Add Helm Repository

```bash
helm repo add open-forge https://charts.openforge.io
helm repo update
```

### Step 2: Create Values File

```yaml
# values.yaml
global:
  environment: production
  imageRegistry: ghcr.io/18bravo

api:
  replicas: 3
  resources:
    requests:
      memory: "1Gi"
      cpu: "500m"
    limits:
      memory: "2Gi"
      cpu: "1"
  ingress:
    enabled: true
    host: api.openforge.example.com
    tls:
      enabled: true
      secretName: api-tls

dagster:
  webserver:
    replicas: 1
  daemon:
    replicas: 1

postgresql:
  enabled: true
  auth:
    existingSecret: open-forge-secrets
    secretKeys:
      adminPasswordKey: DB_PASSWORD
  primary:
    persistence:
      size: 100Gi
      storageClass: fast-ssd

redis:
  enabled: true
  auth:
    existingSecret: open-forge-secrets
    existingSecretPasswordKey: REDIS_PASSWORD

minio:
  enabled: true
  auth:
    existingSecret: open-forge-secrets

iceberg:
  enabled: true
  catalog:
    warehouse: s3://foundry-lake/warehouse

jaeger:
  enabled: true
  collector:
    resources:
      limits:
        memory: "1Gi"

secrets:
  anthropicApiKey:
    existingSecret: open-forge-secrets
    key: ANTHROPIC_API_KEY
```

### Step 3: Install Chart

```bash
# Create secrets first
kubectl create namespace open-forge

kubectl create secret generic open-forge-secrets \
  --namespace open-forge \
  --from-literal=DB_PASSWORD=<password> \
  --from-literal=REDIS_PASSWORD=<password> \
  --from-literal=S3_ACCESS_KEY=<key> \
  --from-literal=S3_SECRET_KEY=<key> \
  --from-literal=ANTHROPIC_API_KEY=<key>

# Install Open Forge
helm install open-forge open-forge/open-forge \
  --namespace open-forge \
  --values values.yaml \
  --wait
```

### Step 4: Verify Installation

```bash
# Check pods
kubectl get pods -n open-forge

# Check services
kubectl get svc -n open-forge

# View logs
kubectl logs -n open-forge -l app=api -f
```

---

## Post-Installation Configuration

### Create Admin User

```bash
# Docker Compose
docker compose exec api python scripts/create_admin.py \
  --email admin@example.com \
  --password <strong-password>

# Kubernetes
kubectl exec -n open-forge deployment/api -- \
  python scripts/create_admin.py \
  --email admin@example.com \
  --password <strong-password>
```

### Generate API Keys

```bash
# Create service account API key
kubectl exec -n open-forge deployment/api -- \
  python scripts/create_api_key.py \
  --name "CI/CD Service" \
  --scopes "execute:agents,read:engagements"
```

### Configure MinIO Buckets

```bash
# Create required buckets
kubectl exec -n open-forge deployment/minio -- \
  mc alias set local http://localhost:9000 $S3_ACCESS_KEY $S3_SECRET_KEY

kubectl exec -n open-forge deployment/minio -- \
  mc mb local/foundry-lake

kubectl exec -n open-forge deployment/minio -- \
  mc mb local/foundry-artifacts
```

### Initialize Database Schema

```bash
# Run migrations
kubectl exec -n open-forge deployment/api -- \
  python -m alembic upgrade head

# Initialize Apache AGE extension
kubectl exec -n open-forge statefulset/postgres -- \
  psql -U foundry -d foundry -c "CREATE EXTENSION IF NOT EXISTS age;"
```

---

## Verification

### Health Checks

```bash
# API health
curl -f https://api.openforge.example.com/health
curl -f https://api.openforge.example.com/health/ready

# Response should be:
# {"status":"healthy","version":"0.1.0","timestamp":"..."}
```

### Service Connectivity

```bash
# Test database
kubectl exec -n open-forge deployment/api -- \
  python -c "from core.database import test_connection; test_connection()"

# Test Redis
kubectl exec -n open-forge deployment/api -- \
  python -c "from core.messaging import test_connection; test_connection()"

# Test MinIO
kubectl exec -n open-forge deployment/api -- \
  python -c "from core.storage import test_connection; test_connection()"
```

### End-to-End Test

```bash
# Create test engagement
curl -X POST https://api.openforge.example.com/api/v1/engagements \
  -H "Content-Type: application/json" \
  -H "X-API-Key: <api-key>" \
  -d '{
    "name": "Installation Test",
    "objective": "Verify Open Forge installation",
    "priority": "low"
  }'

# Expected: 201 Created with engagement ID
```

### Monitoring Dashboards

Access monitoring dashboards:

| Dashboard | URL | Purpose |
|-----------|-----|---------|
| Dagster | http://localhost:3000 | Pipeline monitoring |
| Jaeger | http://localhost:16686 | Distributed tracing |
| MinIO | http://localhost:9001 | Object storage |

---

## Troubleshooting Installation

### Pods Not Starting

```bash
# Check pod events
kubectl describe pod -n open-forge <pod-name>

# Check logs
kubectl logs -n open-forge <pod-name> --previous
```

### Database Connection Errors

```bash
# Verify postgres is running
kubectl get pods -n open-forge -l app=postgres

# Test connection manually
kubectl exec -n open-forge deployment/api -- \
  psql -h postgres -U foundry -d foundry -c "SELECT 1"
```

### Permission Errors

```bash
# Check service account
kubectl get serviceaccount -n open-forge

# Verify RBAC
kubectl auth can-i list pods -n open-forge --as=system:serviceaccount:open-forge:default
```

For more troubleshooting help, see [Troubleshooting Runbook](./troubleshooting.md).

---

## Related Documentation

- [Upgrade Guide](./upgrade.md)
- [Backup and Restore](./backup-restore.md)
- [Scaling Guide](./scaling.md)
- [Troubleshooting](./troubleshooting.md)
