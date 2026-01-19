"""
E2E Test Fixtures for Open Forge.

Provides fixtures for full stack testing including:
- Test application with mock dependencies
- API client for REST and GraphQL
- Mock LLM responses for deterministic testing
- Database and event bus mocking
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

# Import application modules
from api.main import create_app
from api.schemas.engagement import (
    EngagementCreate,
    EngagementStatus,
    EngagementPriority,
    DataSourceReference,
)
from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalType,
    ApprovalDecision,
)


# -----------------------------------------------------------------------------
# Mock LLM Infrastructure
# -----------------------------------------------------------------------------

@dataclass
class MockLLMResponse:
    """A single mock LLM response."""
    content: str
    usage: Dict[str, int] = field(default_factory=lambda: {"prompt_tokens": 100, "completion_tokens": 50})


class MockLLM:
    """
    Mock LLM that returns predetermined responses.

    Use for deterministic E2E testing without actual LLM calls.
    """

    def __init__(self, responses: Optional[List[str]] = None, response_map: Optional[Dict[str, str]] = None):
        """
        Initialize mock LLM.

        Args:
            responses: List of responses to return in order (round-robin).
            response_map: Dict mapping prompt keywords to specific responses.
        """
        self.responses = responses or ["Mock LLM response"]
        self.response_map = response_map or {}
        self.call_count = 0
        self.call_history: List[Dict[str, Any]] = []

    async def ainvoke(self, messages: Any) -> MockLLMResponse:
        """Async invoke that returns mock response."""
        # Extract the prompt content
        prompt_text = ""
        if isinstance(messages, list):
            for msg in messages:
                if hasattr(msg, 'content'):
                    prompt_text += msg.content + " "

        # Record call
        self.call_history.append({
            "prompt": prompt_text,
            "timestamp": datetime.utcnow().isoformat(),
            "call_number": self.call_count,
        })

        # Check response map for keyword match
        for keyword, response in self.response_map.items():
            if keyword.lower() in prompt_text.lower():
                self.call_count += 1
                return MockLLMResponse(content=response)

        # Return round-robin response
        response = self.responses[self.call_count % len(self.responses)]
        self.call_count += 1
        return MockLLMResponse(content=response)

    def invoke(self, messages: Any) -> MockLLMResponse:
        """Sync invoke that returns mock response."""
        return asyncio.get_event_loop().run_until_complete(self.ainvoke(messages))

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get history of all LLM calls."""
        return self.call_history

    def reset(self) -> None:
        """Reset call count and history."""
        self.call_count = 0
        self.call_history = []


# -----------------------------------------------------------------------------
# Mock Database and Storage
# -----------------------------------------------------------------------------

