"""
Pydantic schemas for API request/response models.
"""
from api.schemas.common import (
    PaginationParams,
    PaginatedResponse,
    ErrorResponse,
    SuccessResponse,
)
from api.schemas.engagement import (
    EngagementCreate,
    EngagementUpdate,
    EngagementResponse,
    EngagementStatus,
)
from api.schemas.agent import (
    AgentTaskCreate,
    AgentTaskResponse,
    AgentTaskStatus,
    AgentMessage,
)

__all__ = [
    # Common
    "PaginationParams",
    "PaginatedResponse",
    "ErrorResponse",
    "SuccessResponse",
    # Engagement
    "EngagementCreate",
    "EngagementUpdate",
    "EngagementResponse",
    "EngagementStatus",
    # Agent
    "AgentTaskCreate",
    "AgentTaskResponse",
    "AgentTaskStatus",
    "AgentMessage",
]
