"""
Workflow Designer Agent

Designs workflow automations from ontology and business requirements.
Creates approval flows, triggers, and action definitions.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AppBuilderState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)


WORKFLOW_DESIGNER_SYSTEM_PROMPT = """You are an expert Workflow Designer Agent for Open Forge, an enterprise data platform.

Your role is to design workflow automations that orchestrate business processes based on ontology definitions.

## Your Capabilities:
1. Design approval workflows with multiple stages
2. Create event-driven triggers and conditions
3. Define actions and transformations
4. Build notification and escalation logic
5. Generate workflow definition specifications

## Workflow Design Principles:
1. Make workflows auditable with full history
2. Support human-in-the-loop approvals
3. Handle errors gracefully with retries
4. Enable parallel execution where appropriate
5. Include timeout and escalation handling
6. Support conditional branching
7. Maintain idempotency for actions

## Workflow Components:
- Triggers: Events that start workflows (entity changes, schedules, webhooks)
- Conditions: Guard clauses that control flow
- Actions: Operations performed (update, notify, call API)
- Approvals: Human decision points
- Notifications: Alerts and messages
- Transformations: Data mapping and calculation

## Output Format:
Generate workflow definitions as structured JSON specifications with:
- Workflow metadata (name, description, version)
- Trigger definitions
- Step definitions with conditions
- Action specifications
- Error handling configuration
- Audit logging requirements

