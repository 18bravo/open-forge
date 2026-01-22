"""
Audit logging for LLM operations.

This module provides comprehensive audit logging for compliance:
- Request/response logging (without storing raw prompts by default)
- Token usage tracking
- Latency metrics
- User and ontology context
"""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any
from uuid import uuid4

import hashlib
import structlog

logger = structlog.get_logger(__name__)


@dataclass
class AuditEntry:
    """An audit log entry for an LLM operation."""

    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=datetime.utcnow)

    # Request info
    model: str = ""
    request_hash: str = ""  # Hash of request (not raw content)
    request_type: str = "completion"  # 'completion', 'stream', 'embedding'

    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0

    # Performance
    latency_ms: float = 0.0

    # Status
    success: bool = True
    error_message: str | None = None
    finish_reason: str | None = None

    # Context
    user_id: str | None = None
    ontology_id: str | None = None
    request_id: str | None = None
    session_id: str | None = None

    # Guardrail results
    pii_detected: bool = False
    pii_masked: bool = False
    injection_detected: bool = False
    injection_blocked: bool = False
    guardrail_violations: list[str] = field(default_factory=list)

    # Additional metadata
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat(),
            "model": self.model,
            "request_hash": self.request_hash,
            "request_type": self.request_type,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "total_tokens": self.total_tokens,
            "latency_ms": self.latency_ms,
            "success": self.success,
            "error_message": self.error_message,
            "finish_reason": self.finish_reason,
            "user_id": self.user_id,
            "ontology_id": self.ontology_id,
            "request_id": self.request_id,
            "session_id": self.session_id,
            "pii_detected": self.pii_detected,
            "pii_masked": self.pii_masked,
            "injection_detected": self.injection_detected,
            "injection_blocked": self.injection_blocked,
            "guardrail_violations": self.guardrail_violations,
            "metadata": self.metadata,
        }


