"""
Bundle creation and management for deployment artifacts.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from forge_deploy.products.models import Product, ProductComponent


class ArtifactStore(Protocol):
    """Protocol for artifact storage backends."""

    async def upload(self, local_path: Path, remote_key: str) -> str:
        """Upload an artifact and return its URL."""
        ...

    async def download(self, remote_key: str, local_path: Path) -> None:
        """Download an artifact to a local path."""
        ...


class BundleManifest(BaseModel):
    """Manifest describing bundle contents."""

    product_id: str = Field(..., description="Product this bundle is for")
    version: str = Field(..., description="Product version")
    components: list[dict] = Field(
        default_factory=list, description="Component artifact metadata"
    )
    checksum: str = Field("", description="SHA-256 checksum of the bundle")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str = Field(..., description="User who created the bundle")


class Bundle(BaseModel):
    """A deployment bundle artifact."""

    id: str = Field(..., description="Bundle identifier (product_id-version)")
    product_id: str = Field(..., description="Parent product ID")
    version: str = Field(..., description="Product version")
    artifact_url: str = Field(..., description="URL to download the bundle")
    checksum: str = Field(..., description="SHA-256 checksum for verification")
    manifest: BundleManifest = Field(..., description="Bundle contents manifest")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Bundler:
    """
    Creates deployment bundles for products.

    Bundles package all component artifacts into a single deployable
    tarball with a manifest for verification.
    """

    def __init__(self, artifact_store: ArtifactStore) -> None:
        """
        Initialize the bundler.

        Args:
            artifact_store: Backend for storing bundle artifacts
        """
        self._artifacts = artifact_store

    async def create_bundle(
        self,
        product: "Product",
        version: str,
        target_path: Path,
        created_by: str,
    ) -> Bundle:
        """
        Create a deployment bundle for a product version.

        Args:
            product: Product to bundle
            version: Version string to bundle
            target_path: Local directory for building the bundle
            created_by: User creating the bundle

        Returns:
            Bundle metadata with artifact URL

        Raises:
            ValueError: If product has no components
            BundleError: If packaging fails
        """
        # Scaffold - implementation deferred
        raise NotImplementedError("Bundle creation not yet implemented")

    async def _package_component(
        self,
        component: "ProductComponent",
        bundle_dir: Path,
    ) -> dict:
        """
        Package a single component into the bundle.

        Args:
            component: Component to package
            bundle_dir: Directory to place component artifacts

        Returns:
            Component artifact metadata
        """
        # Scaffold - implementation deferred
        raise NotImplementedError("Component packaging not yet implemented")

    def _compute_checksum(self, path: Path) -> str:
        """
        Compute SHA-256 checksum of a file.

        Args:
            path: File to checksum

        Returns:
            Hex-encoded SHA-256 checksum
        """
        import hashlib

        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()


class BundleError(Exception):
    """Raised when bundle creation fails."""

    pass
