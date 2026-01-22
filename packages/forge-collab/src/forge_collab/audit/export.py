"""Audit export - Compliance exports in various formats."""

import csv
import io
import json
from datetime import datetime
from enum import Enum
from typing import AsyncIterator

from forge_collab.audit.logger import AuditEvent
from forge_collab.audit.query import AuditQuery


class ExportFormat(str, Enum):
    """Supported export formats."""

    JSON = "json"
    CSV = "csv"
    JSONL = "jsonl"  # JSON Lines (one event per line)


class AuditExporter:
    """Export audit events for compliance and analysis.

    Supports multiple export formats and streaming for large exports.

    Example usage:
        exporter = AuditExporter(query)

        # Export to JSON
        json_data = await exporter.export(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
            format=ExportFormat.JSON,
        )

        # Stream large exports
        async for chunk in exporter.export_stream(
            start_time=datetime(2024, 1, 1),
            end_time=datetime(2024, 12, 31),
            format=ExportFormat.JSONL,
        ):
            yield chunk
    """

    # CSV columns for export
    CSV_COLUMNS = [
        "id",
        "timestamp",
        "event_type",
        "action",
        "actor_id",
        "actor_type",
        "resource_type",
        "resource_id",
        "resource_name",
        "success",
        "error_message",
        "ip_address",
        "user_agent",
        "sensitive",
    ]

    def __init__(self, query: AuditQuery):
        """Initialize the exporter.

        Args:
            query: AuditQuery instance for fetching events
        """
        self._query = query

    async def export(
        self,
        start_time: datetime,
        end_time: datetime,
        format: ExportFormat = ExportFormat.JSON,
        event_types: list[str] | None = None,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        include_sensitive: bool = False,
        max_events: int = 10000,
    ) -> str:
        """Export audit events to a string.

        Args:
            start_time: Start of export range
            end_time: End of export range
            format: Export format
            event_types: Filter by event types
            actor_id: Filter by actor
            resource_type: Filter by resource type
            resource_id: Filter by resource ID
            include_sensitive: Include sensitive events
            max_events: Maximum events to export

        Returns:
            Exported data as string
        """
        # Fetch events
        events = await self._fetch_events(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            include_sensitive=include_sensitive,
            max_events=max_events,
        )

        # Format output
        if format == ExportFormat.JSON:
            return self._to_json(events)
        elif format == ExportFormat.CSV:
            return self._to_csv(events)
        elif format == ExportFormat.JSONL:
            return self._to_jsonl(events)

        raise ValueError(f"Unsupported format: {format}")

    async def export_stream(
        self,
        start_time: datetime,
        end_time: datetime,
        format: ExportFormat = ExportFormat.JSONL,
        event_types: list[str] | None = None,
        batch_size: int = 1000,
    ) -> AsyncIterator[str]:
        """Stream export for large datasets.

        Args:
            start_time: Start of export range
            end_time: End of export range
            format: Export format (JSONL recommended for streaming)
            event_types: Filter by event types
            batch_size: Events per batch

        Yields:
            Chunks of exported data
        """
        offset = 0

        while True:
            result = await self._query.search(
                start_time=start_time,
                end_time=end_time,
                event_types=event_types,
                limit=batch_size,
                offset=offset,
            )

            if not result.events:
                break

            # Yield formatted batch
            if format == ExportFormat.JSONL:
                yield self._to_jsonl(result.events)
            elif format == ExportFormat.JSON:
                yield self._to_json(result.events)
            elif format == ExportFormat.CSV:
                # Include header only for first batch
                yield self._to_csv(result.events, include_header=(offset == 0))

            offset += batch_size

            if not result.has_more:
                break

    async def _fetch_events(
        self,
        start_time: datetime,
        end_time: datetime,
        event_types: list[str] | None = None,
        actor_id: str | None = None,
        resource_type: str | None = None,
        resource_id: str | None = None,
        include_sensitive: bool = False,
        max_events: int = 10000,
    ) -> list[AuditEvent]:
        """Fetch events for export."""
        result = await self._query.search(
            start_time=start_time,
            end_time=end_time,
            event_types=event_types,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            sensitive=None if include_sensitive else False,
            limit=max_events,
        )
        return result.events

    def _to_json(self, events: list[AuditEvent]) -> str:
        """Convert events to JSON."""
        return json.dumps(
            [self._event_to_dict(e) for e in events],
            indent=2,
            default=str,
        )

    def _to_jsonl(self, events: list[AuditEvent]) -> str:
        """Convert events to JSON Lines."""
        lines = [
            json.dumps(self._event_to_dict(e), default=str)
            for e in events
        ]
        return "\n".join(lines) + "\n" if lines else ""

    def _to_csv(
        self, events: list[AuditEvent], include_header: bool = True
    ) -> str:
        """Convert events to CSV."""
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=self.CSV_COLUMNS)

        if include_header:
            writer.writeheader()

        for event in events:
            row = self._event_to_csv_row(event)
            writer.writerow(row)

        return output.getvalue()

    def _event_to_dict(self, event: AuditEvent) -> dict:
        """Convert event to dict for JSON export."""
        return event.model_dump(mode="json")

    def _event_to_csv_row(self, event: AuditEvent) -> dict:
        """Convert event to CSV row dict."""
        return {
            "id": event.id,
            "timestamp": event.timestamp.isoformat(),
            "event_type": event.event_type,
            "action": event.action.value,
            "actor_id": event.actor_id,
            "actor_type": event.actor_type,
            "resource_type": event.resource_type or "",
            "resource_id": event.resource_id or "",
            "resource_name": event.resource_name or "",
            "success": str(event.success),
            "error_message": event.error_message or "",
            "ip_address": event.ip_address or "",
            "user_agent": event.user_agent or "",
            "sensitive": str(event.sensitive),
        }

    def get_export_metadata(
        self,
        start_time: datetime,
        end_time: datetime,
        event_count: int,
        format: ExportFormat,
    ) -> dict:
        """Generate metadata for an export.

        Useful for compliance documentation.
        """
        return {
            "export_timestamp": datetime.utcnow().isoformat(),
            "period_start": start_time.isoformat(),
            "period_end": end_time.isoformat(),
            "event_count": event_count,
            "format": format.value,
            "columns": self.CSV_COLUMNS if format == ExportFormat.CSV else None,
        }
