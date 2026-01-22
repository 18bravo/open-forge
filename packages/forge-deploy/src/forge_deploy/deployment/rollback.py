"""
Rollback manager for deployment recovery.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from forge_deploy.deployment.models import (
    Deployment,
    DeploymentStatus,
    RollbackError,
)

if TYPE_CHECKING:
    from forge_deploy.environments.models import Environment
    from forge_deploy.products.bundle import Bundle


class DeploymentRepository(Protocol):
    """Protocol for accessing deployment history."""

    async def get_previous_successful(
        self,
        product_id: str,
        environment_id: str,
        before_deployment_id: str | None = None,
    ) -> Deployment | None:
        """Get the most recent successful deployment."""
        ...

    async def get_by_version(
        self,
        product_id: str,
        environment_id: str,
        version: str,
    ) -> Deployment | None:
        """Get a deployment by version."""
        ...


class BundleRepository(Protocol):
    """Protocol for accessing bundles."""

    async def get(self, product_id: str, version: str) -> "Bundle | None":
        """Get a bundle by product and version."""
        ...


class RollbackManager:
    """
    Manages deployment rollbacks.

    Handles finding previous successful deployments and coordinating
    the rollback process.
    """

    def __init__(
        self,
        deployment_repo: DeploymentRepository | None = None,
        bundle_repo: BundleRepository | None = None,
    ) -> None:
        """
        Initialize the rollback manager.

        Args:
            deployment_repo: Repository for deployment history
            bundle_repo: Repository for bundles
        """
        self._deployments = deployment_repo
        self._bundles = bundle_repo

    async def rollback(
        self,
        deployment: Deployment,
        environment: "Environment",
        target_version: str | None = None,
        initiated_by: str = "system",
    ) -> Deployment:
        """
        Rollback a deployment.

        Args:
            deployment: Failed deployment to rollback
            environment: Environment to rollback in
            target_version: Specific version to rollback to (optional)
            initiated_by: User or system initiating rollback

        Returns:
            New deployment record for the rollback

        Raises:
            RollbackError: If no previous deployment found or rollback fails
        """
        if not self._deployments or not self._bundles:
            raise RollbackError(
                "Rollback manager not configured with repositories",
                deployment.id,
            )

        # Find target deployment
        if target_version:
            previous = await self._deployments.get_by_version(
                deployment.product_id,
                environment.id,
                target_version,
            )
        else:
            previous = await self._deployments.get_previous_successful(
                deployment.product_id,
                environment.id,
                deployment.id,
            )

        if not previous:
            raise RollbackError(
                "No previous deployment to rollback to",
                deployment.id,
            )

        # Get bundle for previous version
        bundle = await self._bundles.get(previous.product_id, previous.version)
        if not bundle:
            raise RollbackError(
                f"Bundle not found for version {previous.version}",
                deployment.id,
            )

        # Create rollback deployment record
        rollback_deployment = Deployment(
            id=str(uuid4()),
            product_id=deployment.product_id,
            version=previous.version,
            environment_id=environment.id,
            strategy=deployment.strategy,
            strategy_config={
                **deployment.strategy_config,
                "is_rollback": True,
                "rollback_from": deployment.version,
            },
            initiated_by=initiated_by,
        )

        # Mark original as rolled back
        deployment.status = DeploymentStatus.ROLLED_BACK

        return rollback_deployment

    async def find_rollback_target(
        self,
        product_id: str,
        environment_id: str,
        current_deployment_id: str | None = None,
        versions_back: int = 1,
    ) -> Deployment | None:
        """
        Find a suitable rollback target.

        Args:
            product_id: Product to find rollback for
            environment_id: Environment to search in
            current_deployment_id: Current deployment to skip
            versions_back: How many successful versions to go back

        Returns:
            Previous successful deployment or None
        """
        if not self._deployments:
            return None

        # For now, just return the most recent successful
        # Could be extended to skip N versions
        return await self._deployments.get_previous_successful(
            product_id,
            environment_id,
            current_deployment_id,
        )
