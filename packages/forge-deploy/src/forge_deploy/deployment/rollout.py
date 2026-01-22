"""
Rollout manager for deployment orchestration.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from forge_deploy.deployment.models import (
    Deployment,
    DeploymentError,
    DeploymentEvent,
    DeploymentStatus,
    DeploymentStrategyType,
)
from forge_deploy.deployment.strategies import (
    BaseDeploymentStrategy,
    DeploymentStrategy,
    get_strategy,
)

if TYPE_CHECKING:
    from forge_deploy.environments.models import Environment
    from forge_deploy.products.bundle import Bundle


class HealthChecker(Protocol):
    """Protocol for deployment health checking."""

    async def check(
        self,
        deployment: Deployment,
        environment: "Environment",
    ) -> bool:
        """
        Check if deployment is healthy.

        Returns:
            True if all health checks pass
        """
        ...


class EventEmitter(Protocol):
    """Protocol for emitting deployment events."""

    async def emit(self, event: DeploymentEvent) -> None:
        """Emit a deployment event."""
        ...


class RolloutManager:
    """
    Orchestrates deployment rollouts.

    Coordinates the deployment process including strategy execution,
    health checking, event emission, and error handling.
    """

    def __init__(
        self,
        health_checker: HealthChecker | None = None,
        event_emitter: EventEmitter | None = None,
    ) -> None:
        """
        Initialize the rollout manager.

        Args:
            health_checker: Optional health check implementation
            event_emitter: Optional event emission implementation
        """
        self._health_checker = health_checker
        self._event_emitter = event_emitter

    async def deploy(
        self,
        deployment: Deployment,
        bundle: "Bundle",
        environment: "Environment",
    ) -> Deployment:
        """
        Execute a deployment.

        Args:
            deployment: Deployment record to execute
            bundle: Bundle to deploy
            environment: Target environment

        Returns:
            Updated deployment record with results

        Raises:
            DeploymentError: If deployment fails and auto-rollback is disabled
        """
        deployment.status = DeploymentStatus.IN_PROGRESS
        deployment.started_at = datetime.utcnow()

        await self._emit_event(
            deployment,
            "started",
            f"Starting deployment of {bundle.product_id} v{bundle.version}",
        )

        try:
            # Get the appropriate strategy
            strategy = get_strategy(
                DeploymentStrategy(deployment.strategy)
            )

            # Execute deployment with progress tracking
            async for progress in strategy.execute(
                bundle=bundle,
                environment=environment,
                config=deployment.strategy_config,
            ):
                deployment.progress = progress
                await self._emit_event(
                    deployment,
                    "progress",
                    f"Deployment progress: {progress}%",
                    {"progress": progress},
                )

            # Verify health if checker is configured
            if self._health_checker:
                healthy = await self._health_checker.check(deployment, environment)
                if not healthy:
                    raise DeploymentError(
                        "Health check failed after deployment",
                        deployment.id,
                    )

            deployment.status = DeploymentStatus.SUCCEEDED
            deployment.deployed_components = [
                c["name"] for c in bundle.manifest.components
            ]

            await self._emit_event(
                deployment,
                "succeeded",
                "Deployment completed successfully",
            )

        except Exception as e:
            deployment.status = DeploymentStatus.FAILED
            deployment.error_message = str(e)

            await self._emit_event(
                deployment,
                "failed",
                f"Deployment failed: {e}",
                {"error": str(e)},
            )

            # Auto-rollback if configured
            if deployment.strategy_config.get("auto_rollback", True):
                await self._emit_event(
                    deployment,
                    "rollback_started",
                    "Initiating automatic rollback",
                )
                # Rollback handled by RollbackManager

        finally:
            deployment.completed_at = datetime.utcnow()
            if deployment.started_at:
                deployment.duration_seconds = int(
                    (deployment.completed_at - deployment.started_at).total_seconds()
                )

        return deployment

    async def _emit_event(
        self,
        deployment: Deployment,
        event_type: str,
        message: str,
        metadata: dict | None = None,
    ) -> None:
        """Emit a deployment event if emitter is configured."""
        if not self._event_emitter:
            return

        event = DeploymentEvent(
            id=str(uuid4()),
            deployment_id=deployment.id,
            event_type=event_type,
            message=message,
            metadata=metadata or {},
        )

        await self._event_emitter.emit(event)

    async def cancel(self, deployment: Deployment) -> Deployment:
        """
        Cancel an in-progress deployment.

        Args:
            deployment: Deployment to cancel

        Returns:
            Updated deployment with cancelled status

        Raises:
            DeploymentError: If deployment cannot be cancelled
        """
        if deployment.status not in (
            DeploymentStatus.PENDING,
            DeploymentStatus.IN_PROGRESS,
        ):
            raise DeploymentError(
                f"Cannot cancel deployment in {deployment.status} state",
                deployment.id,
            )

        deployment.status = DeploymentStatus.CANCELLED
        deployment.completed_at = datetime.utcnow()

        await self._emit_event(
            deployment,
            "cancelled",
            "Deployment was cancelled",
        )

        return deployment
