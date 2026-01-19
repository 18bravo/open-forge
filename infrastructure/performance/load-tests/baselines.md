# Open Forge Performance Baselines

This document defines the expected performance characteristics and targets for Open Forge services.

## Table of Contents

1. [Overview](#overview)
2. [API Performance Baselines](#api-performance-baselines)
3. [Pipeline Performance Baselines](#pipeline-performance-baselines)
4. [Database Performance Baselines](#database-performance-baselines)
5. [Infrastructure Targets](#infrastructure-targets)
6. [Monitoring and Alerting](#monitoring-and-alerting)

## Overview

Performance baselines are established through regular load testing and production monitoring. These baselines serve as:

- **Acceptance criteria** for deployments
- **Alert thresholds** for monitoring
- **Capacity planning** inputs
- **SLA foundations** for service agreements

### Baseline Categories

| Category | Description |
|----------|-------------|
| P50 | 50th percentile (median) response time |
| P95 | 95th percentile response time |
| P99 | 99th percentile response time |
| Throughput | Requests per second (RPS) |
| Error Rate | Percentage of failed requests |

## API Performance Baselines

### Response Time Targets

| Endpoint | P50 | P95 | P99 | Max |
|----------|-----|-----|-----|-----|
| `GET /health` | 5ms | 50ms | 100ms | 200ms |
| `GET /api/v1/engagements` | 30ms | 200ms | 500ms | 1s |
| `GET /api/v1/engagements/{id}` | 20ms | 150ms | 300ms | 500ms |
| `POST /api/v1/engagements` | 50ms | 300ms | 700ms | 1s |
| `PATCH /api/v1/engagements/{id}` | 40ms | 250ms | 500ms | 1s |
| `DELETE /api/v1/engagements/{id}` | 30ms | 200ms | 400ms | 800ms |
| `POST /api/v1/agents/tasks` | 100ms | 1s | 2s | 5s |
| `GET /api/v1/agents/tasks/{id}` | 20ms | 150ms | 300ms | 500ms |
| `GET /api/v1/datasources` | 50ms | 300ms | 600ms | 1s |
| `POST /api/v1/datasources/{id}/query` | 200ms | 1s | 2s | 10s |
| `POST /api/v1/auth/login` | 100ms | 500ms | 1s | 2s |
| `GET /api/v1/users/me` | 20ms | 100ms | 200ms | 500ms |

### Throughput Targets

| Scenario | API Replicas | Target RPS | Max RPS |
|----------|--------------|------------|---------|
| Normal Load | 2 | 100 | 200 |
| High Load | 5 | 300 | 500 |
| Peak Load | 10 | 500 | 1000 |

### Error Rate Targets

| Condition | Target | Alert Threshold | Critical Threshold |
|-----------|--------|-----------------|-------------------|
| Normal | < 0.1% | > 1% | > 5% |
| High Load | < 0.5% | > 2% | > 10% |
| Degraded | < 2% | > 5% | > 15% |

## Pipeline Performance Baselines

### Dagster Operations

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| GraphQL Query (simple) | 50ms | 200ms | 500ms | 1s |
| GraphQL Query (complex) | 200ms | 1s | 2s | 5s |
| Launch Pipeline | 500ms | 2s | 5s | 10s |
| Get Run Status | 20ms | 100ms | 300ms | 500ms |
| List Runs (20 items) | 100ms | 500ms | 1s | 2s |
| Sensor Tick Check | 50ms | 200ms | 500ms | 1s |

### Pipeline Run Durations

| Pipeline Type | P50 | P95 | P99 | Max |
|---------------|-----|-----|-----|-----|
| Data Ingestion (small) | 30s | 2m | 5m | 10m |
| Data Ingestion (large) | 5m | 15m | 30m | 1h |
| Embedding Generation | 2m | 10m | 20m | 30m |
| Report Generation | 1m | 5m | 10m | 20m |
| Full ETL Pipeline | 10m | 30m | 1h | 2h |

### Concurrent Run Limits

| Resource | Development | Staging | Production |
|----------|-------------|---------|------------|
| Max Concurrent Runs | 5 | 10 | 25 |
| Max Queued Runs | 20 | 50 | 100 |
| Run Worker Pods | 2 | 5 | 10 |

## Database Performance Baselines

### PostgreSQL

| Query Type | P50 | P95 | P99 | Max |
|------------|-----|-----|-----|-----|
| Simple SELECT | 1ms | 5ms | 10ms | 50ms |
| Indexed SELECT | 2ms | 10ms | 25ms | 100ms |
| Complex JOIN | 10ms | 50ms | 100ms | 500ms |
| INSERT (single) | 2ms | 10ms | 25ms | 100ms |
| BATCH INSERT (100) | 20ms | 100ms | 250ms | 1s |
| UPDATE (indexed) | 3ms | 15ms | 50ms | 200ms |
| DELETE (indexed) | 3ms | 15ms | 50ms | 200ms |
| Vector Search (pgvector) | 50ms | 200ms | 500ms | 2s |

### Connection Pool Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Active Connections | < 80% of max | > 80% | > 95% |
| Connection Wait Time | < 10ms | > 50ms | > 200ms |
| Transactions/sec | Based on load | N/A | N/A |

### Redis

| Operation | P50 | P95 | P99 | Max |
|-----------|-----|-----|-----|-----|
| GET | 0.1ms | 0.5ms | 1ms | 5ms |
| SET | 0.1ms | 0.5ms | 1ms | 5ms |
| MGET (10 keys) | 0.5ms | 2ms | 5ms | 20ms |
| SCAN (100 keys) | 1ms | 5ms | 10ms | 50ms |
| ZADD | 0.2ms | 1ms | 2ms | 10ms |
| ZRANGE | 0.5ms | 2ms | 5ms | 20ms |

### Cache Metrics

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Hit Rate | > 80% | < 70% | < 50% |
| Miss Rate | < 20% | > 30% | > 50% |
| Eviction Rate | < 100/min | > 500/min | > 1000/min |
| Memory Usage | < 80% | > 85% | > 95% |

## Infrastructure Targets

### Resource Utilization

| Component | CPU Target | CPU Alert | Memory Target | Memory Alert |
|-----------|------------|-----------|---------------|--------------|
| API Pods | 40-60% | > 70% | 50-70% | > 80% |
| Dagster Webserver | 30-50% | > 60% | 40-60% | > 70% |
| Dagster Daemon | 20-40% | > 60% | 30-50% | > 70% |
| PostgreSQL | 40-60% | > 70% | 60-80% | > 85% |
| Redis | 30-50% | > 60% | 60-80% | > 90% |
| UI Pods | 20-40% | > 60% | 30-50% | > 70% |

### Network Performance

| Metric | Target | Warning | Critical |
|--------|--------|---------|----------|
| Pod-to-Pod Latency | < 1ms | > 5ms | > 10ms |
| Service DNS Resolution | < 5ms | > 20ms | > 50ms |
| External API Latency | < 100ms | > 500ms | > 1s |
| Ingress Latency | < 10ms | > 50ms | > 100ms |

### Storage Performance

| Storage Type | IOPS Target | Latency Target | Throughput |
|--------------|-------------|----------------|------------|
| PostgreSQL SSD | 3000 | < 2ms | 125 MB/s |
| Redis SSD | 3000 | < 1ms | 125 MB/s |
| MinIO/S3 | N/A | < 50ms | 100 MB/s |

## Monitoring and Alerting

### SLI Definitions

| Service Level Indicator | Definition | Target |
|------------------------|------------|--------|
| Availability | Successful requests / Total requests | 99.9% |
| Latency (API) | P95 response time < threshold | 99% |
| Latency (Pipeline) | Pipeline completion within timeout | 95% |
| Error Rate | Error requests / Total requests | < 0.1% |

### SLO Targets

| SLO | Target | Measurement Window |
|-----|--------|-------------------|
| API Availability | 99.9% | 30 days |
| API P95 Latency < 500ms | 99% | 7 days |
| Pipeline Success Rate | 95% | 7 days |
| Cache Hit Rate | 80% | 24 hours |

### Alert Thresholds

```yaml
# PrometheusRule alert thresholds
alerts:
  api:
    high_latency:
      warning: "p95 > 500ms for 5m"
      critical: "p95 > 1s for 5m"
    high_error_rate:
      warning: "error_rate > 1% for 5m"
      critical: "error_rate > 5% for 2m"
    low_availability:
      warning: "success_rate < 99.5% for 10m"
      critical: "success_rate < 99% for 5m"

  database:
    high_connections:
      warning: "connections > 80% for 5m"
      critical: "connections > 95% for 2m"
    slow_queries:
      warning: "slow_queries > 10/min for 5m"
      critical: "slow_queries > 50/min for 2m"

  pipeline:
    run_queue_depth:
      warning: "queue_depth > 20 for 10m"
      critical: "queue_depth > 50 for 5m"
    run_failure_rate:
      warning: "failure_rate > 10% for 30m"
      critical: "failure_rate > 25% for 15m"
```

### Load Test Schedule

| Test Type | Frequency | Environment | Duration |
|-----------|-----------|-------------|----------|
| Smoke | Every deployment | All | 1-2 min |
| Load | Weekly | Staging | 15 min |
| Stress | Monthly | Staging | 30 min |
| Soak | Quarterly | Staging | 2-4 hours |

### Baseline Review Process

1. **Monthly Review**: Compare current performance against baselines
2. **Quarterly Update**: Adjust baselines based on:
   - Infrastructure changes
   - Feature additions
   - Traffic pattern changes
3. **Incident Postmortem**: Update baselines if performance regressions are accepted
4. **Capacity Planning**: Use baselines for growth projections

## Appendix: Benchmark Commands

```bash
# Run smoke test
k6 run api-load.js --env SCENARIO=smoke

# Run load test with output
k6 run api-load.js --env SCENARIO=load --out json=results/load-test.json

# Run stress test
k6 run api-load.js --env SCENARIO=stress --env BASE_URL=https://api.staging.example.com

# Run pipeline test
k6 run pipeline-load.js --env SCENARIO=concurrent --env DAGSTER_URL=https://dagster.staging.example.com

# Generate HTML report (requires k6 extension)
k6 run api-load.js --out json=results/output.json && k6-reporter results/output.json
```
