"""
LangSmith integration for comprehensive observability of agent workflows.

Provides decorators and utilities for tracing engagements and agents,
logging feedback, and retrieving trace data from LangSmith.
"""
import os
import functools
import asyncio
from typing import Any, Callable, Optional, TypeVar, ParamSpec
from datetime import datetime
from contextlib import contextmanager
import logging

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

# Type variables for decorator typing
P = ParamSpec("P")
T = TypeVar("T")


class LangSmithConfig(BaseModel):
    """Configuration for LangSmith integration."""

    api_key: Optional[str] = Field(default=None, description="LangSmith API key")
    project: str = Field(default="open-forge", description="LangSmith project name")
    endpoint: str = Field(
        default="https://api.smith.langchain.com",
        description="LangSmith API endpoint (use custom endpoint for self-hosted)",
    )
    tracing_enabled: bool = Field(default=True, description="Enable/disable tracing")

    @classmethod
    def from_env(cls) -> "LangSmithConfig":
        """Create configuration from environment variables."""
        return cls(
            api_key=os.getenv("LANGCHAIN_API_KEY") or os.getenv("LANGSMITH_API_KEY"),
            project=os.getenv("LANGCHAIN_PROJECT", "open-forge"),
            endpoint=os.getenv(
                "LANGCHAIN_ENDPOINT",
                os.getenv("LANGSMITH_ENDPOINT", "https://api.smith.langchain.com"),
            ),
            tracing_enabled=os.getenv("LANGCHAIN_TRACING_V2", "true").lower() == "true",
        )


class TraceInfo(BaseModel):
    """Information about a LangSmith trace."""

    run_id: str = Field(description="Unique run identifier")
    trace_id: str = Field(description="Trace identifier")
    name: str = Field(description="Name of the traced operation")
    start_time: datetime = Field(description="When the trace started")
    end_time: Optional[datetime] = Field(default=None, description="When the trace ended")
    status: str = Field(default="running", description="Trace status")
    engagement_id: Optional[str] = Field(default=None, description="Associated engagement ID")
    agent_id: Optional[str] = Field(default=None, description="Associated agent ID")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    inputs: Optional[dict[str, Any]] = Field(default=None, description="Trace inputs")
    outputs: Optional[dict[str, Any]] = Field(default=None, description="Trace outputs")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency_ms: Optional[float] = Field(default=None, description="Latency in milliseconds")
    token_usage: Optional[dict[str, int]] = Field(
        default=None, description="Token usage statistics"
    )


class FeedbackRecord(BaseModel):
    """Feedback submitted for a trace run."""

    run_id: str = Field(description="Run ID to provide feedback for")
    score: float = Field(ge=0.0, le=1.0, description="Feedback score (0.0-1.0)")
    comment: Optional[str] = Field(default=None, description="Optional comment")
    key: str = Field(default="user_feedback", description="Feedback key/category")
    submitted_at: datetime = Field(default_factory=datetime.utcnow)
    submitted_by: Optional[str] = Field(default=None, description="User who submitted feedback")


class ObservabilityStats(BaseModel):
    """Statistics about observability data."""

    total_traces: int = Field(default=0, description="Total number of traces")
    successful_traces: int = Field(default=0, description="Number of successful traces")
    failed_traces: int = Field(default=0, description="Number of failed traces")
    avg_latency_ms: float = Field(default=0.0, description="Average latency in milliseconds")
    total_tokens: int = Field(default=0, description="Total tokens used")
    feedback_count: int = Field(default=0, description="Number of feedback submissions")
    avg_feedback_score: Optional[float] = Field(
        default=None, description="Average feedback score"
    )
    time_range_start: Optional[datetime] = Field(default=None, description="Stats start time")
    time_range_end: Optional[datetime] = Field(default=None, description="Stats end time")


