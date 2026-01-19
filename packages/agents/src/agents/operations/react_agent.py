"""
Operations ReAct Agent using LangGraph's create_react_agent pattern.

This agent handles monitoring, scaling, maintenance, and incident response
with memory-aware capabilities.
"""
from typing import List, Dict, Any, Optional
import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool, BaseTool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from agent_framework.agents import MemoryAwareAgent
from orchestration.registry.agent_registry import register_agent, AgentCategory

logger = logging.getLogger(__name__)


# Operations system prompt
OPERATIONS_SYSTEM_PROMPT = """You are the Operations Agent for Open Forge, an enterprise data platform.

## Your Role
You configure and manage operational infrastructure including monitoring, scaling,
maintenance, and incident response. You ensure the platform runs reliably and efficiently.

## Capabilities
1. **Monitoring Configuration**: Set up Prometheus metrics, Grafana dashboards,
   and alerting rules for comprehensive observability.

2. **Scaling Management**: Configure auto-scaling policies, load balancers,
   and resource allocation for optimal performance.

3. **Maintenance Planning**: Create backup strategies, maintenance schedules,
   health checks, and disaster recovery plans.

4. **Incident Response**: Develop incident playbooks, escalation procedures,
   and post-mortem templates.

## Output Formats
- Prometheus configs should be valid YAML
- Grafana dashboards should be JSON (compatible with Grafana import)
- Kubernetes HPA specs should be valid YAML
- Playbooks should be structured markdown with clear steps

## Best Practices
- Set up alerts before they're needed, not after
- Design for failure - assume components will fail
- Include runbooks for common operational tasks
- Document escalation paths clearly
- Track SLOs and error budgets

## Monitoring Guidelines
- Use meaningful metric names with proper labels
- Set appropriate alert thresholds (avoid alert fatigue)
- Create dashboards that tell a story
- Include business metrics alongside technical metrics
"""


