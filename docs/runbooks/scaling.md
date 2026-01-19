# Scaling Guide

This runbook covers horizontal and vertical scaling strategies for Open Forge.

## Table of Contents

- [Scaling Overview](#scaling-overview)
- [Horizontal Scaling](#horizontal-scaling)
- [Vertical Scaling](#vertical-scaling)
- [Database Scaling](#database-scaling)
- [Pipeline Scaling](#pipeline-scaling)
- [Auto-Scaling](#auto-scaling)
- [Capacity Planning](#capacity-planning)

---

## Scaling Overview

### When to Scale

| Metric | Warning Threshold | Critical Threshold | Action |
|--------|-------------------|-------------------|--------|
| CPU Usage | > 70% sustained | > 85% sustained | Horizontal scale |
| Memory Usage | > 75% | > 90% | Vertical scale |
| API Latency (p99) | > 500ms | > 2s | Scale API or DB |
| Queue Depth | > 1000 | > 5000 | Scale workers |
| DB Connections | > 80% pool | > 95% pool | Scale DB |

### Architecture for Scale

```
                           ┌──────────────┐
                           │   Load       │
                           │  Balancer    │
                           └──────┬───────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
    ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
    │   API 1     │       │   API 2     │       │   API N     │
    └──────┬──────┘       └──────┬──────┘       └──────┬──────┘
           │                      │                      │
           └──────────────────────┼──────────────────────┘
                                  │
           ┌──────────────────────┼──────────────────────┐
           │                      │                      │
    ┌──────▼──────┐       ┌──────▼──────┐       ┌──────▼──────┐
    │  PostgreSQL │       │   Redis     │       │    MinIO    │
    │   Primary   │       │   Cluster   │       │   Cluster   │
    │  + Replicas │       │             │       │             │
    └─────────────┘       └─────────────┘       └─────────────┘
```

---

## Horizontal Scaling

### Scaling API Servers

#### Docker Compose

```bash
# Scale to 3 API replicas
docker compose -f infrastructure/docker/docker-compose.yml up -d --scale api=3

# Verify
docker compose ps
```

Add a load balancer (nginx):

```yaml
# infrastructure/docker/docker-compose.yml
services:
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - api

  api:
    # ... existing config
    expose:
      - "8000"
    deploy:
      replicas: 3
```

```nginx
# nginx.conf
upstream api {
    least_conn;
    server api:8000;
}

server {
    listen 80;

    location / {
        proxy_pass http://api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://api/health;
    }
}
```

#### Kubernetes

```bash
# Scale deployment
kubectl scale deployment api -n open-forge --replicas=5

# Or update deployment spec
kubectl patch deployment api -n open-forge -p '{"spec":{"replicas":5}}'
```

```yaml
# API deployment with resource requests
apiVersion: apps/v1
kind: Deployment
metadata:
  name: api
  namespace: open-forge
spec:
  replicas: 5
  selector:
    matchLabels:
      app: api
  template:
    spec:
      containers:
        - name: api
          resources:
            requests:
              memory: "1Gi"
              cpu: "500m"
            limits:
              memory: "2Gi"
              cpu: "1"
```

### Scaling Agent Workers

```yaml
# Agent worker deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-worker
  namespace: open-forge
spec:
  replicas: 10  # Scale based on task queue depth
  template:
    spec:
      containers:
        - name: worker
          image: ghcr.io/18bravo/open-forge-worker:latest
          env:
            - name: WORKER_CONCURRENCY
              value: "4"  # Tasks per worker
          resources:
            requests:
              memory: "2Gi"
              cpu: "1"
            limits:
              memory: "4Gi"
              cpu: "2"
```

### Scaling Dagster

```yaml
# Dagster run worker deployment
apiVersion: apps/v1
kind: Deployment
metadata:
  name: dagster-run-worker
  namespace: open-forge
spec:
  replicas: 5  # Scale for parallel pipeline runs
  template:
    spec:
      containers:
        - name: run-worker
          image: ghcr.io/18bravo/open-forge-dagster:latest
          command: ["dagster", "run", "worker", "-w", "workspace.yaml"]
          resources:
            requests:
              memory: "4Gi"
              cpu: "2"
```

---

## Vertical Scaling

### API Server Resources

```yaml
# Increase resources for API
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### Database Resources

```yaml
# PostgreSQL with increased resources
services:
  postgres:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 8G
    command:
      - postgres
      - -c
      - shared_buffers=2GB
      - -c
      - effective_cache_size=6GB
      - -c
      - work_mem=256MB
      - -c
      - maintenance_work_mem=512MB
      - -c
      - max_connections=200
```

### Redis Resources

```yaml
# Redis with increased memory
services:
  redis:
    deploy:
      resources:
        limits:
          memory: 4G
    command:
      - redis-server
      - --maxmemory 3gb
      - --maxmemory-policy allkeys-lru
```

---

## Database Scaling

### PostgreSQL Read Replicas

```yaml
# docker-compose for read replicas
services:
  postgres-primary:
    image: apache/age:latest
    environment:
      POSTGRES_USER: foundry
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_primary:/var/lib/postgresql/data
    command:
      - postgres
      - -c
      - wal_level=replica
      - -c
      - max_wal_senders=10
      - -c
      - max_replication_slots=10

  postgres-replica-1:
    image: apache/age:latest
    environment:
      PGUSER: replicator
      PGPASSWORD: ${REPLICATION_PASSWORD}
    command: |
      bash -c "
        until pg_basebackup -h postgres-primary -D /var/lib/postgresql/data -U replicator -vP -W
        do
          sleep 1
        done
        touch /var/lib/postgresql/data/standby.signal
        postgres
      "
    depends_on:
      - postgres-primary
```

### Connection Pooling with PgBouncer

```yaml
services:
  pgbouncer:
    image: edoburu/pgbouncer:latest
    environment:
      DATABASE_URL: postgres://foundry:${DB_PASSWORD}@postgres:5432/foundry
      MAX_CLIENT_CONN: 1000
      DEFAULT_POOL_SIZE: 100
      POOL_MODE: transaction
    ports:
      - "6432:5432"
```

Update API to use PgBouncer:

```bash
# .env
DB_HOST=pgbouncer
DB_PORT=6432
```

### Redis Cluster

```yaml
# Redis cluster configuration
services:
  redis-1:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7001:6379"
    volumes:
      - redis-1:/data

  redis-2:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7002:6379"
    volumes:
      - redis-2:/data

  redis-3:
    image: redis:7-alpine
    command: redis-server --cluster-enabled yes --cluster-config-file nodes.conf --cluster-node-timeout 5000
    ports:
      - "7003:6379"
    volumes:
      - redis-3:/data

  redis-init:
    image: redis:7-alpine
    depends_on:
      - redis-1
      - redis-2
      - redis-3
    command: |
      sh -c "
        sleep 5
        redis-cli --cluster create redis-1:6379 redis-2:6379 redis-3:6379 --cluster-replicas 0 --cluster-yes
      "
```

---

## Pipeline Scaling

### Dagster Executors

Configure parallel execution:

```python
# pipelines/definitions.py
from dagster import Definitions, multiprocess_executor

defs = Definitions(
    assets=all_assets,
    jobs=[
        define_asset_job(
            name="parallel_job",
            selection=AssetSelection.all(),
            executor_def=multiprocess_executor.configured({
                "max_concurrent": 8,  # Parallel processes
            })
        )
    ]
)
```

### Kubernetes Executor

For larger scale, use Kubernetes job executor:

```python
from dagster_k8s import k8s_job_executor

defs = Definitions(
    jobs=[
        define_asset_job(
            name="k8s_job",
            executor_def=k8s_job_executor.configured({
                "job_namespace": "open-forge",
                "job_image": "ghcr.io/18bravo/open-forge-dagster:latest",
                "image_pull_policy": "Always",
                "resources": {
                    "requests": {
                        "cpu": "1",
                        "memory": "2Gi"
                    },
                    "limits": {
                        "cpu": "2",
                        "memory": "4Gi"
                    }
                }
            })
        )
    ]
)
```

### Scaling Iceberg Operations

Configure partitioning for better parallelism:

```python
@asset(
    partitions_def=DailyPartitionsDefinition(start_date="2024-01-01"),
    io_manager_key="partitioned_iceberg_io_manager"
)
def daily_metrics(context):
    # Process only one day's data at a time
    partition_date = context.partition_key
    ...
```

---

## Auto-Scaling

### Kubernetes HPA

```yaml
# Horizontal Pod Autoscaler for API
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
  namespace: open-forge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: api
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Percent
          value: 10
          periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
        - type: Percent
          value: 100
          periodSeconds: 15
```

### Custom Metrics Scaling

Scale based on queue depth:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: worker-hpa
  namespace: open-forge
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: agent-worker
  minReplicas: 2
  maxReplicas: 50
  metrics:
    - type: External
      external:
        metric:
          name: redis_queue_length
          selector:
            matchLabels:
              queue: agent_tasks_pending
        target:
          type: Value
          value: 100  # Scale up when queue > 100 per replica
```

### KEDA for Event-Driven Scaling

```yaml
apiVersion: keda.sh/v1alpha1
kind: ScaledObject
metadata:
  name: agent-worker-scaler
  namespace: open-forge
spec:
  scaleTargetRef:
    name: agent-worker
  minReplicaCount: 1
  maxReplicaCount: 100
  triggers:
    - type: redis
      metadata:
        address: redis.open-forge.svc:6379
        listName: agent:tasks:pending
        listLength: "10"  # 10 tasks per replica
        databaseIndex: "0"
```

---

## Capacity Planning

### Sizing Guidelines

| Workload | Users | API Replicas | Workers | PostgreSQL | Redis |
|----------|-------|--------------|---------|------------|-------|
| Small | < 50 | 2 | 2 | 2 CPU, 4GB | 1GB |
| Medium | 50-200 | 5 | 10 | 4 CPU, 16GB | 4GB |
| Large | 200-1000 | 10 | 25 | 8 CPU, 32GB | 8GB |
| Enterprise | 1000+ | 20+ | 50+ | Cluster | Cluster |

### Resource Estimation

**API Servers:**
- ~100MB memory per concurrent connection
- 1 CPU core handles ~500 requests/second

**Agent Workers:**
- ~500MB memory per concurrent task
- LLM calls are CPU-bound

**PostgreSQL:**
- ~10MB per connection
- Index size ~ 20% of data size

**Redis:**
- ~1KB per queue item
- Session data varies

### Monitoring for Scaling Decisions

```yaml
# Prometheus alerting rules
groups:
  - name: scaling
    rules:
      - alert: HighCPU
        expr: avg(rate(container_cpu_usage_seconds_total{container="api"}[5m])) > 0.7
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage - consider scaling API"

      - alert: HighMemory
        expr: container_memory_working_set_bytes{container="api"} / container_spec_memory_limit_bytes > 0.8
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage"

      - alert: HighQueueDepth
        expr: redis_queue_length{queue="agent_tasks_pending"} > 1000
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Task queue backing up"

      - alert: HighAPILatency
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
        annotations:
          summary: "High API latency"
```

### Load Testing

Before scaling, load test to validate:

```bash
# Install k6
brew install k6

# Run load test
k6 run --vus 100 --duration 5m scripts/load_test.js
```

```javascript
// scripts/load_test.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export let options = {
  vus: 100,
  duration: '5m',
  thresholds: {
    http_req_duration: ['p(99)<2000'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  let res = http.get('http://localhost:8000/api/v1/engagements', {
    headers: { 'X-API-Key': __ENV.API_KEY },
  });

  check(res, {
    'status is 200': (r) => r.status === 200,
    'response time < 500ms': (r) => r.timings.duration < 500,
  });

  sleep(1);
}
```

---

## Related Documentation

- [Installation Guide](./installation.md)
- [Troubleshooting](./troubleshooting.md)
- [Architecture Overview](../development/architecture.md)
