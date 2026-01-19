"""
Integration tests for base agent implementation.

Tests agent lifecycle, workflow execution, and LLM integration
with mock LLM services.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List, Optional
import json

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver


pytestmark = pytest.mark.integration


class TestAgentLifecycle:
    """Tests for agent lifecycle management."""

    @pytest.mark.asyncio
    async def test_agent_creation_with_mock_llm(self, mock_llm, mock_memory_saver):
        """Test creating an agent with mock LLM."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState
        from contracts.agent_interface import AgentInput

        class TestAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "test_agent"

            @property
            def description(self) -> str:
                return "A test agent for integration testing"

            @property
            def required_inputs(self) -> List[str]:
                return ["test_data"]

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process_node(state: AgentState) -> Dict[str, Any]:
                    return {"outputs": {"result": "processed"}, "current_step": "done"}

                graph.add_node("process", process_node)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = TestAgent(llm=mock_llm, memory=mock_memory_saver)

        assert agent.name == "test_agent"
        assert agent.llm is mock_llm
        assert agent.memory is mock_memory_saver

    @pytest.mark.asyncio
    async def test_agent_graph_compilation(self, mock_llm, mock_memory_saver):
        """Test that agent graph compiles successfully."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class CompileTestAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "compile_test_agent"

            @property
            def description(self) -> str:
                return "Test agent for compilation"

            @property
            def required_inputs(self) -> List[str]:
                return []

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def step1(state: AgentState) -> Dict[str, Any]:
                    return {"current_step": "step1_done"}

                async def step2(state: AgentState) -> Dict[str, Any]:
                    return {"outputs": {"result": "complete"}, "current_step": "done"}

                graph.add_node("step1", step1)
                graph.add_node("step2", step2)
                graph.set_entry_point("step1")
                graph.add_edge("step1", "step2")
                graph.add_edge("step2", END)

                return graph

        agent = CompileTestAgent(llm=mock_llm, memory=mock_memory_saver)
        compiled = agent.compile()

        assert compiled is not None

    @pytest.mark.asyncio
    async def test_agent_input_validation(self, mock_llm, agent_input_factory):
        """Test agent input validation."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class ValidationTestAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "validation_test_agent"

            @property
            def description(self) -> str:
                return "Test agent for validation"

            @property
            def required_inputs(self) -> List[str]:
                return ["required_field_1", "required_field_2"]

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    return {"outputs": {"result": "ok"}}

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = ValidationTestAgent(llm=mock_llm)

        # Test with missing required inputs
        input_missing = agent_input_factory(context={"other_field": "value"})
        is_valid = await agent.validate_input(input_missing)
        assert is_valid is False

        # Test with all required inputs
        input_complete = agent_input_factory(context={
            "required_field_1": "value1",
            "required_field_2": "value2"
        })
        is_valid = await agent.validate_input(input_complete)
        assert is_valid is True


