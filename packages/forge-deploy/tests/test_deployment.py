"""
Tests for deployment module.
"""

import pytest
from datetime import datetime

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
    RollingStrategy,
    BlueGreenStrategy,
    CanaryStrategy,
    RecreateStrategy,
    get_strategy,
)


class TestDeploymentModels:
    """Tests for Deployment models."""

    def test_deployment_creation(self) -> None:
        """Test creating a basic deployment."""
        deployment = Deployment(
            id="deploy-1",
            product_id="test-product-1",
            version="1.0.0",
            environment_id="prod",
            initiated_by="user-123",
        )

        assert deployment.id == "deploy-1"
        assert deployment.status == DeploymentStatus.PENDING
        assert deployment.progress == 0
        assert deployment.strategy == DeploymentStrategyType.ROLLING

    def test_deployment_with_custom_strategy(self) -> None:
        """Test deployment with custom strategy config."""
        deployment = Deployment(
            id="deploy-2",
            product_id="test-product-1",
            version="2.0.0",
            environment_id="staging",
            strategy=DeploymentStrategyType.CANARY,
            strategy_config={
                "steps": [10, 25, 50, 100],
                "interval_seconds": 600,
            },
            initiated_by="user-123",
        )

        assert deployment.strategy == "canary"
        assert deployment.strategy_config["steps"] == [10, 25, 50, 100]

    def test_deployment_event_creation(self) -> None:
        """Test creating a deployment event."""
        event = DeploymentEvent(
            id="event-1",
            deployment_id="deploy-1",
            event_type="progress",
            message="Deployment is 50% complete",
            metadata={"progress": 50},
        )

        assert event.event_type == "progress"
        assert event.metadata["progress"] == 50

    def test_deployment_status_values(self) -> None:
        """Test deployment status enum values."""
        assert DeploymentStatus.PENDING.value == "pending"
        assert DeploymentStatus.IN_PROGRESS.value == "in_progress"
        assert DeploymentStatus.SUCCEEDED.value == "succeeded"
        assert DeploymentStatus.FAILED.value == "failed"
        assert DeploymentStatus.ROLLED_BACK.value == "rolled_back"
        assert DeploymentStatus.CANCELLED.value == "cancelled"


class TestDeploymentStrategies:
    """Tests for deployment strategies."""

    def test_deployment_strategy_enum(self) -> None:
        """Test deployment strategy enum values."""
        assert DeploymentStrategy.ROLLING.value == "rolling"
        assert DeploymentStrategy.BLUE_GREEN.value == "blue_green"
        assert DeploymentStrategy.CANARY.value == "canary"
        assert DeploymentStrategy.RECREATE.value == "recreate"

    def test_get_strategy_rolling(self) -> None:
        """Test getting rolling strategy."""
        strategy = get_strategy(DeploymentStrategy.ROLLING)
        assert isinstance(strategy, RollingStrategy)

    def test_get_strategy_blue_green(self) -> None:
        """Test getting blue-green strategy."""
        strategy = get_strategy(DeploymentStrategy.BLUE_GREEN)
        assert isinstance(strategy, BlueGreenStrategy)

    def test_get_strategy_canary(self) -> None:
        """Test getting canary strategy."""
        strategy = get_strategy(DeploymentStrategy.CANARY)
        assert isinstance(strategy, CanaryStrategy)

    def test_get_strategy_recreate(self) -> None:
        """Test getting recreate strategy."""
        strategy = get_strategy(DeploymentStrategy.RECREATE)
        assert isinstance(strategy, RecreateStrategy)

    def test_get_strategy_invalid(self) -> None:
        """Test getting invalid strategy raises error."""
        with pytest.raises(ValueError):
            get_strategy("invalid")  # type: ignore


class TestDeploymentExceptions:
    """Tests for deployment exceptions."""

    def test_deployment_error(self) -> None:
        """Test DeploymentError exception."""
        error = DeploymentError("Deployment failed", "deploy-1")
        assert str(error) == "Deployment failed"
        assert error.deployment_id == "deploy-1"

    def test_rollback_error(self) -> None:
        """Test RollbackError exception."""
        error = RollbackError("No previous version", "deploy-1")
        assert str(error) == "No previous version"
        assert error.deployment_id == "deploy-1"
