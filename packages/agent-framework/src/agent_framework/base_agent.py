"""
Base agent implementation using LangGraph.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from contracts.agent_interface import AgentInput, AgentOutput, SpecialistAgent
from agent_framework.state_management import AgentState, create_initial_state, Decision
from core.observability.tracing import traced, get_tracer

tracer = get_tracer(__name__)


class BaseOpenForgeAgent(SpecialistAgent, ABC):
    """
    Base class for Open Forge agents using LangGraph.

    Provides:
    - LangGraph workflow construction
    - State management
    - Tool integration
    - Observability/tracing
    - Memory persistence
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.llm = llm
        self.memory = memory or MemorySaver()
        self.config = config or {}
        self._graph: Optional[StateGraph] = None
        self._compiled_graph = None

    @property
    @abstractmethod
    def name(self) -> str:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass

    @property
    @abstractmethod
    def required_inputs(self) -> List[str]:
        pass

    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        pass

    @property
    def state_class(self) -> Type[AgentState]:
        """Override to use custom state class."""
        return AgentState

    @abstractmethod
    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for this agent."""
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        pass

    def get_graph(self) -> StateGraph:
        """Get or build the agent graph."""
        if self._graph is None:
            self._graph = self.build_graph()
        return self._graph

    def compile(self):
        """Compile the graph for execution."""
        if self._compiled_graph is None:
            graph = self.get_graph()
            self._compiled_graph = graph.compile(checkpointer=self.memory)
        return self._compiled_graph

    async def validate_input(self, input: AgentInput) -> bool:
        """Validate that input has all required data."""
        for key in self.required_inputs:
            if key not in input.context:
                return False
        return True

    @traced()
    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute the agent workflow."""
        if not await self.validate_input(input):
            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=False,
                outputs={},
                decisions=[],
                confidence=0.0,
                requires_human_review=False,
                errors=[f"Missing required inputs: {self.required_inputs}"]
            )

        # Create initial state
        initial_state = create_initial_state(
            engagement_id=input.engagement_id,
            phase=input.phase,
            context=input.context
        )

        # Add previous outputs and human inputs to context
        if input.previous_outputs:
            initial_state["agent_context"]["previous_outputs"] = input.previous_outputs
        if input.human_inputs:
            initial_state["agent_context"]["human_inputs"] = input.human_inputs

        # Run the graph
        compiled = self.compile()
        config = {"configurable": {"thread_id": input.engagement_id}}

        try:
            final_state = await compiled.ainvoke(initial_state, config)

            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=len(final_state.get("errors", [])) == 0,
                outputs=final_state.get("outputs", {}),
                decisions=[d.model_dump() for d in final_state.get("decisions", [])],
                confidence=self._calculate_confidence(final_state),
                requires_human_review=final_state.get("requires_human_review", False),
                review_items=final_state.get("review_items", []),
                next_suggested_action=self._get_next_action(final_state),
                errors=final_state.get("errors", [])
            )
        except Exception as e:
            return AgentOutput(
                agent_name=self.name,
                timestamp=datetime.utcnow(),
                success=False,
                outputs={},
                decisions=[],
                confidence=0.0,
                requires_human_review=True,
                review_items=[{
                    "type": "error",
                    "description": f"Agent execution failed: {str(e)}",
                    "priority": "high"
                }],
                errors=[str(e)]
            )

    def _calculate_confidence(self, state: AgentState) -> float:
        """Calculate overall confidence from decisions."""
        decisions = state.get("decisions", [])
        if not decisions:
            return 0.0
        return sum(d.confidence for d in decisions) / len(decisions)

    def _get_next_action(self, state: AgentState) -> Optional[str]:
        """Determine suggested next action based on state."""
        if state.get("requires_human_review"):
            return "await_human_review"
        if state.get("errors"):
            return "handle_errors"
        return None

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses. Override in subclasses."""
        return []


class NodeBuilder:
    """Helper class to build LangGraph nodes."""

    @staticmethod
    def llm_node(llm: BaseChatModel, system_prompt: str):
        """Create an LLM invocation node."""
        async def node(state: AgentState) -> Dict[str, Any]:
            messages = [SystemMessage(content=system_prompt)]
            for msg in state.get("messages", []):
                if msg.role == "user":
                    messages.append(HumanMessage(content=msg.content))
                else:
                    messages.append(AIMessage(content=msg.content))

            response = await llm.ainvoke(messages)
            return {"messages": [{"role": "assistant", "content": response.content}]}

        return node

    @staticmethod
    def tool_node(tools: List[Any]):
        """Create a tool execution node."""
        async def node(state: AgentState) -> Dict[str, Any]:
            # Tool execution logic
            results = {}
            for tool in tools:
                if hasattr(tool, "should_run") and tool.should_run(state):
                    result = await tool.arun(state)
                    results[tool.name] = result
            return {"outputs": results}

        return node

    @staticmethod
    def decision_node(decision_fn):
        """Create a decision/routing node."""
        async def node(state: AgentState) -> str:
            return await decision_fn(state)

        return node
