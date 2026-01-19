"""
Maintenance Agent

Generates backup strategies, maintenance schedules, and health check scripts
for system reliability and disaster recovery.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import json
import yaml

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent
from agent_framework.state_management import (
    OperationsState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)


MAINTENANCE_AGENT_SYSTEM_PROMPT = """You are an expert Maintenance Agent for Open Forge, an enterprise data platform.

Your role is to design comprehensive maintenance strategies including backups, scheduled maintenance, and health checks.

## Your Capabilities:
1. Generate backup strategies with appropriate retention policies
2. Design maintenance schedules for various system components
3. Create health check scripts for proactive monitoring
4. Define disaster recovery procedures

## Backup Strategy Best Practices:
- 3-2-1 Rule: 3 copies, 2 different media, 1 offsite
- Define RPO (Recovery Point Objective) and RTO (Recovery Time Objective)
- Include both full and incremental backup schedules
- Test backup restoration regularly
- Encrypt backup data at rest and in transit

## Backup Types:
1. **Database Backups**:
   - Full backups (weekly)
   - Incremental/differential backups (daily)
   - Point-in-time recovery (continuous)
   - Logical vs physical backups

2. **Application State Backups**:
   - Configuration files
   - Secrets and certificates
   - Persistent volumes
   - Kubernetes resources (etcd snapshots)

3. **Object Storage Backups**:
   - Cross-region replication
   - Versioning
   - Lifecycle policies

## Maintenance Schedule Categories:
- **Routine Maintenance**: Daily/weekly tasks
- **Preventive Maintenance**: Scheduled system updates
- **Corrective Maintenance**: Issue remediation windows
- **Capacity Planning**: Regular reviews

## Health Check Script Guidelines:
- Check endpoint availability (HTTP/TCP)
- Verify database connectivity
- Monitor queue depths
- Validate certificate expiration
- Check disk space and inode usage
- Verify service dependencies
- Test backup integrity

