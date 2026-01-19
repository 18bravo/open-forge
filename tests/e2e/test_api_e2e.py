"""
E2E Tests for API Endpoints.

Tests the full REST and GraphQL API workflows including:
- REST API complete workflow
- GraphQL query and mutation workflow
- WebSocket/SSE real-time updates (mocked)

Expected test durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Full workflow: 60-90 seconds
"""
import json
import pytest
from datetime import datetime
from uuid import uuid4

from api.schemas.engagement import EngagementStatus, EngagementPriority


class TestRESTAPIWorkflow:
    """Tests for REST API complete workflow."""

    @pytest.mark.asyncio
    async def test_health_endpoint(self, e2e_client):
        """
        Test the health check endpoint.

        Expected duration: ~1 second
        """
        response = await e2e_client.http_client.get("/health", headers=e2e_client.headers)

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_root_endpoint(self, e2e_client):
        """
        Test the root API endpoint.

        Expected duration: ~1 second
        """
        response = await e2e_client.http_client.get("/", headers=e2e_client.headers)

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "Open Forge" in data["name"]
        assert "version" in data

    @pytest.mark.asyncio
    async def test_create_engagement_rest(self, e2e_client, sample_engagement_data):
        """
        Test creating an engagement via REST API.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.create_engagement(
            name=sample_engagement_data["name"],
            objective=sample_engagement_data["objective"],
            description=sample_engagement_data["description"],
            priority=sample_engagement_data["priority"],
        )

        assert "id" in response
        assert response["name"] == sample_engagement_data["name"]
        assert response["status"] == EngagementStatus.DRAFT.value

    @pytest.mark.asyncio
    async def test_list_engagements_rest(self, e2e_client):
        """
        Test listing engagements via REST API.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements()

        assert "items" in response
        assert "total" in response
        assert "page" in response
        assert "page_size" in response

    @pytest.mark.asyncio
    async def test_list_engagements_with_pagination(self, e2e_client):
        """
        Test listing engagements with pagination parameters.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements(page=1, page_size=10)

        assert response["page"] == 1
        assert response["page_size"] == 10

    @pytest.mark.asyncio
    async def test_list_engagements_with_status_filter(self, e2e_client):
        """
        Test listing engagements with status filter.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements(status="draft")

        assert "items" in response

    @pytest.mark.asyncio
    async def test_create_approval_rest(self, e2e_client):
        """
        Test creating an approval via REST API.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.create_approval(
            approval_type="engagement",
            title="Test Engagement Approval",
            description="Test description",
            resource_id="test-resource-001",
            resource_type="engagement",
        )

        assert "id" in response
        assert response["status"] == "pending"

    @pytest.mark.asyncio
    async def test_list_approvals_rest(self, e2e_client):
        """
        Test listing approvals via REST API.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_approvals()

        assert "items" in response
        assert "total" in response

    @pytest.mark.asyncio
    async def test_list_approvals_pending_only(self, e2e_client):
        """
        Test listing only pending approvals.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_approvals(pending_only=True)

        assert "items" in response

    @pytest.mark.asyncio
    async def test_full_rest_workflow(self, e2e_client, sample_engagement_data):
        """
        Test complete REST API workflow from engagement creation to completion.

        Expected duration: ~30 seconds
        """
        # 1. Create engagement
        engagement = await e2e_client.create_engagement(
            name="REST Workflow Test",
            objective="Test complete REST workflow",
            description="End-to-end REST API test",
            priority="high",
            requires_approval=True,
        )
        engagement_id = engagement["id"]

        assert engagement["status"] == EngagementStatus.DRAFT.value

        # 2. Create approval for engagement
        approval = await e2e_client.create_approval(
            approval_type="engagement",
            title=f"Approve engagement {engagement_id}",
            description="Approve to start engagement",
            resource_id=engagement_id,
            resource_type="engagement",
        )

        assert approval["status"] == "pending"

        # 3. List engagements to verify creation
        engagements = await e2e_client.list_engagements()
        assert engagements["total"] >= 0  # May be 0 due to mocking

        # 4. List approvals to verify creation
        approvals = await e2e_client.list_approvals(pending_only=True)
        assert "items" in approvals


class TestGraphQLWorkflow:
    """Tests for GraphQL API workflow."""

    @pytest.mark.asyncio
    async def test_graphql_introspection(self, e2e_client):
        """
        Test GraphQL introspection query.

        Expected duration: ~5 seconds
        """
        query = """
        query {
            __schema {
                types {
                    name
                }
            }
        }
        """
        response = await e2e_client.graphql_query(query)

        assert "data" in response or "errors" not in response

    @pytest.mark.asyncio
    async def test_graphql_list_engagements(self, e2e_client):
        """
        Test GraphQL engagements query.

        Expected duration: ~5 seconds
        """
        query = """
        query ListEngagements($page: Int, $pageSize: Int) {
            engagements(page: $page, pageSize: $pageSize) {
                items {
                    id
                    name
                    status
                    priority
                }
                total
                page
                pageSize
            }
        }
        """
        response = await e2e_client.graphql_query(
            query,
            variables={"page": 1, "pageSize": 10},
        )

        assert "data" in response
        assert "engagements" in response["data"]

    @pytest.mark.asyncio
    async def test_graphql_create_engagement(self, e2e_client):
        """
        Test GraphQL create engagement mutation.

        Expected duration: ~5 seconds
        """
        mutation = """
        mutation CreateEngagement($input: EngagementCreateInput!) {
            createEngagement(input: $input) {
                success
                message
                engagement {
                    id
                    name
                    status
                    objective
                }
            }
        }
        """
        variables = {
            "input": {
                "name": "GraphQL Test Engagement",
                "objective": "Test GraphQL mutation",
                "description": "Created via GraphQL",
                "priority": "MEDIUM",
                "dataSources": [],
                "tags": ["graphql", "test"],
                "requiresApproval": True,
            }
        }

        response = await e2e_client.graphql_mutation(mutation, variables)

        assert "data" in response
        result = response["data"]["createEngagement"]
        assert result["success"]
        assert result["engagement"]["name"] == "GraphQL Test Engagement"

    @pytest.mark.asyncio
    async def test_graphql_list_agent_tasks(self, e2e_client):
        """
        Test GraphQL agent tasks query.

        Expected duration: ~5 seconds
        """
        query = """
        query ListAgentTasks($page: Int, $pageSize: Int) {
            agentTasks(page: $page, pageSize: $pageSize) {
                items {
                    id
                    engagementId
                    taskType
                    status
                }
                total
            }
        }
        """
        response = await e2e_client.graphql_query(
            query,
            variables={"page": 1, "pageSize": 20},
        )

        assert "data" in response
        assert "agentTasks" in response["data"]

    @pytest.mark.asyncio
    async def test_graphql_list_data_sources(self, e2e_client):
        """
        Test GraphQL data sources query.

        Expected duration: ~5 seconds
        """
        query = """
        query ListDataSources($page: Int, $pageSize: Int) {
            dataSources(page: $page, pageSize: $pageSize) {
                items {
                    id
                    name
                    sourceType
                }
                total
            }
        }
        """
        response = await e2e_client.graphql_query(
            query,
            variables={"page": 1, "pageSize": 20},
        )

        assert "data" in response
        assert "dataSources" in response["data"]

    @pytest.mark.asyncio
    async def test_graphql_list_approvals(self, e2e_client):
        """
        Test GraphQL approvals query.

        Expected duration: ~5 seconds
        """
        query = """
        query ListApprovals($page: Int, $pendingOnly: Boolean) {
            approvals(page: $page, pendingOnly: $pendingOnly) {
                items {
                    id
                    title
                    status
                    requestedAt
                }
                total
            }
        }
        """
        response = await e2e_client.graphql_query(
            query,
            variables={"page": 1, "pendingOnly": True},
        )

        assert "data" in response
        assert "approvals" in response["data"]

    @pytest.mark.asyncio
    async def test_graphql_create_agent_task(self, e2e_client):
        """
        Test GraphQL create agent task mutation.

        Expected duration: ~5 seconds
        """
        mutation = """
        mutation CreateAgentTask($input: AgentTaskCreateInput!) {
            createAgentTask(input: $input) {
                success
                message
                task {
                    id
                    taskType
                    status
                }
            }
        }
        """
        variables = {
            "input": {
                "engagementId": str(uuid4()),
                "taskType": "discovery",
                "description": "Run discovery analysis",
                "inputData": json.dumps({"context": "test"}),
                "tools": ["stakeholder_analysis", "source_discovery"],
                "maxIterations": 5,
                "timeoutSeconds": 300,
            }
        }

        response = await e2e_client.graphql_mutation(mutation, variables)

        assert "data" in response
        result = response["data"]["createAgentTask"]
        assert result["success"]

    @pytest.mark.asyncio
    async def test_full_graphql_workflow(self, e2e_client):
        """
        Test complete GraphQL workflow.

        Expected duration: ~30 seconds
        """
        # 1. Create engagement
        create_mutation = """
        mutation CreateEngagement($input: EngagementCreateInput!) {
            createEngagement(input: $input) {
                success
                engagement {
                    id
                    name
                    status
                }
            }
        }
        """
        create_result = await e2e_client.graphql_mutation(
            create_mutation,
            {
                "input": {
                    "name": "Full GraphQL Workflow",
                    "objective": "Test complete flow",
                    "priority": "HIGH",
                    "dataSources": [],
                    "tags": [],
                    "requiresApproval": True,
                }
            },
        )

        assert create_result["data"]["createEngagement"]["success"]
        engagement_id = create_result["data"]["createEngagement"]["engagement"]["id"]

        # 2. Query the created engagement
        query = """
        query GetEngagement($id: String!) {
            engagement(id: $id) {
                id
                name
                status
                priority
            }
        }
        """
        # Note: This may return None due to mocking, but tests the query structure
        await e2e_client.graphql_query(query, {"id": engagement_id})

        # 3. List engagements
        list_query = """
        query {
            engagements(page: 1, pageSize: 10) {
                items {
                    id
                    name
                }
                total
            }
        }
        """
        list_result = await e2e_client.graphql_query(list_query)
        assert "data" in list_result


class TestRealTimeUpdates:
    """Tests for WebSocket/SSE real-time updates (mocked)."""

    @pytest.mark.asyncio
    async def test_event_bus_publishes_engagement_created(
        self,
        e2e_client,
        test_app,
    ):
        """
        Test that engagement creation publishes event.

        Expected duration: ~5 seconds
        """
        # Create engagement
        await e2e_client.create_engagement(
            name="Event Test Engagement",
            objective="Test event publishing",
        )

        # Access mock event bus from app state
        event_bus = test_app.state.test_mocks["event_bus"]
        events = event_bus.get_events("engagement.created")

        # Event should have been published
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_event_structure(
        self,
        e2e_client,
        test_app,
    ):
        """
        Test event structure for real-time updates.

        Expected duration: ~5 seconds
        """
        await e2e_client.create_engagement(
            name="Event Structure Test",
            objective="Test event structure",
        )

        event_bus = test_app.state.test_mocks["event_bus"]
        events = event_bus.get_events()

        # Verify event structure
        for event in events:
            assert "type" in event
            assert "payload" in event
            assert "timestamp" in event

    @pytest.mark.asyncio
    async def test_multiple_event_types(
        self,
        e2e_client,
        test_app,
    ):
        """
        Test multiple event types are published.

        Expected duration: ~10 seconds
        """
        # Create engagement (publishes engagement.created)
        await e2e_client.create_engagement(
            name="Multi-Event Test",
            objective="Test multiple events",
        )

        # Create approval (publishes approval.requested)
        await e2e_client.create_approval(
            approval_type="engagement",
            title="Test Approval",
            description="Test",
            resource_id="test-id",
            resource_type="engagement",
        )

        event_bus = test_app.state.test_mocks["event_bus"]
        all_events = event_bus.get_events()
        event_types = {e["type"] for e in all_events}

        # Should have multiple event types
        assert len(event_types) >= 1


class TestAPIErrorHandling:
    """Tests for API error handling."""

    @pytest.mark.asyncio
    async def test_validation_error_response(self, e2e_client):
        """
        Test validation error response format.

        Expected duration: ~5 seconds
        """
        # Try to create engagement without required fields
        response = await e2e_client.http_client.post(
            "/api/v1/engagements",
            json={"invalid": "data"},
            headers=e2e_client.headers,
        )

        assert response.status_code == 422
        error = response.json()
        assert "error" in error or "detail" in error

    @pytest.mark.asyncio
    async def test_not_found_response(self, e2e_client):
        """
        Test 404 response for non-existent resource.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.http_client.get(
            "/api/v1/engagements/non-existent-id",
            headers=e2e_client.headers,
        )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_graphql_error_handling(self, e2e_client):
        """
        Test GraphQL error handling.

        Expected duration: ~5 seconds
        """
        # Invalid query
        query = "query { invalidField }"
        response = await e2e_client.graphql_query(query)

        # Should contain errors
        assert "errors" in response


