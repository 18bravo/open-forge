"""
Notification system with multiple delivery channels.

Provides NotificationService with support for email, Slack,
and in-app notifications.
"""
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Boolean, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import Base, get_async_db
from core.messaging.events import EventBus


class NotificationChannel(str, Enum):
    """Available notification channels."""
    EMAIL = "email"
    SLACK = "slack"
    IN_APP = "in_app"
    WEBHOOK = "webhook"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Types of notifications."""
    APPROVAL_REQUIRED = "approval_required"
    APPROVAL_DECIDED = "approval_decided"
    REVIEW_ASSIGNED = "review_assigned"
    REVIEW_COMPLETED = "review_completed"
    ESCALATION = "escalation"
    DEADLINE_WARNING = "deadline_warning"
    AGENT_REQUIRES_INPUT = "agent_requires_input"
    SYSTEM_ALERT = "system_alert"


class NotificationModel(Base):
    """SQLAlchemy model for in-app notifications."""
    __tablename__ = "notifications"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(255), nullable=False, index=True)
    notification_type = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    body = Column(Text, nullable=True)
    priority = Column(String(20), default=NotificationPriority.NORMAL.value, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    read_at = Column(DateTime, nullable=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    data = Column(JSON, nullable=True)
    engagement_id = Column(String(36), nullable=True, index=True)
    action_url = Column(String(500), nullable=True)


class Notification(BaseModel):
    """Pydantic model for notifications."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    user_id: str
    notification_type: NotificationType
    title: str
    body: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    created_at: datetime = Field(default_factory=datetime.utcnow)
    read_at: Optional[datetime] = None
    is_read: bool = False
    data: Optional[Dict[str, Any]] = None
    engagement_id: Optional[str] = None
    action_url: Optional[str] = None

    class Config:
        from_attributes = True


class NotificationRequest(BaseModel):
    """Request to send a notification."""
    recipients: List[str]
    notification_type: NotificationType
    title: str
    body: Optional[str] = None
    priority: NotificationPriority = NotificationPriority.NORMAL
    channels: List[NotificationChannel] = Field(default_factory=lambda: [NotificationChannel.IN_APP])
    data: Optional[Dict[str, Any]] = None
    engagement_id: Optional[str] = None
    action_url: Optional[str] = None


