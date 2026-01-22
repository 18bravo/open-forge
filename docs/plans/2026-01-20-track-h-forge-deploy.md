# Track H: Forge Deployment Platform Design

**Date:** 2026-01-20
**Status:** Draft
**Track:** H - Deployment
**Dependencies:** api, all other tracks

---

## Executive Summary

Track H implements deployment and distribution capabilities for Open Forge, providing continuous delivery, marketplace functionality, edge deployment, and public-facing consumer apps. This track addresses ~10+ deployment features that enable production operations.

### Key Packages

| Package | Purpose |
|---------|---------|
| `forge-orbit` | Continuous delivery platform |
| `forge-exchange` | Marketplace for solutions |
| `forge-edge` | Edge/offline deployment |
| `forge-consumer` | Public-facing apps |

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       FORGE DEPLOYMENT PLATFORM                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         FORGE ORBIT (CD)                               │  │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────────────┐  │  │
│  │  │  Products │  │ Bundles   │  │ Enviro-   │  │    Rollouts       │  │  │
│  │  │  Registry │  │ Packager  │  │ ments     │  │    & Rollbacks    │  │  │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                      │                                       │
│                                      ▼                                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │ FORGE EXCHANGE  │  │   FORGE EDGE    │  │     FORGE CONSUMER          │  │
│  ├─────────────────┤  ├─────────────────┤  ├─────────────────────────────┤  │
│  │  Solution Pkgs  │  │  Edge Runtime   │  │  Public App Hosting         │  │
│  │  Catalog        │  │  Offline Sync   │  │  Embed SDK                  │  │
│  │  Installation   │  │  Conflict Res   │  │  Custom Domains             │  │
│  │  Reviews        │  │  Field Updates  │  │  Analytics                  │  │
│  └─────────────────┘  └─────────────────┘  └─────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                    INFRASTRUCTURE LAYER                                │  │
│  │  ┌──────────────┐  ┌────────────┐  ┌────────────┐  ┌──────────────┐  │  │
│  │  │  Kubernetes  │  │   Helm     │  │  Terraform │  │   GitOps     │  │  │
│  │  │  Operator    │  │   Charts   │  │   Modules  │  │  (ArgoCD)    │  │  │
│  │  └──────────────┘  └────────────┘  └────────────┘  └──────────────┘  │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Package 1: Forge Orbit

### Purpose

Continuous delivery platform for managing products, bundles, environments, and deployments.

### Module Structure

```
packages/forge-orbit/
├── src/
│   └── forge_orbit/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── product.py         # Product definition
│       │   ├── bundle.py          # Deployment bundle
│       │   ├── environment.py     # Environment config
│       │   ├── release.py         # Release/version
│       │   └── deployment.py      # Deployment record
│       ├── packaging/
│       │   ├── __init__.py
│       │   ├── bundler.py         # Bundle creation
│       │   ├── manifest.py        # Manifest generation
│       │   └── artifacts.py       # Artifact management
│       ├── deployment/
│       │   ├── __init__.py
│       │   ├── engine.py          # Deployment engine
│       │   ├── strategies.py      # Deployment strategies
│       │   ├── rollback.py        # Rollback operations
│       │   └── health.py          # Health checks
│       ├── gitops/
│       │   ├── __init__.py
│       │   ├── sync.py            # GitOps sync
│       │   └── argocd.py          # ArgoCD integration
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/product.py
from pydantic import BaseModel
from datetime import datetime
from typing import Any

class ProductComponent(BaseModel):
    name: str
    type: str  # "app", "pipeline", "ontology", "connector"
    source: str  # Package or resource ID
    version_constraint: str | None = None  # Semver constraint

class Product(BaseModel):
    id: str
    name: str
    description: str | None = None
    owner_id: str
    team_id: str | None = None

    # Components
    components: list[ProductComponent]

    # Versioning
    current_version: str | None = None
    versions: list[str] = []

    # Lifecycle
    status: Literal["draft", "active", "deprecated", "archived"] = "draft"
    created_at: datetime
    updated_at: datetime

    # Metadata
    tags: list[str] = []
    documentation_url: str | None = None
    repository_url: str | None = None

class ProductVersion(BaseModel):
    id: str
    product_id: str
    version: str  # Semver: 1.0.0
    changelog: str | None = None

    # Components with pinned versions
    components: list[ProductComponent]

    # Build info
    build_id: str | None = None
    build_timestamp: datetime | None = None

    # Approval
    approved_by: str | None = None
    approved_at: datetime | None = None

    created_at: datetime
    created_by: str
```