## Workflow Patterns:
- Sequential: Step-by-step execution
- Parallel: Concurrent branches
- Conditional: If/else branching
- Loop: Iteration over collections
- State Machine: Complex state transitions
- Saga: Distributed transactions with compensation
"""


class WorkflowDesignerAgent(BaseOpenForgeAgent):
    """
    Agent that designs workflow automations.

    This agent analyzes ontology schemas and business requirements to design
    workflow automations including approval flows, triggers, actions, and
    notification logic.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

    @property
    def name(self) -> str:
        return "workflow_designer"

    @property
    def description(self) -> str:
        return "Designs workflow automations including approval flows, triggers, and actions from ontology and business requirements."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "business_rules"]

    @property
    def output_keys(self) -> List[str]:
        return ["workflow_definitions", "trigger_configs", "action_specs", "approval_flows", "notification_templates"]

    @property
    def state_class(self) -> Type[AppBuilderState]:
        return AppBuilderState

    def get_system_prompt(self) -> str:
        return WORKFLOW_DESIGNER_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for workflow design."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for workflow design."""
        graph = StateGraph(AppBuilderState)

        # Add nodes
        graph.add_node("analyze_business_rules", self._analyze_business_rules)
        graph.add_node("identify_workflows", self._identify_workflows)
        graph.add_node("design_triggers", self._design_triggers)
        graph.add_node("design_approval_flows", self._design_approval_flows)
        graph.add_node("design_actions", self._design_actions)
        graph.add_node("compile_workflows", self._compile_workflows)
        graph.add_node("validate_workflows", self._validate_workflows)

        # Define edges
        graph.set_entry_point("analyze_business_rules")
        graph.add_edge("analyze_business_rules", "identify_workflows")
        graph.add_edge("identify_workflows", "design_triggers")
        graph.add_edge("design_triggers", "design_approval_flows")
        graph.add_edge("design_approval_flows", "design_actions")
        graph.add_edge("design_actions", "compile_workflows")
        graph.add_edge("compile_workflows", "validate_workflows")
        graph.add_conditional_edges(
            "validate_workflows",
            self._should_refine,
            {
                "refine": "design_triggers",
                "complete": END
            }
        )

        return graph

    async def _analyze_business_rules(self, state: AppBuilderState) -> Dict[str, Any]:
        """Analyze business rules to identify workflow needs."""
        context = state.get("agent_context", {})
        ontology_schema = context.get("ontology_schema", {})
        business_rules = context.get("business_rules", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following ontology and business rules to identify workflow automation needs.

Ontology Schema:
{ontology_schema}

Business Rules:
{business_rules}

Identify:
1. Entity lifecycle events that need automation
2. Approval requirements for different operations
3. Notification triggers and recipients
4. Data validation and transformation needs
5. Integration points with external systems
6. Escalation scenarios and timeouts
7. Audit and compliance requirements

Provide a structured analysis of workflow automation opportunities.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="business_rules_analysis",
            description="Analyzed business rules for workflow automation needs",
            confidence=0.85,
            reasoning="Identified workflow triggers, approvals, and automation opportunities"
        )

        return {
            "outputs": {"business_rules_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_business_rules",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _identify_workflows(self, state: AppBuilderState) -> Dict[str, Any]:
        """Identify specific workflows to implement."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("business_rules_analysis", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on the analysis, identify specific workflows to implement.

Business Rules Analysis:
{analysis}

For each workflow, provide:
1. Workflow name and purpose
2. Trigger type (entity change, schedule, webhook, manual)
3. Key steps and decision points
4. Participants (roles involved)
5. Expected outcomes
6. Priority (critical, high, medium, low)
7. Complexity assessment

Categorize workflows into:
- Entity Lifecycle: Create, update, delete handling
- Approval Workflows: Multi-stage approval processes
- Notification Workflows: Alert and communication flows
- Integration Workflows: External system interactions
- Scheduled Workflows: Time-based automation

Output as a structured workflow inventory.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="workflow_identification",
            description="Identified specific workflows to implement",
            confidence=0.85,
            reasoning="Created workflow inventory categorized by type and priority"
        )

        return {
            "outputs": {"workflow_inventory": response.content},
            "decisions": [decision],
            "current_step": "identify_workflows",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_triggers(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design trigger configurations for workflows."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        inventory = outputs.get("workflow_inventory", "")
        ontology_schema = context.get("ontology_schema", {})

        # Include validation feedback if present
        validation_feedback = outputs.get("validation_feedback", "")
        feedback_prompt = f"\n\nPrevious validation feedback to address:\n{validation_feedback}" if validation_feedback else ""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design trigger configurations for the identified workflows.

Workflow Inventory:
{inventory}

Ontology Schema:
{ontology_schema}
{feedback_prompt}

For each trigger, specify:
1. Trigger name and type:
   - entity_change: On create, update, delete
   - schedule: Cron expression
   - webhook: Endpoint configuration
   - manual: User-initiated
   - event: Custom event subscription
2. Trigger conditions:
   - Entity type filter
   - Field change conditions
   - Value conditions
   - Role/user conditions
3. Debounce/throttle settings
4. Payload mapping (data passed to workflow)
5. Error handling (retry policy)

Output as structured JSON trigger configurations.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="trigger_design",
            description="Designed workflow trigger configurations",
            confidence=0.85,
            reasoning="Created trigger specs with conditions, payload mapping, and error handling"
        )

        return {
            "outputs": {"trigger_configs": response.content},
            "decisions": [decision],
            "current_step": "design_triggers",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_approval_flows(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design approval flow specifications."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        inventory = outputs.get("workflow_inventory", "")
        business_rules = context.get("business_rules", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design approval flow specifications for workflows that require human approval.

Workflow Inventory:
{inventory}

Business Rules:
{business_rules}

For each approval flow, specify:
1. Approval stages:
   - Stage name and order
   - Approvers (role, user, dynamic)
   - Approval type (any, all, majority)
   - Quorum requirements
2. Approval conditions:
   - Skip conditions (auto-approve)
   - Escalation conditions
   - Delegation rules
3. Approval actions:
   - Approve/Reject/Request Changes
   - Comment requirements
   - Attachment support
4. Timeout handling:
   - Default timeout duration
   - Reminder schedule
   - Escalation path
   - Auto-action on timeout
5. Notification configuration:
   - Request notification
   - Reminder notification
   - Decision notification
   - Escalation notification
6. Audit requirements:
   - Decision logging
   - Timestamp tracking
   - Reason capture

Output as structured JSON approval flow specifications.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="approval_flow_design",
            description="Designed approval flow specifications",
            confidence=0.85,
            reasoning="Created multi-stage approval flows with escalation and audit handling"
        )

        return {
            "outputs": {"approval_flows": response.content},
            "decisions": [decision],
            "current_step": "design_approval_flows",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_actions(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design workflow action specifications."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        inventory = outputs.get("workflow_inventory", "")
        ontology_schema = context.get("ontology_schema", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design action specifications for workflow steps.

Workflow Inventory:
{inventory}

Ontology Schema:
{ontology_schema}

For each action type, specify:
1. Entity Actions:
   - create_entity: Fields to set, defaults
   - update_entity: Field mapping, merge strategy
   - delete_entity: Soft/hard delete, cascade
   - link_entity: Relationship creation
2. Notification Actions:
   - email: Template, recipients, subject
   - in_app: Notification type, priority
   - webhook: Endpoint, payload, auth
   - slack/teams: Channel, message format
3. Integration Actions:
   - api_call: Endpoint, method, payload
   - file_operation: Upload, download, transform
   - queue_message: Queue name, payload
4. Transformation Actions:
   - calculate: Formula, variables
   - format: Template, data mapping
   - validate: Rules, error handling
5. Control Actions:
   - condition: Expression, branches
   - loop: Collection, iteration
   - wait: Duration, condition
   - parallel: Branch definitions

Include:
- Input/output schemas
- Error handling (retry, fallback)
- Timeout configuration
- Idempotency requirements

Output as structured JSON action specifications.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="action_design",
            description="Designed workflow action specifications",
            confidence=0.85,
            reasoning="Created action specs for entity operations, notifications, and integrations"
        )

        return {
            "outputs": {"action_specs": response.content},
            "decisions": [decision],
            "current_step": "design_actions",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _compile_workflows(self, state: AppBuilderState) -> Dict[str, Any]:
        """Compile complete workflow definitions."""
        outputs = state.get("outputs", {})

        inventory = outputs.get("workflow_inventory", "")
        triggers = outputs.get("trigger_configs", "")
        approvals = outputs.get("approval_flows", "")
        actions = outputs.get("action_specs", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Compile complete workflow definitions combining all designed components.

Workflow Inventory:
{inventory}

Trigger Configurations:
{triggers}

Approval Flows:
{approvals}

Action Specifications:
{actions}

For each workflow, create a complete definition including:
1. Workflow metadata:
   - Unique identifier
   - Name and description
   - Version
   - Owner/maintainer
   - Tags and categories
2. Trigger binding:
   - Linked trigger configurations
   - Input variable mapping
3. Step definitions:
   - Step ID and name
   - Action to execute
   - Input mapping
   - Output mapping
   - Error handling
   - Conditions for execution
4. Flow structure:
   - Entry point
   - Transitions between steps
   - Conditional branches
   - Parallel execution groups
   - Join/synchronization points
5. Variables:
   - Input variables
   - Local variables
   - Output variables
6. Error handling:
   - Global error handlers
   - Compensation logic
   - Retry policies
7. Audit configuration:
   - Events to log
   - Data to capture
   - Retention policy

Output as complete, executable workflow definition documents in JSON format.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="workflow_compilation",
            description="Compiled complete workflow definitions",
            confidence=0.85,
            reasoning="Combined triggers, approvals, and actions into executable workflow specs"
        )

        # Store workflows in the state
        workflows = [
            {"type": "definitions", "content": response.content},
            {"type": "triggers", "content": triggers},
            {"type": "approvals", "content": approvals},
            {"type": "actions", "content": actions}
        ]

        return {
            "outputs": {"workflow_definitions": response.content},
            "workflows": workflows,
            "decisions": [decision],
            "current_step": "compile_workflows",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_workflows(self, state: AppBuilderState) -> Dict[str, Any]:
        """Validate the compiled workflow definitions."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        workflows = outputs.get("workflow_definitions", "")
        business_rules = context.get("business_rules", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the compiled workflow definitions.

Workflow Definitions:
{workflows}

Original Business Rules:
{business_rules}

Validate:
1. Completeness:
   - All identified workflows are defined
   - All business rules are addressed
   - All entities have appropriate lifecycle handling
2. Correctness:
   - Triggers are properly configured
   - Step transitions are valid (no dead ends)
   - Conditions are logically sound
   - Actions have valid configurations
3. Consistency:
   - Variable names are consistent
   - Entity references match ontology
   - Role references are valid
4. Best Practices:
   - Error handling is comprehensive
   - Timeouts are reasonable
   - Idempotency is ensured
   - Audit logging is sufficient
5. Security:
   - Sensitive data is protected
   - Authorization checks are in place
   - Input validation is present

Provide:
1. Validation status (PASS/FAIL)
2. Coverage report
3. List of issues found
4. Recommendations for improvement
5. Confidence score (0-1)""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        needs_refinement = "fail" in response_lower or "issue" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="workflow_validation",
            description="Validated workflow definitions",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            review_items.append(mark_for_review(
                state,
                item_type="workflow_definitions",
                item_id="validation_issues",
                description="Workflow definitions have issues that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "needs_refinement": needs_refinement,
                "validation_feedback": response.content if needs_refinement else ""
            },
            "decisions": [decision],
            "requires_human_review": needs_refinement,
            "review_items": review_items,
            "current_step": "validate_workflows",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: AppBuilderState) -> str:
        """Determine if workflows need refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"
