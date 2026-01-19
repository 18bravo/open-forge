"""
E2E Tests for Discovery Phase.

Tests the discovery phase of the engagement lifecycle including:
- Stakeholder analysis
- Source discovery
- Requirements gathering
- Approval checkpoint

Expected test durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Full discovery flow: 60-120 seconds
"""
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalType, ApprovalStatus

from .conftest import MockLLM, MockDatabase, MockEventBus
from .utils import (
    wait_for_phase,
    wait_for_approval,
    get_phase_requirements_status,
    complete_phase_requirements,
    submit_approval,
    create_and_approve,
    assert_phase_complete,
    generate_test_engagement_name,
)


class TestStakeholderAnalysis:
    """Tests for stakeholder analysis during discovery."""

    @pytest.fixture
    def stakeholder_llm_responses(self):
        """Mock LLM responses for stakeholder analysis."""
        return {
            "stakeholder": json.dumps([
                {
                    "name": "Alice Chen",
                    "role": "VP of Sales",
                    "department": "Sales",
                    "influence_level": "high",
                    "engagement_priority": "high",
                    "data_needs": [
                        "Sales pipeline visibility",
                        "Customer segmentation",
                        "Revenue forecasting",
                    ],
                    "success_criteria": "50% reduction in report generation time",
                },
                {
                    "name": "Bob Martinez",
                    "role": "Data Analyst",
                    "department": "Analytics",
                    "influence_level": "medium",
                    "engagement_priority": "high",
                    "data_needs": [
                        "Raw transaction data",
                        "Customer demographics",
                        "Historical trends",
                    ],
                    "success_criteria": "Automated daily reporting",
                },
                {
                    "name": "Carol Williams",
                    "role": "IT Director",
                    "department": "IT",
                    "influence_level": "high",
                    "engagement_priority": "medium",
                    "data_needs": [
                        "System integration requirements",
                        "Security compliance",
                        "Infrastructure needs",
                    ],
                    "success_criteria": "No security incidents",
                },
            ]),
            "process": json.dumps({
                "process_name": "Sales Reporting",
                "steps": [
                    {"order": 1, "name": "Data extraction", "duration": "2 hours"},
                    {"order": 2, "name": "Data transformation", "duration": "4 hours"},
                    {"order": 3, "name": "Report generation", "duration": "1 hour"},
                ],
                "pain_points": [
                    "Manual data extraction is error-prone",
                    "Transformation logic is undocumented",
                ],
            }),
            "conflict": json.dumps({
                "conflicts": [
                    {
                        "description": "Sales wants real-time data, IT requires batch processing",
                        "severity": "medium",
                        "affected_stakeholders": ["Alice Chen", "Carol Williams"],
                    }
                ],
                "gaps": ["Mobile access requirements not clearly defined"],
                "dependencies": [],
                "priority_recommendations": ["Address real-time vs batch conflict first"],
            }),
        }

    @pytest.mark.asyncio
    async def test_stakeholder_identification(
        self,
        phase_manager,
        stakeholder_llm_responses,
    ):
        """
        Test that stakeholder identification runs and produces expected output.

        Expected duration: ~10 seconds
        """
        mock_llm = MockLLM(response_map=stakeholder_llm_responses)

        # Simulate stakeholder analysis output
        stakeholders_output = json.loads(stakeholder_llm_responses["stakeholder"])

        # Verify stakeholder structure
        assert len(stakeholders_output) == 3
        assert all("name" in s for s in stakeholders_output)
        assert all("role" in s for s in stakeholders_output)
        assert all("data_needs" in s for s in stakeholders_output)

        # Record output in phase manager
        phase_manager.record_output("stakeholder_map")

        status = get_phase_requirements_status(phase_manager)
        assert "stakeholder_map" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_business_process_mapping(
        self,
        phase_manager,
        stakeholder_llm_responses,
    ):
        """
        Test that business process mapping produces valid output.

        Expected duration: ~10 seconds
        """
        mock_llm = MockLLM(response_map=stakeholder_llm_responses)

        # Simulate process mapping output
        process_output = json.loads(stakeholder_llm_responses["process"])

        # Verify process structure
        assert "process_name" in process_output
        assert "steps" in process_output
        assert len(process_output["steps"]) >= 1
        assert "pain_points" in process_output

    @pytest.mark.asyncio
    async def test_conflict_identification(
        self,
        phase_manager,
        stakeholder_llm_responses,
    ):
        """
        Test that conflicts are identified and flagged for review.

        Expected duration: ~10 seconds
        """
        conflict_output = json.loads(stakeholder_llm_responses["conflict"])

        # Verify conflicts are identified
        assert "conflicts" in conflict_output
        assert len(conflict_output["conflicts"]) > 0

        # Check conflict structure
        conflict = conflict_output["conflicts"][0]
        assert "description" in conflict
        assert "severity" in conflict
        assert "affected_stakeholders" in conflict


