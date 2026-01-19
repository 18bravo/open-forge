# Backup and Restore Guide

This runbook covers backup and disaster recovery procedures for Open Forge.

## Table of Contents

- [Backup Strategy](#backup-strategy)
- [Component Backups](#component-backups)
- [Automated Backup Scripts](#automated-backup-scripts)
- [Restore Procedures](#restore-procedures)
- [Disaster Recovery](#disaster-recovery)
- [Testing Backups](#testing-backups)

---

## Backup Strategy

### What to Backup

| Component | Data Type | Backup Frequency | Retention |
|-----------|-----------|------------------|-----------|
| PostgreSQL | Database | Hourly incremental, Daily full | 30 days |
| Redis | Cache/Sessions | Daily (optional) | 7 days |
| MinIO | Object storage | Daily incremental | 90 days |
| Iceberg | Data lake | Daily incremental | 90 days |
| Configurations | YAML/env files | On change | Forever |
| Secrets | Credentials | On change | Forever |

### Backup Types

1. **Full Backup**: Complete copy of all data
2. **Incremental Backup**: Changes since last backup
3. **Snapshot**: Point-in-time copy (for cloud storage)

### RPO and RTO Targets

| Tier | RPO (Data Loss) | RTO (Downtime) |
|------|-----------------|----------------|
| Critical | 1 hour | 4 hours |
| Standard | 24 hours | 24 hours |
| Development | 1 week | 48 hours |

---

## Component Backups

### PostgreSQL Backup

#### Full Backup

```bash
#!/bin/bash
# backup_postgres_full.sh

BACKUP_DIR="/backups/postgres"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/full_${TIMESTAMP}.sql.gz"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Full database backup
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  pg_dump -U foundry -Fc foundry | gzip > "$BACKUP_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ] && [ -s "$BACKUP_FILE" ]; then
  echo "Backup created: $BACKUP_FILE ($(du -h $BACKUP_FILE | cut -f1))"
else
  echo "ERROR: Backup failed!"
  exit 1
fi

# Clean old backups (keep last 30 days)
find "$BACKUP_DIR" -name "full_*.sql.gz" -mtime +30 -delete
```

#### Incremental Backup with WAL

```bash
# Enable WAL archiving in postgresql.conf
# archive_mode = on
# archive_command = 'cp %p /backups/postgres/wal/%f'

# Archive current WAL segment
docker compose exec postgres pg_switch_wal
```

#### Kubernetes PostgreSQL Backup

```yaml
# backup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: postgres-backup
  namespace: open-forge
spec:
  schedule: "0 2 * * *"  # 2 AM daily
  jobTemplate:
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
                  TIMESTAMP=$(date +%Y%m%d_%H%M%S)
                  pg_dump -h postgres -U foundry -Fc foundry | \
                    gzip > /backup/postgres_${TIMESTAMP}.sql.gz
                  # Upload to S3
                  aws s3 cp /backup/postgres_${TIMESTAMP}.sql.gz \
                    s3://backups/postgres/
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
              emptyDir: {}
          restartPolicy: OnFailure
```

### Redis Backup

```bash
#!/bin/bash
# backup_redis.sh

BACKUP_DIR="/backups/redis"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Trigger RDB snapshot
docker compose -f infrastructure/docker/docker-compose.yml exec redis \
  redis-cli BGSAVE

# Wait for save to complete
sleep 5

# Copy RDB file
docker compose -f infrastructure/docker/docker-compose.yml exec redis \
  cat /data/dump.rdb > "${BACKUP_DIR}/redis_${TIMESTAMP}.rdb"

echo "Redis backup created: redis_${TIMESTAMP}.rdb"
```

### MinIO Backup

```bash
#!/bin/bash
# backup_minio.sh

BACKUP_DIR="/backups/minio"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BUCKETS=("foundry-lake" "foundry-artifacts")

mkdir -p "$BACKUP_DIR"

# Configure mc client
mc alias set local http://localhost:9000 $S3_ACCESS_KEY $S3_SECRET_KEY

# Sync each bucket
for bucket in "${BUCKETS[@]}"; do
  mc mirror local/$bucket "${BACKUP_DIR}/${bucket}_${TIMESTAMP}/"
done

# Or sync to remote S3
# mc mirror local/foundry-lake s3/backups/minio/foundry-lake/
```

### Iceberg Tables Backup

```bash
#!/bin/bash
# backup_iceberg.sh

# Iceberg tables are stored in MinIO, so backing up MinIO backs up Iceberg data
# However, we also need to backup the catalog metadata

BACKUP_DIR="/backups/iceberg"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Export catalog metadata
curl -X GET "http://localhost:8181/v1/namespaces" \
  -H "Content-Type: application/json" > "${BACKUP_DIR}/namespaces_${TIMESTAMP}.json"

# Export table metadata for each namespace
for ns in $(cat "${BACKUP_DIR}/namespaces_${TIMESTAMP}.json" | jq -r '.namespaces[][]'); do
  curl -X GET "http://localhost:8181/v1/namespaces/${ns}/tables" \
    -H "Content-Type: application/json" > "${BACKUP_DIR}/${ns}_tables_${TIMESTAMP}.json"
done
```

### Configuration Backup

```bash
#!/bin/bash
# backup_configs.sh

BACKUP_DIR="/backups/configs"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup environment files (without secrets)
grep -v "PASSWORD\|SECRET\|KEY" .env > "${BACKUP_DIR}/env_${TIMESTAMP}.txt"

# Backup Kubernetes configs
kubectl get configmap -n open-forge -o yaml > "${BACKUP_DIR}/configmaps_${TIMESTAMP}.yaml"

# Backup Helm values
helm get values open-forge -n open-forge > "${BACKUP_DIR}/helm_values_${TIMESTAMP}.yaml"
```

---

## Automated Backup Scripts

### Complete Backup Script

```bash
#!/bin/bash
# backup_all.sh
# Full backup script for all Open Forge components

set -e

BACKUP_ROOT="${BACKUP_ROOT:-/backups}"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="${BACKUP_ROOT}/${TIMESTAMP}"
LOG_FILE="${BACKUP_DIR}/backup.log"

# Create backup directory
mkdir -p "$BACKUP_DIR"

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "Starting backup to $BACKUP_DIR"

# PostgreSQL backup
log "Backing up PostgreSQL..."
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  pg_dump -U foundry -Fc foundry > "${BACKUP_DIR}/postgres.dump"
log "PostgreSQL backup complete: $(du -h ${BACKUP_DIR}/postgres.dump | cut -f1)"

# Redis backup
log "Backing up Redis..."
docker compose -f infrastructure/docker/docker-compose.yml exec -T redis \
  redis-cli BGSAVE
sleep 5
docker compose -f infrastructure/docker/docker-compose.yml exec -T redis \
  cat /data/dump.rdb > "${BACKUP_DIR}/redis.rdb"
log "Redis backup complete"

# MinIO backup
log "Backing up MinIO buckets..."
mc mirror local/foundry-lake "${BACKUP_DIR}/foundry-lake/"
mc mirror local/foundry-artifacts "${BACKUP_DIR}/foundry-artifacts/"
log "MinIO backup complete"

# Configuration backup
log "Backing up configurations..."
grep -v "PASSWORD\|SECRET\|KEY" .env > "${BACKUP_DIR}/env.txt"
cp docker-compose.yml "${BACKUP_DIR}/"
log "Configuration backup complete"

# Create manifest
log "Creating backup manifest..."
cat > "${BACKUP_DIR}/manifest.json" <<EOF
{
  "timestamp": "${TIMESTAMP}",
  "version": "$(curl -s localhost:8000/health | jq -r '.version')",
  "components": {
    "postgres": "$(du -h ${BACKUP_DIR}/postgres.dump | cut -f1)",
    "redis": "$(du -h ${BACKUP_DIR}/redis.rdb | cut -f1)",
    "minio_lake": "$(du -sh ${BACKUP_DIR}/foundry-lake | cut -f1)",
    "minio_artifacts": "$(du -sh ${BACKUP_DIR}/foundry-artifacts | cut -f1)"
  }
}
EOF

# Compress backup
log "Compressing backup..."
cd "$BACKUP_ROOT"
tar czf "${TIMESTAMP}.tar.gz" "$TIMESTAMP"
rm -rf "$TIMESTAMP"

# Upload to remote storage
log "Uploading to remote storage..."
aws s3 cp "${TIMESTAMP}.tar.gz" "s3://openforge-backups/${TIMESTAMP}.tar.gz"

log "Backup complete: ${TIMESTAMP}.tar.gz"

# Clean old local backups (keep last 7 days)
find "$BACKUP_ROOT" -name "*.tar.gz" -mtime +7 -delete
```

### Cron Configuration

```bash
# /etc/cron.d/openforge-backup

# Full backup daily at 2 AM
0 2 * * * root /opt/open-forge/scripts/backup_all.sh >> /var/log/openforge-backup.log 2>&1

# PostgreSQL incremental every hour
0 * * * * root /opt/open-forge/scripts/backup_postgres_incremental.sh

# Cleanup old backups weekly
0 3 * * 0 root find /backups -mtime +30 -delete
```

---

## Restore Procedures

### PostgreSQL Restore

#### Full Restore

```bash
#!/bin/bash
# restore_postgres.sh

BACKUP_FILE=${1:-"latest"}

if [ "$BACKUP_FILE" = "latest" ]; then
  BACKUP_FILE=$(ls -t /backups/postgres/full_*.sql.gz | head -1)
fi

echo "Restoring from: $BACKUP_FILE"

# Stop application services
docker compose -f infrastructure/docker/docker-compose.yml stop api dagster-webserver dagster-daemon

# Drop and recreate database
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  psql -U foundry -c "DROP DATABASE IF EXISTS foundry;"
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  psql -U foundry -c "CREATE DATABASE foundry;"

# Restore from backup
gunzip -c "$BACKUP_FILE" | \
  docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  pg_restore -U foundry -d foundry

# Restart services
docker compose -f infrastructure/docker/docker-compose.yml up -d

echo "Restore complete"
```

#### Point-in-Time Recovery

```bash
# Restore to specific point in time using WAL
recovery_target_time = '2024-01-15 14:30:00'
```

### Redis Restore

```bash
#!/bin/bash
# restore_redis.sh

BACKUP_FILE=${1:-"/backups/redis/redis_latest.rdb"}

# Stop Redis
docker compose -f infrastructure/docker/docker-compose.yml stop redis

# Copy RDB file
docker compose -f infrastructure/docker/docker-compose.yml run --rm -v "${BACKUP_FILE}:/restore/dump.rdb" redis \
  cp /restore/dump.rdb /data/dump.rdb

# Start Redis
docker compose -f infrastructure/docker/docker-compose.yml up -d redis

echo "Redis restore complete"
```

### MinIO Restore

```bash
#!/bin/bash
# restore_minio.sh

BACKUP_DIR=${1:-"/backups/minio/latest"}

# Restore buckets
mc mirror "${BACKUP_DIR}/foundry-lake/" local/foundry-lake/
mc mirror "${BACKUP_DIR}/foundry-artifacts/" local/foundry-artifacts/

echo "MinIO restore complete"
```

### Full System Restore

```bash
#!/bin/bash
# restore_all.sh

BACKUP_ARCHIVE=${1:-"latest"}

if [ "$BACKUP_ARCHIVE" = "latest" ]; then
  # Download latest from S3
  BACKUP_ARCHIVE=$(aws s3 ls s3://openforge-backups/ | sort | tail -n 1 | awk '{print $4}')
  aws s3 cp "s3://openforge-backups/${BACKUP_ARCHIVE}" /tmp/
  BACKUP_ARCHIVE="/tmp/${BACKUP_ARCHIVE}"
fi

# Extract backup
RESTORE_DIR="/tmp/restore_$(date +%s)"
mkdir -p "$RESTORE_DIR"
tar xzf "$BACKUP_ARCHIVE" -C "$RESTORE_DIR"
BACKUP_DIR=$(ls "$RESTORE_DIR")

echo "Restoring from: $BACKUP_DIR"

# Stop all services
docker compose -f infrastructure/docker/docker-compose.yml down

# Start only databases
docker compose -f infrastructure/docker/docker-compose.yml up -d postgres redis minio

sleep 10

# Restore PostgreSQL
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  pg_restore -U foundry -d foundry "${RESTORE_DIR}/${BACKUP_DIR}/postgres.dump"

# Restore MinIO
mc mirror "${RESTORE_DIR}/${BACKUP_DIR}/foundry-lake/" local/foundry-lake/
mc mirror "${RESTORE_DIR}/${BACKUP_DIR}/foundry-artifacts/" local/foundry-artifacts/

# Start all services
docker compose -f infrastructure/docker/docker-compose.yml up -d

# Cleanup
rm -rf "$RESTORE_DIR"

echo "Full restore complete"
```

---

## Disaster Recovery

### DR Runbook

#### Step 1: Assess Situation

```bash
# Check current system status
docker compose -f infrastructure/docker/docker-compose.yml ps
docker compose -f infrastructure/docker/docker-compose.yml logs --tail=100
```

#### Step 2: Notify Stakeholders

- Alert on-call engineer
- Update status page
- Notify affected users

#### Step 3: Execute Recovery

```bash
# Option A: Restore from backup
./scripts/restore_all.sh latest

# Option B: Failover to DR site
./scripts/failover_to_dr.sh

# Option C: Rebuild from scratch
./scripts/rebuild_environment.sh
```

#### Step 4: Verify Recovery

```bash
# Run health checks
curl http://localhost:8000/health/ready

# Run smoke tests
pytest tests/smoke -v

# Verify data integrity
./scripts/verify_data_integrity.sh
```

#### Step 5: Post-Incident

- Document timeline
- Identify root cause
- Update procedures

### DR Site Setup

```yaml
# dr-site/docker-compose.yml
# Identical configuration for DR site
# Kept in sync via backup replication

services:
  postgres:
    image: apache/age:latest
    volumes:
      - dr_postgres_data:/var/lib/postgresql/data
    # Configure as replica or from backup

volumes:
  dr_postgres_data:
```

### Cross-Region Replication

```bash
# Sync backups to DR region
aws s3 sync s3://openforge-backups-primary s3://openforge-backups-dr \
  --source-region us-east-1 \
  --region us-west-2
```

---

## Testing Backups

### Backup Verification Script

```bash
#!/bin/bash
# verify_backup.sh

BACKUP_FILE=${1}

echo "Verifying backup: $BACKUP_FILE"

# Test archive integrity
if ! tar tzf "$BACKUP_FILE" > /dev/null 2>&1; then
  echo "ERROR: Archive is corrupted"
  exit 1
fi
echo "Archive integrity: OK"

# Extract to temp directory
TEMP_DIR=$(mktemp -d)
tar xzf "$BACKUP_FILE" -C "$TEMP_DIR"

# Verify PostgreSQL dump
if ! pg_restore --list "${TEMP_DIR}/*/postgres.dump" > /dev/null 2>&1; then
  echo "ERROR: PostgreSQL dump is invalid"
  exit 1
fi
echo "PostgreSQL dump: OK"

# Verify manifest
if [ ! -f "${TEMP_DIR}/*/manifest.json" ]; then
  echo "WARNING: No manifest found"
else
  echo "Manifest: OK"
  cat "${TEMP_DIR}/*/manifest.json"
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo "Backup verification complete"
```

### Restore Testing

```bash
#!/bin/bash
# test_restore.sh
# Test restore in isolated environment

# Create isolated network
docker network create restore-test

# Start test database
docker run -d --name test-postgres --network restore-test \
  -e POSTGRES_USER=foundry \
  -e POSTGRES_PASSWORD=test \
  -e POSTGRES_DB=foundry \
  postgres:15

sleep 10

# Restore backup
docker run --rm --network restore-test \
  -v /backups/postgres/latest.sql.gz:/backup.sql.gz \
  postgres:15 \
  bash -c "gunzip -c /backup.sql.gz | psql -h test-postgres -U foundry -d foundry"

# Verify data
docker exec test-postgres psql -U foundry -d foundry \
  -c "SELECT COUNT(*) FROM engagements;"

# Cleanup
docker stop test-postgres
docker rm test-postgres
docker network rm restore-test
```

### Monthly DR Drill

```bash
#!/bin/bash
# dr_drill.sh
# Monthly disaster recovery drill

echo "Starting DR drill at $(date)"

# Document start state
./scripts/capture_state.sh > /tmp/pre_drill_state.txt

# Simulate disaster (stop primary)
docker compose -f infrastructure/docker/docker-compose.yml down

# Restore from backup
./scripts/restore_all.sh latest

# Verify functionality
./scripts/run_smoke_tests.sh

# Document end state
./scripts/capture_state.sh > /tmp/post_drill_state.txt

# Compare states
diff /tmp/pre_drill_state.txt /tmp/post_drill_state.txt

echo "DR drill complete at $(date)"
```

---

## Related Documentation

- [Installation Guide](./installation.md)
- [Upgrade Guide](./upgrade.md)
- [Troubleshooting](./troubleshooting.md)
- [Scaling Guide](./scaling.md)
