"""
Phase Manager for Engagement Lifecycle

Manages engagement phases (discovery, design, build, deploy) and
validates phase transition requirements.
"""
from typing import Any, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class EngagementPhase(str, Enum):
    """Engagement lifecycle phases."""
    DISCOVERY = "discovery"
    DESIGN = "design"
    BUILD = "build"
    DEPLOY = "deploy"
    COMPLETE = "complete"


class PhaseTransition(BaseModel):
    """Represents a phase transition event."""
    from_phase: EngagementPhase
    to_phase: EngagementPhase
    transition_time: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    notes: Optional[str] = None


class QualityGate(BaseModel):
    """Quality gate that must be passed for phase transition."""
    gate_id: str
    name: str
    description: str
    required: bool = True
    passed: bool = False
    passed_at: Optional[datetime] = None
    evidence: Optional[Dict[str, Any]] = None
    validator: Optional[str] = None  # Agent or human that validated


class PhaseRequirements(BaseModel):
    """Requirements and completion criteria for a phase."""
    phase: EngagementPhase
    required_outputs: List[str]
    quality_gates: List[QualityGate]
    required_approvals: List[str] = Field(default_factory=list)
    minimum_confidence: float = 0.7
    allow_human_override: bool = True


class PhaseStatus(BaseModel):
    """Current status of a phase."""
    phase: EngagementPhase
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    outputs_completed: Set[str] = Field(default_factory=set)
    gates_passed: Set[str] = Field(default_factory=set)
    approvals_received: Set[str] = Field(default_factory=set)
    is_complete: bool = False
    completion_percentage: float = 0.0


# Define phase requirements and valid transitions
PHASE_REQUIREMENTS: Dict[EngagementPhase, PhaseRequirements] = {
    EngagementPhase.DISCOVERY: PhaseRequirements(
        phase=EngagementPhase.DISCOVERY,
        required_outputs=[
            "stakeholder_map",
            "requirements",
            "discovered_sources",
            "source_assessments",
            "source_recommendations"
        ],
        quality_gates=[
            QualityGate(
                gate_id="stakeholder_coverage",
                name="Stakeholder Coverage",
                description="All key stakeholders have been identified and interviewed",
                required=True
            ),
            QualityGate(
                gate_id="data_sources_validated",
                name="Data Sources Validated",
                description="At least one viable data source identified and assessed",
                required=True
            ),
            QualityGate(
                gate_id="requirements_documented",
                name="Requirements Documented",
                description="Business and technical requirements are documented",
                required=True
            ),
        ],
        required_approvals=["discovery_sign_off"],
        minimum_confidence=0.7
    ),
    EngagementPhase.DESIGN: PhaseRequirements(
        phase=EngagementPhase.DESIGN,
        required_outputs=[
            "ontology_draft",
            "schema_definitions",
            "data_models",
            "transformation_specs",
            "validation_rules"
        ],
        quality_gates=[
            QualityGate(
                gate_id="ontology_validated",
                name="Ontology Validated",
                description="Ontology schema passes LinkML validation",
                required=True
            ),
            QualityGate(
                gate_id="schema_completeness",
                name="Schema Completeness",
                description="All required entities and relationships are defined",
                required=True
            ),
            QualityGate(
                gate_id="data_model_review",
                name="Data Model Review",
                description="Data models reviewed by stakeholders",
                required=True
            ),
        ],
        required_approvals=["design_approval"],
        minimum_confidence=0.75
    ),
    EngagementPhase.BUILD: PhaseRequirements(
        phase=EngagementPhase.BUILD,
        required_outputs=[
            "compiled_ontology",
            "data_pipelines",
            "ui_components",
            "workflows",
            "integrations"
        ],
        quality_gates=[
            QualityGate(
                gate_id="pipeline_tested",
                name="Pipeline Tested",
                description="Data pipelines pass integration tests",
                required=True
            ),
            QualityGate(
                gate_id="ui_validated",
                name="UI Validated",
                description="UI components pass accessibility and usability review",
                required=True
            ),
            QualityGate(
                gate_id="security_review",
                name="Security Review",
                description="Security review completed with no critical issues",
                required=True
            ),
        ],
        required_approvals=["build_approval", "security_sign_off"],
        minimum_confidence=0.8
    ),
    EngagementPhase.DEPLOY: PhaseRequirements(
        phase=EngagementPhase.DEPLOY,
        required_outputs=[
            "deployment_config",
            "environment_setup",
            "deployment_verification",
            "documentation",
            "training_materials"
        ],
        quality_gates=[
            QualityGate(
                gate_id="deployment_validated",
                name="Deployment Validated",
                description="Deployment verified in target environment",
                required=True
            ),
            QualityGate(
                gate_id="documentation_complete",
                name="Documentation Complete",
                description="User and technical documentation finalized",
                required=True
            ),
            QualityGate(
                gate_id="user_acceptance",
                name="User Acceptance",
                description="User acceptance testing completed",
                required=True
            ),
        ],
        required_approvals=["deployment_approval", "client_sign_off"],
        minimum_confidence=0.85
    ),
}

