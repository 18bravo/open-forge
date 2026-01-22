"""
Quality monitoring infrastructure.

Provides scheduling and execution of quality checks with result tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Literal

from pydantic import BaseModel, Field


class ScheduleType(str, Enum):
    """Type of monitor schedule."""

    CRON = "cron"
    INTERVAL = "interval"
    ON_CHANGE = "on_change"


class MonitorSchedule(BaseModel):
    """Schedule configuration for a quality monitor."""

    type: ScheduleType
    cron: str | None = None  # For cron type, e.g., "0 * * * *"
    interval_minutes: int | None = None  # For interval type


class AlertConfig(BaseModel):
    """Alert configuration for a monitor."""

    channels: list[str] = Field(default_factory=list)  # ["slack", "email", "pagerduty"]
    severity_threshold: str = "warning"
    notify_on_recovery: bool = True


class QualityMonitor(BaseModel):
    """
    A quality monitor that runs checks on a schedule.

    Monitors group related checks together and handle scheduling,
    execution, and alerting.
    """

    id: str
    name: str
    description: str | None = None
    dataset_id: str
    checks: list[dict[str, Any]]  # Check configurations
    schedule: MonitorSchedule
    alerting: AlertConfig | None = None
    enabled: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # SLA configuration
    sla_target_percentage: float | None = None  # e.g., 99.5
    sla_window_days: int = 30


class MonitorRun(BaseModel):
    """Record of a monitor execution."""

    id: str
    monitor_id: str
    started_at: datetime
    completed_at: datetime | None = None
    status: Literal["running", "completed", "failed"] = "running"
    check_results: list[dict[str, Any]] = Field(default_factory=list)
    error_message: str | None = None


class MonitorRunner:
    """
    Executes quality monitors and manages results.

    This is a stub implementation. Full implementation would integrate
    with the check registry, data context, and result storage.
    """

    def __init__(
        self,
        check_registry: Any = None,
        alert_dispatcher: Any = None,
        result_store: Any = None,
    ):
        """
        Initialize the monitor runner.

        Args:
            check_registry: Registry for instantiating checks from config
            alert_dispatcher: Dispatcher for sending alerts
            result_store: Storage for check results
        """
        self.check_registry = check_registry
        self.alert_dispatcher = alert_dispatcher
        self.result_store = result_store

    async def run_monitor(
        self,
        monitor: QualityMonitor,
        data_context: Any,
    ) -> MonitorRun:
        """
        Execute all checks in a monitor.

        Args:
            monitor: The monitor to execute
            data_context: Context providing data access

        Returns:
            MonitorRun with results

        Note: This is a stub. Full implementation would:
        1. Instantiate checks from monitor.checks config
        2. Execute checks concurrently with timeout
        3. Store results
        4. Send alerts for failures
        """
        run = MonitorRun(
            id=f"run-{monitor.id}-{datetime.utcnow().isoformat()}",
            monitor_id=monitor.id,
            started_at=datetime.utcnow(),
        )

        # Stub: In full implementation, would execute checks here
        run.completed_at = datetime.utcnow()
        run.status = "completed"

        return run
