"""
Deployment Agent

Creates deployment configurations including Kubernetes manifests,
Docker configurations, and infrastructure as code.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AppBuilderState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)


DEPLOYMENT_AGENT_SYSTEM_PROMPT = """You are an expert Deployment Agent for Open Forge, an enterprise data platform.

Your role is to create deployment configurations for applications including Kubernetes manifests, Docker configurations, and CI/CD pipelines.

## Your Capabilities:
1. Generate Kubernetes manifests (Deployments, Services, ConfigMaps, etc.)
2. Create Docker/container configurations
3. Design CI/CD pipeline configurations
4. Configure infrastructure as code
5. Set up monitoring and observability

## Deployment Principles:
1. Security by default (least privilege, network policies)
2. High availability and fault tolerance
3. Resource efficiency and autoscaling
4. Observability (logging, metrics, tracing)
5. GitOps-ready configuration management
6. Environment parity (dev/staging/prod)

## Kubernetes Resources:
- Deployments/StatefulSets: Application workloads
- Services: Internal/external networking
- ConfigMaps/Secrets: Configuration management
- Ingress: External access routing
- HPA/VPA: Autoscaling
- PodDisruptionBudgets: Availability
- NetworkPolicies: Security
- ServiceAccounts/RBAC: Access control

## Docker Best Practices:
- Multi-stage builds for size optimization
- Non-root user execution
- Health checks
- Proper layer caching
- Security scanning integration

