"""
Data catalog navigator.

Provides browsing and management of data assets in the catalog.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class AssetType(str, Enum):
    """Types of assets in the catalog."""

    DATASET = "dataset"
    TABLE = "table"
    VIEW = "view"
    PIPELINE = "pipeline"
    MODEL = "model"
    DASHBOARD = "dashboard"
    REPORT = "report"


class Owner(BaseModel):
    """Owner of a data asset."""

    id: str
    name: str
    email: str | None = None
    team: str | None = None


class Tag(BaseModel):
    """Tag for categorizing assets."""

    key: str
    value: str | None = None


class ColumnMetadata(BaseModel):
    """Metadata for a column in a dataset."""

    name: str
    data_type: str
    nullable: bool = True
    description: str | None = None
    tags: list[Tag] = Field(default_factory=list)
    pii: bool = False  # Personally identifiable information
    primary_key: bool = False


class SchemaMetadata(BaseModel):
    """Schema information for a data asset."""

    columns: list[ColumnMetadata] = Field(default_factory=list)
    primary_keys: list[str] = Field(default_factory=list)
    foreign_keys: list[dict[str, Any]] = Field(default_factory=list)
    partition_keys: list[str] = Field(default_factory=list)


class DataAsset(BaseModel):
    """
    A data asset in the catalog.

    Represents any discoverable data resource: dataset, table, view, etc.
    """

    id: str
    name: str
    qualified_name: str  # Full path: source.database.schema.table
    asset_type: AssetType
    description: str | None = None

    # Ownership and governance
    owner: Owner | None = None
    stewards: list[Owner] = Field(default_factory=list)
    tags: list[Tag] = Field(default_factory=list)
    classification: str | None = None  # e.g., "confidential", "public"

    # Schema
    schema_metadata: SchemaMetadata | None = None

    # Source information
    source_system: str | None = None
    source_url: str | None = None
    connection_id: str | None = None

    # Statistics
    row_count: int | None = None
    size_bytes: int | None = None
    column_count: int | None = None

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_refreshed_at: datetime | None = None

    # Custom metadata
    custom_properties: dict[str, Any] = Field(default_factory=dict)


class CatalogEntry(BaseModel):
    """
    An entry in the catalog (wrapper around DataAsset with additional context).
    """

    asset: DataAsset
    lineage_upstream_count: int = 0
    lineage_downstream_count: int = 0
    quality_score: float | None = None  # 0-100
    last_quality_check: datetime | None = None
    popularity_score: float = 0.0  # Based on usage


class CatalogNavigator:
    """
    Navigator for browsing the data catalog.

    Provides methods for discovering, registering, and managing
    data assets in the catalog.

    Example:
        navigator = CatalogNavigator()

        # Register a new asset
        asset = await navigator.register_asset(
            name="users",
            asset_type=AssetType.TABLE,
            source_system="postgres",
            qualified_name="prod.public.users"
        )

        # Browse assets
        assets = await navigator.list_assets(
            asset_type=AssetType.TABLE,
            source_system="postgres"
        )

        # Get asset with full context
        entry = await navigator.get_entry("asset-123")
    """

    def __init__(self) -> None:
        self._assets: dict[str, DataAsset] = {}
        self._entries: dict[str, CatalogEntry] = {}

    async def register_asset(
        self,
        name: str,
        asset_type: AssetType,
        qualified_name: str,
        description: str | None = None,
        owner: Owner | None = None,
        tags: list[Tag] | None = None,
        schema_metadata: SchemaMetadata | None = None,
        source_system: str | None = None,
        custom_properties: dict[str, Any] | None = None,
    ) -> DataAsset:
        """
        Register a new asset in the catalog.

        Args:
            name: Asset name
            asset_type: Type of asset
            qualified_name: Fully qualified name
            description: Asset description
            owner: Asset owner
            tags: Asset tags
            schema_metadata: Schema information
            source_system: Source system name
            custom_properties: Custom properties

        Returns:
            The registered DataAsset
        """
        import hashlib

        asset_id = hashlib.sha256(qualified_name.encode()).hexdigest()[:12]

        asset = DataAsset(
            id=asset_id,
            name=name,
            qualified_name=qualified_name,
            asset_type=asset_type,
            description=description,
            owner=owner,
            tags=tags or [],
            schema_metadata=schema_metadata,
            source_system=source_system,
            custom_properties=custom_properties or {},
        )

        self._assets[asset_id] = asset
        self._entries[asset_id] = CatalogEntry(asset=asset)

        return asset

    async def get_asset(self, asset_id: str) -> DataAsset | None:
        """Get an asset by ID."""
        return self._assets.get(asset_id)

    async def get_entry(self, asset_id: str) -> CatalogEntry | None:
        """Get a catalog entry with full context."""
        return self._entries.get(asset_id)

    async def update_asset(
        self,
        asset_id: str,
        updates: dict[str, Any],
    ) -> DataAsset | None:
        """
        Update an asset's metadata.

        Args:
            asset_id: Asset ID
            updates: Fields to update

        Returns:
            Updated asset or None if not found
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return None

        for key, value in updates.items():
            if hasattr(asset, key):
                setattr(asset, key, value)

        asset.updated_at = datetime.utcnow()
        return asset

    async def delete_asset(self, asset_id: str) -> bool:
        """
        Delete an asset from the catalog.

        Args:
            asset_id: Asset ID

        Returns:
            True if deleted
        """
        if asset_id in self._assets:
            del self._assets[asset_id]
            if asset_id in self._entries:
                del self._entries[asset_id]
            return True
        return False

    async def list_assets(
        self,
        asset_type: AssetType | None = None,
        source_system: str | None = None,
        owner_id: str | None = None,
        tags: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[DataAsset]:
        """
        List assets with optional filters.

        Args:
            asset_type: Filter by asset type
            source_system: Filter by source system
            owner_id: Filter by owner ID
            tags: Filter by tags (any match)
            limit: Maximum results
            offset: Skip first N results

        Returns:
            List of matching assets
        """
        assets = list(self._assets.values())

        if asset_type:
            assets = [a for a in assets if a.asset_type == asset_type]

        if source_system:
            assets = [a for a in assets if a.source_system == source_system]

        if owner_id:
            assets = [a for a in assets if a.owner and a.owner.id == owner_id]

        if tags:
            tag_set = set(tags)
            assets = [
                a for a in assets
                if any(t.key in tag_set or t.value in tag_set for t in a.tags)
            ]

        return assets[offset:offset + limit]

    async def get_by_qualified_name(
        self,
        qualified_name: str,
    ) -> DataAsset | None:
        """
        Get an asset by its qualified name.

        Args:
            qualified_name: Fully qualified name

        Returns:
            Asset if found
        """
        for asset in self._assets.values():
            if asset.qualified_name == qualified_name:
                return asset
        return None

    async def add_tag(
        self,
        asset_id: str,
        tag: Tag,
    ) -> bool:
        """
        Add a tag to an asset.

        Args:
            asset_id: Asset ID
            tag: Tag to add

        Returns:
            True if added
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        # Check for duplicate
        if not any(t.key == tag.key and t.value == tag.value for t in asset.tags):
            asset.tags.append(tag)
            asset.updated_at = datetime.utcnow()

        return True

    async def remove_tag(
        self,
        asset_id: str,
        tag_key: str,
    ) -> bool:
        """
        Remove a tag from an asset.

        Args:
            asset_id: Asset ID
            tag_key: Tag key to remove

        Returns:
            True if removed
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        original_count = len(asset.tags)
        asset.tags = [t for t in asset.tags if t.key != tag_key]

        if len(asset.tags) < original_count:
            asset.updated_at = datetime.utcnow()
            return True

        return False

    async def set_owner(
        self,
        asset_id: str,
        owner: Owner,
    ) -> bool:
        """
        Set the owner of an asset.

        Args:
            asset_id: Asset ID
            owner: New owner

        Returns:
            True if updated
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        asset.owner = owner
        asset.updated_at = datetime.utcnow()
        return True

    async def update_statistics(
        self,
        asset_id: str,
        row_count: int | None = None,
        size_bytes: int | None = None,
        column_count: int | None = None,
    ) -> bool:
        """
        Update asset statistics.

        Args:
            asset_id: Asset ID
            row_count: New row count
            size_bytes: New size in bytes
            column_count: New column count

        Returns:
            True if updated
        """
        asset = self._assets.get(asset_id)
        if not asset:
            return False

        if row_count is not None:
            asset.row_count = row_count
        if size_bytes is not None:
            asset.size_bytes = size_bytes
        if column_count is not None:
            asset.column_count = column_count

        asset.last_refreshed_at = datetime.utcnow()
        asset.updated_at = datetime.utcnow()

        return True