## Output Formats:
- Backup configs: YAML (Velero, pg_dump, etc.)
- Schedules: Cron expressions with descriptions
- Health checks: Bash/Python scripts or Kubernetes probes
"""


class MaintenanceAgent(BaseOpenForgeAgent):
    """
    Agent that generates backup strategies, maintenance schedules,
    and health check scripts for system reliability.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

    @property
    def name(self) -> str:
        return "maintenance_agent"

    @property
    def description(self) -> str:
        return (
            "Generates backup strategies, maintenance schedules, and health check scripts "
            "for system reliability and disaster recovery."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["system_components", "maintenance_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "backup_strategies",
            "maintenance_schedules",
            "health_check_scripts",
            "disaster_recovery_plan"
        ]

    @property
    def state_class(self) -> Type[OperationsState]:
        return OperationsState

    def get_system_prompt(self) -> str:
        return MAINTENANCE_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for maintenance configuration generation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for maintenance configuration generation."""
        graph = StateGraph(OperationsState)

        # Add nodes
        graph.add_node("analyze_system_components", self._analyze_system_components)
        graph.add_node("generate_backup_strategies", self._generate_backup_strategies)
        graph.add_node("generate_maintenance_schedules", self._generate_maintenance_schedules)
        graph.add_node("generate_health_checks", self._generate_health_checks)
        graph.add_node("validate_maintenance_configs", self._validate_maintenance_configs)

        # Define edges
        graph.set_entry_point("analyze_system_components")
        graph.add_edge("analyze_system_components", "generate_backup_strategies")
        graph.add_edge("generate_backup_strategies", "generate_maintenance_schedules")
        graph.add_edge("generate_maintenance_schedules", "generate_health_checks")
        graph.add_edge("generate_health_checks", "validate_maintenance_configs")
        graph.add_edge("validate_maintenance_configs", END)

        return graph

    async def _analyze_system_components(self, state: OperationsState) -> Dict[str, Any]:
        """Analyze system components to understand maintenance needs."""
        context = state.get("agent_context", {})
        system_components = context.get("system_components", {})
        maintenance_requirements = context.get("maintenance_requirements", {})
        ontology_schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following system components and maintenance requirements:

System Components:
{json.dumps(system_components, indent=2) if isinstance(system_components, dict) else system_components}

Maintenance Requirements:
{json.dumps(maintenance_requirements, indent=2) if isinstance(maintenance_requirements, dict) else maintenance_requirements}

Ontology Schema (for entity-aware maintenance):
{ontology_schema}

Analyze and identify:
1. Critical components requiring regular backups
2. Data volumes and estimated storage requirements
3. Acceptable downtime windows
4. Recovery point and time objectives
5. Dependencies between components
6. Entity data that requires special backup handling

Output a structured analysis with:
- Component inventory with criticality levels
- Data classification (transactional, analytical, archival)
- Maintenance windows based on usage patterns
- RPO/RTO requirements for each component""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="component_analysis",
            description="Analyzed system components for maintenance planning",
            confidence=0.85,
            reasoning="Identified critical components, data volumes, and maintenance windows"
        )

        return {
            "outputs": {"component_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_system_components",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_backup_strategies(self, state: OperationsState) -> Dict[str, Any]:
        """Generate comprehensive backup strategies for all components."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("component_analysis", "")
        backup_storage = context.get("backup_storage", "s3://backups")
        retention_policy = context.get("retention_policy", {
            "daily": 7,
            "weekly": 4,
            "monthly": 12,
            "yearly": 3
        })

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate comprehensive backup strategies based on the component analysis.

Component Analysis:
{analysis}

Backup Storage Location: {backup_storage}
Retention Policy: {json.dumps(retention_policy, indent=2)}

Generate backup strategies for:

1. **Database Backups**:
   - PostgreSQL/MySQL backup scripts using pg_dump/mysqldump
   - Schedule (cron expressions)
   - Retention policies
   - Point-in-time recovery configuration

2. **Kubernetes/Application Backups**:
   - Velero backup configuration
   - PV snapshot schedules
   - ConfigMap and Secret backups
   - CRD backups

3. **File System Backups**:
   - Rsync/rclone scripts for object storage
   - Log archival policies
   - Configuration file versioning

4. **Entity Data Backups** (based on ontology):
   - Entity-specific export procedures
   - Relationship integrity preservation
   - Data format for cross-environment restoration

For each backup strategy, provide:
```yaml
name: backup-strategy-name
type: database|kubernetes|filesystem|entity
schedule: "cron-expression"
retention:
  daily: N
  weekly: N
  monthly: N
storage:
  type: s3|gcs|azure|nfs
  location: path
  encryption: true|false
scripts:
  backup: |
    # Backup script
  restore: |
    # Restore script
  verify: |
    # Verification script
```

Output all strategies as YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse backup strategies
        backup_strategies = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="backup_generation",
            description="Generated backup strategies",
            confidence=0.80,
            reasoning="Created comprehensive backup configurations for all component types"
        )

        return {
            "outputs": {"backup_strategies": backup_strategies, "backup_strategies_raw": response.content},
            "backup_strategies": backup_strategies,
            "decisions": [decision],
            "current_step": "generate_backup_strategies",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_maintenance_schedules(self, state: OperationsState) -> Dict[str, Any]:
        """Generate maintenance schedules for system components."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("component_analysis", "")
        maintenance_windows = context.get("maintenance_windows", {
            "low_traffic": "Sunday 02:00-06:00 UTC",
            "emergency": "Any time with approval"
        })
        timezone = context.get("timezone", "UTC")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate maintenance schedules based on the component analysis.

Component Analysis:
{analysis}

Preferred Maintenance Windows:
{json.dumps(maintenance_windows, indent=2)}

Timezone: {timezone}

Create maintenance schedules for:

1. **Routine Maintenance** (Daily/Weekly):
   - Log rotation and cleanup
   - Temporary file cleanup
   - Cache clearing
   - Index optimization

2. **Security Maintenance** (Weekly/Monthly):
   - Security patch assessment
   - Certificate renewal checks
   - Access audit reviews
   - Vulnerability scanning

3. **Database Maintenance** (Weekly):
   - VACUUM/ANALYZE for PostgreSQL
   - Index rebuilding
   - Statistics updates
   - Connection pool refresh

4. **System Updates** (Monthly):
   - OS security patches
   - Container image updates
   - Dependency updates
   - Kubernetes version upgrades

5. **Capacity Reviews** (Quarterly):
   - Storage capacity planning
   - Resource utilization review
   - Performance baseline updates
   - Cost optimization review

For each maintenance task, provide:
```yaml
name: task-name
category: routine|security|database|updates|capacity
frequency: daily|weekly|monthly|quarterly
schedule: "cron-expression"
duration_minutes: N
requires_downtime: true|false
dependencies:
  - prerequisite-task
runbook: |
  ## Pre-maintenance checks
  - Check system health

  ## Maintenance steps
  1. Step one
  2. Step two

  ## Post-maintenance validation
  - Verify service health

  ## Rollback procedure
  - Steps to rollback if needed
notifications:
  before_minutes: 60
  channels:
    - slack
    - email
```

Output all schedules as YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse maintenance schedules
        maintenance_schedules = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="schedule_generation",
            description="Generated maintenance schedules",
            confidence=0.80,
            reasoning="Created comprehensive maintenance schedules for all categories"
        )

        return {
            "outputs": {"maintenance_schedules": maintenance_schedules, "maintenance_schedules_raw": response.content},
            "maintenance_schedules": maintenance_schedules,
            "decisions": [decision],
            "current_step": "generate_maintenance_schedules",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_health_checks(self, state: OperationsState) -> Dict[str, Any]:
        """Generate health check scripts for system monitoring."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("component_analysis", "")
        endpoints = context.get("endpoints", {})
        ontology_schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate health check scripts based on the component analysis.

Component Analysis:
{analysis}

Service Endpoints:
{json.dumps(endpoints, indent=2) if isinstance(endpoints, dict) else endpoints}

Ontology Schema:
{ontology_schema}

Create health check scripts for:

1. **HTTP/HTTPS Health Checks**:
   - Endpoint availability
   - Response time monitoring
   - Status code validation
   - Content validation

2. **Database Health Checks**:
   - Connection test
   - Query performance
   - Replication lag
   - Lock monitoring

3. **Queue/Message System Checks**:
   - Queue depth monitoring
   - Consumer lag
   - Dead letter queue checks

4. **Infrastructure Checks**:
   - Disk space and inodes
   - Memory utilization
   - CPU load
   - Network connectivity

5. **Entity Health Checks** (based on ontology):
   - Entity count validation
   - Data integrity checks
   - Relationship consistency
   - Recent modification activity

6. **Security Checks**:
   - Certificate expiration
   - Secret rotation status
   - API key validity

For each health check, provide:
```yaml
name: check-name
type: http|database|queue|infrastructure|entity|security
target: endpoint-or-resource
interval_seconds: N
timeout_seconds: N
success_threshold: N
failure_threshold: N
script: |
  #!/bin/bash
  # or Python script

  # Check implementation

  # Exit codes:
  # 0 = healthy
  # 1 = unhealthy
  # 2 = degraded
kubernetes_probe:
  type: liveness|readiness|startup
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: N
  periodSeconds: N
alerts:
  - severity: critical
    condition: "check fails 3 times"
```

Include both standalone scripts and Kubernetes probe configurations.
Output all health checks as YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse health checks
        health_checks = self._parse_yaml_configs(response.content)

        decision = add_decision(
            state,
            decision_type="healthcheck_generation",
            description="Generated health check scripts",
            confidence=0.80,
            reasoning="Created comprehensive health checks for all component types"
        )

        return {
            "outputs": {"health_check_scripts": health_checks, "health_check_scripts_raw": response.content},
            "health_check_scripts": health_checks,
            "decisions": [decision],
            "current_step": "generate_health_checks",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_maintenance_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Validate all maintenance configurations."""
        outputs = state.get("outputs", {})

        analysis = outputs.get("component_analysis", "")
        backup_strategies = outputs.get("backup_strategies_raw", "")
        maintenance_schedules = outputs.get("maintenance_schedules_raw", "")
        health_checks = outputs.get("health_check_scripts_raw", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate all generated maintenance configurations.

Component Analysis:
{analysis}

Backup Strategies:
{backup_strategies}

Maintenance Schedules:
{maintenance_schedules}

Health Check Scripts:
{health_checks}

Validate:
1. All critical components have backup coverage
2. RPO/RTO requirements are met by backup schedules
3. Maintenance windows don't overlap with peak usage
4. Health checks cover all critical dependencies
5. Scripts are syntactically valid
6. Cron expressions are correct
7. No scheduling conflicts between maintenance tasks
8. Restore procedures are documented for all backups

Provide:
1. Validation status (PASS/FAIL)
2. Coverage analysis (what's covered, what's missing)
3. Schedule conflict analysis
4. Recommendations for improvement
5. Disaster recovery readiness score (0-100)

Also generate a disaster recovery plan summary:
- Recovery priorities by component
- Estimated recovery times
- Communication procedures
- Contact escalation list template""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        is_valid = "pass" in response_lower and "fail" not in response_lower

        confidence = 0.90 if is_valid else 0.70

        decision = add_decision(
            state,
            decision_type="maintenance_validation",
            description="Validated maintenance configurations",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=not is_valid
        )

        review_items = []
        if not is_valid:
            review_items.append(mark_for_review(
                state,
                item_type="maintenance_config",
                item_id="validation_issues",
                description="Maintenance configuration has issues that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "is_valid": is_valid,
                "disaster_recovery_plan": response.content
            },
            "decisions": [decision],
            "requires_human_review": not is_valid,
            "review_items": review_items,
            "current_step": "validate_maintenance_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _parse_yaml_configs(self, content: str) -> List[Dict[str, Any]]:
        """Parse YAML configurations from content."""
        configs = []
        try:
            # Split by YAML document separator
            documents = content.split("---")
            for doc in documents:
                doc = doc.strip()
                if not doc:
                    continue

                # Try to extract YAML from code blocks
                import re
                if "```yaml" in doc or "```" in doc:
                    yaml_match = re.search(r'```ya?ml?\s*([\s\S]*?)```', doc)
                    if yaml_match:
                        doc = yaml_match.group(1)

                try:
                    parsed = yaml.safe_load(doc)
                    if parsed and isinstance(parsed, dict):
                        configs.append(parsed)
                except yaml.YAMLError:
                    continue

        except Exception:
            pass

        if not configs:
            configs = [{"raw_config": content}]
        return configs