```python
# models/environment.py
class Environment(BaseModel):
    id: str
    name: str
    description: str | None = None
    type: Literal["development", "staging", "production", "edge"]

    # Infrastructure
    cluster_id: str
    namespace: str
    region: str | None = None

    # Configuration
    config: dict = {}
    secrets_ref: str | None = None  # External secrets reference

    # Promotion
    promotion_from: str | None = None  # Previous environment in chain
    auto_promote: bool = False
    promotion_rules: dict | None = None

    # Protection
    protected: bool = False
    required_approvers: list[str] = []

    created_at: datetime
    updated_at: datetime

class EnvironmentVariable(BaseModel):
    key: str
    value: str | None = None
    secret: bool = False
    secret_ref: str | None = None  # Reference to external secret
```

```python
# models/deployment.py
class DeploymentStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"

class Deployment(BaseModel):
    id: str
    product_id: str
    version: str
    environment_id: str

    # Status
    status: DeploymentStatus = DeploymentStatus.PENDING
    progress: int = 0  # 0-100

    # Strategy
    strategy: Literal["rolling", "blue_green", "canary", "recreate"] = "rolling"
    strategy_config: dict = {}

    # Timing
    started_at: datetime | None = None
    completed_at: datetime | None = None
    duration_seconds: int | None = None

    # Actors
    initiated_by: str
    approved_by: str | None = None

    # Results
    deployed_components: list[str] = []
    error_message: str | None = None
    logs_url: str | None = None

    created_at: datetime

class DeploymentEvent(BaseModel):
    id: str
    deployment_id: str
    event_type: str
    message: str
    timestamp: datetime
    metadata: dict = {}
```

```python
# packaging/bundler.py
import tarfile
import hashlib
import json
from pathlib import Path

class BundleManifest(BaseModel):
    product_id: str
    version: str
    components: list[dict]
    checksum: str
    created_at: datetime
    created_by: str

class Bundler:
    """Create deployment bundles."""

    def __init__(self, artifact_store: "ArtifactStore"):
        self.artifacts = artifact_store

    async def create_bundle(
        self,
        product: Product,
        version: str,
        target_path: Path
    ) -> "Bundle":
        """Create a deployment bundle for a product version."""
        bundle_dir = target_path / f"{product.id}-{version}"
        bundle_dir.mkdir(parents=True, exist_ok=True)

        # Collect component artifacts
        components = []
        for component in product.components:
            artifact = await self._package_component(component, bundle_dir)
            components.append(artifact)

        # Generate manifest
        manifest = BundleManifest(
            product_id=product.id,
            version=version,
            components=components,
            checksum="",  # Computed below
            created_at=datetime.utcnow(),
            created_by=self._get_current_user()
        )

        manifest_path = bundle_dir / "manifest.json"
        manifest_path.write_text(manifest.json(indent=2))

        # Create tarball
        bundle_path = target_path / f"{product.id}-{version}.tar.gz"
        with tarfile.open(bundle_path, "w:gz") as tar:
            tar.add(bundle_dir, arcname=f"{product.id}-{version}")

        # Compute checksum
        checksum = self._compute_checksum(bundle_path)
        manifest.checksum = checksum

        # Upload to artifact store
        artifact_url = await self.artifacts.upload(bundle_path, f"bundles/{product.id}/{version}")

        return Bundle(
            id=f"{product.id}-{version}",
            product_id=product.id,
            version=version,
            artifact_url=artifact_url,
            checksum=checksum,
            manifest=manifest,
            created_at=datetime.utcnow()
        )

    async def _package_component(
        self,
        component: ProductComponent,
        bundle_dir: Path
    ) -> dict:
        """Package a single component."""
        if component.type == "app":
            return await self._package_app(component, bundle_dir)
        elif component.type == "pipeline":
            return await self._package_pipeline(component, bundle_dir)
        elif component.type == "ontology":
            return await self._package_ontology(component, bundle_dir)
        elif component.type == "connector":
            return await self._package_connector(component, bundle_dir)

        raise ValueError(f"Unknown component type: {component.type}")

    def _compute_checksum(self, path: Path) -> str:
        """Compute SHA-256 checksum."""
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()
```

