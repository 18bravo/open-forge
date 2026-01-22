"""
Open Forge Deploy - Deployment Platform (Orbit CD)

This package provides deployment capabilities for the Open Forge platform:

- **products**: Product definitions, component bundling, and version management
- **deployment**: GitOps sync, gradual rollout strategies, rollback automation
- **environments**: Environment definitions and promotion workflows

Note: Edge deployment and marketplace functionality are deferred per the
consolidated architecture (see docs/plans/2026-01-21-consolidated-architecture.md).

Example usage:
    from forge_deploy import (
        Product,
        ProductVersion,
        Deployment,
        DeploymentStrategy,
        Environment,
        RolloutManager,
    )

    # Define a product
    product = Product(
        id="my-app",
        name="My Application",
        owner_id="user-123",
        components=[
            ProductComponent(name="api", type="app", source="my-api:1.0.0"),
        ],
    )

    # Create a deployment
    deployment = Deployment(
        id="deploy-1",
        product_id=product.id,
        version="1.0.0",
        environment_id="production",
        strategy=DeploymentStrategy.ROLLING,
        initiated_by="user-123",
    )

    # Execute with rollout manager
    manager = RolloutManager()
    result = await manager.deploy(deployment, bundle, environment)
"""

# Products
from forge_deploy.products.models import (
    Product,
    ProductComponent,
    ProductStatus,
    ProductVersion,
    ComponentType,
)
from forge_deploy.products.bundle import (
    Bundle,
    BundleManifest,
    Bundler,
    BundleError,
)

# Deployment
from forge_deploy.deployment.models import (
    Deployment,
    DeploymentEvent,
    DeploymentStatus,
    DeploymentStrategyType,
    DeploymentError,
    RollbackError,
)
from forge_deploy.deployment.strategies import (
    DeploymentStrategy,
    BaseDeploymentStrategy,
    RollingStrategy,
    BlueGreenStrategy,
    CanaryStrategy,
    RecreateStrategy,
    get_strategy,
)
from forge_deploy.deployment.rollout import RolloutManager
from forge_deploy.deployment.rollback import RollbackManager
from forge_deploy.deployment.gitops import GitOpsSync, SyncStatus, SyncResult

# Environments
from forge_deploy.environments.models import (
    Environment,
    EnvironmentType,
    EnvironmentVariable,
)
from forge_deploy.environments.promotion import (
    PromotionWorkflow,
    PromotionRule,
    PromotionRuleType,
    PromotionResult,
    PromotionStatus,
    PromotionError,
)

# API
from forge_deploy.api import router

__version__ = "0.1.0"

__all__ = [
    # Products
    "Product",
    "ProductVersion",
    "ProductComponent",
    "ProductStatus",
    "ComponentType",
    "Bundle",
    "BundleManifest",
    "Bundler",
    "BundleError",
    # Deployment
    "Deployment",
    "DeploymentEvent",
    "DeploymentStatus",
    "DeploymentStrategyType",
    "DeploymentStrategy",
    "BaseDeploymentStrategy",
    "RollingStrategy",
    "BlueGreenStrategy",
    "CanaryStrategy",
    "RecreateStrategy",
    "get_strategy",
    "DeploymentError",
    "RollbackError",
    "RolloutManager",
    "RollbackManager",
    "GitOpsSync",
    "SyncStatus",
    "SyncResult",
    # Environments
    "Environment",
    "EnvironmentType",
    "EnvironmentVariable",
    "PromotionWorkflow",
    "PromotionRule",
    "PromotionRuleType",
    "PromotionResult",
    "PromotionStatus",
    "PromotionError",
    # API
    "router",
]
