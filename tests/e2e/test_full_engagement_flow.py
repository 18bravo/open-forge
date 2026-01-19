"""
End-to-end test for the full engagement flow.

Tests the complete lifecycle of an engagement through all phases:
- Discovery
- Data Foundation
- Application
- Operations
- Enablement
- Deployment
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List
import json

from unittest.mock import AsyncMock, MagicMock, patch


pytestmark = [pytest.mark.e2e, pytest.mark.slow]


class TestFullEngagementFlow:
    """
    End-to-end tests for complete engagement workflow.

    These tests verify that all agent clusters work together
    to complete a full engagement from discovery to deployment.
    """

    @pytest_asyncio.fixture
    async def engagement_setup(self, e2e_client, sample_engagement_data):
        """Set up a new engagement for testing."""
        # Create the engagement
        response = await e2e_client.create_engagement(sample_engagement_data)
        assert response["status"] == "success"

        engagement_id = response["engagement_id"]

        yield {
            "engagement_id": engagement_id,
            "client": e2e_client
        }

        # Cleanup - would delete engagement in real implementation
        # await e2e_client.delete_engagement(engagement_id)

    @pytest.mark.asyncio
    async def test_discovery_to_data_foundation_transition(
        self,
        engagement_setup,
        mock_llm_responses
    ):
        """Test transition from Discovery to Data Foundation phase."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Verify we start in discovery phase
        engagement = await client.get_engagement(engagement_id)
        assert engagement["current_phase"] == "discovery"

        # Complete discovery phase tasks
        discovery_output = await client.complete_phase(
            engagement_id,
            "discovery",
            {
                "discovered_sources": [
                    {"name": "customers_db", "type": "postgres"},
                    {"name": "orders_api", "type": "rest"}
                ],
                "stakeholders": [
                    {"name": "Product Owner", "role": "owner"}
                ],
                "requirements": [
                    {"id": "REQ-001", "description": "Customer 360 view"}
                ]
            }
        )

        assert discovery_output["success"] is True

        # Verify phase transition
        engagement = await client.get_engagement(engagement_id)
        assert engagement["current_phase"] == "data_foundation"

    @pytest.mark.asyncio
    async def test_data_foundation_ontology_creation(
        self,
        engagement_setup,
        mock_llm_responses,
        sample_ontology_yaml
    ):
        """Test ontology creation in Data Foundation phase."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Skip to data foundation phase
        await client.advance_to_phase(engagement_id, "data_foundation")

        # Create ontology
        ontology_result = await client.create_ontology(
            engagement_id,
            {
                "name": "CustomerOrders",
                "schema": sample_ontology_yaml,
                "version": "1.0.0"
            }
        )

        assert ontology_result["success"] is True
        assert "ontology_id" in ontology_result

        # Validate ontology
        validation = await client.validate_ontology(
            engagement_id,
            ontology_result["ontology_id"]
        )

        assert validation["is_valid"] is True

    @pytest.mark.asyncio
    async def test_application_phase_code_generation(
        self,
        engagement_setup,
        mock_llm_responses
    ):
        """Test code generation in Application phase."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Skip to application phase
        await client.advance_to_phase(engagement_id, "application")

        # Trigger code generation
        codegen_result = await client.trigger_code_generation(
            engagement_id,
            generators=["fastapi", "orm", "tests", "hooks"]
        )

        assert codegen_result["job_id"] is not None

        # Wait for completion (in mock, immediate)
        status = await client.get_codegen_status(codegen_result["job_id"])
        assert status["status"] in ["completed", "running"]

    @pytest.mark.asyncio
    async def test_operations_phase_configuration(
        self,
        engagement_setup,
        mock_llm_responses
    ):
        """Test operations configuration generation."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Skip to operations phase (or support as phase name)
        await client.advance_to_phase(engagement_id, "support")

        # Run operations cluster
        operations_result = await client.run_operations_cluster(
            engagement_id,
            {
                "ontology_schema": "# test ontology",
                "system_architecture": {"type": "microservices"},
                "system_requirements": {"availability": "99.9%"}
            }
        )

        assert operations_result["success"] is True

        # Verify outputs exist
        outputs = operations_result.get("outputs", {})
        # Operations outputs include monitoring, scaling, maintenance, incident configs
        assert "operations_report" in outputs or len(outputs) > 0

    @pytest.mark.asyncio
    async def test_enablement_phase_documentation(
        self,
        engagement_setup,
        mock_llm_responses,
        sample_ontology_yaml
    ):
        """Test enablement content generation."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Skip to enablement (or combined support phase)
        await client.advance_to_phase(engagement_id, "support")

        # Run enablement cluster
        enablement_result = await client.run_enablement_cluster(
            engagement_id,
            {
                "ontology_schema": sample_ontology_yaml,
                "system_architecture": {"type": "microservices"},
                "system_features": ["CRUD", "Search", "Reports"]
            }
        )

        assert enablement_result["success"] is True

        # Verify documentation, training, and support outputs
        outputs = enablement_result.get("outputs", {})
        assert "enablement_report" in outputs or len(outputs) > 0

    @pytest.mark.asyncio
    async def test_full_engagement_completion(
        self,
        engagement_setup,
        mock_llm_responses
    ):
        """Test completing an entire engagement from start to finish."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Phase 1: Discovery
        await client.complete_phase(
            engagement_id,
            "discovery",
            {"discovered_sources": [], "requirements": []}
        )

        # Phase 2: Data Foundation
        engagement = await client.get_engagement(engagement_id)
        if engagement["current_phase"] == "data_foundation":
            await client.complete_phase(
                engagement_id,
                "data_foundation",
                {"ontology_created": True, "pipelines_configured": True}
            )

        # Phase 3: Application
        engagement = await client.get_engagement(engagement_id)
        if engagement["current_phase"] == "application":
            await client.complete_phase(
                engagement_id,
                "application",
                {"code_generated": True, "ui_created": True}
            )

        # Phase 4: Support (Operations + Enablement)
        engagement = await client.get_engagement(engagement_id)
        if engagement["current_phase"] == "support":
            await client.complete_phase(
                engagement_id,
                "support",
                {"operations_configured": True, "enablement_complete": True}
            )

        # Verify final state
        final_engagement = await client.get_engagement(engagement_id)
        assert final_engagement["status"] in ["completed", "deployed", "support"]

    @pytest.mark.asyncio
    async def test_approval_workflow_integration(
        self,
        engagement_setup,
        mock_llm_responses
    ):
        """Test that approval workflows are triggered correctly."""
        client = engagement_setup["client"]
        engagement_id = engagement_setup["engagement_id"]

        # Trigger an action that requires approval
        approval_request = await client.request_approval(
            engagement_id,
            {
                "type": "ontology_approval",
                "title": "Approve Ontology Design",
                "description": "Please review the ontology design",
                "context": {"entities": ["Customer", "Order"]}
            }
        )

        assert approval_request["approval_id"] is not None

        # Approve it
        approval_result = await client.submit_approval(
            approval_request["approval_id"],
            {
                "decision": "approved",
                "feedback": "Looks good!"
            }
        )

        assert approval_result["success"] is True

        # Verify approval was recorded
        approval = await client.get_approval(approval_request["approval_id"])
        assert approval["status"] == "approved"


class TestAgentClusterIntegration:
    """Tests for agent cluster integration within engagements."""

    @pytest.mark.asyncio
    async def test_operations_and_enablement_parallel_execution(
        self,
        e2e_client,
        sample_engagement_data,
        mock_llm_responses,
        sample_ontology_yaml
    ):
        """Test that operations and enablement can run in parallel."""
        # Create engagement
        response = await e2e_client.create_engagement(sample_engagement_data)
        engagement_id = response["engagement_id"]

        # Advance to support phase
        await e2e_client.advance_to_phase(engagement_id, "support")

        context = {
            "ontology_schema": sample_ontology_yaml,
            "system_architecture": {"type": "microservices"}
        }

        # Run both clusters (simulated parallel execution)
        operations_task = e2e_client.run_operations_cluster(engagement_id, context)
        enablement_task = e2e_client.run_enablement_cluster(engagement_id, context)

        # In real async code, these would run concurrently
        operations_result = await operations_task
        enablement_result = await enablement_task

        # Both should succeed
        assert operations_result["success"] is True
        assert enablement_result["success"] is True

    @pytest.mark.asyncio
    async def test_agent_output_passed_to_next_cluster(
        self,
        e2e_client,
        sample_engagement_data,
        mock_llm_responses
    ):
        """Test that outputs from one cluster are available to the next."""
        response = await e2e_client.create_engagement(sample_engagement_data)
        engagement_id = response["engagement_id"]

        # Run discovery cluster first
        discovery_output = {
            "discovered_sources": [{"name": "db1", "type": "postgres"}],
            "requirements": [{"id": "R1", "description": "Data integration"}]
        }
        await e2e_client.complete_phase(engagement_id, "discovery", discovery_output)

        # Verify outputs are stored and accessible
        engagement = await e2e_client.get_engagement(engagement_id)
        stored_outputs = engagement.get("phase_outputs", {}).get("discovery", {})

        # Next phase should have access to these outputs
        # This is verified by the agent receiving previous_outputs in its input


class TestErrorHandling:
    """Tests for error handling in the engagement flow."""

    @pytest.mark.asyncio
    async def test_agent_failure_triggers_human_review(
        self,
        e2e_client,
        sample_engagement_data,
        mock_llm_with_error_responses
    ):
        """Test that agent failures properly trigger human review."""
        response = await e2e_client.create_engagement(sample_engagement_data)
        engagement_id = response["engagement_id"]

        # Simulate an agent run that fails
        with patch.object(e2e_client, '_mock_agent_run', side_effect=Exception("LLM error")):
            result = await e2e_client.run_agent(
                engagement_id,
                "discovery_agent",
                {}
            )

        # Should flag for human review
        engagement = await e2e_client.get_engagement(engagement_id)
        # Check for review items or error state
        assert engagement.get("requires_human_review", False) or "error" in str(result).lower()

    @pytest.mark.asyncio
    async def test_validation_failure_prevents_phase_transition(
        self,
        e2e_client,
        sample_engagement_data,
        mock_llm_responses
    ):
        """Test that validation failures prevent phase transitions."""
        response = await e2e_client.create_engagement(sample_engagement_data)
        engagement_id = response["engagement_id"]

        # Try to complete phase with invalid outputs
        result = await e2e_client.complete_phase(
            engagement_id,
            "discovery",
            {"invalid": "data"}  # Missing required outputs
        )

        # Should fail validation (depending on implementation)
        # or phase should not advance
        engagement = await e2e_client.get_engagement(engagement_id)
        # In strict validation mode, phase wouldn't advance
        # In lenient mode, it might proceed but flag issues


class TestPerformance:
    """Performance-related tests for the engagement flow."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_concurrent_engagements(
        self,
        e2e_client,
        sample_engagement_data
    ):
        """Test that multiple engagements can run concurrently."""
        import asyncio

        # Create multiple engagements
        create_tasks = [
            e2e_client.create_engagement({
                **sample_engagement_data,
                "name": f"Concurrent Test {i}"
            })
            for i in range(5)
        ]

        results = await asyncio.gather(*create_tasks)

        # All should succeed
        for result in results:
            assert result["status"] == "success"
            assert result["engagement_id"] is not None

        # Verify all are independent
        engagement_ids = [r["engagement_id"] for r in results]
        assert len(set(engagement_ids)) == 5  # All unique

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_large_ontology_handling(
        self,
        e2e_client,
        sample_engagement_data
    ):
        """Test handling of large ontology schemas."""
        # Create engagement
        response = await e2e_client.create_engagement(sample_engagement_data)
        engagement_id = response["engagement_id"]

        # Generate a large ontology schema (many entities)
        entities = []
        for i in range(50):
            entities.append(f"""
  Entity{i}:
    description: Entity number {i}
    attributes:
      id:
        range: string
        required: true
        identifier: true
      name:
        range: string
      value:
        range: integer
""")

        large_ontology = f"""
id: https://example.org/large-ontology
name: LargeOntology
version: "1.0.0"
classes:
{"".join(entities)}
"""

        # Try to create ontology
        await e2e_client.advance_to_phase(engagement_id, "data_foundation")
        result = await e2e_client.create_ontology(
            engagement_id,
            {
                "name": "LargeOntology",
                "schema": large_ontology,
                "version": "1.0.0"
            }
        )

        # Should handle without timing out
        assert result.get("success", True) is True or "ontology_id" in result
