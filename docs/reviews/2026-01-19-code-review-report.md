# Open Forge Code Review Report

**Date:** 2026-01-19
**Reviewer:** Claude Code
**Scope:** Full codebase review (Gates 1-9)

---

## Executive Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 4 | 7 | 5 | 4 |
| Bugs | 0 | 0 | 0 | 0 |
| Performance | 0 | 0 | 0 | 0 |
| Code Quality | 0 | 0 | 0 | 0 |
| Testing | 0 | 0 | 0 | 0 |
| Documentation | 0 | 0 | 0 | 0 |
| Dependencies | 1 | 1 | 2 | 1 |

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

**Status:** Reviewed

**Findings:**

| # | Severity | Issue | Location | Recommendation |
|---|----------|-------|----------|----------------|
| 1 | High | Hardcoded development passwords in Python code | `definitions.py:164,172` | Move credentials to environment variables; use External Secrets Operator references |
| 2 | High | Development passwords in .env.example | `.env.example:16,32,68` | Use placeholder values only (e.g., `<your-password-here>`); never commit real passwords |
| 3 | Medium | Placeholder secrets with CHANGE_ME values in Kubernetes manifests | `grafana-deployment.yaml:133`, `alertmanager-deployment.yaml:79`, `redis-sentinel.yaml:608` | Reference ExternalSecret resources instead of hardcoded Secret manifests |
| 4 | Low | Example tokens in docstrings | `graphql.py:108`, `rest.py:75` | Low risk but consider using `<token>` placeholder format for consistency |

**Positive Observations:**
- External Secrets Operator is properly configured with ClusterSecretStore for AWS Secrets Manager (`external-secrets.yaml:15-40`)
- SecretStore for HashiCorp Vault configured for both production and staging (`external-secrets.yaml:42-88`)
- ClusterSecretStore for Google Secret Manager available (`external-secrets.yaml:90-112`)
- ExternalSecret resources defined for database, Redis, and MinIO credentials (`external-secrets.yaml:115-220`)
- Templates properly use mustache syntax `{{ .password }}` for secret injection
- `.env.example` files follow good practice of using placeholder format for sensitive API keys (`your_api_key_here`)
- No real production secrets found committed to repository
- `.gitignore` properly excludes `.env` files (only `.env.example` committed)

**Details:**

**High: Hardcoded Development Passwords (definitions.py:164,172)**
```python
"database": DatabaseResource(
    password="foundry_dev",  # Line 164
),
"iceberg": IcebergResource(
    s3_secret_key="minio123",  # Line 172
),
```
While marked as development defaults, these hardcoded credentials could be accidentally used in production if environment variables are not properly set. Should use `EnvVar.get_required()` pattern to fail fast if credentials are missing.

**High: Development Passwords in .env.example (.env.example:16,32,68)**
```
DB_PASSWORD=foundry_dev
S3_SECRET_KEY=minio123
DAGSTER_POSTGRES_PASSWORD=foundry_dev
```
The `.env.example` contains actual development passwords rather than placeholders. While these are development-only values, it establishes a bad pattern. Should use `<your-password-here>` format.

**Medium: CHANGE_ME Placeholder Secrets in K8s Manifests**

Multiple Kubernetes Secret manifests contain hardcoded placeholder values:
```yaml
# grafana-deployment.yaml:133
admin-password: "CHANGE_ME_IN_PRODUCTION"

# alertmanager-deployment.yaml:79
smtp-password: "CHANGE_ME"

# redis-sentinel.yaml:608
password: "CHANGE_ME_IN_PRODUCTION"
```
While these are clearly marked as placeholders, the manifests should reference ExternalSecret resources rather than defining Secrets with hardcoded values. This ensures secrets are never committed, even as placeholders.

**Git History Check:**
No historical commits containing production secrets were found. All secret-like strings in history are development defaults or template values.

### Dependency Vulnerabilities

**Status:** Reviewed

**Findings:**

| # | Severity | Issue | Package | Recommendation |
|---|----------|-------|---------|----------------|
| 1 | Critical | 13 known vulnerabilities including SSRF, Auth Bypass, DoS, Cache Poisoning | `next@14.x` | Upgrade to `next@15.x` or later (breaking change) |
| 2 | High | Command injection via --cmd flag | `glob@10.2.0-10.4.5` | Upgrade to `glob@11.x` via `npm audit fix --force` |
| 3 | Moderate | Development server request vulnerability | `esbuild<=0.24.2` | Upgrade via `npm audit fix --force` (requires vitest update) |
| 4 | Moderate | esbuild vulnerability propagates through vite | `vite@0.11.0-6.1.6` | Upgrade vitest to latest for patched vite-node |
| 5 | Low | Python dependency version floors may include vulnerable versions | `langchain>=0.2.0`, `fastapi>=0.110.0` | Pin to specific versions and run `pip-audit` in CI |

**npm Audit Summary (packages/ui):**
```
13 critical (next)
1 high (glob)
4 moderate (esbuild, vite chain)
```

**Details:**

**Critical: Next.js Vulnerabilities (next@14.x)**

The UI package uses Next.js 14.x which has 13 documented security vulnerabilities:
- GHSA-fr5h-rqp8-mj6g: Server-Side Request Forgery in Server Actions
- GHSA-7gfc-8cq8-jh5f: Authorization bypass vulnerability
- GHSA-f82v-jwr5-mffw: Authorization Bypass in Middleware
- GHSA-gp8f-8m3g-qvj9: Cache Poisoning
- GHSA-g77x-44xx-532m: DoS in image optimization
- GHSA-7m27-7ghc-44w9: DoS with Server Actions
- GHSA-3h52-269p-cp9r: Information exposure in dev server
- GHSA-g5qg-72qw-gw5v: Cache Key Confusion for Image Optimization
- GHSA-4342-x723-ch2f: SSRF via Middleware Redirect
- GHSA-xv57-4mr9-wg8v: Content Injection in Image Optimization
- GHSA-qpjv-v59x-3qc4: Race Condition Cache Poisoning
- GHSA-mwv6-3258-q52c: DoS with Server Components
- GHSA-5j59-xgg2-r9c4: DoS with Server Components (follow-up)

**Recommendation:** Upgrade to Next.js 15.x. This is a breaking change requiring migration effort.

**High: glob Command Injection (glob@10.2.0-10.4.5)**

GHSA-5j98-mcp5-4vw2: The glob CLI allows command injection through the `-c/--cmd` flag with `shell:true`. This affects `@next/eslint-plugin-next` and `eslint-config-next`.

**Recommendation:** Run `npm audit fix --force` to upgrade eslint-config-next to 16.x.

**Moderate: esbuild Development Server Vulnerability**

GHSA-67mh-4wv8-2f99: esbuild <= 0.24.2 allows any website to send requests to the development server. This propagates through vite-node and vitest.

**Recommendation:** Upgrade vitest to 4.x for patched dependencies.

**Python Dependencies:**

Current version floors in pyproject.toml files:
- `langchain>=0.2.0` - LangChain has had security patches; pin to specific version
- `fastapi>=0.110.0` - Should pin to specific version for reproducibility
- `pydantic>=2.0.0` - Broad version range
- `sqlalchemy>=2.0.0` - Broad version range

**Recommendations:**
1. Pin Python dependencies to specific versions or narrower ranges
2. Add `pip-audit` to CI pipeline for vulnerability scanning
3. Run `safety check` or `pip-audit` before releases
4. Consider using `dependabot` or `renovate` for automated updates

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