```python
# deployment/engine.py
class DeploymentEngine:
    """Execute deployments."""

    def __init__(
        self,
        kubernetes: "KubernetesClient",
        health_checker: "HealthChecker"
    ):
        self.k8s = kubernetes
        self.health = health_checker

    async def deploy(
        self,
        deployment: Deployment,
        bundle: Bundle,
        environment: Environment
    ) -> Deployment:
        """Execute a deployment."""
        deployment.status = DeploymentStatus.IN_PROGRESS
        deployment.started_at = datetime.utcnow()

        try:
            strategy = self._get_strategy(deployment.strategy)

            # Execute deployment
            async for progress in strategy.execute(
                bundle=bundle,
                environment=environment,
                config=deployment.strategy_config
            ):
                deployment.progress = progress
                await self._emit_event(deployment, "progress", f"Progress: {progress}%")

            # Verify health
            healthy = await self.health.check_deployment(deployment, environment)
            if not healthy:
                raise DeploymentError("Health check failed")

            deployment.status = DeploymentStatus.SUCCEEDED
            deployment.deployed_components = [c.name for c in bundle.manifest.components]

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)

            # Auto-rollback if configured
            if deployment.strategy_config.get("auto_rollback", True):
                await self.rollback(deployment, environment)

        finally:
            deployment.completed_at = datetime.utcnow()
            deployment.duration_seconds = int(
                (deployment.completed_at - deployment.started_at).total_seconds()
            )

        return deployment

    async def rollback(
        self,
        deployment: Deployment,
        environment: Environment,
        target_version: str | None = None
    ) -> Deployment:
        """Rollback to previous version."""
        # Find previous successful deployment
        if target_version:
            previous = await self._get_deployment_by_version(
                deployment.product_id,
                environment.id,
                target_version
            )
        else:
            previous = await self._get_previous_successful_deployment(
                deployment.product_id,
                environment.id
            )

        if not previous:
            raise RollbackError("No previous deployment to rollback to")

        # Get bundle for previous version
        bundle = await self._get_bundle(previous.product_id, previous.version)

        # Create rollback deployment
        rollback_deployment = Deployment(
            id=str(uuid.uuid4()),
            product_id=deployment.product_id,
            version=previous.version,
            environment_id=environment.id,
            strategy=deployment.strategy,
            initiated_by="system",
            created_at=datetime.utcnow()
        )

        # Execute rollback
        return await self.deploy(rollback_deployment, bundle, environment)
```

```python
# deployment/strategies.py
from abc import ABC, abstractmethod
from typing import AsyncIterator

class DeploymentStrategy(ABC):
    """Abstract deployment strategy."""

    @abstractmethod
    async def execute(
        self,
        bundle: Bundle,
        environment: Environment,
        config: dict
    ) -> AsyncIterator[int]:
        """Execute deployment, yielding progress 0-100."""
        pass

class RollingStrategy(DeploymentStrategy):
    """Rolling update deployment."""

    async def execute(
        self,
        bundle: Bundle,
        environment: Environment,
        config: dict
    ) -> AsyncIterator[int]:
        max_surge = config.get("max_surge", "25%")
        max_unavailable = config.get("max_unavailable", "25%")

        # Apply Kubernetes rolling update
        for component in bundle.manifest.components:
            # Update deployment
            await self._update_deployment(
                component,
                environment,
                max_surge=max_surge,
                max_unavailable=max_unavailable
            )

            # Wait for rollout
            async for progress in self._wait_for_rollout(component, environment):
                yield progress

class BlueGreenStrategy(DeploymentStrategy):
    """Blue-green deployment."""

    async def execute(
        self,
        bundle: Bundle,
        environment: Environment,
        config: dict
    ) -> AsyncIterator[int]:
        # Deploy to green environment
        green_env = await self._create_green_environment(environment)

        yield 10

        # Deploy all components to green
        for i, component in enumerate(bundle.manifest.components):
            await self._deploy_component(component, green_env)
            yield 10 + int(40 * (i + 1) / len(bundle.manifest.components))

        yield 50

        # Verify green environment
        healthy = await self._verify_health(green_env)
        if not healthy:
            raise DeploymentError("Green environment health check failed")

        yield 75

        # Switch traffic
        await self._switch_traffic(environment, green_env)

        yield 90

        # Cleanup blue environment
        await self._cleanup_blue(environment)

        yield 100

class CanaryStrategy(DeploymentStrategy):
    """Canary deployment with progressive traffic shifting."""

    async def execute(
        self,
        bundle: Bundle,
        environment: Environment,
        config: dict
    ) -> AsyncIterator[int]:
        steps = config.get("steps", [10, 25, 50, 75, 100])
        interval_seconds = config.get("interval_seconds", 300)
        error_threshold = config.get("error_threshold", 0.01)

        # Deploy canary
        canary = await self._deploy_canary(bundle, environment)
        yield 10

        # Progressive traffic shift
        for i, percentage in enumerate(steps):
            await self._set_traffic_weight(canary, percentage)
            yield 10 + int(80 * (i + 1) / len(steps))

            # Monitor error rate
            await asyncio.sleep(interval_seconds)
            error_rate = await self._get_error_rate(canary)

            if error_rate > error_threshold:
                await self._rollback_canary(canary)
                raise DeploymentError(f"Canary error rate {error_rate} exceeds threshold")

        # Promote canary
        await self._promote_canary(canary, environment)
        yield 100
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/orbit", tags=["orbit"])

@router.get("/products")
async def list_products(
    status: str | None = None
) -> list[Product]:
    """List products."""
    pass

@router.post("/products")
async def create_product(
    name: str,
    components: list[ProductComponent],
    description: str | None = None
) -> Product:
    """Create a product."""
    pass

@router.get("/products/{product_id}")
async def get_product(product_id: str) -> Product:
    """Get product details."""
    pass

@router.post("/products/{product_id}/versions")
async def create_version(
    product_id: str,
    version: str,
    changelog: str | None = None
) -> ProductVersion:
    """Create a new product version."""
    pass

@router.get("/products/{product_id}/versions")
async def list_versions(product_id: str) -> list[ProductVersion]:
    """List product versions."""
    pass

@router.post("/products/{product_id}/bundle")
async def create_bundle(
    product_id: str,
    version: str
) -> Bundle:
    """Create deployment bundle."""
    pass

@router.get("/environments")
async def list_environments() -> list[Environment]:
    """List environments."""
    pass

@router.post("/environments")
async def create_environment(
    name: str,
    type: str,
    cluster_id: str,
    namespace: str
) -> Environment:
    """Create an environment."""
    pass

@router.post("/deployments")
async def create_deployment(
    product_id: str,
    version: str,
    environment_id: str,
    strategy: str = "rolling"
) -> Deployment:
    """Create and start a deployment."""
    pass

@router.get("/deployments/{deployment_id}")
async def get_deployment(deployment_id: str) -> Deployment:
    """Get deployment status."""
    pass

@router.post("/deployments/{deployment_id}/rollback")
async def rollback_deployment(
    deployment_id: str,
    target_version: str | None = None
) -> Deployment:
    """Rollback a deployment."""
    pass

@router.get("/deployments/{deployment_id}/events")
async def get_deployment_events(
    deployment_id: str
) -> list[DeploymentEvent]:
    """Get deployment events."""
    pass

@router.post("/promote")
async def promote(
    product_id: str,
    from_environment: str,
    to_environment: str
) -> Deployment:
    """Promote product between environments."""
    pass
```

