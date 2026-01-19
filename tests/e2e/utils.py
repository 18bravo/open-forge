"""
E2E Test Utilities for Open Forge.

Provides helper functions for common E2E testing operations:
- Waiting for phase transitions
- Submitting approvals
- Checking engagement status
- Polling for async operations
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar
from dataclasses import dataclass
from enum import Enum

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalDecision, ApprovalStatus


T = TypeVar("T")


class TimeoutError(Exception):
    """Raised when an operation times out."""
    pass


class PhaseTransitionError(Exception):
    """Raised when a phase transition fails."""
    pass


class ApprovalError(Exception):
    """Raised when an approval operation fails."""
    pass


# -----------------------------------------------------------------------------
# Timing and Polling Utilities
# -----------------------------------------------------------------------------

@dataclass
class WaitResult:
    """Result of a wait operation."""
    success: bool
    elapsed_seconds: float
    final_value: Any
    attempts: int
    error: Optional[str] = None


async def wait_for_condition(
    condition: Callable[[], Any],
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.5,
    description: str = "condition",
) -> WaitResult:
    """
    Wait for a condition to become truthy.

    Args:
        condition: Callable that returns a truthy value when ready.
        timeout_seconds: Maximum time to wait.
        poll_interval: Time between checks.
        description: Description for error messages.

    Returns:
        WaitResult with success status and details.
    """
    start_time = time.time()
    attempts = 0

    while True:
        elapsed = time.time() - start_time
        attempts += 1

        try:
            if asyncio.iscoroutinefunction(condition):
                result = await condition()
            else:
                result = condition()

            if result:
                return WaitResult(
                    success=True,
                    elapsed_seconds=elapsed,
                    final_value=result,
                    attempts=attempts,
                )
        except Exception as e:
            # Record error but continue waiting
            if elapsed >= timeout_seconds:
                return WaitResult(
                    success=False,
                    elapsed_seconds=elapsed,
                    final_value=None,
                    attempts=attempts,
                    error=f"Condition check failed: {str(e)}",
                )

        if elapsed >= timeout_seconds:
            return WaitResult(
                success=False,
                elapsed_seconds=elapsed,
                final_value=None,
                attempts=attempts,
                error=f"Timeout waiting for {description} after {timeout_seconds}s",
            )

        await asyncio.sleep(poll_interval)


async def wait_for_value(
    getter: Callable[[], T],
    expected_value: T,
    timeout_seconds: float = 30.0,
    poll_interval: float = 0.5,
    description: str = "value",
) -> WaitResult:
    """
    Wait for a value to match expected.

    Args:
        getter: Callable that returns the current value.
        expected_value: The value to wait for.
        timeout_seconds: Maximum time to wait.
        poll_interval: Time between checks.
        description: Description for error messages.

    Returns:
        WaitResult with success status and details.
    """
    async def condition():
        if asyncio.iscoroutinefunction(getter):
            current = await getter()
        else:
            current = getter()
        return current == expected_value

    return await wait_for_condition(
        condition,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        description=f"{description} to equal {expected_value}",
    )


# -----------------------------------------------------------------------------
# Phase Management Utilities
# -----------------------------------------------------------------------------

async def wait_for_phase(
    phase_manager: PhaseManager,
    target_phase: EngagementPhase,
    timeout_seconds: float = 60.0,
    poll_interval: float = 1.0,
) -> WaitResult:
    """
    Wait for an engagement to reach a specific phase.

    Args:
        phase_manager: PhaseManager instance to monitor.
        target_phase: The phase to wait for.
        timeout_seconds: Maximum time to wait (default 60s).
        poll_interval: Time between checks (default 1s).

    Returns:
        WaitResult with success status and final phase info.

    Expected duration: 5-60 seconds depending on phase complexity.
    """
    def get_phase():
        return phase_manager.get_current_phase()

    result = await wait_for_value(
        get_phase,
        target_phase,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        description=f"phase transition to {target_phase.value}",
    )

    if result.success:
        result.final_value = phase_manager.get_phase_summary()

    return result


def get_phase_requirements_status(
    phase_manager: PhaseManager,
    phase: Optional[EngagementPhase] = None,
) -> Dict[str, Any]:
    """
    Get detailed status of phase requirements completion.

    Args:
        phase_manager: PhaseManager instance.
        phase: Specific phase to check (defaults to current).

    Returns:
        Dict with completion status for outputs, gates, and approvals.
    """
    status = phase_manager.get_phase_status(phase)
    requirements = phase_manager.get_phase_requirements(phase)
    remaining = phase_manager.get_remaining_work(phase)

    return {
        "phase": status.phase.value,
        "completion_percentage": status.completion_percentage,
        "is_complete": status.is_complete,
        "outputs": {
            "completed": list(status.outputs_completed),
            "remaining": remaining["remaining_outputs"],
            "total": len(requirements.required_outputs),
        },
        "quality_gates": {
            "passed": list(status.gates_passed),
            "remaining": remaining["remaining_gates"],
            "total": len(requirements.quality_gates),
        },
        "approvals": {
            "received": list(status.approvals_received),
            "remaining": remaining["remaining_approvals"],
            "total": len(requirements.required_approvals),
        },
    }


def complete_phase_requirements(
    phase_manager: PhaseManager,
    outputs: Optional[List[str]] = None,
    gates: Optional[List[str]] = None,
    approvals: Optional[List[str]] = None,
    phase: Optional[EngagementPhase] = None,
) -> Dict[str, Any]:
    """
    Helper to mark multiple phase requirements as complete.

    Args:
        phase_manager: PhaseManager instance.
        outputs: List of output keys to mark complete.
        gates: List of gate IDs to pass.
        approvals: List of approval types to receive.
        phase: Specific phase (defaults to current).

    Returns:
        Updated phase status.
    """
    target_phase = phase or phase_manager.get_current_phase()

    if outputs:
        for output in outputs:
            phase_manager.record_output(output, target_phase)

    if gates:
        for gate_id in gates:
            phase_manager.pass_quality_gate(
                gate_id,
                evidence={"completed_by": "e2e_test"},
                validator="e2e_test",
                phase=target_phase,
            )

    if approvals:
        for approval_type in approvals:
            phase_manager.receive_approval(
                approval_type,
                approved_by="e2e_test_user",
                phase=target_phase,
            )

    return phase_manager.get_phase_summary()


def force_phase_transition(
    phase_manager: PhaseManager,
    target_phase: EngagementPhase,
    approved_by: str = "e2e_test",
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Force a phase transition for testing (bypasses requirements).

    Args:
        phase_manager: PhaseManager instance.
        target_phase: Phase to transition to.
        approved_by: Who approved the transition.
        notes: Optional notes about the transition.

    Returns:
        Transition result.
    """
    return phase_manager.transition_to(
        target_phase,
        approved_by=approved_by,
        notes=notes or "Forced transition for E2E testing",
        force=True,
    )


