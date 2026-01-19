"""
Messaging module for Open Forge.
Provides Redis Streams-based event bus for inter-service communication.
"""
from core.messaging.events import EventBus, Event

__all__ = ["EventBus", "Event"]
