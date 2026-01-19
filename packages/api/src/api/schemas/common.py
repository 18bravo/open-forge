"""
Common schemas shared across API endpoints.
"""
from typing import Any, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list endpoints."""
    page: int = Field(default=1, ge=1, description="Page number (1-indexed)")
    page_size: int = Field(default=20, ge=1, le=100, description="Items per page")

    @property
    def offset(self) -> int:
        """Calculate offset for database query."""
        return (self.page - 1) * self.page_size

    @property
    def limit(self) -> int:
        """Limit for database query."""
        return self.page_size


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response wrapper."""
    items: List[T]
    total: int = Field(description="Total number of items")
    page: int = Field(description="Current page number")
    page_size: int = Field(description="Items per page")
    total_pages: int = Field(description="Total number of pages")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create a paginated response from items and pagination info."""
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages
        )


class ErrorDetail(BaseModel):
    """Detailed error information."""
    field: Optional[str] = Field(default=None, description="Field that caused the error")
    message: str = Field(description="Error message")
    code: Optional[str] = Field(default=None, description="Error code")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(description="Error type")
    message: str = Field(description="Human-readable error message")
    details: Optional[List[ErrorDetail]] = Field(default=None, description="Detailed errors")
    request_id: Optional[str] = Field(default=None, description="Request ID for tracing")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SuccessResponse(BaseModel):
    """Generic success response."""
    success: bool = Field(default=True)
    message: str = Field(description="Success message")
    data: Optional[Any] = Field(default=None, description="Optional response data")


class HealthStatus(BaseModel):
    """Health check status."""
    status: str = Field(description="Overall health status")
    version: str = Field(description="API version")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    components: dict[str, str] = Field(
        default_factory=dict,
        description="Individual component health statuses"
    )


class UserContext(BaseModel):
    """Current user context."""
    user_id: str = Field(description="User ID")
    username: str = Field(description="Username")
    email: Optional[str] = Field(default=None, description="User email")
    roles: List[str] = Field(default_factory=list, description="User roles")
    permissions: List[str] = Field(default_factory=list, description="User permissions")
