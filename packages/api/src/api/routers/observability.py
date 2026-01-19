"""
Observability endpoints for LangSmith integration.

Provides API access to trace data, feedback submission, and observability statistics.
"""
from typing import Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from api.dependencies import DbSession, CurrentUser
from api.schemas.common import PaginatedResponse
from core.observability.tracing import traced, add_span_attribute

router = APIRouter(prefix="/observability", tags=["Observability"])


# ============================================================================
# Request/Response Schemas
# ============================================================================


class TraceInfo(BaseModel):
    """Information about a LangSmith trace."""

    run_id: str = Field(description="Unique run identifier")
    trace_id: str = Field(description="Trace identifier")
    name: str = Field(description="Name of the traced operation")
    start_time: datetime = Field(description="When the trace started")
    end_time: Optional[datetime] = Field(default=None, description="When the trace ended")
    status: str = Field(default="running", description="Trace status")
    engagement_id: Optional[str] = Field(
        default=None, description="Associated engagement ID"
    )
    agent_id: Optional[str] = Field(default=None, description="Associated agent ID")
    metadata: dict = Field(default_factory=dict, description="Additional metadata")
    inputs: Optional[dict] = Field(default=None, description="Trace inputs")
    outputs: Optional[dict] = Field(default=None, description="Trace outputs")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    latency_ms: Optional[float] = Field(
        default=None, description="Latency in milliseconds"
    )
    token_usage: Optional[dict] = Field(
        default=None, description="Token usage statistics"
    )


class FeedbackCreate(BaseModel):
    """Request body for submitting feedback."""

    run_id: str = Field(description="Run ID to provide feedback for")
    score: float = Field(ge=0.0, le=1.0, description="Feedback score (0.0-1.0)")
    comment: Optional[str] = Field(default=None, description="Optional feedback comment")
    key: str = Field(default="user_feedback", description="Feedback key/category")


class FeedbackResponse(BaseModel):
    """Response after submitting feedback."""

    run_id: str = Field(description="Run ID feedback was submitted for")
    score: float = Field(description="Submitted score")
    comment: Optional[str] = Field(default=None, description="Submitted comment")
    key: str = Field(description="Feedback key")
    submitted_at: datetime = Field(description="When feedback was submitted")
    submitted_by: str = Field(description="User who submitted feedback")


class ObservabilityStats(BaseModel):
    """Statistics about observability data."""

    total_traces: int = Field(default=0, description="Total number of traces")
    successful_traces: int = Field(
        default=0, description="Number of successful traces"
    )
    failed_traces: int = Field(default=0, description="Number of failed traces")
    avg_latency_ms: float = Field(
        default=0.0, description="Average latency in milliseconds"
    )
    total_tokens: int = Field(default=0, description="Total tokens used")
    feedback_count: int = Field(
        default=0, description="Number of feedback submissions"
    )
    avg_feedback_score: Optional[float] = Field(
        default=None, description="Average feedback score"
    )
    time_range_start: Optional[datetime] = Field(
        default=None, description="Stats start time"
    )
    time_range_end: Optional[datetime] = Field(default=None, description="Stats end time")
    top_operations: list[dict] = Field(
        default_factory=list, description="Most frequent operations"
    )
    error_breakdown: dict = Field(
        default_factory=dict, description="Error types and counts"
    )


class DashboardUrlResponse(BaseModel):
    """Response containing LangSmith dashboard URL."""

    url: str = Field(description="LangSmith dashboard URL")
    engagement_id: Optional[str] = Field(default=None, description="Filter engagement ID")
    run_id: Optional[str] = Field(default=None, description="Specific run ID")


# ============================================================================
# Endpoints
# ============================================================================


@router.get(
    "/traces/{engagement_id}",
    response_model=PaginatedResponse[TraceInfo],
    summary="Get traces for engagement",
    description="Returns traces associated with a specific engagement",
)
@traced("observability.get_engagement_traces")
async def get_engagement_traces(
    engagement_id: str,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(
        default=None,
        alias="status",
        description="Filter by status (success, error, running)",
    ),
    start_time: Optional[datetime] = Query(
        default=None, description="Filter traces after this time"
    ),
    end_time: Optional[datetime] = Query(
        default=None, description="Filter traces before this time"
    ),
) -> PaginatedResponse[TraceInfo]:
    """
    Get traces for a specific engagement from LangSmith.

    Retrieves all traced operations associated with the engagement,
    including agent runs, tool calls, and LLM interactions.
    """
    add_span_attribute("engagement.id", engagement_id)
    add_span_attribute("pagination.page", page)
    add_span_attribute("pagination.page_size", page_size)

    try:
        # Import LangSmith integration
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        # Get traces from LangSmith
        traces = await langsmith.get_engagement_traces(
            engagement_id=engagement_id,
            limit=page_size * page,  # Get enough for pagination
            start_time=start_time,
            end_time=end_time,
        )

        # Apply status filter
        if status_filter:
            traces = [t for t in traces if t.status == status_filter]

        # Calculate pagination
        total = len(traces)
        offset = (page - 1) * page_size
        paginated_traces = traces[offset : offset + page_size]

        # Convert to response model
        items = [
            TraceInfo(
                run_id=t.run_id,
                trace_id=t.trace_id,
                name=t.name,
                start_time=t.start_time,
                end_time=t.end_time,
                status=t.status,
                engagement_id=t.engagement_id,
                agent_id=t.agent_id,
                metadata=t.metadata,
                inputs=t.inputs,
                outputs=t.outputs,
                error=t.error,
                latency_ms=t.latency_ms,
                token_usage=t.token_usage,
            )
            for t in paginated_traces
        ]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except ImportError:
        # LangSmith not available, return empty response
        return PaginatedResponse.create(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve traces: {str(e)}",
        )


