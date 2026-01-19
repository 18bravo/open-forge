# Comprehensive Code Review Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Conduct a thorough code review of the Open Forge project to identify bugs, security vulnerabilities, code quality issues, and improvement opportunities before production deployment.

**Architecture:** Systematic review of all 12 packages organized by layer (infrastructure → core → agents → API → UI), with dedicated passes for security, performance, testing coverage, and documentation completeness.

**Tech Stack:** Python 3.11+, TypeScript/React, FastAPI, LangGraph, Dagster, PostgreSQL, Kubernetes

---

## Review Methodology

Each task follows this pattern:
1. **Scan** - Identify files and understand structure
2. **Analyze** - Check against criteria
3. **Document** - Record findings in review report
4. **Prioritize** - Classify as Critical/High/Medium/Low

**Output:** `docs/reviews/2026-01-19-code-review-report.md`

---

### Task 1: Create Review Report Structure

**Files:**
- Create: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Create review report template**

```markdown
# Open Forge Code Review Report

**Date:** 2026-01-19
**Reviewer:** Claude Code
**Scope:** Full codebase review (Gates 1-9)

---

## Executive Summary

| Category | Critical | High | Medium | Low |
|----------|----------|------|--------|-----|
| Security | 0 | 0 | 0 | 0 |
| Bugs | 0 | 0 | 0 | 0 |
| Performance | 0 | 0 | 0 | 0 |
| Code Quality | 0 | 0 | 0 | 0 |
| Testing | 0 | 0 | 0 | 0 |
| Documentation | 0 | 0 | 0 | 0 |

---

## Critical Findings

_None identified yet._

---

## Security Review

### Authentication & Authorization
_Pending review._

### Input Validation
_Pending review._

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
```

**Step 2: Create the reviews directory and file**

Run: `mkdir -p docs/reviews && touch docs/reviews/2026-01-19-code-review-report.md`

**Step 3: Commit**

```bash
git add docs/reviews/
git commit -m "docs: initialize code review report structure"
```

---

### Task 2: Security Review - Authentication & Authorization

**Files:**
- Review: `packages/api/src/api/dependencies.py`
- Review: `packages/api/src/api/routers/*.py`
- Review: `packages/api/src/api/auth.py` (if exists)
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review authentication implementation**

Check for:
- [ ] JWT token validation (signature, expiration, issuer)
- [ ] API key validation and storage (hashed, not plaintext)
- [ ] Session management (timeout, rotation)
- [ ] Password handling (bcrypt/argon2, no plaintext)

Run: `grep -r "jwt\|token\|api_key\|password\|auth" packages/api/src/api/ --include="*.py" -n`

**Step 2: Review authorization patterns**

Check for:
- [ ] Role-based access control (RBAC) implementation
- [ ] Resource ownership validation
- [ ] Permission checks on all endpoints
- [ ] No authorization bypass vulnerabilities

Run: `grep -r "Depends\|get_current_user\|permission\|role" packages/api/src/api/routers/ --include="*.py" -n`

**Step 3: Check for hardcoded secrets**

Run: `grep -rE "(password|secret|key|token)\s*=\s*['\"][^'\"]+['\"]" packages/ --include="*.py" -n | grep -v "test\|example\|placeholder"`

**Step 4: Document findings in review report**

Update the "Authentication & Authorization" section with:
- Findings (with file:line references)
- Severity classification
- Recommended fixes

**Step 5: Commit review progress**

```bash
git add docs/reviews/
git commit -m "docs: complete auth security review"
```

---

### Task 3: Security Review - Input Validation

**Files:**
- Review: `packages/api/src/api/schemas/*.py`
- Review: `packages/api/src/api/routers/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review Pydantic schema validation**

Check for:
- [ ] All API inputs have Pydantic models
- [ ] String fields have max_length constraints
- [ ] Numeric fields have min/max bounds
- [ ] Email/URL fields use proper validators
- [ ] Enum fields for constrained choices

Run: `grep -r "class.*BaseModel\|Field\|validator\|constr\|conint" packages/api/src/api/schemas/ --include="*.py" -n`

**Step 2: Check for SQL injection vulnerabilities**

Check for:
- [ ] No raw SQL string concatenation
- [ ] Parameterized queries used
- [ ] SQLAlchemy ORM used properly

Run: `grep -rE "execute\(|raw\(|text\(" packages/ --include="*.py" -n`

**Step 3: Check for command injection**

Check for:
- [ ] No subprocess with shell=True and user input
- [ ] No os.system() with user input
- [ ] No eval() or exec() with user input

Run: `grep -rE "subprocess\.|os\.system\(|eval\(|exec\(" packages/ --include="*.py" -n`

**Step 4: Check for path traversal**

Check for:
- [ ] File paths validated/sanitized
- [ ] No direct user input in file operations

Run: `grep -rE "open\(|Path\(|os\.path" packages/ --include="*.py" -n | grep -v test`

**Step 5: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete input validation security review"
```

