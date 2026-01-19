"""
Agent memory system for maintaining context across executions.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from pydantic import BaseModel
import json
from sqlalchemy import text
from core.database.connection import get_async_db

class MemoryEntry(BaseModel):
    """A single memory entry."""
    id: str
    engagement_id: str
    agent_name: str
    run_id: str
    entry_type: str  # execution, insight, decision
    content: Dict[str, Any]
    timestamp: datetime
    relevance_score: Optional[float] = None

class AgentMemory:
    """Memory system for agents."""
    
    async def store_execution(
        self,
        engagement_id: str,
        agent_name: str,
        run_id: str,
        input: Dict[str, Any],
        output: Dict[str, Any]
    ) -> None:
        """Store an execution result in memory."""
        entry = MemoryEntry(
            id=f"{engagement_id}_{agent_name}_{run_id}",
            engagement_id=engagement_id,
            agent_name=agent_name,
            run_id=run_id,
            entry_type="execution",
            content={"input": input, "output": output},
            timestamp=datetime.now()
        )
        
        async with get_async_db() as session:
            await session.execute(text("""
                INSERT INTO engagements.agent_memory 
                (id, engagement_id, agent_name, run_id, entry_type, content, timestamp)
                VALUES (:id, :engagement_id, :agent_name, :run_id, :entry_type, :content, :timestamp)
                ON CONFLICT (id) DO UPDATE SET content = :content, timestamp = :timestamp
            """), {
                "id": entry.id,
                "engagement_id": engagement_id,
                "agent_name": agent_name,
                "run_id": run_id,
                "entry_type": "execution",
                "content": json.dumps(entry.content),
                "timestamp": entry.timestamp
            })
    
    async def store_insight(
        self,
        engagement_id: str,
        agent_name: str,
        insight: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Store an insight derived by an agent."""
        run_id = f"insight_{datetime.now().timestamp()}"
        
        async with get_async_db() as session:
            await session.execute(text("""
                INSERT INTO engagements.agent_memory 
                (id, engagement_id, agent_name, run_id, entry_type, content, timestamp)
                VALUES (:id, :engagement_id, :agent_name, :run_id, :entry_type, :content, :timestamp)
            """), {
                "id": f"{engagement_id}_{agent_name}_{run_id}",
                "engagement_id": engagement_id,
                "agent_name": agent_name,
                "run_id": run_id,
                "entry_type": "insight",
                "content": json.dumps({"insight": insight, "metadata": metadata or {}}),
                "timestamp": datetime.now()
            })
    
    async def get_relevant_context(
        self,
        engagement_id: str,
        agent_name: str,
        limit: int = 10
    ) -> List[MemoryEntry]:
        """Get relevant context for an agent."""
        async with get_async_db() as session:
            result = await session.execute(text("""
                SELECT id, engagement_id, agent_name, run_id, entry_type, content, timestamp
                FROM engagements.agent_memory
                WHERE engagement_id = :engagement_id
                ORDER BY timestamp DESC
                LIMIT :limit
            """), {
                "engagement_id": engagement_id,
                "limit": limit
            })
            
            entries = []
            for row in result.fetchall():
                entries.append(MemoryEntry(
                    id=row[0],
                    engagement_id=row[1],
                    agent_name=row[2],
                    run_id=row[3],
                    entry_type=row[4],
                    content=json.loads(row[5]) if isinstance(row[5], str) else row[5],
                    timestamp=row[6]
                ))
            
            return entries
    
    async def get_agent_history(
        self,
        engagement_id: str,
        agent_name: str
    ) -> List[MemoryEntry]:
        """Get all history for a specific agent."""
        async with get_async_db() as session:
            result = await session.execute(text("""
                SELECT id, engagement_id, agent_name, run_id, entry_type, content, timestamp
                FROM engagements.agent_memory
                WHERE engagement_id = :engagement_id AND agent_name = :agent_name
                ORDER BY timestamp ASC
            """), {
                "engagement_id": engagement_id,
                "agent_name": agent_name
            })
            
            entries = []
            for row in result.fetchall():
                entries.append(MemoryEntry(
                    id=row[0],
                    engagement_id=row[1],
                    agent_name=row[2],
                    run_id=row[3],
                    entry_type=row[4],
                    content=json.loads(row[5]) if isinstance(row[5], str) else row[5],
                    timestamp=row[6]
                ))
            
            return entries
            