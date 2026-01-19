"""
Base agent class that all specialist agents inherit from.
Implements the SpecialistAgent contract.
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Type
from pydantic import BaseModel
from datetime import datetime
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import BaseTool
from agent_framework.state_management import StateManager
from agent_framework.memory import AgentMemory
from agent_framework.prompts import PromptManager
from core.observability.tracing import traced, get_tracer
from core.config import get_settings
import uuid

settings = get_settings()
tracer = get_tracer(__name__)

class AgentInput(BaseModel):
    """Standard input for all agents."""
    engagement_id: str
    phase: str
    context: Dict[str, Any]
    previous_outputs: Optional[Dict[str, Any]] = None
    human_inputs: Optional[List[Dict[str, Any]]] = None

class AgentOutput(BaseModel):
    """Standard output for all agents."""
    agent_name: str
    run_id: str
    timestamp: datetime
    success: bool
    outputs: Dict[str, Any]
    decisions: List[Dict[str, Any]]
    confidence: float
    requires_human_review: bool
    review_items: Optional[List[Dict[str, Any]]] = None
    next_suggested_action: Optional[str] = None
    errors: Optional[List[str]] = None
    token_usage: Optional[Dict[str, int]] = None

class BaseSpecialistAgent(ABC):
    """
    Base class for all specialist agents.
    Provides common functionality and enforces the contract.
    """
    
    def __init__(
        self,
        model: str = None,
        temperature: float = 0.1,
        max_tokens: int = 16000
    ):
        self.model = model or settings.llm.default_model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        self.llm = ChatAnthropic(
            model=self.model,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            api_key=settings.llm.anthropic_api_key
        )
        
        self.state_manager = StateManager()
        self.memory = AgentMemory()
        self.prompt_manager = PromptManager()
        
        self._tools: List[BaseTool] = []
        self._setup_tools()
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Unique name for this agent."""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Description of what this agent does."""
        pass
    
    @property
    @abstractmethod
    def required_inputs(self) -> List[str]:
        """List of required input keys in context."""
        pass
    
    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        """List of output keys this agent produces."""
        pass
    
    @abstractmethod
    def _setup_tools(self) -> None:
        """Set up tools for this agent."""
        pass
    
    @abstractmethod
    async def _execute(self, input: AgentInput) -> Dict[str, Any]:
        """Execute the agent's core logic. Override in subclasses."""
        pass
    
    def get_tools(self) -> List[BaseTool]:
        """Return list of tools this agent uses."""
        return self._tools
    
    def register_tool(self, tool: BaseTool) -> None:
        """Register a tool for this agent."""
        self._tools.append(tool)
    
    async def validate_input(self, input: AgentInput) -> bool:
        """Validate that input has all required data."""
        for key in self.required_inputs:
            if key not in input.context or input.context[key] is None:
                return False
        return True
    
    @traced()
    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's primary function."""
        run_id = str(uuid.uuid4())
        start_time = datetime.now()
        errors = []
        
        with tracer.start_as_current_span(f"agent.{self.name}.run") as span:
            span.set_attribute("engagement_id", input.engagement_id)
            span.set_attribute("run_id", run_id)
            
            try:
                # Validate input
                if not await self.validate_input(input):
                    missing = [k for k in self.required_inputs if k not in input.context]
                    return AgentOutput(
                        agent_name=self.name,
                        run_id=run_id,
                        timestamp=datetime.now(),
                        success=False,
                        outputs={},
                        decisions=[],
                        confidence=0.0,
                        requires_human_review=True,
                        review_items=[{"type": "missing_input", "keys": missing}],
                        errors=[f"Missing required inputs: {missing}"]
                    )
                
                # Load memory context
                memory_context = await self.memory.get_relevant_context(
                    engagement_id=input.engagement_id,
                    agent_name=self.name
                )
                
                # Execute core logic
                result = await self._execute(input)
                
                # Extract decisions and confidence
                decisions = result.get("decisions", [])
                confidence = result.get("confidence", 0.8)
                requires_review = result.get("requires_human_review", False)
                review_items = result.get("review_items", None)
                
                # Store to memory
                await self.memory.store_execution(
                    engagement_id=input.engagement_id,
                    agent_name=self.name,
                    run_id=run_id,
                    input=input.model_dump(),
                    output=result
                )
                
                return AgentOutput(
                    agent_name=self.name,
                    run_id=run_id,
                    timestamp=datetime.now(),
                    success=True,
                    outputs=result.get("outputs", result),
                    decisions=decisions,
                    confidence=confidence,
                    requires_human_review=requires_review,
                    review_items=review_items,
                    next_suggested_action=result.get("next_action"),
                    token_usage=result.get("token_usage")
                )
                
            except Exception as e:
                span.record_exception(e)
                errors.append(str(e))
                
                return AgentOutput(
                    agent_name=self.name,
                    run_id=run_id,
                    timestamp=datetime.now(),
                    success=False,
                    outputs={},
                    decisions=[],
                    confidence=0.0,
                    requires_human_review=True,
                    review_items=[{"type": "error", "message": str(e)}],
                    errors=errors
                )
    
    def get_prompt(self, prompt_name: str) -> ChatPromptTemplate:
        """Get a prompt template by name."""
        return self.prompt_manager.get_prompt(self.name, prompt_name)
    
    async def invoke_llm(
        self,
        prompt: ChatPromptTemplate,
        variables: Dict[str, Any]
    ) -> str:
        """Invoke the LLM with a prompt."""
        chain = prompt | self.llm
        response = await chain.ainvoke(variables)
        return response.content