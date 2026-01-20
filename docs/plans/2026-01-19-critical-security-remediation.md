# Critical Security Remediation Plan

> **For Claude:** Execute these tasks sequentially. Each task must be completed before moving to the next.

**Goal:** Fix 5 critical security vulnerabilities blocking production deployment

**Priority:** CRITICAL - Must be completed before any production deployment

---

## Task 1: Implement JWT Authentication (Remove hardcoded test-token)

**Files:**
- Modify: `packages/api/src/api/dependencies.py:90-116`
- Create: `packages/api/src/api/auth.py`

**Current Issue:**
```python
# Line 103 - Hardcoded test-token grants admin access to anyone
if token == "test-token":
    return UserContext(
        user_id="test-user",
        username="test_user",
        email="test@example.com",
        roles=["admin"],
        permissions=["read", "write", "admin"]
    )
```

**Fix:** Implement proper JWT validation using PyJWT library with configurable secret key.

---

## Task 2: Replace eval() in transformation.py with Safe Expression Parser

**Files:**
- Modify: `packages/pipelines/src/pipelines/assets/transformation.py:254-263`

**Current Issue:**
```python
# Line 260 - eval() allows arbitrary code execution
df = df.with_columns(eval(expression).alias(col_name))
```

**Fix:** Create a safe Polars expression parser that only allows whitelisted operations.

---

## Task 3: Replace eval() in compiler.py with Safe Expression Parser

**Files:**
- Modify: `packages/pipelines/src/canvas/compiler.py:599-610`

**Current Issue:**
```python
# Line 607 - eval() allows arbitrary code execution
return df.filter(eval(expression))
```

**Fix:** Use the same safe expression parser created in Task 2.

---

## Task 4: Fix SQL Injection in Database Connectors

**Files:**
- Modify: `packages/connectors/src/connectors/database/base_sql.py:203-216`

**Current Issue:**
```python
# Lines 206, 212 - Table name used directly in f-string without validation
text(f"SELECT COUNT(*) FROM {source}")
text(f"SELECT * FROM {source} LIMIT :limit")
```

**Fix:** Validate and properly quote table names using SQLAlchemy's quote_identifier or a whitelist approach.

---

## Task 5: Upgrade Next.js to Address Critical CVEs

**Files:**
- Modify: `packages/ui/package.json:31`

**Current Issue:**
```json
"next": "14.1.0"  // 13 critical CVEs
```

**Fix:** Upgrade to Next.js 14.2.x or later with security patches.

---

## Execution Order

1. Task 1 (JWT) - Blocks all authenticated API usage
2. Task 2 (transformation.py eval) - RCE vulnerability
3. Task 3 (compiler.py eval) - RCE vulnerability
4. Task 4 (SQL injection) - Data exposure risk
5. Task 5 (Next.js) - Client-side vulnerabilities

Each task will be committed separately with a descriptive message.
