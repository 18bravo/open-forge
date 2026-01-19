# Upgrade Guide

This runbook provides procedures for upgrading Open Forge to new versions.

## Table of Contents

- [Before You Upgrade](#before-you-upgrade)
- [Version Compatibility](#version-compatibility)
- [Docker Compose Upgrade](#docker-compose-upgrade)
- [Kubernetes Upgrade](#kubernetes-upgrade)
- [Helm Chart Upgrade](#helm-chart-upgrade)
- [Database Migrations](#database-migrations)
- [Rollback Procedures](#rollback-procedures)
- [Post-Upgrade Verification](#post-upgrade-verification)

---

## Before You Upgrade

### Pre-Upgrade Checklist

- [ ] Read the [release notes](https://github.com/18bravo/open-forge/releases) for breaking changes
- [ ] Create a full backup (see [Backup Guide](./backup-restore.md))
- [ ] Verify backup can be restored
- [ ] Test upgrade in staging environment first
- [ ] Schedule maintenance window
- [ ] Notify users of planned downtime
- [ ] Document current version numbers

### Check Current Version

```bash
# API version
curl -s http://localhost:8000/health | jq '.version'

# Docker images
docker compose -f infrastructure/docker/docker-compose.yml images

# Helm release
helm list -n open-forge
```

### Backup Current State

```bash
# Full backup (see backup-restore.md for details)
./scripts/backup.sh --full

# Or minimal backup
./scripts/backup.sh --database-only
```

---

## Version Compatibility

### Supported Upgrade Paths

| From Version | To Version | Direct Upgrade | Notes |
|--------------|------------|----------------|-------|
| 0.1.x | 0.2.x | Yes | Minor version upgrade |
| 0.1.x | 0.3.x | No | Must upgrade to 0.2.x first |
| 0.2.x | 0.3.x | Yes | Minor version upgrade |
| 0.x.x | 1.0.x | Yes | Major version, review breaking changes |

### Dependency Compatibility Matrix

| Open Forge | Python | PostgreSQL | Redis | Dagster |
|------------|--------|------------|-------|---------|
| 0.1.x | 3.11+ | 14+ | 7.0+ | 1.7+ |
| 0.2.x | 3.11+ | 15+ | 7.2+ | 1.8+ |
| 0.3.x | 3.12+ | 16+ | 7.2+ | 1.9+ |

---

## Docker Compose Upgrade

### Step 1: Stop Services

```bash
cd /path/to/open-forge

# Stop application services (keep database running for backup)
docker compose -f infrastructure/docker/docker-compose.yml stop api dagster-webserver dagster-daemon

# Verify services stopped
docker compose -f infrastructure/docker/docker-compose.yml ps
```

### Step 2: Backup

```bash
# Backup database
docker compose -f infrastructure/docker/docker-compose.yml exec postgres \
  pg_dump -U foundry foundry > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup volumes
docker run --rm \
  -v openforge_postgres_data:/data \
  -v $(pwd)/backups:/backup \
  alpine tar czf /backup/postgres_data_$(date +%Y%m%d).tar.gz /data
```

### Step 3: Pull New Version

```bash
# Pull latest code
git fetch origin
git checkout v0.2.0  # or desired version

# Pull new images
docker compose -f infrastructure/docker/docker-compose.yml pull
```

### Step 4: Apply Configuration Changes

```bash
# Compare configuration changes
diff .env.example .env

# Update .env with any new required variables
nano .env
```

### Step 5: Run Database Migrations

```bash
# Start database if not running
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres

# Wait for database to be ready
sleep 10

# Run migrations
docker compose -f infrastructure/docker/docker-compose.yml run --rm api \
  python -m alembic upgrade head
```

### Step 6: Start Services

```bash
# Start all services with new version
docker compose -f infrastructure/docker/docker-compose.yml up -d

# Monitor logs for errors
docker compose -f infrastructure/docker/docker-compose.yml logs -f
```

### Step 7: Verify Upgrade

```bash
# Check version
curl http://localhost:8000/health

# Run health checks
make infra-test

# Test API
curl http://localhost:8000/api/v1/engagements
```

---

## Kubernetes Upgrade

### Step 1: Prepare for Upgrade

```bash
# Check current state
kubectl get pods -n open-forge
kubectl get deployments -n open-forge

# Scale down for maintenance
kubectl scale deployment api -n open-forge --replicas=1
kubectl scale deployment dagster-webserver -n open-forge --replicas=0
kubectl scale deployment dagster-daemon -n open-forge --replicas=0
```

### Step 2: Backup Database

```bash
# Create backup job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: pre-upgrade-backup
  namespace: open-forge
spec:
  template:
    spec:
      containers:
        - name: backup
          image: postgres:15
          command:
            - /bin/bash
            - -c
            - |
              pg_dump -h postgres -U foundry foundry | gzip > /backup/pre-upgrade-$(date +%Y%m%d_%H%M%S).sql.gz
          env:
            - name: PGPASSWORD
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: DB_PASSWORD
          volumeMounts:
            - name: backup
              mountPath: /backup
      volumes:
        - name: backup
          persistentVolumeClaim:
            claimName: backup-pvc
      restartPolicy: Never
EOF

# Wait for backup to complete
kubectl wait --for=condition=complete job/pre-upgrade-backup -n open-forge --timeout=300s
```

### Step 3: Update Image Tags

```bash
# Update API deployment
kubectl set image deployment/api \
  api=ghcr.io/18bravo/open-forge-api:v0.2.0 \
  -n open-forge

# Update Dagster deployments
kubectl set image deployment/dagster-webserver \
  dagster=ghcr.io/18bravo/open-forge-dagster:v0.2.0 \
  -n open-forge

kubectl set image deployment/dagster-daemon \
  dagster=ghcr.io/18bravo/open-forge-dagster:v0.2.0 \
  -n open-forge
```

### Step 4: Run Migrations

```bash
# Run migration job
kubectl apply -f - <<EOF
apiVersion: batch/v1
kind: Job
metadata:
  name: db-migration
  namespace: open-forge
spec:
  template:
    spec:
      containers:
        - name: migrate
          image: ghcr.io/18bravo/open-forge-api:v0.2.0
          command: ["python", "-m", "alembic", "upgrade", "head"]
          envFrom:
            - configMapRef:
                name: open-forge-config
          env:
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: open-forge-secrets
                  key: DB_PASSWORD
      restartPolicy: Never
EOF

# Wait for migration
kubectl wait --for=condition=complete job/db-migration -n open-forge --timeout=300s

# Check migration logs
kubectl logs job/db-migration -n open-forge
```

### Step 5: Scale Up Services

```bash
# Scale up API
kubectl scale deployment api -n open-forge --replicas=3

# Wait for rollout
kubectl rollout status deployment/api -n open-forge

# Scale up Dagster
kubectl scale deployment dagster-webserver -n open-forge --replicas=1
kubectl scale deployment dagster-daemon -n open-forge --replicas=1
```

### Step 6: Verify Upgrade

```bash
# Check pod status
kubectl get pods -n open-forge

# Check logs for errors
kubectl logs -n open-forge -l app=api --tail=100

# Test health endpoint
kubectl exec -n open-forge deployment/api -- curl -s localhost:8000/health
```

---

## Helm Chart Upgrade

### Step 1: Get Current Values

```bash
# Export current values
helm get values open-forge -n open-forge > current-values.yaml
```

### Step 2: Update Repository

```bash
helm repo update open-forge
```

### Step 3: Review Changes

```bash
# Compare chart changes
helm show values open-forge/open-forge --version 0.2.0 > new-values.yaml
diff current-values.yaml new-values.yaml
```

### Step 4: Upgrade with Helm

```bash
# Dry run to preview changes
helm upgrade open-forge open-forge/open-forge \
  --namespace open-forge \
  --version 0.2.0 \
  --values current-values.yaml \
  --dry-run

# Apply upgrade
helm upgrade open-forge open-forge/open-forge \
  --namespace open-forge \
  --version 0.2.0 \
  --values current-values.yaml \
  --wait \
  --timeout 10m
```

### Step 5: Verify Upgrade

```bash
# Check release status
helm status open-forge -n open-forge

# Check all resources
kubectl get all -n open-forge
```

---

## Database Migrations

### Understanding Migrations

Open Forge uses Alembic for database migrations:

```
migrations/
  versions/
    001_initial.py
    002_add_agent_tables.py
    003_add_ontology_tables.py
```

### Running Migrations

```bash
# Check current migration state
alembic current

# See pending migrations
alembic history --indicate-current

# Upgrade to latest
alembic upgrade head

# Upgrade to specific version
alembic upgrade 003
```

### Migration Best Practices

1. **Always backup before migrating**
2. **Test migrations in staging first**
3. **Review migration SQL before running**:
   ```bash
   alembic upgrade head --sql > migration.sql
   cat migration.sql
   ```

### Handling Migration Failures

If a migration fails:

```bash
# Check current state
alembic current

# View migration history
alembic history -v

# Manually fix and re-run
alembic upgrade head

# Or rollback (if supported)
alembic downgrade -1
```

---

## Rollback Procedures

### Docker Compose Rollback

```bash
# Stop current version
docker compose -f infrastructure/docker/docker-compose.yml down

# Checkout previous version
git checkout v0.1.5

# Restore database backup
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  psql -U foundry foundry < backup_20240115.sql

# Start previous version
docker compose -f infrastructure/docker/docker-compose.yml up -d
```

### Kubernetes Rollback

```bash
# Rollback deployment
kubectl rollout undo deployment/api -n open-forge

# Or rollback to specific revision
kubectl rollout undo deployment/api -n open-forge --to-revision=2

# Check rollback status
kubectl rollout status deployment/api -n open-forge
```

### Helm Rollback

```bash
# List release history
helm history open-forge -n open-forge

# Rollback to previous release
helm rollback open-forge 1 -n open-forge

# Or rollback to specific revision
helm rollback open-forge 3 -n open-forge
```

### Database Rollback

```bash
# Restore from backup
kubectl exec -n open-forge statefulset/postgres -- \
  psql -U foundry foundry < /backup/pre-upgrade.sql

# Or use Alembic downgrade (if available)
alembic downgrade -1
```

---

## Post-Upgrade Verification

### Health Check Verification

```bash
#!/bin/bash
# post-upgrade-check.sh

set -e

API_URL=${API_URL:-"http://localhost:8000"}
EXPECTED_VERSION=${1:-"0.2.0"}

echo "Running post-upgrade verification..."

# Check API health
echo "Checking API health..."
HEALTH=$(curl -sf "$API_URL/health")
VERSION=$(echo $HEALTH | jq -r '.version')

if [ "$VERSION" != "$EXPECTED_VERSION" ]; then
  echo "ERROR: Version mismatch. Expected $EXPECTED_VERSION, got $VERSION"
  exit 1
fi
echo "API version: $VERSION"

# Check readiness
echo "Checking readiness..."
READY=$(curl -sf "$API_URL/health/ready")
STATUS=$(echo $READY | jq -r '.status')

if [ "$STATUS" != "healthy" ]; then
  echo "ERROR: Service not ready. Status: $STATUS"
  echo "Components: $(echo $READY | jq '.components')"
  exit 1
fi
echo "Service ready: $STATUS"

# Test API endpoint
echo "Testing API..."
ENGAGEMENTS=$(curl -sf -H "X-API-Key: $API_KEY" "$API_URL/api/v1/engagements")
if [ $? -ne 0 ]; then
  echo "ERROR: API test failed"
  exit 1
fi
echo "API test passed"

echo "Post-upgrade verification complete!"
```

### Functional Tests

```bash
# Run integration tests
pytest tests/integration -v

# Run smoke tests
pytest tests/smoke -v

# Test specific functionality
pytest tests/integration/test_engagements.py -v
```

### Performance Verification

```bash
# Run basic performance test
ab -n 1000 -c 10 http://localhost:8000/health

# Check response times
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:8000/health
```

### Monitoring Verification

```bash
# Check metrics are being collected
curl http://localhost:8000/metrics

# Verify tracing
curl http://localhost:16686/api/services
```

---

## Related Documentation

- [Installation Guide](./installation.md)
- [Backup and Restore](./backup-restore.md)
- [Troubleshooting](./troubleshooting.md)
- [Scaling Guide](./scaling.md)
