"""
Monitoring Agent

Generates Prometheus metrics configurations, Grafana dashboards,
and alerting rules based on ontology entities and system requirements.
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


MONITORING_AGENT_SYSTEM_PROMPT = """You are an expert Monitoring Agent for Open Forge, an enterprise data platform.

Your role is to design comprehensive monitoring configurations based on system ontology and operational requirements.

## Your Capabilities:
1. Generate Prometheus metrics configurations with appropriate metric types (counters, gauges, histograms, summaries)
2. Create Grafana dashboard JSON definitions with relevant panels and visualizations
3. Design alerting rules with appropriate thresholds and severity levels
4. Map ontology entities to entity-specific metrics for domain-aware monitoring

## Prometheus Configuration Best Practices:
- Use meaningful metric names following the pattern: `<namespace>_<subsystem>_<name>_<unit>`
- Include appropriate labels for filtering and aggregation
- Define scrape configs with proper intervals
- Set up recording rules for frequently queried expressions

## Grafana Dashboard Standards:
- Organize panels logically by subsystem or entity type
- Include overview panels with key metrics
- Use appropriate visualization types (time series, stat panels, tables, heatmaps)
- Add templating variables for dynamic filtering
- Include annotations for deployments and incidents

## Alerting Rule Guidelines:
- Define clear severity levels: critical, warning, info
- Include meaningful annotations with runbook links
- Set appropriate evaluation intervals
- Use recording rules for complex alert expressions
- Implement alert grouping and routing

## Entity-Based Monitoring:
- Map ontology entities to domain-specific metrics
- Create entity lifecycle metrics (created, updated, deleted counts)
- Track entity relationship health
- Monitor data quality metrics per entity type

Always output configurations in valid YAML (for Prometheus) and JSON (for Grafana) formats.
Include documentation comments explaining the purpose of each configuration section.
"""


class MonitoringAgent(BaseOpenForgeAgent):
    """
    Agent that generates monitoring configurations including Prometheus metrics,
    Grafana dashboards, and alerting rules based on ontology and requirements.
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
        return "monitoring_agent"

    @property
    def description(self) -> str:
        return (
            "Generates Prometheus metrics configurations, Grafana dashboards, "
            "and alerting rules based on ontology entities and system requirements."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "system_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "prometheus_config",
            "grafana_dashboards",
            "alerting_rules",
            "entity_metrics_map"
        ]

    @property
    def state_class(self) -> Type[OperationsState]:
        return OperationsState

    def get_system_prompt(self) -> str:
        return MONITORING_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for monitoring configuration generation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for monitoring configuration generation."""
        graph = StateGraph(OperationsState)

        # Add nodes
        graph.add_node("analyze_ontology", self._analyze_ontology)
        graph.add_node("generate_prometheus_config", self._generate_prometheus_config)
        graph.add_node("generate_grafana_dashboards", self._generate_grafana_dashboards)
        graph.add_node("generate_alerting_rules", self._generate_alerting_rules)
        graph.add_node("validate_configs", self._validate_configs)

        # Define edges
        graph.set_entry_point("analyze_ontology")
        graph.add_edge("analyze_ontology", "generate_prometheus_config")
        graph.add_edge("generate_prometheus_config", "generate_grafana_dashboards")
        graph.add_edge("generate_grafana_dashboards", "generate_alerting_rules")
        graph.add_edge("generate_alerting_rules", "validate_configs")
        graph.add_edge("validate_configs", END)

        return graph

    async def _analyze_ontology(self, state: OperationsState) -> Dict[str, Any]:
        """Analyze ontology to identify entities and relationships for monitoring."""
        context = state.get("agent_context", {})
        ontology_schema = context.get("ontology_schema", "")
        system_requirements = context.get("system_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following ontology schema and system requirements to identify monitoring needs:

Ontology Schema:
{ontology_schema}

System Requirements:
{json.dumps(system_requirements, indent=2) if isinstance(system_requirements, dict) else system_requirements}

Identify:
1. Entity types that need monitoring (with their key attributes)
2. Relationships that should be tracked
3. Critical operations and workflows to monitor
4. Key performance indicators (KPIs) for each entity type
5. Data quality dimensions to track

Output a structured analysis with specific monitoring recommendations for each entity.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="ontology_analysis",
            description="Analyzed ontology for monitoring requirements",
            confidence=0.85,
            reasoning="Identified entities, relationships, and KPIs for monitoring"
        )

        return {
            "outputs": {"ontology_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_ontology",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_prometheus_config(self, state: OperationsState) -> Dict[str, Any]:
        """Generate Prometheus metrics configuration."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("ontology_analysis", "")
        namespace = context.get("metrics_namespace", "openforge")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on the ontology analysis, generate a comprehensive Prometheus configuration.

Ontology Analysis:
{analysis}

Metrics Namespace: {namespace}

Generate:
1. Global Prometheus configuration (scrape configs, rule files)
2. Metric definitions with types (counter, gauge, histogram, summary)
3. Labels for each metric
4. Recording rules for frequently used queries
5. Entity-specific metrics based on the ontology

