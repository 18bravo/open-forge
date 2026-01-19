"""
Integration Agent

Configures system integrations, API connections, and authentication.
Sets up data connectors and external service bindings.
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


INTEGRATION_AGENT_SYSTEM_PROMPT = """You are an expert Integration Agent for Open Forge, an enterprise data platform.

Your role is to configure system integrations, API connections, and authentication for applications.

## Your Capabilities:
1. Configure API endpoints and connections
2. Set up authentication mechanisms (OAuth, API keys, JWT)
3. Design data synchronization strategies
4. Create webhook configurations
5. Define error handling and retry policies

## Integration Design Principles:
1. Security first - proper authentication and authorization
2. Resilience - retries, circuit breakers, fallbacks
3. Observability - logging, metrics, tracing
4. Performance - caching, batching, rate limiting
5. Maintainability - clear configuration, documentation

## Integration Types:
- REST APIs: Endpoints, methods, headers, authentication
- GraphQL: Schemas, queries, mutations
- Webhooks: Inbound and outbound event handling
- Message Queues: Pub/sub, message formats
- Databases: Connection pools, queries
- File Storage: S3, blob storage, FTP
- Identity Providers: SSO, LDAP, SAML

## Authentication Methods:
- API Key: Header or query parameter
- OAuth 2.0: Authorization code, client credentials
- JWT: Token generation and validation
- Basic Auth: Username/password
- mTLS: Certificate-based authentication

