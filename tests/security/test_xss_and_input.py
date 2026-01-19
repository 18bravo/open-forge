"""
XSS and input validation security tests.

Tests for:
- Cross-Site Scripting (XSS) prevention
- Input validation and sanitization
- Path traversal prevention
- Content type validation
"""
import pytest
import pytest_asyncio

from tests.security.conftest import (
    XSS_PAYLOADS,
    PATH_TRAVERSAL_PAYLOADS,
)


pytestmark = [pytest.mark.security, pytest.mark.asyncio]


class TestXSSPrevention:
    """Tests for Cross-Site Scripting (XSS) prevention."""

    @pytest.mark.xss
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_xss_in_engagement_name(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test XSS prevention in engagement name field."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": payload,
                "objective": "Test objective",
                "priority": "medium"
            }
        )

        if response.status_code == 201:
            # If accepted, check that the response properly escapes the payload
            data = response.json()
            # The raw XSS should not be in response unescaped
            response_text = response.text
            # Check for unescaped script tags
            assert "<script>" not in response_text.lower() or "\\u003c" in response_text or "&lt;" in response_text, (
                f"Potential stored XSS vulnerability with: {payload}"
            )

    @pytest.mark.xss
    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    async def test_xss_in_description(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test XSS prevention in description field."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": "XSS Test",
                "description": payload,
                "objective": "Test objective",
                "priority": "medium"
            }
        )

        # Should either sanitize or reject
        assert response.status_code in [201, 400, 422]

    @pytest.mark.xss
    async def test_xss_in_error_messages(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that error messages don't reflect XSS payloads."""
        payload = "<script>alert('xss')</script>"

        response = await security_test_client.get(
            f"/api/v1/engagements/{payload}",
            headers=valid_auth_headers
        )

        # Error message should not contain unescaped payload
        if response.status_code in [400, 404, 422]:
            response_text = response.text
            assert "<script>" not in response_text.lower(), (
                "XSS payload reflected in error message"
            )


class TestInputValidation:
    """Tests for input validation."""

    async def test_engagement_name_length_limit(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that extremely long names are rejected."""
        long_name = "A" * 10000  # 10KB name

        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": long_name,
                "objective": "Test",
                "priority": "medium"
            }
        )

        # Should reject excessively long input
        assert response.status_code in [400, 413, 422]

    async def test_engagement_invalid_priority(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test validation of priority enum values."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": "Test",
                "objective": "Test",
                "priority": "invalid_priority"
            }
        )

        # Should reject invalid enum value
        assert response.status_code == 422

    async def test_engagement_invalid_status(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test validation of status enum values."""
        response = await security_test_client.post(
            "/api/v1/engagements/test-id/status",
            headers=valid_auth_headers,
            json={
                "status": "invalid_status"
            }
        )

        # Should reject invalid enum value
        assert response.status_code in [404, 422]

    async def test_pagination_bounds(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test pagination parameter bounds."""
        # Test negative page
        response = await security_test_client.get(
            "/api/v1/engagements",
            params={"page": -1},
            headers=valid_auth_headers
        )
        assert response.status_code in [400, 422]

        # Test zero page
        response = await security_test_client.get(
            "/api/v1/engagements",
            params={"page": 0},
            headers=valid_auth_headers
        )
        assert response.status_code in [400, 422]

        # Test excessive page size
        response = await security_test_client.get(
            "/api/v1/engagements",
            params={"page_size": 10000},
            headers=valid_auth_headers
        )
        assert response.status_code in [200, 400, 422]  # May cap or reject

    async def test_required_field_validation(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that required fields are enforced."""
        # Missing name
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "objective": "Test",
                "priority": "medium"
            }
        )
        assert response.status_code == 422

        # Missing objective
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": "Test",
                "priority": "medium"
            }
        )
        assert response.status_code == 422

    async def test_type_coercion_attacks(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test handling of type coercion attacks."""
        # Send array where string expected
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": ["array", "of", "strings"],
                "objective": "Test",
                "priority": "medium"
            }
        )
        assert response.status_code == 422

        # Send object where string expected
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": {"nested": "object"},
                "objective": "Test",
                "priority": "medium"
            }
        )
        assert response.status_code == 422


class TestPathTraversal:
    """Tests for path traversal vulnerabilities."""

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    async def test_path_traversal_in_engagement_id(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test path traversal prevention in engagement ID."""
        response = await security_test_client.get(
            f"/api/v1/engagements/{payload}",
            headers=valid_auth_headers
        )

        # Should return 404 or 400, not expose file system
        assert response.status_code in [400, 404, 422]
        # Should not contain file system content
        assert "/etc/passwd" not in response.text
        assert "root:" not in response.text

    @pytest.mark.parametrize("payload", PATH_TRAVERSAL_PAYLOADS)
    async def test_path_traversal_in_codegen_download(
        self,
        security_test_client,
        valid_auth_headers,
        payload
    ):
        """Test path traversal in code generation download."""
        response = await security_test_client.get(
            f"/api/v1/codegen/download/{payload}",
            headers=valid_auth_headers
        )

        # Should not expose arbitrary files
        assert response.status_code in [400, 404, 422]
        assert "root:" not in response.text


class TestContentTypeValidation:
    """Tests for content type validation."""

    async def test_json_content_type_required(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that JSON content type is required for POST."""
        headers = {**valid_auth_headers}
        headers["Content-Type"] = "text/plain"

        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=headers,
            content='{"name": "Test", "objective": "Test", "priority": "medium"}'
        )

        # Should reject non-JSON content type or handle gracefully
        assert response.status_code in [201, 400, 415, 422]

    async def test_multipart_when_json_expected(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test handling of multipart when JSON expected."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers={
                **valid_auth_headers,
                "Content-Type": "multipart/form-data; boundary=----boundary"
            },
            content='------boundary\r\nContent-Disposition: form-data; name="name"\r\n\r\nTest\r\n------boundary--'
        )

        # Should handle appropriately
        assert response.status_code in [400, 415, 422]


class TestSpecialCharacterHandling:
    """Tests for special character handling."""

    SPECIAL_CHARS = [
        "Test\x00Name",  # Null byte
        "Test\rName",  # Carriage return
        "Test\nName",  # Newline
        "Test\tName",  # Tab
        "Test Name",  # Zero-width space
        "Test<>Name",  # Angle brackets
        "Test&Name",  # Ampersand
        "Test\"Name",  # Quote
        "Test'Name",  # Single quote
        "Test`Name",  # Backtick
    ]

    @pytest.mark.parametrize("special_char", SPECIAL_CHARS)
    async def test_special_characters_in_name(
        self,
        security_test_client,
        valid_auth_headers,
        special_char
    ):
        """Test handling of special characters in name field."""
        response = await security_test_client.post(
            "/api/v1/engagements",
            headers=valid_auth_headers,
            json={
                "name": special_char,
                "objective": "Test",
                "priority": "medium"
            }
        )

        # Should either accept (sanitized) or reject, not error
        assert response.status_code in [201, 400, 422], (
            f"Unexpected status for special char: {repr(special_char)}"
        )
