"""
Testing utilities for agents.
"""
from typing import Any, Dict, List, Optional, Type
from unittest.mock import AsyncMock, MagicMock
from agent_framework.base_agent import BaseSpecialistAgent, AgentInput, AgentOutput
from datetime import datetime
import pytest

class MockLLM:
    """Mock LLM for testing."""
    
    def __init__(self, responses: List[str] = None):
        self.responses = responses or ["Mock response"]
        self.call_count = 0
        self.call_history: List[Dict] = []
    
    async def ainvoke(self, input: Any) -> MagicMock:
        """Mock async invoke."""
        response = MagicMock()
        response.content = self.responses[self.call_count % len(self.responses)]
        self.call_history.append({"input": input})
        self.call_count += 1
        return response
    
    def invoke(self, input: Any) -> MagicMock:
        """Mock sync invoke."""
        response = MagicMock()
        response.content = self.responses[self.call_count % len(self.responses)]
        self.call_history.append({"input": input})
        self.call_count += 1
        return response

class AgentTestHarness:
    """Test harness for running agent tests."""
    
    def __init__(self, agent_class: Type[BaseSpecialistAgent]):
        self.agent_class = agent_class
        self.agent: Optional[BaseSpecialistAgent] = None
        self.mock_llm: Optional[MockLLM] = None
    
    def setup(self, llm_responses: List[str] = None) -> BaseSpecialistAgent:
        """Set up agent with mocks."""
        self.mock_llm = MockLLM(llm_responses)
        self.agent = self.agent_class()
        self.agent.llm = self.mock_llm
        
        # Mock memory
        self.agent.memory.store_execution = AsyncMock()
        self.agent.memory.get_relevant_context = AsyncMock(return_value=[])
        
        return self.agent
    
    async def run_test(
        self,
        context: Dict[str, Any],
        engagement_id: str = "test-engagement",
        phase: str = "test"
    ) -> AgentOutput:
        """Run a test with the given context."""
        if not self.agent:
            self.setup()
        
        input = AgentInput(
            engagement_id=engagement_id,
            phase=phase,
            context=context
        )
        
        return await self.agent.run(input)
    
    def assert_output_keys(self, output: AgentOutput, expected_keys: List[str]) -> None:
        """Assert that output contains expected keys."""
        for key in expected_keys:
            assert key in output.outputs, f"Missing expected key: {key}"
    
    def assert_success(self, output: AgentOutput) -> None:
        """Assert that the agent run was successful."""
        assert output.success, f"Agent failed with errors: {output.errors}"
    
    def get_llm_calls(self) -> List[Dict]:
        """Get history of LLM calls."""
        return self.mock_llm.call_history if self.mock_llm else []

@pytest.fixture
def agent_harness():
    """Pytest fixture for agent test harness."""
    def _create_harness(agent_class: Type[BaseSpecialistAgent]) -> AgentTestHarness:
        return AgentTestHarness(agent_class)
    return _create_harness