# contracts/agent_interface.py
"""
Agent Interface Contract
All specialist agents MUST implement this interface.
"""
from abc import ABC, abstractmethod
from typing import TypedDict, Any, List, Optional
from pydantic import BaseModel
from datetime import datetime

class AgentInput(BaseModel):
    """Standard input for all agents."""
    engagement_id: str
    phase: str
    context: dict
    previous_outputs: Optional[dict] = None
    human_inputs: Optional[List[dict]] = None

class AgentOutput(BaseModel):
    """Standard output for all agents."""
    agent_name: str
    timestamp: datetime
    success: bool
    outputs: dict
    decisions: List[dict]
    confidence: float
    requires_human_review: bool
    review_items: Optional[List[dict]] = None
    next_suggested_action: Optional[str] = None
    errors: Optional[List[str]] = None

class SpecialistAgent(ABC):
    """Base class for all specialist agents."""
    
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
        """List of required input keys."""
        pass
    
    @property
    @abstractmethod
    def output_keys(self) -> List[str]:
        """List of output keys this agent produces."""
        pass
    
    @abstractmethod
    async def run(self, input: AgentInput) -> AgentOutput:
        """Execute the agent's primary function."""
        pass
    
    @abstractmethod
    async def validate_input(self, input: AgentInput) -> bool:
        """Validate that input has all required data."""
        pass
    
    @abstractmethod
    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        pass