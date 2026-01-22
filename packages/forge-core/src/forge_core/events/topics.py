"""
Event Topic Definitions

This module defines standard event topics and patterns for the Open Forge platform.
Topics follow a hierarchical naming convention for easy filtering.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from typing import ClassVar


class EventTopic(str, Enum):
    """
    Standard event topics in the Open Forge platform.

    Topics follow the pattern: {domain}.{resource}.{action}
    """

    # User events
    USERS_CREATED = "users.user.created"
    USERS_UPDATED = "users.user.updated"
    USERS_DELETED = "users.user.deleted"
    USERS_LOGIN = "users.session.login"
    USERS_LOGOUT = "users.session.logout"

    # Dataset events
    DATASETS_CREATED = "data.dataset.created"
    DATASETS_UPDATED = "data.dataset.updated"
    DATASETS_DELETED = "data.dataset.deleted"
    DATASETS_SYNCED = "data.dataset.synced"

    # Pipeline events
    PIPELINES_CREATED = "pipelines.pipeline.created"
    PIPELINES_STARTED = "pipelines.run.started"
    PIPELINES_COMPLETED = "pipelines.run.completed"
    PIPELINES_FAILED = "pipelines.run.failed"

    # Connector events
    CONNECTORS_CONNECTED = "connectors.connection.connected"
    CONNECTORS_DISCONNECTED = "connectors.connection.disconnected"
    CONNECTORS_ERROR = "connectors.connection.error"

    # AI events
    AI_INFERENCE_STARTED = "ai.inference.started"
    AI_INFERENCE_COMPLETED = "ai.inference.completed"
    AI_AGENT_STARTED = "ai.agent.started"
    AI_AGENT_COMPLETED = "ai.agent.completed"

    # Application events
    APPS_PUBLISHED = "apps.app.published"
    APPS_DEPLOYED = "apps.app.deployed"

    # System events
    SYSTEM_HEALTH = "system.health.changed"
    SYSTEM_CONFIG = "system.config.updated"


@dataclass
class TopicPattern:
    """
    Pattern for matching event topics.

    Supports wildcards:
    - '*' matches a single level (e.g., "data.*.created" matches "data.dataset.created")
    - '**' matches multiple levels (e.g., "data.**" matches all data events)

    Example usage:
        >>> pattern = TopicPattern("data.*.created")
        >>> pattern.matches("data.dataset.created")  # True
        >>> pattern.matches("data.pipeline.created")  # True
        >>> pattern.matches("data.dataset.updated")  # False
    """

    pattern: str

    # Pattern compilation cache
    _regex: re.Pattern | None = None

    # Wildcard constants
    SINGLE_LEVEL: ClassVar[str] = "*"
    MULTI_LEVEL: ClassVar[str] = "**"

    def matches(self, topic: str) -> bool:
        """
        Check if a topic matches this pattern.

        Args:
            topic: Topic string to match

        Returns:
            True if the topic matches the pattern
        """
        # Exact match
        if self.pattern == topic:
            return True

        # Match all
        if self.pattern == self.MULTI_LEVEL:
            return True

        # Compile and cache regex
        if self._regex is None:
            regex_pattern = self._compile_pattern()
            object.__setattr__(self, "_regex", re.compile(regex_pattern))

        return bool(self._regex.match(topic))

    def _compile_pattern(self) -> str:
        """Convert pattern to regex."""
        parts = []
        for part in self.pattern.split("."):
            if part == self.MULTI_LEVEL:
                parts.append(r".*")
            elif part == self.SINGLE_LEVEL:
                parts.append(r"[^.]+")
            else:
                parts.append(re.escape(part))
        return r"^" + r"\.".join(parts) + r"$"

    @classmethod
    def all_events(cls) -> "TopicPattern":
        """Create a pattern that matches all events."""
        return cls(cls.MULTI_LEVEL)

    @classmethod
    def domain(cls, domain: str) -> "TopicPattern":
        """Create a pattern that matches all events in a domain."""
        return cls(f"{domain}.**")

    @classmethod
    def resource(cls, domain: str, resource: str) -> "TopicPattern":
        """Create a pattern that matches all events for a resource."""
        return cls(f"{domain}.{resource}.*")
