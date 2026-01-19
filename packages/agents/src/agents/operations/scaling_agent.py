"""
Scaling Agent

Generates auto-scaling policies (Kubernetes HPA), load balancing configurations,
and analyzes workload patterns to suggest optimal scaling thresholds.
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


SCALING_AGENT_SYSTEM_PROMPT = """You are an expert Scaling Agent for Open Forge, an enterprise data platform.

Your role is to design auto-scaling policies and load balancing configurations for optimal resource utilization.

## Your Capabilities:
1. Generate Kubernetes Horizontal Pod Autoscaler (HPA) configurations
2. Design Vertical Pod Autoscaler (VPA) recommendations
3. Create load balancer configurations (Ingress, Service, Gateway API)
4. Analyze workload patterns to suggest scaling thresholds
5. Design custom metrics-based scaling policies

## Kubernetes HPA Best Practices:
- Use appropriate metrics (CPU, memory, custom metrics)
- Set realistic minReplicas and maxReplicas
- Configure stabilization windows to prevent thrashing
- Use behavior policies for scale up/down
- Consider scaling velocity (pods per period)

## HPA Configuration Structure:
```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: <workload>-hpa
  namespace: <namespace>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: <workload>
  minReplicas: <min>
  maxReplicas: <max>
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: <target>
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
```

## Load Balancing Strategies:
- Round Robin: Equal distribution
- Least Connections: Route to least busy server
- IP Hash: Session persistence
- Weighted: Proportional distribution
- Geographic: Location-based routing

## Custom Metrics for Scaling:
- Request rate (requests per second)
- Queue depth (pending jobs)
- Response latency (P95, P99)
- Business metrics (active users, transactions)
- Entity processing rates from ontology

