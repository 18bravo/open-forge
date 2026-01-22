"""
Deployment models and status tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class DeploymentStatus(str, Enum):
    """Status of a deployment operation."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


class DeploymentStrategyType(str, Enum):
    """Available deployment strategies."""

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class Deployment(BaseModel):
    """
    A deployment operation record.

    Tracks the state and progress of deploying a product version
    to a specific environment.
    """

    id: str = Field(..., description="Unique deployment identifier")
    product_id: str = Field(..., description="Product being deployed")
    version: str = Field(..., description="Version being deployed")
    environment_id: str = Field(..., description="Target environment")

    # Status tracking
    status: DeploymentStatus = Field(
        DeploymentStatus.PENDING, description="Current deployment status"
    )
    progress: int = Field(0, ge=0, le=100, description="Progress percentage (0-100)")

    # Strategy configuration
    strategy: DeploymentStrategyType = Field(
        DeploymentStrategyType.ROLLING, description="Deployment strategy to use"
    )
    strategy_config: dict = Field(
        default_factory=dict, description="Strategy-specific configuration"
    )

    # Timing
    started_at: datetime | None = Field(None, description="When deployment started")
    completed_at: datetime | None = Field(None, description="When deployment completed")
    duration_seconds: int | None = Field(None, description="Total deployment duration")

    # Actors
    initiated_by: str = Field(..., description="User who initiated the deployment")
    approved_by: str | None = Field(None, description="User who approved (if required)")

    # Results
    deployed_components: list[str] = Field(
        default_factory=list, description="Components successfully deployed"
    )
    error_message: str | None = Field(None, description="Error message if failed")
    logs_url: str | None = Field(None, description="URL to deployment logs")

    # Metadata
    created_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True


class DeploymentEvent(BaseModel):
    """
    An event that occurred during a deployment.

    Events provide an audit trail and debugging information
    for deployment operations.
    """

    id: str = Field(..., description="Unique event identifier")
    deployment_id: str = Field(..., description="Parent deployment")
    event_type: str = Field(
        ..., description="Type of event (e.g., 'started', 'progress', 'health_check')"
    )
    message: str = Field(..., description="Human-readable event message")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict = Field(default_factory=dict, description="Additional event data")


class DeploymentError(Exception):
    """Raised when a deployment operation fails."""

    def __init__(self, message: str, deployment_id: str | None = None) -> None:
        super().__init__(message)
        self.deployment_id = deployment_id


class RollbackError(Exception):
    """Raised when a rollback operation fails."""

    def __init__(self, message: str, deployment_id: str | None = None) -> None:
        super().__init__(message)
        self.deployment_id = deployment_id
