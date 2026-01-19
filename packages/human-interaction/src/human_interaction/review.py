"""
Review workflows with priority-based queue management.

Provides ReviewItem model and ReviewQueue for managing items
requiring human review, with batch processing support.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4
import heapq

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import Base, get_async_db
from core.messaging.events import EventBus


class ReviewStatus(str, Enum):
    """Review item states."""
    QUEUED = "queued"
    IN_REVIEW = "in_review"
    COMPLETED = "completed"
    DEFERRED = "deferred"
    SKIPPED = "skipped"


class ReviewPriority(int, Enum):
    """Priority levels for review items (lower is higher priority)."""
    CRITICAL = 1
    HIGH = 2
    MEDIUM = 3
    LOW = 4
    BACKGROUND = 5


class ReviewCategory(str, Enum):
    """Categories of review items."""
    DATA_QUALITY = "data_quality"
    AGENT_OUTPUT = "agent_output"
    CONFIGURATION = "configuration"
    MAPPING = "mapping"
    ANOMALY = "anomaly"
    COMPLIANCE = "compliance"


class ReviewItemModel(Base):
    """SQLAlchemy model for review items."""
    __tablename__ = "review_items"

    id = Column(String(36), primary_key=True)
    engagement_id = Column(String(36), nullable=False, index=True)
    category = Column(String(50), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    status = Column(
        SQLEnum(ReviewStatus),
        default=ReviewStatus.QUEUED,
        nullable=False,
        index=True
    )
    priority = Column(Integer, default=ReviewPriority.MEDIUM.value, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    assigned_to = Column(String(255), nullable=True, index=True)
    assigned_at = Column(DateTime, nullable=True)
    completed_by = Column(String(255), nullable=True)
    completed_at = Column(DateTime, nullable=True)
    review_data = Column(JSON, nullable=True)
    review_result = Column(JSON, nullable=True)
    batch_id = Column(String(36), nullable=True, index=True)
    source_type = Column(String(50), nullable=True)
    source_id = Column(String(255), nullable=True)


class ReviewItem(BaseModel):
    """Pydantic model for review items."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: str
    category: ReviewCategory
    title: str
    description: Optional[str] = None
    status: ReviewStatus = ReviewStatus.QUEUED
    priority: ReviewPriority = ReviewPriority.MEDIUM
    created_at: datetime = Field(default_factory=datetime.utcnow)
    assigned_to: Optional[str] = None
    assigned_at: Optional[datetime] = None
    completed_by: Optional[str] = None
    completed_at: Optional[datetime] = None
    review_data: Optional[Dict[str, Any]] = None
    review_result: Optional[Dict[str, Any]] = None
    batch_id: Optional[str] = None
    source_type: Optional[str] = None
    source_id: Optional[str] = None

    class Config:
        from_attributes = True

    def __lt__(self, other: "ReviewItem") -> bool:
        """Comparison for priority queue (lower priority value = higher priority)."""
        if self.priority.value != other.priority.value:
            return self.priority.value < other.priority.value
        return self.created_at < other.created_at


class ReviewResult(BaseModel):
    """Result of a review action."""
    status: ReviewStatus
    reviewer: str
    comments: Optional[str] = None
    corrections: Optional[Dict[str, Any]] = None
    flags: Optional[List[str]] = None


class BatchReviewResult(BaseModel):
    """Result of a batch review operation."""
    batch_id: str
    items_reviewed: int
    items_accepted: int
    items_rejected: int
    items_deferred: int
    reviewer: str
    completed_at: datetime


