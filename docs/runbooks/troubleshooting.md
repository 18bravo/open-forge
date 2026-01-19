# Troubleshooting Guide

This runbook provides solutions for common issues with Open Forge.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Service-Specific Issues](#service-specific-issues)
- [Agent Issues](#agent-issues)
- [Pipeline Issues](#pipeline-issues)
- [Performance Issues](#performance-issues)
- [Common Error Messages](#common-error-messages)
- [Log Analysis](#log-analysis)

---

## Quick Diagnostics

### System Health Check

Run this script to quickly diagnose system health:

```bash
#!/bin/bash
# health_check.sh

echo "=== Open Forge Health Check ==="
echo ""

# Check Docker services
echo "1. Docker Services:"
docker compose -f infrastructure/docker/docker-compose.yml ps --format "table {{.Name}}\t{{.Status}}"
echo ""

# Check API health
echo "2. API Health:"
curl -sf http://localhost:8000/health | jq '.'
echo ""

# Check API readiness
echo "3. API Readiness:"
curl -sf http://localhost:8000/health/ready | jq '.'
echo ""

# Check database connection
echo "4. Database:"
docker compose -f infrastructure/docker/docker-compose.yml exec -T postgres \
  pg_isready -U foundry -d foundry && echo "OK" || echo "FAILED"
echo ""

# Check Redis
echo "5. Redis:"
docker compose -f infrastructure/docker/docker-compose.yml exec -T redis \
  redis-cli ping && echo "OK" || echo "FAILED"
echo ""

# Check MinIO
echo "6. MinIO:"
curl -sf http://localhost:9000/minio/health/live && echo "OK" || echo "FAILED"
echo ""

# Check disk space
echo "7. Disk Space:"
df -h / | tail -1
echo ""

# Check memory
echo "8. Memory:"
free -h | grep Mem
echo ""
```

### Service Status Matrix

| Symptom | Check | Likely Cause |
|---------|-------|--------------|
| API returns 500 | `curl localhost:8000/health` | Database or Redis down |
| API returns 503 | `curl localhost:8000/health/ready` | Dependency not ready |
| Slow responses | Check Jaeger traces | Database or LLM latency |
| Tasks stuck | Check Redis queues | Worker not running |
| UI not loading | Check browser console | Frontend build issue |

---

## Service-Specific Issues

### PostgreSQL Issues

#### Database Not Starting

**Symptoms:** PostgreSQL container exits or restarts repeatedly.

**Check logs:**
```bash
docker compose -f infrastructure/docker/docker-compose.yml logs postgres
```

**Common causes and solutions:**

1. **Corrupt data directory:**
   ```bash
   # Backup existing data
   docker run --rm -v openforge_postgres_data:/data -v $(pwd):/backup alpine \
     tar czf /backup/postgres_backup.tar.gz /data

   # Reset data volume
   docker compose -f infrastructure/docker/docker-compose.yml down
   docker volume rm openforge_postgres_data
   docker compose -f infrastructure/docker/docker-compose.yml up -d postgres

   # Restore from backup if needed
   ./scripts/restore_postgres.sh
   ```

2. **Disk full:**
   ```bash
   # Check disk space
   df -h

   # Clean old WAL files
   docker compose exec postgres pg_archivecleanup /var/lib/postgresql/data/pg_wal 000000010000000000000010
   ```

3. **Memory issues:**
   ```bash
   # Increase shared_buffers in postgresql.conf
   # shared_buffers = 2GB  # Increase based on available RAM
   ```

#### Connection Refused

**Symptoms:** API cannot connect to database.

**Solutions:**
```bash
# Check postgres is listening
docker compose exec postgres pg_isready -U foundry

# Check network connectivity
docker compose exec api nc -zv postgres 5432

# Verify connection string
docker compose exec api env | grep DB_
```

#### Slow Queries

**Symptoms:** API responses are slow.

```bash
# Check running queries
docker compose exec postgres psql -U foundry -c "
  SELECT pid, now() - pg_stat_activity.query_start AS duration, query
  FROM pg_stat_activity
  WHERE state = 'active'
  ORDER BY duration DESC
  LIMIT 10;
"

# Check missing indexes
docker compose exec postgres psql -U foundry -c "
  SELECT relname, seq_scan, idx_scan
  FROM pg_stat_user_tables
  WHERE seq_scan > idx_scan
  ORDER BY seq_scan DESC
  LIMIT 10;
"
```

### Redis Issues

#### Connection Refused

**Check:**
```bash
# Verify Redis is running
docker compose exec redis redis-cli ping

# Check auth
docker compose exec redis redis-cli -a $REDIS_PASSWORD ping
```

**Solution:**
```bash
# Restart Redis
docker compose restart redis
```

#### Memory Full

**Symptoms:** Redis returns OOM errors.

```bash
# Check memory usage
docker compose exec redis redis-cli info memory

# Clear expired keys
docker compose exec redis redis-cli --scan --pattern "*" | head -1000 | xargs docker compose exec -T redis redis-cli DEL

# Configure maxmemory policy
# maxmemory-policy allkeys-lru
```

### MinIO Issues

#### Bucket Not Found

```bash
# List buckets
mc ls local/

# Create missing bucket
mc mb local/foundry-lake
mc mb local/foundry-artifacts
```

#### Access Denied

```bash
# Check credentials
mc alias set local http://localhost:9000 $S3_ACCESS_KEY $S3_SECRET_KEY

# Check bucket policy
mc policy get local/foundry-lake
```

### API Server Issues

#### Service Not Starting

**Check logs:**
```bash
docker compose logs api
```

**Common issues:**

1. **Missing environment variables:**
   ```bash
   docker compose exec api env | grep -E "DB_|REDIS_|ANTHROPIC"
   ```

2. **Import errors:**
   ```bash
   docker compose exec api python -c "from api import get_app; print('OK')"
   ```

3. **Port already in use:**
   ```bash
   lsof -i :8000
   kill -9 <PID>
   ```

#### High Memory Usage

```bash
# Check memory usage
docker stats api

# Restart with memory limit
docker compose down api
docker compose up -d api --memory=2g
```

---

## Agent Issues

### Agent Task Stuck

**Symptoms:** Task status is `running` but no progress.

**Diagnostics:**
```bash
# Check task status
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/api/v1/agents/tasks/$TASK_ID" | jq '.'

# Check agent logs
docker compose logs api | grep -A 20 "$TASK_ID"

# Check Redis queue
docker compose exec redis redis-cli LRANGE agent:tasks:pending 0 -1
```

**Solutions:**

1. **Cancel and retry:**
   ```bash
   curl -X POST -H "X-API-Key: $API_KEY" \
     "http://localhost:8000/api/v1/agents/tasks/$TASK_ID/cancel" \
     -d '{"reason": "Task stuck"}'

   curl -X POST -H "X-API-Key: $API_KEY" \
     "http://localhost:8000/api/v1/agents/tasks/$TASK_ID/retry"
   ```

2. **Check Anthropic API status:**
   ```bash
   curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/v1/messages \
     -d '{"model":"claude-sonnet-4-20250514","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
   ```

### Agent Returns Poor Results

**Symptoms:** Agent output doesn't match expected quality.

**Diagnostics:**
```bash
# Review agent conversation
curl -H "X-API-Key: $API_KEY" \
  "http://localhost:8000/api/v1/agents/tasks/$TASK_ID/messages" | jq '.'
```

**Solutions:**

1. **Improve input context:**
   - Add more specific instructions
   - Provide examples
   - Include relevant data samples

2. **Adjust agent configuration:**
   ```json
   {
     "agent_config": {
       "temperature": 0.2,
       "max_tokens": 8000,
       "system_prompt_additions": "Be precise and thorough."
     }
   }
   ```

### Tool Execution Failures

**Symptoms:** Agent fails when executing tools.

**Check tool logs:**
```bash
docker compose logs api | grep -i "tool" | grep -i "error"
```

**Common issues:**

1. **Database tool fails:**
   - Check database connectivity
   - Verify SQL syntax
   - Check permissions

2. **File tool fails:**
   - Check file path exists
   - Verify permissions
   - Check disk space

---

## Pipeline Issues

### Dagster Not Starting

**Check:**
```bash
docker compose logs dagster-webserver
docker compose logs dagster-daemon
```

**Solutions:**
```bash
# Reset Dagster home
docker compose down dagster-webserver dagster-daemon
docker volume rm openforge_dagster_home
docker compose up -d dagster-webserver dagster-daemon
```

### Pipeline Run Failures

**Diagnostics:**
```bash
# Check run status in Dagster UI
open http://localhost:3000

# Check run logs
docker compose logs dagster-daemon | grep -A 50 "$RUN_ID"
```

**Common causes:**

1. **Resource connection errors:**
   - Check database connectivity
   - Verify S3/MinIO access
   - Check Iceberg catalog

2. **Memory errors:**
   - Increase container memory limits
   - Process data in smaller batches

3. **Data quality issues:**
   - Check input data format
   - Validate schema compatibility

### Sensor Not Triggering

**Check sensor status:**
```bash
# In Dagster UI, navigate to Sensors
# Or check logs
docker compose logs dagster-daemon | grep -i sensor
```

**Solutions:**
- Verify sensor is enabled in UI
- Check sensor interval
- Verify sensor conditions are being met

---

## Performance Issues

### Slow API Responses

**Diagnostics:**

1. **Check Jaeger traces:**
   ```
   http://localhost:16686
   ```

2. **Profile endpoint:**
   ```bash
   curl -w "@curl-format.txt" -o /dev/null -s \
     "http://localhost:8000/api/v1/engagements"
   ```
   Where `curl-format.txt` contains:
   ```
   time_namelookup:  %{time_namelookup}\n
   time_connect:  %{time_connect}\n
   time_appconnect:  %{time_appconnect}\n
   time_pretransfer:  %{time_pretransfer}\n
   time_redirect:  %{time_redirect}\n
   time_starttransfer:  %{time_starttransfer}\n
   time_total:  %{time_total}\n
   ```

**Solutions:**

1. **Add database indexes:**
   ```sql
   CREATE INDEX idx_engagements_status ON engagements(status);
   CREATE INDEX idx_tasks_engagement_id ON agent_tasks(engagement_id);
   ```

2. **Enable query caching:**
   ```python
   # Use Redis cache for frequent queries
   @cached(ttl=300)
   def get_engagement(engagement_id):
       ...
   ```

3. **Scale API replicas:**
   ```bash
   docker compose up -d --scale api=3
   ```

### High Memory Usage

**Check memory:**
```bash
docker stats --no-stream
```

**Solutions:**

1. **Tune PostgreSQL:**
   ```
   shared_buffers = 1GB
   effective_cache_size = 3GB
   work_mem = 256MB
   ```

2. **Limit container memory:**
   ```yaml
   services:
     api:
       deploy:
         resources:
           limits:
             memory: 2G
   ```

3. **Enable swap (temporary):**
   ```bash
   sudo fallocate -l 4G /swapfile
   sudo chmod 600 /swapfile
   sudo mkswap /swapfile
   sudo swapon /swapfile
   ```

---

## Common Error Messages

### "Connection refused"

**Meaning:** Target service is not running or not accepting connections.

**Resolution:**
1. Check if service is running: `docker compose ps`
2. Check service logs: `docker compose logs <service>`
3. Verify port mappings
4. Check firewall rules

### "Authentication failed"

**Meaning:** Invalid credentials.

**Resolution:**
1. Verify environment variables
2. Check secret values
3. Regenerate credentials if needed

### "Rate limit exceeded"

**Meaning:** Too many API requests.

**Resolution:**
1. Implement exponential backoff
2. Use caching
3. Upgrade rate limit tier

### "Out of memory"

**Meaning:** Container or process ran out of memory.

**Resolution:**
1. Increase memory limits
2. Process data in batches
3. Optimize queries

### "Disk full"

**Meaning:** No available disk space.

**Resolution:**
```bash
# Find large files
du -sh /* 2>/dev/null | sort -h | tail -20

# Clean Docker
docker system prune -a --volumes

# Clean logs
find /var/log -name "*.log" -mtime +7 -delete
```

---

## Log Analysis

### Viewing Logs

```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f api

# Last N lines
docker compose logs --tail=100 api

# With timestamps
docker compose logs -t api
```

### Searching Logs

```bash
# Search for errors
docker compose logs api 2>&1 | grep -i error

# Search for specific request
docker compose logs api 2>&1 | grep "req_abc123"

# Search time range (if using structured logging)
docker compose logs api 2>&1 | grep "2024-01-15T14"
```

### Log Aggregation

For production, consider centralized logging:

```yaml
# docker-compose.yml - add logging driver
services:
  api:
    logging:
      driver: "json-file"
      options:
        max-size: "100m"
        max-file: "5"
```

Or use a log aggregation service:
- ELK Stack (Elasticsearch, Logstash, Kibana)
- Loki + Grafana
- Cloud logging (CloudWatch, Stackdriver)

### Debug Mode

Enable debug logging:

```bash
# Set environment variable
export DEBUG=true
export LOG_LEVEL=DEBUG

# Restart services
docker compose up -d
```

---

## Getting Help

### Before Requesting Support

1. Run the health check script
2. Collect relevant logs
3. Note the error message and context
4. Try the troubleshooting steps above

### Submitting a Bug Report

Include:
- Open Forge version
- Environment (Docker/K8s)
- Steps to reproduce
- Expected vs actual behavior
- Relevant logs
- Screenshots if applicable

### Community Resources

- GitHub Issues: Report bugs
- GitHub Discussions: Ask questions
- Documentation: Reference guides

---

## Related Documentation

- [Installation Guide](./installation.md)
- [Upgrade Guide](./upgrade.md)
- [Backup and Restore](./backup-restore.md)
- [Scaling Guide](./scaling.md)