@router.get(
    "/traces/agent/{agent_id}",
    response_model=PaginatedResponse[TraceInfo],
    summary="Get traces for agent",
    description="Returns traces associated with a specific agent",
)
@traced("observability.get_agent_traces")
async def get_agent_traces(
    agent_id: str,
    db: DbSession,
    user: CurrentUser,
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=20, ge=1, le=100, description="Items per page"),
    engagement_id: Optional[str] = Query(
        default=None, description="Filter by engagement"
    ),
    start_time: Optional[datetime] = Query(
        default=None, description="Filter traces after this time"
    ),
    end_time: Optional[datetime] = Query(
        default=None, description="Filter traces before this time"
    ),
) -> PaginatedResponse[TraceInfo]:
    """
    Get traces for a specific agent from LangSmith.

    Retrieves all traced operations for the agent, optionally filtered by engagement.
    """
    add_span_attribute("agent.id", agent_id)
    add_span_attribute("pagination.page", page)

    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        traces = await langsmith.get_agent_traces(
            agent_id=agent_id,
            limit=page_size * page,
            start_time=start_time,
            end_time=end_time,
        )

        # Filter by engagement if provided
        if engagement_id:
            traces = [t for t in traces if t.engagement_id == engagement_id]

        total = len(traces)
        offset = (page - 1) * page_size
        paginated_traces = traces[offset : offset + page_size]

        items = [
            TraceInfo(
                run_id=t.run_id,
                trace_id=t.trace_id,
                name=t.name,
                start_time=t.start_time,
                end_time=t.end_time,
                status=t.status,
                engagement_id=t.engagement_id,
                agent_id=t.agent_id,
                metadata=t.metadata,
                inputs=t.inputs,
                outputs=t.outputs,
                error=t.error,
                latency_ms=t.latency_ms,
                token_usage=t.token_usage,
            )
            for t in paginated_traces
        ]

        return PaginatedResponse.create(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
        )

    except ImportError:
        return PaginatedResponse.create(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve traces: {str(e)}",
        )


@router.post(
    "/feedback",
    response_model=FeedbackResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit feedback",
    description="Submit feedback on a specific trace run",
)
@traced("observability.submit_feedback")
async def submit_feedback(
    feedback: FeedbackCreate,
    db: DbSession,
    user: CurrentUser,
) -> FeedbackResponse:
    """
    Submit feedback for a specific run.

    Feedback is recorded in LangSmith and can be used for evaluation,
    fine-tuning, and quality monitoring.
    """
    add_span_attribute("feedback.run_id", feedback.run_id)
    add_span_attribute("feedback.score", feedback.score)
    add_span_attribute("feedback.key", feedback.key)

    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        result = await langsmith.log_feedback(
            run_id=feedback.run_id,
            score=feedback.score,
            comment=feedback.comment,
            key=feedback.key,
            submitted_by=user.user_id,
        )

        return FeedbackResponse(
            run_id=result.run_id,
            score=result.score,
            comment=result.comment,
            key=result.key,
            submitted_at=result.submitted_at,
            submitted_by=user.user_id,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LangSmith integration not available",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to submit feedback: {str(e)}",
        )