---

### Task 4: Security Review - Secrets & Dependencies

**Files:**
- Review: `packages/*/pyproject.toml`
- Review: `packages/ui/package.json`
- Review: `.env*` files (if any)
- Review: `infrastructure/security/secrets/`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Check for committed secrets**

Run: `git log --all --full-history -p | grep -iE "(api_key|secret|password|token)\s*=\s*['\"][^'\"]{8,}['\"]" | head -20`

**Step 2: Run dependency vulnerability scan**

Run: `pip-audit --desc 2>/dev/null || echo "pip-audit not installed - install with: pip install pip-audit"`

**Step 3: Check npm vulnerabilities**

Run: `cd packages/ui && npm audit --json 2>/dev/null | head -50 || echo "Run npm audit manually"`

**Step 4: Review External Secrets configuration**

Check for:
- [ ] All sensitive values reference external secrets
- [ ] No plaintext secrets in ConfigMaps
- [ ] Proper secret rotation policies defined

Run: `grep -r "secretKeyRef\|ExternalSecret\|SecretStore" infrastructure/ --include="*.yaml" -n`

**Step 5: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete secrets and dependencies security review"
```

---

### Task 5: Code Quality Review - Core Package

**Files:**
- Review: `packages/core/src/core/**/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Check type annotations**

Check for:
- [ ] All public functions have type hints
- [ ] Return types specified
- [ ] No `Any` types without justification

Run: `grep -r "def " packages/core/src/core/ --include="*.py" | grep -v "-> " | head -20`

**Step 2: Check error handling**

Check for:
- [ ] Specific exception types (not bare `except:`)
- [ ] Proper error messages with context
- [ ] No silent failures (empty except blocks)

Run: `grep -rE "except:|except Exception:" packages/core/src/core/ --include="*.py" -n`

**Step 3: Check code complexity**

Check for:
- [ ] Functions under 50 lines
- [ ] Cyclomatic complexity reasonable
- [ ] No deeply nested conditionals (>3 levels)

Run: `find packages/core/src/core -name "*.py" -exec wc -l {} \; | sort -n | tail -10`

**Step 4: Check for code smells**

Check for:
- [ ] No global mutable state
- [ ] No circular imports
- [ ] Proper separation of concerns

Run: `grep -r "^[A-Z_].*= \[\]$\|^[A-Z_].*= {}$" packages/core/src/core/ --include="*.py" -n`

**Step 5: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete core package quality review"
```

---

### Task 6: Code Quality Review - Agent Framework

**Files:**
- Review: `packages/agent-framework/src/agent_framework/**/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review LangGraph patterns**

Check for:
- [ ] Proper StateGraph construction
- [ ] State immutability respected
- [ ] Correct edge definitions
- [ ] Checkpointer integration

Run: `grep -r "StateGraph\|add_node\|add_edge\|compile" packages/agent-framework/ --include="*.py" -n`

**Step 2: Review memory management**

Check for:
- [ ] Proper PostgresSaver usage
- [ ] Memory namespace isolation
- [ ] No memory leaks in long-running agents

Run: `grep -r "PostgresSaver\|MemoryStore\|checkpoint" packages/agent-framework/ --include="*.py" -n`

**Step 3: Review tool definitions**

Check for:
- [ ] Proper tool annotations
- [ ] Input validation in tools
- [ ] Error handling in tool execution
- [ ] No blocking operations in async tools

Run: `grep -r "@tool\|StructuredTool\|BaseTool" packages/agent-framework/ --include="*.py" -n`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete agent-framework quality review"
```

---

### Task 7: Code Quality Review - Agents Package

**Files:**
- Review: `packages/agents/src/agents/**/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review agent cluster patterns**

Check for:
- [ ] Consistent agent structure across clusters
- [ ] Proper inheritance from base classes
- [ ] Correct supervisor patterns

Run: `grep -r "class.*Agent\|create_react_agent\|create_supervisor" packages/agents/ --include="*.py" -n`

