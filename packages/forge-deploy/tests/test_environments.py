"""
Tests for environments module.
"""

import pytest
from datetime import datetime

from forge_deploy.environments.models import (
    Environment,
    EnvironmentType,
    EnvironmentVariable,
)
from forge_deploy.environments.promotion import (
    PromotionRule,
    PromotionRuleType,
    PromotionResult,
    PromotionStatus,
    PromotionError,
)


class TestEnvironmentModels:
    """Tests for Environment models."""

    def test_environment_creation(self) -> None:
        """Test creating a basic environment."""
        env = Environment(
            id="prod",
            name="Production",
            type=EnvironmentType.PRODUCTION,
            cluster_id="cluster-1",
            namespace="prod-ns",
        )

        assert env.id == "prod"
        assert env.type == "production"
        assert env.protected is False
        assert env.auto_promote is False

    def test_environment_with_protection(self) -> None:
        """Test creating a protected environment."""
        env = Environment(
            id="prod",
            name="Production",
            type=EnvironmentType.PRODUCTION,
            cluster_id="cluster-1",
            namespace="prod-ns",
            protected=True,
            required_approvers=["user-1", "user-2"],
            minimum_approvals=2,
        )

        assert env.is_protected()
        assert len(env.required_approvers) == 2
        assert env.minimum_approvals == 2

    def test_environment_promotion_chain(self) -> None:
        """Test environment promotion configuration."""
        staging = Environment(
            id="staging",
            name="Staging",
            type=EnvironmentType.STAGING,
            cluster_id="cluster-1",
            namespace="staging-ns",
        )

        prod = Environment(
            id="prod",
            name="Production",
            type=EnvironmentType.PRODUCTION,
            cluster_id="cluster-1",
            namespace="prod-ns",
            promotion_from="staging",
        )

        assert prod.can_receive_promotion_from("staging")
        assert not prod.can_receive_promotion_from("dev")

    def test_environment_variable_plain(self) -> None:
        """Test plain environment variable."""
        var = EnvironmentVariable(
            key="LOG_LEVEL",
            value="INFO",
            secret=False,
        )

        assert var.key == "LOG_LEVEL"
        assert var.value == "INFO"
        assert not var.secret

    def test_environment_variable_secret(self) -> None:
        """Test secret environment variable."""
        var = EnvironmentVariable(
            key="DB_PASSWORD",
            secret=True,
            secret_ref="vault:db/password",
        )

        assert var.secret
        assert var.value is None
        assert var.secret_ref == "vault:db/password"


class TestPromotionModels:
    """Tests for Promotion models."""

    def test_promotion_rule_creation(self) -> None:
        """Test creating a promotion rule."""
        rule = PromotionRule(
            type=PromotionRuleType.TESTS_PASSED,
            config={"test_suite": "integration"},
            required=True,
        )

        assert rule.type == "tests_passed"
        assert rule.required

    def test_promotion_result_creation(self) -> None:
        """Test creating a promotion result."""
        result = PromotionResult(
            id="promo-1",
            source_environment_id="staging",
            target_environment_id="prod",
            product_id="test-product",
            version="1.0.0",
            initiated_by="user-123",
        )

        assert result.status == PromotionStatus.PENDING
        assert result.all_rules_passed is False
        assert result.approvals == []

    def test_promotion_status_values(self) -> None:
        """Test promotion status enum values."""
        assert PromotionStatus.PENDING.value == "pending"
        assert PromotionStatus.AWAITING_APPROVAL.value == "awaiting_approval"
        assert PromotionStatus.APPROVED.value == "approved"
        assert PromotionStatus.COMPLETED.value == "completed"
        assert PromotionStatus.REJECTED.value == "rejected"

    def test_promotion_rule_types(self) -> None:
        """Test promotion rule type enum values."""
        assert PromotionRuleType.TESTS_PASSED.value == "tests_passed"
        assert PromotionRuleType.HEALTH_CHECK.value == "health_check"
        assert PromotionRuleType.MIN_SOAK_TIME.value == "min_soak_time"
        assert PromotionRuleType.APPROVAL_REQUIRED.value == "approval_required"


class TestPromotionExceptions:
    """Tests for promotion exceptions."""

    def test_promotion_error(self) -> None:
        """Test PromotionError exception."""
        error = PromotionError("Cannot promote", "staging", "prod")
        assert str(error) == "Cannot promote"
        assert error.source_env_id == "staging"
        assert error.target_env_id == "prod"