class TestAgentExecution:
    """Tests for agent execution."""

    @pytest.mark.asyncio
    async def test_agent_run_success(self, mock_llm, agent_input_factory):
        """Test successful agent execution."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class ExecutionTestAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "execution_test_agent"

            @property
            def description(self) -> str:
                return "Test agent for execution"

            @property
            def required_inputs(self) -> List[str]:
                return ["input_data"]

            @property
            def output_keys(self) -> List[str]:
                return ["processed_data"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    context = state.get("agent_context", {})
                    input_data = context.get("input_data", "")
                    return {
                        "outputs": {"processed_data": f"processed: {input_data}"},
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = ExecutionTestAgent(llm=mock_llm)

        input_data = agent_input_factory(context={"input_data": "test_value"})
        output = await agent.run(input_data)

        assert output.success is True
        assert output.agent_name == "execution_test_agent"
        assert "processed_data" in output.outputs

    @pytest.mark.asyncio
    async def test_agent_run_with_missing_inputs(self, mock_llm, agent_input_factory):
        """Test agent execution with missing required inputs."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class MissingInputAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "missing_input_agent"

            @property
            def description(self) -> str:
                return "Test agent for missing inputs"

            @property
            def required_inputs(self) -> List[str]:
                return ["required_field"]

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    return {"outputs": {"result": "ok"}}

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = MissingInputAgent(llm=mock_llm)

        input_data = agent_input_factory(context={"other_field": "value"})
        output = await agent.run(input_data)

        assert output.success is False
        assert len(output.errors) > 0
        assert "Missing required inputs" in output.errors[0]

    @pytest.mark.asyncio
    async def test_agent_run_with_human_review(self, mock_llm, agent_input_factory):
        """Test agent execution that requires human review."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class ReviewAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "review_agent"

            @property
            def description(self) -> str:
                return "Test agent that requires review"

            @property
            def required_inputs(self) -> List[str]:
                return ["data"]

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are a test agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    return {
                        "outputs": {"result": "needs_review"},
                        "requires_human_review": True,
                        "review_items": [
                            {"type": "data_quality", "description": "Review needed"}
                        ],
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = ReviewAgent(llm=mock_llm)

        input_data = agent_input_factory(context={"data": "test"})
        output = await agent.run(input_data)

        assert output.success is True
        assert output.requires_human_review is True
        assert len(output.review_items) > 0


class TestAgentWithLLMInteraction:
    """Tests for agent LLM interaction."""

    @pytest.mark.asyncio
    async def test_agent_llm_invocation(self, mock_llm, agent_input_factory):
        """Test agent invoking the LLM."""
        from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
        from agent_framework.state_management import AgentState

        class LLMAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "llm_agent"

            @property
            def description(self) -> str:
                return "Test agent with LLM calls"

            @property
            def required_inputs(self) -> List[str]:
                return ["prompt"]

            @property
            def output_keys(self) -> List[str]:
                return ["llm_response"]

            def get_system_prompt(self) -> str:
                return "You are a helpful assistant."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def invoke_llm(state: AgentState) -> Dict[str, Any]:
                    context = state.get("agent_context", {})
                    prompt = context.get("prompt", "")

                    from langchain_core.messages import HumanMessage, SystemMessage

                    messages = [
                        SystemMessage(content=self.get_system_prompt()),
                        HumanMessage(content=prompt)
                    ]

                    response = await self.llm.ainvoke(messages)

                    return {
                        "outputs": {"llm_response": response.content},
                        "current_step": "done"
                    }

                graph.add_node("invoke_llm", invoke_llm)
                graph.set_entry_point("invoke_llm")
                graph.add_edge("invoke_llm", END)

                return graph

        agent = LLMAgent(llm=mock_llm)

        input_data = agent_input_factory(context={"prompt": "Hello, world!"})
        output = await agent.run(input_data)

        assert output.success is True
        assert "llm_response" in output.outputs
        assert len(mock_llm.call_history) > 0

    @pytest.mark.asyncio
    async def test_agent_with_custom_llm_responses(
        self,
        mock_llm_with_custom_responses,
        agent_input_factory
    ):
        """Test agent with custom LLM response patterns."""
        custom_llm = mock_llm_with_custom_responses({
            "analyze": '{"analysis": "Custom analysis result", "confidence": 0.95}',
            "summarize": '{"summary": "Brief summary of content"}',
        })

        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class CustomResponseAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "custom_response_agent"

            @property
            def description(self) -> str:
                return "Agent with custom responses"

            @property
            def required_inputs(self) -> List[str]:
                return ["task_type"]

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are an analysis agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    context = state.get("agent_context", {})
                    task_type = context.get("task_type", "analyze")

                    from langchain_core.messages import HumanMessage

                    response = await self.llm.ainvoke([
                        HumanMessage(content=f"Please {task_type} this data")
                    ])

                    try:
                        result = json.loads(response.content)
                    except json.JSONDecodeError:
                        result = {"raw": response.content}

                    return {
                        "outputs": {"result": result},
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = CustomResponseAgent(llm=custom_llm)

        # Test with "analyze" task
        input_data = agent_input_factory(context={"task_type": "analyze"})
        output = await agent.run(input_data)

        assert output.success is True
        assert "result" in output.outputs
        if isinstance(output.outputs["result"], dict):
            assert output.outputs["result"].get("confidence") == 0.95


class TestAgentDecisions:
    """Tests for agent decision tracking."""

    @pytest.mark.asyncio
    async def test_agent_records_decisions(self, mock_llm, agent_input_factory):
        """Test that agent records decisions."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState, Decision, add_decision

        class DecisionAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "decision_agent"

            @property
            def description(self) -> str:
                return "Agent that makes decisions"

            @property
            def required_inputs(self) -> List[str]:
                return ["data"]

            @property
            def output_keys(self) -> List[str]:
                return ["decision"]

            def get_system_prompt(self) -> str:
                return "You are a decision-making agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def make_decision(state: AgentState) -> Dict[str, Any]:
                    decision = Decision(
                        decision_type="data_classification",
                        description="Classified data as type A",
                        confidence=0.85,
                        reasoning="Based on pattern matching"
                    )

                    return {
                        "outputs": {"decision": "type_A"},
                        "decisions": [decision],
                        "current_step": "done"
                    }

                graph.add_node("decide", make_decision)
                graph.set_entry_point("decide")
                graph.add_edge("decide", END)

                return graph

        agent = DecisionAgent(llm=mock_llm)

        input_data = agent_input_factory(context={"data": "test_data"})
        output = await agent.run(input_data)

        assert output.success is True
        assert len(output.decisions) > 0
        assert output.confidence > 0

    @pytest.mark.asyncio
    async def test_agent_confidence_calculation(self, mock_llm, agent_input_factory):
        """Test agent confidence score calculation."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState, Decision

        class MultiDecisionAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "multi_decision_agent"

            @property
            def description(self) -> str:
                return "Agent with multiple decisions"

            @property
            def required_inputs(self) -> List[str]:
                return []

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are an agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def process(state: AgentState) -> Dict[str, Any]:
                    decisions = [
                        Decision(
                            decision_type="step1",
                            description="First decision",
                            confidence=0.9,
                            reasoning="High confidence"
                        ),
                        Decision(
                            decision_type="step2",
                            description="Second decision",
                            confidence=0.7,
                            reasoning="Medium confidence"
                        ),
                        Decision(
                            decision_type="step3",
                            description="Third decision",
                            confidence=0.8,
                            reasoning="Good confidence"
                        ),
                    ]

                    return {
                        "outputs": {"result": "complete"},
                        "decisions": decisions,
                        "current_step": "done"
                    }

                graph.add_node("process", process)
                graph.set_entry_point("process")
                graph.add_edge("process", END)

                return graph

        agent = MultiDecisionAgent(llm=mock_llm)

        input_data = agent_input_factory()
        output = await agent.run(input_data)

        # Average of 0.9, 0.7, 0.8 = 0.8
        assert 0.75 <= output.confidence <= 0.85


class TestAgentErrorHandling:
    """Tests for agent error handling."""

    @pytest.mark.asyncio
    async def test_agent_handles_workflow_exception(self, mock_llm, agent_input_factory):
        """Test that agent handles exceptions in workflow."""
        from agent_framework.base_agent import BaseOpenForgeAgent
        from agent_framework.state_management import AgentState

        class FailingAgent(BaseOpenForgeAgent):
            @property
            def name(self) -> str:
                return "failing_agent"

            @property
            def description(self) -> str:
                return "Agent that fails"

            @property
            def required_inputs(self) -> List[str]:
                return []

            @property
            def output_keys(self) -> List[str]:
                return ["result"]

            def get_system_prompt(self) -> str:
                return "You are an agent."

            def build_graph(self) -> StateGraph:
                graph = StateGraph(AgentState)

                async def fail_node(state: AgentState) -> Dict[str, Any]:
                    raise ValueError("Intentional failure for testing")

                graph.add_node("fail", fail_node)
                graph.set_entry_point("fail")
                graph.add_edge("fail", END)

                return graph

        agent = FailingAgent(llm=mock_llm)

        input_data = agent_input_factory()
        output = await agent.run(input_data)

        assert output.success is False
        assert len(output.errors) > 0
        assert output.requires_human_review is True
