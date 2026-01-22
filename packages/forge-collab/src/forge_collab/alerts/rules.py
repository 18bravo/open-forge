"""Alert rules - Definitions for triggering notifications."""

from datetime import datetime
from enum import Enum
from typing import Literal, Any
import fnmatch
import re

from pydantic import BaseModel, Field


class Severity(str, Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ConditionOperator(str, Enum):
    """Operators for condition evaluation."""

    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_EQUAL = "gte"
    LESS_EQUAL = "lte"
    IN = "in"
    NOT_IN = "not_in"
    CONTAINS = "contains"
    REGEX = "regex"


class AlertCondition(BaseModel):
    """Condition that triggers an alert.

    Supports multiple condition types:
    - threshold: Compare metric against value
    - change: Detect when a field changes
    - pattern: Match field value against regex
    - schedule: Alert if event doesn't occur by expected time
    """

    type: Literal["threshold", "change", "pattern", "schedule"]
    parameters: dict[str, Any]

    def evaluate(self, event_data: dict[str, Any]) -> bool:
        """Evaluate if this condition is met.

        Args:
            event_data: Event data to evaluate against

        Returns:
            True if condition is met (alert should fire)
        """
        if self.type == "threshold":
            return self._evaluate_threshold(event_data)
        elif self.type == "change":
            return self._evaluate_change(event_data)
        elif self.type == "pattern":
            return self._evaluate_pattern(event_data)
        elif self.type == "schedule":
            return self._evaluate_schedule(event_data)
        return False

    def _evaluate_threshold(self, data: dict[str, Any]) -> bool:
        """Evaluate threshold condition."""
        metric = self.parameters.get("metric")
        operator = self.parameters.get("operator")
        value = self.parameters.get("value")

        if metric is None or operator is None or value is None:
            return False

        actual = data.get(metric)
        if actual is None:
            return False

        operators = {
            "eq": lambda a, b: a == b,
            "ne": lambda a, b: a != b,
            "gt": lambda a, b: a > b,
            "lt": lambda a, b: a < b,
            "gte": lambda a, b: a >= b,
            "lte": lambda a, b: a <= b,
        }

        op_func = operators.get(operator)
        if op_func is None:
            return False

        return op_func(actual, value)

    def _evaluate_change(self, data: dict[str, Any]) -> bool:
        """Evaluate change detection condition."""
        field = self.parameters.get("field")
        change_type = self.parameters.get("change_type", "any")

        if field is None:
            return False

        old_value = data.get(f"old_{field}")
        new_value = data.get(f"new_{field}")

        if change_type == "any":
            return old_value != new_value
        elif change_type == "increase":
            try:
                return float(new_value) > float(old_value)
            except (TypeError, ValueError):
                return False
        elif change_type == "decrease":
            try:
                return float(new_value) < float(old_value)
            except (TypeError, ValueError):
                return False

        return False

    def _evaluate_pattern(self, data: dict[str, Any]) -> bool:
        """Evaluate regex pattern match condition."""
        field = self.parameters.get("field")
        pattern = self.parameters.get("regex")

        if field is None or pattern is None:
            return False

        value = data.get(field, "")
        try:
            return bool(re.match(pattern, str(value)))
        except re.error:
            return False

    def _evaluate_schedule(self, data: dict[str, Any]) -> bool:
        """Evaluate schedule-based condition (e.g., expected by time)."""
        # This typically requires external state tracking
        # Scaffold only - full implementation needs scheduler
        expected_by = self.parameters.get("expected_by")
        if expected_by is None:
            return False

        # Check if event arrived late
        event_time = data.get("timestamp")
        if event_time is None:
            return True  # No event = alert

        # TODO: Implement full schedule comparison with timezone
        return False


class AlertAction(BaseModel):
    """Action to take when an alert fires.

    Actions define what happens when an alert condition is met.
    Common actions include sending notifications to various channels.
    """

    type: Literal["notify", "webhook", "execute"]
    parameters: dict[str, Any]


class AlertRule(BaseModel):
    """Alert rule definition.

    An alert rule combines:
    - Resource matching (which resources to monitor)
    - Conditions (when to fire)
    - Actions (what to do when fired)
    - Metadata (severity, ownership, etc.)
    """

    id: str
    name: str
    description: str | None = None
    resource_type: str
    resource_pattern: str = Field(
        description="Glob pattern for matching resources, e.g., 'datasets/prod-*'"
    )
    condition: AlertCondition
    actions: list[AlertAction]
    severity: Severity = Severity.WARNING
    enabled: bool = True
    created_by: str
    created_at: datetime
    updated_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    def matches_resource(self, resource_type: str, resource_id: str) -> bool:
        """Check if this rule applies to a specific resource.

        Args:
            resource_type: Type of the resource
            resource_id: ID of the resource

        Returns:
            True if the rule matches this resource
        """
        if self.resource_type != resource_type:
            return False

        return fnmatch.fnmatch(resource_id, self.resource_pattern)

    def evaluate(
        self,
        resource_type: str,
        resource_id: str,
        event_data: dict[str, Any],
    ) -> bool:
        """Evaluate if this rule should fire for given event.

        Args:
            resource_type: Type of the resource
            resource_id: ID of the resource
            event_data: Event data to evaluate

        Returns:
            True if alert should fire
        """
        if not self.enabled:
            return False

        if not self.matches_resource(resource_type, resource_id):
            return False

        return self.condition.evaluate(event_data)
