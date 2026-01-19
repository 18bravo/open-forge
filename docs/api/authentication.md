# Authentication Guide

This guide covers authentication methods for the Open Forge API.

## Table of Contents

- [Overview](#overview)
- [API Key Authentication](#api-key-authentication)
- [JWT Authentication](#jwt-authentication)
- [Service-to-Service Authentication](#service-to-service-authentication)
- [Security Best Practices](#security-best-practices)

---

## Overview

Open Forge supports two authentication methods:

| Method | Use Case | Header |
|--------|----------|--------|
| **API Key** | Service-to-service communication, CLI tools | `X-API-Key` |
| **JWT Token** | User sessions, web applications | `Authorization: Bearer <token>` |

All API endpoints (except health checks) require authentication.

---

## API Key Authentication

API keys are ideal for programmatic access, automation scripts, and service integrations.

### Obtaining an API Key

1. Log into the Open Forge admin dashboard
2. Navigate to **Settings > API Keys**
3. Click **Create New Key**
4. Provide a description and select permissions
5. Copy the generated key (it will only be shown once)

### Using API Keys

Include the API key in the `X-API-Key` header:

```bash
curl -H "X-API-Key: your_api_key_here" \
  https://api.openforge.io/v1/engagements
```

**Python Example:**

```python
import httpx

client = httpx.Client(
    base_url="https://api.openforge.io/v1",
    headers={"X-API-Key": "your_api_key_here"}
)

response = client.get("/engagements")
print(response.json())
```

**TypeScript Example:**

```typescript
const response = await fetch('https://api.openforge.io/v1/engagements', {
  headers: {
    'X-API-Key': 'your_api_key_here'
  }
});

const data = await response.json();
```

### API Key Permissions

API keys can have different permission scopes:

| Scope | Description |
|-------|-------------|
| `read:engagements` | Read engagement data |
| `write:engagements` | Create and modify engagements |
| `read:data-sources` | Read data source configurations |
| `write:data-sources` | Manage data source connections |
| `execute:agents` | Execute agent tasks |
| `approve:requests` | Approve pending requests |
| `admin` | Full administrative access |

### Key Rotation

For security, rotate API keys regularly:

1. Create a new API key
2. Update your applications to use the new key
3. Verify functionality with the new key
4. Revoke the old key

---

## JWT Authentication

JWT (JSON Web Token) authentication is used for user sessions in web applications.

### Obtaining a JWT Token

#### Login Endpoint

```bash
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "your_password"
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### Using JWT Tokens

Include the token in the `Authorization` header:

```bash
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..." \
  https://api.openforge.io/v1/engagements
```

**Python Example:**

```python
import httpx

# Login and get token
auth_response = httpx.post(
    "https://api.openforge.io/v1/auth/login",
    json={"email": "user@example.com", "password": "password"}
)
tokens = auth_response.json()

# Use token for authenticated requests
client = httpx.Client(
    base_url="https://api.openforge.io/v1",
    headers={"Authorization": f"Bearer {tokens['access_token']}"}
)

response = client.get("/engagements")
```

### Token Refresh

Access tokens expire after 1 hour. Use the refresh token to obtain a new access token:

```bash
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

**Response:**

```json
{
  "access_token": "eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 3600
}
```

### JWT Token Structure

Open Forge JWT tokens contain the following claims:

```json
{
  "sub": "user_id_123",
  "email": "user@example.com",
  "name": "John Doe",
  "roles": ["user", "engineer"],
  "permissions": ["read:engagements", "write:engagements"],
  "iat": 1704067200,
  "exp": 1704070800,
  "iss": "openforge"
}
```

| Claim | Description |
|-------|-------------|
| `sub` | User ID (subject) |
| `email` | User email address |
| `name` | User display name |
| `roles` | Assigned roles |
| `permissions` | Granted permissions |
| `iat` | Issued at timestamp |
| `exp` | Expiration timestamp |
| `iss` | Token issuer |

---

## Service-to-Service Authentication

For internal service communication, use service accounts with API keys.

### Creating a Service Account

```bash
# Using the CLI
openforge admin create-service-account \
  --name "pipeline-service" \
  --description "Dagster pipeline service account" \
  --scopes "execute:agents,read:data-sources"
```

### mTLS (Mutual TLS)

For enhanced security in production, enable mTLS:

```yaml
# docker-compose.yml
services:
  api:
    environment:
      MTLS_ENABLED: "true"
      MTLS_CA_CERT: /certs/ca.crt
      MTLS_SERVER_CERT: /certs/server.crt
      MTLS_SERVER_KEY: /certs/server.key
```

---

## Security Best Practices

### 1. Never Expose Credentials

- Never commit API keys or tokens to version control
- Use environment variables or secret managers
- Use `.env` files for local development (add to `.gitignore`)

```bash
# .env (never commit this file)
OPENFORGE_API_KEY=your_api_key_here
```

```python
import os

api_key = os.environ.get("OPENFORGE_API_KEY")
```

### 2. Use HTTPS

Always use HTTPS in production. HTTP is only acceptable for local development.

### 3. Implement Token Refresh Logic

Handle token expiration gracefully:

```python
import httpx
from datetime import datetime, timedelta

class OpenForgeClient:
    def __init__(self, email: str, password: str):
        self.email = email
        self.password = password
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self._client = httpx.Client(base_url="https://api.openforge.io/v1")

    def _ensure_authenticated(self):
        if not self.access_token or datetime.now() >= self.token_expires_at:
            if self.refresh_token:
                self._refresh_token()
            else:
                self._login()

    def _login(self):
        response = self._client.post("/auth/login", json={
            "email": self.email,
            "password": self.password
        })
        self._handle_auth_response(response.json())

    def _refresh_token(self):
        response = self._client.post("/auth/refresh", json={
            "refresh_token": self.refresh_token
        })
        self._handle_auth_response(response.json())

    def _handle_auth_response(self, data: dict):
        self.access_token = data["access_token"]
        self.refresh_token = data.get("refresh_token", self.refresh_token)
        self.token_expires_at = datetime.now() + timedelta(seconds=data["expires_in"] - 60)
        self._client.headers["Authorization"] = f"Bearer {self.access_token}"

    def get(self, path: str):
        self._ensure_authenticated()
        return self._client.get(path)
```

### 4. Use Least Privilege

Request only the permissions your application needs:

```python
# Bad: Requesting admin access for a read-only application
api_key = create_api_key(scopes=["admin"])

# Good: Requesting only necessary permissions
api_key = create_api_key(scopes=["read:engagements", "read:data-sources"])
```

### 5. Monitor and Audit

- Enable audit logging for all authentication events
- Monitor for unusual access patterns
- Set up alerts for failed authentication attempts

### 6. Key Expiration

Set expiration dates for API keys:

```python
# Create a key that expires in 90 days
api_key = create_api_key(
    description="CI/CD pipeline",
    scopes=["execute:agents"],
    expires_in_days=90
)
```

---

## Error Responses

### 401 Unauthorized

Missing or invalid credentials:

```json
{
  "error": "unauthorized",
  "message": "Invalid or missing authentication credentials"
}
```

### 403 Forbidden

Valid credentials but insufficient permissions:

```json
{
  "error": "forbidden",
  "message": "You do not have permission to perform this action",
  "details": {
    "required_scope": "write:engagements",
    "your_scopes": ["read:engagements"]
  }
}
```

### 401 Token Expired

JWT token has expired:

```json
{
  "error": "token_expired",
  "message": "Access token has expired",
  "details": {
    "expired_at": "2024-01-15T12:00:00Z"
  }
}
```

---

## Related Documentation

- [Rate Limiting](./rate-limiting.md)
- [Error Codes](./errors.md)
- [API Reference](./openapi.yaml)