---

## Package 2: Forge Exchange

### Purpose

Marketplace for sharing and distributing pre-built solutions, templates, and integrations.

### Module Structure

```
packages/forge-exchange/
├── src/
│   └── forge_exchange/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── listing.py         # Marketplace listing
│       │   ├── installation.py    # Installation record
│       │   └── review.py          # User reviews
│       ├── catalog/
│       │   ├── __init__.py
│       │   ├── search.py          # Catalog search
│       │   └── categories.py      # Categories
│       ├── installation/
│       │   ├── __init__.py
│       │   ├── installer.py       # Installation engine
│       │   └── dependencies.py    # Dependency resolution
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/listing.py
class ListingType(str, Enum):
    APP = "app"
    CONNECTOR = "connector"
    PIPELINE = "pipeline"
    ONTOLOGY = "ontology"
    TEMPLATE = "template"
    INTEGRATION = "integration"

class Listing(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    long_description: str | None = None
    listing_type: ListingType

    # Publisher
    publisher_id: str
    publisher_name: str
    verified_publisher: bool = False

    # Content
    product_id: str
    current_version: str
    icon_url: str | None = None
    screenshots: list[str] = []
    documentation_url: str | None = None
    repository_url: str | None = None

    # Categorization
    categories: list[str] = []
    tags: list[str] = []

    # Pricing
    pricing_model: Literal["free", "subscription", "one_time"] = "free"
    price: float | None = None
    currency: str = "USD"

    # Stats
    install_count: int = 0
    rating_average: float | None = None
    rating_count: int = 0

    # Lifecycle
    status: Literal["draft", "pending_review", "published", "rejected", "archived"]
    published_at: datetime | None = None
    created_at: datetime
    updated_at: datetime

class ListingVersion(BaseModel):
    id: str
    listing_id: str
    version: str
    bundle_url: str
    changelog: str | None = None
    min_platform_version: str | None = None
    dependencies: list[dict] = []
    published_at: datetime
```

```python
# models/installation.py
class Installation(BaseModel):
    id: str
    listing_id: str
    version: str
    workspace_id: str
    installed_by: str
    installed_at: datetime

    # Status
    status: Literal["installing", "active", "updating", "failed", "uninstalled"]

    # Configuration
    config: dict = {}

    # Resources created
    created_resources: list[dict] = []

class InstallationUpdate(BaseModel):
    installation_id: str
    from_version: str
    to_version: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error_message: str | None = None
```