class AuditStore(ABC):
    """Abstract base class for audit log storage."""

    @abstractmethod
    async def save(self, entry: AuditEntry) -> None:
        """Save an audit entry."""
        ...

    @abstractmethod
    async def get(self, entry_id: str) -> AuditEntry | None:
        """Retrieve an audit entry by ID."""
        ...

    @abstractmethod
    async def query(
        self,
        user_id: str | None = None,
        ontology_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        model: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries with filters."""
        ...

    @abstractmethod
    async def get_usage_summary(
        self,
        user_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated usage statistics."""
        ...


class InMemoryAuditStore(AuditStore):
    """In-memory audit store for testing and development."""

    def __init__(self, max_entries: int = 10000):
        self._entries: dict[str, AuditEntry] = {}
        self._max_entries = max_entries

    async def save(self, entry: AuditEntry) -> None:
        """Save an audit entry."""
        # Enforce max entries (FIFO eviction)
        if len(self._entries) >= self._max_entries:
            oldest_id = min(self._entries.keys(), key=lambda k: self._entries[k].timestamp)
            del self._entries[oldest_id]

        self._entries[entry.id] = entry

    async def get(self, entry_id: str) -> AuditEntry | None:
        """Retrieve an audit entry by ID."""
        return self._entries.get(entry_id)

    async def query(
        self,
        user_id: str | None = None,
        ontology_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        model: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[AuditEntry]:
        """Query audit entries with filters."""
        results = list(self._entries.values())

        # Apply filters
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        if ontology_id:
            results = [e for e in results if e.ontology_id == ontology_id]
        if start_time:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time:
            results = [e for e in results if e.timestamp <= end_time]
        if model:
            results = [e for e in results if e.model == model]

        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return results[offset : offset + limit]

    async def get_usage_summary(
        self,
        user_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get aggregated usage statistics."""
        entries = await self.query(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        if not entries:
            return {
                "total_requests": 0,
                "total_tokens": 0,
                "total_input_tokens": 0,
                "total_output_tokens": 0,
                "avg_latency_ms": 0.0,
                "success_rate": 0.0,
                "by_model": {},
            }

        total_tokens = sum(e.total_tokens for e in entries)
        total_input = sum(e.input_tokens for e in entries)
        total_output = sum(e.output_tokens for e in entries)
        avg_latency = sum(e.latency_ms for e in entries) / len(entries)
        success_count = sum(1 for e in entries if e.success)

        # Aggregate by model
        by_model: dict[str, dict[str, Any]] = {}
        for entry in entries:
            if entry.model not in by_model:
                by_model[entry.model] = {
                    "requests": 0,
                    "tokens": 0,
                    "input_tokens": 0,
                    "output_tokens": 0,
                }
            by_model[entry.model]["requests"] += 1
            by_model[entry.model]["tokens"] += entry.total_tokens
            by_model[entry.model]["input_tokens"] += entry.input_tokens
            by_model[entry.model]["output_tokens"] += entry.output_tokens

        return {
            "total_requests": len(entries),
            "total_tokens": total_tokens,
            "total_input_tokens": total_input,
            "total_output_tokens": total_output,
            "avg_latency_ms": avg_latency,
            "success_rate": success_count / len(entries) if entries else 0.0,
            "by_model": by_model,
        }


@dataclass
class AuditLoggerConfig:
    """Configuration for the audit logger."""

    # What to log
    log_requests: bool = True
    log_responses: bool = True
    log_errors: bool = True

    # Privacy settings
    hash_requests: bool = True  # Hash request content instead of storing raw
    store_raw_prompts: bool = False  # If True, stores actual prompt content (compliance risk)

    # Sampling (for high-volume scenarios)
    sample_rate: float = 1.0  # 1.0 = log all, 0.1 = log 10%

    # Sensitive model tracking
    sensitive_models: list[str] = field(default_factory=list)  # Models that always get logged


class AuditLogger:
    """
    Audit logger for LLM operations.

    Logs all LLM requests and responses for compliance and monitoring.
    By default, does not store raw prompts to protect user privacy.
    """

    def __init__(
        self,
        store: AuditStore | None = None,
        config: AuditLoggerConfig | None = None,
    ):
        """
        Initialize the audit logger.

        Args:
            store: Storage backend for audit entries. Uses InMemoryAuditStore if not provided.
            config: Configuration for logging behavior.
        """
        self.store = store or InMemoryAuditStore()
        self.config = config or AuditLoggerConfig()

    async def log_request(
        self,
        request: Any,  # CompletionRequest
        response: Any | None = None,  # CompletionResponse
        error: Exception | None = None,
        guardrail_result: Any | None = None,  # GuardrailResult
    ) -> AuditEntry:
        """
        Log an LLM request/response.

        Args:
            request: The completion request.
            response: The completion response (if successful).
            error: The error (if failed).
            guardrail_result: Results from guardrail checks.

        Returns:
            The created audit entry.
        """
        # Check sampling
        if self.config.sample_rate < 1.0:
            import random
            if random.random() > self.config.sample_rate:
                # Skip logging based on sample rate (unless sensitive model)
                model = getattr(request, "model", "")
                if model not in self.config.sensitive_models:
                    return AuditEntry(metadata={"sampled_out": True})

        # Create entry
        entry = AuditEntry(
            model=getattr(request, "model", ""),
            request_hash=self._hash_request(request) if self.config.hash_requests else "",
            request_type="completion",
            user_id=getattr(request, "user_id", None),
            ontology_id=getattr(request, "ontology_id", None),
            request_id=getattr(request, "request_id", None),
        )

        # Add response data
        if response:
            entry.success = True
            entry.input_tokens = getattr(response.usage, "input_tokens", 0) if hasattr(response, "usage") else 0
            entry.output_tokens = getattr(response.usage, "output_tokens", 0) if hasattr(response, "usage") else 0
            entry.total_tokens = getattr(response.usage, "total_tokens", 0) if hasattr(response, "usage") else 0
            entry.latency_ms = getattr(response, "latency_ms", 0.0)
            entry.finish_reason = getattr(response, "finish_reason", None)

        # Add error data
        if error:
            entry.success = False
            entry.error_message = str(error)

        # Add guardrail data
        if guardrail_result:
            entry.pii_detected = getattr(guardrail_result, "has_violations", False)
            entry.pii_masked = getattr(guardrail_result, "was_modified", False)
            entry.injection_blocked = getattr(guardrail_result, "was_blocked", False)

            violations = getattr(guardrail_result, "violations", [])
            entry.guardrail_violations = [
                getattr(v, "rule_name", str(v)) for v in violations
            ]
            entry.injection_detected = any(
                "injection" in v.lower() for v in entry.guardrail_violations
            )

        # Store raw prompt if configured (compliance risk)
        if self.config.store_raw_prompts:
            messages = getattr(request, "messages", [])
            entry.metadata["raw_messages"] = [
                {"role": getattr(m, "role", ""), "content_length": len(str(getattr(m, "content", "")))}
                for m in messages
            ]

        # Save entry
        await self.store.save(entry)

        logger.debug(
            "Audit entry created",
            entry_id=entry.id,
            model=entry.model,
            success=entry.success,
            tokens=entry.total_tokens,
        )

        return entry

    def _hash_request(self, request: Any) -> str:
        """Create a hash of the request for privacy-preserving logging."""
        # Hash key parts of the request
        messages = getattr(request, "messages", [])
        content_parts = []

        for msg in messages:
            role = getattr(msg, "role", "")
            content = str(getattr(msg, "content", ""))
            content_parts.append(f"{role}:{len(content)}")

        hash_input = "|".join(content_parts)
        return hashlib.sha256(hash_input.encode()).hexdigest()[:16]

    async def get_user_usage(
        self,
        user_id: str,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
    ) -> dict[str, Any]:
        """Get usage summary for a specific user."""
        return await self.store.get_usage_summary(
            user_id=user_id,
            start_time=start_time,
            end_time=end_time,
        )

    async def get_recent_entries(
        self,
        limit: int = 100,
        user_id: str | None = None,
    ) -> list[AuditEntry]:
        """Get recent audit entries."""
        return await self.store.query(user_id=user_id, limit=limit)

    async def export_compliance_report(
        self,
        start_time: datetime,
        end_time: datetime,
    ) -> AsyncIterator[dict[str, Any]]:
        """
        Export audit entries for compliance reporting.

        Yields entries as dictionaries suitable for compliance exports.
        """
        entries = await self.store.query(
            start_time=start_time,
            end_time=end_time,
            limit=100000,
        )

        for entry in entries:
            yield entry.to_dict()
