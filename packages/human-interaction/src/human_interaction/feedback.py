"""
Feedback collection system with structured forms and agent learning.

Provides FeedbackCollector for gathering and analyzing human feedback
on agent outputs, decisions, and system behavior.
"""
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from pydantic import BaseModel, Field
from sqlalchemy import Column, String, DateTime, Text, JSON, Integer, Float, Enum as SQLEnum
from sqlalchemy.ext.asyncio import AsyncSession

from core.database.connection import Base, get_async_db
from core.messaging.events import EventBus


class FeedbackType(str, Enum):
    """Types of feedback."""
    RATING = "rating"
    CORRECTION = "correction"
    SUGGESTION = "suggestion"
    BUG_REPORT = "bug_report"
    QUALITY_ASSESSMENT = "quality_assessment"
    APPROVAL_FEEDBACK = "approval_feedback"


class FeedbackCategory(str, Enum):
    """Categories for feedback context."""
    AGENT_OUTPUT = "agent_output"
    DATA_QUALITY = "data_quality"
    MAPPING_ACCURACY = "mapping_accuracy"
    RECOMMENDATION = "recommendation"
    CLASSIFICATION = "classification"
    UI_UX = "ui_ux"
    PERFORMANCE = "performance"


class FeedbackSentiment(str, Enum):
    """Sentiment of feedback."""
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    NEGATIVE = "negative"


class FeedbackModel(Base):
    """SQLAlchemy model for feedback entries."""
    __tablename__ = "feedback_entries"

    id = Column(String(36), primary_key=True)
    engagement_id = Column(String(36), nullable=True, index=True)
    feedback_type = Column(String(50), nullable=False)
    category = Column(String(50), nullable=False)
    submitted_by = Column(String(255), nullable=False, index=True)
    submitted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Rating fields
    rating = Column(Integer, nullable=True)
    rating_scale_max = Column(Integer, default=5, nullable=True)

    # Text feedback
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)

    # Structured data
    form_data = Column(JSON, nullable=True)
    corrections = Column(JSON, nullable=True)

    # Context
    source_type = Column(String(50), nullable=True)
    source_id = Column(String(255), nullable=True, index=True)
    agent_name = Column(String(255), nullable=True, index=True)

    # Processing
    sentiment = Column(String(20), nullable=True)
    is_processed = Column(Boolean, default=False, nullable=False)
    processed_at = Column(DateTime, nullable=True)


from sqlalchemy import Boolean


