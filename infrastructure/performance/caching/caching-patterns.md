# Open Forge Caching Patterns and Best Practices

This document describes the caching strategies and patterns used in Open Forge for optimal performance.

## Table of Contents

1. [Overview](#overview)
2. [Cache Architecture](#cache-architecture)
3. [Caching Patterns](#caching-patterns)
4. [Python Implementation](#python-implementation)
5. [Cache Key Conventions](#cache-key-conventions)
6. [TTL Strategies](#ttl-strategies)
7. [Cache Invalidation](#cache-invalidation)
8. [Monitoring](#monitoring)

## Overview

Open Forge uses Redis as the primary caching layer with the following objectives:

- Reduce database load for frequently accessed data
- Improve API response times
- Cache expensive computations (embeddings, aggregations)
- Support session management and rate limiting

## Cache Architecture

```
                                    +------------------+
                                    |   CDN (Static)   |
                                    +--------+---------+
                                             |
+------------+     +----------+     +--------v---------+     +------------+
|   Client   +---->+  Ingress +---->+    API Server    +---->+ PostgreSQL |
+------------+     +----------+     +--------+---------+     +------------+
                                             |
                                    +--------v---------+
                                    |      Redis       |
                                    | (Cache + Queue)  |
                                    +------------------+
```

## Caching Patterns

### 1. Cache-Aside (Lazy Loading)

The primary pattern for most read operations.

```python
# Pattern: Application manages cache reads and writes
async def get_engagement(engagement_id: str) -> Engagement:
    # Try cache first
    cached = await cache.get(f"engagement:{engagement_id}")
    if cached:
        return Engagement.parse_raw(cached)

    # Cache miss - fetch from database
    engagement = await db.get_engagement(engagement_id)

    # Populate cache for next time
    await cache.set(
        f"engagement:{engagement_id}",
        engagement.json(),
        ex=3600  # 1 hour TTL
    )

    return engagement
```

### 2. Write-Through

For data that must be immediately consistent.

```python
# Pattern: Write to cache and database simultaneously
async def update_engagement(engagement_id: str, data: EngagementUpdate):
    # Update database
    engagement = await db.update_engagement(engagement_id, data)

    # Update cache synchronously
    await cache.set(
        f"engagement:{engagement_id}",
        engagement.json(),
        ex=3600
    )

    return engagement
```

### 3. Write-Behind (Write-Back)

For high-write scenarios where eventual consistency is acceptable.

```python
# Pattern: Write to cache, asynchronously persist to database
async def log_agent_activity(agent_id: str, activity: Activity):
    # Write to cache immediately
    await cache.lpush(f"agent:activity:{agent_id}", activity.json())

    # Queue for async database write
    await queue.enqueue(
        "persist_agent_activity",
        agent_id=agent_id,
        activity=activity
    )
```

### 4. Read-Through with Refresh

For data that should be pre-warmed.

```python
# Pattern: Background refresh before expiration
async def get_dashboard_stats(org_id: str) -> DashboardStats:
    cache_key = f"dashboard:stats:{org_id}"
    ttl = await cache.ttl(cache_key)

    # If TTL is low, trigger background refresh
    if ttl and ttl < 300:  # Less than 5 minutes remaining
        background_tasks.add_task(refresh_dashboard_stats, org_id)

    cached = await cache.get(cache_key)
    if cached:
        return DashboardStats.parse_raw(cached)

    # Cache miss - compute and store
    stats = await compute_dashboard_stats(org_id)
    await cache.set(cache_key, stats.json(), ex=3600)

    return stats
```

## Python Implementation

### Redis Cache Decorator

```python
# packages/api/app/core/cache.py

import functools
import hashlib
import json
from typing import Any, Callable, Optional, TypeVar, Union
from redis.asyncio import Redis
from datetime import timedelta

T = TypeVar("T")


class CacheConfig:
    """Cache configuration settings."""

    DEFAULT_TTL = 3600  # 1 hour
    SHORT_TTL = 300     # 5 minutes
    MEDIUM_TTL = 1800   # 30 minutes
    LONG_TTL = 86400    # 24 hours

    # TTL by data type
    TTL_MAP = {
        "engagement": MEDIUM_TTL,
        "agent": SHORT_TTL,
        "data_source": LONG_TTL,
        "user": MEDIUM_TTL,
        "config": LONG_TTL,
        "embedding": LONG_TTL,
    }


def cache_key(*args, prefix: str = "", **kwargs) -> str:
    """Generate a consistent cache key from arguments."""
    key_data = {
        "args": args,
        "kwargs": sorted(kwargs.items())
    }
    key_hash = hashlib.md5(
        json.dumps(key_data, sort_keys=True, default=str).encode()
    ).hexdigest()[:16]

    return f"{prefix}:{key_hash}" if prefix else key_hash


def cached(
    prefix: str,
    ttl: Optional[int] = None,
    key_builder: Optional[Callable[..., str]] = None,
    condition: Optional[Callable[..., bool]] = None,
):
    """
    Decorator for caching function results in Redis.

    Args:
        prefix: Cache key prefix (e.g., "engagement", "agent")
        ttl: Time-to-live in seconds (default from TTL_MAP or DEFAULT_TTL)
        key_builder: Custom function to build cache key
        condition: Function to determine if result should be cached

    Example:
        @cached(prefix="engagement", ttl=1800)
        async def get_engagement(engagement_id: str) -> Engagement:
            return await db.get_engagement(engagement_id)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Get Redis client from context
            redis: Redis = kwargs.pop("_redis", None) or get_redis()

            # Build cache key
            if key_builder:
                cache_k = key_builder(*args, **kwargs)
            else:
                cache_k = cache_key(*args, prefix=prefix, **kwargs)

            # Try to get from cache
            cached_value = await redis.get(cache_k)
            if cached_value is not None:
                return json.loads(cached_value)

            # Execute function
            result = await func(*args, **kwargs)

            # Check if we should cache the result
            should_cache = condition is None or condition(result)

            if should_cache and result is not None:
                # Determine TTL
                cache_ttl = ttl or CacheConfig.TTL_MAP.get(
                    prefix, CacheConfig.DEFAULT_TTL
                )

                # Store in cache
                await redis.set(
                    cache_k,
                    json.dumps(result, default=str),
                    ex=cache_ttl
                )

            return result

        return wrapper
    return decorator


def invalidate_cache(pattern: str):
    """
    Decorator to invalidate cache entries after function execution.

    Args:
        pattern: Cache key pattern to invalidate (supports wildcards)

    Example:
        @invalidate_cache("engagement:{engagement_id}*")
        async def update_engagement(engagement_id: str, data: dict):
            return await db.update_engagement(engagement_id, data)
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            # Execute function first
            result = await func(*args, **kwargs)

            # Get Redis client
            redis: Redis = kwargs.pop("_redis", None) or get_redis()

            # Build invalidation pattern from function arguments
            invalidation_pattern = pattern.format(**kwargs)

            # Invalidate matching keys
            async for key in redis.scan_iter(match=invalidation_pattern):
                await redis.delete(key)

            return result

        return wrapper
    return decorator


class CacheManager:
    """
    Centralized cache management for Open Forge.
    """

    def __init__(self, redis: Redis):
        self.redis = redis

    async def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
    ) -> None:
        """Set a value in cache."""
        await self.redis.set(
            key,
            json.dumps(value, default=str),
            ex=ttl or CacheConfig.DEFAULT_TTL
        )

    async def delete(self, key: str) -> None:
        """Delete a key from cache."""
        await self.redis.delete(key)

    async def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        count = 0
        async for key in self.redis.scan_iter(match=pattern):
            await self.redis.delete(key)
            count += 1
        return count

    async def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Any:
        """Get from cache or compute and store."""
        value = await self.get(key)
        if value is not None:
            return value

        value = await factory()
        await self.set(key, value, ttl)
        return value

    async def increment(
        self,
        key: str,
        amount: int = 1,
        ttl: Optional[int] = None,
    ) -> int:
        """Atomic increment with optional TTL."""
        pipe = self.redis.pipeline()
        pipe.incrby(key, amount)
        if ttl:
            pipe.expire(key, ttl)
        results = await pipe.execute()
        return results[0]

    async def rate_limit(
        self,
        key: str,
        limit: int,
        window: int,
    ) -> tuple[bool, int]:
        """
        Check rate limit using sliding window.

        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        current = await self.increment(key, ttl=window)
        remaining = max(0, limit - current)
        allowed = current <= limit
        return allowed, remaining
```

## Cache Key Conventions

### Key Structure

```
{entity_type}:{identifier}:{sub_type}
```

### Examples

```
# Engagement data
engagement:550e8400-e29b-41d4-a716-446655440000

# Engagement with sub-resource
engagement:550e8400-e29b-41d4-a716-446655440000:tasks

# Agent data
agent:agent-001:config

# User session
session:user-123:token

# Rate limiting
ratelimit:api:user-123

# Dashboard cache
dashboard:org-456:stats

# Search results
search:embeddings:query_hash_abc123

# Computed aggregations
agg:engagement:550e8400:metrics:daily
```

### Key Prefixes by Domain

| Domain | Prefix | Example |
|--------|--------|---------|
| Engagements | `engagement:` | `engagement:{id}` |
| Agents | `agent:` | `agent:{id}:config` |
| Data Sources | `datasource:` | `datasource:{id}:schema` |
| Users | `user:` | `user:{id}:preferences` |
| Sessions | `session:` | `session:{token}` |
| Rate Limits | `ratelimit:` | `ratelimit:{endpoint}:{user_id}` |
| Embeddings | `embedding:` | `embedding:{hash}` |
| Pipelines | `pipeline:` | `pipeline:{id}:status` |

## TTL Strategies

### By Data Volatility

| Category | TTL | Use Case |
|----------|-----|----------|
| Real-time | 30-60s | Live metrics, active status |
| Volatile | 5 min | Agent task status, session data |
| Standard | 30 min | Engagement data, user profiles |
| Stable | 1-24 hours | Configuration, schemas, embeddings |
| Permanent | No expiry | Reference data (use with caution) |

### TTL Configuration

```python
TTL_CONFIG = {
    # Real-time data
    "agent:status": 60,
    "pipeline:run:status": 30,

    # Volatile data
    "session": 300,
    "ratelimit": 60,

    # Standard data
    "engagement": 1800,
    "user:profile": 1800,
    "dashboard:stats": 900,

    # Stable data
    "datasource:schema": 86400,
    "embedding": 86400,
    "config": 3600,
}
```

## Cache Invalidation

### Strategies

1. **Time-based Expiration (TTL)**
   - Simplest approach
   - Data becomes stale until TTL expires
   - Suitable for data that can tolerate staleness

2. **Event-driven Invalidation**
   - Invalidate on write operations
   - Ensures immediate consistency
   - Requires careful tracking of cache dependencies

3. **Version-based Invalidation**
   - Include version in cache key
   - Increment version on updates
   - Old versions expire naturally

### Implementation

```python
# Event-driven invalidation example
class EngagementService:
    def __init__(self, cache: CacheManager, db: Database):
        self.cache = cache
        self.db = db

    async def update_engagement(
        self,
        engagement_id: str,
        data: EngagementUpdate
    ) -> Engagement:
        # Update database
        engagement = await self.db.update(engagement_id, data)

        # Invalidate related caches
        await self.cache.delete(f"engagement:{engagement_id}")
        await self.cache.delete_pattern(f"engagement:{engagement_id}:*")
        await self.cache.delete_pattern(f"dashboard:*:engagement_list")

        return engagement
```

### Pub/Sub for Distributed Invalidation

```python
# Subscribe to invalidation events across instances
async def cache_invalidation_listener(redis: Redis):
    pubsub = redis.pubsub()
    await pubsub.subscribe("cache:invalidate")

    async for message in pubsub.listen():
        if message["type"] == "message":
            pattern = message["data"].decode()
            await cache_manager.delete_pattern(pattern)

# Publish invalidation event
async def publish_invalidation(pattern: str):
    await redis.publish("cache:invalidate", pattern)
```

## Monitoring

### Key Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Hit Rate | Cache hits / (hits + misses) | > 80% |
| Miss Rate | Cache misses / total requests | < 20% |
| Eviction Rate | Keys evicted per second | Minimize |
| Memory Usage | Current memory / max memory | < 80% |
| Connection Count | Active client connections | < max_clients |
| Latency P99 | 99th percentile response time | < 1ms |

### Prometheus Metrics

```yaml
# Redis metrics to monitor
- redis_connected_clients
- redis_blocked_clients
- redis_used_memory
- redis_used_memory_peak
- redis_mem_fragmentation_ratio
- redis_keyspace_hits
- redis_keyspace_misses
- redis_evicted_keys
- redis_expired_keys
- redis_commands_processed_total
```

### Alerting Rules

```yaml
# Alert on low cache hit rate
- alert: RedisLowHitRate
  expr: |
    redis_keyspace_hits / (redis_keyspace_hits + redis_keyspace_misses) < 0.7
  for: 10m
  labels:
    severity: warning

# Alert on high memory usage
- alert: RedisHighMemoryUsage
  expr: redis_used_memory / redis_maxmemory > 0.9
  for: 5m
  labels:
    severity: critical

# Alert on high eviction rate
- alert: RedisHighEvictionRate
  expr: rate(redis_evicted_keys[5m]) > 100
  for: 5m
  labels:
    severity: warning
```