```python
# installation/installer.py
class Installer:
    """Install marketplace listings."""

    def __init__(
        self,
        bundle_store: "BundleStore",
        resource_manager: "ResourceManager"
    ):
        self.bundles = bundle_store
        self.resources = resource_manager

    async def install(
        self,
        listing: Listing,
        version: str,
        workspace_id: str,
        config: dict | None = None
    ) -> Installation:
        """Install a listing."""
        installation = Installation(
            id=str(uuid.uuid4()),
            listing_id=listing.id,
            version=version,
            workspace_id=workspace_id,
            installed_by=self._get_current_user(),
            installed_at=datetime.utcnow(),
            status="installing",
            config=config or {}
        )

        try:
            # Download bundle
            bundle = await self.bundles.download(listing.product_id, version)

            # Resolve dependencies
            dependencies = await self._resolve_dependencies(bundle)
            for dep in dependencies:
                await self._install_dependency(dep, workspace_id)

            # Install components
            created_resources = []
            for component in bundle.manifest.components:
                resources = await self._install_component(
                    component,
                    workspace_id,
                    config
                )
                created_resources.extend(resources)

            installation.created_resources = created_resources
            installation.status = "active"

        except Exception as e:
            installation.status = "failed"
            installation.config["error"] = str(e)
            # Cleanup partial installation
            await self._cleanup_installation(installation)

        return installation

    async def update(
        self,
        installation: Installation,
        to_version: str
    ) -> InstallationUpdate:
        """Update an installation to a new version."""
        update = InstallationUpdate(
            installation_id=installation.id,
            from_version=installation.version,
            to_version=to_version,
            status="in_progress",
            started_at=datetime.utcnow()
        )

        try:
            # Get listing
            listing = await self._get_listing(installation.listing_id)

            # Download new bundle
            bundle = await self.bundles.download(listing.product_id, to_version)

            # Run migrations if any
            migrations = await self._get_migrations(
                installation.version,
                to_version,
                bundle
            )
            for migration in migrations:
                await self._run_migration(migration, installation)

            # Update components
            await self._update_components(installation, bundle)

            installation.version = to_version
            installation.status = "active"
            update.status = "completed"

        except Exception as e:
            update.status = "failed"
            update.error_message = str(e)
            # Rollback
            await self._rollback_update(installation)

        finally:
            update.completed_at = datetime.utcnow()

        return update

    async def uninstall(self, installation: Installation):
        """Uninstall a listing."""
        # Check for dependents
        dependents = await self._get_dependents(installation)
        if dependents:
            raise UninstallError(f"Cannot uninstall: used by {len(dependents)} other installations")

        # Remove created resources
        for resource in installation.created_resources:
            await self.resources.delete(resource["type"], resource["id"])

        installation.status = "uninstalled"
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/exchange", tags=["exchange"])

@router.get("/listings")
async def search_listings(
    q: str | None = None,
    category: str | None = None,
    listing_type: ListingType | None = None,
    tags: list[str] | None = None,
    verified_only: bool = False,
    sort: Literal["popular", "recent", "rating"] = "popular",
    limit: int = 50,
    offset: int = 0
) -> list[Listing]:
    """Search marketplace listings."""
    pass

@router.get("/listings/{listing_id}")
async def get_listing(listing_id: str) -> Listing:
    """Get listing details."""
    pass

@router.get("/listings/{listing_id}/versions")
async def list_listing_versions(listing_id: str) -> list[ListingVersion]:
    """List available versions."""
    pass

@router.get("/listings/{listing_id}/reviews")
async def get_reviews(
    listing_id: str,
    limit: int = 20
) -> list[Review]:
    """Get listing reviews."""
    pass

@router.post("/listings/{listing_id}/reviews")
async def create_review(
    listing_id: str,
    rating: int,
    comment: str | None = None
) -> Review:
    """Create a review."""
    pass

@router.post("/listings/{listing_id}/install")
async def install_listing(
    listing_id: str,
    version: str | None = None,
    workspace_id: str | None = None,
    config: dict | None = None
) -> Installation:
    """Install a listing."""
    pass

@router.get("/installations")
async def list_installations(
    workspace_id: str | None = None
) -> list[Installation]:
    """List installations."""
    pass

@router.post("/installations/{installation_id}/update")
async def update_installation(
    installation_id: str,
    to_version: str
) -> InstallationUpdate:
    """Update an installation."""
    pass

@router.delete("/installations/{installation_id}")
async def uninstall(installation_id: str) -> dict:
    """Uninstall a listing."""
    pass

@router.get("/categories")
async def list_categories() -> list[dict]:
    """List marketplace categories."""
    pass

# Publisher endpoints
@router.post("/publish")
async def publish_listing(
    product_id: str,
    name: str,
    description: str,
    listing_type: ListingType,
    categories: list[str]
) -> Listing:
    """Publish a product to the marketplace."""
    pass

@router.post("/listings/{listing_id}/versions")
async def publish_version(
    listing_id: str,
    version: str,
    changelog: str | None = None
) -> ListingVersion:
    """Publish a new version."""
    pass
```

---

## Package 3: Forge Edge

### Purpose

Edge deployment for disconnected/offline scenarios with sync and conflict resolution.

### Module Structure