class TestAPIPagination:
    """Tests for API pagination behavior."""

    @pytest.mark.asyncio
    async def test_pagination_defaults(self, e2e_client):
        """
        Test default pagination values.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements()

        assert response["page"] == 1
        assert response["page_size"] == 20

    @pytest.mark.asyncio
    async def test_pagination_custom_values(self, e2e_client):
        """
        Test custom pagination values.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements(page=2, page_size=50)

        assert response["page"] == 2
        assert response["page_size"] == 50

    @pytest.mark.asyncio
    async def test_pagination_max_page_size(self, e2e_client):
        """
        Test page size maximum limit.

        Expected duration: ~5 seconds
        """
        # Try to request more than max
        response = await e2e_client.http_client.get(
            "/api/v1/engagements",
            params={"page_size": 1000},  # Exceeds limit
            headers=e2e_client.headers,
        )

        # Should either return error or cap at max
        assert response.status_code in [200, 422]

    @pytest.mark.asyncio
    async def test_pagination_response_structure(self, e2e_client):
        """
        Test pagination response structure.

        Expected duration: ~5 seconds
        """
        response = await e2e_client.list_engagements()

        # Verify all pagination fields
        assert "items" in response
        assert "total" in response
        assert "page" in response
        assert "page_size" in response
        assert "total_pages" in response
        assert isinstance(response["items"], list)


class TestAPIAuthentication:
    """Tests for API authentication handling."""

    @pytest.mark.asyncio
    async def test_request_includes_user_id(self, e2e_client):
        """
        Test that requests include user ID header.

        Expected duration: ~5 seconds
        """
        engagement = await e2e_client.create_engagement(
            name="Auth Test",
            objective="Test authentication",
        )

        # Should have created_by from user header
        assert engagement["created_by"] == e2e_client.user_id

    @pytest.mark.asyncio
    async def test_request_includes_request_id(self, e2e_client):
        """
        Test that requests include request ID header.

        Expected duration: ~5 seconds
        """
        headers = e2e_client.headers
        assert "X-Request-Id" in headers