class ReviewQueue:
    """
    Priority-based queue for managing review items.

    Supports:
    - Priority-based ordering
    - Assignment tracking
    - Batch operations
    - Category filtering
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the ReviewQueue.

        Args:
            event_bus: Optional EventBus for publishing review events.
        """
        self.event_bus = event_bus
        self._in_memory_queue: List[ReviewItem] = []
        self._use_database = True

    async def add_item(
        self,
        engagement_id: str,
        category: ReviewCategory,
        title: str,
        description: Optional[str] = None,
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        review_data: Optional[Dict[str, Any]] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> ReviewItem:
        """
        Add an item to the review queue.

        Args:
            engagement_id: ID of the associated engagement.
            category: Category of the review item.
            title: Brief title for the item.
            description: Detailed description.
            priority: Priority level.
            review_data: Data to be reviewed.
            source_type: Type of source (e.g., "agent", "pipeline").
            source_id: ID of the source.
            batch_id: Optional batch identifier.
            session: Optional database session.

        Returns:
            The created ReviewItem.
        """
        item = ReviewItem(
            engagement_id=engagement_id,
            category=category,
            title=title,
            description=description,
            priority=priority,
            review_data=review_data,
            source_type=source_type,
            source_id=source_id,
            batch_id=batch_id,
        )

        await self._persist_item(item, session)

        await self._emit_event("review.item_added", {
            "item_id": item.id,
            "engagement_id": item.engagement_id,
            "category": item.category.value,
            "priority": item.priority.value,
            "title": item.title,
            "batch_id": item.batch_id,
        })

        return item

    async def add_batch(
        self,
        engagement_id: str,
        category: ReviewCategory,
        items: List[Dict[str, Any]],
        priority: ReviewPriority = ReviewPriority.MEDIUM,
        source_type: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> str:
        """
        Add multiple items as a batch.

        Args:
            engagement_id: ID of the associated engagement.
            category: Category for all items.
            items: List of item data dicts with 'title', 'description', 'review_data'.
            priority: Priority for all items.
            source_type: Type of source.
            session: Optional database session.

        Returns:
            The batch ID.
        """
        batch_id = str(uuid4())

        for item_data in items:
            await self.add_item(
                engagement_id=engagement_id,
                category=category,
                title=item_data.get("title", "Batch Item"),
                description=item_data.get("description"),
                priority=priority,
                review_data=item_data.get("review_data"),
                source_type=source_type,
                source_id=item_data.get("source_id"),
                batch_id=batch_id,
                session=session,
            )

        await self._emit_event("review.batch_created", {
            "batch_id": batch_id,
            "engagement_id": engagement_id,
            "category": category.value,
            "item_count": len(items),
        })

        return batch_id

    async def get_next(
        self,
        engagement_id: Optional[str] = None,
        category: Optional[ReviewCategory] = None,
        reviewer: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ReviewItem]:
        """
        Get the next highest-priority item from the queue.

        Args:
            engagement_id: Optional filter by engagement.
            category: Optional filter by category.
            reviewer: If provided, assigns the item to this reviewer.
            session: Optional database session.

        Returns:
            The next ReviewItem or None if queue is empty.
        """
        from sqlalchemy import select, asc

        async def _fetch(s: AsyncSession) -> Optional[ReviewItem]:
            query = select(ReviewItemModel).where(
                ReviewItemModel.status == ReviewStatus.QUEUED
            )

            if engagement_id:
                query = query.where(ReviewItemModel.engagement_id == engagement_id)
            if category:
                query = query.where(ReviewItemModel.category == category.value)

            query = query.order_by(
                asc(ReviewItemModel.priority),
                asc(ReviewItemModel.created_at)
            ).limit(1)

            result = await s.execute(query)
            row = result.scalar_one_or_none()

            if row:
                item = ReviewItem.model_validate(row)

                if reviewer:
                    item.assigned_to = reviewer
                    item.assigned_at = datetime.utcnow()
                    item.status = ReviewStatus.IN_REVIEW
                    await self._update_item(item, s)

                    await self._emit_event("review.item_assigned", {
                        "item_id": item.id,
                        "reviewer": reviewer,
                        "assigned_at": item.assigned_at.isoformat(),
                    })

                return item
            return None

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def get_batch_items(
        self,
        batch_id: str,
        status: Optional[ReviewStatus] = None,
        session: Optional[AsyncSession] = None,
    ) -> List[ReviewItem]:
        """
        Get all items in a batch.

        Args:
            batch_id: The batch identifier.
            status: Optional status filter.
            session: Optional database session.

        Returns:
            List of ReviewItems in the batch.
        """
        from sqlalchemy import select, asc

        async def _fetch(s: AsyncSession) -> List[ReviewItem]:
            query = select(ReviewItemModel).where(
                ReviewItemModel.batch_id == batch_id
            )

            if status:
                query = query.where(ReviewItemModel.status == status)

            query = query.order_by(
                asc(ReviewItemModel.priority),
                asc(ReviewItemModel.created_at)
            )

            result = await s.execute(query)
            rows = result.scalars().all()
            return [ReviewItem.model_validate(row) for row in rows]

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def complete_review(
        self,
        item_id: str,
        result: ReviewResult,
        session: Optional[AsyncSession] = None,
    ) -> ReviewItem:
        """
        Complete the review of an item.

        Args:
            item_id: ID of the review item.
            result: The review result.
            session: Optional database session.

        Returns:
            The updated ReviewItem.
        """
        item = await self.get_item(item_id, session)
        if not item:
            raise ValueError(f"Review item {item_id} not found")

        item.status = result.status
        item.completed_by = result.reviewer
        item.completed_at = datetime.utcnow()
        item.review_result = {
            "status": result.status.value,
            "comments": result.comments,
            "corrections": result.corrections,
            "flags": result.flags,
        }

        await self._update_item(item, session)

        await self._emit_event("review.item_completed", {
            "item_id": item.id,
            "engagement_id": item.engagement_id,
            "status": item.status.value,
            "reviewer": result.reviewer,
            "completed_at": item.completed_at.isoformat(),
        })

        return item

    async def complete_batch(
        self,
        batch_id: str,
        reviewer: str,
        default_action: ReviewStatus = ReviewStatus.COMPLETED,
        exceptions: Optional[Dict[str, ReviewStatus]] = None,
        session: Optional[AsyncSession] = None,
    ) -> BatchReviewResult:
        """
        Complete all items in a batch.

        Args:
            batch_id: The batch identifier.
            reviewer: The reviewer completing the batch.
            default_action: Default status for all items.
            exceptions: Dict mapping item IDs to different statuses.
            session: Optional database session.

        Returns:
            BatchReviewResult summarizing the operation.
        """
        exceptions = exceptions or {}

        items = await self.get_batch_items(batch_id, session=session)

        counts = {
            "accepted": 0,
            "rejected": 0,
            "deferred": 0,
        }

        for item in items:
            if item.status not in [ReviewStatus.QUEUED, ReviewStatus.IN_REVIEW]:
                continue

            status = exceptions.get(item.id, default_action)
            result = ReviewResult(
                status=status,
                reviewer=reviewer,
            )
            await self.complete_review(item.id, result, session)

            if status == ReviewStatus.COMPLETED:
                counts["accepted"] += 1
            elif status == ReviewStatus.SKIPPED:
                counts["rejected"] += 1
            elif status == ReviewStatus.DEFERRED:
                counts["deferred"] += 1

        batch_result = BatchReviewResult(
            batch_id=batch_id,
            items_reviewed=len(items),
            items_accepted=counts["accepted"],
            items_rejected=counts["rejected"],
            items_deferred=counts["deferred"],
            reviewer=reviewer,
            completed_at=datetime.utcnow(),
        )

        await self._emit_event("review.batch_completed", {
            "batch_id": batch_id,
            "items_reviewed": batch_result.items_reviewed,
            "items_accepted": batch_result.items_accepted,
            "items_rejected": batch_result.items_rejected,
            "items_deferred": batch_result.items_deferred,
            "reviewer": reviewer,
            "completed_at": batch_result.completed_at.isoformat(),
        })

        return batch_result

    async def get_item(
        self,
        item_id: str,
        session: Optional[AsyncSession] = None,
    ) -> Optional[ReviewItem]:
        """
        Retrieve a review item by ID.

        Args:
            item_id: ID of the review item.
            session: Optional database session.

        Returns:
            The ReviewItem if found, None otherwise.
        """
        from sqlalchemy import select

        async def _fetch(s: AsyncSession) -> Optional[ReviewItem]:
            result = await s.execute(
                select(ReviewItemModel).where(ReviewItemModel.id == item_id)
            )
            row = result.scalar_one_or_none()
            if row:
                return ReviewItem.model_validate(row)
            return None

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def get_queue_stats(
        self,
        engagement_id: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> Dict[str, Any]:
        """
        Get statistics about the review queue.

        Args:
            engagement_id: Optional filter by engagement.
            session: Optional database session.

        Returns:
            Dict with queue statistics.
        """
        from sqlalchemy import select, func

        async def _fetch(s: AsyncSession) -> Dict[str, Any]:
            # Count by status
            base_query = select(
                ReviewItemModel.status,
                func.count(ReviewItemModel.id)
            )

            if engagement_id:
                base_query = base_query.where(
                    ReviewItemModel.engagement_id == engagement_id
                )

            status_query = base_query.group_by(ReviewItemModel.status)
            status_result = await s.execute(status_query)
            status_counts = dict(status_result.fetchall())

            # Count by priority (queued only)
            priority_query = select(
                ReviewItemModel.priority,
                func.count(ReviewItemModel.id)
            ).where(
                ReviewItemModel.status == ReviewStatus.QUEUED
            )

            if engagement_id:
                priority_query = priority_query.where(
                    ReviewItemModel.engagement_id == engagement_id
                )

            priority_query = priority_query.group_by(ReviewItemModel.priority)
            priority_result = await s.execute(priority_query)
            priority_counts = dict(priority_result.fetchall())

            return {
                "total_queued": status_counts.get(ReviewStatus.QUEUED, 0),
                "in_review": status_counts.get(ReviewStatus.IN_REVIEW, 0),
                "completed": status_counts.get(ReviewStatus.COMPLETED, 0),
                "deferred": status_counts.get(ReviewStatus.DEFERRED, 0),
                "skipped": status_counts.get(ReviewStatus.SKIPPED, 0),
                "by_priority": {
                    "critical": priority_counts.get(ReviewPriority.CRITICAL.value, 0),
                    "high": priority_counts.get(ReviewPriority.HIGH.value, 0),
                    "medium": priority_counts.get(ReviewPriority.MEDIUM.value, 0),
                    "low": priority_counts.get(ReviewPriority.LOW.value, 0),
                    "background": priority_counts.get(ReviewPriority.BACKGROUND.value, 0),
                },
            }

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def defer_item(
        self,
        item_id: str,
        reviewer: str,
        reason: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> ReviewItem:
        """
        Defer a review item for later.

        Args:
            item_id: ID of the review item.
            reviewer: Who deferred the item.
            reason: Reason for deferring.
            session: Optional database session.

        Returns:
            The updated ReviewItem.
        """
        return await self.complete_review(
            item_id,
            ReviewResult(
                status=ReviewStatus.DEFERRED,
                reviewer=reviewer,
                comments=reason,
            ),
            session,
        )

    async def reassign_item(
        self,
        item_id: str,
        new_reviewer: str,
        session: Optional[AsyncSession] = None,
    ) -> ReviewItem:
        """
        Reassign a review item to a different reviewer.

        Args:
            item_id: ID of the review item.
            new_reviewer: The new reviewer.
            session: Optional database session.

        Returns:
            The updated ReviewItem.
        """
        item = await self.get_item(item_id, session)
        if not item:
            raise ValueError(f"Review item {item_id} not found")

        previous_reviewer = item.assigned_to
        item.assigned_to = new_reviewer
        item.assigned_at = datetime.utcnow()
        item.status = ReviewStatus.IN_REVIEW

        await self._update_item(item, session)

        await self._emit_event("review.item_reassigned", {
            "item_id": item.id,
            "previous_reviewer": previous_reviewer,
            "new_reviewer": new_reviewer,
            "reassigned_at": item.assigned_at.isoformat(),
        })

        return item

    async def _persist_item(
        self,
        item: ReviewItem,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Persist a new review item to the database."""
        model = ReviewItemModel(
            id=item.id,
            engagement_id=item.engagement_id,
            category=item.category.value,
            title=item.title,
            description=item.description,
            status=item.status,
            priority=item.priority.value,
            created_at=item.created_at,
            review_data=item.review_data,
            batch_id=item.batch_id,
            source_type=item.source_type,
            source_id=item.source_id,
        )

        async def _save(s: AsyncSession) -> None:
            s.add(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)

    async def _update_item(
        self,
        item: ReviewItem,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Update an existing review item in the database."""
        from sqlalchemy import update

        async def _do_update(s: AsyncSession) -> None:
            await s.execute(
                update(ReviewItemModel)
                .where(ReviewItemModel.id == item.id)
                .values(
                    status=item.status,
                    assigned_to=item.assigned_to,
                    assigned_at=item.assigned_at,
                    completed_by=item.completed_by,
                    completed_at=item.completed_at,
                    review_result=item.review_result,
                )
            )
            await s.flush()

        if session:
            await _do_update(session)
        else:
            async with get_async_db() as session:
                await _do_update(session)

    async def _emit_event(
        self,
        event_type: str,
        payload: Dict[str, Any]
    ) -> None:
        """Emit an event if event bus is configured."""
        if self.event_bus:
            await self.event_bus.publish(event_type, payload)