```
packages/forge-edge/
├── src/
│   └── forge_edge/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── device.py          # Edge device
│       │   ├── sync.py            # Sync state
│       │   └── conflict.py        # Conflicts
│       ├── runtime/
│       │   ├── __init__.py
│       │   ├── engine.py          # Edge runtime
│       │   └── cache.py           # Local cache
│       ├── sync/
│       │   ├── __init__.py
│       │   ├── manager.py         # Sync manager
│       │   ├── resolver.py        # Conflict resolver
│       │   └── queue.py           # Offline queue
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/device.py
class EdgeDevice(BaseModel):
    id: str
    name: str
    device_type: str  # "laptop", "tablet", "industrial", "vehicle"
    owner_id: str

    # Status
    status: Literal["online", "offline", "syncing", "error"]
    last_seen: datetime | None = None
    last_sync: datetime | None = None

    # Configuration
    sync_config: "SyncConfig"
    installed_products: list[str] = []

    # Location
    location: dict | None = None
    region: str | None = None

    created_at: datetime
    updated_at: datetime

class SyncConfig(BaseModel):
    sync_interval_minutes: int = 60
    auto_sync: bool = True
    sync_on_connect: bool = True
    max_offline_days: int = 30
    data_filters: dict = {}  # What data to sync
    priority_datasets: list[str] = []
```

```python
# sync/manager.py
class SyncManager:
    """Manage data synchronization between edge and cloud."""

    def __init__(
        self,
        local_store: "LocalStore",
        cloud_client: "CloudClient",
        conflict_resolver: "ConflictResolver"
    ):
        self.local = local_store
        self.cloud = cloud_client
        self.resolver = conflict_resolver

    async def sync(
        self,
        device: EdgeDevice,
        direction: Literal["push", "pull", "both"] = "both"
    ) -> "SyncResult":
        """Synchronize data with cloud."""
        result = SyncResult(
            device_id=device.id,
            started_at=datetime.utcnow()
        )

        try:
            if direction in ["pull", "both"]:
                # Pull changes from cloud
                pull_result = await self._pull_changes(device)
                result.pulled_records = pull_result.count
                result.conflicts.extend(pull_result.conflicts)

            if direction in ["push", "both"]:
                # Push local changes
                push_result = await self._push_changes(device)
                result.pushed_records = push_result.count
                result.conflicts.extend(push_result.conflicts)

            # Resolve conflicts
            for conflict in result.conflicts:
                resolution = await self.resolver.resolve(conflict, device.sync_config)
                result.resolved_conflicts.append(resolution)

            result.status = "completed"

        except Exception as e:
            result.status = "failed"
            result.error_message = str(e)

        finally:
            result.completed_at = datetime.utcnow()

        return result

    async def _pull_changes(self, device: EdgeDevice) -> "ChangeSet":
        """Pull changes from cloud since last sync."""
        last_sync = device.last_sync or datetime.min

        # Get cloud changes
        cloud_changes = await self.cloud.get_changes_since(
            last_sync,
            filters=device.sync_config.data_filters
        )

        # Apply changes locally
        conflicts = []
        count = 0

        for change in cloud_changes:
            local_version = await self.local.get_version(change.record_id)

            if local_version and local_version.modified_at > last_sync:
                # Conflict: both sides changed
                conflicts.append(SyncConflict(
                    record_id=change.record_id,
                    local_version=local_version,
                    cloud_version=change,
                    conflict_type="concurrent_modification"
                ))
            else:
                # Safe to apply
                await self.local.apply_change(change)
                count += 1

        return ChangeSet(count=count, conflicts=conflicts)

    async def _push_changes(self, device: EdgeDevice) -> "ChangeSet":
        """Push local changes to cloud."""
        last_sync = device.last_sync or datetime.min

        # Get local changes
        local_changes = await self.local.get_changes_since(last_sync)

        conflicts = []
        count = 0

        for change in local_changes:
            try:
                await self.cloud.apply_change(change, device.id)
                await self.local.mark_synced(change.record_id)
                count += 1
            except ConflictError as e:
                conflicts.append(SyncConflict(
                    record_id=change.record_id,
                    local_version=change,
                    cloud_version=e.cloud_version,
                    conflict_type="server_conflict"
                ))

        return ChangeSet(count=count, conflicts=conflicts)
```

