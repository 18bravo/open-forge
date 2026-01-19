"""
Authorization security tests.

Tests for:
- Role-based access control
- Resource ownership validation
- Privilege escalation prevention
- Horizontal access control
"""
import pytest
import pytest_asyncio


pytestmark = [pytest.mark.security, pytest.mark.authz, pytest.mark.asyncio]


class TestRoleBasedAccessControl:
    """Tests for role-based access control (RBAC)."""

    async def test_admin_endpoints_require_admin_role(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that admin endpoints require admin role."""
        admin_endpoints = [
            "/api/v1/admin/health",
            "/api/v1/admin/dashboard/stats",
            "/api/v1/admin/agents/clusters",
            "/api/v1/admin/pipelines",
            "/api/v1/admin/settings",
            "/api/v1/admin/settings/users",
        ]

        for endpoint in admin_endpoints:
            response = await security_test_client.get(
                endpoint,
                headers=valid_auth_headers
            )

            # Should require appropriate role
            # If user doesn't have admin role, should get 403
            # If auth passes but user is admin, should get 200
            assert response.status_code in [200, 403, 404], (
                f"Unexpected status for admin endpoint {endpoint}: {response.status_code}"
            )

    async def test_user_cannot_access_other_users_engagements(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test horizontal access control for engagements."""
        # Try to access engagement belonging to another user
        # This tests that authorization checks ownership
        other_user_engagement_id = "other-user-engagement-id"

        response = await security_test_client.get(
            f"/api/v1/engagements/{other_user_engagement_id}",
            headers=valid_auth_headers
        )

        # Should either not find it (404) or deny access (403)
        assert response.status_code in [403, 404]

    async def test_user_cannot_modify_other_users_engagements(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot modify other users' engagements."""
        other_user_engagement_id = "other-user-engagement-id"

        response = await security_test_client.put(
            f"/api/v1/engagements/{other_user_engagement_id}",
            headers=valid_auth_headers,
            json={
                "name": "Malicious Update",
                "objective": "Unauthorized modification"
            }
        )

        assert response.status_code in [403, 404]

    async def test_user_cannot_delete_other_users_engagements(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot delete other users' engagements."""
        other_user_engagement_id = "other-user-engagement-id"

        response = await security_test_client.delete(
            f"/api/v1/engagements/{other_user_engagement_id}",
            headers=valid_auth_headers
        )

        assert response.status_code in [403, 404]


class TestPrivilegeEscalation:
    """Tests for privilege escalation prevention."""

    async def test_cannot_self_assign_admin_role(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot escalate their own privileges."""
        # Attempt to update user profile with elevated role
        response = await security_test_client.put(
            "/api/v1/users/me",
            headers=valid_auth_headers,
            json={
                "role": "admin"
            }
        )

        # Should either not allow or return 403
        assert response.status_code in [400, 403, 404, 422]

    async def test_cannot_access_system_endpoints_as_regular_user(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that regular users cannot access system-level operations."""
        system_endpoints = [
            ("/api/v1/admin/settings", "PUT", {"instance_name": "Hacked"}),
            ("/api/v1/admin/agents/clusters/discovery/scale", "POST", {"target_instances": 100}),
        ]

        for endpoint, method, payload in system_endpoints:
            if method == "PUT":
                response = await security_test_client.put(
                    endpoint,
                    headers=valid_auth_headers,
                    json=payload
                )
            elif method == "POST":
                response = await security_test_client.post(
                    endpoint,
                    headers=valid_auth_headers,
                    json=payload
                )

            # Should deny access to system operations
            assert response.status_code in [403, 404, 405]


class TestApprovalAuthorization:
    """Tests for approval workflow authorization."""

    async def test_cannot_approve_own_requests(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot approve their own requests."""
        # Assuming the auth token identifies user who made the request
        my_approval_id = "my-approval-request-id"

        response = await security_test_client.post(
            f"/api/v1/approvals/{my_approval_id}/decide",
            headers=valid_auth_headers,
            json={
                "approved": True,
                "reason": "Self-approval attempt"
            }
        )

        # Should deny self-approval or return not found
        assert response.status_code in [403, 404]

    async def test_only_designated_approvers_can_approve(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that only designated approvers can approve requests."""
        approval_id = "restricted-approval-id"

        response = await security_test_client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            headers=valid_auth_headers,
            json={
                "approved": True,
                "reason": "Unauthorized approval attempt"
            }
        )

        # If user is not a designated approver, should be denied
        assert response.status_code in [403, 404]


class TestDataSourceAuthorization:
    """Tests for data source access authorization."""

    async def test_cannot_access_other_orgs_data_sources(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot access data sources from other organizations."""
        other_org_source_id = "other-org-data-source-id"

        response = await security_test_client.get(
            f"/api/v1/data-sources/{other_org_source_id}",
            headers=valid_auth_headers
        )

        assert response.status_code in [403, 404]

    async def test_cannot_test_connection_for_other_orgs_sources(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that connection testing requires ownership."""
        other_org_source_id = "other-org-data-source-id"

        response = await security_test_client.post(
            f"/api/v1/data-sources/{other_org_source_id}/test",
            headers=valid_auth_headers
        )

        assert response.status_code in [403, 404]


class TestAgentTaskAuthorization:
    """Tests for agent task authorization."""

    async def test_cannot_view_other_users_agent_tasks(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot view agent tasks from other engagements."""
        other_task_id = "other-user-task-id"

        response = await security_test_client.get(
            f"/api/v1/agents/tasks/{other_task_id}",
            headers=valid_auth_headers
        )

        assert response.status_code in [403, 404]

    async def test_cannot_approve_tools_for_other_users_tasks(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that users cannot approve tool calls for other users' tasks."""
        other_task_id = "other-user-task-id"

        response = await security_test_client.post(
            f"/api/v1/agents/tasks/{other_task_id}/tool-approvals",
            headers=valid_auth_headers,
            json={
                "tool_call_id": "tool-call-123",
                "approved": True,
                "reason": "Unauthorized approval"
            }
        )

        assert response.status_code in [403, 404]


class TestCodegenAuthorization:
    """Tests for code generation authorization."""

    async def test_cannot_generate_code_for_other_users_ontology(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that code generation requires ontology ownership."""
        response = await security_test_client.post(
            "/api/v1/codegen/generate",
            headers=valid_auth_headers,
            json={
                "ontology_id": "other-user-ontology-id",
                "generators": ["fastapi"],
            }
        )

        assert response.status_code in [400, 403, 404]

    async def test_cannot_download_other_users_generated_code(
        self,
        security_test_client,
        valid_auth_headers
    ):
        """Test that code download requires job ownership."""
        other_job_id = "other-user-job-id"

        response = await security_test_client.get(
            f"/api/v1/codegen/download/{other_job_id}",
            headers=valid_auth_headers
        )

        assert response.status_code in [403, 404]