## Output Format:
Generate integration configurations as structured JSON with:
- Connection settings
- Authentication configuration
- Endpoint definitions
- Error handling policies
- Rate limiting configuration
- Monitoring/alerting setup
"""


class IntegrationAgent(BaseOpenForgeAgent):
    """
    Agent that configures system integrations.

    This agent analyzes integration requirements and generates configurations
    for API connections, authentication, webhooks, and data synchronization.
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
        return "integration"

    @property
    def description(self) -> str:
        return "Configures system integrations, API connections, and authentication mechanisms for applications."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "integration_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return ["api_configs", "auth_configs", "webhook_configs", "sync_configs", "connector_specs"]

    @property
    def state_class(self) -> Type[AppBuilderState]:
        return AppBuilderState

    def get_system_prompt(self) -> str:
        return INTEGRATION_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for integration configuration."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for integration configuration."""
        graph = StateGraph(AppBuilderState)

        # Add nodes
        graph.add_node("analyze_requirements", self._analyze_requirements)
        graph.add_node("design_api_configs", self._design_api_configs)
        graph.add_node("design_auth_configs", self._design_auth_configs)
        graph.add_node("design_webhooks", self._design_webhooks)
        graph.add_node("design_sync_strategies", self._design_sync_strategies)
        graph.add_node("compile_integrations", self._compile_integrations)
        graph.add_node("validate_integrations", self._validate_integrations)

        # Define edges
        graph.set_entry_point("analyze_requirements")
        graph.add_edge("analyze_requirements", "design_api_configs")
        graph.add_edge("design_api_configs", "design_auth_configs")
        graph.add_edge("design_auth_configs", "design_webhooks")
        graph.add_edge("design_webhooks", "design_sync_strategies")
        graph.add_edge("design_sync_strategies", "compile_integrations")
        graph.add_edge("compile_integrations", "validate_integrations")
        graph.add_conditional_edges(
            "validate_integrations",
            self._should_refine,
            {
                "refine": "design_api_configs",
                "complete": END
            }
        )

        return graph

    async def _analyze_requirements(self, state: AppBuilderState) -> Dict[str, Any]:
        """Analyze integration requirements."""
        context = state.get("agent_context", {})
        ontology_schema = context.get("ontology_schema", {})
        integration_requirements = context.get("integration_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following ontology and requirements to identify integration needs.

Ontology Schema:
{ontology_schema}

Integration Requirements:
{integration_requirements}

Identify:
1. External systems to integrate with
2. Data flows (inbound and outbound)
3. Authentication requirements per system
4. Real-time vs batch synchronization needs
5. Webhook requirements (events to publish/subscribe)
6. Rate limiting and quota considerations
7. Error handling and retry requirements
8. Security and compliance constraints

Provide a structured analysis of all integration needs.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="integration_analysis",
            description="Analyzed integration requirements",
            confidence=0.85,
            reasoning="Identified external systems, data flows, and integration patterns"
        )

        return {
            "outputs": {"integration_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_requirements",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_api_configs(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design API endpoint configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("integration_analysis", "")
        ontology_schema = context.get("ontology_schema", {})

        # Include validation feedback if present
        validation_feedback = outputs.get("validation_feedback", "")
        feedback_prompt = f"\n\nPrevious validation feedback to address:\n{validation_feedback}" if validation_feedback else ""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design API endpoint configurations for identified integrations.

Integration Analysis:
{analysis}

Ontology Schema:
{ontology_schema}
{feedback_prompt}

For each API integration, specify:
1. Connection Configuration:
   - Base URL (with environment variable support)
   - Default headers
   - Timeout settings
   - Connection pool size
2. Endpoint Definitions:
   - Path template
   - HTTP method
   - Request body schema
   - Response schema
   - Query parameters
   - Path parameters
3. Error Handling:
   - Retry policy (count, backoff)
   - Circuit breaker settings
   - Fallback behavior
   - Error mapping
4. Rate Limiting:
   - Requests per second/minute
   - Burst allowance
   - Quota tracking
5. Caching:
   - Cache TTL
   - Cache keys
   - Invalidation triggers
6. Transformation:
   - Request transformation
   - Response transformation
   - Field mapping

Output as structured JSON API configurations.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="api_config_design",
            description="Designed API endpoint configurations",
            confidence=0.85,
            reasoning="Created API configs with endpoints, error handling, and rate limiting"
        )

        return {
            "outputs": {"api_configs": response.content},
            "decisions": [decision],
            "current_step": "design_api_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_auth_configs(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design authentication configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("integration_analysis", "")
        api_configs = outputs.get("api_configs", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design authentication configurations for all integrations.

Integration Analysis:
{analysis}

API Configurations:
{api_configs}

For each authentication requirement, specify:
1. OAuth 2.0 Configuration:
   - Grant type (authorization_code, client_credentials, etc.)
   - Authorization URL
   - Token URL
   - Scopes required
   - Client ID/Secret storage (env vars, secrets manager)
   - Token refresh handling
   - PKCE support
2. API Key Configuration:
   - Key location (header, query, body)
   - Key name
   - Key storage reference
   - Rotation policy
3. JWT Configuration:
   - Token generation parameters
   - Signing algorithm
   - Claims mapping
   - Expiration settings
   - Refresh token handling
4. Basic Auth Configuration:
   - Credential storage
   - Encoding requirements
5. mTLS Configuration:
   - Certificate paths
   - Key paths
   - CA bundle
   - Certificate rotation
6. Security Best Practices:
   - Secret rotation schedule
   - Audit logging
   - Access control
   - Encryption at rest

Output as structured JSON authentication configurations.
IMPORTANT: Use placeholder references for actual secrets (e.g., ${{secrets.api_key}}), never include actual credentials.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="auth_config_design",
            description="Designed authentication configurations",
            confidence=0.85,
            reasoning="Created secure auth configs with proper secret management"
        )

        return {
            "outputs": {"auth_configs": response.content},
            "decisions": [decision],
            "current_step": "design_auth_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_webhooks(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design webhook configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("integration_analysis", "")
        ontology_schema = context.get("ontology_schema", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design webhook configurations for event-driven integrations.

Integration Analysis:
{analysis}

Ontology Schema:
{ontology_schema}

For inbound webhooks, specify:
1. Endpoint Configuration:
   - Path pattern
   - HTTP methods allowed
   - Request validation schema
   - Authentication (signature verification, API key)
2. Event Processing:
   - Event type mapping
   - Payload transformation
   - Entity mapping
   - Idempotency handling
3. Response Handling:
   - Success response
   - Error responses
   - Async acknowledgment

For outbound webhooks, specify:
1. Subscription Configuration:
   - Event types to publish
   - Target URL (configurable per subscriber)
   - HTTP method
   - Headers
2. Payload Configuration:
   - Event payload schema
   - Data filtering (what to include)
   - Payload signing (HMAC)
3. Delivery Configuration:
   - Retry policy
   - Timeout settings
   - Dead letter handling
   - Delivery confirmation
4. Management:
   - Subscription registration
   - Health monitoring
   - Pause/resume support

Output as structured JSON webhook configurations.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="webhook_design",
            description="Designed webhook configurations",
            confidence=0.85,
            reasoning="Created inbound/outbound webhook specs with security and retry handling"
        )

        return {
            "outputs": {"webhook_configs": response.content},
            "decisions": [decision],
            "current_step": "design_webhooks",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _design_sync_strategies(self, state: AppBuilderState) -> Dict[str, Any]:
        """Design data synchronization strategies."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("integration_analysis", "")
        ontology_schema = context.get("ontology_schema", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Design data synchronization strategies for integrations.

Integration Analysis:
{analysis}

Ontology Schema:
{ontology_schema}

For each data synchronization need, specify:
1. Sync Strategy:
   - Type: real-time, near-real-time, batch
   - Direction: inbound, outbound, bidirectional
   - Frequency/trigger
2. Data Mapping:
   - Source fields to target fields
   - Transformation rules
   - Default values
   - Validation rules
3. Conflict Resolution:
   - Strategy: last-write-wins, merge, manual
   - Version tracking
   - Conflict detection
   - Resolution workflow
4. Change Detection:
   - Method: polling, CDC, events
   - Checkpoint management
   - Incremental vs full sync
5. Batch Processing:
   - Batch size
   - Parallelism
   - Ordering requirements
   - Transaction boundaries
6. Error Handling:
   - Failed record handling
   - Partial success behavior
   - Rollback capability
   - Dead letter queue
7. Monitoring:
   - Sync status tracking
   - Lag monitoring
   - Data quality checks
   - Alerts and notifications

Output as structured JSON synchronization configurations.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="sync_strategy_design",
            description="Designed data synchronization strategies",
            confidence=0.85,
            reasoning="Created sync configs with conflict resolution and error handling"
        )

        return {
            "outputs": {"sync_configs": response.content},
            "decisions": [decision],
            "current_step": "design_sync_strategies",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _compile_integrations(self, state: AppBuilderState) -> Dict[str, Any]:
        """Compile complete integration specifications."""
        outputs = state.get("outputs", {})

        api_configs = outputs.get("api_configs", "")
        auth_configs = outputs.get("auth_configs", "")
        webhook_configs = outputs.get("webhook_configs", "")
        sync_configs = outputs.get("sync_configs", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Compile complete integration specifications from all designed components.

API Configurations:
{api_configs}

Authentication Configurations:
{auth_configs}

Webhook Configurations:
{webhook_configs}

Synchronization Configurations:
{sync_configs}

Create a comprehensive integration specification that includes:
1. Integration Registry:
   - All integrations with metadata
   - Dependencies between integrations
   - Health check endpoints
2. Connector Specifications:
   - Unified connector interface
   - Per-integration connector config
   - Connection pooling
3. Environment Configuration:
   - Environment-specific overrides
   - Feature flags
   - Configuration validation
4. Monitoring Setup:
   - Metrics to collect
   - Log formats
   - Trace propagation
   - Dashboard definitions
5. Security Summary:
   - Secrets required
   - Certificate requirements
   - Network policies
   - Compliance requirements
6. Operational Runbook:
   - Health check procedures
   - Troubleshooting guides
   - Recovery procedures

Output as a comprehensive JSON integration specification document.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="integration_compilation",
            description="Compiled complete integration specifications",
            confidence=0.85,
            reasoning="Combined all integration configs into comprehensive specification"
        )

        # Store integrations in the state
        integrations = {
            "api_configs": api_configs,
            "auth_configs": auth_configs,
            "webhook_configs": webhook_configs,
            "sync_configs": sync_configs,
            "connector_specs": response.content
        }

        return {
            "outputs": {"connector_specs": response.content},
            "integrations": integrations,
            "decisions": [decision],
            "current_step": "compile_integrations",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_integrations(self, state: AppBuilderState) -> Dict[str, Any]:
        """Validate the compiled integration specifications."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        connector_specs = outputs.get("connector_specs", "")
        integration_requirements = context.get("integration_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the compiled integration specifications.

Integration Specifications:
{connector_specs}

Original Requirements:
{integration_requirements}

Validate:
1. Completeness:
   - All required integrations are configured
   - All data flows are addressed
   - All authentication is specified
2. Security:
   - No hardcoded credentials
   - Proper secret management
   - TLS/encryption configured
   - Authorization checks in place
3. Resilience:
   - Retry policies defined
   - Circuit breakers configured
   - Fallback behavior specified
   - Error handling complete
4. Performance:
   - Rate limiting appropriate
   - Caching configured where beneficial
   - Connection pooling set up
   - Batch sizes reasonable
5. Observability:
   - Logging configured
   - Metrics defined
   - Tracing enabled
   - Alerts specified
6. Maintainability:
   - Configuration is environment-aware
   - Documentation is complete
   - Runbooks are actionable

Provide:
1. Validation status (PASS/FAIL)
2. Security assessment
3. List of issues found
4. Recommendations
5. Confidence score (0-1)""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        needs_refinement = "fail" in response_lower or "issue" in response_lower or "security" in response_lower and "concern" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="integration_validation",
            description="Validated integration specifications",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            review_items.append(mark_for_review(
                state,
                item_type="integration_configs",
                item_id="validation_issues",
                description="Integration configurations have issues that may need review",
                priority="high" if "security" in response_lower else "medium"
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
            "current_step": "validate_integrations",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: AppBuilderState) -> str:
        """Determine if integrations need refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"