```python
# sync/resolver.py
class ConflictResolver:
    """Resolve sync conflicts."""

    async def resolve(
        self,
        conflict: "SyncConflict",
        config: SyncConfig
    ) -> "ConflictResolution":
        """Resolve a sync conflict."""
        strategy = config.conflict_strategy or "server_wins"

        if strategy == "server_wins":
            return await self._resolve_server_wins(conflict)
        elif strategy == "client_wins":
            return await self._resolve_client_wins(conflict)
        elif strategy == "latest_wins":
            return await self._resolve_latest_wins(conflict)
        elif strategy == "merge":
            return await self._resolve_merge(conflict)
        elif strategy == "manual":
            return await self._flag_for_manual(conflict)

        raise ValueError(f"Unknown conflict strategy: {strategy}")

    async def _resolve_latest_wins(
        self,
        conflict: "SyncConflict"
    ) -> "ConflictResolution":
        """Take the most recently modified version."""
        if conflict.local_version.modified_at > conflict.cloud_version.modified_at:
            winner = "local"
            winning_version = conflict.local_version
        else:
            winner = "cloud"
            winning_version = conflict.cloud_version

        return ConflictResolution(
            conflict_id=conflict.id,
            strategy="latest_wins",
            winner=winner,
            resolved_version=winning_version,
            resolved_at=datetime.utcnow()
        )

    async def _resolve_merge(
        self,
        conflict: "SyncConflict"
    ) -> "ConflictResolution":
        """Attempt to merge non-conflicting fields."""
        local = conflict.local_version.data
        cloud = conflict.cloud_version.data
        base = conflict.base_version.data if conflict.base_version else {}

        merged = {}
        field_conflicts = []

        all_fields = set(local.keys()) | set(cloud.keys())

        for field in all_fields:
            local_val = local.get(field)
            cloud_val = cloud.get(field)
            base_val = base.get(field)

            if local_val == cloud_val:
                merged[field] = local_val
            elif local_val == base_val:
                merged[field] = cloud_val
            elif cloud_val == base_val:
                merged[field] = local_val
            else:
                # True conflict
                field_conflicts.append(field)
                # Default to cloud for unresolvable
                merged[field] = cloud_val

        return ConflictResolution(
            conflict_id=conflict.id,
            strategy="merge",
            winner="merged",
            resolved_version=MergedVersion(data=merged),
            field_conflicts=field_conflicts,
            resolved_at=datetime.utcnow()
        )
```

---

## Package 4: Forge Consumer

### Purpose

Host public-facing applications with custom domains, embedding, and analytics.

### Module Structure

```
packages/forge-consumer/
├── src/
│   └── forge_consumer/
│       ├── __init__.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── app.py             # Consumer app
│       │   ├── domain.py          # Custom domains
│       │   └── embed.py           # Embed configuration
│       ├── hosting/
│       │   ├── __init__.py
│       │   ├── server.py          # App server
│       │   └── cdn.py             # CDN integration
│       ├── auth/
│       │   ├── __init__.py
│       │   ├── public.py          # Public access
│       │   └── portal.py          # User portal
│       ├── analytics/
│       │   ├── __init__.py
│       │   └── tracker.py         # Usage analytics
│       └── api/
│           ├── __init__.py
│           └── routes.py
├── tests/
└── pyproject.toml
```

### Core Classes

```python
# models/app.py
class ConsumerApp(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None = None

    # Source
    source_app_id: str
    source_version: str

    # Access
    access_type: Literal["public", "authenticated", "invite_only"]
    allowed_domains: list[str] | None = None

    # Branding
    logo_url: str | None = None
    favicon_url: str | None = None
    primary_color: str | None = None
    custom_css: str | None = None

    # Domains
    default_domain: str  # myapp.forgeapps.io
    custom_domains: list["CustomDomain"] = []

    # Analytics
    analytics_enabled: bool = True
    google_analytics_id: str | None = None

    # Status
    status: Literal["draft", "published", "maintenance", "disabled"]
    published_at: datetime | None = None

    created_at: datetime
    updated_at: datetime

class CustomDomain(BaseModel):
    domain: str
    verified: bool = False
    ssl_status: Literal["pending", "active", "error"]
    verification_token: str | None = None
    verified_at: datetime | None = None
```

```python
# models/embed.py
class EmbedConfig(BaseModel):
    id: str
    app_id: str
    name: str

    # Allowed origins
    allowed_origins: list[str]

    # Embedded components
    components: list[str]  # Which components can be embedded

    # Sizing
    default_width: str = "100%"
    default_height: str = "600px"
    responsive: bool = True

    # Authentication
    require_auth: bool = False
    auth_mode: Literal["redirect", "popup", "inline"] = "popup"

    # Customization
    hide_header: bool = False
    hide_footer: bool = False
    theme: str = "light"

    created_at: datetime

class EmbedToken(BaseModel):
    token: str
    embed_config_id: str
    expires_at: datetime
    user_context: dict | None = None
```

