"""
Tests for products module.
"""

import pytest
from datetime import datetime

from forge_deploy.products.models import (
    Product,
    ProductComponent,
    ProductStatus,
    ProductVersion,
    ComponentType,
)
from forge_deploy.products.bundle import Bundle, BundleManifest, Bundler


class TestProductModels:
    """Tests for Product and ProductVersion models."""

    def test_product_creation(self) -> None:
        """Test creating a basic product."""
        product = Product(
            id="test-product-1",
            name="Test Product",
            owner_id="user-123",
        )

        assert product.id == "test-product-1"
        assert product.name == "Test Product"
        assert product.status == ProductStatus.DRAFT
        assert product.components == []
        assert product.versions == []

    def test_product_with_components(self) -> None:
        """Test creating a product with components."""
        components = [
            ProductComponent(
                name="api",
                type=ComponentType.APP,
                source="forge-api:1.0.0",
            ),
            ProductComponent(
                name="pipeline",
                type=ComponentType.PIPELINE,
                source="data-pipeline:2.0.0",
                version_constraint=">=2.0.0",
            ),
        ]

        product = Product(
            id="test-product-2",
            name="Multi-Component Product",
            owner_id="user-123",
            components=components,
        )

        assert len(product.components) == 2
        assert product.components[0].type == "app"
        assert product.components[1].version_constraint == ">=2.0.0"

    def test_product_version_creation(self) -> None:
        """Test creating a product version."""
        version = ProductVersion(
            id="version-1",
            product_id="test-product-1",
            version="1.0.0",
            changelog="Initial release",
            created_by="user-123",
        )

        assert version.version == "1.0.0"
        assert version.approved_by is None
        assert version.build_id is None

    def test_product_status_transitions(self) -> None:
        """Test product status values."""
        assert ProductStatus.DRAFT.value == "draft"
        assert ProductStatus.ACTIVE.value == "active"
        assert ProductStatus.DEPRECATED.value == "deprecated"
        assert ProductStatus.ARCHIVED.value == "archived"


class TestBundleModels:
    """Tests for Bundle and BundleManifest models."""

    def test_bundle_manifest_creation(self) -> None:
        """Test creating a bundle manifest."""
        manifest = BundleManifest(
            product_id="test-product-1",
            version="1.0.0",
            components=[
                {"name": "api", "artifact": "api.tar.gz"},
            ],
            checksum="abc123",
            created_by="user-123",
        )

        assert manifest.product_id == "test-product-1"
        assert manifest.version == "1.0.0"
        assert len(manifest.components) == 1

    def test_bundle_creation(self) -> None:
        """Test creating a bundle."""
        manifest = BundleManifest(
            product_id="test-product-1",
            version="1.0.0",
            components=[],
            checksum="abc123",
            created_by="user-123",
        )

        bundle = Bundle(
            id="test-product-1-1.0.0",
            product_id="test-product-1",
            version="1.0.0",
            artifact_url="s3://bundles/test-product-1/1.0.0.tar.gz",
            checksum="abc123",
            manifest=manifest,
        )

        assert bundle.id == "test-product-1-1.0.0"
        assert bundle.artifact_url.startswith("s3://")