# Valid phase transitions
VALID_TRANSITIONS: Dict[EngagementPhase, List[EngagementPhase]] = {
    EngagementPhase.DISCOVERY: [EngagementPhase.DESIGN],
    EngagementPhase.DESIGN: [EngagementPhase.BUILD, EngagementPhase.DISCOVERY],  # Can go back
    EngagementPhase.BUILD: [EngagementPhase.DEPLOY, EngagementPhase.DESIGN],  # Can go back
    EngagementPhase.DEPLOY: [EngagementPhase.COMPLETE, EngagementPhase.BUILD],  # Can go back
    EngagementPhase.COMPLETE: [],  # Terminal state
}


class PhaseManager:
    """
    Manages engagement phases and validates transitions.

    Responsibilities:
    - Track current phase and status
    - Validate phase transition requirements
    - Manage quality gates
    - Handle approvals
    """

    def __init__(self, engagement_id: str):
        self.engagement_id = engagement_id
        self.current_phase = EngagementPhase.DISCOVERY
        self.phase_history: List[PhaseTransition] = []
        self.phase_statuses: Dict[EngagementPhase, PhaseStatus] = {}

        # Initialize all phase statuses
        for phase in EngagementPhase:
            self.phase_statuses[phase] = PhaseStatus(phase=phase)

        # Mark discovery as started
        self.phase_statuses[EngagementPhase.DISCOVERY].started_at = datetime.utcnow()

    def get_current_phase(self) -> EngagementPhase:
        """Get the current engagement phase."""
        return self.current_phase

    def get_phase_requirements(self, phase: Optional[EngagementPhase] = None) -> PhaseRequirements:
        """Get requirements for a phase (defaults to current phase)."""
        target_phase = phase or self.current_phase
        return PHASE_REQUIREMENTS[target_phase]

    def get_phase_status(self, phase: Optional[EngagementPhase] = None) -> PhaseStatus:
        """Get status of a phase (defaults to current phase)."""
        target_phase = phase or self.current_phase
        return self.phase_statuses[target_phase]

    def get_available_transitions(self) -> List[EngagementPhase]:
        """Get valid transitions from current phase."""
        return VALID_TRANSITIONS.get(self.current_phase, [])

    def record_output(self, output_key: str, phase: Optional[EngagementPhase] = None) -> None:
        """Record that an output has been completed."""
        target_phase = phase or self.current_phase
        status = self.phase_statuses[target_phase]
        status.outputs_completed.add(output_key)
        self._update_completion_percentage(target_phase)

    def pass_quality_gate(
        self,
        gate_id: str,
        evidence: Optional[Dict[str, Any]] = None,
        validator: Optional[str] = None,
        phase: Optional[EngagementPhase] = None
    ) -> bool:
        """Mark a quality gate as passed."""
        target_phase = phase or self.current_phase
        requirements = PHASE_REQUIREMENTS[target_phase]
        status = self.phase_statuses[target_phase]

        # Find and update the gate
        for gate in requirements.quality_gates:
            if gate.gate_id == gate_id:
                gate.passed = True
                gate.passed_at = datetime.utcnow()
                gate.evidence = evidence
                gate.validator = validator
                status.gates_passed.add(gate_id)
                self._update_completion_percentage(target_phase)
                return True

        return False

    def receive_approval(
        self,
        approval_type: str,
        approved_by: str,
        phase: Optional[EngagementPhase] = None
    ) -> None:
        """Record an approval received."""
        target_phase = phase or self.current_phase
        status = self.phase_statuses[target_phase]
        status.approvals_received.add(approval_type)
        self._update_completion_percentage(target_phase)

    def _update_completion_percentage(self, phase: EngagementPhase) -> None:
        """Update the completion percentage for a phase."""
        requirements = PHASE_REQUIREMENTS[phase]
        status = self.phase_statuses[phase]

        total_items = (
            len(requirements.required_outputs) +
            len(requirements.quality_gates) +
            len(requirements.required_approvals)
        )

        completed_items = (
            len(status.outputs_completed & set(requirements.required_outputs)) +
            len(status.gates_passed) +
            len(status.approvals_received & set(requirements.required_approvals))
        )

        status.completion_percentage = (completed_items / total_items * 100) if total_items > 0 else 0

    def validate_transition(
        self,
        target_phase: EngagementPhase,
        allow_override: bool = False
    ) -> Dict[str, Any]:
        """
        Validate if transition to target phase is allowed.

        Returns validation result with details on what's missing.
        """
        result = {
            "valid": False,
            "target_phase": target_phase.value,
            "current_phase": self.current_phase.value,
            "missing_outputs": [],
            "missing_gates": [],
            "missing_approvals": [],
            "can_override": False,
            "override_reason": None
        }

        # Check if transition is valid
        if target_phase not in VALID_TRANSITIONS.get(self.current_phase, []):
            result["error"] = f"Invalid transition from {self.current_phase.value} to {target_phase.value}"
            return result

        # For backward transitions, always allow (with appropriate tracking)
        phase_order = list(EngagementPhase)
        if phase_order.index(target_phase) < phase_order.index(self.current_phase):
            result["valid"] = True
            result["is_backward"] = True
            return result

        # Check current phase completion requirements
        requirements = PHASE_REQUIREMENTS[self.current_phase]
        status = self.phase_statuses[self.current_phase]

        # Check outputs
        for output in requirements.required_outputs:
            if output not in status.outputs_completed:
                result["missing_outputs"].append(output)

        # Check quality gates
        for gate in requirements.quality_gates:
            if gate.required and not gate.passed:
                result["missing_gates"].append({
                    "gate_id": gate.gate_id,
                    "name": gate.name,
                    "description": gate.description
                })

        # Check approvals
        for approval in requirements.required_approvals:
            if approval not in status.approvals_received:
                result["missing_approvals"].append(approval)

        # Determine if valid
        all_complete = (
            len(result["missing_outputs"]) == 0 and
            len(result["missing_gates"]) == 0 and
            len(result["missing_approvals"]) == 0
        )

        result["valid"] = all_complete

        # Check if override is possible
        if not all_complete and allow_override:
            if requirements.allow_human_override:
                result["can_override"] = True
                result["override_reason"] = "Human override available for this phase"

        return result

    def transition_to(
        self,
        target_phase: EngagementPhase,
        approved_by: Optional[str] = None,
        notes: Optional[str] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        Transition to a new phase.

        Args:
            target_phase: The phase to transition to
            approved_by: Who approved the transition
            notes: Optional notes about the transition
            force: Force transition even if requirements not met

        Returns:
            Result of the transition attempt
        """
        validation = self.validate_transition(target_phase, allow_override=force)

        if not validation["valid"] and not force:
            return {
                "success": False,
                "reason": "Phase requirements not met",
                "validation": validation
            }

        # Record the transition
        transition = PhaseTransition(
            from_phase=self.current_phase,
            to_phase=target_phase,
            approved_by=approved_by,
            notes=notes
        )
        self.phase_history.append(transition)

        # Update current phase status
        self.phase_statuses[self.current_phase].completed_at = datetime.utcnow()
        self.phase_statuses[self.current_phase].is_complete = True

        # Set new current phase
        previous_phase = self.current_phase
        self.current_phase = target_phase

        # Initialize new phase
        if not self.phase_statuses[target_phase].started_at:
            self.phase_statuses[target_phase].started_at = datetime.utcnow()

        return {
            "success": True,
            "previous_phase": previous_phase.value,
            "current_phase": self.current_phase.value,
            "transition": transition.model_dump(),
            "forced": force and not validation["valid"]
        }

    def get_phase_summary(self) -> Dict[str, Any]:
        """Get a summary of all phase statuses."""
        return {
            "engagement_id": self.engagement_id,
            "current_phase": self.current_phase.value,
            "available_transitions": [p.value for p in self.get_available_transitions()],
            "phases": {
                phase.value: {
                    "started_at": status.started_at.isoformat() if status.started_at else None,
                    "completed_at": status.completed_at.isoformat() if status.completed_at else None,
                    "is_complete": status.is_complete,
                    "completion_percentage": status.completion_percentage,
                    "outputs_completed": list(status.outputs_completed),
                    "gates_passed": list(status.gates_passed),
                    "approvals_received": list(status.approvals_received)
                }
                for phase, status in self.phase_statuses.items()
            },
            "history": [t.model_dump() for t in self.phase_history]
        }

    def get_remaining_work(self, phase: Optional[EngagementPhase] = None) -> Dict[str, Any]:
        """Get remaining work items for a phase."""
        target_phase = phase or self.current_phase
        requirements = PHASE_REQUIREMENTS[target_phase]
        status = self.phase_statuses[target_phase]

        return {
            "phase": target_phase.value,
            "remaining_outputs": [
                o for o in requirements.required_outputs
                if o not in status.outputs_completed
            ],
            "remaining_gates": [
                {"gate_id": g.gate_id, "name": g.name, "description": g.description}
                for g in requirements.quality_gates
                if g.required and not g.passed
            ],
            "remaining_approvals": [
                a for a in requirements.required_approvals
                if a not in status.approvals_received
            ],
            "completion_percentage": status.completion_percentage
        }
