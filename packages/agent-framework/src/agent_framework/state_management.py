"""
LangGraph state management for Open Forge agents.
"""
from typing import TypedDict, Annotated, Sequence, Optional, Any, Dict, List
from datetime import datetime
import operator
from pydantic import BaseModel, Field
from langgraph.graph import MessagesState


class Message(BaseModel):
    """A message in the agent conversation."""
    role: str
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Decision(BaseModel):
    """A decision made by an agent."""
    decision_type: str
    description: str
    confidence: float
    reasoning: str
    requires_approval: bool = False
    approved: Optional[bool] = None


class AgentState(TypedDict):
    """Base state for all Open Forge agents."""
    # Engagement context
    engagement_id: str
    phase: str

    # Messages with reducer for accumulation
    messages: Annotated[Sequence[Message], operator.add]

    # Agent outputs accumulate
    outputs: Annotated[Dict[str, Any], lambda x, y: {**x, **y}]

    # Decisions made by agents
    decisions: Annotated[List[Decision], operator.add]

    # Current step in the workflow
    current_step: str

    # Whether human review is needed
    requires_human_review: bool
    review_items: List[Dict[str, Any]]

    # Error tracking
    errors: Annotated[List[str], operator.add]

    # Agent-specific context
    agent_context: Dict[str, Any]


class DiscoveryState(AgentState):
    """State for discovery agent cluster."""
    discovered_sources: List[Dict[str, Any]]
    source_assessments: Dict[str, Dict[str, Any]]
    stakeholder_map: Dict[str, Any]
    requirements: List[Dict[str, Any]]


class DataArchitectState(AgentState):
    """State for data architect agent cluster."""
    ontology_draft: Optional[Dict[str, Any]]
    schema_definitions: Dict[str, Any]
    data_models: List[Dict[str, Any]]
    validation_results: Dict[str, Any]


class AppBuilderState(AgentState):
    """State for app builder agent cluster."""
    ui_components: List[Dict[str, Any]]
    workflows: List[Dict[str, Any]]
    integrations: Dict[str, Any]
    deployment_config: Optional[Dict[str, Any]]


class OperationsState(AgentState):
    """State for operations agent cluster."""
    # Monitoring outputs
    prometheus_configs: Dict[str, Any]
    grafana_dashboards: List[Dict[str, Any]]
    alerting_rules: List[Dict[str, Any]]

    # Scaling outputs
    scaling_policies: List[Dict[str, Any]]
    load_balancer_configs: Dict[str, Any]
    workload_analysis: Dict[str, Any]

    # Maintenance outputs
    backup_strategies: List[Dict[str, Any]]
    maintenance_schedules: List[Dict[str, Any]]
    health_check_scripts: List[Dict[str, Any]]

    # Incident outputs
    incident_playbooks: List[Dict[str, Any]]
    escalation_procedures: List[Dict[str, Any]]
    postmortem_templates: List[Dict[str, Any]]

    # Ontology integration
    entity_metrics_map: Dict[str, Any]


class EnablementState(AgentState):
    """State for enablement agent cluster."""
    # Documentation outputs
    api_documentation: Dict[str, Any]
    user_guides: List[Dict[str, Any]]
    runbooks: List[Dict[str, Any]]

    # Training outputs
    training_materials: List[Dict[str, Any]]
    tutorials: List[Dict[str, Any]]
    quickstart_guides: List[Dict[str, Any]]

    # Support outputs
    faq_documents: List[Dict[str, Any]]
    troubleshooting_guides: List[Dict[str, Any]]
    knowledge_base_articles: List[Dict[str, Any]]

    # Ontology context
    ontology_entities: List[Dict[str, Any]]
    ontology_relationships: List[Dict[str, Any]]


def create_initial_state(
    engagement_id: str,
    phase: str,
    context: Optional[Dict[str, Any]] = None
) -> AgentState:
    """Create initial state for an agent workflow."""
    return AgentState(
        engagement_id=engagement_id,
        phase=phase,
        messages=[],
        outputs={},
        decisions=[],
        current_step="start",
        requires_human_review=False,
        review_items=[],
        errors=[],
        agent_context=context or {}
    )


def add_decision(
    state: AgentState,
    decision_type: str,
    description: str,
    confidence: float,
    reasoning: str,
    requires_approval: bool = False
) -> Decision:
    """Helper to create and track a decision."""
    decision = Decision(
        decision_type=decision_type,
        description=description,
        confidence=confidence,
        reasoning=reasoning,
        requires_approval=requires_approval
    )
    return decision


def mark_for_review(
    state: AgentState,
    item_type: str,
    item_id: str,
    description: str,
    priority: str = "medium"
) -> Dict[str, Any]:
    """Mark an item for human review."""
    review_item = {
        "type": item_type,
        "id": item_id,
        "description": description,
        "priority": priority,
        "created_at": datetime.utcnow().isoformat()
    }
    return review_item