@router.get(
    "/stats",
    response_model=ObservabilityStats,
    summary="Get observability statistics",
    description="Returns aggregated statistics about traces and feedback",
)
@traced("observability.get_stats")
async def get_observability_stats(
    db: DbSession,
    user: CurrentUser,
    engagement_id: Optional[str] = Query(
        default=None, description="Filter by engagement"
    ),
    start_time: Optional[datetime] = Query(
        default=None, description="Start time for stats window"
    ),
    end_time: Optional[datetime] = Query(
        default=None, description="End time for stats window"
    ),
) -> ObservabilityStats:
    """
    Get aggregated observability statistics.

    Returns metrics including trace counts, success rates, latency,
    token usage, and feedback summaries.
    """
    if engagement_id:
        add_span_attribute("engagement.id", engagement_id)

    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        stats = await langsmith.get_stats(
            engagement_id=engagement_id,
            start_time=start_time,
            end_time=end_time,
        )

        return ObservabilityStats(
            total_traces=stats.total_traces,
            successful_traces=stats.successful_traces,
            failed_traces=stats.failed_traces,
            avg_latency_ms=stats.avg_latency_ms,
            total_tokens=stats.total_tokens,
            feedback_count=stats.feedback_count,
            avg_feedback_score=stats.avg_feedback_score,
            time_range_start=stats.time_range_start,
            time_range_end=stats.time_range_end,
            top_operations=[],  # TODO: Implement top operations aggregation
            error_breakdown={},  # TODO: Implement error breakdown
        )

    except ImportError:
        return ObservabilityStats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get statistics: {str(e)}",
        )


@router.get(
    "/dashboard-url",
    response_model=DashboardUrlResponse,
    summary="Get LangSmith dashboard URL",
    description="Returns the URL to the LangSmith dashboard for an engagement or run",
)
@traced("observability.get_dashboard_url")
async def get_dashboard_url(
    user: CurrentUser,
    engagement_id: Optional[str] = Query(
        default=None, description="Filter by engagement"
    ),
    run_id: Optional[str] = Query(default=None, description="Specific run to view"),
) -> DashboardUrlResponse:
    """
    Get the URL to the LangSmith dashboard.

    Can be filtered to show traces for a specific engagement or a specific run.
    """
    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        url = langsmith.get_dashboard_url(
            engagement_id=engagement_id,
            run_id=run_id,
        )

        return DashboardUrlResponse(
            url=url,
            engagement_id=engagement_id,
            run_id=run_id,
        )

    except ImportError:
        # Return a placeholder URL if LangSmith is not configured
        return DashboardUrlResponse(
            url="https://smith.langchain.com",
            engagement_id=engagement_id,
            run_id=run_id,
        )


@router.get(
    "/trace/{run_id}",
    response_model=TraceInfo,
    summary="Get single trace",
    description="Returns details for a specific trace by run ID",
)
@traced("observability.get_trace")
async def get_trace(
    run_id: str,
    db: DbSession,
    user: CurrentUser,
) -> TraceInfo:
    """
    Get detailed information about a specific trace.
    """
    add_span_attribute("run_id", run_id)

    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        # Get the run from LangSmith
        run = langsmith.client.read_run(run_id)

        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trace {run_id} not found",
            )

        return TraceInfo(
            run_id=str(run.id),
            trace_id=str(run.trace_id) if run.trace_id else str(run.id),
            name=run.name,
            start_time=run.start_time,
            end_time=run.end_time,
            status="success" if run.status == "success" else (
                "error" if run.status == "error" else "running"
            ),
            engagement_id=run.extra.get("metadata", {}).get("engagement_id"),
            agent_id=run.extra.get("metadata", {}).get("agent_id"),
            metadata=run.extra.get("metadata", {}),
            inputs=run.inputs,
            outputs=run.outputs,
            error=str(run.error) if run.error else None,
            latency_ms=(
                (run.end_time - run.start_time).total_seconds() * 1000
                if run.end_time
                else None
            ),
            token_usage=run.extra.get("token_usage"),
        )

    except ImportError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LangSmith integration not available",
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve trace: {str(e)}",
        )


@router.get(
    "/health",
    summary="Check LangSmith health",
    description="Check the health and connectivity of LangSmith integration",
)
@traced("observability.health_check")
async def langsmith_health_check():
    """
    Check LangSmith integration health.

    Returns the status of the LangSmith connection and configuration.
    """
    try:
        from core.observability.langsmith import get_langsmith

        langsmith = get_langsmith()

        # Check if we can connect to LangSmith
        is_configured = bool(langsmith.config.api_key)
        is_enabled = langsmith.config.tracing_enabled

        if is_configured:
            try:
                # Try to list projects to verify connectivity
                projects = list(langsmith.client.list_projects(limit=1))
                is_connected = True
            except Exception:
                is_connected = False
        else:
            is_connected = False

        return {
            "status": "healthy" if is_connected else "degraded",
            "configured": is_configured,
            "enabled": is_enabled,
            "connected": is_connected,
            "project": langsmith.config.project,
            "endpoint": langsmith.config.endpoint,
        }

    except ImportError:
        return {
            "status": "unavailable",
            "configured": False,
            "enabled": False,
            "connected": False,
            "error": "langsmith package not installed",
        }
