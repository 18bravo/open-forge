"""
Forge Data Quality Module

Provides data health checks (freshness, completeness, schema validation),
monitors, and alerting capabilities.
"""

from forge_data.quality.checks import (
    CheckResult,
    CheckSeverity,
    QualityCheck,
    FreshnessCheck,
    CompletenessCheck,
    SchemaCheck,
)
from forge_data.quality.monitors import QualityMonitor, MonitorSchedule
from forge_data.quality.alerting import AlertChannel, AlertConfig, AlertDispatcher

__all__ = [
    # Checks
    "QualityCheck",
    "CheckResult",
    "CheckSeverity",
    "FreshnessCheck",
    "CompletenessCheck",
    "SchemaCheck",
    # Monitors
    "QualityMonitor",
    "MonitorSchedule",
    # Alerting
    "AlertChannel",
    "AlertConfig",
    "AlertDispatcher",
]
