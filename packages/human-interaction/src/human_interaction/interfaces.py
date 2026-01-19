"""
Abstract interfaces for UI integration.

Provides ApprovalInterface, ReviewInterface, and NotificationInterface
for implementing UI components that interact with human-in-the-loop systems.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Callable, Dict, Generic, List, Optional, TypeVar
from enum import Enum

from pydantic import BaseModel, Field

from human_interaction.approvals import (
    ApprovalRequest,
    ApprovalDecision,
    ApprovalStatus,
    ApprovalType,
)
from human_interaction.review import (
    ReviewItem,
    ReviewResult,
    ReviewStatus,
    ReviewCategory,
    ReviewPriority,
)
from human_interaction.notifications import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from human_interaction.feedback import (
    FeedbackEntry,
    FeedbackForm,
    FeedbackType,
    FeedbackCategory,
)


# Type variable for generic pagination
T = TypeVar("T")


class PaginationParams(BaseModel):
    """Pagination parameters for list queries."""
    page: int = 1
    page_size: int = 20
    sort_by: Optional[str] = None
    sort_order: str = "desc"


class PaginatedResult(BaseModel, Generic[T]):
    """Paginated result wrapper."""
    items: List[Any]  # Will be List[T] at runtime
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int,
    ) -> "PaginatedResult[T]":
        """Create a paginated result."""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )


class FilterOperator(str, Enum):
    """Filter operators for queries."""
    EQUALS = "eq"
    NOT_EQUALS = "ne"
    GREATER_THAN = "gt"
    LESS_THAN = "lt"
    GREATER_OR_EQUAL = "gte"
    LESS_OR_EQUAL = "lte"
    CONTAINS = "contains"
    IN = "in"
    NOT_IN = "not_in"


class FilterCondition(BaseModel):
    """A single filter condition."""
    field: str
    operator: FilterOperator
    value: Any


class ApprovalListParams(BaseModel):
    """Parameters for listing approvals."""
    engagement_id: Optional[str] = None
    status: Optional[List[ApprovalStatus]] = None
    approval_type: Optional[List[ApprovalType]] = None
    requested_by: Optional[str] = None
    escalation_level: Optional[str] = None
    has_deadline: Optional[bool] = None
    deadline_before: Optional[datetime] = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class ReviewListParams(BaseModel):
    """Parameters for listing review items."""
    engagement_id: Optional[str] = None
    status: Optional[List[ReviewStatus]] = None
    category: Optional[List[ReviewCategory]] = None
    priority: Optional[List[ReviewPriority]] = None
    assigned_to: Optional[str] = None
    batch_id: Optional[str] = None
    source_type: Optional[str] = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class NotificationListParams(BaseModel):
    """Parameters for listing notifications."""
    user_id: str
    is_read: Optional[bool] = None
    notification_type: Optional[List[NotificationType]] = None
    priority: Optional[List[NotificationPriority]] = None
    engagement_id: Optional[str] = None
    pagination: PaginationParams = Field(default_factory=PaginationParams)


class ApprovalInterface(ABC):
    """
    Abstract interface for approval UI components.

    Implement this interface to create custom UI components
    for managing approvals in web, mobile, or CLI applications.
    """

    @abstractmethod
    async def list_approvals(
        self,
        params: ApprovalListParams,
    ) -> PaginatedResult[ApprovalRequest]:
        """
        List approval requests with filtering and pagination.

        Args:
            params: List parameters including filters and pagination.

        Returns:
            Paginated list of ApprovalRequests.
        """
        pass

    @abstractmethod
    async def get_approval(
        self,
        approval_id: str,
    ) -> Optional[ApprovalRequest]:
        """
        Get a single approval request by ID.

        Args:
            approval_id: The approval ID.

        Returns:
            The ApprovalRequest if found.
        """
        pass

    @abstractmethod
    async def submit_decision(
        self,
        approval_id: str,
        decision: ApprovalDecision,
    ) -> ApprovalRequest:
        """
        Submit a decision on an approval.

        Args:
            approval_id: The approval ID.
            decision: The approval decision.

        Returns:
            The updated ApprovalRequest.
        """
        pass

    @abstractmethod
    async def get_approval_context(
        self,
        approval_id: str,
    ) -> Dict[str, Any]:
        """
        Get the full context for an approval.

        This may include related data, history, comments, etc.

        Args:
            approval_id: The approval ID.

        Returns:
            Dict containing all context information.
        """
        pass

    @abstractmethod
    async def add_comment(
        self,
        approval_id: str,
        user_id: str,
        comment: str,
    ) -> None:
        """
        Add a comment to an approval.

        Args:
            approval_id: The approval ID.
            user_id: The commenting user.
            comment: The comment text.
        """
        pass

    @abstractmethod
    async def get_my_pending_approvals(
        self,
        user_id: str,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResult[ApprovalRequest]:
        """
        Get approvals pending action from a specific user.

        Args:
            user_id: The user ID.
            pagination: Optional pagination params.

        Returns:
            Paginated list of pending approvals.
        """
        pass

    @abstractmethod
    async def get_approval_stats(
        self,
        engagement_id: Optional[str] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get approval statistics.

        Args:
            engagement_id: Optional engagement filter.
            user_id: Optional user filter.

        Returns:
            Dict with statistics (counts, averages, etc.).
        """
        pass


