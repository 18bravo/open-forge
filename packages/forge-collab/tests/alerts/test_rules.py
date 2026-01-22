"""Tests for alert rules and conditions."""

from datetime import datetime

import pytest

from forge_collab.alerts.rules import (
    AlertRule,
    AlertCondition,
    AlertAction,
    Severity,
)


class TestAlertCondition:
    """Tests for AlertCondition evaluation."""

    def test_threshold_condition_gt(self):
        """Test threshold condition with greater than operator."""
        condition = AlertCondition(
            type="threshold",
            parameters={
                "metric": "row_count",
                "operator": "gt",
                "value": 1000,
            }
        )

        # Should trigger when above threshold
        assert condition.evaluate({"row_count": 1500}) is True
        assert condition.evaluate({"row_count": 500}) is False
        assert condition.evaluate({"row_count": 1000}) is False

    def test_threshold_condition_lt(self):
        """Test threshold condition with less than operator."""
        condition = AlertCondition(
            type="threshold",
            parameters={
                "metric": "completeness",
                "operator": "lt",
                "value": 0.95,
            }
        )

        # Should trigger when below threshold
        assert condition.evaluate({"completeness": 0.85}) is True
        assert condition.evaluate({"completeness": 0.99}) is False

    def test_change_condition_any(self):
        """Test change condition detecting any change."""
        condition = AlertCondition(
            type="change",
            parameters={
                "field": "schema",
                "change_type": "any",
            }
        )

        # Should trigger when field changes
        assert condition.evaluate({
            "old_schema": "v1",
            "new_schema": "v2",
        }) is True

        # Should not trigger when same
        assert condition.evaluate({
            "old_schema": "v1",
            "new_schema": "v1",
        }) is False

    def test_change_condition_increase(self):
        """Test change condition detecting increase."""
        condition = AlertCondition(
            type="change",
            parameters={
                "field": "size",
                "change_type": "increase",
            }
        )

        assert condition.evaluate({"old_size": 100, "new_size": 200}) is True
        assert condition.evaluate({"old_size": 200, "new_size": 100}) is False

    def test_pattern_condition(self):
        """Test pattern matching condition."""
        condition = AlertCondition(
            type="pattern",
            parameters={
                "field": "status",
                "regex": "FAILED|ERROR",
            }
        )

        assert condition.evaluate({"status": "FAILED"}) is True
        assert condition.evaluate({"status": "ERROR"}) is True
        assert condition.evaluate({"status": "SUCCESS"}) is False

    def test_missing_metric_returns_false(self):
        """Test condition returns false for missing metric."""
        condition = AlertCondition(
            type="threshold",
            parameters={
                "metric": "row_count",
                "operator": "gt",
                "value": 1000,
            }
        )

        assert condition.evaluate({}) is False
        assert condition.evaluate({"other_metric": 500}) is False


class TestAlertRule:
    """Tests for AlertRule matching and evaluation."""

    @pytest.fixture
    def sample_rule(self):
        """Create a sample alert rule."""
        return AlertRule(
            id="rule-123",
            name="Data Quality Alert",
            description="Alert when completeness drops",
            resource_type="dataset",
            resource_pattern="prod-*",
            condition=AlertCondition(
                type="threshold",
                parameters={
                    "metric": "completeness",
                    "operator": "lt",
                    "value": 0.95,
                }
            ),
            actions=[
                AlertAction(
                    type="notify",
                    parameters={"channels": ["slack", "email"]}
                )
            ],
            severity=Severity.WARNING,
            created_by="user-123",
            created_at=datetime.utcnow(),
        )

    def test_matches_resource_exact(self, sample_rule):
        """Test exact resource pattern matching."""
        rule = AlertRule(
            id="rule-456",
            name="Test Rule",
            resource_type="dataset",
            resource_pattern="customer-data",
            condition=AlertCondition(type="threshold", parameters={}),
            actions=[],
            created_by="user-123",
            created_at=datetime.utcnow(),
        )

        assert rule.matches_resource("dataset", "customer-data") is True
        assert rule.matches_resource("dataset", "other-data") is False
        assert rule.matches_resource("pipeline", "customer-data") is False

    def test_matches_resource_glob(self, sample_rule):
        """Test glob pattern matching."""
        assert sample_rule.matches_resource("dataset", "prod-customers") is True
        assert sample_rule.matches_resource("dataset", "prod-sales") is True
        assert sample_rule.matches_resource("dataset", "dev-customers") is False

    def test_evaluate_rule_matches_and_triggers(self, sample_rule):
        """Test rule evaluation when condition is met."""
        result = sample_rule.evaluate(
            resource_type="dataset",
            resource_id="prod-customers",
            event_data={"completeness": 0.85},
        )

        assert result is True

    def test_evaluate_rule_matches_but_no_trigger(self, sample_rule):
        """Test rule evaluation when condition is not met."""
        result = sample_rule.evaluate(
            resource_type="dataset",
            resource_id="prod-customers",
            event_data={"completeness": 0.99},
        )

        assert result is False

    def test_evaluate_rule_no_match(self, sample_rule):
        """Test rule evaluation when resource doesn't match."""
        result = sample_rule.evaluate(
            resource_type="dataset",
            resource_id="dev-customers",  # Doesn't match prod-*
            event_data={"completeness": 0.85},
        )

        assert result is False

    def test_disabled_rule_does_not_evaluate(self, sample_rule):
        """Test disabled rule always returns False."""
        sample_rule.enabled = False

        result = sample_rule.evaluate(
            resource_type="dataset",
            resource_id="prod-customers",
            event_data={"completeness": 0.85},
        )

        assert result is False
