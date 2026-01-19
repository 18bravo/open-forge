"""
GraphQL resolvers for Open Forge.
"""
from typing import List, Optional
from datetime import datetime
from uuid import uuid4

import strawberry
from strawberry.types import Info

from api.graphql.types import (
    # Query types
    Engagement,
    EngagementConnection,
    EngagementStatusGQL,
    EngagementPriorityGQL,
    AgentTask,
    AgentTaskConnection,
    AgentTaskStatusGQL,
    DataSource,
    DataSourceConnection,
    DataSourceTypeGQL,
    ApprovalRequest,
    ApprovalRequestConnection,
    ApprovalStatusGQL,
    DataSourceReference,
    # Input types
    EngagementCreateInput,
    EngagementUpdateInput,
    AgentTaskCreateInput,
    ToolApprovalInput,
    ApprovalDecisionInput,
    # Result types
    MutationResult,
    EngagementMutationResult,
    AgentTaskMutationResult,
    ApprovalMutationResult,
)
from core.observability.tracing import traced, add_span_attribute


async def get_user_from_context(info: Info) -> dict:
    """Extract user from request context."""
    request = info.context["request"]
    user_id = request.headers.get("x-user-id", "anonymous")
    return {"user_id": user_id, "username": f"user_{user_id}"}


@strawberry.type
class Query:
    """Root query type."""

    @strawberry.field
    @traced("graphql.engagements")
    async def engagements(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
        status: Optional[EngagementStatusGQL] = None,
        search: Optional[str] = None,
    ) -> EngagementConnection:
        """List engagements with pagination and filtering."""
        add_span_attribute("pagination.page", page)
        add_span_attribute("pagination.page_size", page_size)

        # TODO: Implement database query
        return EngagementConnection(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )

    @strawberry.field
    @traced("graphql.engagement")
    async def engagement(
        self,
        info: Info,
        id: str,
    ) -> Optional[Engagement]:
        """Get a specific engagement by ID."""
        add_span_attribute("engagement.id", id)

        # TODO: Fetch from database
        return None

    @strawberry.field
    @traced("graphql.agent_tasks")
    async def agent_tasks(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
        engagement_id: Optional[str] = None,
        status: Optional[AgentTaskStatusGQL] = None,
    ) -> AgentTaskConnection:
        """List agent tasks with pagination and filtering."""
        add_span_attribute("pagination.page", page)

        # TODO: Implement database query
        return AgentTaskConnection(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )

    @strawberry.field
    @traced("graphql.agent_task")
    async def agent_task(
        self,
        info: Info,
        id: str,
    ) -> Optional[AgentTask]:
        """Get a specific agent task by ID."""
        add_span_attribute("task.id", id)

        # TODO: Fetch from database
        return None

    @strawberry.field
    @traced("graphql.data_sources")
    async def data_sources(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
        source_type: Optional[DataSourceTypeGQL] = None,
        search: Optional[str] = None,
    ) -> DataSourceConnection:
        """List data sources with pagination and filtering."""
        add_span_attribute("pagination.page", page)

        # TODO: Implement database query
        return DataSourceConnection(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )

    @strawberry.field
    @traced("graphql.data_source")
    async def data_source(
        self,
        info: Info,
        id: str,
    ) -> Optional[DataSource]:
        """Get a specific data source by ID."""
        add_span_attribute("data_source.id", id)

        # TODO: Fetch from database
        return None

    @strawberry.field
    @traced("graphql.approvals")
    async def approvals(
        self,
        info: Info,
        page: int = 1,
        page_size: int = 20,
        status: Optional[ApprovalStatusGQL] = None,
        pending_only: bool = False,
    ) -> ApprovalRequestConnection:
        """List approval requests with pagination and filtering."""
        add_span_attribute("pagination.page", page)
        add_span_attribute("filter.pending_only", pending_only)

        # TODO: Implement database query
        return ApprovalRequestConnection(
            items=[],
            total=0,
            page=page,
            page_size=page_size,
            total_pages=0
        )

    @strawberry.field
    @traced("graphql.approval")
    async def approval(
        self,
        info: Info,
        id: str,
    ) -> Optional[ApprovalRequest]:
        """Get a specific approval request by ID."""
        add_span_attribute("approval.id", id)

        # TODO: Fetch from database
        return None


