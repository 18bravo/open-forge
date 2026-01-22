"""
Deployment module for Forge Deploy.

Provides deployment orchestration, rollout strategies, GitOps sync,
and rollback automation for Orbit CD.
"""

from forge_deploy.deployment.models import (
    Deployment,
    DeploymentEvent,
    DeploymentStatus,
)
from forge_deploy.deployment.strategies import (
    BlueGreenStrategy,
    CanaryStrategy,
    DeploymentStrategy,
    RecreateStrategy,
    RollingStrategy,
)
from forge_deploy.deployment.rollout import RolloutManager
from forge_deploy.deployment.rollback import RollbackManager
from forge_deploy.deployment.gitops import GitOpsSync

__all__ = [
    # Models
    "Deployment",
    "DeploymentEvent",
    "DeploymentStatus",
    # Strategies
    "DeploymentStrategy",
    "RollingStrategy",
    "BlueGreenStrategy",
    "CanaryStrategy",
    "RecreateStrategy",
    # Managers
    "RolloutManager",
    "RollbackManager",
    "GitOpsSync",
]