Output the configuration as valid YAML with the following structure:
- global: Global settings
- scrape_configs: Scrape configurations
- rule_files: Rule file references

Also provide a separate metrics_definitions section that documents each metric:
- name: Metric name
- type: counter/gauge/histogram/summary
- help: Description
- labels: List of labels
- entity_type: Associated ontology entity (if applicable)

Use namespace '{namespace}' for all metrics.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse and structure the Prometheus config
        prometheus_config = self._parse_prometheus_config(response.content)

        decision = add_decision(
            state,
            decision_type="prometheus_generation",
            description="Generated Prometheus metrics configuration",
            confidence=0.80,
            reasoning="Created metric definitions based on ontology entities"
        )

        return {
            "outputs": {"prometheus_config": prometheus_config, "prometheus_config_raw": response.content},
            "prometheus_configs": prometheus_config,
            "decisions": [decision],
            "current_step": "generate_prometheus_config",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_grafana_dashboards(self, state: OperationsState) -> Dict[str, Any]:
        """Generate Grafana dashboard JSON definitions."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("ontology_analysis", "")
        prometheus_config = outputs.get("prometheus_config_raw", "")
        dashboard_title = context.get("dashboard_title", "Open Forge Operations")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate Grafana dashboard definitions based on the Prometheus metrics.

Ontology Analysis:
{analysis}

Prometheus Metrics Configuration:
{prometheus_config}

Dashboard Title: {dashboard_title}

Create the following dashboards as JSON:

1. **Overview Dashboard**: High-level system health and KPIs
   - System health indicators
   - Request rates and latencies
   - Error rates
   - Resource utilization

2. **Entity Monitoring Dashboard**: Entity-specific metrics
   - Entity counts by type
   - Entity lifecycle events (create/update/delete rates)
   - Entity relationship health
   - Data quality metrics per entity

3. **Operations Dashboard**: Operational metrics
   - API endpoint performance
   - Database query metrics
   - Background job status
   - Integration health

For each dashboard, provide:
- Dashboard JSON with panels
- Variable templates for filtering
- Time range defaults
- Refresh intervals

Output each dashboard as a separate JSON object with the following structure:
{{
  "title": "...",
  "uid": "...",
  "panels": [...],
  "templating": {{...}},
  "time": {{...}},
  "refresh": "..."
}}""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse dashboards from response
        dashboards = self._parse_grafana_dashboards(response.content)

        decision = add_decision(
            state,
            decision_type="grafana_generation",
            description="Generated Grafana dashboard definitions",
            confidence=0.80,
            reasoning="Created dashboards for overview, entity monitoring, and operations"
        )

        return {
            "outputs": {"grafana_dashboards": dashboards, "grafana_dashboards_raw": response.content},
            "grafana_dashboards": dashboards,
            "decisions": [decision],
            "current_step": "generate_grafana_dashboards",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_alerting_rules(self, state: OperationsState) -> Dict[str, Any]:
        """Generate alerting rules for Prometheus/Alertmanager."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("ontology_analysis", "")
        prometheus_config = outputs.get("prometheus_config_raw", "")
        alert_namespace = context.get("metrics_namespace", "openforge")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate comprehensive alerting rules based on the monitoring configuration.

Ontology Analysis:
{analysis}

Prometheus Metrics Configuration:
{prometheus_config}

Alert Namespace: {alert_namespace}

Create alerting rules for:

1. **Infrastructure Alerts**:
   - High CPU/memory utilization
   - Disk space warnings
   - Network connectivity issues
   - Service availability

2. **Application Alerts**:
   - High error rates
   - Elevated latency
   - Low throughput
   - Request failures

3. **Entity-Specific Alerts**:
   - Entity processing failures
   - Data quality degradation
   - Relationship integrity violations
   - Unusual entity patterns (e.g., sudden spikes)

4. **Business Logic Alerts**:
   - SLA violations
   - Business rule failures
   - Critical workflow failures

For each alert rule, provide:
- alert: Alert name
- expr: PromQL expression
- for: Duration before firing
- labels:
    severity: critical/warning/info
    team: team responsible
- annotations:
    summary: Brief description
    description: Detailed description with template variables
    runbook_url: Link to runbook

Output as valid YAML alert rules format:
groups:
  - name: group_name
    rules:
      - alert: AlertName
        ...""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse alerting rules
        alerting_rules = self._parse_alerting_rules(response.content)

        decision = add_decision(
            state,
            decision_type="alerting_generation",
            description="Generated alerting rules",
            confidence=0.85,
            reasoning="Created infrastructure, application, entity, and business alerts"
        )

        return {
            "outputs": {"alerting_rules": alerting_rules, "alerting_rules_raw": response.content},
            "alerting_rules": alerting_rules,
            "decisions": [decision],
            "current_step": "generate_alerting_rules",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Validate all generated monitoring configurations."""
        outputs = state.get("outputs", {})

        prometheus_config = outputs.get("prometheus_config_raw", "")
        grafana_dashboards = outputs.get("grafana_dashboards_raw", "")
        alerting_rules = outputs.get("alerting_rules_raw", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the generated monitoring configurations for completeness and correctness.

Prometheus Configuration:
{prometheus_config}

Grafana Dashboards:
{grafana_dashboards}

Alerting Rules:
{alerting_rules}

Check for:
1. YAML/JSON syntax validity
2. Metric name consistency across configs
3. Dashboard panels reference existing metrics
4. Alert expressions use valid PromQL
5. Appropriate severity levels and thresholds
6. Complete coverage of identified entities
7. Missing or redundant configurations

Provide:
1. Validation status (PASS/FAIL)
2. List of any issues found
3. Recommendations for improvement
4. Entity metrics mapping summary

Also output an entity_metrics_map that maps ontology entities to their metrics:
{{
  "EntityName": {{
    "metrics": ["metric1", "metric2"],
    "dashboards": ["dashboard_uid1"],
    "alerts": ["AlertName1", "AlertName2"]
  }}
}}""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        is_valid = "pass" in response_lower and "fail" not in response_lower

        # Extract entity metrics map
        entity_metrics_map = self._extract_entity_metrics_map(response.content)

        confidence = 0.90 if is_valid else 0.70

        decision = add_decision(
            state,
            decision_type="config_validation",
            description="Validated monitoring configurations",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=not is_valid
        )

        review_items = []
        if not is_valid:
            review_items.append(mark_for_review(
                state,
                item_type="monitoring_config",
                item_id="validation_issues",
                description="Monitoring configuration has issues that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "is_valid": is_valid,
                "entity_metrics_map": entity_metrics_map
            },
            "entity_metrics_map": entity_metrics_map,
            "decisions": [decision],
            "requires_human_review": not is_valid,
            "review_items": review_items,
            "current_step": "validate_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _parse_prometheus_config(self, content: str) -> Dict[str, Any]:
        """Parse Prometheus configuration from LLM response."""
        try:
            # Try to extract YAML content
            yaml_blocks = self._extract_yaml_blocks(content)
            if yaml_blocks:
                return yaml_blocks[0] if len(yaml_blocks) == 1 else {"configs": yaml_blocks}
        except Exception:
            pass
        return {"raw_config": content}

    def _parse_grafana_dashboards(self, content: str) -> List[Dict[str, Any]]:
        """Parse Grafana dashboard JSON from LLM response."""
        dashboards = []
        try:
            json_blocks = self._extract_json_blocks(content)
            for block in json_blocks:
                if "title" in block or "panels" in block:
                    dashboards.append(block)
        except Exception:
            pass

        if not dashboards:
            dashboards = [{"raw_content": content}]
        return dashboards

    def _parse_alerting_rules(self, content: str) -> List[Dict[str, Any]]:
        """Parse alerting rules from LLM response."""
        try:
            yaml_blocks = self._extract_yaml_blocks(content)
            rules = []
            for block in yaml_blocks:
                if "groups" in block:
                    rules.extend(block.get("groups", []))
                elif "rules" in block:
                    rules.append(block)
            return rules if rules else [{"raw_config": content}]
        except Exception:
            return [{"raw_config": content}]

    def _extract_entity_metrics_map(self, content: str) -> Dict[str, Any]:
        """Extract entity metrics mapping from validation response."""
        json_blocks = self._extract_json_blocks(content)
        for block in json_blocks:
            # Look for entity mapping structure
            if any(isinstance(v, dict) and ("metrics" in v or "dashboards" in v)
                   for v in block.values() if isinstance(block, dict)):
                return block
        return {}

    def _extract_yaml_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract YAML blocks from content."""
        import re
        blocks = []

        # Find YAML code blocks
        yaml_pattern = r'```ya?ml\s*([\s\S]*?)```'
        matches = re.findall(yaml_pattern, content)

        for match in matches:
            try:
                parsed = yaml.safe_load(match)
                if parsed:
                    blocks.append(parsed)
            except yaml.YAMLError:
                continue

        # If no code blocks, try parsing the whole content as YAML
        if not blocks:
            try:
                parsed = yaml.safe_load(content)
                if parsed and isinstance(parsed, dict):
                    blocks.append(parsed)
            except yaml.YAMLError:
                pass

        return blocks

    def _extract_json_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Extract JSON blocks from content."""
        import re
        blocks = []

        # Find JSON code blocks
        json_pattern = r'```json\s*([\s\S]*?)```'
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                parsed = json.loads(match)
                if parsed:
                    blocks.append(parsed)
            except json.JSONDecodeError:
                continue

        # Try finding standalone JSON objects
        if not blocks:
            object_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            for match in re.finditer(object_pattern, content):
                try:
                    parsed = json.loads(match.group())
                    if parsed:
                        blocks.append(parsed)
                except json.JSONDecodeError:
                    continue

        return blocks
