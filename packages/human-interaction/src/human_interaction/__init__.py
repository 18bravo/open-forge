"""
Open Forge Human Interaction Package

Human-in-the-loop workflows and approval systems.

This package provides:
- Approval workflows with state machine and persistence
- Review queues with priority-based management
- Multi-channel notification delivery
- Feedback collection for agent learning
- Timeout-based escalation workflows
- Abstract interfaces for UI integration

Example Usage:
    from human_interaction import (
        ApprovalManager,
        ApprovalType,
        ReviewQueue,
        ReviewPriority,
        NotificationService,
        FeedbackCollector,
        EscalationManager,
    )

    # Create an approval request
    manager = ApprovalManager(event_bus=event_bus)
    approval = await manager.create_request(
        engagement_id="eng-123",
        approval_type=ApprovalType.AGENT_ACTION,
        title="Agent action requires approval",
        requested_by="agent:discovery",
        timeout_minutes=60,
    )

    # Add items to review queue
    queue = ReviewQueue(event_bus=event_bus)
    item = await queue.add_item(
        engagement_id="eng-123",
        category=ReviewCategory.DATA_QUALITY,
        title="Review data mapping",
        priority=ReviewPriority.HIGH,
    )
"""

__version__ = "0.1.0"

# Approvals
from human_interaction.approvals import (
    ApprovalStatus,
    ApprovalType,
    ApprovalRequest,
    ApprovalDecision,
    ApprovalManager,
    ApprovalRequestModel,
    create_approval_for_agent,
)

# Reviews
from human_interaction.review import (
    ReviewStatus,
    ReviewPriority,
    ReviewCategory,
    ReviewItem,
    ReviewResult,
    BatchReviewResult,
    ReviewQueue,
    ReviewItemModel,
)

# Notifications
from human_interaction.notifications import (
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    Notification,
    NotificationRequest,
    NotificationChannelProvider,
    EmailNotificationProvider,
    SlackNotificationProvider,
    InAppNotificationProvider,
    NotificationService,
    NotificationModel,
)

# Feedback
from human_interaction.feedback import (
    FeedbackType,
    FeedbackCategory,
    FeedbackSentiment,
    FeedbackEntry,
    FeedbackFormField,
    FeedbackForm,
    FeedbackSummary,
    AgentLearningSignal,
    FeedbackCollector,
    FeedbackModel,
    AGENT_OUTPUT_FEEDBACK_FORM,
    MAPPING_FEEDBACK_FORM,
)

# Escalation
from human_interaction.escalation import (
    EscalationTrigger,
    EscalationAction,
    EscalationLevel,
    EscalationPolicy,
    EscalationHistory,
    EscalationManager,
    EscalationPolicyModel,
    EscalationHistoryModel,
    DEFAULT_ESCALATION_POLICY,
    URGENT_ESCALATION_POLICY,
)

# Interfaces
from human_interaction.interfaces import (
    PaginationParams,
    PaginatedResult,
    FilterOperator,
    FilterCondition,
    ApprovalListParams,
    ReviewListParams,
    NotificationListParams,
    ApprovalInterface,
    ReviewInterface,
    NotificationInterface,
    FeedbackInterface,
    HumanInteractionPortal,
)

__all__ = [
    # Version
    "__version__",
    # Approvals
    "ApprovalStatus",
    "ApprovalType",
    "ApprovalRequest",
    "ApprovalDecision",
    "ApprovalManager",
    "ApprovalRequestModel",
    "create_approval_for_agent",
    # Reviews
    "ReviewStatus",
    "ReviewPriority",
    "ReviewCategory",
    "ReviewItem",
    "ReviewResult",
    "BatchReviewResult",
    "ReviewQueue",
    "ReviewItemModel",
    # Notifications
    "NotificationChannel",
    "NotificationPriority",
    "NotificationType",
    "Notification",
    "NotificationRequest",
    "NotificationChannelProvider",
    "EmailNotificationProvider",
    "SlackNotificationProvider",
    "InAppNotificationProvider",
    "NotificationService",
    "NotificationModel",
    # Feedback
    "FeedbackType",
    "FeedbackCategory",
    "FeedbackSentiment",
    "FeedbackEntry",
    "FeedbackFormField",
    "FeedbackForm",
    "FeedbackSummary",
    "AgentLearningSignal",
    "FeedbackCollector",
    "FeedbackModel",
    "AGENT_OUTPUT_FEEDBACK_FORM",
    "MAPPING_FEEDBACK_FORM",
    # Escalation
    "EscalationTrigger",
    "EscalationAction",
    "EscalationLevel",
    "EscalationPolicy",
    "EscalationHistory",
    "EscalationManager",
    "EscalationPolicyModel",
    "EscalationHistoryModel",
    "DEFAULT_ESCALATION_POLICY",
    "URGENT_ESCALATION_POLICY",
    # Interfaces
    "PaginationParams",
    "PaginatedResult",
    "FilterOperator",
    "FilterCondition",
    "ApprovalListParams",
    "ReviewListParams",
    "NotificationListParams",
    "ApprovalInterface",
    "ReviewInterface",
    "NotificationInterface",
    "FeedbackInterface",
    "HumanInteractionPortal",
]