class NotificationChannelProvider(ABC):
    """Abstract base class for notification channel providers."""

    @property
    @abstractmethod
    def channel(self) -> NotificationChannel:
        """Return the channel this provider handles."""
        pass

    @abstractmethod
    async def send(
        self,
        recipient: str,
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a notification through this channel.

        Args:
            recipient: The recipient identifier.
            title: Notification title.
            body: Notification body.
            priority: Priority level.
            data: Additional data.

        Returns:
            True if sent successfully, False otherwise.
        """
        pass

    @abstractmethod
    async def send_batch(
        self,
        recipients: List[str],
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """
        Send notifications to multiple recipients.

        Args:
            recipients: List of recipient identifiers.
            title: Notification title.
            body: Notification body.
            priority: Priority level.
            data: Additional data.

        Returns:
            Dict mapping recipient to success status.
        """
        pass


class EmailNotificationProvider(NotificationChannelProvider):
    """
    Email notification provider interface.

    This is an abstract implementation that should be extended
    with actual email sending logic (e.g., SMTP, SendGrid, SES).
    """

    def __init__(
        self,
        smtp_host: Optional[str] = None,
        smtp_port: Optional[int] = None,
        from_address: Optional[str] = None,
    ):
        """
        Initialize the email provider.

        Args:
            smtp_host: SMTP server host.
            smtp_port: SMTP server port.
            from_address: Default from address.
        """
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.from_address = from_address

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.EMAIL

    async def send(
        self,
        recipient: str,
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an email notification.

        Override this method with actual email sending implementation.
        """
        # TODO: Implement actual email sending
        # This is a placeholder that logs the intended email
        import logging
        logging.info(
            f"[EMAIL] To: {recipient}, Subject: {title}, "
            f"Priority: {priority.value}, Body: {body}"
        )
        return True

    async def send_batch(
        self,
        recipients: List[str],
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """Send emails to multiple recipients."""
        results = {}
        for recipient in recipients:
            results[recipient] = await self.send(
                recipient, title, body, priority, data
            )
        return results


class SlackNotificationProvider(NotificationChannelProvider):
    """
    Slack notification provider interface.

    This is an abstract implementation that should be extended
    with actual Slack API integration.
    """

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: Optional[str] = None,
    ):
        """
        Initialize the Slack provider.

        Args:
            webhook_url: Slack webhook URL.
            bot_token: Slack bot token for API access.
            default_channel: Default channel for notifications.
        """
        self.webhook_url = webhook_url
        self.bot_token = bot_token
        self.default_channel = default_channel

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.SLACK

    async def send(
        self,
        recipient: str,
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send a Slack notification.

        Override this method with actual Slack API implementation.
        """
        # TODO: Implement actual Slack sending
        # This is a placeholder that logs the intended message
        import logging
        logging.info(
            f"[SLACK] To: {recipient}, Title: {title}, "
            f"Priority: {priority.value}, Body: {body}"
        )
        return True

    async def send_batch(
        self,
        recipients: List[str],
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """Send Slack messages to multiple recipients."""
        results = {}
        for recipient in recipients:
            results[recipient] = await self.send(
                recipient, title, body, priority, data
            )
        return results


class InAppNotificationProvider(NotificationChannelProvider):
    """In-app notification provider with database persistence."""

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the in-app provider.

        Args:
            event_bus: Optional EventBus for real-time updates.
        """
        self.event_bus = event_bus

    @property
    def channel(self) -> NotificationChannel:
        return NotificationChannel.IN_APP

    async def send(
        self,
        recipient: str,
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Store an in-app notification in the database.
        """
        notification = Notification(
            user_id=recipient,
            notification_type=data.get("type", NotificationType.SYSTEM_ALERT) if data else NotificationType.SYSTEM_ALERT,
            title=title,
            body=body,
            priority=priority,
            data=data,
            engagement_id=data.get("engagement_id") if data else None,
            action_url=data.get("action_url") if data else None,
        )

        await self._persist_notification(notification)

        # Emit real-time event
        if self.event_bus:
            await self.event_bus.publish("notification.created", {
                "notification_id": notification.id,
                "user_id": recipient,
                "title": title,
                "priority": priority.value,
            })

        return True

    async def send_batch(
        self,
        recipients: List[str],
        title: str,
        body: Optional[str],
        priority: NotificationPriority,
        data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, bool]:
        """Create in-app notifications for multiple users."""
        results = {}
        for recipient in recipients:
            results[recipient] = await self.send(
                recipient, title, body, priority, data
            )
        return results

    async def _persist_notification(
        self,
        notification: Notification,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Persist notification to database."""
        model = NotificationModel(
            id=notification.id,
            user_id=notification.user_id,
            notification_type=notification.notification_type.value,
            title=notification.title,
            body=notification.body,
            priority=notification.priority.value,
            created_at=notification.created_at,
            data=notification.data,
            engagement_id=notification.engagement_id,
            action_url=notification.action_url,
        )

        async def _save(s: AsyncSession) -> None:
            s.add(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)


class NotificationService:
    """
    Central notification service managing multiple channels.

    Coordinates notification delivery across email, Slack,
    and in-app channels.
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the NotificationService.

        Args:
            event_bus: Optional EventBus for events and in-app notifications.
        """
        self.event_bus = event_bus
        self._providers: Dict[NotificationChannel, NotificationChannelProvider] = {}

        # Register default in-app provider
        self.register_provider(InAppNotificationProvider(event_bus))

    def register_provider(self, provider: NotificationChannelProvider) -> None:
        """
        Register a notification channel provider.

        Args:
            provider: The provider to register.
        """
        self._providers[provider.channel] = provider

    def get_provider(
        self,
        channel: NotificationChannel
    ) -> Optional[NotificationChannelProvider]:
        """
        Get a registered provider by channel.

        Args:
            channel: The notification channel.

        Returns:
            The provider if registered, None otherwise.
        """
        return self._providers.get(channel)

    async def send(
        self,
        request: NotificationRequest,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notifications according to the request.

        Args:
            request: The notification request.

        Returns:
            Nested dict mapping channel to recipient to success status.
        """
        results: Dict[str, Dict[str, bool]] = {}

        for channel in request.channels:
            provider = self._providers.get(channel)
            if not provider:
                results[channel.value] = {
                    recipient: False for recipient in request.recipients
                }
                continue

            # Add notification type to data
            data = request.data or {}
            data["type"] = request.notification_type
            data["engagement_id"] = request.engagement_id
            data["action_url"] = request.action_url

            channel_results = await provider.send_batch(
                recipients=request.recipients,
                title=request.title,
                body=request.body,
                priority=request.priority,
                data=data,
            )
            results[channel.value] = channel_results

        return results

    async def notify_approval_required(
        self,
        approval_id: str,
        engagement_id: str,
        title: str,
        approvers: List[str],
        description: Optional[str] = None,
        deadline: Optional[datetime] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notifications for a required approval.

        Args:
            approval_id: ID of the approval request.
            engagement_id: ID of the engagement.
            title: Title of the approval.
            approvers: List of user IDs who can approve.
            description: Optional description.
            deadline: Optional deadline.
            channels: Channels to use (defaults to in_app and email).

        Returns:
            Results of notification delivery.
        """
        channels = channels or [NotificationChannel.IN_APP, NotificationChannel.EMAIL]

        body = description or f"An approval is required: {title}"
        if deadline:
            body += f"\n\nDeadline: {deadline.isoformat()}"

        return await self.send(NotificationRequest(
            recipients=approvers,
            notification_type=NotificationType.APPROVAL_REQUIRED,
            title=f"Approval Required: {title}",
            body=body,
            priority=NotificationPriority.HIGH,
            channels=channels,
            engagement_id=engagement_id,
            data={
                "approval_id": approval_id,
                "deadline": deadline.isoformat() if deadline else None,
            },
            action_url=f"/approvals/{approval_id}",
        ))

    async def notify_approval_decided(
        self,
        approval_id: str,
        engagement_id: str,
        title: str,
        requester: str,
        decision: str,
        decided_by: str,
        comments: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notification about an approval decision.

        Args:
            approval_id: ID of the approval request.
            engagement_id: ID of the engagement.
            title: Title of the approval.
            requester: User who requested approval.
            decision: The decision (approved/rejected).
            decided_by: Who made the decision.
            comments: Optional decision comments.
            channels: Channels to use.

        Returns:
            Results of notification delivery.
        """
        channels = channels or [NotificationChannel.IN_APP]

        body = f"Your approval request has been {decision} by {decided_by}."
        if comments:
            body += f"\n\nComments: {comments}"

        return await self.send(NotificationRequest(
            recipients=[requester],
            notification_type=NotificationType.APPROVAL_DECIDED,
            title=f"Approval {decision.title()}: {title}",
            body=body,
            priority=NotificationPriority.NORMAL,
            channels=channels,
            engagement_id=engagement_id,
            data={
                "approval_id": approval_id,
                "decision": decision,
                "decided_by": decided_by,
            },
            action_url=f"/approvals/{approval_id}",
        ))

    async def notify_review_assigned(
        self,
        item_id: str,
        engagement_id: str,
        title: str,
        reviewer: str,
        category: str,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notification about a review assignment.

        Args:
            item_id: ID of the review item.
            engagement_id: ID of the engagement.
            title: Title of the review item.
            reviewer: User assigned to review.
            category: Category of the item.
            channels: Channels to use.

        Returns:
            Results of notification delivery.
        """
        channels = channels or [NotificationChannel.IN_APP]

        return await self.send(NotificationRequest(
            recipients=[reviewer],
            notification_type=NotificationType.REVIEW_ASSIGNED,
            title=f"Review Assigned: {title}",
            body=f"You have been assigned to review a {category} item.",
            priority=NotificationPriority.NORMAL,
            channels=channels,
            engagement_id=engagement_id,
            data={
                "item_id": item_id,
                "category": category,
            },
            action_url=f"/reviews/{item_id}",
        ))

    async def notify_escalation(
        self,
        approval_id: str,
        engagement_id: str,
        title: str,
        escalated_to: List[str],
        escalation_level: str,
        reason: Optional[str] = None,
        channels: Optional[List[NotificationChannel]] = None,
    ) -> Dict[str, Dict[str, bool]]:
        """
        Send notification about an escalation.

        Args:
            approval_id: ID of the approval request.
            engagement_id: ID of the engagement.
            title: Title of the approval.
            escalated_to: Users to escalate to.
            escalation_level: The escalation level.
            reason: Reason for escalation.
            channels: Channels to use.

        Returns:
            Results of notification delivery.
        """
        channels = channels or [
            NotificationChannel.IN_APP,
            NotificationChannel.EMAIL,
            NotificationChannel.SLACK,
        ]

        body = f"An approval request has been escalated to {escalation_level}."
        if reason:
            body += f"\n\nReason: {reason}"

        return await self.send(NotificationRequest(
            recipients=escalated_to,
            notification_type=NotificationType.ESCALATION,
            title=f"Escalation: {title}",
            body=body,
            priority=NotificationPriority.URGENT,
            channels=channels,
            engagement_id=engagement_id,
            data={
                "approval_id": approval_id,
                "escalation_level": escalation_level,
                "reason": reason,
            },
            action_url=f"/approvals/{approval_id}",
        ))

    async def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        session: Optional[AsyncSession] = None,
    ) -> List[Notification]:
        """
        Get notifications for a user.

        Args:
            user_id: The user ID.
            unread_only: Only return unread notifications.
            limit: Maximum number to return.
            session: Optional database session.

        Returns:
            List of notifications.
        """
        from sqlalchemy import select, desc

        async def _fetch(s: AsyncSession) -> List[Notification]:
            query = select(NotificationModel).where(
                NotificationModel.user_id == user_id
            )

            if unread_only:
                query = query.where(NotificationModel.is_read == False)

            query = query.order_by(
                desc(NotificationModel.created_at)
            ).limit(limit)

            result = await s.execute(query)
            rows = result.scalars().all()
            return [Notification.model_validate(row) for row in rows]

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def mark_read(
        self,
        notification_ids: List[str],
        user_id: str,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """
        Mark notifications as read.

        Args:
            notification_ids: IDs of notifications to mark read.
            user_id: The user ID (for security).
            session: Optional database session.

        Returns:
            Number of notifications marked read.
        """
        from sqlalchemy import update

        async def _update(s: AsyncSession) -> int:
            result = await s.execute(
                update(NotificationModel)
                .where(
                    NotificationModel.id.in_(notification_ids),
                    NotificationModel.user_id == user_id,
                )
                .values(
                    is_read=True,
                    read_at=datetime.utcnow(),
                )
            )
            await s.flush()
            return result.rowcount

        if session:
            return await _update(session)

        async with get_async_db() as session:
            return await _update(session)

    async def get_unread_count(
        self,
        user_id: str,
        session: Optional[AsyncSession] = None,
    ) -> int:
        """
        Get count of unread notifications for a user.

        Args:
            user_id: The user ID.
            session: Optional database session.

        Returns:
            Count of unread notifications.
        """
        from sqlalchemy import select, func

        async def _count(s: AsyncSession) -> int:
            result = await s.execute(
                select(func.count(NotificationModel.id)).where(
                    NotificationModel.user_id == user_id,
                    NotificationModel.is_read == False,
                )
            )
            return result.scalar() or 0

        if session:
            return await _count(session)

        async with get_async_db() as session:
            return await _count(session)
