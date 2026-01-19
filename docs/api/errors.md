# Error Codes and Handling

This guide documents all error codes returned by the Open Forge API and provides guidance on handling them.

## Table of Contents

- [Error Response Format](#error-response-format)
- [HTTP Status Codes](#http-status-codes)
- [Error Code Reference](#error-code-reference)
- [Error Handling Best Practices](#error-handling-best-practices)
- [Troubleshooting Common Errors](#troubleshooting-common-errors)

---

## Error Response Format

All API errors follow a consistent JSON format:

```json
{
  "error": "error_code",
  "message": "Human-readable error description",
  "details": {
    "field": "additional context",
    "suggestion": "how to resolve"
  },
  "request_id": "req_abc123xyz",
  "timestamp": "2024-01-15T12:00:00Z"
}
```

### Fields

| Field | Type | Description |
|-------|------|-------------|
| `error` | string | Machine-readable error code |
| `message` | string | Human-readable error description |
| `details` | object | Additional context (optional) |
| `request_id` | string | Unique request identifier for support |
| `timestamp` | string | ISO 8601 timestamp |

---

## HTTP Status Codes

### Success Codes (2xx)

| Code | Description |
|------|-------------|
| `200 OK` | Request succeeded |
| `201 Created` | Resource created successfully |
| `202 Accepted` | Request accepted for async processing |
| `204 No Content` | Success with no response body |

### Client Error Codes (4xx)

| Code | Description |
|------|-------------|
| `400 Bad Request` | Invalid request syntax or parameters |
| `401 Unauthorized` | Missing or invalid authentication |
| `403 Forbidden` | Valid auth but insufficient permissions |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | Resource state conflict |
| `422 Unprocessable Entity` | Validation error |
| `429 Too Many Requests` | Rate limit exceeded |

### Server Error Codes (5xx)

| Code | Description |
|------|-------------|
| `500 Internal Server Error` | Unexpected server error |
| `502 Bad Gateway` | Upstream service error |
| `503 Service Unavailable` | Service temporarily unavailable |
| `504 Gateway Timeout` | Upstream service timeout |

---

## Error Code Reference

### Authentication Errors

#### `unauthorized`
**HTTP Status:** 401

Missing or invalid authentication credentials.

```json
{
  "error": "unauthorized",
  "message": "Authentication required. Please provide valid credentials.",
  "details": {
    "suggestion": "Include X-API-Key header or Authorization: Bearer token"
  }
}
```

**Resolution:**
- Verify your API key or JWT token is correct
- Check the token has not expired
- Ensure proper header format

#### `invalid_token`
**HTTP Status:** 401

The provided token is malformed or invalid.

```json
{
  "error": "invalid_token",
  "message": "The provided token is invalid",
  "details": {
    "reason": "Token signature verification failed"
  }
}
```

#### `token_expired`
**HTTP Status:** 401

The JWT token has expired.

```json
{
  "error": "token_expired",
  "message": "Access token has expired",
  "details": {
    "expired_at": "2024-01-15T11:00:00Z",
    "suggestion": "Use refresh token to obtain a new access token"
  }
}
```

#### `forbidden`
**HTTP Status:** 403

Valid authentication but insufficient permissions.

```json
{
  "error": "forbidden",
  "message": "You do not have permission to perform this action",
  "details": {
    "required_permission": "write:engagements",
    "your_permissions": ["read:engagements"]
  }
}
```

---

### Resource Errors

#### `not_found`
**HTTP Status:** 404

The requested resource does not exist.

```json
{
  "error": "not_found",
  "message": "Engagement with ID 'eng_123' not found",
  "details": {
    "resource_type": "engagement",
    "resource_id": "eng_123"
  }
}
```

#### `already_exists`
**HTTP Status:** 409

A resource with the same identifier already exists.

```json
{
  "error": "already_exists",
  "message": "A data source with this name already exists",
  "details": {
    "resource_type": "data_source",
    "conflicting_field": "name",
    "conflicting_value": "production-database"
  }
}
```

#### `conflict`
**HTTP Status:** 409

The request conflicts with the current state of the resource.

```json
{
  "error": "conflict",
  "message": "Cannot delete engagement while tasks are running",
  "details": {
    "engagement_id": "eng_123",
    "running_tasks": ["task_456", "task_789"],
    "suggestion": "Cancel running tasks before deleting the engagement"
  }
}
```

---

### Validation Errors

#### `validation_error`
**HTTP Status:** 422

Request body failed validation.

```json
{
  "error": "validation_error",
  "message": "Request validation failed",
  "details": {
    "errors": [
      {
        "field": "name",
        "message": "Field is required",
        "code": "required"
      },
      {
        "field": "priority",
        "message": "Must be one of: low, medium, high, critical",
        "code": "invalid_enum",
        "received": "urgent"
      }
    ]
  }
}
```

#### `invalid_parameter`
**HTTP Status:** 400

A query parameter or path parameter is invalid.

```json
{
  "error": "invalid_parameter",
  "message": "Invalid value for parameter 'page'",
  "details": {
    "parameter": "page",
    "received": "-1",
    "constraint": "Must be a positive integer"
  }
}
```

---

### Rate Limiting Errors

#### `rate_limit_exceeded`
**HTTP Status:** 429

Too many requests in the time window.

```json
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

**Resolution:**
- Wait for the `Retry-After` duration
- Implement exponential backoff
- Consider upgrading your subscription tier

---

### Agent Errors

#### `agent_execution_failed`
**HTTP Status:** 500

The agent task failed during execution.

```json
{
  "error": "agent_execution_failed",
  "message": "Agent task failed: LLM response parsing error",
  "details": {
    "task_id": "task_123",
    "agent": "ontology_designer",
    "step": "generate_schema",
    "error_type": "LLMResponseError",
    "suggestion": "Retry the task or contact support if the issue persists"
  }
}
```

#### `agent_timeout`
**HTTP Status:** 504

The agent task exceeded its timeout limit.

```json
{
  "error": "agent_timeout",
  "message": "Agent task timed out after 300 seconds",
  "details": {
    "task_id": "task_123",
    "timeout_seconds": 300,
    "suggestion": "Increase timeout or break into smaller tasks"
  }
}
```

#### `tool_approval_required`
**HTTP Status:** 202

A tool call requires human approval before proceeding.

```json
{
  "error": "tool_approval_required",
  "message": "Tool execution requires approval",
  "details": {
    "task_id": "task_123",
    "tool_call_id": "call_456",
    "tool_name": "execute_sql",
    "approval_url": "/api/v1/agents/tasks/task_123/approve-tool"
  }
}
```

#### `agent_not_available`
**HTTP Status:** 503

The requested agent is not available.

```json
{
  "error": "agent_not_available",
  "message": "The ontology_designer agent is currently unavailable",
  "details": {
    "agent": "ontology_designer",
    "reason": "Service scaling in progress",
    "retry_after": 30
  }
}
```

---

### Data Source Errors

#### `connection_failed`
**HTTP Status:** 502

Failed to connect to the data source.

```json
{
  "error": "connection_failed",
  "message": "Failed to connect to data source",
  "details": {
    "source_id": "ds_123",
    "source_type": "postgresql",
    "error": "Connection refused",
    "host": "db.example.com",
    "port": 5432
  }
}
```

#### `authentication_failed`
**HTTP Status:** 401

Data source authentication failed.

```json
{
  "error": "authentication_failed",
  "message": "Data source authentication failed",
  "details": {
    "source_id": "ds_123",
    "source_type": "postgresql",
    "error": "Invalid username or password"
  }
}
```

#### `schema_discovery_failed`
**HTTP Status:** 500

Failed to discover schema from data source.

```json
{
  "error": "schema_discovery_failed",
  "message": "Failed to discover schema from data source",
  "details": {
    "source_id": "ds_123",
    "error": "Permission denied on information_schema"
  }
}
```

---

### Pipeline Errors

#### `pipeline_failed`
**HTTP Status:** 500

A data pipeline execution failed.

```json
{
  "error": "pipeline_failed",
  "message": "Pipeline execution failed",
  "details": {
    "pipeline_id": "pipe_123",
    "job_id": "job_456",
    "failed_step": "transformation",
    "error": "Division by zero in column 'ratio'"
  }
}
```

#### `resource_unavailable`
**HTTP Status:** 503

A required pipeline resource is unavailable.

```json
{
  "error": "resource_unavailable",
  "message": "Pipeline resource unavailable",
  "details": {
    "resource": "iceberg_catalog",
    "error": "Connection to Iceberg REST catalog failed"
  }
}
```

---

### Server Errors

#### `internal_error`
**HTTP Status:** 500

An unexpected internal error occurred.

```json
{
  "error": "internal_error",
  "message": "An unexpected error occurred. Please try again later.",
  "details": {
    "request_id": "req_abc123xyz",
    "suggestion": "Contact support with this request_id if the issue persists"
  }
}
```

#### `service_unavailable`
**HTTP Status:** 503

The service is temporarily unavailable.

```json
{
  "error": "service_unavailable",
  "message": "Service temporarily unavailable",
  "details": {
    "reason": "Scheduled maintenance",
    "retry_after": 300,
    "status_page": "https://status.openforge.io"
  }
}
```

---

## Error Handling Best Practices

### 1. Always Check Status Codes

```python
import httpx

response = client.post("/engagements", json=data)

if response.status_code == 201:
    engagement = response.json()
elif response.status_code == 422:
    errors = response.json()["details"]["errors"]
    for error in errors:
        print(f"Validation error on {error['field']}: {error['message']}")
elif response.status_code == 429:
    retry_after = int(response.headers.get("Retry-After", 60))
    print(f"Rate limited. Retry after {retry_after} seconds")
else:
    error = response.json()
    print(f"Error: {error['message']}")
```

### 2. Implement Retry Logic

```python
import time
from typing import Callable

def with_retry(
    func: Callable,
    max_retries: int = 3,
    retry_codes: set = {429, 500, 502, 503, 504}
):
    """Retry a function on specific error codes."""
    last_exception = None

    for attempt in range(max_retries):
        try:
            response = func()

            if response.status_code not in retry_codes:
                return response

            if response.status_code == 429:
                wait = int(response.headers.get("Retry-After", 2 ** attempt))
            else:
                wait = 2 ** attempt  # Exponential backoff

            print(f"Attempt {attempt + 1} failed, retrying in {wait}s...")
            time.sleep(wait)

        except Exception as e:
            last_exception = e
            time.sleep(2 ** attempt)

    if last_exception:
        raise last_exception
    return response
```

### 3. Handle Validation Errors Gracefully

```python
def handle_validation_errors(response: httpx.Response) -> list[str]:
    """Extract validation error messages from response."""
    if response.status_code != 422:
        return []

    error_data = response.json()
    errors = error_data.get("details", {}).get("errors", [])

    messages = []
    for error in errors:
        field = error.get("field", "unknown")
        message = error.get("message", "Invalid value")
        messages.append(f"{field}: {message}")

    return messages
```

### 4. Log Error Details

```python
import logging

logger = logging.getLogger(__name__)

def log_api_error(response: httpx.Response):
    """Log API error with relevant context."""
    try:
        error = response.json()
        logger.error(
            "API Error",
            extra={
                "status_code": response.status_code,
                "error_code": error.get("error"),
                "message": error.get("message"),
                "request_id": error.get("request_id"),
                "details": error.get("details")
            }
        )
    except Exception:
        logger.error(f"API Error: HTTP {response.status_code}")
```

### 5. Use Request IDs for Support

Always include the `request_id` when contacting support:

```python
def report_error(response: httpx.Response):
    error = response.json()
    request_id = error.get("request_id")

    print(f"""
    An error occurred. Please contact support with the following information:

    Request ID: {request_id}
    Error Code: {error.get('error')}
    Message: {error.get('message')}
    Timestamp: {error.get('timestamp')}
    """)
```

---

## Troubleshooting Common Errors

### "Authentication required" but I included the API key

**Possible causes:**
1. Header name is incorrect (should be `X-API-Key`)
2. API key has been revoked or expired
3. API key has no permissions for this endpoint

**Solution:**
```bash
# Verify header format
curl -v -H "X-API-Key: your_key" https://api.openforge.io/v1/health
```

### "Rate limit exceeded" with low traffic

**Possible causes:**
1. Shared IP address with other users
2. API key used across multiple applications
3. Burst of requests at startup

**Solution:**
- Implement request queuing
- Use separate API keys for different applications
- Add startup delay between requests

### "Connection failed" for data source

**Possible causes:**
1. Network connectivity issues
2. Firewall blocking connection
3. Incorrect host/port configuration
4. Data source is down

**Solution:**
1. Verify network connectivity from Open Forge to data source
2. Check firewall rules allow connection
3. Verify connection details are correct
4. Test connection from another client

### "Agent execution failed" repeatedly

**Possible causes:**
1. Input data format issues
2. Agent prompt needs refinement
3. LLM service issues

**Solution:**
1. Verify input data matches expected schema
2. Check agent logs for specific errors
3. Try with simplified input
4. Contact support if issue persists

---

## Related Documentation

- [Authentication](./authentication.md)
- [Rate Limiting](./rate-limiting.md)
- [API Reference](./openapi.yaml)
