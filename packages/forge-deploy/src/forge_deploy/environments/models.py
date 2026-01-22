"""
Environment models for deployment targets.
"""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class EnvironmentType(str, Enum):
    """Types of deployment environments."""

    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class EnvironmentVariable(BaseModel):
    """
    An environment variable configuration.

    Supports both direct values and references to external secrets.
    """

    key: str = Field(..., description="Variable name")
    value: str | None = Field(None, description="Direct value (if not secret)")
    secret: bool = Field(False, description="Whether this is a secret")
    secret_ref: str | None = Field(
        None, description="Reference to external secret (e.g., vault path)"
    )

    class Config:
        # Prevent accidental exposure of secrets
        json_schema_extra = {
            "examples": [
                {"key": "LOG_LEVEL", "value": "INFO", "secret": False},
                {"key": "DB_PASSWORD", "secret": True, "secret_ref": "vault:db/password"},
            ]
        }


class Environment(BaseModel):
    """
    A deployment target environment.

    Environments represent distinct deployment targets (dev, staging, prod)
    with their own configuration, infrastructure, and promotion rules.
    """

    id: str = Field(..., description="Unique environment identifier")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Environment description")
    type: EnvironmentType = Field(..., description="Environment type/tier")

    # Infrastructure
    cluster_id: str = Field(..., description="Kubernetes cluster identifier")
    namespace: str = Field(..., description="Kubernetes namespace")
    region: str | None = Field(None, description="Cloud region")

    # Configuration
    config: dict = Field(
        default_factory=dict, description="Environment-specific configuration"
    )
    variables: list[EnvironmentVariable] = Field(
        default_factory=list, description="Environment variables"
    )
    secrets_ref: str | None = Field(
        None, description="External secrets reference (e.g., AWS Secrets Manager ARN)"
    )

    # Promotion chain
    promotion_from: str | None = Field(
        None, description="Environment ID to promote from"
    )
    auto_promote: bool = Field(
        False, description="Automatically promote successful deployments"
    )
    promotion_rules: dict | None = Field(
        None, description="Rules that must pass before promotion"
    )

    # Protection
    protected: bool = Field(
        False, description="Require approval for deployments"
    )
    required_approvers: list[str] = Field(
        default_factory=list, description="User IDs required to approve"
    )
    minimum_approvals: int = Field(
        1, description="Minimum number of approvals required"
    )

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        use_enum_values = True

    def is_protected(self) -> bool:
        """Check if this environment requires approval."""
        return self.protected or len(self.required_approvers) > 0

    def can_receive_promotion_from(self, source_env_id: str) -> bool:
        """Check if this environment can receive promotions from another."""
        return self.promotion_from == source_env_id
