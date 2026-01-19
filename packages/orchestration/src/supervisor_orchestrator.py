"""
Supervisor Orchestrator using LangGraph's create_supervisor pattern.

This module provides a high-level orchestrator that coordinates specialist agents
(Discovery, Data Architect, App Builder, Operations, Enablement) using the
LangGraph supervisor pattern with PostgreSQL-backed persistence.
"""
from typing import Dict, Any, List, Optional, Union
import logging
from functools import cached_property

from langchain_core.language_models import BaseChatModel
from langgraph.prebuilt import create_supervisor
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore
from langgraph.graph import CompiledGraph

logger = logging.getLogger(__name__)


# Supervisor system prompt for routing decisions
SUPERVISOR_SYSTEM_PROMPT = """You are the Open Forge Orchestrator, responsible for coordinating specialist agents to build enterprise data solutions.

## Available Specialist Agents:

1. **discovery_agent** - Use for:
   - Initial stakeholder interviews and requirements gathering
   - Data source discovery and catalog building
   - Business process analysis
   - Understanding client needs and context

2. **data_architect_agent** - Use for:
   - Ontology and schema design
   - Data model creation (LinkML schemas)
   - ETL specification development
   - Schema validation and refinement

3. **app_builder_agent** - Use for:
   - UI component generation
   - Workflow automation design
   - Integration configuration
   - Deployment manifest creation

4. **operations_agent** - Use for:
   - Monitoring configuration (Prometheus, Grafana)
   - Scaling and load balancing setup
   - Maintenance and backup strategies
   - Incident playbooks and runbooks

5. **enablement_agent** - Use for:
   - Documentation generation (API docs, user guides)
   - Training material creation
   - FAQ and troubleshooting guides
   - Knowledge base articles

## Routing Guidelines:

- Start new engagements with **discovery_agent** to understand requirements
- After discovery, route to **data_architect_agent** for schema design
- Once schema is validated, use **app_builder_agent** for application specs
- Use **operations_agent** for infrastructure and monitoring setup
- Use **enablement_agent** for documentation and training materials
- Multiple agents can work on different aspects in parallel when appropriate

## Output Format:

When routing, consider:
1. The current phase of the engagement
2. What information is available vs. needed
3. Dependencies between agent outputs
4. Whether human review is required before proceeding

Route to the most appropriate agent based on the user's request and current context.
"""


