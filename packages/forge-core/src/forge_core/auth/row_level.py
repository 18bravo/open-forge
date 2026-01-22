"""
Row-Level Security

This module defines row-level security policies that filter data access
based on user attributes, roles, or custom conditions.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Protocol, runtime_checkable


class FilterOperator(str, Enum):
    """Operators for filter conditions."""

    EQ = "eq"  # Equal
    NE = "ne"  # Not equal
    GT = "gt"  # Greater than
    GTE = "gte"  # Greater than or equal
    LT = "lt"  # Less than
    LTE = "lte"  # Less than or equal
    IN = "in"  # In list
    NOT_IN = "not_in"  # Not in list
    CONTAINS = "contains"  # String contains
    STARTS_WITH = "starts_with"  # String starts with
    ENDS_WITH = "ends_with"  # String ends with
    IS_NULL = "is_null"  # Is null
    IS_NOT_NULL = "is_not_null"  # Is not null


class LogicalOperator(str, Enum):
    """Logical operators for combining conditions."""

    AND = "and"
    OR = "or"
    NOT = "not"


@dataclass
class FilterCondition:
    """
    A single filter condition.

    Attributes:
        field: Field name to filter on
        operator: Comparison operator
        value: Value to compare against (can be literal or user attribute reference)
    """

    field: str
    operator: FilterOperator
    value: Any

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "field": self.field,
            "operator": self.operator.value,
            "value": self.value,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "FilterCondition":
        """Create from dictionary representation."""
        return cls(
            field=data["field"],
            operator=FilterOperator(data["operator"]),
            value=data["value"],
        )


@dataclass
class Filter:
    """
    A filter that can contain multiple conditions combined with logical operators.

    Filters are composable and can be nested for complex access patterns.

    Examples:
        >>> # Simple filter: department = user's department
        >>> Filter(
        ...     conditions=[FilterCondition("department", FilterOperator.EQ, "$user.department")]
        ... )

        >>> # Complex filter: (department = user's department) AND (region IN user's regions)
        >>> Filter(
        ...     conditions=[
        ...         FilterCondition("department", FilterOperator.EQ, "$user.department"),
        ...         FilterCondition("region", FilterOperator.IN, "$user.regions"),
        ...     ],
        ...     operator=LogicalOperator.AND
        ... )
    """

    conditions: list[FilterCondition | "Filter"] = field(default_factory=list)
    operator: LogicalOperator = LogicalOperator.AND

    def is_empty(self) -> bool:
        """Check if the filter has no conditions."""
        return len(self.conditions) == 0

    def add_condition(self, condition: FilterCondition | "Filter") -> "Filter":
        """Add a condition and return self for chaining."""
        self.conditions.append(condition)
        return self

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "operator": self.operator.value,
            "conditions": [
                c.to_dict() if isinstance(c, (FilterCondition, Filter)) else c
                for c in self.conditions
            ],
        }

    def to_sql_where(self, param_prefix: str = "p") -> tuple[str, dict[str, Any]]:
        """
        Convert filter to SQL WHERE clause.

        Returns:
            Tuple of (SQL string, parameter dictionary)

        Note:
            This is a stub. Real implementation would handle SQL generation safely.
        """
        raise NotImplementedError("SQL generation not yet implemented")


@dataclass
class RowLevelPolicy:
    """
    A row-level security policy that defines data access rules.

    Policies can be based on:
    - User attributes (department, region, etc.)
    - User roles
    - Resource ownership
    - Custom expressions

    Attributes:
        name: Unique policy identifier
        object_type: Type of object this policy applies to
        filter_expression: The filter to apply for this policy
        applies_to_roles: Roles this policy applies to (empty = all roles)
        priority: Policy priority (higher = evaluated first)
        enabled: Whether the policy is active
        description: Human-readable description
    """

    name: str
    object_type: str
    filter_expression: Filter
    applies_to_roles: set[str] = field(default_factory=set)
    priority: int = 0
    enabled: bool = True
    description: str = ""
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def applies_to_user_roles(self, user_roles: set[str]) -> bool:
        """Check if this policy applies to a user with given roles."""
        if not self.applies_to_roles:
            # Empty means applies to all
            return True
        return bool(self.applies_to_roles & user_roles)


@runtime_checkable
class RowLevelSecurityProvider(Protocol):
    """
    Protocol for row-level security providers.

    Implementations should resolve user attributes and build filters.
    """

    async def get_filter_for_user(
        self, user_id: str, object_type: str
    ) -> Filter | None:
        """
        Get the combined filter for a user and object type.

        Args:
            user_id: User identifier
            object_type: Type of object being accessed

        Returns:
            Combined filter from all applicable policies, or None if no filtering
        """
        ...

    async def evaluate_policies(
        self, user_id: str, object_type: str
    ) -> list[RowLevelPolicy]:
        """
        Get all policies that apply to a user and object type.

        Args:
            user_id: User identifier
            object_type: Type of object being accessed

        Returns:
            List of applicable policies in priority order
        """
        ...