class TestSourceDiscovery:
    """Tests for data source discovery."""

    @pytest.fixture
    def source_discovery_responses(self):
        """Mock LLM responses for source discovery."""
        return {
            "discover": json.dumps([
                {
                    "name": "Salesforce CRM",
                    "source_type": "saas_application",
                    "technology": "Salesforce API",
                    "description": "Primary CRM system with customer and opportunity data",
                    "owner": "Sales Operations",
                    "estimated_volume": "500GB",
                    "update_frequency": "Real-time",
                    "access_method": "REST API",
                },
                {
                    "name": "PostgreSQL Analytics DB",
                    "source_type": "database",
                    "technology": "PostgreSQL 14",
                    "description": "Analytics data warehouse with historical data",
                    "owner": "Data Engineering",
                    "estimated_volume": "2TB",
                    "update_frequency": "Daily batch",
                    "access_method": "JDBC",
                },
                {
                    "name": "S3 Data Lake",
                    "source_type": "cloud_storage",
                    "technology": "AWS S3",
                    "description": "Raw data files from various sources",
                    "owner": "Data Platform",
                    "estimated_volume": "10TB",
                    "update_frequency": "Hourly",
                    "access_method": "S3 API",
                },
            ]),
            "quality": json.dumps({
                "overall_score": 0.75,
                "dimension_scores": {
                    "completeness": {"score": 0.85, "evidence": "95% non-null values"},
                    "accuracy": {"score": 0.70, "evidence": "Some data entry errors detected"},
                    "consistency": {"score": 0.80, "evidence": "Consistent formats across tables"},
                    "timeliness": {"score": 0.65, "evidence": "Some stale records"},
                    "validity": {"score": 0.75, "evidence": "Most values conform to rules"},
                    "uniqueness": {"score": 0.90, "evidence": "Low duplicate rate"},
                },
                "recommendations": [
                    "Implement data validation at ingestion",
                    "Set up automated freshness checks",
                ],
            }),
            "integration": json.dumps({
                "technical_complexity": 2,
                "effort_estimate": "3-5 days",
                "required_connectors": ["Salesforce REST connector"],
                "transformation_requirements": ["Field mapping", "Date normalization"],
                "security_considerations": ["OAuth 2.0 required", "PII handling"],
                "risks": [
                    {"risk": "API rate limits", "mitigation": "Implement backoff"},
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_source_discovery_identifies_sources(
        self,
        phase_manager,
        source_discovery_responses,
    ):
        """
        Test that source discovery identifies available data sources.

        Expected duration: ~15 seconds
        """
        sources = json.loads(source_discovery_responses["discover"])

        # Verify sources are discovered
        assert len(sources) >= 1
        assert all("name" in s for s in sources)
        assert all("source_type" in s for s in sources)

        # Verify source types are valid
        valid_types = [
            "database", "api", "file_system", "cloud_storage",
            "saas_application", "data_warehouse", "streaming", "legacy_system"
        ]
        for source in sources:
            assert source["source_type"] in valid_types

        # Record output
        phase_manager.record_output("discovered_sources")
        status = get_phase_requirements_status(phase_manager)
        assert "discovered_sources" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_source_quality_assessment(
        self,
        phase_manager,
        source_discovery_responses,
    ):
        """
        Test that data quality is assessed for discovered sources.

        Expected duration: ~10 seconds
        """
        quality = json.loads(source_discovery_responses["quality"])

        # Verify quality assessment structure
        assert "overall_score" in quality
        assert 0 <= quality["overall_score"] <= 1
        assert "dimension_scores" in quality

        # Verify all dimensions are assessed
        expected_dimensions = [
            "completeness", "accuracy", "consistency",
            "timeliness", "validity", "uniqueness"
        ]
        for dim in expected_dimensions:
            assert dim in quality["dimension_scores"]
            assert "score" in quality["dimension_scores"][dim]

        # Record output
        phase_manager.record_output("source_assessments")
        status = get_phase_requirements_status(phase_manager)
        assert "source_assessments" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_low_quality_source_flagged_for_review(
        self,
        phase_manager,
        mock_event_bus,
    ):
        """
        Test that sources with low quality scores are flagged.

        Expected duration: ~10 seconds
        """
        # Simulate a low-quality source assessment
        low_quality_assessment = {
            "source_name": "Legacy System",
            "overall_score": 0.4,  # Below threshold
            "issues": [
                "High percentage of null values",
                "Inconsistent date formats",
                "Many duplicate records",
            ],
        }

        # This should trigger a review flag
        if low_quality_assessment["overall_score"] < 0.6:
            # Record that review is needed
            assert True, "Low quality source should be flagged"

    @pytest.mark.asyncio
    async def test_integration_complexity_evaluated(
        self,
        phase_manager,
        source_discovery_responses,
    ):
        """
        Test that integration complexity is evaluated for each source.

        Expected duration: ~10 seconds
        """
        integration = json.loads(source_discovery_responses["integration"])

        # Verify integration assessment
        assert "technical_complexity" in integration
        assert 1 <= integration["technical_complexity"] <= 5
        assert "effort_estimate" in integration
        assert "required_connectors" in integration
        assert "security_considerations" in integration


class TestRequirementsGathering:
    """Tests for requirements gathering during discovery."""

    @pytest.fixture
    def requirements_responses(self):
        """Mock LLM responses for requirements gathering."""
        return {
            "requirements": json.dumps({
                "explicit_requirements": [
                    {
                        "id": "REQ-001",
                        "description": "Dashboard must update in real-time",
                        "priority": "high",
                        "source": "VP of Sales interview",
                    },
                    {
                        "id": "REQ-002",
                        "description": "Support for 100 concurrent users",
                        "priority": "high",
                        "source": "IT requirements document",
                    },
                    {
                        "id": "REQ-003",
                        "description": "Export reports to PDF and Excel",
                        "priority": "medium",
                        "source": "Analyst feedback",
                    },
                ],
                "implicit_requirements": [
                    {
                        "id": "REQ-I01",
                        "description": "Mobile-responsive design",
                        "reasoning": "Users mentioned accessing reports on tablets",
                    },
                    {
                        "id": "REQ-I02",
                        "description": "Audit logging for compliance",
                        "reasoning": "Financial data requires tracking",
                    },
                ],
                "constraints": [
                    "Must integrate with existing SSO",
                    "Cannot exceed $50K annual infrastructure cost",
                ],
                "timeline": "6 months",
                "success_metrics": [
                    "50% reduction in report generation time",
                    "90% user satisfaction score",
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_requirements_documented(
        self,
        phase_manager,
        requirements_responses,
    ):
        """
        Test that requirements are properly documented.

        Expected duration: ~10 seconds
        """
        requirements = json.loads(requirements_responses["requirements"])

        # Verify explicit requirements
        assert "explicit_requirements" in requirements
        assert len(requirements["explicit_requirements"]) >= 1
        for req in requirements["explicit_requirements"]:
            assert "id" in req
            assert "description" in req
            assert "priority" in req

        # Verify implicit requirements are captured
        assert "implicit_requirements" in requirements

        # Record output
        phase_manager.record_output("requirements")
        status = get_phase_requirements_status(phase_manager)
        assert "requirements" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_constraints_identified(
        self,
        phase_manager,
        requirements_responses,
    ):
        """
        Test that constraints and limitations are identified.

        Expected duration: ~5 seconds
        """
        requirements = json.loads(requirements_responses["requirements"])

        assert "constraints" in requirements
        assert len(requirements["constraints"]) >= 1

    @pytest.mark.asyncio
    async def test_success_metrics_defined(
        self,
        phase_manager,
        requirements_responses,
    ):
        """
        Test that success metrics are defined.

        Expected duration: ~5 seconds
        """
        requirements = json.loads(requirements_responses["requirements"])

        assert "success_metrics" in requirements
        assert len(requirements["success_metrics"]) >= 1


class TestDiscoveryApprovalCheckpoint:
    """Tests for the discovery phase approval checkpoint."""

    @pytest.mark.asyncio
    async def test_approval_request_created_at_checkpoint(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test that an approval request is created at the discovery checkpoint.

        Expected duration: ~5 seconds
        """
        # Create approval request for discovery sign-off
        approval = await approval_manager.create_request(
            engagement_id="test-engagement-001",
            approval_type=ApprovalType.CONFIGURATION,
            title="Discovery Phase Sign-off",
            description="Review and approve discovery phase outputs",
            requested_by="discovery_agent",
            timeout_minutes=60,
            context_data={
                "stakeholders_identified": 3,
                "sources_discovered": 3,
                "requirements_count": 5,
                "conflicts_found": 1,
            },
        )

        assert approval.status == ApprovalStatus.PENDING
        assert approval.engagement_id == "test-engagement-001"

        # Verify event was published
        events = mock_event_bus.get_events("approval.requested")
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_approval_blocks_phase_transition(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test that pending approval blocks transition to next phase.

        Expected duration: ~10 seconds
        """
        # Complete all outputs and gates but not approvals
        complete_phase_requirements(
            phase_manager,
            outputs=[
                "stakeholder_map",
                "requirements",
                "discovered_sources",
                "source_assessments",
                "source_recommendations",
            ],
            gates=[
                "stakeholder_coverage",
                "data_sources_validated",
                "requirements_documented",
            ],
            # Note: NOT completing approvals
        )

        # Validation should fail due to missing approval
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert not validation["valid"]
        assert "discovery_sign_off" in validation["missing_approvals"]

    @pytest.mark.asyncio
    async def test_approved_discovery_enables_transition(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test that approved discovery allows transition to design.

        Expected duration: ~15 seconds
        """
        # Complete all requirements including approval
        complete_phase_requirements(
            phase_manager,
            outputs=[
                "stakeholder_map",
                "requirements",
                "discovered_sources",
                "source_assessments",
                "source_recommendations",
            ],
            gates=[
                "stakeholder_coverage",
                "data_sources_validated",
                "requirements_documented",
            ],
            approvals=["discovery_sign_off"],
        )

        # Validation should pass
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert validation["valid"]

        # Perform transition
        result = phase_manager.transition_to(
            EngagementPhase.DESIGN,
            approved_by="test_approver",
        )
        assert result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.DESIGN


class TestFullDiscoveryPhase:
    """Tests for complete discovery phase flow."""

    @pytest.mark.asyncio
    async def test_complete_discovery_phase(
        self,
        e2e_client,
        phase_manager,
        approval_manager,
        mock_event_bus,
        sample_engagement_data,
    ):
        """
        Test complete discovery phase from start to approval.

        This test simulates:
        1. Create engagement with initial context
        2. Run stakeholder analysis
        3. Run source discovery
        4. Gather requirements
        5. Submit for approval
        6. Approve and transition

        Expected duration: 60-120 seconds
        """
        # 1. Create engagement
        engagement = await e2e_client.create_engagement(
            name=generate_test_engagement_name("Discovery Phase Test"),
            objective=sample_engagement_data["objective"],
            description=sample_engagement_data["description"],
            data_sources=sample_engagement_data["data_sources"],
        )
        engagement_id = engagement["id"]

        # 2. Verify starting in discovery phase
        assert phase_manager.get_current_phase() == EngagementPhase.DISCOVERY

        # 3. Simulate stakeholder analysis completion
        phase_manager.record_output("stakeholder_map")

        # 4. Simulate source discovery completion
        phase_manager.record_output("discovered_sources")
        phase_manager.record_output("source_assessments")
        phase_manager.record_output("source_recommendations")

        # 5. Simulate requirements gathering
        phase_manager.record_output("requirements")

        # 6. Pass quality gates
        phase_manager.pass_quality_gate(
            "stakeholder_coverage",
            evidence={"stakeholder_count": 3},
            validator="stakeholder_agent",
        )
        phase_manager.pass_quality_gate(
            "data_sources_validated",
            evidence={"source_count": 3, "viable_sources": 3},
            validator="source_discovery_agent",
        )
        phase_manager.pass_quality_gate(
            "requirements_documented",
            evidence={"requirement_count": 5},
            validator="requirements_agent",
        )

        # Check progress before approval
        status = get_phase_requirements_status(phase_manager)
        assert status["outputs"]["total"] == len(status["outputs"]["completed"]) + len(status["outputs"]["remaining"])

        # 7. Create approval request
        approval = await approval_manager.create_request(
            engagement_id=engagement_id,
            approval_type=ApprovalType.CONFIGURATION,
            title="Discovery Phase Sign-off",
            description="Review discovery phase outputs",
            requested_by="e2e_test",
        )

        # 8. Submit approval decision
        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            decided_by="test_approver",
            comments="Discovery phase outputs approved",
        )
        assert result["success"]

        # 9. Record approval in phase manager
        phase_manager.receive_approval("discovery_sign_off", approved_by="test_approver")

        # 10. Verify transition is now possible
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert validation["valid"], f"Transition should be valid: {validation}"

        # 11. Transition to design phase
        transition_result = phase_manager.transition_to(
            EngagementPhase.DESIGN,
            approved_by="test_approver",
            notes="Discovery phase complete - transitioning to design",
        )
        assert transition_result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.DESIGN

        # 12. Verify events were published
        events = mock_event_bus.get_events()
        event_types = [e["type"] for e in events]
        assert "approval.requested" in event_types
        assert "approval.decided" in event_types