class ReviewInterface(ABC):
    """
    Abstract interface for review UI components.

    Implement this interface to create custom UI components
    for managing review queues.
    """

    @abstractmethod
    async def list_review_items(
        self,
        params: ReviewListParams,
    ) -> PaginatedResult[ReviewItem]:
        """
        List review items with filtering and pagination.

        Args:
            params: List parameters including filters and pagination.

        Returns:
            Paginated list of ReviewItems.
        """
        pass

    @abstractmethod
    async def get_review_item(
        self,
        item_id: str,
    ) -> Optional[ReviewItem]:
        """
        Get a single review item by ID.

        Args:
            item_id: The review item ID.

        Returns:
            The ReviewItem if found.
        """
        pass

    @abstractmethod
    async def claim_item(
        self,
        item_id: str,
        reviewer: str,
    ) -> ReviewItem:
        """
        Claim a review item for review.

        Args:
            item_id: The review item ID.
            reviewer: The claiming reviewer.

        Returns:
            The updated ReviewItem.
        """
        pass

    @abstractmethod
    async def submit_review(
        self,
        item_id: str,
        result: ReviewResult,
    ) -> ReviewItem:
        """
        Submit a review for an item.

        Args:
            item_id: The review item ID.
            result: The review result.

        Returns:
            The updated ReviewItem.
        """
        pass

    @abstractmethod
    async def get_next_item(
        self,
        reviewer: str,
        engagement_id: Optional[str] = None,
        category: Optional[ReviewCategory] = None,
    ) -> Optional[ReviewItem]:
        """
        Get the next item for review and claim it.

        Args:
            reviewer: The reviewer claiming the item.
            engagement_id: Optional engagement filter.
            category: Optional category filter.

        Returns:
            The next ReviewItem or None if queue is empty.
        """
        pass

    @abstractmethod
    async def get_batch_items(
        self,
        batch_id: str,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResult[ReviewItem]:
        """
        Get items in a batch.

        Args:
            batch_id: The batch ID.
            pagination: Optional pagination params.

        Returns:
            Paginated list of batch items.
        """
        pass

    @abstractmethod
    async def submit_batch_review(
        self,
        batch_id: str,
        reviewer: str,
        default_action: ReviewStatus,
        exceptions: Optional[Dict[str, ReviewStatus]] = None,
    ) -> Dict[str, Any]:
        """
        Submit a batch review.

        Args:
            batch_id: The batch ID.
            reviewer: The reviewer.
            default_action: Default status for all items.
            exceptions: Items with different statuses.

        Returns:
            Summary of the batch review.
        """
        pass

    @abstractmethod
    async def get_queue_stats(
        self,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get review queue statistics.

        Args:
            engagement_id: Optional engagement filter.

        Returns:
            Dict with queue statistics.
        """
        pass

    @abstractmethod
    async def get_my_assignments(
        self,
        reviewer: str,
        include_completed: bool = False,
        pagination: Optional[PaginationParams] = None,
    ) -> PaginatedResult[ReviewItem]:
        """
        Get items assigned to a reviewer.

        Args:
            reviewer: The reviewer ID.
            include_completed: Include completed items.
            pagination: Optional pagination params.

        Returns:
            Paginated list of assigned items.
        """
        pass


class NotificationInterface(ABC):
    """
    Abstract interface for notification UI components.

    Implement this interface to create custom notification
    centers and delivery mechanisms.
    """

    @abstractmethod
    async def list_notifications(
        self,
        params: NotificationListParams,
    ) -> PaginatedResult[Notification]:
        """
        List notifications with filtering and pagination.

        Args:
            params: List parameters including filters and pagination.

        Returns:
            Paginated list of Notifications.
        """
        pass

    @abstractmethod
    async def get_notification(
        self,
        notification_id: str,
    ) -> Optional[Notification]:
        """
        Get a single notification by ID.

        Args:
            notification_id: The notification ID.

        Returns:
            The Notification if found.
        """
        pass

    @abstractmethod
    async def mark_as_read(
        self,
        notification_ids: List[str],
        user_id: str,
    ) -> int:
        """
        Mark notifications as read.

        Args:
            notification_ids: IDs of notifications to mark.
            user_id: The user ID (for security).

        Returns:
            Number of notifications marked.
        """
        pass

    @abstractmethod
    async def mark_all_read(
        self,
        user_id: str,
    ) -> int:
        """
        Mark all notifications as read for a user.

        Args:
            user_id: The user ID.

        Returns:
            Number of notifications marked.
        """
        pass

    @abstractmethod
    async def get_unread_count(
        self,
        user_id: str,
    ) -> int:
        """
        Get count of unread notifications.

        Args:
            user_id: The user ID.

        Returns:
            Count of unread notifications.
        """
        pass

    @abstractmethod
    async def delete_notification(
        self,
        notification_id: str,
        user_id: str,
    ) -> bool:
        """
        Delete a notification.

        Args:
            notification_id: The notification ID.
            user_id: The user ID (for security).

        Returns:
            True if deleted, False if not found.
        """
        pass

    @abstractmethod
    async def subscribe_to_updates(
        self,
        user_id: str,
        callback: Callable[[Notification], None],
    ) -> str:
        """
        Subscribe to real-time notification updates.

        Args:
            user_id: The user ID.
            callback: Function to call on new notifications.

        Returns:
            Subscription ID for unsubscribing.
        """
        pass

    @abstractmethod
    async def unsubscribe_from_updates(
        self,
        subscription_id: str,
    ) -> None:
        """
        Unsubscribe from notification updates.

        Args:
            subscription_id: The subscription ID.
        """
        pass

    @abstractmethod
    async def get_notification_preferences(
        self,
        user_id: str,
    ) -> Dict[str, Any]:
        """
        Get notification preferences for a user.

        Args:
            user_id: The user ID.

        Returns:
            Dict of notification preferences.
        """
        pass

    @abstractmethod
    async def update_notification_preferences(
        self,
        user_id: str,
        preferences: Dict[str, Any],
    ) -> None:
        """
        Update notification preferences.

        Args:
            user_id: The user ID.
            preferences: New preference values.
        """
        pass


class FeedbackInterface(ABC):
    """
    Abstract interface for feedback UI components.

    Implement this interface to create custom feedback
    collection forms and displays.
    """

    @abstractmethod
    async def get_form(
        self,
        form_id: str,
    ) -> Optional[FeedbackForm]:
        """
        Get a feedback form definition.

        Args:
            form_id: The form ID.

        Returns:
            The FeedbackForm if found.
        """
        pass

    @abstractmethod
    async def list_forms(
        self,
        category: Optional[FeedbackCategory] = None,
    ) -> List[FeedbackForm]:
        """
        List available feedback forms.

        Args:
            category: Optional category filter.

        Returns:
            List of FeedbackForms.
        """
        pass

    @abstractmethod
    async def submit_feedback(
        self,
        form_id: str,
        user_id: str,
        responses: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None,
    ) -> FeedbackEntry:
        """
        Submit feedback using a form.

        Args:
            form_id: The form ID.
            user_id: The submitting user.
            responses: Form field responses.
            context: Additional context (source, engagement, etc.).

        Returns:
            The created FeedbackEntry.
        """
        pass

    @abstractmethod
    async def submit_quick_rating(
        self,
        user_id: str,
        rating: int,
        source_type: str,
        source_id: str,
        comment: Optional[str] = None,
    ) -> FeedbackEntry:
        """
        Submit a quick rating without a form.

        Args:
            user_id: The submitting user.
            rating: The rating value.
            source_type: Type of thing being rated.
            source_id: ID of thing being rated.
            comment: Optional comment.

        Returns:
            The created FeedbackEntry.
        """
        pass

    @abstractmethod
    async def get_feedback_summary(
        self,
        source_type: str,
        source_id: str,
    ) -> Dict[str, Any]:
        """
        Get feedback summary for a source.

        Args:
            source_type: Type of source.
            source_id: ID of source.

        Returns:
            Summary statistics.
        """
        pass


class HumanInteractionPortal(ABC):
    """
    Unified interface for the complete human interaction portal.

    Provides a single entry point for all human-in-the-loop
    functionality. Implement this to create a complete UI.
    """

    @property
    @abstractmethod
    def approvals(self) -> ApprovalInterface:
        """Get the approval interface."""
        pass

    @property
    @abstractmethod
    def reviews(self) -> ReviewInterface:
        """Get the review interface."""
        pass

    @property
    @abstractmethod
    def notifications(self) -> NotificationInterface:
        """Get the notification interface."""
        pass

    @property
    @abstractmethod
    def feedback(self) -> FeedbackInterface:
        """Get the feedback interface."""
        pass

    @abstractmethod
    async def get_dashboard_data(
        self,
        user_id: str,
        engagement_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get data for the main dashboard.

        Args:
            user_id: The current user.
            engagement_id: Optional engagement context.

        Returns:
            Dict containing dashboard data including:
            - pending_approvals_count
            - review_queue_stats
            - unread_notifications_count
            - recent_activity
        """
        pass

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: str,
        types: Optional[List[str]] = None,
    ) -> Dict[str, List[Any]]:
        """
        Search across all human interaction items.

        Args:
            query: Search query.
            user_id: The searching user.
            types: Optional list of types to search.

        Returns:
            Dict mapping type to list of results.
        """
        pass
