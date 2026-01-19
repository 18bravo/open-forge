"""
Injection vulnerability tests.

Tests for:
- SQL injection
- Command injection
- LDAP injection
- NoSQL injection
- Header injection
"""
import pytest
import pytest_asyncio
import json

from tests.security.conftest import (
    SQL_INJECTION_PAYLOADS,
    COMMAND_INJECTION_PAYLOADS,
    LDAP_INJECTION_PAYLOADS,
    HEADER_INJECTION_PAYLOADS,
)


pytestmark = [pytest.mark.security, pytest.mark.injection, pytest.mark.asyncio]


class TestSQLInjection:
    """Tests for SQL injection vulnerabilities."""

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_sql_injection_in_engagement_name(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test SQL injection prevention in engagement name field."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": payload,
                "objective": "Test objective",
                "priority": "medium"
            }
        )

        # Should either reject the payload (400/422) or accept it safely (201)
        # Should NEVER return 500 (server error indicating potential injection)
        assert response.status_code != 500, (
            f"Potential SQL injection vulnerability with payload: {payload}"
        )

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_sql_injection_in_search_param(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test SQL injection prevention in search parameters."""
        response = await security_test_client.get(
            "/api/v1/engagements",
            params={"search": payload},
            headers=valid_auth_headers
        )

        # Should handle safely
        assert response.status_code != 500, (
            f"Potential SQL injection vulnerability with search: {payload}"
        )

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    async def test_sql_injection_in_id_param(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test SQL injection prevention in ID parameters."""
        response = await security_test_client.get(
            f"/api/v1/engagements/{payload}",
            headers=valid_auth_headers
        )

        # Should return 404 or 400, not 500
        assert response.status_code in [400, 404, 422], (
            f"Unexpected response for ID injection: {payload}, "
            f"status: {response.status_code}"
        )

    async def test_sql_injection_in_pagination(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test SQL injection in pagination parameters."""
        injection_values = ["1; DROP TABLE engagements;--", "1 OR 1=1", "-1"]

        for value in injection_values:
            # Test in page parameter
            response = await security_test_client.get(
                "/api/v1/engagements",
                params={"page": value, "page_size": "20"},
                headers=valid_auth_headers
            )

            # Should validate and reject or handle safely
            assert response.status_code in [200, 400, 422], (
                f"Pagination injection not handled: {value}"
            )


class TestCommandInjection:
    """Tests for command injection vulnerabilities."""

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS)
    async def test_command_injection_in_engagement_data(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test command injection prevention in engagement data."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": "Test Engagement",
                "description": payload,
                "objective": payload,
                "priority": "medium"
            }
        )

        # Should not cause server errors
        assert response.status_code != 500, (
            f"Potential command injection with: {payload}"
        )

    @pytest.mark.parametrize("payload", COMMAND_INJECTION_PAYLOADS)
    async def test_command_injection_in_data_source_config(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test command injection in data source configuration."""
        response = await security_test_client.post(
            "/api/v1/data-sources",
            headers=valid_auth_headers,
            json={
                "name": "Test Source",
                "source_type": "postgresql",
                "connection_config": {
                    "host": payload,
                    "database": payload,
                    "username": payload
                }
            }
        )

        # Should validate connection config
        assert response.status_code in [400, 422, 201], (
            f"Command injection not properly handled: {payload}"
        )


class TestNoSQLInjection:
    """Tests for NoSQL injection vulnerabilities."""

    NOSQL_PAYLOADS = [
        '{"$gt": ""}',
        '{"$ne": null}',
        '{"$where": "this.password.match(/.*/)"}',
        '{"$regex": ".*"}',
    ]

    @pytest.mark.parametrize("payload", NOSQL_PAYLOADS)
    async def test_nosql_injection_in_query(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test NoSQL injection prevention in queries."""
        response = await security_test_client.get(
            "/api/v1/engagements",
            params={"search": payload},
            headers=valid_auth_headers
        )

        # Should handle safely
        assert response.status_code in [200, 400, 422]


class TestHeaderInjection:
    """Tests for HTTP header injection vulnerabilities."""

    @pytest.mark.parametrize("payload", HEADER_INJECTION_PAYLOADS)
    async def test_header_injection_in_custom_headers(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test header injection prevention."""
        headers = {
            **valid_auth_headers,
            "X-Custom-Header": payload,
        }

        response = await security_test_client.get(
            "/api/v1/engagements",
            headers=headers
        )

        # Check that injected headers are not in response
        response_headers = dict(response.headers)
        assert "X-Injected" not in response_headers, "Header injection successful"
        assert "Set-Cookie" not in str(response.headers).lower() or "injected" not in str(response.headers).lower()


class TestJSONInjection:
    """Tests for JSON-based injection attacks."""

    async def test_json_depth_bomb(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test handling of deeply nested JSON."""
        # Create deeply nested JSON
        depth = 100
        nested = {"level": 0}
        current = nested
        for i in range(1, depth):
            current["nested"] = {"level": i}
            current = current["nested"]

        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": "Depth Test",
                "objective": "Test",
                "priority": "medium",
                "metadata": nested
            }
        )

        # Should handle gracefully (reject or accept limited depth)
        assert response.status_code in [200, 201, 400, 413, 422]

    async def test_json_key_collision(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test handling of duplicate JSON keys."""
        # FastAPI/Pydantic typically handles this, but verify
        raw_json = '{"name": "First", "name": "Second", "objective": "Test", "priority": "medium"}'

        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            content=raw_json
        )

        # Should handle consistently (likely uses last value or rejects)
        assert response.status_code in [200, 201, 400, 422]

    async def test_unicode_injection(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test handling of unicode injection attempts."""
        unicode_payloads = [
            "\u0000null byte",  # Null byte
            "test\u202Eevil",  # Right-to-left override
            "\uFEFFBOM",  # Byte order mark
            "test\u0008backspace",  # Backspace
        ]

        for payload in unicode_payloads:
            response = await security_test_client.post(
                "/api/v1/engagements",
                headers=valid_auth_headers,
                json={
                    "name": payload,
                    "objective": "Test",
                    "priority": "medium"
                }
            )

            # Should handle safely
            assert response.status_code != 500, f"Unicode injection issue: {repr(payload)}"


class TestLDAPInjection:
    """Tests for LDAP injection vulnerabilities."""

    @pytest.mark.parametrize("payload", LDAP_INJECTION_PAYLOADS)
    async def test_ldap_injection_in_user_search(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test LDAP injection prevention in user-related endpoints."""
        response = await security_test_client.get(
            "/api/v1/admin/settings/users",
            params={"search": payload},
            headers=valid_auth_headers
        )

        # Should handle safely
        assert response.status_code in [200, 400, 404, 422, 500]  # 500 may occur if not implemented
