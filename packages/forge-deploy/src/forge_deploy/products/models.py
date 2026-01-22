"""
Product and ProductVersion models for deployment management.
"""

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class ProductStatus(str, Enum):
    """Lifecycle status of a product."""

    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ComponentType(str, Enum):
    """Types of deployable components."""

    APP = "app"
    PIPELINE = "pipeline"
    ONTOLOGY = "ontology"
    CONNECTOR = "connector"
    AGENT = "agent"


class ProductComponent(BaseModel):
    """A component included in a product deployment."""

    name: str = Field(..., description="Component name")
    type: ComponentType = Field(..., description="Type of component")
    source: str = Field(..., description="Package or resource ID reference")
    version_constraint: str | None = Field(
        None, description="Semver constraint (e.g., ^1.0.0, >=2.0.0)"
    )

    class Config:
        use_enum_values = True


class Product(BaseModel):
    """
    A deployable product definition.

    Products bundle multiple components (apps, pipelines, ontologies, connectors)
    into a single deployable unit with versioning and lifecycle management.
    """

    id: str = Field(..., description="Unique product identifier")
    name: str = Field(..., description="Display name")
    description: str | None = Field(None, description="Product description")
    owner_id: str = Field(..., description="User ID of product owner")
    team_id: str | None = Field(None, description="Team ID for shared ownership")

    # Components
    components: list[ProductComponent] = Field(
        default_factory=list, description="Components included in this product"
    )

    # Versioning
    current_version: str | None = Field(None, description="Current active version")
    versions: list[str] = Field(default_factory=list, description="All version strings")

    # Lifecycle
    status: ProductStatus = Field(
        ProductStatus.DRAFT, description="Product lifecycle status"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Metadata
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    documentation_url: str | None = Field(None, description="Link to documentation")
    repository_url: str | None = Field(None, description="Source repository URL")

    class Config:
        use_enum_values = True


class ProductVersion(BaseModel):
    """
    A specific version of a product.

    Captures a snapshot of component versions and build information
    for reproducible deployments.
    """

    id: str = Field(..., description="Unique version identifier")
    product_id: str = Field(..., description="Parent product ID")
    version: str = Field(..., description="Semver version string (e.g., 1.0.0)")
    changelog: str | None = Field(None, description="Version changelog/release notes")

    # Components with pinned versions
    components: list[ProductComponent] = Field(
        default_factory=list, description="Components with resolved version constraints"
    )

    # Build info
    build_id: str | None = Field(None, description="CI/CD build identifier")
    build_timestamp: datetime | None = Field(None, description="When the build was created")

    # Approval workflow
    approved_by: str | None = Field(None, description="User who approved this version")
    approved_at: datetime | None = Field(None, description="When approval was granted")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created this version")