**Step 2: Review prompt engineering**

Check for:
- [ ] Clear, well-structured prompts
- [ ] No prompt injection vulnerabilities
- [ ] Proper variable interpolation

Run: `grep -r "SystemMessage\|HumanMessage\|prompt" packages/agents/ --include="*.py" -n | head -30`

**Step 3: Review agent tool usage**

Check for:
- [ ] Appropriate tools for each agent type
- [ ] No overly permissive tool access
- [ ] Tool error handling

Run: `grep -r "tools=\[" packages/agents/ --include="*.py" -n`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete agents package quality review"
```

---

### Task 8: Code Quality Review - API Package

**Files:**
- Review: `packages/api/src/api/**/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review FastAPI patterns**

Check for:
- [ ] Proper dependency injection
- [ ] Correct HTTP status codes
- [ ] Consistent response models
- [ ] Proper async/await usage

Run: `grep -r "@router\.\|Depends\|status\." packages/api/src/api/routers/ --include="*.py" -n | head -30`

**Step 2: Review error handling**

Check for:
- [ ] HTTPException with proper status codes
- [ ] Error response schema consistency
- [ ] No stack traces in production errors

Run: `grep -r "HTTPException\|raise\|except" packages/api/src/api/ --include="*.py" -n | head -30`

**Step 3: Review database operations**

Check for:
- [ ] Session management (proper closing)
- [ ] Transaction handling
- [ ] N+1 query problems

Run: `grep -r "session\|commit\|rollback" packages/api/src/api/ --include="*.py" -n`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete API package quality review"
```

---

### Task 9: Code Quality Review - UI Package

**Files:**
- Review: `packages/ui/src/**/*.tsx`
- Review: `packages/ui/src/**/*.ts`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review React patterns**

Check for:
- [ ] Proper hook usage (useEffect dependencies)
- [ ] Memoization where needed (useMemo, useCallback)
- [ ] No state mutations
- [ ] Proper error boundaries

Run: `grep -r "useEffect\|useMemo\|useCallback\|useState" packages/ui/src/ --include="*.tsx" -n | head -30`

**Step 2: Review React Query usage**

Check for:
- [ ] Proper query key management
- [ ] Error handling in queries
- [ ] Optimistic updates where appropriate
- [ ] Stale time configuration

Run: `grep -r "useQuery\|useMutation\|queryKey" packages/ui/src/ --include="*.ts" --include="*.tsx" -n | head -30`

**Step 3: Review TypeScript strictness**

Check for:
- [ ] No `any` types
- [ ] Proper interface definitions
- [ ] No type assertions without validation

Run: `grep -r ": any\|as any" packages/ui/src/ --include="*.ts" --include="*.tsx" -n`

**Step 4: Review accessibility**

Check for:
- [ ] Proper ARIA labels
- [ ] Keyboard navigation
- [ ] Color contrast

Run: `grep -r "aria-\|role=\|tabIndex" packages/ui/src/ --include="*.tsx" -n | head -20`

**Step 5: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete UI package quality review"
```

---

### Task 10: Performance Review

**Files:**
- Review: All packages for performance issues
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Check for N+1 queries**

Look for loops that make database calls:

Run: `grep -rB5 "for.*in.*:" packages/ --include="*.py" | grep -A5 "session\|query\|select" | head -30`

**Step 2: Check async patterns**

Look for blocking calls in async functions:

Run: `grep -rE "async def" packages/ --include="*.py" -A10 | grep -E "time\.sleep|requests\." | head -20`

**Step 3: Check for memory leaks**

Look for unbounded collections:

Run: `grep -r "\.append\|\.extend" packages/ --include="*.py" -B3 | grep -v "test" | head -30`

**Step 4: Check caching usage**

Verify caching is used for expensive operations:

Run: `grep -r "@cached\|@lru_cache\|cache\." packages/ --include="*.py" -n | head -20`

