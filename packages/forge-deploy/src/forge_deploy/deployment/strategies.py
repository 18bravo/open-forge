"""
Deployment strategy implementations.

Provides different deployment strategies for various reliability
and availability requirements.
"""

from abc import ABC, abstractmethod
from enum import Enum
from typing import TYPE_CHECKING, AsyncIterator

if TYPE_CHECKING:
    from forge_deploy.environments.models import Environment
    from forge_deploy.products.bundle import Bundle


class DeploymentStrategy(str, Enum):
    """
    Available deployment strategies.

    - ROLLING: Gradual replacement of old pods with new ones
    - BLUE_GREEN: Deploy new version in parallel, then switch traffic
    - CANARY: Gradual traffic shift with monitoring
    - RECREATE: Stop all old, start all new (downtime)
    """

    ROLLING = "rolling"
    BLUE_GREEN = "blue_green"
    CANARY = "canary"
    RECREATE = "recreate"


class BaseDeploymentStrategy(ABC):
    """
    Abstract base class for deployment strategies.

    Strategies implement the actual deployment logic for different
    approaches to zero-downtime or controlled deployments.
    """

    @abstractmethod
    async def execute(
        self,
        bundle: "Bundle",
        environment: "Environment",
        config: dict,
    ) -> AsyncIterator[int]:
        """
        Execute the deployment strategy.

        Args:
            bundle: Bundle to deploy
            environment: Target environment
            config: Strategy-specific configuration

        Yields:
            Progress percentage (0-100)

        Raises:
            DeploymentError: If deployment fails
        """
        ...

    @abstractmethod
    async def rollback(
        self,
        bundle: "Bundle",
        environment: "Environment",
    ) -> None:
        """
        Rollback a failed deployment.

        Args:
            bundle: Bundle that failed to deploy
            environment: Environment to rollback

        Raises:
            RollbackError: If rollback fails
        """
        ...


class RollingStrategy(BaseDeploymentStrategy):
    """
    Rolling update deployment strategy.

    Gradually replaces old pods with new ones, maintaining availability
    throughout the deployment process.

    Configuration options:
        max_surge: Maximum pods above desired (default: 25%)
        max_unavailable: Maximum unavailable pods (default: 25%)
    """

    async def execute(
        self,
        bundle: "Bundle",
        environment: "Environment",
        config: dict,
    ) -> AsyncIterator[int]:
        """Execute rolling update deployment."""
        # Scaffold - implementation deferred
        raise NotImplementedError("Rolling strategy not yet implemented")
        yield 0  # Make this a generator

    async def rollback(
        self,
        bundle: "Bundle",
        environment: "Environment",
    ) -> None:
        """Rollback rolling update."""
        raise NotImplementedError("Rolling rollback not yet implemented")


class BlueGreenStrategy(BaseDeploymentStrategy):
    """
    Blue-green deployment strategy.

    Deploys new version to a parallel "green" environment, verifies health,
    then switches traffic from "blue" to "green".

    Configuration options:
        switch_delay_seconds: Delay before traffic switch (default: 0)
        cleanup_blue: Whether to cleanup old environment (default: True)
    """

    async def execute(
        self,
        bundle: "Bundle",
        environment: "Environment",
        config: dict,
    ) -> AsyncIterator[int]:
        """Execute blue-green deployment."""
        # Scaffold - implementation deferred
        raise NotImplementedError("Blue-green strategy not yet implemented")
        yield 0

    async def rollback(
        self,
        bundle: "Bundle",
        environment: "Environment",
    ) -> None:
        """Rollback blue-green deployment by switching back to blue."""
        raise NotImplementedError("Blue-green rollback not yet implemented")


class CanaryStrategy(BaseDeploymentStrategy):
    """
    Canary deployment strategy.

    Gradually shifts traffic to the new version while monitoring
    error rates. Automatically rolls back if errors exceed threshold.

    Configuration options:
        steps: Traffic percentage steps (default: [10, 25, 50, 75, 100])
        interval_seconds: Time between steps (default: 300)
        error_threshold: Max error rate before rollback (default: 0.01)
    """

    async def execute(
        self,
        bundle: "Bundle",
        environment: "Environment",
        config: dict,
    ) -> AsyncIterator[int]:
        """Execute canary deployment."""
        # Scaffold - implementation deferred
        raise NotImplementedError("Canary strategy not yet implemented")
        yield 0

    async def rollback(
        self,
        bundle: "Bundle",
        environment: "Environment",
    ) -> None:
        """Rollback canary deployment by shifting all traffic back."""
        raise NotImplementedError("Canary rollback not yet implemented")


class RecreateStrategy(BaseDeploymentStrategy):
    """
    Recreate deployment strategy.

    Stops all existing pods, then starts new pods. Results in downtime
    but ensures clean state. Useful for development environments.

    Configuration options:
        graceful_shutdown_seconds: Time for graceful shutdown (default: 30)
    """

    async def execute(
        self,
        bundle: "Bundle",
        environment: "Environment",
        config: dict,
    ) -> AsyncIterator[int]:
        """Execute recreate deployment."""
        # Scaffold - implementation deferred
        raise NotImplementedError("Recreate strategy not yet implemented")
        yield 0

    async def rollback(
        self,
        bundle: "Bundle",
        environment: "Environment",
    ) -> None:
        """Rollback recreate deployment."""
        raise NotImplementedError("Recreate rollback not yet implemented")


def get_strategy(strategy_type: DeploymentStrategy) -> BaseDeploymentStrategy:
    """
    Factory function to get a deployment strategy instance.

    Args:
        strategy_type: Type of strategy to create

    Returns:
        Strategy instance

    Raises:
        ValueError: If strategy type is unknown
    """
    strategies = {
        DeploymentStrategy.ROLLING: RollingStrategy,
        DeploymentStrategy.BLUE_GREEN: BlueGreenStrategy,
        DeploymentStrategy.CANARY: CanaryStrategy,
        DeploymentStrategy.RECREATE: RecreateStrategy,
    }

    strategy_cls = strategies.get(strategy_type)
    if not strategy_cls:
        raise ValueError(f"Unknown strategy type: {strategy_type}")

    return strategy_cls()