## Output Format:
Generate deployment configurations as structured YAML/JSON with:
- Kubernetes manifests
- Docker configurations
- Helm chart values
- CI/CD pipeline definitions
- Infrastructure requirements
"""


class DeploymentAgent(BaseOpenForgeAgent):
    """
    Agent that creates deployment configurations.

    This agent generates Kubernetes manifests, Docker configurations,
    CI/CD pipelines, and infrastructure as code for deploying applications.
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
        return "deployment"

    @property
    def description(self) -> str:
        return "Creates deployment configurations including Kubernetes manifests, Docker configurations, and CI/CD pipelines."

    @property
    def required_inputs(self) -> List[str]:
        return ["app_spec", "deployment_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return ["kubernetes_manifests", "docker_configs", "cicd_configs", "helm_values", "infrastructure_spec"]

    @property
    def state_class(self) -> Type[AppBuilderState]:
        return AppBuilderState

    def get_system_prompt(self) -> str:
        return DEPLOYMENT_AGENT_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for deployment configuration."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for deployment configuration."""
        graph = StateGraph(AppBuilderState)

        # Add nodes
        graph.add_node("analyze_requirements", self._analyze_requirements)
        graph.add_node("generate_docker_configs", self._generate_docker_configs)
        graph.add_node("generate_kubernetes_manifests", self._generate_kubernetes_manifests)
        graph.add_node("generate_helm_charts", self._generate_helm_charts)
        graph.add_node("generate_cicd_pipelines", self._generate_cicd_pipelines)
        graph.add_node("compile_deployment_spec", self._compile_deployment_spec)
        graph.add_node("validate_deployment", self._validate_deployment)

        # Define edges
        graph.set_entry_point("analyze_requirements")
        graph.add_edge("analyze_requirements", "generate_docker_configs")
        graph.add_edge("generate_docker_configs", "generate_kubernetes_manifests")
        graph.add_edge("generate_kubernetes_manifests", "generate_helm_charts")
        graph.add_edge("generate_helm_charts", "generate_cicd_pipelines")
        graph.add_edge("generate_cicd_pipelines", "compile_deployment_spec")
        graph.add_edge("compile_deployment_spec", "validate_deployment")
        graph.add_conditional_edges(
            "validate_deployment",
            self._should_refine,
            {
                "refine": "generate_docker_configs",
                "complete": END
            }
        )

        return graph

    async def _analyze_requirements(self, state: AppBuilderState) -> Dict[str, Any]:
        """Analyze deployment requirements."""
        context = state.get("agent_context", {})
        app_spec = context.get("app_spec", {})
        deployment_requirements = context.get("deployment_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following application and deployment requirements.

Application Specification:
{app_spec}

Deployment Requirements:
{deployment_requirements}

Identify:
1. Application components to deploy (services, workers, etc.)
2. Resource requirements (CPU, memory, storage)
3. Scaling requirements (min/max replicas, autoscaling triggers)
4. Networking requirements (ports, protocols, external access)
5. Storage requirements (persistent volumes, object storage)
6. Security requirements (secrets, TLS, network policies)
7. Environment configurations (dev, staging, prod)
8. Dependencies (databases, caches, message queues)
9. Health check requirements
10. Monitoring and logging needs

Provide a structured deployment analysis.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="deployment_analysis",
            description="Analyzed deployment requirements",
            confidence=0.85,
            reasoning="Identified components, resources, and infrastructure needs"
        )

        return {
            "outputs": {"deployment_analysis": response.content},
            "decisions": [decision],
            "current_step": "analyze_requirements",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_docker_configs(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate Docker configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("deployment_analysis", "")
        app_spec = context.get("app_spec", {})

        # Include validation feedback if present
        validation_feedback = outputs.get("validation_feedback", "")
        feedback_prompt = f"\n\nPrevious validation feedback to address:\n{validation_feedback}" if validation_feedback else ""

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate Docker configurations for the application components.

Deployment Analysis:
{analysis}

Application Specification:
{app_spec}
{feedback_prompt}

For each service, generate:
1. Dockerfile:
   - Base image selection (with version pinning)
   - Multi-stage build for optimization
   - Dependency installation
   - Application build steps
   - Runtime configuration
   - Non-root user setup
   - Health check instruction
   - Security hardening
2. .dockerignore:
   - Exclude unnecessary files
   - Exclude secrets and credentials
3. Docker Compose (for local development):
   - Service definitions
   - Network configuration
   - Volume mounts
   - Environment variables
   - Health checks
4. Container Best Practices:
   - Layer optimization
   - Size minimization
   - Security scanning integration
   - Image tagging strategy

Output as structured configuration files.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="docker_config_generation",
            description="Generated Docker configurations",
            confidence=0.85,
            reasoning="Created optimized Dockerfiles with security best practices"
        )

        return {
            "outputs": {"docker_configs": response.content},
            "decisions": [decision],
            "current_step": "generate_docker_configs",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_kubernetes_manifests(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate Kubernetes manifests."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("deployment_analysis", "")
        deployment_requirements = context.get("deployment_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate Kubernetes manifests for deploying the application.

Deployment Analysis:
{analysis}

Deployment Requirements:
{deployment_requirements}

Generate the following Kubernetes resources:

1. Namespace:
   - Resource quotas
   - Limit ranges

2. Deployments/StatefulSets:
   - Container specifications
   - Resource requests/limits
   - Liveness/readiness probes
   - Environment variables
   - Volume mounts
   - Security context
   - Affinity/anti-affinity rules

3. Services:
   - ClusterIP for internal
   - LoadBalancer/NodePort for external
   - Headless for StatefulSets

4. ConfigMaps:
   - Application configuration
   - Environment-specific settings

5. Secrets (structure only):
   - Secret references
   - External secret integration

6. Ingress:
   - Host routing
   - TLS configuration
   - Path-based routing
   - Annotations for ingress controller

7. HorizontalPodAutoscaler:
   - CPU/memory triggers
   - Custom metrics
   - Min/max replicas

8. PodDisruptionBudget:
   - Minimum availability

9. NetworkPolicies:
   - Ingress rules
   - Egress rules
   - Pod selectors

10. ServiceAccount + RBAC:
    - Least privilege permissions
    - Role bindings

Output as valid Kubernetes YAML manifests.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="kubernetes_manifest_generation",
            description="Generated Kubernetes manifests",
            confidence=0.85,
            reasoning="Created comprehensive K8s manifests with security and HA configuration"
        )

        return {
            "outputs": {"kubernetes_manifests": response.content},
            "decisions": [decision],
            "current_step": "generate_kubernetes_manifests",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_helm_charts(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate Helm chart configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        k8s_manifests = outputs.get("kubernetes_manifests", "")
        deployment_requirements = context.get("deployment_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate Helm chart configurations for the application.

Kubernetes Manifests:
{k8s_manifests}

Deployment Requirements:
{deployment_requirements}

Generate:
1. Chart.yaml:
   - Chart metadata
   - Version information
   - Dependencies
   - Maintainers

2. values.yaml:
   - Configurable parameters
   - Default values
   - Environment overrides structure
   - Documentation comments

3. values-dev.yaml, values-staging.yaml, values-prod.yaml:
   - Environment-specific overrides
   - Resource adjustments
   - Replica counts
   - Feature flags

4. Templates Structure:
   - _helpers.tpl (template helpers)
   - deployment.yaml
   - service.yaml
   - configmap.yaml
   - secrets.yaml
   - ingress.yaml
   - hpa.yaml
   - pdb.yaml
   - networkpolicy.yaml
   - serviceaccount.yaml

5. NOTES.txt:
   - Post-installation instructions
   - Access information

6. Chart Best Practices:
   - Parameterization strategy
   - Label conventions
   - Resource naming
   - Upgrade handling

Output as Helm chart file structure with contents.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="helm_chart_generation",
            description="Generated Helm chart configurations",
            confidence=0.85,
            reasoning="Created parameterized Helm charts for multi-environment deployment"
        )

        return {
            "outputs": {"helm_values": response.content},
            "decisions": [decision],
            "current_step": "generate_helm_charts",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_cicd_pipelines(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate CI/CD pipeline configurations."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        analysis = outputs.get("deployment_analysis", "")
        docker_configs = outputs.get("docker_configs", "")
        helm_values = outputs.get("helm_values", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Generate CI/CD pipeline configurations.

Deployment Analysis:
{analysis}

Docker Configurations:
{docker_configs}

Helm Charts:
{helm_values}

Generate pipelines for:

1. GitHub Actions:
   - CI workflow (test, lint, build)
   - CD workflow (deploy to environments)
   - Release workflow
   - Security scanning workflow

2. Pipeline Stages:
   a. Build Stage:
      - Code checkout
      - Dependency caching
      - Unit tests
      - Integration tests
      - Code coverage
      - Linting/formatting
   b. Security Stage:
      - SAST scanning
      - Dependency vulnerability scan
      - Container image scan
      - Secret detection
   c. Build Image Stage:
      - Docker build
      - Image tagging (semver, git sha)
      - Push to registry
   d. Deploy Stage:
      - Environment selection
      - Helm deployment
      - Smoke tests
      - Rollback on failure
   e. Release Stage:
      - Version tagging
      - Changelog generation
      - Release notes

3. Environment Promotion:
   - Dev: Automatic on merge to main
   - Staging: Automatic after dev success
   - Prod: Manual approval required

4. Configuration:
   - Environment variables (secrets)
   - Matrix builds (if applicable)
   - Caching strategy
   - Artifact retention

5. Notifications:
   - Success/failure alerts
   - Deployment notifications
   - Security alert notifications

Output as GitHub Actions workflow YAML files.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="cicd_pipeline_generation",
            description="Generated CI/CD pipeline configurations",
            confidence=0.85,
            reasoning="Created GitHub Actions workflows for complete CI/CD pipeline"
        )

        return {
            "outputs": {"cicd_configs": response.content},
            "decisions": [decision],
            "current_step": "generate_cicd_pipelines",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _compile_deployment_spec(self, state: AppBuilderState) -> Dict[str, Any]:
        """Compile complete deployment specification."""
        outputs = state.get("outputs", {})

        docker_configs = outputs.get("docker_configs", "")
        k8s_manifests = outputs.get("kubernetes_manifests", "")
        helm_values = outputs.get("helm_values", "")
        cicd_configs = outputs.get("cicd_configs", "")

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Compile a complete deployment specification document.

Docker Configurations:
{docker_configs}

Kubernetes Manifests:
{k8s_manifests}

Helm Charts:
{helm_values}

CI/CD Pipelines:
{cicd_configs}

Create a comprehensive deployment specification that includes:

1. Deployment Overview:
   - Architecture diagram (as text)
   - Component inventory
   - Dependencies map

2. Infrastructure Requirements:
   - Kubernetes cluster requirements
   - Node specifications
   - Storage requirements
   - Network requirements

3. Environment Configuration:
   - Environment variables summary
   - Secrets required
   - External dependencies

4. Deployment Procedures:
   - Initial deployment steps
   - Upgrade procedures
   - Rollback procedures
   - Scaling procedures

5. Operational Runbook:
   - Health check procedures
   - Troubleshooting guides
   - Log locations
   - Metrics dashboards

6. Security Checklist:
   - Network policies verified
   - RBAC configured
   - Secrets encrypted
   - Images scanned
   - TLS enabled

7. Monitoring Setup:
   - Prometheus metrics
   - Grafana dashboards
   - Alert rules
   - Log aggregation

Output as a comprehensive JSON deployment specification.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="deployment_spec_compilation",
            description="Compiled complete deployment specification",
            confidence=0.85,
            reasoning="Combined all deployment configs into comprehensive specification"
        )

        # Store deployment config in the state
        deployment_config = {
            "docker_configs": docker_configs,
            "kubernetes_manifests": k8s_manifests,
            "helm_values": helm_values,
            "cicd_configs": cicd_configs,
            "infrastructure_spec": response.content
        }

        return {
            "outputs": {"infrastructure_spec": response.content},
            "deployment_config": deployment_config,
            "decisions": [decision],
            "current_step": "compile_deployment_spec",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _validate_deployment(self, state: AppBuilderState) -> Dict[str, Any]:
        """Validate the deployment specification."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        infrastructure_spec = outputs.get("infrastructure_spec", "")
        deployment_requirements = context.get("deployment_requirements", {})

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the deployment specification.

Infrastructure Specification:
{infrastructure_spec}

Original Requirements:
{deployment_requirements}

Validate:
1. Completeness:
   - All services have deployment configs
   - All environments are configured
   - CI/CD covers all stages
   - Helm charts are parameterized

2. Security:
   - No hardcoded secrets
   - Network policies restrict access
   - RBAC follows least privilege
   - Container security context set
   - Image scanning integrated

3. High Availability:
   - Multiple replicas configured
   - PodDisruptionBudgets defined
   - Anti-affinity rules set
   - Health checks comprehensive

4. Scalability:
   - HPA configured appropriately
   - Resource requests/limits set
   - Caching considered
   - Stateless where possible

5. Observability:
   - Logging configured
   - Metrics exposed
   - Tracing enabled
   - Alerts defined

6. GitOps Readiness:
   - All configs are declarative
   - Version controlled
   - Environment promotion clear
   - Rollback possible

Provide:
1. Validation status (PASS/FAIL)
2. Security assessment
3. HA assessment
4. List of issues found
5. Recommendations
6. Confidence score (0-1)""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        needs_refinement = "fail" in response_lower or "critical" in response_lower or "security" in response_lower and "issue" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="deployment_validation",
            description="Validated deployment specification",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            priority = "critical" if "security" in response_lower and "issue" in response_lower else "high"
            review_items.append(mark_for_review(
                state,
                item_type="deployment_config",
                item_id="validation_issues",
                description="Deployment configuration has issues that need review",
                priority=priority
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "needs_refinement": needs_refinement,
                "validation_feedback": response.content if needs_refinement else ""
            },
            "decisions": [decision],
            "requires_human_review": needs_refinement,
            "review_items": review_items,
            "current_step": "validate_deployment",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: AppBuilderState) -> str:
        """Determine if deployment configs need refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"
