# Rate Limiting

This guide explains the rate limiting policies for the Open Forge API.

## Table of Contents

- [Overview](#overview)
- [Rate Limit Tiers](#rate-limit-tiers)
- [Rate Limit Headers](#rate-limit-headers)
- [Handling Rate Limits](#handling-rate-limits)
- [Best Practices](#best-practices)

---

## Overview

Open Forge implements rate limiting to ensure fair usage and protect the API from abuse. Rate limits are applied per API key or user account.

### How Rate Limiting Works

```
                    Request
                        |
                        v
            +---------------------+
            |  Check Rate Limit   |
            +---------------------+
                   |       |
           Under Limit    Over Limit
                   |           |
                   v           v
            +----------+  +----------------+
            |  Allow   |  | 429 Too Many   |
            | Request  |  |   Requests     |
            +----------+  +----------------+
```

Rate limits use a sliding window algorithm:
- Requests are counted within a rolling time window
- When the limit is reached, further requests are rejected
- The counter gradually decreases as older requests fall outside the window

---

## Rate Limit Tiers

### Default Limits

| Endpoint Category | Requests/Minute | Requests/Hour |
|-------------------|-----------------|---------------|
| Health checks | Unlimited | Unlimited |
| Read operations | 120 | 3,600 |
| Write operations | 30 | 600 |
| Agent execution | 10 | 100 |
| File uploads | 5 | 50 |

### Subscription Tiers

| Tier | Read/Min | Write/Min | Agents/Min | Monthly Cost |
|------|----------|-----------|------------|--------------|
| **Free** | 60 | 10 | 5 | $0 |
| **Pro** | 300 | 60 | 30 | $99 |
| **Enterprise** | 1,000 | 200 | 100 | Custom |

### Endpoint-Specific Limits

Some endpoints have additional specific limits:

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /auth/login` | 5 | 1 minute |
| `POST /agents/tasks` | 10 | 1 minute |
| `GET /agents/tasks/{id}/stream` | 3 concurrent | - |
| `POST /data-sources/{id}/test` | 10 | 5 minutes |
| `POST /data-sources/{id}/schema/refresh` | 5 | 5 minutes |

---

## Rate Limit Headers

Every API response includes rate limit information in the headers:

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 118
X-RateLimit-Reset: 1704067260
X-RateLimit-Policy: 120;w=60
```

### Header Descriptions

| Header | Description |
|--------|-------------|
| `X-RateLimit-Limit` | Maximum requests allowed in the current window |
| `X-RateLimit-Remaining` | Remaining requests in the current window |
| `X-RateLimit-Reset` | Unix timestamp when the rate limit resets |
| `X-RateLimit-Policy` | Rate limit policy (limit;window in seconds) |

### Rate Limit Exceeded Response

When you exceed the rate limit, you receive a `429 Too Many Requests` response:

```http
HTTP/1.1 429 Too Many Requests
Content-Type: application/json
X-RateLimit-Limit: 120
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1704067260
Retry-After: 45

{
  "error": "rate_limit_exceeded",
  "message": "Rate limit exceeded. Please retry after 45 seconds.",
  "details": {
    "limit": 120,
    "window_seconds": 60,
    "retry_after": 45
  }
}
```

---

## Handling Rate Limits

### Basic Retry Logic

Implement exponential backoff when rate limited:

```python
import time
import httpx

def make_request_with_retry(client: httpx.Client, url: str, max_retries: int = 3):
    for attempt in range(max_retries):
        response = client.get(url)

        if response.status_code == 429:
            # Get retry delay from header or calculate exponentially
            retry_after = int(response.headers.get("Retry-After", 2 ** attempt))
            print(f"Rate limited. Retrying after {retry_after} seconds...")
            time.sleep(retry_after)
            continue

        return response

    raise Exception("Max retries exceeded")
```

### Async Python with Rate Limit Awareness

```python
import asyncio
import httpx
from typing import Optional

class RateLimitedClient:
    def __init__(self, base_url: str, api_key: str):
        self.client = httpx.AsyncClient(
            base_url=base_url,
            headers={"X-API-Key": api_key}
        )
        self.remaining = None
        self.reset_time = None

    async def request(self, method: str, url: str, **kwargs):
        # Wait if we know we're rate limited
        if self.remaining == 0 and self.reset_time:
            wait_time = max(0, self.reset_time - time.time())
            if wait_time > 0:
                await asyncio.sleep(wait_time)

        response = await self.client.request(method, url, **kwargs)

        # Update rate limit tracking
        self.remaining = int(response.headers.get("X-RateLimit-Remaining", 999))
        self.reset_time = int(response.headers.get("X-RateLimit-Reset", 0))

        if response.status_code == 429:
            retry_after = int(response.headers.get("Retry-After", 60))
            await asyncio.sleep(retry_after)
            return await self.request(method, url, **kwargs)

        return response

    async def get(self, url: str, **kwargs):
        return await self.request("GET", url, **kwargs)

    async def post(self, url: str, **kwargs):
        return await self.request("POST", url, **kwargs)
```

### TypeScript/JavaScript Example

```typescript
class RateLimitedClient {
  private remaining: number | null = null;
  private resetTime: number | null = null;

  constructor(
    private baseUrl: string,
    private apiKey: string
  ) {}

  async request(method: string, path: string, options: RequestInit = {}): Promise<Response> {
    // Wait if we know we're rate limited
    if (this.remaining === 0 && this.resetTime) {
      const waitTime = Math.max(0, this.resetTime - Date.now() / 1000);
      if (waitTime > 0) {
        await new Promise(resolve => setTimeout(resolve, waitTime * 1000));
      }
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      method,
      headers: {
        'X-API-Key': this.apiKey,
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    // Update rate limit tracking
    this.remaining = parseInt(response.headers.get('X-RateLimit-Remaining') || '999');
    this.resetTime = parseInt(response.headers.get('X-RateLimit-Reset') || '0');

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
      await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
      return this.request(method, path, options);
    }

    return response;
  }

  get(path: string) {
    return this.request('GET', path);
  }

  post(path: string, body: object) {
    return this.request('POST', path, { body: JSON.stringify(body) });
  }
}
```

---

## Best Practices

### 1. Monitor Rate Limit Headers

Always check the rate limit headers and adjust your request rate accordingly:

```python
def check_rate_limit(response: httpx.Response) -> dict:
    return {
        "limit": int(response.headers.get("X-RateLimit-Limit", 0)),
        "remaining": int(response.headers.get("X-RateLimit-Remaining", 0)),
        "reset": int(response.headers.get("X-RateLimit-Reset", 0)),
        "usage_percent": (1 - int(response.headers.get("X-RateLimit-Remaining", 0)) /
                         max(1, int(response.headers.get("X-RateLimit-Limit", 1)))) * 100
    }
```

### 2. Implement Request Queuing

For high-throughput applications, queue requests to stay within limits:

```python
import asyncio
from collections import deque

class RequestQueue:
    def __init__(self, requests_per_second: float):
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0
        self.lock = asyncio.Lock()

    async def wait(self):
        async with self.lock:
            now = asyncio.get_event_loop().time()
            time_since_last = now - self.last_request_time

            if time_since_last < self.min_interval:
                await asyncio.sleep(self.min_interval - time_since_last)

            self.last_request_time = asyncio.get_event_loop().time()

# Usage
queue = RequestQueue(requests_per_second=2)  # 120 requests/minute

async def make_throttled_request(client, url):
    await queue.wait()
    return await client.get(url)
```

### 3. Batch Operations

When possible, use batch endpoints to reduce the number of API calls:

```python
# Instead of multiple individual requests
for engagement_id in engagement_ids:
    response = client.get(f"/engagements/{engagement_id}")

# Use batch endpoint (when available)
response = client.post("/engagements/batch", json={
    "ids": engagement_ids
})
```

### 4. Use Webhooks

For real-time updates, use webhooks instead of polling:

```python
# Instead of polling
while True:
    response = client.get(f"/agents/tasks/{task_id}")
    if response.json()["status"] == "completed":
        break
    time.sleep(5)  # This wastes rate limit quota

# Configure webhook
client.post("/webhooks", json={
    "url": "https://myapp.example.com/webhook",
    "events": ["agent.task.completed"]
})
```

### 5. Cache Responses

Cache read responses to reduce API calls:

```python
from functools import lru_cache
import time

class CachedClient:
    def __init__(self, client: httpx.Client, cache_ttl: int = 60):
        self.client = client
        self.cache_ttl = cache_ttl
        self._cache = {}

    def get_cached(self, url: str) -> dict:
        cache_key = url
        cached = self._cache.get(cache_key)

        if cached and time.time() - cached["time"] < self.cache_ttl:
            return cached["data"]

        response = self.client.get(url)
        data = response.json()

        self._cache[cache_key] = {
            "data": data,
            "time": time.time()
        }

        return data
```

### 6. Distribute Requests

If you have multiple API keys or service accounts, distribute requests:

```python
import itertools

class LoadBalancedClient:
    def __init__(self, api_keys: list[str]):
        self.clients = itertools.cycle([
            httpx.Client(headers={"X-API-Key": key})
            for key in api_keys
        ])

    def get(self, url: str):
        client = next(self.clients)
        return client.get(url)
```

---

## Rate Limit Exemptions

### Health Check Endpoints

The following endpoints are not rate limited:

- `GET /health`
- `GET /health/ready`
- `GET /health/live`

### Internal Services

Services running within the Open Forge cluster with proper mTLS authentication have elevated rate limits.

### Enterprise Accounts

Enterprise accounts can request custom rate limits. Contact support for details.

---

## Monitoring Rate Limits

### Prometheus Metrics

Open Forge exposes rate limit metrics:

```prometheus
# Rate limit hits
openforge_api_rate_limit_hits_total{endpoint="/engagements", method="GET"} 42

# Requests by rate limit status
openforge_api_requests_total{status="allowed"} 10000
openforge_api_requests_total{status="rate_limited"} 150
```

### Grafana Dashboard

Import the Open Forge API dashboard (ID: `openforge-api`) for rate limit visualization.

---

## Related Documentation

- [Authentication](./authentication.md)
- [Error Codes](./errors.md)
- [API Reference](./openapi.yaml)
