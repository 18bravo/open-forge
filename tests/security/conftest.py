"""
Shared fixtures for security testing.
"""
import os
from typing import Dict

import pytest
import pytest_asyncio


def get_security_test_env() -> Dict[str, str]:
    """Get environment variables for security testing."""
    return {
        "ENVIRONMENT": "security-test",
        "DATABASE__HOST": os.environ.get("TEST_DB_HOST", "localhost"),
        "DATABASE__PORT": os.environ.get("TEST_DB_PORT", "5432"),
        "DATABASE__NAME": os.environ.get("TEST_DB_NAME", "openforge_test"),
        "DATABASE__USER": os.environ.get("TEST_DB_USER", "foundry"),
        "DATABASE__PASSWORD": os.environ.get("TEST_DB_PASSWORD", "foundry_dev"),
        "LLM__PROVIDER": "mock",
        "DEBUG": "false",  # Ensure debug mode is off for security tests
    }


@pytest.fixture(scope="session")
def security_test_env():
    """Set up security test environment."""
    env_vars = get_security_test_env()
    original_env = {k: os.environ.get(k) for k in env_vars}

    os.environ.update(env_vars)

    yield env_vars

    for k, v in original_env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


@pytest_asyncio.fixture
async def security_test_client(security_test_env):
    """Create a test client for security testing."""
    from httpx import AsyncClient, ASGITransport
    from api.main import create_app

    app = create_app()

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        timeout=30.0
    ) as client:
        yield client


@pytest.fixture
def valid_auth_headers():
    """Valid authentication headers."""
    return {
        "Authorization": "Bearer valid-test-token",
        "Content-Type": "application/json",
    }


@pytest.fixture
def invalid_auth_headers():
    """Invalid authentication headers for testing auth failures."""
    return {
        "Authorization": "Bearer invalid-token-12345",
        "Content-Type": "application/json",
    }


@pytest.fixture
def no_auth_headers():
    """Headers without authentication."""
    return {
        "Content-Type": "application/json",
    }


# Common malicious payloads for security testing
SQL_INJECTION_PAYLOADS = [
    "'; DROP TABLE users; --",
    "1' OR '1'='1",
    "1; SELECT * FROM users",
    "admin'--",
    "' UNION SELECT * FROM users --",
    "1 AND 1=1",
    "' OR 1=1 #",
    "'; WAITFOR DELAY '0:0:10'--",
]

XSS_PAYLOADS = [
    "<script>alert('xss')</script>",
    "<img src=x onerror=alert('xss')>",
    "<svg onload=alert('xss')>",
    "javascript:alert('xss')",
    "<body onload=alert('xss')>",
    "'\"><script>alert('xss')</script>",
    "<iframe src=\"javascript:alert('xss')\">",
    "<a href=\"javascript:alert('xss')\">click</a>",
]

PATH_TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\system32\\config\\sam",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc/passwd",
    "/etc/passwd%00.txt",
]

COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| cat /etc/passwd",
    "& whoami",
    "`id`",
    "$(cat /etc/passwd)",
    "|| ping -c 10 127.0.0.1",
]

LDAP_INJECTION_PAYLOADS = [
    "*)(uid=*))(|(uid=*",
    "admin)(&)",
    "x)(|(cn=*))%00",
]

HEADER_INJECTION_PAYLOADS = [
    "Header-Value\r\nX-Injected: true",
    "value\nSet-Cookie: injected=true",
]


def pytest_configure(config):
    """Configure custom pytest markers for security tests."""
    config.addinivalue_line(
        "markers", "security: marks tests as security tests"
    )
    config.addinivalue_line(
        "markers", "auth: marks tests related to authentication"
    )
    config.addinivalue_line(
        "markers", "authz: marks tests related to authorization"
    )
    config.addinivalue_line(
        "markers", "injection: marks tests for injection vulnerabilities"
    )
    config.addinivalue_line(
        "markers", "xss: marks tests for XSS vulnerabilities"
    )
    config.addinivalue_line(
        "markers", "owasp: marks tests based on OWASP Top 10"
    )