class LangSmithObservability:
    """
    LangSmith integration for tracing and observability.

    Provides methods for:
    - Tracing engagements and agent operations
    - Logging user feedback on runs
    - Retrieving trace data for analysis
    - Managing LangSmith configuration

    Supports both hosted and self-hosted LangSmith deployments.
    """

    def __init__(self, config: Optional[LangSmithConfig] = None):
        """
        Initialize LangSmith observability.

        Args:
            config: LangSmith configuration. If not provided, reads from environment.
        """
        self.config = config or LangSmithConfig.from_env()
        self._client: Optional[Any] = None
        self._setup_environment()

    def _setup_environment(self) -> None:
        """Configure environment variables for LangChain/LangSmith integration."""
        if self.config.tracing_enabled and self.config.api_key:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = self.config.api_key
            os.environ["LANGCHAIN_PROJECT"] = self.config.project
            os.environ["LANGCHAIN_ENDPOINT"] = self.config.endpoint
            logger.info(
                f"LangSmith tracing enabled for project: {self.config.project}"
            )
        else:
            os.environ["LANGCHAIN_TRACING_V2"] = "false"
            logger.info("LangSmith tracing disabled")

    @property
    def client(self) -> Any:
        """
        Get or create the LangSmith client.

        Returns:
            LangSmith Client instance

        Raises:
            ImportError: If langsmith package is not installed
        """
        if self._client is None:
            try:
                from langsmith import Client

                self._client = Client(
                    api_key=self.config.api_key,
                    api_url=self.config.endpoint,
                )
            except ImportError:
                logger.warning(
                    "langsmith package not installed. Install with: pip install langsmith"
                )
                raise
        return self._client

    def trace_engagement(
        self, engagement_id: str, name: Optional[str] = None
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """
        Decorator to trace an engagement operation.

        Args:
            engagement_id: Unique identifier for the engagement
            name: Optional name for the trace (defaults to function name)

        Returns:
            Decorated function with LangSmith tracing

        Example:
            @langsmith.trace_engagement("eng-123")
            async def process_engagement(data):
                # ... engagement logic
                pass
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            trace_name = name or f"engagement.{func.__name__}"

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if not self.config.tracing_enabled:
                    return await func(*args, **kwargs)

                try:
                    from langsmith import traceable

                    traced_func = traceable(
                        name=trace_name,
                        metadata={
                            "engagement_id": engagement_id,
                            "trace_type": "engagement",
                        },
                        tags=["engagement", f"engagement:{engagement_id}"],
                    )(func)
                    return await traced_func(*args, **kwargs)
                except ImportError:
                    logger.warning("langsmith not available, running without tracing")
                    return await func(*args, **kwargs)

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if not self.config.tracing_enabled:
                    return func(*args, **kwargs)

                try:
                    from langsmith import traceable

                    traced_func = traceable(
                        name=trace_name,
                        metadata={
                            "engagement_id": engagement_id,
                            "trace_type": "engagement",
                        },
                        tags=["engagement", f"engagement:{engagement_id}"],
                    )(func)
                    return traced_func(*args, **kwargs)
                except ImportError:
                    logger.warning("langsmith not available, running without tracing")
                    return func(*args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper  # type: ignore
            return sync_wrapper  # type: ignore

        return decorator

    def trace_agent(
        self,
        agent_id: str,
        engagement_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Callable[[Callable[P, T]], Callable[P, T]]:
        """
        Decorator to trace an agent operation.

        Args:
            agent_id: Unique identifier for the agent
            engagement_id: Optional engagement ID if agent is part of an engagement
            name: Optional name for the trace (defaults to function name)

        Returns:
            Decorated function with LangSmith tracing

        Example:
            @langsmith.trace_agent("agent-discovery-001", engagement_id="eng-123")
            async def run_discovery(data):
                # ... agent logic
                pass
        """

        def decorator(func: Callable[P, T]) -> Callable[P, T]:
            trace_name = name or f"agent.{func.__name__}"
            metadata = {
                "agent_id": agent_id,
                "trace_type": "agent",
            }
            tags = ["agent", f"agent:{agent_id}"]

            if engagement_id:
                metadata["engagement_id"] = engagement_id
                tags.append(f"engagement:{engagement_id}")

            @functools.wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if not self.config.tracing_enabled:
                    return await func(*args, **kwargs)

                try:
                    from langsmith import traceable

                    traced_func = traceable(
                        name=trace_name,
                        metadata=metadata,
                        tags=tags,
                    )(func)
                    return await traced_func(*args, **kwargs)
                except ImportError:
                    logger.warning("langsmith not available, running without tracing")
                    return await func(*args, **kwargs)

            @functools.wraps(func)
            def sync_wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
                if not self.config.tracing_enabled:
                    return func(*args, **kwargs)

                try:
                    from langsmith import traceable

                    traced_func = traceable(
                        name=trace_name,
                        metadata=metadata,
                        tags=tags,
                    )(func)
                    return traced_func(*args, **kwargs)
                except ImportError:
                    logger.warning("langsmith not available, running without tracing")
                    return func(*args, **kwargs)

            if asyncio.iscoroutinefunction(func):
                return async_wrapper  # type: ignore
            return sync_wrapper  # type: ignore

        return decorator

    @contextmanager
    def trace_context(
        self,
        name: str,
        engagement_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """
        Context manager for manual tracing.

        Args:
            name: Name for the trace
            engagement_id: Optional engagement ID
            agent_id: Optional agent ID
            metadata: Additional metadata to include

        Yields:
            Run context for adding inputs/outputs

        Example:
            with langsmith.trace_context("custom_operation", engagement_id="eng-123") as run:
                # ... operation logic
                run.add_outputs({"result": "success"})
        """
        if not self.config.tracing_enabled:
            yield None
            return

        try:
            from langsmith import trace as ls_trace

            trace_metadata = metadata or {}
            tags = []

            if engagement_id:
                trace_metadata["engagement_id"] = engagement_id
                tags.append(f"engagement:{engagement_id}")
            if agent_id:
                trace_metadata["agent_id"] = agent_id
                tags.append(f"agent:{agent_id}")

            with ls_trace(name=name, metadata=trace_metadata, tags=tags) as run:
                yield run
        except ImportError:
            logger.warning("langsmith not available, running without tracing")
            yield None

    async def log_feedback(
        self,
        run_id: str,
        score: float,
        comment: Optional[str] = None,
        key: str = "user_feedback",
        submitted_by: Optional[str] = None,
    ) -> FeedbackRecord:
        """
        Log feedback for a specific run.

        Args:
            run_id: The run ID to provide feedback for
            score: Feedback score (0.0-1.0)
            comment: Optional feedback comment
            key: Feedback key/category
            submitted_by: User who submitted the feedback

        Returns:
            FeedbackRecord with the submitted feedback

        Raises:
            ValueError: If score is out of range
            Exception: If feedback submission fails
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError("Score must be between 0.0 and 1.0")

        feedback = FeedbackRecord(
            run_id=run_id,
            score=score,
            comment=comment,
            key=key,
            submitted_by=submitted_by,
        )

        if not self.config.tracing_enabled or not self.config.api_key:
            logger.warning("LangSmith not configured, feedback not submitted")
            return feedback

        try:
            self.client.create_feedback(
                run_id=run_id,
                key=key,
                score=score,
                comment=comment,
            )
            logger.info(f"Feedback submitted for run {run_id}: score={score}")
        except Exception as e:
            logger.error(f"Failed to submit feedback: {e}")
            raise

        return feedback

    async def get_engagement_traces(
        self,
        engagement_id: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[TraceInfo]:
        """
        Retrieve traces for a specific engagement.

        Args:
            engagement_id: The engagement ID to filter by
            limit: Maximum number of traces to return
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of TraceInfo objects for the engagement
        """
        if not self.config.tracing_enabled or not self.config.api_key:
            logger.warning("LangSmith not configured, returning empty traces")
            return []

        try:
            runs = list(
                self.client.list_runs(
                    project_name=self.config.project,
                    filter=f'has(metadata, "engagement_id") and eq(metadata["engagement_id"], "{engagement_id}")',
                    limit=limit,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

            traces = []
            for run in runs:
                trace = TraceInfo(
                    run_id=str(run.id),
                    trace_id=str(run.trace_id) if run.trace_id else str(run.id),
                    name=run.name,
                    start_time=run.start_time,
                    end_time=run.end_time,
                    status="success" if run.status == "success" else (
                        "error" if run.status == "error" else "running"
                    ),
                    engagement_id=engagement_id,
                    agent_id=run.extra.get("metadata", {}).get("agent_id"),
                    metadata=run.extra.get("metadata", {}),
                    inputs=run.inputs,
                    outputs=run.outputs,
                    error=str(run.error) if run.error else None,
                    latency_ms=(
                        (run.end_time - run.start_time).total_seconds() * 1000
                        if run.end_time else None
                    ),
                    token_usage=run.extra.get("token_usage"),
                )
                traces.append(trace)

            return traces

        except Exception as e:
            logger.error(f"Failed to retrieve traces: {e}")
            return []

    async def get_agent_traces(
        self,
        agent_id: str,
        limit: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> list[TraceInfo]:
        """
        Retrieve traces for a specific agent.

        Args:
            agent_id: The agent ID to filter by
            limit: Maximum number of traces to return
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            List of TraceInfo objects for the agent
        """
        if not self.config.tracing_enabled or not self.config.api_key:
            logger.warning("LangSmith not configured, returning empty traces")
            return []

        try:
            runs = list(
                self.client.list_runs(
                    project_name=self.config.project,
                    filter=f'has(metadata, "agent_id") and eq(metadata["agent_id"], "{agent_id}")',
                    limit=limit,
                    start_time=start_time,
                    end_time=end_time,
                )
            )

            traces = []
            for run in runs:
                trace = TraceInfo(
                    run_id=str(run.id),
                    trace_id=str(run.trace_id) if run.trace_id else str(run.id),
                    name=run.name,
                    start_time=run.start_time,
                    end_time=run.end_time,
                    status="success" if run.status == "success" else (
                        "error" if run.status == "error" else "running"
                    ),
                    engagement_id=run.extra.get("metadata", {}).get("engagement_id"),
                    agent_id=agent_id,
                    metadata=run.extra.get("metadata", {}),
                    inputs=run.inputs,
                    outputs=run.outputs,
                    error=str(run.error) if run.error else None,
                    latency_ms=(
                        (run.end_time - run.start_time).total_seconds() * 1000
                        if run.end_time else None
                    ),
                    token_usage=run.extra.get("token_usage"),
                )
                traces.append(trace)

            return traces

        except Exception as e:
            logger.error(f"Failed to retrieve traces: {e}")
            return []

    async def get_stats(
        self,
        engagement_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> ObservabilityStats:
        """
        Get observability statistics.

        Args:
            engagement_id: Optional filter by engagement
            start_time: Optional start time filter
            end_time: Optional end time filter

        Returns:
            ObservabilityStats with aggregated statistics
        """
        if not self.config.tracing_enabled or not self.config.api_key:
            return ObservabilityStats()

        try:
            # Build filter
            filter_parts = []
            if engagement_id:
                filter_parts.append(
                    f'has(metadata, "engagement_id") and eq(metadata["engagement_id"], "{engagement_id}")'
                )

            filter_str = " and ".join(filter_parts) if filter_parts else None

            runs = list(
                self.client.list_runs(
                    project_name=self.config.project,
                    filter=filter_str,
                    start_time=start_time,
                    end_time=end_time,
                    limit=1000,  # Get enough for meaningful stats
                )
            )

            if not runs:
                return ObservabilityStats(
                    time_range_start=start_time,
                    time_range_end=end_time,
                )

            total = len(runs)
            successful = sum(1 for r in runs if r.status == "success")
            failed = sum(1 for r in runs if r.status == "error")

            latencies = []
            total_tokens = 0
            for run in runs:
                if run.end_time and run.start_time:
                    latencies.append(
                        (run.end_time - run.start_time).total_seconds() * 1000
                    )
                token_usage = run.extra.get("token_usage", {})
                total_tokens += token_usage.get("total_tokens", 0)

            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

            # Get feedback stats
            feedbacks = list(self.client.list_feedback(project_name=self.config.project))
            feedback_scores = [f.score for f in feedbacks if f.score is not None]
            avg_score = (
                sum(feedback_scores) / len(feedback_scores)
                if feedback_scores
                else None
            )

            return ObservabilityStats(
                total_traces=total,
                successful_traces=successful,
                failed_traces=failed,
                avg_latency_ms=avg_latency,
                total_tokens=total_tokens,
                feedback_count=len(feedbacks),
                avg_feedback_score=avg_score,
                time_range_start=start_time,
                time_range_end=end_time,
            )

        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return ObservabilityStats()

    def get_dashboard_url(
        self,
        engagement_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> str:
        """
        Get the LangSmith dashboard URL.

        Args:
            engagement_id: Optional engagement to filter by
            run_id: Optional specific run to view

        Returns:
            URL to the LangSmith dashboard
        """
        base_url = self.config.endpoint.rstrip("/")

        # Handle self-hosted vs cloud endpoints
        if "api.smith.langchain.com" in base_url:
            dashboard_url = "https://smith.langchain.com"
        else:
            # For self-hosted, assume dashboard is at same host without /api
            dashboard_url = base_url.replace("/api", "").rstrip("/")

        if run_id:
            return f"{dashboard_url}/runs/{run_id}"
        elif engagement_id:
            return f"{dashboard_url}/projects/{self.config.project}?filter=engagement:{engagement_id}"
        else:
            return f"{dashboard_url}/projects/{self.config.project}"


# Global instance for convenience
_langsmith_instance: Optional[LangSmithObservability] = None


def get_langsmith() -> LangSmithObservability:
    """
    Get the global LangSmith observability instance.

    Returns:
        LangSmithObservability singleton instance
    """
    global _langsmith_instance
    if _langsmith_instance is None:
        _langsmith_instance = LangSmithObservability()
    return _langsmith_instance


def setup_langsmith(config: Optional[LangSmithConfig] = None) -> LangSmithObservability:
    """
    Initialize and return the global LangSmith observability instance.

    Args:
        config: Optional configuration override

    Returns:
        Configured LangSmithObservability instance
    """
    global _langsmith_instance
    _langsmith_instance = LangSmithObservability(config)
    return _langsmith_instance


# Convenience decorators using global instance
def trace_engagement(engagement_id: str, name: Optional[str] = None):
    """Decorator to trace engagement operations using global LangSmith instance."""
    return get_langsmith().trace_engagement(engagement_id, name)


def trace_agent(
    agent_id: str,
    engagement_id: Optional[str] = None,
    name: Optional[str] = None,
):
    """Decorator to trace agent operations using global LangSmith instance."""
    return get_langsmith().trace_agent(agent_id, engagement_id, name)
