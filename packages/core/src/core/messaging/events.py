"""
Event publishing and subscription using Redis Streams.
"""
from typing import Any, Callable, Dict, List, Optional
import asyncio
import json
from datetime import datetime
from redis.asyncio import Redis
from pydantic import BaseModel
from core.config import get_settings

settings = get_settings()

class Event(BaseModel):
    """Base event model."""
    event_id: str
    event_type: str
    timestamp: datetime
    payload: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class EventBus:
    """Redis Streams-based event bus."""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.handlers: Dict[str, List[Callable]] = {}
    
    async def connect(self) -> None:
        """Connect to Redis."""
        self.redis = Redis.from_url(
            settings.redis.connection_string,
            decode_responses=True
        )
    
    async def disconnect(self) -> None:
        """Disconnect from Redis."""
        if self.redis:
            await self.redis.close()
    
    async def publish(self, event_type: str, payload: Dict[str, Any]) -> str:
        """Publish an event to the stream."""
        if not self.redis:
            raise RuntimeError("EventBus not connected")
        
        event = Event(
            event_id=f"{event_type}_{datetime.now().timestamp()}",
            event_type=event_type,
            timestamp=datetime.now(),
            payload=payload
        )
        
        stream_name = f"events:{event_type.split('.')[0]}"
        
        message_id = await self.redis.xadd(
            stream_name,
            {"data": event.model_dump_json()}
        )
        
        return message_id
    
    def subscribe(self, event_type: str, handler: Callable) -> None:
        """Subscribe to an event type."""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        self.handlers[event_type].append(handler)
    
    async def start_consumer(self, consumer_group: str, consumer_name: str) -> None:
        """Start consuming events."""
        if not self.redis:
            raise RuntimeError("EventBus not connected")
        
        # Get unique stream names from handlers
        streams = set()
        for event_type in self.handlers.keys():
            stream_name = f"events:{event_type.split('.')[0]}"
            streams.add(stream_name)
        
        # Create consumer groups
        for stream in streams:
            try:
                await self.redis.xgroup_create(stream, consumer_group, mkstream=True)
            except Exception:
                pass  # Group already exists
        
        # Start consuming
        while True:
            for stream in streams:
                messages = await self.redis.xreadgroup(
                    consumer_group,
                    consumer_name,
                    {stream: ">"},
                    count=10,
                    block=1000
                )
                
                for stream_name, stream_messages in messages:
                    for message_id, data in stream_messages:
                        event = Event.model_validate_json(data["data"])
                        
                        # Call handlers
                        if event.event_type in self.handlers:
                            for handler in self.handlers[event.event_type]:
                                try:
                                    await handler(event)
                                except Exception as e:
                                    print(f"Handler error: {e}")
                        
                        # Acknowledge message
                        await self.redis.xack(stream_name, consumer_group, message_id)