# -----------------------------------------------------------------------------
# Approval Utilities
# -----------------------------------------------------------------------------

async def submit_approval(
    approval_manager: ApprovalManager,
    approval_id: str,
    decision: bool,
    decided_by: str = "e2e_test_approver",
    comments: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Submit a decision on an approval request.

    Args:
        approval_manager: ApprovalManager instance.
        approval_id: ID of the approval to decide.
        decision: True to approve, False to reject.
        decided_by: Who made the decision.
        comments: Optional comments.

    Returns:
        Updated approval request as dict.

    Expected duration: <1 second.
    """
    approval_decision = ApprovalDecision(
        approved=decision,
        decided_by=decided_by,
        comments=comments or ("Approved for testing" if decision else "Rejected for testing"),
    )

    try:
        result = await approval_manager.decide(approval_id, approval_decision)
        return {
            "success": True,
            "approval_id": result.id,
            "status": result.status.value,
            "decided_by": result.decided_by,
            "decided_at": result.decided_at.isoformat() if result.decided_at else None,
        }
    except ValueError as e:
        return {
            "success": False,
            "error": str(e),
            "approval_id": approval_id,
        }


async def wait_for_approval(
    approval_manager: ApprovalManager,
    approval_id: str,
    expected_status: ApprovalStatus = ApprovalStatus.PENDING,
    timeout_seconds: float = 30.0,
) -> WaitResult:
    """
    Wait for an approval to reach a specific status.

    Args:
        approval_manager: ApprovalManager instance.
        approval_id: ID of the approval to monitor.
        expected_status: Status to wait for.
        timeout_seconds: Maximum time to wait.

    Returns:
        WaitResult with approval details.
    """
    async def get_status():
        request = await approval_manager.get_request(approval_id)
        if request:
            return request.status
        return None

    return await wait_for_value(
        get_status,
        expected_status,
        timeout_seconds=timeout_seconds,
        description=f"approval {approval_id} status",
    )


async def create_and_approve(
    approval_manager: ApprovalManager,
    engagement_id: str,
    approval_type: str,
    title: str,
    description: str = "Test approval",
    decided_by: str = "e2e_test_approver",
) -> Dict[str, Any]:
    """
    Create an approval request and immediately approve it.

    Useful for tests that need to skip approval flows.

    Args:
        approval_manager: ApprovalManager instance.
        engagement_id: Associated engagement ID.
        approval_type: Type of approval.
        title: Approval title.
        description: Approval description.
        decided_by: Who approved.

    Returns:
        Dict with created and approved request info.
    """
    from human_interaction.approvals import ApprovalType as ApprovalTypeEnum

    # Map string to enum if needed
    if isinstance(approval_type, str):
        try:
            approval_type_enum = ApprovalTypeEnum(approval_type)
        except ValueError:
            approval_type_enum = ApprovalTypeEnum.AGENT_ACTION
    else:
        approval_type_enum = approval_type

    # Create the request
    request = await approval_manager.create_request(
        engagement_id=engagement_id,
        approval_type=approval_type_enum,
        title=title,
        description=description,
        requested_by="e2e_test",
    )

    # Immediately approve
    result = await submit_approval(
        approval_manager,
        request.id,
        decision=True,
        decided_by=decided_by,
    )

    return {
        "created": {
            "id": request.id,
            "title": request.title,
            "status": request.status.value,
        },
        "decision": result,
    }


# -----------------------------------------------------------------------------
# Engagement Status Utilities
# -----------------------------------------------------------------------------

async def get_engagement_status(
    client: Any,
    engagement_id: str,
) -> Dict[str, Any]:
    """
    Get comprehensive engagement status including phases.

    Args:
        client: E2EClient instance.
        engagement_id: ID of the engagement.

    Returns:
        Dict with engagement and phase status.

    Expected duration: <1 second.
    """
    engagement = await client.get_engagement(engagement_id)

    return {
        "engagement_id": engagement_id,
        "status": engagement.get("status"),
        "name": engagement.get("name"),
        "created_at": engagement.get("created_at"),
        "updated_at": engagement.get("updated_at"),
        "started_at": engagement.get("started_at"),
        "completed_at": engagement.get("completed_at"),
        "error_message": engagement.get("error_message"),
    }


async def wait_for_engagement_status(
    client: Any,
    engagement_id: str,
    expected_status: str,
    timeout_seconds: float = 60.0,
    poll_interval: float = 2.0,
) -> WaitResult:
    """
    Wait for an engagement to reach a specific status.

    Args:
        client: E2EClient instance.
        engagement_id: ID of the engagement.
        expected_status: Status to wait for.
        timeout_seconds: Maximum time to wait.
        poll_interval: Time between checks.

    Returns:
        WaitResult with engagement details.

    Expected duration: 5-60 seconds depending on workflow.
    """
    async def get_status():
        try:
            result = await client.get_engagement(engagement_id)
            return result.get("status")
        except Exception:
            return None

    return await wait_for_value(
        get_status,
        expected_status,
        timeout_seconds=timeout_seconds,
        poll_interval=poll_interval,
        description=f"engagement {engagement_id} status",
    )


# -----------------------------------------------------------------------------
# Test Data Helpers
# -----------------------------------------------------------------------------

def generate_test_engagement_name(prefix: str = "E2E Test") -> str:
    """Generate a unique engagement name for testing."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix} - {timestamp}"


def generate_test_data_sources(count: int = 2) -> List[Dict[str, Any]]:
    """Generate test data source configurations."""
    sources = []
    for i in range(count):
        sources.append({
            "source_id": f"test-source-{i+1}",
            "source_type": "database" if i % 2 == 0 else "api",
            "access_mode": "read",
            "config": {
                "host": f"test-host-{i+1}.example.com",
                "port": 5432 + i,
            },
        })
    return sources


# -----------------------------------------------------------------------------
# Assertion Helpers
# -----------------------------------------------------------------------------

def assert_phase_complete(
    phase_status: Dict[str, Any],
    expected_outputs: Optional[List[str]] = None,
    expected_gates: Optional[List[str]] = None,
) -> None:
    """
    Assert that a phase is complete with expected outputs and gates.

    Args:
        phase_status: Phase status dict from get_phase_requirements_status.
        expected_outputs: Optional list of expected output keys.
        expected_gates: Optional list of expected gate IDs.

    Raises:
        AssertionError: If assertions fail.
    """
    assert phase_status["is_complete"], (
        f"Phase {phase_status['phase']} is not complete. "
        f"Completion: {phase_status['completion_percentage']}%"
    )

    if expected_outputs:
        completed = phase_status["outputs"]["completed"]
        for output in expected_outputs:
            assert output in completed, f"Expected output '{output}' not found in completed outputs"

    if expected_gates:
        passed = phase_status["quality_gates"]["passed"]
        for gate in expected_gates:
            assert gate in passed, f"Expected gate '{gate}' not found in passed gates"


def assert_approval_pending(approval: Dict[str, Any]) -> None:
    """Assert that an approval is in pending status."""
    status = approval.get("status", "")
    assert status.lower() == "pending", f"Expected pending approval, got: {status}"


def assert_approval_decided(
    approval: Dict[str, Any],
    expected_decision: bool,
) -> None:
    """Assert that an approval has been decided as expected."""
    status = approval.get("status", "").lower()
    if expected_decision:
        assert status == "approved", f"Expected approved status, got: {status}"
    else:
        assert status == "rejected", f"Expected rejected status, got: {status}"


def assert_engagement_in_phase(
    engagement_status: Dict[str, Any],
    expected_phase: str,
) -> None:
    """Assert that an engagement is in the expected phase."""
    current_phase = engagement_status.get("phase", "")
    assert current_phase == expected_phase, (
        f"Expected engagement in phase '{expected_phase}', got: '{current_phase}'"
    )


# -----------------------------------------------------------------------------
# Test Duration Markers
# -----------------------------------------------------------------------------

# Test duration expectations (in seconds)
EXPECTED_DURATIONS = {
    "quick": 5,           # Simple API calls
    "standard": 30,       # Single phase execution
    "extended": 120,      # Multi-phase workflow
    "full_lifecycle": 300,  # Complete engagement lifecycle
}


def get_expected_duration(test_type: str) -> int:
    """Get expected test duration in seconds."""
    return EXPECTED_DURATIONS.get(test_type, 60)