```python
# hosting/server.py
class ConsumerAppServer:
    """Serve consumer applications."""

    def __init__(
        self,
        app_store: "AppStore",
        asset_cdn: "CDN",
        analytics: "AnalyticsTracker"
    ):
        self.apps = app_store
        self.cdn = asset_cdn
        self.analytics = analytics

    async def serve_app(
        self,
        domain: str,
        path: str,
        request: Request
    ) -> Response:
        """Serve a consumer app request."""
        # Resolve app from domain
        app = await self._resolve_app(domain)
        if not app:
            raise HTTPException(404, "App not found")

        # Check access
        if not await self._check_access(app, request):
            return await self._redirect_to_auth(app, request)

        # Track pageview
        await self.analytics.track_pageview(app.id, path, request)

        # Serve content
        if self._is_api_request(path):
            return await self._proxy_api(app, path, request)
        else:
            return await self._serve_static(app, path)

    async def _serve_static(
        self,
        app: ConsumerApp,
        path: str
    ) -> Response:
        """Serve static assets."""
        # Try to serve from CDN
        cdn_url = await self.cdn.get_url(app.id, path)
        if cdn_url:
            return RedirectResponse(cdn_url)

        # Fall back to origin
        return await self._serve_from_origin(app, path)

    async def _proxy_api(
        self,
        app: ConsumerApp,
        path: str,
        request: Request
    ) -> Response:
        """Proxy API requests to backend."""
        # Rewrite path
        backend_path = path.replace("/api/", f"/api/v1/consumer/{app.id}/")

        # Forward request
        async with httpx.AsyncClient() as client:
            response = await client.request(
                method=request.method,
                url=f"{self.backend_url}{backend_path}",
                headers=dict(request.headers),
                content=await request.body()
            )

        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers)
        )
```

### API Routes

```python
# api/routes.py
router = APIRouter(prefix="/api/v1/consumer", tags=["consumer"])

@router.get("/apps")
async def list_consumer_apps(
    status: str | None = None
) -> list[ConsumerApp]:
    """List consumer apps."""
    pass

@router.post("/apps")
async def create_consumer_app(
    name: str,
    source_app_id: str,
    access_type: str = "authenticated"
) -> ConsumerApp:
    """Create a consumer app."""
    pass

@router.get("/apps/{app_id}")
async def get_consumer_app(app_id: str) -> ConsumerApp:
    """Get consumer app details."""
    pass

@router.patch("/apps/{app_id}")
async def update_consumer_app(
    app_id: str,
    updates: dict
) -> ConsumerApp:
    """Update consumer app."""
    pass

@router.post("/apps/{app_id}/publish")
async def publish_app(app_id: str) -> ConsumerApp:
    """Publish consumer app."""
    pass

@router.post("/apps/{app_id}/domains")
async def add_custom_domain(
    app_id: str,
    domain: str
) -> CustomDomain:
    """Add custom domain."""
    pass

@router.post("/apps/{app_id}/domains/{domain}/verify")
async def verify_domain(
    app_id: str,
    domain: str
) -> CustomDomain:
    """Verify domain ownership."""
    pass

@router.get("/apps/{app_id}/analytics")
async def get_app_analytics(
    app_id: str,
    start_date: datetime,
    end_date: datetime
) -> dict:
    """Get app analytics."""
    pass

@router.post("/embed")
async def create_embed_config(
    app_id: str,
    name: str,
    allowed_origins: list[str],
    components: list[str]
) -> EmbedConfig:
    """Create embed configuration."""
    pass

@router.post("/embed/{embed_id}/token")
async def generate_embed_token(
    embed_id: str,
    expires_in_minutes: int = 60
) -> EmbedToken:
    """Generate embed token."""
    pass
```

---

## Implementation Roadmap

### Phase H1: Orbit + Exchange (Weeks 1-4)

**Deliverables:**
1. forge-orbit with product/bundle management
2. Deployment engine with strategies
3. forge-exchange with catalog and installation
4. Deployment UI

### Phase H2: Edge + Consumer (Weeks 5-7)

**Deliverables:**
1. forge-edge with sync manager
2. forge-consumer with app hosting
3. Conflict resolution
4. Custom domain support

---

## Infrastructure Components

### Kubernetes Operator

```yaml
# forge-operator CRD
apiVersion: forge.dev/v1
kind: ForgeProduct
metadata:
  name: my-product
spec:
  version: 1.0.0
  components:
    - name: api
      type: deployment
      replicas: 3
      image: forge/api:1.0.0
    - name: worker
      type: deployment
      replicas: 2
      image: forge/worker:1.0.0
  environments:
    - name: production
      namespace: prod
      config:
        replicas:
          api: 5
          worker: 4
```

### Helm Chart Values

```yaml
# values.yaml
forge:
  orbit:
    enabled: true
    strategies:
      - rolling
      - blue_green
      - canary
    gitops:
      enabled: true
      argocd:
        server: https://argocd.example.com

  exchange:
    enabled: true
    storage:
      type: s3
      bucket: forge-exchange

  edge:
    enabled: true
    sync:
      interval: 60
      conflictStrategy: latest_wins

  consumer:
    enabled: true
    cdn:
      provider: cloudflare
    domains:
      base: forgeapps.io
```

---

## Security Considerations

1. **Bundle Signing**: All bundles cryptographically signed
2. **RBAC**: Deployment permissions per environment
3. **Secret Management**: Secrets never in bundles, injected at runtime
4. **Audit Trail**: All deployments logged
5. **Network Policies**: Environment isolation in Kubernetes
6. **Edge Security**: Device attestation, encrypted sync
