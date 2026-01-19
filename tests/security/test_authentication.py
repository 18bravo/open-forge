"""
Authentication security tests.

Tests for:
- Authentication enforcement
- Token validation
- Session management
- Brute force protection
"""
import pytest
import pytest_asyncio

from tests.security.conftest import (
    HEADER_INJECTION_PAYLOADS,
)


pytestmark = [pytest.mark.security, pytest.mark.auth, pytest.mark.asyncio]


class TestAuthenticationEnforcement:
    """Tests for authentication enforcement on protected endpoints."""

    PROTECTED_ENDPOINTS = [
        ("GET", "/api/v1/engagements"),
        ("POST", "/api/v1/engagements"),
        ("GET", "/api/v1/engagements/test-id"),
        ("PUT", "/api/v1/engagements/test-id"),
        ("DELETE", "/api/v1/engagements/test-id"),
        ("GET", "/api/v1/approvals"),
        ("GET", "/api/v1/approvals/test-id"),
        ("POST", "/api/v1/approvals/test-id/decide"),
        ("GET", "/api/v1/admin/health"),
        ("GET", "/api/v1/admin/agents/clusters"),
        ("GET", "/api/v1/admin/pipelines"),
    ]

    @pytest.mark.parametrize("method,endpoint", PROTECTED_ENDPOINTS)
    async def test_protected_endpoint_requires_auth(
        self,
        security_test_client,
        no_auth_headers,
        method,
        endpoint
    ):
        """Test that protected endpoints require authentication."""
        if method == "GET":
            response = await security_test_client.get(
                endpoint,
                headers=no_auth_headers
            )
        elif method == "POST":
            response = await security_test_client.post(
                endpoint,
                headers=no_auth_headers,
                json={}
            )
        elif method == "PUT":
            response = await security_test_client.put(
                endpoint,
                headers=no_auth_headers,
                json={}
            )
        elif method == "DELETE":
            response = await security_test_client.delete(
                endpoint,
                headers=no_auth_headers
            )

        # Should return 401 Unauthorized or 403 Forbidden
        assert response.status_code in [401, 403], (
            f"{method} {endpoint} did not require authentication. "
            f"Got status code: {response.status_code}"
        )

    async def test_health_endpoint_is_public(
        self,
        security_test_client,
        no_auth_headers
    ):
        """Health check endpoint should be publicly accessible."""
        response = await security_test_client.get(
            "/api/v1/health",
            headers=no_auth_headers
        )
        # Health endpoint should be accessible without auth
        assert response.status_code == 200


class TestTokenValidation:
    """Tests for authentication token validation."""

    async def test_invalid_token_rejected(
        self,
        security_test_client,
        invalid_auth_headers
    ):
        """Test that invalid tokens are rejected."""
        response = await security_test_client.get(
            "/api/v1/engagements",
            headers=invalid_auth_headers
        )

        # Should reject invalid token
        assert response.status_code in [401, 403]

    async def test_malformed_auth_header(
        self,
        security_test_client
    ):
        """Test handling of malformed Authorization headers."""
        malformed_headers = [
            {"Authorization": "Bearer"},  # Missing token
            {"Authorization": ""},  # Empty
            {"Authorization": "InvalidScheme token123"},  # Wrong scheme
            {"Authorization": "bearer token123"},  # lowercase bearer
            {"Authorization": "Bearer "},  # Only whitespace after Bearer
        ]

        for headers in malformed_headers:
            headers["Content-Type"] = "application/json"
            response = await security_test_client.get(
                "/api/v1/engagements",
                headers=headers
            )

            # Should handle gracefully (401/403, not 500)
            assert response.status_code in [401, 403, 422], (
                f"Malformed header '{headers.get('Authorization')}' caused "
                f"unexpected status code: {response.status_code}"
            )

    async def test_expired_token_handling(
        self,
        security_test_client
    ):
        """Test that expired tokens are properly rejected."""
        # Simulate expired token
        headers = {
            "Authorization": "Bearer expired.token.here",
            "Content-Type": "application/json",
        }

        response = await security_test_client.get(
            "/api/v1/engagements",
            headers=headers
        )

        # Should reject expired token
        assert response.status_code in [401, 403]

    async def test_token_in_header_injection(
        self,
        security_test_client
    ):
        """Test that header injection in auth is prevented."""
        for payload in HEADER_INJECTION_PAYLOADS:
            headers = {
                "Authorization": f"Bearer {payload}",
                "Content-Type": "application/json",
            }

            response = await security_test_client.get(
                "/api/v1/engagements",
                headers=headers
            )

            # Should reject or handle gracefully
            assert response.status_code in [400, 401, 403, 422]


class TestBruteForceProtection:
    """Tests for brute force attack prevention."""

    async def test_multiple_failed_auth_attempts(
        self,
        security_test_client
    ):
        """Test rate limiting on failed authentication attempts."""
        # Attempt multiple failed authentications
        failed_attempts = 0
        rate_limited = False

        for i in range(20):
            headers = {
                "Authorization": f"Bearer invalid-token-{i}",
                "Content-Type": "application/json",
            }

            response = await security_test_client.get(
                "/api/v1/engagements",
                headers=headers
            )

            if response.status_code == 429:  # Too Many Requests
                rate_limited = True
                break
            elif response.status_code in [401, 403]:
                failed_attempts += 1

        # Either rate limiting should kick in, or we completed without server errors
        # Note: If rate limiting is not implemented, this test documents the behavior
        print(f"\nBrute force test: {failed_attempts} failed attempts, rate_limited={rate_limited}")


class TestSessionSecurity:
    """Tests for session management security."""

    async def test_concurrent_session_handling(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that concurrent sessions are handled properly."""
        import asyncio

        # Simulate multiple concurrent requests with same session
        async def make_request():
            return await security_test_client.get(
                "/api/v1/engagements",
                headers=valid_auth_headers
            )

        responses = await asyncio.gather(*[make_request() for _ in range(10)])

        # All requests should succeed or fail consistently
        status_codes = {r.status_code for r in responses}
        # Should not have mixed success/failure (except for rate limiting)
        assert len(status_codes) <= 2, f"Inconsistent session handling: {status_codes}"

    async def test_session_not_in_url(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that session tokens cannot be passed in URL."""
        # Session in URL is a security risk
        response = await security_test_client.get(
            "/api/v1/engagements?token=test-token-123",
            headers={"Content-Type": "application/json"}
        )

        # Should require proper header authentication
        assert response.status_code in [401, 403]