class FeedbackEntry(BaseModel):
    """Pydantic model for feedback entries."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    engagement_id: Optional[str] = None
    feedback_type: FeedbackType
    category: FeedbackCategory
    submitted_by: str
    submitted_at: datetime = Field(default_factory=datetime.utcnow)

    # Rating
    rating: Optional[int] = None
    rating_scale_max: int = 5

    # Text
    title: Optional[str] = None
    description: Optional[str] = None

    # Structured
    form_data: Optional[Dict[str, Any]] = None
    corrections: Optional[Dict[str, Any]] = None

    # Context
    source_type: Optional[str] = None
    source_id: Optional[str] = None
    agent_name: Optional[str] = None

    # Processing
    sentiment: Optional[FeedbackSentiment] = None
    is_processed: bool = False
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FeedbackFormField(BaseModel):
    """Definition of a feedback form field."""
    name: str
    label: str
    field_type: str  # text, textarea, select, radio, checkbox, rating
    required: bool = False
    options: Optional[List[str]] = None
    default_value: Optional[Any] = None
    validation: Optional[Dict[str, Any]] = None


class FeedbackForm(BaseModel):
    """Structured feedback form definition."""
    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    feedback_type: FeedbackType
    category: FeedbackCategory
    fields: List[FeedbackFormField]
    include_rating: bool = True
    include_comments: bool = True


class FeedbackSummary(BaseModel):
    """Summary of feedback for a source."""
    source_type: str
    source_id: str
    total_entries: int
    average_rating: Optional[float] = None
    sentiment_breakdown: Dict[str, int]
    category_breakdown: Dict[str, int]
    recent_entries: List[FeedbackEntry]


class AgentLearningSignal(BaseModel):
    """Signal extracted from feedback for agent learning."""
    agent_name: str
    signal_type: str  # correction, preference, quality_issue
    context: Dict[str, Any]
    corrections: Optional[Dict[str, Any]] = None
    confidence: float = 1.0
    source_feedback_ids: List[str]
    created_at: datetime = Field(default_factory=datetime.utcnow)


class FeedbackCollector:
    """
    Collects and manages human feedback for agent learning.

    Supports:
    - Structured feedback forms
    - Rating collection
    - Correction tracking
    - Sentiment analysis
    - Agent learning signal generation
    """

    def __init__(self, event_bus: Optional[EventBus] = None):
        """
        Initialize the FeedbackCollector.

        Args:
            event_bus: Optional EventBus for publishing feedback events.
        """
        self.event_bus = event_bus
        self._forms: Dict[str, FeedbackForm] = {}
        self._learning_handlers: Dict[str, List[Callable]] = {}

    def register_form(self, form: FeedbackForm) -> None:
        """
        Register a feedback form.

        Args:
            form: The feedback form definition.
        """
        self._forms[form.id] = form

    def get_form(self, form_id: str) -> Optional[FeedbackForm]:
        """
        Get a registered feedback form.

        Args:
            form_id: The form identifier.

        Returns:
            The FeedbackForm if found, None otherwise.
        """
        return self._forms.get(form_id)

    def register_learning_handler(
        self,
        agent_name: str,
        handler: Callable[[AgentLearningSignal], None]
    ) -> None:
        """
        Register a handler for agent learning signals.

        Args:
            agent_name: Name of the agent to receive signals.
            handler: Callback function for learning signals.
        """
        if agent_name not in self._learning_handlers:
            self._learning_handlers[agent_name] = []
        self._learning_handlers[agent_name].append(handler)

    async def submit_feedback(
        self,
        feedback_type: FeedbackType,
        category: FeedbackCategory,
        submitted_by: str,
        engagement_id: Optional[str] = None,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        description: Optional[str] = None,
        form_data: Optional[Dict[str, Any]] = None,
        corrections: Optional[Dict[str, Any]] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> FeedbackEntry:
        """
        Submit a feedback entry.

        Args:
            feedback_type: Type of feedback.
            category: Category of feedback.
            submitted_by: User submitting feedback.
            engagement_id: Optional engagement ID.
            rating: Optional numeric rating.
            title: Optional title.
            description: Optional description.
            form_data: Optional structured form data.
            corrections: Optional corrections data.
            source_type: Type of source being rated.
            source_id: ID of source being rated.
            agent_name: Name of agent if feedback is about agent.
            session: Optional database session.

        Returns:
            The created FeedbackEntry.
        """
        # Analyze sentiment
        sentiment = self._analyze_sentiment(rating, description)

        entry = FeedbackEntry(
            engagement_id=engagement_id,
            feedback_type=feedback_type,
            category=category,
            submitted_by=submitted_by,
            rating=rating,
            title=title,
            description=description,
            form_data=form_data,
            corrections=corrections,
            source_type=source_type,
            source_id=source_id,
            agent_name=agent_name,
            sentiment=sentiment,
        )

        await self._persist_entry(entry, session)

        await self._emit_event("feedback.submitted", {
            "feedback_id": entry.id,
            "engagement_id": entry.engagement_id,
            "feedback_type": entry.feedback_type.value,
            "category": entry.category.value,
            "submitted_by": entry.submitted_by,
            "rating": entry.rating,
            "agent_name": entry.agent_name,
            "sentiment": entry.sentiment.value if entry.sentiment else None,
        })

        # Process for learning if it's agent feedback with corrections
        if agent_name and (corrections or feedback_type == FeedbackType.CORRECTION):
            await self._process_for_learning(entry)

        return entry

    async def submit_form_response(
        self,
        form_id: str,
        submitted_by: str,
        responses: Dict[str, Any],
        engagement_id: Optional[str] = None,
        source_type: Optional[str] = None,
        source_id: Optional[str] = None,
        agent_name: Optional[str] = None,
        session: Optional[AsyncSession] = None,
    ) -> FeedbackEntry:
        """
        Submit a response to a feedback form.

        Args:
            form_id: ID of the feedback form.
            submitted_by: User submitting the response.
            responses: Dict mapping field names to values.
            engagement_id: Optional engagement ID.
            source_type: Type of source being rated.
            source_id: ID of source being rated.
            agent_name: Name of agent if feedback is about agent.
            session: Optional database session.

        Returns:
            The created FeedbackEntry.

        Raises:
            ValueError: If form not found or validation fails.
        """
        form = self._forms.get(form_id)
        if not form:
            raise ValueError(f"Feedback form {form_id} not found")

        # Validate required fields
        for field in form.fields:
            if field.required and field.name not in responses:
                raise ValueError(f"Required field '{field.name}' is missing")

        # Extract rating if present
        rating = responses.get("_rating")
        description = responses.get("_comments")

        return await self.submit_feedback(
            feedback_type=form.feedback_type,
            category=form.category,
            submitted_by=submitted_by,
            engagement_id=engagement_id,
            rating=rating,
            title=form.name,
            description=description,
            form_data=responses,
            source_type=source_type,
            source_id=source_id,
            agent_name=agent_name,
            session=session,
        )

    async def get_feedback_summary(
        self,
        source_type: str,
        source_id: str,
        session: Optional[AsyncSession] = None,
    ) -> FeedbackSummary:
        """
        Get a summary of feedback for a source.

        Args:
            source_type: Type of source.
            source_id: ID of source.
            session: Optional database session.

        Returns:
            FeedbackSummary with aggregated stats.
        """
        from sqlalchemy import select, func

        async def _fetch(s: AsyncSession) -> FeedbackSummary:
            # Get all entries for this source
            query = select(FeedbackModel).where(
                FeedbackModel.source_type == source_type,
                FeedbackModel.source_id == source_id,
            )
            result = await s.execute(query)
            rows = result.scalars().all()
            entries = [FeedbackEntry.model_validate(row) for row in rows]

            # Calculate stats
            total = len(entries)
            ratings = [e.rating for e in entries if e.rating is not None]
            avg_rating = sum(ratings) / len(ratings) if ratings else None

            sentiment_breakdown = {
                "positive": 0,
                "neutral": 0,
                "negative": 0,
            }
            for entry in entries:
                if entry.sentiment:
                    sentiment_breakdown[entry.sentiment.value] += 1

            category_breakdown: Dict[str, int] = {}
            for entry in entries:
                cat = entry.category.value
                category_breakdown[cat] = category_breakdown.get(cat, 0) + 1

            # Get recent entries
            recent = sorted(entries, key=lambda x: x.submitted_at, reverse=True)[:5]

            return FeedbackSummary(
                source_type=source_type,
                source_id=source_id,
                total_entries=total,
                average_rating=avg_rating,
                sentiment_breakdown=sentiment_breakdown,
                category_breakdown=category_breakdown,
                recent_entries=recent,
            )

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def get_agent_feedback(
        self,
        agent_name: str,
        feedback_type: Optional[FeedbackType] = None,
        limit: int = 100,
        include_processed: bool = True,
        session: Optional[AsyncSession] = None,
    ) -> List[FeedbackEntry]:
        """
        Get feedback for a specific agent.

        Args:
            agent_name: Name of the agent.
            feedback_type: Optional filter by type.
            limit: Maximum entries to return.
            include_processed: Include already-processed entries.
            session: Optional database session.

        Returns:
            List of FeedbackEntry objects.
        """
        from sqlalchemy import select, desc

        async def _fetch(s: AsyncSession) -> List[FeedbackEntry]:
            query = select(FeedbackModel).where(
                FeedbackModel.agent_name == agent_name
            )

            if feedback_type:
                query = query.where(FeedbackModel.feedback_type == feedback_type.value)

            if not include_processed:
                query = query.where(FeedbackModel.is_processed == False)

            query = query.order_by(desc(FeedbackModel.submitted_at)).limit(limit)

            result = await s.execute(query)
            rows = result.scalars().all()
            return [FeedbackEntry.model_validate(row) for row in rows]

        if session:
            return await _fetch(session)

        async with get_async_db() as session:
            return await _fetch(session)

    async def generate_learning_signals(
        self,
        agent_name: str,
        session: Optional[AsyncSession] = None,
    ) -> List[AgentLearningSignal]:
        """
        Generate learning signals from unprocessed feedback.

        Args:
            agent_name: Name of the agent.
            session: Optional database session.

        Returns:
            List of AgentLearningSignal objects.
        """
        entries = await self.get_agent_feedback(
            agent_name,
            include_processed=False,
            session=session,
        )

        signals: List[AgentLearningSignal] = []

        # Group corrections
        corrections = [e for e in entries if e.corrections or e.feedback_type == FeedbackType.CORRECTION]
        if corrections:
            signal = AgentLearningSignal(
                agent_name=agent_name,
                signal_type="correction",
                context={
                    "count": len(corrections),
                    "categories": list(set(e.category.value for e in corrections)),
                },
                corrections={
                    e.id: e.corrections for e in corrections if e.corrections
                },
                confidence=0.9,
                source_feedback_ids=[e.id for e in corrections],
            )
            signals.append(signal)

        # Analyze quality issues (low ratings)
        low_rated = [e for e in entries if e.rating and e.rating <= 2]
        if low_rated:
            signal = AgentLearningSignal(
                agent_name=agent_name,
                signal_type="quality_issue",
                context={
                    "count": len(low_rated),
                    "average_rating": sum(e.rating for e in low_rated if e.rating) / len(low_rated),
                    "categories": list(set(e.category.value for e in low_rated)),
                    "descriptions": [e.description for e in low_rated if e.description],
                },
                confidence=0.7,
                source_feedback_ids=[e.id for e in low_rated],
            )
            signals.append(signal)

        # Mark entries as processed
        for entry in entries:
            entry.is_processed = True
            entry.processed_at = datetime.utcnow()
            await self._update_entry(entry, session)

        # Call learning handlers
        for signal in signals:
            handlers = self._learning_handlers.get(agent_name, [])
            for handler in handlers:
                try:
                    if asyncio.iscoroutinefunction(handler):
                        await handler(signal)
                    else:
                        handler(signal)
                except Exception as e:
                    import logging
                    logging.error(f"Learning handler error: {e}")

            await self._emit_event("feedback.learning_signal", {
                "agent_name": signal.agent_name,
                "signal_type": signal.signal_type,
                "feedback_count": len(signal.source_feedback_ids),
                "confidence": signal.confidence,
            })

        return signals

    def _analyze_sentiment(
        self,
        rating: Optional[int],
        description: Optional[str],
    ) -> Optional[FeedbackSentiment]:
        """
        Analyze sentiment from rating and description.

        Simple heuristic-based analysis. In production, this could
        use NLP models.
        """
        if rating is not None:
            if rating >= 4:
                return FeedbackSentiment.POSITIVE
            elif rating <= 2:
                return FeedbackSentiment.NEGATIVE
            else:
                return FeedbackSentiment.NEUTRAL

        if description:
            description_lower = description.lower()
            positive_words = ["great", "excellent", "good", "perfect", "amazing", "helpful"]
            negative_words = ["bad", "poor", "wrong", "incorrect", "broken", "terrible"]

            positive_count = sum(1 for word in positive_words if word in description_lower)
            negative_count = sum(1 for word in negative_words if word in description_lower)

            if positive_count > negative_count:
                return FeedbackSentiment.POSITIVE
            elif negative_count > positive_count:
                return FeedbackSentiment.NEGATIVE

        return FeedbackSentiment.NEUTRAL

    async def _process_for_learning(self, entry: FeedbackEntry) -> None:
        """Process a feedback entry for agent learning."""
        if not entry.agent_name:
            return

        await self._emit_event("feedback.requires_learning", {
            "feedback_id": entry.id,
            "agent_name": entry.agent_name,
            "feedback_type": entry.feedback_type.value,
            "has_corrections": entry.corrections is not None,
        })

    async def _persist_entry(
        self,
        entry: FeedbackEntry,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Persist a feedback entry to the database."""
        model = FeedbackModel(
            id=entry.id,
            engagement_id=entry.engagement_id,
            feedback_type=entry.feedback_type.value,
            category=entry.category.value,
            submitted_by=entry.submitted_by,
            submitted_at=entry.submitted_at,
            rating=entry.rating,
            rating_scale_max=entry.rating_scale_max,
            title=entry.title,
            description=entry.description,
            form_data=entry.form_data,
            corrections=entry.corrections,
            source_type=entry.source_type,
            source_id=entry.source_id,
            agent_name=entry.agent_name,
            sentiment=entry.sentiment.value if entry.sentiment else None,
            is_processed=entry.is_processed,
        )

        async def _save(s: AsyncSession) -> None:
            s.add(model)
            await s.flush()

        if session:
            await _save(session)
        else:
            async with get_async_db() as session:
                await _save(session)

    async def _update_entry(
        self,
        entry: FeedbackEntry,
        session: Optional[AsyncSession] = None,
    ) -> None:
        """Update a feedback entry in the database."""
        from sqlalchemy import update

        async def _do_update(s: AsyncSession) -> None:
            await s.execute(
                update(FeedbackModel)
                .where(FeedbackModel.id == entry.id)
                .values(
                    is_processed=entry.is_processed,
                    processed_at=entry.processed_at,
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


import asyncio

# Pre-built feedback forms
AGENT_OUTPUT_FEEDBACK_FORM = FeedbackForm(
    id="agent_output_feedback",
    name="Agent Output Feedback",
    description="Provide feedback on agent-generated output",
    feedback_type=FeedbackType.QUALITY_ASSESSMENT,
    category=FeedbackCategory.AGENT_OUTPUT,
    fields=[
        FeedbackFormField(
            name="accuracy",
            label="How accurate was the output?",
            field_type="rating",
            required=True,
        ),
        FeedbackFormField(
            name="completeness",
            label="How complete was the output?",
            field_type="rating",
            required=True,
        ),
        FeedbackFormField(
            name="usefulness",
            label="How useful was the output?",
            field_type="rating",
            required=True,
        ),
        FeedbackFormField(
            name="issues",
            label="What issues did you notice?",
            field_type="checkbox",
            options=["Incorrect data", "Missing information", "Poor formatting", "Other"],
        ),
    ],
)

MAPPING_FEEDBACK_FORM = FeedbackForm(
    id="mapping_feedback",
    name="Mapping Accuracy Feedback",
    description="Provide feedback on data mapping accuracy",
    feedback_type=FeedbackType.CORRECTION,
    category=FeedbackCategory.MAPPING_ACCURACY,
    fields=[
        FeedbackFormField(
            name="mapping_correct",
            label="Is the mapping correct?",
            field_type="radio",
            required=True,
            options=["Yes", "Partially", "No"],
        ),
        FeedbackFormField(
            name="correct_mapping",
            label="What should the correct mapping be?",
            field_type="textarea",
        ),
        FeedbackFormField(
            name="confidence",
            label="How confident are you in your correction?",
            field_type="select",
            options=["Very confident", "Somewhat confident", "Not sure"],
        ),
    ],
)