@strawberry.type
class Mutation:
    """Root mutation type."""

    # Engagement mutations

    @strawberry.mutation
    @traced("graphql.create_engagement")
    async def create_engagement(
        self,
        info: Info,
        input: EngagementCreateInput,
    ) -> EngagementMutationResult:
        """Create a new engagement."""
        user = await get_user_from_context(info)
        engagement_id = str(uuid4())
        now = datetime.utcnow()

        add_span_attribute("engagement.id", engagement_id)
        add_span_attribute("engagement.name", input.name)

        # Convert data sources
        data_sources = [
            DataSourceReference(
                source_id=ds.source_id,
                source_type=ds.source_type,
                access_mode=ds.access_mode
            )
            for ds in input.data_sources
        ]

        # TODO: Persist to database
        engagement = Engagement(
            id=engagement_id,
            name=input.name,
            description=input.description,
            objective=input.objective,
            status=EngagementStatusGQL.DRAFT,
            priority=input.priority,
            data_sources=data_sources,
            tags=input.tags,
            requires_approval=input.requires_approval,
            created_by=user["user_id"],
            created_at=now,
            updated_at=now,
            started_at=None,
            completed_at=None,
            error_message=None,
        )

        return EngagementMutationResult(
            success=True,
            message="Engagement created successfully",
            engagement=engagement
        )

    @strawberry.mutation
    @traced("graphql.update_engagement")
    async def update_engagement(
        self,
        info: Info,
        id: str,
        input: EngagementUpdateInput,
    ) -> EngagementMutationResult:
        """Update an existing engagement."""
        add_span_attribute("engagement.id", id)

        # TODO: Implement update
        return EngagementMutationResult(
            success=False,
            message=f"Engagement {id} not found",
            engagement=None
        )

    @strawberry.mutation
    @traced("graphql.delete_engagement")
    async def delete_engagement(
        self,
        info: Info,
        id: str,
    ) -> MutationResult:
        """Delete an engagement."""
        add_span_attribute("engagement.id", id)

        # TODO: Implement deletion
        return MutationResult(
            success=False,
            message=f"Engagement {id} not found",
            id=id
        )

    @strawberry.mutation
    @traced("graphql.execute_engagement")
    async def execute_engagement(
        self,
        info: Info,
        id: str,
    ) -> EngagementMutationResult:
        """Execute an approved engagement."""
        add_span_attribute("engagement.id", id)

        # TODO: Implement execution
        return EngagementMutationResult(
            success=False,
            message=f"Engagement {id} not found",
            engagement=None
        )

    @strawberry.mutation
    @traced("graphql.cancel_engagement")
    async def cancel_engagement(
        self,
        info: Info,
        id: str,
        reason: Optional[str] = None,
    ) -> EngagementMutationResult:
        """Cancel a running engagement."""
        add_span_attribute("engagement.id", id)

        # TODO: Implement cancellation
        return EngagementMutationResult(
            success=False,
            message=f"Engagement {id} not found",
            engagement=None
        )

    # Agent task mutations

    @strawberry.mutation
    @traced("graphql.create_agent_task")
    async def create_agent_task(
        self,
        info: Info,
        input: AgentTaskCreateInput,
    ) -> AgentTaskMutationResult:
        """Create a new agent task."""
        task_id = str(uuid4())
        now = datetime.utcnow()

        add_span_attribute("task.id", task_id)
        add_span_attribute("task.engagement_id", input.engagement_id)

        # TODO: Persist to database
        task = AgentTask(
            id=task_id,
            engagement_id=input.engagement_id,
            task_type=input.task_type,
            description=input.description,
            status=AgentTaskStatusGQL.PENDING,
            input_data=input.input_data,
            output_data=None,
            tools=input.tools,
            max_iterations=input.max_iterations,
            current_iteration=0,
            timeout_seconds=input.timeout_seconds,
            messages=[],
            pending_tool_approvals=[],
            created_at=now,
            started_at=None,
            completed_at=None,
            error_message=None,
        )

        return AgentTaskMutationResult(
            success=True,
            message="Agent task created successfully",
            task=task
        )

    @strawberry.mutation
    @traced("graphql.approve_tool_execution")
    async def approve_tool_execution(
        self,
        info: Info,
        task_id: str,
        input: ToolApprovalInput,
    ) -> AgentTaskMutationResult:
        """Approve or reject a pending tool execution."""
        add_span_attribute("task.id", task_id)
        add_span_attribute("tool_call.id", input.tool_call_id)
        add_span_attribute("tool_call.approved", input.approved)

        # TODO: Implement approval
        return AgentTaskMutationResult(
            success=False,
            message=f"Task {task_id} not found",
            task=None
        )

    @strawberry.mutation
    @traced("graphql.cancel_agent_task")
    async def cancel_agent_task(
        self,
        info: Info,
        id: str,
        reason: Optional[str] = None,
    ) -> AgentTaskMutationResult:
        """Cancel a running agent task."""
        add_span_attribute("task.id", id)

        # TODO: Implement cancellation
        return AgentTaskMutationResult(
            success=False,
            message=f"Task {id} not found",
            task=None
        )

    # Approval mutations

    @strawberry.mutation
    @traced("graphql.decide_approval")
    async def decide_approval(
        self,
        info: Info,
        id: str,
        input: ApprovalDecisionInput,
    ) -> ApprovalMutationResult:
        """Make a decision on an approval request."""
        add_span_attribute("approval.id", id)
        add_span_attribute("decision.approved", input.approved)

        # TODO: Implement decision
        return ApprovalMutationResult(
            success=False,
            message=f"Approval request {id} not found",
            approval=None
        )

    @strawberry.mutation
    @traced("graphql.cancel_approval")
    async def cancel_approval(
        self,
        info: Info,
        id: str,
        reason: Optional[str] = None,
    ) -> ApprovalMutationResult:
        """Cancel a pending approval request."""
        add_span_attribute("approval.id", id)

        # TODO: Implement cancellation
        return ApprovalMutationResult(
            success=False,
            message=f"Approval request {id} not found",
            approval=None
        )
