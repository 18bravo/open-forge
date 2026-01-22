"""Audit query - Search and filter audit events."""

from datetime import datetime
from typing import Any, Protocol

from pydantic import BaseModel

from forge_collab.audit.logger import AuditEvent, AuditAction


class AuditSearchResult(BaseModel):
    """Result of an audit search query."""

    events: list[AuditEvent]
    total_count: int
    offset: int
    limit: int
    has_more: bool


class AuditStorageQuery(Protocol):
    """Protocol for queryable audit storage."""

    async def search(
        self,
        filters: list[dict[str, Any]],
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditSearchResult:
        """Search audit events with filters."""
        ...

    async def aggregate(
        self,
        group_by: str,
        metric: str,
        filters: list[dict[str, Any]],
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """Aggregate audit events."""
        ...


class AuditQuery:
    """Query interface for audit events.

    Provides a fluent interface for searching and filtering audit events.

    Example usage:
        query = AuditQuery(storage)

        # Search by multiple criteria
        results = await query.search(
            event_types=["dataset.created", "dataset.updated"],
            actor_id="user-123",
            start_time=datetime(2024, 1, 1),
            limit=50,
        )

        # Get activity timeline for a resource
        timeline = await query.get_activity_timeline(
            resource_type="dataset",
            resource_id="ds-456",
        )
    """

    def __init__(self, storage: AuditStorageQuery | None = None):
        """Initialize the query interface.

        Args:
            storage: Storage backend for querying events
        """
        self._storage = storage

    async def search(
        self,
        event_types: list[str] | None = None,
        actions: list[AuditAction] | None = None,
        actor_id: str | None = None,
        actor_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        success: bool | None = None,
        sensitive: bool | None = None,
        query: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> AuditSearchResult:
        """Search audit events with filters.

        Args:
            event_types: Filter by event types
            actions: Filter by actions
            actor_id: Filter by actor ID
            actor_type: Filter by actor type
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            start_time: Events after this time
            end_time: Events before this time
            success: Filter by success status
            sensitive: Filter by sensitive flag
            query: Full-text search query
            limit: Max results to return
            offset: Offset for pagination

        Returns:
            AuditSearchResult with matching events
        """
        filters = self._build_filters(
            event_types=event_types,
            actions=actions,
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            start_time=start_time,
            end_time=end_time,
            success=success,
            sensitive=sensitive,
        )

        if self._storage:
            return await self._storage.search(
                filters=filters,
                query=query,
                limit=limit,
                offset=offset,
            )

        # Scaffold: return empty results
        return AuditSearchResult(
            events=[],
            total_count=0,
            offset=offset,
            limit=limit,
            has_more=False,
        )

    def _build_filters(
        self,
        event_types: list[str] | None = None,
        actions: list[AuditAction] | None = None,
        actor_id: str | None = None,
        actor_type: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        success: bool | None = None,
        sensitive: bool | None = None,
    ) -> list[dict[str, Any]]:
        """Build filter list for storage query."""
        filters: list[dict[str, Any]] = []

        if event_types:
            filters.append({"event_type": {"$in": event_types}})
        if actions:
            filters.append({"action": {"$in": [a.value for a in actions]}})
        if actor_id:
            filters.append({"actor_id": actor_id})
        if actor_type:
            filters.append({"actor_type": actor_type})
        if resource_type:
            filters.append({"resource_type": resource_type})
        if resource_id:
            filters.append({"resource_id": resource_id})
        if start_time:
            filters.append({"timestamp": {"$gte": start_time}})
        if end_time:
            filters.append({"timestamp": {"$lte": end_time}})
        if success is not None:
            filters.append({"success": success})
        if sensitive is not None:
            filters.append({"sensitive": sensitive})

        return filters

    async def get_activity_timeline(
        self,
        resource_type: str,
        resource_id: str,
        limit: int = 50,
    ) -> list[AuditEvent]:
        """Get activity timeline for a specific resource.

        Args:
            resource_type: Type of the resource
            resource_id: ID of the resource
            limit: Max events to return

        Returns:
            List of events in reverse chronological order
        """
        result = await self.search(
            resource_type=resource_type,
            resource_id=resource_id,
            limit=limit,
        )
        return result.events

    async def get_user_activity(
        self,
        user_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get activity for a specific user.

        Args:
            user_id: User ID to get activity for
            start_time: Start of time range
            end_time: End of time range
            limit: Max events to return

        Returns:
            List of events
        """
        result = await self.search(
            actor_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
        )
        return result.events

    async def get_failed_actions(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get failed actions for security analysis.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Max events to return

        Returns:
            List of failed events
        """
        result = await self.search(
            start_time=start_time,
            end_time=end_time,
            success=False,
            limit=limit,
        )
        return result.events

    async def get_sensitive_operations(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 100,
    ) -> list[AuditEvent]:
        """Get sensitive operations for compliance review.

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Max events to return

        Returns:
            List of sensitive events
        """
        result = await self.search(
            start_time=start_time,
            end_time=end_time,
            sensitive=True,
            limit=limit,
        )
        return result.events

    async def count_by_event_type(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> dict[str, int]:
        """Get event counts by type.

        Args:
            start_time: Start of time range
            end_time: End of time range

        Returns:
            Dict mapping event_type to count
        """
        if self._storage:
            results = await self._storage.aggregate(
                group_by="event_type",
                metric="count",
                filters=[
                    {"timestamp": {"$gte": start_time}},
                    {"timestamp": {"$lte": end_time}},
                ],
            )
            return {r["event_type"]: r["count"] for r in results}

        return {}

    async def count_by_actor(
        self,
        start_time: datetime,
        end_time: datetime,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Get event counts by actor (most active users).

        Args:
            start_time: Start of time range
            end_time: End of time range
            limit: Max actors to return

        Returns:
            List of {actor_id, count} dicts
        """
        if self._storage:
            return await self._storage.aggregate(
                group_by="actor_id",
                metric="count",
                filters=[
                    {"timestamp": {"$gte": start_time}},
                    {"timestamp": {"$lte": end_time}},
                ],
                limit=limit,
            )

        return []
