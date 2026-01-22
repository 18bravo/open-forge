"""
Event Bus Module

This module provides event-driven communication between Open Forge components.

The event bus supports:
- Publish/subscribe patterns for loose coupling
- Multiple backends (Redis, PostgreSQL, in-memory)
- Topic-based message routing
- Handler registration and management

Use events for:
- Cross-package communication
- Async processing triggers
- Audit logging
- Real-time notifications
"""

from forge_core.events.bus import (
    Event,
    EventBus,
    EventHandler,
    Subscription,
)
from forge_core.events.handlers import EventHandlerRegistry
from forge_core.events.topics import EventTopic, TopicPattern

__all__ = [
    # Core types
    "Event",
    "EventBus",
    "EventHandler",
    "Subscription",
    # Topics
    "EventTopic",
    "TopicPattern",
    # Registry
    "EventHandlerRegistry",
]