class MockDatabase:
    """In-memory database for E2E testing."""

    def __init__(self):
        self.engagements: Dict[str, Dict[str, Any]] = {}
        self.approvals: Dict[str, Dict[str, Any]] = {}
        self.agent_tasks: Dict[str, Dict[str, Any]] = {}
        self.data_sources: Dict[str, Dict[str, Any]] = {}
        self.phase_statuses: Dict[str, Dict[str, Any]] = {}

    async def save_engagement(self, engagement_id: str, data: Dict[str, Any]) -> None:
        """Save an engagement."""
        self.engagements[engagement_id] = {**data, "updated_at": datetime.utcnow().isoformat()}

    async def get_engagement(self, engagement_id: str) -> Optional[Dict[str, Any]]:
        """Get an engagement by ID."""
        return self.engagements.get(engagement_id)

    async def list_engagements(
        self,
        status: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict[str, Any]]:
        """List engagements with optional filtering."""
        items = list(self.engagements.values())
        if status:
            items = [e for e in items if e.get("status") == status]
        return items[offset:offset + limit]

    async def save_approval(self, approval_id: str, data: Dict[str, Any]) -> None:
        """Save an approval request."""
        self.approvals[approval_id] = {**data, "updated_at": datetime.utcnow().isoformat()}

    async def get_approval(self, approval_id: str) -> Optional[Dict[str, Any]]:
        """Get an approval by ID."""
        return self.approvals.get(approval_id)

    async def list_pending_approvals(self, engagement_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """List pending approval requests."""
        items = [
            a for a in self.approvals.values()
            if a.get("status") in [ApprovalStatus.PENDING.value, "pending"]
        ]
        if engagement_id:
            items = [a for a in items if a.get("engagement_id") == engagement_id]
        return items

    async def save_phase_status(self, engagement_id: str, phase: str, data: Dict[str, Any]) -> None:
        """Save phase status for an engagement."""
        if engagement_id not in self.phase_statuses:
            self.phase_statuses[engagement_id] = {}
        self.phase_statuses[engagement_id][phase] = data

    async def get_phase_status(self, engagement_id: str, phase: str) -> Optional[Dict[str, Any]]:
        """Get phase status."""
        return self.phase_statuses.get(engagement_id, {}).get(phase)

    def clear(self) -> None:
        """Clear all data."""
        self.engagements.clear()
        self.approvals.clear()
        self.agent_tasks.clear()
        self.data_sources.clear()
        self.phase_statuses.clear()


class MockEventBus:
    """Mock event bus for E2E testing."""

    def __init__(self):
        self.events: List[Dict[str, Any]] = []
        self.subscribers: Dict[str, List[callable]] = {}

    async def publish(self, event_type: str, payload: Dict[str, Any]) -> None:
        """Publish an event."""
        event = {
            "type": event_type,
            "payload": payload,
            "timestamp": datetime.utcnow().isoformat(),
        }
        self.events.append(event)

        # Notify subscribers
        for subscriber in self.subscribers.get(event_type, []):
            try:
                await subscriber(event)
            except Exception:
                pass  # Ignore subscriber errors in tests

    def subscribe(self, event_type: str, callback: callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.subscribers:
            self.subscribers[event_type] = []
        self.subscribers[event_type].append(callback)

    def get_events(self, event_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get recorded events, optionally filtered by type."""
        if event_type:
            return [e for e in self.events if e["type"] == event_type]
        return self.events

    def clear(self) -> None:
        """Clear all recorded events."""
        self.events.clear()


# -----------------------------------------------------------------------------
# Test Application Factory
# -----------------------------------------------------------------------------

@asynccontextmanager
async def create_test_app(
    mock_db: Optional[MockDatabase] = None,
    mock_event_bus: Optional[MockEventBus] = None,
    mock_llm: Optional[MockLLM] = None,
) -> AsyncGenerator[FastAPI, None]:
    """
    Create a test application with mock dependencies.

    Args:
        mock_db: Optional mock database instance.
        mock_event_bus: Optional mock event bus instance.
        mock_llm: Optional mock LLM instance.

    Yields:
        Configured FastAPI application.
    """
    # Create defaults if not provided
    mock_db = mock_db or MockDatabase()
    mock_event_bus = mock_event_bus or MockEventBus()
    mock_llm = mock_llm or MockLLM()

    # Store mocks for access in tests
    _test_mocks = {
        "db": mock_db,
        "event_bus": mock_event_bus,
        "llm": mock_llm,
    }

    # Patch dependencies
    with patch("api.dependencies.get_async_db", return_value=MagicMock()):
        with patch("api.dependencies.init_event_bus", return_value=mock_event_bus):
            with patch("api.dependencies.get_event_bus", return_value=mock_event_bus):
                with patch("core.database.connection.init_db", new_callable=AsyncMock):
                    with patch("core.database.connection.close_db", new_callable=AsyncMock):
                        app = create_app()

                        # Attach mocks to app state for test access
                        app.state.test_mocks = _test_mocks

                        yield app


# -----------------------------------------------------------------------------
# API Client Fixtures
# -----------------------------------------------------------------------------

@dataclass
class E2EClient:
    """E2E test client with REST and GraphQL support."""

    http_client: AsyncClient
    base_url: str = "http://test"
    user_id: str = "test-user-001"

    @property
    def headers(self) -> Dict[str, str]:
        """Get default headers."""
        return {
            "Content-Type": "application/json",
            "X-User-Id": self.user_id,
            "X-Request-Id": str(uuid4()),
        }

    # REST API Methods

    async def create_engagement(
        self,
        name: str,
        objective: str,
        description: Optional[str] = None,
        priority: str = "medium",
        data_sources: Optional[List[Dict[str, Any]]] = None,
        requires_approval: bool = True,
    ) -> Dict[str, Any]:
        """Create a new engagement via REST API."""
        payload = {
            "name": name,
            "objective": objective,
            "description": description,
            "priority": priority,
            "data_sources": data_sources or [],
            "requires_approval": requires_approval,
        }
        response = await self.http_client.post(
            "/api/v1/engagements",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    async def get_engagement(self, engagement_id: str) -> Dict[str, Any]:
        """Get engagement by ID."""
        response = await self.http_client.get(
            f"/api/v1/engagements/{engagement_id}",
            headers=self.headers,
        )
        return response.json()

    async def update_engagement_status(
        self,
        engagement_id: str,
        status: str,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update engagement status."""
        payload = {"status": status}
        if reason:
            payload["reason"] = reason
        response = await self.http_client.post(
            f"/api/v1/engagements/{engagement_id}/status",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    async def execute_engagement(self, engagement_id: str) -> Dict[str, Any]:
        """Execute an engagement."""
        response = await self.http_client.post(
            f"/api/v1/engagements/{engagement_id}/execute",
            headers=self.headers,
        )
        return response.json()

    async def list_engagements(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List engagements."""
        params = {"page": page, "page_size": page_size}
        if status:
            params["status"] = status
        response = await self.http_client.get(
            "/api/v1/engagements",
            params=params,
            headers=self.headers,
        )
        return response.json()

    # Approval API Methods

    async def create_approval(
        self,
        approval_type: str,
        title: str,
        description: str,
        resource_id: str,
        resource_type: str,
        expiration_hours: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Create an approval request."""
        payload = {
            "approval_type": approval_type,
            "title": title,
            "description": description,
            "resource_id": resource_id,
            "resource_type": resource_type,
        }
        if expiration_hours:
            payload["expiration_hours"] = expiration_hours
        response = await self.http_client.post(
            "/api/v1/approvals",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    async def get_approval(self, approval_id: str) -> Dict[str, Any]:
        """Get approval request by ID."""
        response = await self.http_client.get(
            f"/api/v1/approvals/{approval_id}",
            headers=self.headers,
        )
        return response.json()

    async def submit_approval_decision(
        self,
        approval_id: str,
        approved: bool,
        reason: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Submit a decision on an approval request."""
        payload = {"approved": approved}
        if reason:
            payload["reason"] = reason
        response = await self.http_client.post(
            f"/api/v1/approvals/{approval_id}/decide",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    async def list_approvals(
        self,
        pending_only: bool = False,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List approval requests."""
        params = {"page": page, "page_size": page_size, "pending_only": pending_only}
        response = await self.http_client.get(
            "/api/v1/approvals",
            params=params,
            headers=self.headers,
        )
        return response.json()

    # GraphQL Methods

    async def graphql_query(self, query: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL query."""
        payload = {"query": query}
        if variables:
            payload["variables"] = variables
        response = await self.http_client.post(
            "/graphql",
            json=payload,
            headers=self.headers,
        )
        return response.json()

    async def graphql_mutation(self, mutation: str, variables: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute a GraphQL mutation."""
        return await self.graphql_query(mutation, variables)


# -----------------------------------------------------------------------------
# Pytest Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def mock_llm_responses() -> Dict[str, str]:
    """
    Default mock LLM response mapping.

    Override this fixture to customize responses for specific tests.
    """
    return {
        # Discovery phase responses
        "stakeholder": json.dumps([
            {
                "name": "John Smith",
                "role": "Data Analyst",
                "department": "Analytics",
                "influence_level": "high",
                "data_needs": ["Sales data", "Customer data"],
            }
        ]),
        "discover": json.dumps([
            {
                "name": "Sales Database",
                "source_type": "database",
                "technology": "PostgreSQL",
                "description": "Primary sales transaction database",
            }
        ]),
        "requirements": json.dumps({
            "explicit_requirements": ["Real-time reporting", "Data quality checks"],
            "implicit_requirements": ["Access control", "Audit logging"],
        }),
        # Design phase responses
        "ontology": json.dumps({
            "entities": [
                {"name": "Customer", "attributes": ["id", "name", "email"]},
                {"name": "Order", "attributes": ["id", "customer_id", "total"]},
            ],
            "relationships": [
                {"from": "Order", "to": "Customer", "type": "belongs_to"},
            ],
        }),
        "schema": json.dumps({
            "valid": True,
            "entities": ["Customer", "Order"],
            "warnings": [],
        }),
        "transformation": json.dumps({
            "transformations": [
                {"source": "raw_sales", "target": "sales_fact", "type": "aggregate"},
            ],
        }),
        # Build phase responses
        "ui": json.dumps({
            "components": [
                {"name": "CustomerForm", "type": "form", "entity": "Customer"},
                {"name": "OrderTable", "type": "table", "entity": "Order"},
            ],
        }),
        "workflow": json.dumps({
            "workflows": [
                {"name": "order_processing", "steps": ["validate", "process", "notify"]},
            ],
        }),
    }


@pytest.fixture
def mock_llm(mock_llm_responses) -> MockLLM:
    """Create a mock LLM with default responses."""
    return MockLLM(response_map=mock_llm_responses)


@pytest.fixture
def mock_db() -> MockDatabase:
    """Create a mock database."""
    db = MockDatabase()
    yield db
    db.clear()


@pytest.fixture
def mock_event_bus() -> MockEventBus:
    """Create a mock event bus."""
    bus = MockEventBus()
    yield bus
    bus.clear()


@pytest.fixture
async def test_app(mock_db, mock_event_bus, mock_llm) -> AsyncGenerator[FastAPI, None]:
    """Create a test application with all mocks."""
    async with create_test_app(mock_db, mock_event_bus, mock_llm) as app:
        yield app


@pytest.fixture
async def e2e_client(test_app) -> AsyncGenerator[E2EClient, None]:
    """Create an E2E test client."""
    transport = ASGITransport(app=test_app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield E2EClient(http_client=client)


@pytest.fixture
def sync_client(test_app) -> TestClient:
    """Create a synchronous test client (for simpler tests)."""
    return TestClient(test_app)


@pytest.fixture
def phase_manager() -> PhaseManager:
    """Create a phase manager for testing phase transitions."""
    return PhaseManager(engagement_id="test-engagement")


@pytest.fixture
def approval_manager(mock_event_bus) -> ApprovalManager:
    """Create an approval manager for testing approvals."""
    return ApprovalManager(event_bus=mock_event_bus)


# -----------------------------------------------------------------------------
# Sample Data Fixtures
# -----------------------------------------------------------------------------

@pytest.fixture
def sample_engagement_data() -> Dict[str, Any]:
    """Sample engagement data for testing."""
    return {
        "name": "CRM Analytics Platform",
        "description": "Build analytics platform for customer relationship data",
        "objective": "Create a unified view of customer interactions with real-time dashboards",
        "priority": "high",
        "data_sources": [
            {
                "source_id": "salesforce-001",
                "source_type": "saas_application",
                "access_mode": "read",
            },
            {
                "source_id": "postgres-crm",
                "source_type": "database",
                "access_mode": "read",
            },
        ],
        "requires_approval": True,
        "tags": ["crm", "analytics", "customer-360"],
        "metadata": {
            "department": "Sales",
            "budget": "50000",
            "sponsor": "VP of Sales",
        },
    }


@pytest.fixture
def sample_ontology_data() -> Dict[str, Any]:
    """Sample ontology data for testing."""
    return {
        "name": "CRM Ontology",
        "version": "1.0.0",
        "entities": [
            {
                "name": "Customer",
                "description": "A customer entity",
                "attributes": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "name", "type": "string", "required": True},
                    {"name": "email", "type": "string", "required": True},
                    {"name": "created_at", "type": "datetime", "required": True},
                ],
            },
            {
                "name": "Contact",
                "description": "A contact interaction",
                "attributes": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "customer_id", "type": "string", "required": True},
                    {"name": "type", "type": "enum", "values": ["call", "email", "meeting"]},
                    {"name": "notes", "type": "text"},
                    {"name": "contacted_at", "type": "datetime", "required": True},
                ],
            },
            {
                "name": "Opportunity",
                "description": "A sales opportunity",
                "attributes": [
                    {"name": "id", "type": "string", "required": True},
                    {"name": "customer_id", "type": "string", "required": True},
                    {"name": "value", "type": "decimal", "required": True},
                    {"name": "stage", "type": "enum", "values": ["lead", "qualified", "proposal", "closed"]},
                    {"name": "close_date", "type": "date"},
                ],
            },
        ],
        "relationships": [
            {
                "name": "customer_contacts",
                "from_entity": "Customer",
                "to_entity": "Contact",
                "type": "one_to_many",
            },
            {
                "name": "customer_opportunities",
                "from_entity": "Customer",
                "to_entity": "Opportunity",
                "type": "one_to_many",
            },
        ],
    }


@pytest.fixture
def sample_data_source_config() -> Dict[str, Any]:
    """Sample data source configuration for testing."""
    return {
        "id": "postgres-crm",
        "name": "CRM PostgreSQL Database",
        "type": "database",
        "technology": "postgresql",
        "connection": {
            "host": "localhost",
            "port": 5432,
            "database": "crm_db",
            "schema": "public",
        },
        "tables": [
            {"name": "customers", "estimated_rows": 50000},
            {"name": "contacts", "estimated_rows": 200000},
            {"name": "opportunities", "estimated_rows": 75000},
        ],
        "refresh_schedule": "0 * * * *",  # Hourly
    }


# -----------------------------------------------------------------------------
# Test Environment Setup
# -----------------------------------------------------------------------------

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
def setup_test_environment(monkeypatch):
    """Set up test environment variables."""
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE__HOST", "localhost")
    monkeypatch.setenv("DATABASE__PORT", "5432")
    monkeypatch.setenv("DATABASE__NAME", "test_db")
    monkeypatch.setenv("DATABASE__USER", "test_user")
    monkeypatch.setenv("DATABASE__PASSWORD", "test_pass")
    monkeypatch.setenv("LLM__PROVIDER", "mock")
    monkeypatch.setenv("LLM__MODEL", "mock-model")
    monkeypatch.setenv("LLM__API_KEY", "test-api-key")