**Step 5: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete performance review"
```

---

### Task 11: Testing Review

**Files:**
- Review: `packages/*/tests/**/*.py`
- Review: `packages/ui/src/__tests__/**/*.tsx`
- Review: `tests/**/*.py`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Check test coverage**

Run: `pytest --cov=packages --cov-report=term-missing 2>/dev/null | tail -50 || echo "Run pytest with coverage manually"`

**Step 2: Review test quality**

Check for:
- [ ] Tests have clear assertions (not just "no error")
- [ ] Edge cases covered
- [ ] Proper mocking (not testing mocks)
- [ ] Test isolation (no shared state)

Run: `grep -r "assert\|expect" packages/*/tests tests/ --include="*.py" | wc -l`

**Step 3: Check for missing tests**

Identify untested functions:

Run: `find packages -name "*.py" -path "*/src/*" | xargs grep -l "def " | while read f; do basename "$f" .py; done | sort -u > /tmp/src_files.txt && find packages tests -name "test_*.py" | xargs grep -l "def test_" | while read f; do basename "$f" .py | sed 's/test_//'; done | sort -u > /tmp/test_files.txt && comm -23 /tmp/src_files.txt /tmp/test_files.txt | head -20`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete testing review"
```

---

### Task 12: Documentation Review

**Files:**
- Review: `docs/**/*.md`
- Review: `packages/*/README.md`
- Review: Code docstrings
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Check API documentation completeness**

Compare endpoints to docs:

Run: `grep -r "@router\." packages/api/src/api/routers/ --include="*.py" | wc -l && echo "vs" && grep -c "path:" docs/api/openapi.yaml`

**Step 2: Check docstring coverage**

Run: `grep -rE "def [a-z_]+\(" packages/*/src/ --include="*.py" | wc -l && echo "functions vs" && grep -rE '"""' packages/*/src/ --include="*.py" | wc -l && echo "docstrings"`

**Step 3: Check README completeness**

Verify each package has README with:
- [ ] Purpose description
- [ ] Installation instructions
- [ ] Usage examples
- [ ] API reference

Run: `find packages -name "README.md" -exec echo "=== {} ===" \; -exec head -5 {} \;`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete documentation review"
```

---

### Task 13: Infrastructure Review

**Files:**
- Review: `infrastructure/kubernetes/**/*.yaml`
- Review: `infrastructure/helm/**/*.yaml`
- Review: `infrastructure/docker/**/*`
- Review: `.github/workflows/**/*.yml`
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Review Kubernetes security**

Check for:
- [ ] No root containers
- [ ] Resource limits set
- [ ] Network policies applied
- [ ] Secrets not in plain text

Run: `grep -r "securityContext\|runAsNonRoot\|resources:" infrastructure/kubernetes/ --include="*.yaml" -n | head -20`

**Step 2: Review CI/CD security**

Check for:
- [ ] No hardcoded secrets in workflows
- [ ] Proper secret references
- [ ] Pinned action versions

Run: `grep -r "secrets\.\|env:" .github/workflows/ --include="*.yml" -n | head -20`

**Step 3: Review Dockerfile best practices**

Check for:
- [ ] Multi-stage builds
- [ ] Non-root user
- [ ] Minimal base images
- [ ] No secrets in build args

Run: `grep -E "FROM|USER|ARG|ENV" infrastructure/docker/Dockerfile.* | head -30`

**Step 4: Document findings and commit**

```bash
git add docs/reviews/
git commit -m "docs: complete infrastructure review"
```

---

### Task 14: Finalize Review Report

**Files:**
- Update: `docs/reviews/2026-01-19-code-review-report.md`

**Step 1: Compile executive summary**

- Count findings by severity
- Identify top 5 critical/high issues
- Calculate overall health score

**Step 2: Write recommendations**

Organize into:
- Immediate actions (Critical/High - fix before deployment)
- Short-term improvements (Medium - fix within 2 weeks)
- Future enhancements (Low - backlog items)

**Step 3: Final commit**

```bash
git add docs/reviews/
git commit -m "docs: finalize comprehensive code review report"
```

**Step 4: Push review**

```bash
git push origin main
```

---

## Review Checklist Summary

### Security
- [ ] Authentication implementation
- [ ] Authorization checks
- [ ] Input validation (SQL, command, path injection)
- [ ] Secrets management
- [ ] Dependency vulnerabilities

### Code Quality
- [ ] Type annotations
- [ ] Error handling
- [ ] Code complexity
- [ ] Package: core
- [ ] Package: agent-framework
- [ ] Package: agents
- [ ] Package: api
- [ ] Package: ui

### Performance
- [ ] N+1 queries
- [ ] Async patterns
- [ ] Memory management
- [ ] Caching

### Testing
- [ ] Coverage
- [ ] Test quality
- [ ] Missing tests

### Documentation
- [ ] API docs
- [ ] Docstrings
- [ ] READMEs

### Infrastructure
- [ ] Kubernetes security
- [ ] CI/CD security
- [ ] Dockerfile best practices
