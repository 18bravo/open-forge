"""
E2E Tests for Human-in-the-Loop Interactions.

Tests the human approval and interaction workflows including:
- Approval request creation
- Approval submission (approve/reject)
- Rejection and re-work flow
- Escalation timeout

Expected test durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Timeout tests: 60-120 seconds
"""
import asyncio
import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import patch

from human_interaction.approvals import (
    ApprovalManager,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    ApprovalType,
)
from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager

from .conftest import MockEventBus
from .utils import (
    wait_for_approval,
    submit_approval,
    create_and_approve,
)


class TestApprovalRequestCreation:
    """Tests for approval request creation."""

    @pytest.mark.asyncio
    async def test_create_approval_request(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test creating a basic approval request.

        Expected duration: ~5 seconds
        """
        approval = await approval_manager.create_request(
            engagement_id="test-eng-001",
            approval_type=ApprovalType.AGENT_ACTION,
            title="Test Agent Action Approval",
            description="Test description for approval",
            requested_by="test_agent",
        )

        assert approval.id is not None
        assert approval.status == ApprovalStatus.PENDING
        assert approval.engagement_id == "test-eng-001"
        assert approval.title == "Test Agent Action Approval"
        assert approval.requested_by == "test_agent"

    @pytest.mark.asyncio
    async def test_create_approval_with_context_data(
        self,
        approval_manager,
    ):
        """
        Test creating an approval with context data.

        Expected duration: ~5 seconds
        """
        context = {
            "action": "create_table",
            "table_name": "customers",
            "estimated_rows": 50000,
            "affected_systems": ["warehouse", "reporting"],
        }

        approval = await approval_manager.create_request(
            engagement_id="test-eng-002",
            approval_type=ApprovalType.DATA_CHANGE,
            title="Create Customer Table",
            description="Create new customer table in data warehouse",
            requested_by="transformation_agent",
            context_data=context,
        )

        assert approval.context_data is not None
        assert approval.context_data["action"] == "create_table"
        assert approval.context_data["table_name"] == "customers"

    @pytest.mark.asyncio
    async def test_create_approval_with_timeout(
        self,
        approval_manager,
    ):
        """
        Test creating an approval with timeout.

        Expected duration: ~5 seconds
        """
        approval = await approval_manager.create_request(
            engagement_id="test-eng-003",
            approval_type=ApprovalType.CONFIGURATION,
            title="Config Change Approval",
            description="Approve configuration change",
            requested_by="config_agent",
            timeout_minutes=60,
        )

        assert approval.deadline is not None
        assert approval.deadline > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_approval_request_publishes_event(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test that creating approval publishes event.

        Expected duration: ~5 seconds
        """
        await approval_manager.create_request(
            engagement_id="test-eng-004",
            approval_type=ApprovalType.DEPLOYMENT,
            title="Deploy to Production",
            description="Approve deployment to production environment",
            requested_by="deploy_agent",
        )

        events = mock_event_bus.get_events("approval.requested")
        assert len(events) >= 1

        event = events[-1]
        assert event["payload"]["type"] == ApprovalType.DEPLOYMENT.value

    @pytest.mark.asyncio
    @pytest.mark.parametrize("approval_type", [
        ApprovalType.AGENT_ACTION,
        ApprovalType.DATA_CHANGE,
        ApprovalType.CONFIGURATION,
        ApprovalType.DEPLOYMENT,
        ApprovalType.ACCESS_GRANT,
    ])
    async def test_create_approval_for_all_types(
        self,
        approval_manager,
        approval_type,
    ):
        """
        Test creating approvals for all approval types.

        Expected duration: ~5 seconds per type
        """
        approval = await approval_manager.create_request(
            engagement_id="test-eng-types",
            approval_type=approval_type,
            title=f"Test {approval_type.value} Approval",
            description=f"Testing {approval_type.value} approval type",
            requested_by="test_agent",
        )

        assert approval.approval_type == approval_type


class TestApprovalSubmission:
    """Tests for approval decision submission."""

    @pytest.mark.asyncio
    async def test_approve_request(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test approving a request.

        Expected duration: ~5 seconds
        """
        # Create request
        approval = await approval_manager.create_request(
            engagement_id="test-eng-approve",
            approval_type=ApprovalType.AGENT_ACTION,
            title="Test Approval",
            description="Test",
            requested_by="agent",
        )

        # Approve it
        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            decided_by="test_approver",
            comments="Looks good!",
        )

        assert result["success"]
        assert result["status"] == ApprovalStatus.APPROVED.value

        # Verify event published
        events = mock_event_bus.get_events("approval.decided")
        assert len(events) >= 1
        assert events[-1]["payload"]["decision"] == "approved"

    @pytest.mark.asyncio
    async def test_reject_request(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test rejecting a request.

        Expected duration: ~5 seconds
        """
        # Create request
        approval = await approval_manager.create_request(
            engagement_id="test-eng-reject",
            approval_type=ApprovalType.DATA_CHANGE,
            title="Test Rejection",
            description="Test",
            requested_by="agent",
        )

        # Reject it
        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=False,
            decided_by="test_approver",
            comments="Changes needed",
        )

        assert result["success"]
        assert result["status"] == ApprovalStatus.REJECTED.value

        # Verify event
        events = mock_event_bus.get_events("approval.decided")
        assert events[-1]["payload"]["decision"] == "rejected"

    @pytest.mark.asyncio
    async def test_cannot_decide_already_decided(
        self,
        approval_manager,
    ):
        """
        Test that already-decided approvals cannot be decided again.

        Expected duration: ~5 seconds
        """
        # Create and approve
        approval = await approval_manager.create_request(
            engagement_id="test-eng-double",
            approval_type=ApprovalType.CONFIGURATION,
            title="Test Double Decision",
            description="Test",
            requested_by="agent",
        )

        # First decision
        await submit_approval(approval_manager, approval.id, True, "approver1")

        # Try second decision - should fail
        result = await submit_approval(approval_manager, approval.id, False, "approver2")
        assert not result["success"]


class TestRejectionAndRework:
    """Tests for rejection and re-work flow."""

    @pytest.mark.asyncio
    async def test_rejection_blocks_phase_transition(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test that rejection blocks phase transition.

        Expected duration: ~10 seconds
        """
        # Complete outputs but get rejected
        from .utils import complete_phase_requirements
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
            # Note: approval NOT received
        )

        # Transition should fail
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert not validation["valid"]
        assert "discovery_sign_off" in validation["missing_approvals"]

    @pytest.mark.asyncio
    async def test_rework_after_rejection(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test re-work flow after rejection.

        Expected duration: ~15 seconds
        """
        # Create approval request
        approval = await approval_manager.create_request(
            engagement_id="test-rework",
            approval_type=ApprovalType.CONFIGURATION,
            title="Discovery Sign-off",
            description="Review discovery phase",
            requested_by="discovery_agent",
        )

        # Reject with feedback
        decision = ApprovalDecision(
            approved=False,
            decided_by="reviewer",
            comments="Need more stakeholder interviews. Please include Finance team.",
        )
        rejected = await approval_manager.decide(approval.id, decision)

        assert rejected.status == ApprovalStatus.REJECTED
        assert "Finance" in rejected.decision_comments

        # Simulate rework - create new approval request
        new_approval = await approval_manager.create_request(
            engagement_id="test-rework",
            approval_type=ApprovalType.CONFIGURATION,
            title="Discovery Sign-off (Revised)",
            description="Review revised discovery phase with Finance stakeholders",
            requested_by="discovery_agent",
            context_data={"revision": 2, "addressed_feedback": True},
        )

        # Approve the revised request
        result = await submit_approval(
            approval_manager,
            new_approval.id,
            decision=True,
            decided_by="reviewer",
            comments="Finance team included. Approved.",
        )

        assert result["success"]

    @pytest.mark.asyncio
    async def test_multiple_rejection_cycles(
        self,
        approval_manager,
    ):
        """
        Test multiple rejection-rework cycles.

        Expected duration: ~15 seconds
        """
        engagement_id = "test-multi-reject"
        revisions = []

        for i in range(3):
            # Create approval
            approval = await approval_manager.create_request(
                engagement_id=engagement_id,
                approval_type=ApprovalType.CONFIGURATION,
                title=f"Approval (Revision {i+1})",
                description="Test",
                requested_by="agent",
                context_data={"revision": i + 1},
            )
            revisions.append(approval)

            if i < 2:
                # Reject first two
                await submit_approval(
                    approval_manager,
                    approval.id,
                    decision=False,
                    comments=f"Needs more work (iteration {i+1})",
                )
            else:
                # Approve final
                await submit_approval(
                    approval_manager,
                    approval.id,
                    decision=True,
                    comments="Finally approved!",
                )

        # Verify final approval
        final_status = await approval_manager.get_request(revisions[-1].id)
        assert final_status.status == ApprovalStatus.APPROVED


class TestEscalationTimeout:
    """Tests for escalation and timeout handling."""

    @pytest.mark.asyncio
    async def test_approval_expires_after_timeout(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test that approval expires after timeout.

        Note: This test uses a very short timeout for speed.

        Expected duration: ~10 seconds
        """
        # Create approval with very short timeout
        approval = await approval_manager.create_request(
            engagement_id="test-timeout",
            approval_type=ApprovalType.AGENT_ACTION,
            title="Time-sensitive Approval",
            description="This will expire quickly",
            requested_by="agent",
            timeout_minutes=1,  # 1 minute for test
        )

        assert approval.deadline is not None

        # For immediate testing, manually expire
        expired = await approval_manager.expire(approval.id)
        assert expired.status == ApprovalStatus.EXPIRED

        # Verify event
        events = mock_event_bus.get_events("approval.expired")
        assert len(events) >= 1

    @pytest.mark.asyncio
    async def test_escalation_to_higher_level(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test escalation to higher approval level.

        Expected duration: ~10 seconds
        """
        # Create approval at level 1
        approval = await approval_manager.create_request(
            engagement_id="test-escalate",
            approval_type=ApprovalType.DEPLOYMENT,
            title="Production Deployment",
            description="Deploy to production",
            requested_by="deploy_agent",
        )

        assert approval.escalation_level == "level_1"

        # Escalate to level 2
        escalated = await approval_manager.escalate(
            approval.id,
            new_level="level_2",
            reason="No response within SLA",
        )

        assert escalated.status == ApprovalStatus.ESCALATED
        assert escalated.escalation_level == "level_2"

        # Verify event
        events = mock_event_bus.get_events("approval.escalated")
        assert len(events) >= 1
        assert events[-1]["payload"]["new_level"] == "level_2"

    @pytest.mark.asyncio
    async def test_escalated_approval_can_be_decided(
        self,
        approval_manager,
    ):
        """
        Test that escalated approvals can still be decided.

        Expected duration: ~10 seconds
        """
        # Create and escalate
        approval = await approval_manager.create_request(
            engagement_id="test-escalate-decide",
            approval_type=ApprovalType.DATA_CHANGE,
            title="Critical Data Change",
            description="Test",
            requested_by="agent",
        )

        await approval_manager.escalate(approval.id, "level_2", "SLA exceeded")

        # Decide at higher level
        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            decided_by="senior_approver",
            comments="Approved at escalated level",
        )

        assert result["success"]
        assert result["status"] == ApprovalStatus.APPROVED.value


class TestPendingApprovalsList:
    """Tests for listing pending approvals."""

    @pytest.mark.asyncio
    async def test_list_pending_approvals(
        self,
        approval_manager,
    ):
        """
        Test listing pending approvals.

        Expected duration: ~10 seconds
        """
        engagement_id = "test-pending-list"

        # Create multiple approvals
        for i in range(3):
            await approval_manager.create_request(
                engagement_id=engagement_id,
                approval_type=ApprovalType.AGENT_ACTION,
                title=f"Pending Approval {i+1}",
                description="Test",
                requested_by="agent",
            )

        # List pending
        pending = await approval_manager.get_pending_requests(engagement_id=engagement_id)

        assert len(pending) == 3
        assert all(a.status in [ApprovalStatus.PENDING, ApprovalStatus.ESCALATED] for a in pending)

    @pytest.mark.asyncio
    async def test_list_pending_by_type(
        self,
        approval_manager,
    ):
        """
        Test listing pending approvals filtered by type.

        Expected duration: ~10 seconds
        """
        # Create different types
        await approval_manager.create_request(
            engagement_id="test-type-filter",
            approval_type=ApprovalType.DATA_CHANGE,
            title="Data Change 1",
            description="Test",
            requested_by="agent",
        )
        await approval_manager.create_request(
            engagement_id="test-type-filter",
            approval_type=ApprovalType.DEPLOYMENT,
            title="Deployment 1",
            description="Test",
            requested_by="agent",
        )

        # Filter by type
        data_changes = await approval_manager.get_pending_requests(
            approval_type=ApprovalType.DATA_CHANGE
        )

        assert len(data_changes) >= 1
        assert all(a.approval_type == ApprovalType.DATA_CHANGE for a in data_changes)


class TestApprovalIntegrationWithPhases:
    """Tests for approval integration with phase management."""

    @pytest.mark.asyncio
    async def test_quick_approval_workflow(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test quick approval using helper utility.

        Expected duration: ~5 seconds
        """
        result = await create_and_approve(
            approval_manager,
            engagement_id="test-quick",
            approval_type="agent_action",
            title="Quick Approval Test",
            description="Test quick approval flow",
        )

        assert result["created"]["status"] == ApprovalStatus.PENDING.value
        assert result["decision"]["success"]
        assert result["decision"]["status"] == ApprovalStatus.APPROVED.value

    @pytest.mark.asyncio
    async def test_full_approval_flow_with_phase(
        self,
        phase_manager,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test full approval flow integrated with phase management.

        Expected duration: ~30 seconds
        """
        from .utils import complete_phase_requirements

        # Complete discovery phase requirements (except approval)
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
        )

        # Create approval request
        approval = await approval_manager.create_request(
            engagement_id="test-phase-approval",
            approval_type=ApprovalType.CONFIGURATION,
            title="Discovery Phase Approval",
            description="Approve discovery phase completion",
            requested_by="discovery_agent",
            context_data={
                "phase": "discovery",
                "outputs_completed": 5,
                "gates_passed": 3,
            },
        )

        # Verify transition blocked
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert not validation["valid"]

        # Submit approval
        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            decided_by="phase_approver",
        )
        assert result["success"]

        # Record approval in phase manager
        phase_manager.receive_approval("discovery_sign_off", approved_by="phase_approver")

        # Now transition should be valid
        validation = phase_manager.validate_transition(EngagementPhase.DESIGN)
        assert validation["valid"]

        # Perform transition
        transition = phase_manager.transition_to(
            EngagementPhase.DESIGN,
            approved_by="phase_approver",
        )
        assert transition["success"]
