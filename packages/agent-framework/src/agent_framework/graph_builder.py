"""
LangGraph workflow construction utilities.
"""
from typing import Callable, Dict, List, Optional, Any, Type
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.state_management import AgentState


class WorkflowBuilder:
    """
    Fluent builder for LangGraph workflows.

    Example:
        builder = WorkflowBuilder(DiscoveryState)
        graph = (builder
            .add_node("analyze", analyze_node)
            .add_node("validate", validate_node)
            .add_node("review", review_node)
            .set_entry("analyze")
            .add_edge("analyze", "validate")
            .add_conditional("validate", route_validation)
            .build())
    """

    def __init__(self, state_class: Type[AgentState] = AgentState):
        self.state_class = state_class
        self._graph = StateGraph(state_class)
        self._entry_point: Optional[str] = None
        self._nodes: Dict[str, Callable] = {}
        self._edges: List[tuple] = []
        self._conditional_edges: List[tuple] = []

    def add_node(self, name: str, node_fn: Callable) -> "WorkflowBuilder":
        """Add a node to the graph."""
        self._nodes[name] = node_fn
        self._graph.add_node(name, node_fn)
        return self

    def set_entry(self, node_name: str) -> "WorkflowBuilder":
        """Set the entry point of the graph."""
        self._entry_point = node_name
        self._graph.set_entry_point(node_name)
        return self

    def add_edge(self, from_node: str, to_node: str) -> "WorkflowBuilder":
        """Add a direct edge between nodes."""
        self._edges.append((from_node, to_node))
        if to_node == "END":
            self._graph.add_edge(from_node, END)
        else:
            self._graph.add_edge(from_node, to_node)
        return self

    def add_conditional(
        self,
        from_node: str,
        condition_fn: Callable[[AgentState], str],
        route_map: Optional[Dict[str, str]] = None
    ) -> "WorkflowBuilder":
        """Add a conditional edge based on a routing function."""
        self._conditional_edges.append((from_node, condition_fn, route_map))

        if route_map:
            # Map includes END handling
            mapped_routes = {}
            for key, target in route_map.items():
                mapped_routes[key] = END if target == "END" else target
            self._graph.add_conditional_edges(from_node, condition_fn, mapped_routes)
        else:
            self._graph.add_conditional_edges(from_node, condition_fn)

        return self

    def build(self) -> StateGraph:
        """Build and return the graph."""
        if not self._entry_point:
            raise ValueError("Entry point not set. Call set_entry() first.")
        return self._graph

    def compile(self, checkpointer: Optional[MemorySaver] = None):
        """Build and compile the graph."""
        graph = self.build()
        return graph.compile(checkpointer=checkpointer)


def create_approval_subgraph() -> StateGraph:
    """
    Create a reusable approval workflow subgraph.

    Flow:
    1. Request approval
    2. Wait for response
    3. Route based on approval/rejection
    """

    async def request_approval(state: AgentState) -> Dict[str, Any]:
        """Mark state as requiring approval."""
        return {
            "requires_human_review": True,
            "current_step": "awaiting_approval"
        }

    async def check_approval(state: AgentState) -> str:
        """Check if approval was granted."""
        context = state.get("agent_context", {})
        human_inputs = context.get("human_inputs", [])

        for input_item in human_inputs:
            if input_item.get("type") == "approval_response":
                if input_item.get("approved"):
                    return "approved"
                return "rejected"

        return "pending"

    async def handle_approved(state: AgentState) -> Dict[str, Any]:
        return {
            "requires_human_review": False,
            "current_step": "approved"
        }

    async def handle_rejected(state: AgentState) -> Dict[str, Any]:
        return {
            "requires_human_review": False,
            "current_step": "rejected",
            "errors": ["Approval was rejected"]
        }

    builder = WorkflowBuilder(AgentState)
    graph = (builder
        .add_node("request_approval", request_approval)
        .add_node("approved", handle_approved)
        .add_node("rejected", handle_rejected)
        .set_entry("request_approval")
        .add_conditional("request_approval", check_approval, {
            "approved": "approved",
            "rejected": "rejected",
            "pending": "END"
        })
        .add_edge("approved", "END")
        .add_edge("rejected", "END")
        .build())

    return graph


def create_retry_wrapper(
    node_fn: Callable,
    max_retries: int = 3,
    retry_on_errors: Optional[List[Type[Exception]]] = None
) -> Callable:
    """
    Wrap a node function with retry logic.
    """
    retry_errors = retry_on_errors or [Exception]

    async def wrapped(state: AgentState) -> Dict[str, Any]:
        last_error = None
        for attempt in range(max_retries):
            try:
                return await node_fn(state)
            except tuple(retry_errors) as e:
                last_error = e
                if attempt < max_retries - 1:
                    continue

        return {
            "errors": [f"Node failed after {max_retries} attempts: {str(last_error)}"]
        }

    return wrapped
