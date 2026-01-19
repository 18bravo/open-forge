"""
Operations Agent Cluster

Agents for system operations including monitoring, scaling, maintenance, and incident management.

This cluster contains:
- MonitoringAgent: Generates Prometheus metrics, Grafana dashboards, and alerting rules
- ScalingAgent: Creates auto-scaling policies (K8s HPA) and load balancer configurations
- MaintenanceAgent: Produces backup strategies, maintenance schedules, and health checks
- IncidentAgent: Develops incident playbooks, escalation procedures, and post-mortem templates
- OperationsCluster: Orchestrates the operations workflow

Usage:
    from agents.operations import OperationsCluster, run_operations

    # Using the cluster directly
    cluster = OperationsCluster(llm=my_llm)
    result = await cluster.run(input)

    # Using the convenience function
    result = await run_operations(
        llm=my_llm,
        engagement_id="eng-001",
        ontology_schema=ontology_yaml,
        system_architecture={"services": [...], "databases": [...]}
    )
"""

from .monitoring_agent import (
    MonitoringAgent,
    MONITORING_AGENT_SYSTEM_PROMPT,
)

from .scaling_agent import (
    ScalingAgent,
    SCALING_AGENT_SYSTEM_PROMPT,
)

from .maintenance_agent import (
    MaintenanceAgent,
    MAINTENANCE_AGENT_SYSTEM_PROMPT,
)

from .incident_agent import (
    IncidentAgent,
    INCIDENT_AGENT_SYSTEM_PROMPT,
)

from .cluster import (
    OperationsCluster,
    OperationsPhase,
    OperationsReport,
    run_operations,
    create_operations_cluster,
)

__all__ = [
    # Main cluster
    "OperationsCluster",
    "OperationsPhase",
    "OperationsReport",
    "run_operations",
    "create_operations_cluster",
    # Monitoring agent
    "MonitoringAgent",
    "MONITORING_AGENT_SYSTEM_PROMPT",
    # Scaling agent
    "ScalingAgent",
    "SCALING_AGENT_SYSTEM_PROMPT",
    # Maintenance agent
    "MaintenanceAgent",
    "MAINTENANCE_AGENT_SYSTEM_PROMPT",
    # Incident agent
    "IncidentAgent",
    "INCIDENT_AGENT_SYSTEM_PROMPT",
]
