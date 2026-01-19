# Open Forge Code Review Report

**Date:** 2026-01-19
**Reviewer:** Claude Code
**Scope:** Full codebase review (Gates 1-9)

---

## Executive Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 4 | 5 | 4 | 3 |
| Bugs | 0 | 0 | 0 | 0 |
| Performance | 0 | 0 | 0 | 0 |
| Code Quality | 0 | 0 | 0 | 0 |
| Testing | 0 | 0 | 0 | 0 |
| Documentation | 0 | 0 | 0 | 0 |

---

## Critical Findings

1. **Hardcoded Test Token** (`packages/api/src/api/dependencies.py:103`): A hardcoded `test-token` grants full admin privileges to any request using it. This must be removed before production.

2. **No JWT Validation** (`packages/api/src/api/dependencies.py:90-116`): JWT tokens are not validated (no signature, expiration, or issuer checks). The authentication system is non-functional for production use.

3. **Code Injection via eval()** (`packages/pipelines/src/pipelines/assets/transformation.py:260`): User-provided expressions are passed directly to Python's `eval()`, allowing arbitrary code execution on the server.

4. **Code Injection via eval() in Canvas** (`packages/pipelines/src/canvas/compiler.py:607`): Canvas filter expressions use `eval()`, enabling arbitrary code execution through crafted filter expressions.

---

## Security Review

### Authentication & Authorization

**Status:** Reviewed

**Findings:**

| # | Severity | Issue | Location | Recommendation |
|---|----------|-------|----------|----------------|
| 1 | Critical | Hardcoded test token bypasses authentication | `dependencies.py:103` | Remove hardcoded `test-token` check; implement proper JWT validation with signature verification |
| 2 | Critical | No JWT validation implemented | `dependencies.py:90-116` | Implement full JWT validation: signature verification, expiration check, issuer validation |
| 3 | High | Development header bypass allows arbitrary user impersonation | `dependencies.py:82-88` | Add environment check to disable X-User-ID header in production |
| 4 | High | Admin endpoints lack admin role enforcement | `admin.py` (all endpoints) | Add `require_role("admin")` dependency to all admin endpoints |
| 5 | Medium | No resource ownership validation | All routers | Implement ownership checks for resource-specific operations (e.g., only task creator can cancel) |
| 6 | Medium | Missing rate limiting on auth endpoints | `dependencies.py` | Add rate limiting to prevent brute force attacks |
| 7 | Low | Default permissions granted are too broad | `dependencies.py:87` | Review default permissions; consider principle of least privilege |
| 8 | Low | Health endpoints may expose sensitive info | `health.py:52-71` | Consider restricting readiness check details in production |

**Positive Observations:**
- Good RBAC foundation with `require_permission()` and `require_role()` dependency factories (`dependencies.py:143-186`)
- `CurrentUser` dependency consistently applied across most endpoints
- Proper 401/403 HTTP status codes with WWW-Authenticate headers
- Sensitive connection config fields are redacted before returning to clients (`data_sources.py:359-375`)
- UserContext model properly structures user identity data (`schemas/common.py:88-94`)

**Details:**

**Critical: Hardcoded Test Token (dependencies.py:103)**
```python
if token == "test-token":
    return UserContext(
        user_id="test-user",
        username="test_user",
        email="test@example.com",
        roles=["admin"],
        permissions=["read", "write", "admin"]
    )
```
This allows anyone with knowledge of `test-token` to gain full admin access. This must be removed before production deployment.

**Critical: Missing JWT Validation (dependencies.py:90-116)**
The code has a TODO comment stating "Implement proper JWT validation" but currently only checks for the hardcoded test token. Real JWT validation must include:
- Signature verification using a secret/public key
- Token expiration (`exp` claim) validation
- Issuer (`iss`) validation
- Audience (`aud`) validation if applicable

**High: X-User-ID Header Bypass (dependencies.py:82-88)**
```python
if x_user_id:
    return UserContext(
        user_id=x_user_id,
        username=f"user_{x_user_id}",
        roles=["user"],
        permissions=["read", "write"]
    )
```
Any request with an `X-User-ID` header can impersonate any user. This should be disabled or heavily restricted in production.

**High: Admin Endpoints Unprotected (admin.py)**
All admin endpoints (system health, agent clusters, pipelines, settings, users, audit logs) only require `CurrentUser` but do not verify admin role. Example:
```python
@router.get("/settings/users", ...)
async def list_users(user: CurrentUser, ...):  # Missing require_role("admin")
```

**Hardcoded Secrets Note:**
The hardcoded credentials found in `packages/connectors/` and `packages/pipelines/` are in example/docstring code and development configurations that fall back when environment variables are not set. While not ideal, these are clearly marked as development defaults and use environment variable overrides for production.

### Input Validation

**Status:** Reviewed

**Findings:**