class SupervisorOrchestrator:
    """
    Supervisor-based orchestrator for coordinating Open Forge specialist agents.

    Uses LangGraph's create_supervisor pattern to intelligently route requests
    to the appropriate specialist agent based on context and engagement phase.

    Example:
        orchestrator = SupervisorOrchestrator(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str)
        )

        result = await orchestrator.invoke(
            "Start a discovery session for Acme Corp's data platform",
            engagement_id="eng_123",
            thread_id="thread_1"
        )
    """

    def __init__(
        self,
        llm: BaseChatModel,
        checkpointer: PostgresSaver,
        store: PostgresStore,
        agents: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        output_mode: str = "last_message",
    ):
        """
        Initialize the Supervisor Orchestrator.

        Args:
            llm: The language model for supervisor routing decisions
            checkpointer: PostgresSaver for short-term thread checkpoints
            store: PostgresStore for long-term cross-thread memory
            agents: Optional dict of agent_name -> agent instances.
                    If not provided, agents must be registered before compilation.
            system_prompt: Optional custom system prompt for the supervisor.
                          Defaults to SUPERVISOR_SYSTEM_PROMPT.
            output_mode: Output mode for supervisor. Options:
                        - "last_message": Return only the final agent response
                        - "full_history": Return complete conversation history
        """
        self.llm = llm
        self.checkpointer = checkpointer
        self.store = store
        self._agents: Dict[str, Any] = agents or {}
        self.system_prompt = system_prompt or SUPERVISOR_SYSTEM_PROMPT
        self.output_mode = output_mode
        self._compiled_supervisor: Optional[CompiledGraph] = None

    def register_agent(self, name: str, agent: Any) -> "SupervisorOrchestrator":
        """
        Register a specialist agent with the supervisor.

        Args:
            name: The name used to route to this agent
            agent: The agent instance (must be a compiled LangGraph graph or
                   have an 'agent' attribute that is a compiled graph)

        Returns:
            self for method chaining
        """
        # Clear compiled supervisor if adding new agents
        if self._compiled_supervisor is not None:
            logger.warning("Adding agent after compilation - supervisor will be recompiled")
            self._compiled_supervisor = None

        self._agents[name] = agent
        logger.info(f"Registered agent: {name}")
        return self

    def register_agents(self, agents: Dict[str, Any]) -> "SupervisorOrchestrator":
        """
        Register multiple agents at once.

        Args:
            agents: Dict mapping agent names to agent instances

        Returns:
            self for method chaining
        """
        for name, agent in agents.items():
            self.register_agent(name, agent)
        return self

    @property
    def agents(self) -> Dict[str, Any]:
        """Get the registered agents."""
        return self._agents.copy()

    def _get_agent_graphs(self) -> List[Any]:
        """
        Extract the compiled graphs from registered agents.

        Returns:
            List of compiled LangGraph graphs
        """
        graphs = []
        for name, agent in self._agents.items():
            # Handle different agent types
            if hasattr(agent, 'agent'):
                # MemoryAwareAgent pattern - has .agent attribute
                graphs.append(agent.agent)
            elif hasattr(agent, 'compile'):
                # Uncompiled graph - compile it
                graphs.append(agent.compile())
            else:
                # Assume it's already a compiled graph
                graphs.append(agent)
        return graphs

    def compile(self) -> CompiledGraph:
        """
        Compile the supervisor graph with all registered agents.

        Returns:
            The compiled supervisor graph

        Raises:
            ValueError: If no agents are registered
        """
        if not self._agents:
            raise ValueError("No agents registered. Register agents before compiling.")

        if self._compiled_supervisor is not None:
            return self._compiled_supervisor

        agent_graphs = self._get_agent_graphs()

        logger.info(f"Compiling supervisor with {len(agent_graphs)} agents")

        # Create the supervisor using LangGraph's prebuilt pattern
        self._compiled_supervisor = create_supervisor(
            agents=agent_graphs,
            model=self.llm,
            prompt=self.system_prompt,
            checkpointer=self.checkpointer,
            output_mode=self.output_mode,
        )

        return self._compiled_supervisor

    async def invoke(
        self,
        input_message: str,
        engagement_id: str,
        thread_id: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke the supervisor orchestrator with a message.

        The supervisor will route to the appropriate specialist agent
        based on the message content and current context.

        Args:
            input_message: The user's input message
            engagement_id: The engagement this request belongs to
            thread_id: Unique identifier for this conversation thread
            additional_context: Optional additional context to include

        Returns:
            The supervisor/agent response including messages and outputs
        """
        supervisor = self.compile()

        config = {
            "configurable": {
                "thread_id": thread_id,
                "engagement_id": engagement_id,
            }
        }

        # Build the input message
        messages = [{"role": "user", "content": input_message}]

        if additional_context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in additional_context.items()
            )
            messages[0]["content"] = f"Context:\n{context_str}\n\nRequest: {input_message}"

        try:
            result = await supervisor.ainvoke(
                {"messages": messages},
                config=config,
            )

            logger.info(
                f"Supervisor completed for engagement={engagement_id}, thread={thread_id}"
            )

            return result
        except Exception as e:
            logger.error(f"Supervisor error: {e}")
            raise

    async def stream(
        self,
        input_message: str,
        engagement_id: str,
        thread_id: str,
        additional_context: Optional[Dict[str, Any]] = None,
    ):
        """
        Stream the supervisor orchestrator execution.

        Args:
            input_message: The user's input message
            engagement_id: The engagement this request belongs to
            thread_id: Unique identifier for this conversation thread
            additional_context: Optional additional context to include

        Yields:
            Streaming events from the supervisor execution
        """
        supervisor = self.compile()

        config = {
            "configurable": {
                "thread_id": thread_id,
                "engagement_id": engagement_id,
            }
        }

        messages = [{"role": "user", "content": input_message}]

        if additional_context:
            context_str = "\n".join(
                f"{k}: {v}" for k, v in additional_context.items()
            )
            messages[0]["content"] = f"Context:\n{context_str}\n\nRequest: {input_message}"

        async for event in supervisor.astream(
            {"messages": messages},
            config=config,
        ):
            yield event

    def get_thread_history(self, thread_id: str) -> List[Dict[str, Any]]:
        """
        Get the conversation history for a specific thread.

        Args:
            thread_id: The thread to get history for

        Returns:
            List of messages in the thread
        """
        config = {"configurable": {"thread_id": thread_id}}
        try:
            state = self.checkpointer.get(config)
            if state and "messages" in state.values:
                return state.values["messages"]
            return []
        except Exception as e:
            logger.error(f"Error getting thread history: {e}")
            return []

    def list_agents(self) -> List[Dict[str, str]]:
        """
        List all registered agents with their metadata.

        Returns:
            List of dicts with agent name, description, and type info
        """
        agent_info = []
        for name, agent in self._agents.items():
            info = {"name": name}

            # Try to get description from agent
            if hasattr(agent, 'description'):
                info["description"] = agent.description
            elif hasattr(agent, 'get_description'):
                info["description"] = agent.get_description()
            else:
                info["description"] = f"Specialist agent: {name}"

            # Get agent type
            info["type"] = type(agent).__name__

            agent_info.append(info)

        return agent_info


def create_supervisor_orchestrator(
    llm: BaseChatModel,
    connection_string: str,
    agents: Optional[Dict[str, Any]] = None,
    system_prompt: Optional[str] = None,
) -> SupervisorOrchestrator:
    """
    Factory function to create a SupervisorOrchestrator with PostgreSQL persistence.

    Args:
        llm: The language model for supervisor routing
        connection_string: PostgreSQL connection string
        agents: Optional dict of agent_name -> agent instances
        system_prompt: Optional custom supervisor prompt

    Returns:
        Configured SupervisorOrchestrator instance
    """
    checkpointer = PostgresSaver.from_conn_string(connection_string)
    store = PostgresStore.from_conn_string(connection_string)

    return SupervisorOrchestrator(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        agents=agents,
        system_prompt=system_prompt,
    )