@register_agent(
    name="operations_react",
    category=AgentCategory.OPERATIONS,
    description="Operations agent using ReAct pattern for monitoring, scaling, "
                "maintenance, and incident management",
    version="1.0.0",
    required_inputs=["engagement_id"],
    output_keys=["monitoring_config", "scaling_config", "maintenance_plan", "incident_playbooks"],
    capabilities=["monitoring_setup", "scaling_config", "maintenance_planning", "incident_response"],
    dependencies=["app_builder_react"],
    is_react_agent=True,
    is_memory_aware=True,
)
class OperationsReActAgent(MemoryAwareAgent):
    """
    Operations agent using LangGraph's ReAct pattern with memory capabilities.

    This agent combines:
    - ReAct pattern for systematic operational setup
    - Memory tools for persisting configurations
    - Specialized tools for monitoring, scaling, and incident management

    Example:
        agent = OperationsReActAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="operations_1"
        )

        result = await agent.run(
            "Set up monitoring for the order processing service",
            thread_id="setup_monitoring_1"
        )
    """

    def get_tools(self) -> List[BaseTool]:
        """
        Get operations-specific tools.

        Returns:
            List of tools for monitoring, scaling, and incident management
        """
        engagement_id = self.engagement_id
        store = self.store

        @tool
        async def configure_prometheus_metrics(
            service_name: str,
            metric_definitions: str,
            scrape_interval: str = "15s",
        ) -> str:
            """
            Configure Prometheus metrics for a service.

            Use this to define what metrics should be collected from a service.

            Args:
                service_name: Name of the service to monitor
                metric_definitions: JSON array of metric definitions
                    e.g., '[{"name": "requests_total", "type": "counter", "help": "Total requests"}]'
                scrape_interval: How often to scrape metrics (default: 15s)

            Returns:
                Generated Prometheus configuration
            """
            import uuid

            try:
                metrics = json.loads(metric_definitions) if isinstance(metric_definitions, str) else metric_definitions
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in metric_definitions: {e}"

            prometheus_config = {
                "service_name": service_name,
                "scrape_interval": scrape_interval,
                "metrics": metrics,
            }

            # Generate prometheus.yml snippet
            prom_yaml = f"""# Prometheus scrape config for {service_name}
- job_name: '{service_name}'
  scrape_interval: {scrape_interval}
  static_configs:
    - targets: ['{service_name}:9090']
  relabel_configs:
    - source_labels: [__address__]
      target_label: instance
      regex: '([^:]+):.*'
      replacement: '$1'
"""

            prometheus_config["prometheus_yaml"] = prom_yaml

            namespace = ("engagements", engagement_id, "monitoring_config")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": prometheus_config,
                        "search_text": f"prometheus metrics {service_name} monitoring",
                    }
                )
                logger.info(f"Configured Prometheus metrics for: {service_name}")
                return f"Configured Prometheus metrics for {service_name} with {len(metrics)} metrics (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing prometheus config: {e}")
                return f"Error storing prometheus config: {str(e)}"

        @tool
        async def create_alerting_rule(
            alert_name: str,
            service_name: str,
            expression: str,
            duration: str,
            severity: str,
            summary: str,
            description: str,
            runbook_url: str = "",
        ) -> str:
            """
            Create a Prometheus alerting rule.

            Use this to define alerts that should fire when conditions are met.

            Args:
                alert_name: Name of the alert (PascalCase)
                service_name: Service this alert is for
                expression: PromQL expression that triggers the alert
                duration: How long condition must be true (e.g., "5m")
                severity: Alert severity (critical, warning, info)
                summary: Short summary of the alert
                description: Detailed description with context
                runbook_url: Optional link to runbook for resolution

            Returns:
                Generated alerting rule configuration
            """
            import uuid

            alert_rule = {
                "alert_name": alert_name,
                "service_name": service_name,
                "expr": expression,
                "for": duration,
                "severity": severity,
                "summary": summary,
                "description": description,
                "runbook_url": runbook_url,
            }

            # Generate alert rule YAML
            alert_yaml = f"""# Alert rule: {alert_name}
- alert: {alert_name}
  expr: {expression}
  for: {duration}
  labels:
    severity: {severity}
    service: {service_name}
  annotations:
    summary: "{summary}"
    description: "{description}"
"""
            if runbook_url:
                alert_yaml += f'    runbook_url: "{runbook_url}"\n'

            alert_rule["alert_yaml"] = alert_yaml

            namespace = ("engagements", engagement_id, "alerting_rule")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": alert_rule,
                        "search_text": f"alert {alert_name} {service_name} {severity}",
                    }
                )
                logger.info(f"Created alerting rule: {alert_name}")
                return f"Created alerting rule: {alert_name} ({severity}) for {service_name} (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing alert rule: {e}")
                return f"Error storing alert rule: {str(e)}"

        @tool
        async def configure_autoscaling(
            deployment_name: str,
            namespace: str,
            min_replicas: int,
            max_replicas: int,
            target_cpu_percent: int = 70,
            target_memory_percent: int = 80,
            scale_up_cooldown: str = "60s",
            scale_down_cooldown: str = "300s",
        ) -> str:
            """
            Configure Kubernetes Horizontal Pod Autoscaler.

            Use this to set up auto-scaling for deployments based on resource usage.

            Args:
                deployment_name: Name of the deployment to scale
                namespace: Kubernetes namespace
                min_replicas: Minimum number of replicas
                max_replicas: Maximum number of replicas
                target_cpu_percent: Target CPU utilization percentage
                target_memory_percent: Target memory utilization percentage
                scale_up_cooldown: Time to wait before scaling up again
                scale_down_cooldown: Time to wait before scaling down again

            Returns:
                Generated HPA configuration
            """
            import uuid

            hpa_config = {
                "deployment_name": deployment_name,
                "namespace": namespace,
                "min_replicas": min_replicas,
                "max_replicas": max_replicas,
                "target_cpu_percent": target_cpu_percent,
                "target_memory_percent": target_memory_percent,
                "cooldowns": {
                    "scale_up": scale_up_cooldown,
                    "scale_down": scale_down_cooldown,
                },
            }

            # Generate HPA YAML
            hpa_yaml = f"""apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: {deployment_name}-hpa
  namespace: {namespace}
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: {deployment_name}
  minReplicas: {min_replicas}
  maxReplicas: {max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {target_cpu_percent}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {target_memory_percent}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: {int(scale_up_cooldown.replace('s', ''))}
      policies:
      - type: Percent
        value: 100
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: {int(scale_down_cooldown.replace('s', ''))}
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
"""

            hpa_config["hpa_yaml"] = hpa_yaml

            namespace_store = ("engagements", engagement_id, "scaling_config")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace_store,
                    key,
                    {
                        "content": hpa_config,
                        "search_text": f"autoscaling hpa {deployment_name} kubernetes",
                    }
                )
                logger.info(f"Configured autoscaling for: {deployment_name}")
                return f"Configured autoscaling for {deployment_name}: {min_replicas}-{max_replicas} replicas (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing HPA config: {e}")
                return f"Error storing HPA config: {str(e)}"

        @tool
        async def create_backup_strategy(
            resource_name: str,
            resource_type: str,
            backup_schedule: str,
            retention_days: int,
            backup_location: str,
            encryption_enabled: bool = True,
        ) -> str:
            """
            Create a backup strategy for a resource.

            Use this to define backup policies for databases, volumes, or other stateful resources.

            Args:
                resource_name: Name of the resource to back up
                resource_type: Type of resource (database, volume, config)
                backup_schedule: Cron schedule for backups (e.g., "0 2 * * *" for 2am daily)
                retention_days: Number of days to retain backups
                backup_location: Where to store backups (e.g., "s3://backups/...")
                encryption_enabled: Whether to encrypt backups

            Returns:
                Generated backup strategy configuration
            """
            import uuid

            strategy = {
                "resource_name": resource_name,
                "resource_type": resource_type,
                "schedule": backup_schedule,
                "retention_days": retention_days,
                "location": backup_location,
                "encryption": encryption_enabled,
            }

            namespace = ("engagements", engagement_id, "backup_strategy")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": strategy,
                        "search_text": f"backup {resource_name} {resource_type} strategy",
                    }
                )
                logger.info(f"Created backup strategy for: {resource_name}")
                return f"Created backup strategy for {resource_name}: schedule={backup_schedule}, retention={retention_days} days (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing backup strategy: {e}")
                return f"Error storing backup strategy: {str(e)}"

        @tool
        async def create_incident_playbook(
            playbook_name: str,
            incident_type: str,
            severity: str,
            detection_steps: str,
            investigation_steps: str,
            mitigation_steps: str,
            escalation_contacts: str,
            recovery_steps: str,
        ) -> str:
            """
            Create an incident response playbook.

            Use this to document how to respond to specific types of incidents.

            Args:
                playbook_name: Name of the playbook
                incident_type: Type of incident (outage, degradation, security, data_issue)
                severity: Severity level (p1, p2, p3, p4)
                detection_steps: How to confirm the incident (JSON array of steps)
                investigation_steps: How to investigate root cause (JSON array of steps)
                mitigation_steps: How to mitigate impact (JSON array of steps)
                escalation_contacts: Who to escalate to (JSON array)
                recovery_steps: How to fully recover (JSON array of steps)

            Returns:
                Generated incident playbook
            """
            import uuid

            try:
                detection = json.loads(detection_steps) if isinstance(detection_steps, str) else detection_steps
                investigation = json.loads(investigation_steps) if isinstance(investigation_steps, str) else investigation_steps
                mitigation = json.loads(mitigation_steps) if isinstance(mitigation_steps, str) else mitigation_steps
                contacts = json.loads(escalation_contacts) if isinstance(escalation_contacts, str) else escalation_contacts
                recovery = json.loads(recovery_steps) if isinstance(recovery_steps, str) else recovery_steps
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            playbook = {
                "name": playbook_name,
                "incident_type": incident_type,
                "severity": severity,
                "detection": detection,
                "investigation": investigation,
                "mitigation": mitigation,
                "escalation_contacts": contacts,
                "recovery": recovery,
            }

            # Generate markdown playbook
            playbook_md = f"""# {playbook_name}

**Incident Type:** {incident_type}
**Severity:** {severity}

## Detection

{chr(10).join(f"- {step}" for step in detection)}

## Investigation

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(investigation))}

## Mitigation

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(mitigation))}

## Escalation Contacts

{chr(10).join(f"- {contact}" for contact in contacts)}

## Recovery

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(recovery))}

## Post-Incident

- Document timeline of events
- Complete post-mortem within 48 hours
- Update this playbook with lessons learned
"""

            playbook["playbook_md"] = playbook_md

            namespace = ("engagements", engagement_id, "incident_playbook")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": playbook,
                        "search_text": f"incident playbook {playbook_name} {incident_type} {severity}",
                    }
                )
                logger.info(f"Created incident playbook: {playbook_name}")
                return f"Created incident playbook: {playbook_name} ({incident_type}, {severity}) (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing playbook: {e}")
                return f"Error storing playbook: {str(e)}"

        @tool
        async def generate_operations_summary() -> str:
            """
            Generate a summary of all operations configurations.

            Use this to compile a comprehensive summary of monitoring,
            scaling, backup, and incident response configurations.

            Returns:
                Complete operations configuration summary
            """
            summary_parts = ["# Operations Configuration Summary\n"]

            # Get monitoring configs
            try:
                namespace = ("engagements", engagement_id, "monitoring_config")
                configs = await store.alist(namespace=namespace, limit=50)
                if configs:
                    summary_parts.append("## Monitoring Configurations")
                    for item in configs:
                        content = item.value.get("content", {})
                        summary_parts.append(f"- **{content.get('service_name')}** (scrape: {content.get('scrape_interval')})")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting monitoring configs: {e}")

            # Get alerting rules
            try:
                namespace = ("engagements", engagement_id, "alerting_rule")
                rules = await store.alist(namespace=namespace, limit=50)
                if rules:
                    summary_parts.append("## Alerting Rules")
                    for item in rules:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('alert_name')}** [{content.get('severity')}] - {content.get('service_name')}"
                        )
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting alerting rules: {e}")

            # Get scaling configs
            try:
                namespace = ("engagements", engagement_id, "scaling_config")
                scaling = await store.alist(namespace=namespace, limit=50)
                if scaling:
                    summary_parts.append("## Auto-Scaling Configurations")
                    for item in scaling:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('deployment_name')}**: {content.get('min_replicas')}-{content.get('max_replicas')} replicas"
                        )
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting scaling configs: {e}")

            # Get backup strategies
            try:
                namespace = ("engagements", engagement_id, "backup_strategy")
                backups = await store.alist(namespace=namespace, limit=50)
                if backups:
                    summary_parts.append("## Backup Strategies")
                    for item in backups:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('resource_name')}** ({content.get('resource_type')}): {content.get('schedule')}"
                        )
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting backup strategies: {e}")

            # Get incident playbooks
            try:
                namespace = ("engagements", engagement_id, "incident_playbook")
                playbooks = await store.alist(namespace=namespace, limit=50)
                if playbooks:
                    summary_parts.append("## Incident Playbooks")
                    for item in playbooks:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('name')}** [{content.get('severity')}] - {content.get('incident_type')}"
                        )
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting playbooks: {e}")

            if len(summary_parts) == 1:
                return "No operations configurations created yet."

            return "\n".join(summary_parts)

        return [
            configure_prometheus_metrics,
            create_alerting_rule,
            configure_autoscaling,
            create_backup_strategy,
            create_incident_playbook,
            generate_operations_summary,
        ]

    def get_system_prompt(self) -> str:
        """Get the operations agent system prompt."""
        return OPERATIONS_SYSTEM_PROMPT


# Factory function for easier instantiation
def create_operations_react_agent(
    llm: BaseChatModel,
    checkpointer: PostgresSaver,
    store: PostgresStore,
    engagement_id: str,
    agent_id: str = "operations_react",
) -> OperationsReActAgent:
    """
    Create a configured Operations ReAct agent.

    Args:
        llm: The language model to use
        checkpointer: PostgresSaver for thread checkpoints
        store: PostgresStore for long-term memory
        engagement_id: The engagement this agent operates within
        agent_id: Optional custom agent ID

    Returns:
        Configured OperationsReActAgent instance
    """
    return OperationsReActAgent(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        engagement_id=engagement_id,
        agent_id=agent_id,
    )
