"""
Promotion workflow for environment-to-environment deployments.
"""

from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Protocol
from uuid import uuid4

from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from forge_deploy.deployment.models import Deployment
    from forge_deploy.environments.models import Environment


class PromotionRuleType(str, Enum):
    """Types of promotion rules."""

    TESTS_PASSED = "tests_passed"
    HEALTH_CHECK = "health_check"
    MIN_SOAK_TIME = "min_soak_time"
    APPROVAL_REQUIRED = "approval_required"
    ERROR_RATE_BELOW = "error_rate_below"


class PromotionRule(BaseModel):
    """
    A rule that must pass before promotion.

    Rules define conditions that must be met before a deployment
    can be promoted to the next environment.
    """

    type: PromotionRuleType = Field(..., description="Type of rule")
    config: dict = Field(default_factory=dict, description="Rule-specific configuration")
    required: bool = Field(True, description="Whether rule must pass")
    error_message: str | None = Field(None, description="Custom error message on failure")

    class Config:
        use_enum_values = True


class PromotionStatus(str, Enum):
    """Status of a promotion operation."""

    PENDING = "pending"
    CHECKING_RULES = "checking_rules"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class PromotionResult(BaseModel):
    """Result of a promotion operation."""

    id: str = Field(..., description="Promotion identifier")
    source_environment_id: str = Field(..., description="Source environment")
    target_environment_id: str = Field(..., description="Target environment")
    product_id: str = Field(..., description="Product being promoted")
    version: str = Field(..., description="Version being promoted")

    # Status
    status: PromotionStatus = Field(
        PromotionStatus.PENDING, description="Promotion status"
    )

    # Rule checks
    rules_checked: list[dict] = Field(
        default_factory=list, description="Results of rule checks"
    )
    all_rules_passed: bool = Field(False, description="Whether all rules passed")

    # Approval
    approvals: list[dict] = Field(
        default_factory=list, description="Approval records"
    )
    rejected_by: str | None = Field(None, description="User who rejected")
    rejection_reason: str | None = Field(None, description="Reason for rejection")

    # Result
    deployment_id: str | None = Field(
        None, description="Resulting deployment ID if successful"
    )
    error_message: str | None = Field(None, description="Error if failed")

    # Timestamps
    initiated_by: str = Field(..., description="User who initiated promotion")
    initiated_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: datetime | None = Field(None)

    class Config:
        use_enum_values = True


class RuleChecker(Protocol):
    """Protocol for checking promotion rules."""

    async def check(
        self,
        rule: PromotionRule,
        deployment: "Deployment",
        environment: "Environment",
    ) -> tuple[bool, str | None]:
        """
        Check if a rule passes.

        Returns:
            Tuple of (passed, error_message)
        """
        ...


class PromotionWorkflow:
    """
    Manages promotion workflows between environments.

    Handles rule checking, approval workflows, and coordinating
    the actual promotion deployment.
    """

    def __init__(
        self,
        rule_checker: RuleChecker | None = None,
    ) -> None:
        """
        Initialize the promotion workflow.

        Args:
            rule_checker: Implementation for checking promotion rules
        """
        self._rule_checker = rule_checker

    async def initiate(
        self,
        source: "Environment",
        target: "Environment",
        deployment: "Deployment",
        initiated_by: str,
    ) -> PromotionResult:
        """
        Initiate a promotion from one environment to another.

        Args:
            source: Source environment
            target: Target environment
            deployment: Successful deployment to promote
            initiated_by: User initiating the promotion

        Returns:
            Promotion result with initial status

        Raises:
            PromotionError: If promotion cannot be initiated
        """
        # Validate promotion path
        if not target.can_receive_promotion_from(source.id):
            raise PromotionError(
                f"Cannot promote from {source.name} to {target.name}",
                source.id,
                target.id,
            )

        result = PromotionResult(
            id=str(uuid4()),
            source_environment_id=source.id,
            target_environment_id=target.id,
            product_id=deployment.product_id,
            version=deployment.version,
            status=PromotionStatus.CHECKING_RULES,
            initiated_by=initiated_by,
        )

        # Check promotion rules
        if target.promotion_rules:
            rules = [
                PromotionRule(**rule_config)
                for rule_config in target.promotion_rules.get("rules", [])
            ]
            await self._check_rules(result, rules, deployment, source)

        if not result.all_rules_passed:
            result.status = PromotionStatus.FAILED
            return result

        # Check if approval is required
        if target.is_protected():
            result.status = PromotionStatus.AWAITING_APPROVAL
        else:
            result.status = PromotionStatus.APPROVED

        return result

    async def _check_rules(
        self,
        result: PromotionResult,
        rules: list[PromotionRule],
        deployment: "Deployment",
        environment: "Environment",
    ) -> None:
        """Check all promotion rules."""
        all_passed = True

        for rule in rules:
            if self._rule_checker:
                passed, error = await self._rule_checker.check(
                    rule, deployment, environment
                )
            else:
                # Without a rule checker, all rules pass
                passed, error = True, None

            result.rules_checked.append({
                "rule_type": rule.type,
                "passed": passed,
                "error": error,
                "required": rule.required,
            })

            if not passed and rule.required:
                all_passed = False

        result.all_rules_passed = all_passed

    async def approve(
        self,
        promotion: PromotionResult,
        approver_id: str,
        comment: str | None = None,
    ) -> PromotionResult:
        """
        Approve a promotion.

        Args:
            promotion: Promotion awaiting approval
            approver_id: User approving
            comment: Optional approval comment

        Returns:
            Updated promotion result
        """
        if promotion.status != PromotionStatus.AWAITING_APPROVAL:
            raise PromotionError(
                f"Cannot approve promotion in {promotion.status} state",
                promotion.source_environment_id,
                promotion.target_environment_id,
            )

        promotion.approvals.append({
            "user_id": approver_id,
            "approved_at": datetime.utcnow().isoformat(),
            "comment": comment,
        })

        # Check if enough approvals
        # This would need the target environment info for minimum_approvals
        promotion.status = PromotionStatus.APPROVED

        return promotion

    async def reject(
        self,
        promotion: PromotionResult,
        rejector_id: str,
        reason: str,
    ) -> PromotionResult:
        """
        Reject a promotion.

        Args:
            promotion: Promotion to reject
            rejector_id: User rejecting
            reason: Reason for rejection

        Returns:
            Updated promotion result
        """
        promotion.status = PromotionStatus.REJECTED
        promotion.rejected_by = rejector_id
        promotion.rejection_reason = reason
        promotion.completed_at = datetime.utcnow()

        return promotion


class PromotionError(Exception):
    """Raised when a promotion operation fails."""

    def __init__(
        self,
        message: str,
        source_env_id: str | None = None,
        target_env_id: str | None = None,
    ) -> None:
        super().__init__(message)
        self.source_env_id = source_env_id
        self.target_env_id = target_env_id
