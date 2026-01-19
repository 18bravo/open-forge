"""
State management for agent workflows.
Handles persistence and retrieval of engagement state.
"""
from typing import Any, Dict, Optional
from datetime import datetime
from pydantic import BaseModel
from sqlalchemy import text
from core.database.connection import get_async_db
import json

class EngagementState(BaseModel):
    """Full engagement state model - matches the contract schema."""
    engagement_id: str
    customer_name: str
    current_phase: str
    created_at: datetime
    updated_at: datetime
    target_completion: Optional[datetime] = None
    discovery: Optional[Dict[str, Any]] = None
    data_foundation: Optional[Dict[str, Any]] = None
    application: Optional[Dict[str, Any]] = None
    deployment: Optional[Dict[str, Any]] = None
    human_interactions: list = []
    agent_decisions: list = []
    approvals: list = []

class StateManager:
    """Manages engagement state persistence."""
    
    async def create_engagement(
        self,
        engagement_id: str,
        customer_name: str,
        initial_state: Optional[Dict[str, Any]] = None
    ) -> EngagementState:
        """Create a new engagement."""
        now = datetime.now()
        
        state = EngagementState(
            engagement_id=engagement_id,
            customer_name=customer_name,
            current_phase="discovery",
            created_at=now,
            updated_at=now,
            **(initial_state or {})
        )
        
        async with get_async_db() as session:
            await session.execute(text("""
                INSERT INTO engagements.engagements 
                (id, customer_name, current_phase, state, created_at, updated_at)
                VALUES (:id, :customer_name, :phase, :state, :created_at, :updated_at)
            """), {
                "id": engagement_id,
                "customer_name": customer_name,
                "phase": "discovery",
                "state": state.model_dump_json(),
                "created_at": now,
                "updated_at": now
            })
        
        return state
    
    async def get_engagement(self, engagement_id: str) -> Optional[EngagementState]:
        """Get engagement state by ID."""
        async with get_async_db() as session:
            result = await session.execute(text("""
                SELECT state FROM engagements.engagements WHERE id = :id
            """), {"id": engagement_id})
            
            row = result.fetchone()
            if not row:
                return None
            
            return EngagementState.model_validate_json(row[0])
    
    async def update_engagement(
        self,
        engagement_id: str,
        updates: Dict[str, Any]
    ) -> EngagementState:
        """Update engagement state."""
        current = await self.get_engagement(engagement_id)
        if not current:
            raise ValueError(f"Engagement {engagement_id} not found")
        
        # Apply updates
        current_dict = current.model_dump()
        for key, value in updates.items():
            if key in current_dict:
                if isinstance(current_dict[key], dict) and isinstance(value, dict):
                    current_dict[key].update(value)
                elif isinstance(current_dict[key], list) and isinstance(value, list):
                    current_dict[key].extend(value)
                else:
                    current_dict[key] = value
        
        current_dict["updated_at"] = datetime.now()
        updated_state = EngagementState(**current_dict)
        
        async with get_async_db() as session:
            await session.execute(text("""
                UPDATE engagements.engagements 
                SET state = :state, 
                    current_phase = :phase,
                    updated_at = :updated_at
                WHERE id = :id
            """), {
                "id": engagement_id,
                "state": updated_state.model_dump_json(),
                "phase": updated_state.current_phase,
                "updated_at": updated_state.updated_at
            })
        
        return updated_state
    
    async def transition_phase(
        self,
        engagement_id: str,
        new_phase: str
    ) -> EngagementState:
        """Transition engagement to a new phase."""
        valid_transitions = {
            "discovery": ["data_foundation"],
            "data_foundation": ["application", "discovery"],
            "application": ["deployment", "data_foundation"],
            "deployment": ["support", "application"],
            "support": []
        }
        
        current = await self.get_engagement(engagement_id)
        if not current:
            raise ValueError(f"Engagement {engagement_id} not found")
        
        if new_phase not in valid_transitions.get(current.current_phase, []):
            raise ValueError(
                f"Invalid transition from {current.current_phase} to {new_phase}"
            )
        
        return await self.update_engagement(engagement_id, {
            "current_phase": new_phase
        })