| # | Severity | Issue | Location | Recommendation |
|---|----------|-------|----------|----------------|
| 1 | Critical | Unsafe `eval()` executes arbitrary code from user-provided expressions | `transformation.py:260` | Replace `eval()` with a safe expression parser (e.g., Polars native expressions or a sandboxed DSL) |
| 2 | Critical | Unsafe `eval()` in filter expressions allows code injection | `compiler.py:607` | Replace `eval()` with validated expression parsing; use allowlist of safe operations |
| 3 | High | SQL injection via f-string in table queries | `base_sql.py:206,212` | Use parameterized queries; validate table names against allowlist of known tables |
| 4 | High | SQL injection in graph database queries | `graph.py:24,27,41-43` | Use parameterized queries; escape/validate user input before string interpolation |
| 5 | High | Cypher injection via string replacement in queries | `graph.py:39-43` | Use proper Cypher parameter binding instead of string replacement |
| 6 | Medium | File path validation missing for CSV/Parquet connectors | `csv.py:82`, `parquet.py:94` | Add path sanitization; prevent traversal patterns (`../`); restrict to allowed directories |
| 7 | Medium | No max_length on some string fields in schemas | `agent.py:53-54`, `common.py:90-91` | Add max_length constraints to prevent DoS via oversized inputs |
| 8 | Low | Dict[str, Any] fields accept arbitrary nested data | Multiple schema files | Consider schema validation for nested config structures |

**Positive Observations:**
- Pydantic models consistently used for all API input validation (`packages/api/src/api/schemas/`)
- Good use of Field() constraints with min_length, max_length on name/description fields (`engagement.py:40-41`, `data_sources.py:44-45`)
- Numeric fields properly bounded with ge/le constraints (`common.py:13-14`, `agent.py:63-73`)
- Enum types used for status and type fields preventing invalid values (`engagement.py:10-28`, `agent.py:10-26`)
- Pagination parameters have proper bounds (page_size max 100, `common.py:14`)
- FastAPI Query parameters also use bounds validation (`data_sources.py:179-180`)

**Details:**

**Critical: eval() Code Injection (transformation.py:260)**
```python
# In derived_columns processing
df = df.with_columns(eval(expression).alias(col_name))
```
User-provided expressions from `config.derived_columns` are passed directly to Python's `eval()`, allowing arbitrary code execution. An attacker could inject `__import__('os').system('rm -rf /')` as an expression.

**Critical: eval() in Filter Transform (compiler.py:607)**
```python
def _apply_filter_transform(self, df, config, context):
    expression = config.get("expression")
    return df.filter(eval(expression))
```
Canvas filter expressions are evaluated with `eval()`, creating the same arbitrary code execution risk.

**High: SQL Injection in base_sql.py**
```python
# Line 206 - Table name directly interpolated
count_result = await conn.execute(
    text(f"SELECT COUNT(*) FROM {source}")
)
# Line 212
result = await conn.execute(
    text(f"SELECT * FROM {source} LIMIT :limit"),
    {"limit": limit}
)
```
While `limit` is parameterized, `source` (table name) is directly interpolated. An attacker could pass `users; DROP TABLE users; --` as the source.

**High: SQL Injection in graph.py**
```python
# Line 24
result = await session.execute(text(
    f"SELECT * FROM ag_catalog.ag_graph WHERE name = '{self.graph_name}'"
))
# Lines 39-43 - String replacement for Cypher parameters
if params:
    for key, value in params.items():
        if isinstance(value, str):
            cypher_query = cypher_query.replace(f"${key}", f"'{value}'")
```
Graph name and Cypher parameters use string interpolation instead of parameterized queries. The string replacement for Cypher parameters doesn't properly escape values.

**Medium: Path Traversal Risk (csv.py, parquet.py)**
File connectors accept `file_path` from configuration without path sanitization:
```python
self._path = Path(self.config.file_path)  # No traversal validation
```
While these are typically server-side configs, if user input ever reaches these paths, attackers could access arbitrary files using `../` patterns.

**Medium: Unbounded String Fields**
Several schema fields lack max_length constraints:
- `agent.py:53-54`: `task_type`, `description` have no max_length
- `common.py:90-91`: `user_id`, `username` have no max_length
- Various `Optional[str]` fields across schemas

While Pydantic provides type safety, unbounded strings could be used for DoS attacks with extremely large payloads.

### Secrets Management
_Pending review._

### Dependency Vulnerabilities
_Pending review._

---

## Code Quality Review

### Package: core
_Pending review._

### Package: agent-framework
_Pending review._

### Package: agents
_Pending review._

### Package: api
_Pending review._

### Package: ui
_Pending review._

---

## Performance Review

### Database Queries
_Pending review._

### Memory Management
_Pending review._

### Async Patterns
_Pending review._

---

## Testing Review

### Coverage Gaps
_Pending review._

### Test Quality
_Pending review._

---

## Documentation Review

### API Documentation
_Pending review._

### Code Comments
_Pending review._

---

## Recommendations

### Immediate Actions (Critical/High)
_Pending review._

### Short-term Improvements (Medium)
_Pending review._

### Future Enhancements (Low)
_Pending review._