Always output configurations in valid Kubernetes YAML format.
Include annotations and labels for proper resource management.
"""


class ScalingAgent(BaseOpenForgeAgent):
    """
    Agent that generates auto-scaling policies and load balancing configurations.
    Analyzes workload patterns to suggest optimal scaling thresholds.
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
        return "scaling_agent"

    @property
    def description(self) -> str:
        return (
            "Generates auto-scaling policies (K8s HPA), load balancing configurations, "
            "and analyzes workload patterns to suggest scaling thresholds."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["workload_specs", "scaling_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "hpa_configs",
            "load_balancer_configs",
            "workload_analysis",
            "scaling_recommendations"
        ]

    @property
    def state_class(self) -> Type[OperationsState]:
        return OperationsState

    def get_system_prompt(self) -> str:
        return SCALING_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for scaling configuration generation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for scaling configuration generation."""
        graph = StateGraph(OperationsState)

        # Add nodes
        graph.add_node("analyze_workloads", self._analyze_workloads)
        graph.add_node("generate_hpa_configs", self._generate_hpa_configs)
        graph.add_node("generate_load_balancer_configs", self._generate_load_balancer_configs)
        graph.add_node("calculate_thresholds", self._calculate_thresholds)
        graph.add_node("validate_scaling_configs", self._validate_scaling_configs)

        # Define edges
        graph.set_entry_point("analyze_workloads")
        graph.add_edge("analyze_workloads", "generate_hpa_configs")
        graph.add_edge("generate_hpa_configs", "generate_load_balancer_configs")
        graph.add_edge("generate_load_balancer_configs", "calculate_thresholds")
        graph.add_edge("calculate_thresholds", "validate_scaling_configs")
        graph.add_edge("validate_scaling_configs", END)

        return graph

    async def _analyze_workloads(self, state: OperationsState) -> Dict[str, Any]:
        """Analyze workload specifications to understand scaling needs."""
        context = state.get("agent_context", {})
        workload_specs = context.get("workload_specs", {})
        scaling_requirements = context.get("scaling_requirements", {})
        ontology_schema = context.get("ontology_schema", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following workload specifications and scaling requirements:

Workload Specifications:
{json.dumps(workload_specs, indent=2) if isinstance(workload_specs, dict) else workload_specs}

Scaling Requirements:
{json.dumps(scaling_requirements, indent=2) if isinstance(scaling_requirements, dict) else scaling_requirements}

Ontology Schema (for entity-based scaling):
{ontology_schema}

Analyze and provide:
1. Workload classification (CPU-bound, memory-bound, I/O-bound, mixed)
2. Expected traffic patterns (steady, bursty, periodic)
3. Criticality level for each workload
4. Interdependencies between workloads
5. Entity processing characteristics from ontology
6. Recommended scaling strategy for each workload type

Output a structured analysis with specific scaling recommendations.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="workload_analysis",
            description="Analyzed workloads for scaling requirements",
            confidence=0.85,
            reasoning="Identified workload characteristics and scaling strategies"
        )

        return {
            "outputs": {"workload_analysis": response.content},
            "workload_analysis": {"analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_workloads",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_hpa_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Generate Kubernetes HPA configurations for each workload."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("workload_analysis", "")
        namespace = context.get("namespace", "default")
        workload_specs = context.get("workload_specs", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Based on the workload analysis, generate Kubernetes HPA configurations.

Workload Analysis:
{analysis}

Workload Specifications:
{json.dumps(workload_specs, indent=2) if isinstance(workload_specs, dict) else workload_specs}

Namespace: {namespace}

Generate HPA configurations for each workload that needs auto-scaling:

1. **Standard HPAs** (CPU/Memory based):
   - Use autoscaling/v2 API
   - Set appropriate min/max replicas
   - Configure target utilization
   - Add scale behavior policies

2. **Custom Metrics HPAs** (for entity processing):
   - Reference Prometheus metrics
   - Use external metrics API
   - Scale based on queue depth or processing rate

3. **VPA Recommendations** (for vertical scaling):
   - Resource requests/limits recommendations
   - Update mode suggestions

For each HPA, provide:
- Complete YAML configuration
- Explanation of threshold choices
- Expected behavior under load

Output all configurations as valid Kubernetes YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse HPA configs
        hpa_configs = self._parse_k8s_configs(response.content)

        decision = add_decision(
            state,
            decision_type="hpa_generation",
            description="Generated HPA configurations",
            confidence=0.80,
            reasoning="Created horizontal pod autoscaler configs based on workload analysis"
        )

        return {
            "outputs": {"hpa_configs": hpa_configs, "hpa_configs_raw": response.content},
            "scaling_policies": hpa_configs,
            "decisions": [decision],
            "current_step": "generate_hpa_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_load_balancer_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Generate load balancer and ingress configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("workload_analysis", "")
        namespace = context.get("namespace", "default")
        domain = context.get("domain", "example.com")
        workload_specs = context.get("workload_specs", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate load balancer and ingress configurations for the workloads.

Workload Analysis:
{analysis}

Workload Specifications:
{json.dumps(workload_specs, indent=2) if isinstance(workload_specs, dict) else workload_specs}

Namespace: {namespace}
Domain: {domain}

Create the following configurations:

1. **Kubernetes Services**:
   - ClusterIP services for internal communication
   - LoadBalancer services for external access
   - Headless services for stateful workloads

2. **Ingress Configuration**:
   - Path-based routing
   - Host-based routing
   - TLS termination
   - Rate limiting annotations
   - Health check paths

3. **Gateway API Resources** (optional, for advanced routing):
   - Gateway
   - HTTPRoute
   - ReferenceGrant

4. **Load Balancer Annotations**:
   - Cloud provider specific (AWS ALB, GCP LB, Azure LB)
   - Session affinity settings
   - Timeout configurations
   - Health check settings

Include:
- Service YAML for each workload
- Ingress YAML with routing rules
- ConfigMap for nginx/envoy configuration if needed
- Annotations for load balancer behavior

Output as valid Kubernetes YAML, separated by `---`.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse load balancer configs
        lb_configs = self._parse_k8s_configs(response.content)

        decision = add_decision(
            state,
            decision_type="loadbalancer_generation",
            description="Generated load balancer configurations",
            confidence=0.80,
            reasoning="Created services, ingress, and load balancer configs"
        )

        return {
            "outputs": {"load_balancer_configs": lb_configs, "load_balancer_configs_raw": response.content},
            "load_balancer_configs": lb_configs if isinstance(lb_configs, dict) else {"configs": lb_configs},
            "decisions": [decision],
            "current_step": "generate_load_balancer_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _calculate_thresholds(self, state: OperationsState) -> Dict[str, Any]:
        """Calculate optimal scaling thresholds based on workload patterns."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("workload_analysis", "")
        historical_metrics = context.get("historical_metrics", {})
        sla_requirements = context.get("sla_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Calculate optimal scaling thresholds based on workload analysis and requirements.

Workload Analysis:
{analysis}

Historical Metrics (if available):
{json.dumps(historical_metrics, indent=2) if isinstance(historical_metrics, dict) else historical_metrics}

SLA Requirements:
{json.dumps(sla_requirements, indent=2) if isinstance(sla_requirements, dict) else sla_requirements}

Calculate and provide:

1. **CPU Utilization Thresholds**:
   - Scale-up threshold (typically 70-80%)
   - Scale-down threshold (typically 30-50%)
   - Justification based on workload type

2. **Memory Utilization Thresholds**:
   - Scale-up threshold
   - Scale-down threshold
   - Memory pressure considerations

3. **Custom Metrics Thresholds**:
   - Request rate thresholds
   - Queue depth limits
   - Latency targets (P95, P99)
   - Entity processing rate thresholds

4. **Timing Parameters**:
   - Scale-up stabilization window
   - Scale-down stabilization window
   - Metric evaluation period

5. **Cost Optimization Recommendations**:
   - Minimum replicas for baseline cost
   - Maximum replicas for budget limits
   - Spot/preemptible instance considerations

Output a structured JSON object with all thresholds and justifications:
{{
  "workload_name": {{
    "cpu_scale_up": <percent>,
    "cpu_scale_down": <percent>,
    "memory_scale_up": <percent>,
    "memory_scale_down": <percent>,
    "custom_metrics": {{
      "metric_name": {{"target": <value>, "scale_up": <value>, "scale_down": <value>}}
    }},
    "stabilization": {{
      "scale_up_window": <seconds>,
      "scale_down_window": <seconds>
    }},
    "replicas": {{
      "min": <count>,
      "max": <count>,
      "initial": <count>
    }},
    "justification": "<explanation>"
  }}
}}""")
        ]

        response = await self.llm.ainvoke(messages)

        # Extract thresholds
        thresholds = self._extract_thresholds(response.content)

        decision = add_decision(
            state,
            decision_type="threshold_calculation",
            description="Calculated optimal scaling thresholds",
            confidence=0.85,
            reasoning="Determined thresholds based on workload patterns and SLA requirements"
        )

        return {
            "outputs": {"scaling_thresholds": thresholds, "scaling_thresholds_raw": response.content},
            "decisions": [decision],
            "current_step": "calculate_thresholds",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_scaling_configs(self, state: OperationsState) -> Dict[str, Any]:
        """Validate all scaling configurations for completeness and correctness."""
        outputs = state.get("outputs", {})

        hpa_configs = outputs.get("hpa_configs_raw", "")
        lb_configs = outputs.get("load_balancer_configs_raw", "")
        thresholds = outputs.get("scaling_thresholds_raw", "")
        analysis = outputs.get("workload_analysis", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the generated scaling configurations for completeness and correctness.

Workload Analysis:
{analysis}

HPA Configurations:
{hpa_configs}

Load Balancer Configurations:
{lb_configs}

Scaling Thresholds:
{thresholds}

Validate:
1. YAML syntax validity for all Kubernetes resources
2. API version compatibility (autoscaling/v2, networking.k8s.io/v1)
3. Resource references are correct (Deployment names, Service names)
4. Threshold values are within acceptable ranges
5. Scaling policies prevent thrashing
6. Load balancer configs match workload requirements
7. All workloads have appropriate scaling coverage

Provide:
1. Validation status (PASS/FAIL)
2. List of any issues found
3. Specific recommendations for each workload
4. Summary of scaling recommendations

Output a comprehensive validation report.""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        is_valid = "pass" in response_lower and "fail" not in response_lower

        confidence = 0.90 if is_valid else 0.70

        decision = add_decision(
            state,
            decision_type="scaling_validation",
            description="Validated scaling configurations",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=not is_valid
        )

        review_items = []
        if not is_valid:
            review_items.append(mark_for_review(
                state,
                item_type="scaling_config",
                item_id="validation_issues",
                description="Scaling configuration has issues that may need review",
                priority="medium"
            ))

        # Compile scaling recommendations
        scaling_recommendations = {
            "analysis": outputs.get("workload_analysis", ""),
            "thresholds": outputs.get("scaling_thresholds", {}),
            "validation": response.content,
            "is_valid": is_valid
        }

        return {
            "outputs": {
                "validation_result": response.content,
                "is_valid": is_valid,
                "scaling_recommendations": scaling_recommendations
            },
            "decisions": [decision],
            "requires_human_review": not is_valid,
            "review_items": review_items,
            "current_step": "validate_scaling_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _parse_k8s_configs(self, content: str) -> List[Dict[str, Any]]:
        """Parse Kubernetes YAML configurations from content."""
        configs = []
        try:
            # Split by YAML document separator
            documents = content.split("---")
            for doc in documents:
                doc = doc.strip()
                if not doc:
                    continue

                # Try to extract YAML from code blocks
                if "```yaml" in doc or "```" in doc:
                    import re
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

    def _extract_thresholds(self, content: str) -> Dict[str, Any]:
        """Extract scaling thresholds from LLM response."""
        import re

        # Try to find JSON object
        json_pattern = r'\{[\s\S]*\}'
        matches = re.findall(json_pattern, content)

        for match in matches:
            try:
                parsed = json.loads(match)
                if parsed and isinstance(parsed, dict):
                    # Check if it looks like thresholds structure
                    for key, value in parsed.items():
                        if isinstance(value, dict) and any(
                            k in value for k in ["cpu_scale_up", "min", "replicas", "custom_metrics"]
                        ):
                            return parsed
            except json.JSONDecodeError:
                continue

        return {"raw_thresholds": content}
