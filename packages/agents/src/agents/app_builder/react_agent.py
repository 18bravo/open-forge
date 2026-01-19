"""
App Builder ReAct Agent using LangGraph's create_react_agent pattern.

This agent handles UI generation, workflow design, integration configuration,
and deployment setup with memory-aware capabilities.
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


# App Builder system prompt
APP_BUILDER_SYSTEM_PROMPT = """You are the App Builder Agent for Open Forge, an enterprise data platform.

## Your Role
You generate complete application specifications from ontology definitions, including
UI components, workflow automations, integrations, and deployment configurations.

## Capabilities
1. **UI Generation**: Create React/TypeScript component specifications for forms,
   tables, dashboards, and detail views based on the ontology.

2. **Workflow Design**: Design workflow automations including approval flows,
   triggers, and scheduled jobs.

3. **Integration Configuration**: Set up API connections, webhooks, and
   authentication configurations.

4. **Deployment Setup**: Generate Kubernetes manifests, Docker configurations,
   and CI/CD pipeline definitions.

## Output Formats
- UI specs should be JSON with component type, props, and child components
- Workflows should be YAML with triggers, conditions, and actions
- Integrations should be JSON with endpoints, auth, and data mappings
- Deployments should be Kubernetes YAML manifests

## Best Practices
- Generate one component per entity for CRUD operations
- Include form validation based on ontology constraints
- Design workflows that support human approval for critical actions
- Configure proper authentication and authorization
- Include health checks and monitoring in deployments

## Component Guidelines
- Use consistent naming: Entity + Component type (e.g., CustomerForm, CustomerTable)
- Include proper TypeScript types
- Add accessibility attributes
- Support responsive layouts
"""


@register_agent(
    name="app_builder_react",
    category=AgentCategory.APP_BUILDER,
    description="App Builder agent using ReAct pattern for UI generation, "
                "workflow design, and deployment configuration",
    version="1.0.0",
    required_inputs=["engagement_id"],
    output_keys=["ui_components", "workflows", "integrations", "deployment_config"],
    capabilities=["ui_generation", "workflow_design", "integration_config", "deployment_setup"],
    dependencies=["data_architect_react"],
    is_react_agent=True,
    is_memory_aware=True,
)
class AppBuilderReActAgent(MemoryAwareAgent):
    """
    App Builder agent using LangGraph's ReAct pattern with memory capabilities.

    This agent combines:
    - ReAct pattern for iterative application design
    - Memory tools for persisting generated artifacts
    - Specialized tools for UI, workflow, and deployment generation

    Example:
        agent = AppBuilderReActAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="app_builder_1"
        )

        result = await agent.run(
            "Generate a form component for the Customer entity",
            thread_id="generate_customer_form_1"
        )
    """

    def get_tools(self) -> List[BaseTool]:
        """
        Get app builder-specific tools.

        Returns:
            List of tools for UI generation, workflow design, and deployment
        """
        engagement_id = self.engagement_id
        store = self.store

        @tool
        async def generate_form_component(
            entity_name: str,
            component_name: str,
            fields: str,
            validation_rules: str = "",
            submit_action: str = "create",
        ) -> str:
            """
            Generate a form component specification for an entity.

            Use this to create form components for creating or editing entity instances.

            Args:
                entity_name: The entity this form is for
                component_name: Name for the component (e.g., "CustomerForm")
                fields: JSON array of field definitions
                    e.g., '[{"name": "name", "type": "text", "label": "Name", "required": true}]'
                validation_rules: Optional JSON validation rules
                submit_action: Action type (create, update, both)

            Returns:
                Generated form component specification
            """
            import uuid

            try:
                field_defs = json.loads(fields) if isinstance(fields, str) else fields
                validations = json.loads(validation_rules) if validation_rules else []
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            component = {
                "name": component_name,
                "type": "form",
                "entity": entity_name,
                "fields": field_defs,
                "validation": validations,
                "actions": {
                    "submit": submit_action,
                    "cancel": "navigate_back",
                },
                "layout": "vertical",
                "responsive": True,
            }

            # Generate TypeScript interface
            ts_interface = f"interface {component_name}Props {{\n"
            ts_interface += f"  mode: 'create' | 'edit';\n"
            ts_interface += f"  initialData?: {entity_name};\n"
            ts_interface += f"  onSubmit: (data: {entity_name}) => Promise<void>;\n"
            ts_interface += f"  onCancel: () => void;\n"
            ts_interface += f"}}"

            component["typescript"] = ts_interface

            namespace = ("engagements", engagement_id, "ui_component")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": component,
                        "search_text": f"form {component_name} {entity_name} ui component",
                    }
                )
                logger.info(f"Generated form component: {component_name}")
                return f"Generated form component: {component_name} for {entity_name} with {len(field_defs)} fields (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing component: {e}")
                return f"Error storing component: {str(e)}"

        @tool
        async def generate_table_component(
            entity_name: str,
            component_name: str,
            columns: str,
            sortable: bool = True,
            filterable: bool = True,
            paginated: bool = True,
            actions: str = "view,edit,delete",
        ) -> str:
            """
            Generate a data table component specification for an entity.

            Use this to create table/list views for displaying entity collections.

            Args:
                entity_name: The entity this table displays
                component_name: Name for the component (e.g., "CustomerTable")
                columns: JSON array of column definitions
                    e.g., '[{"key": "name", "label": "Name", "sortable": true}]'
                sortable: Enable column sorting
                filterable: Enable column filtering
                paginated: Enable pagination
                actions: Comma-separated row actions

            Returns:
                Generated table component specification
            """
            import uuid

            try:
                column_defs = json.loads(columns) if isinstance(columns, str) else columns
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in columns: {e}"

            component = {
                "name": component_name,
                "type": "table",
                "entity": entity_name,
                "columns": column_defs,
                "features": {
                    "sortable": sortable,
                    "filterable": filterable,
                    "paginated": paginated,
                    "pageSize": 25,
                },
                "rowActions": [a.strip() for a in actions.split(",")],
                "responsive": True,
            }

            namespace = ("engagements", engagement_id, "ui_component")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": component,
                        "search_text": f"table {component_name} {entity_name} list ui component",
                    }
                )
                logger.info(f"Generated table component: {component_name}")
                return f"Generated table component: {component_name} for {entity_name} with {len(column_defs)} columns (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing component: {e}")
                return f"Error storing component: {str(e)}"

        @tool
        async def design_workflow(
            workflow_name: str,
            description: str,
            trigger_type: str,
            trigger_config: str,
            steps: str,
            requires_approval: bool = False,
            approvers: str = "",
        ) -> str:
            """
            Design a workflow automation specification.

            Use this to create workflow automations for business processes.

            Args:
                workflow_name: Name for the workflow
                description: What this workflow does
                trigger_type: Type of trigger (event, schedule, manual)
                trigger_config: JSON configuration for the trigger
                    Event: '{"entity": "Order", "event": "created"}'
                    Schedule: '{"cron": "0 9 * * *"}'
                steps: JSON array of workflow steps
                    e.g., '[{"action": "send_email", "config": {...}}, {"action": "update_status", "config": {...}}]'
                requires_approval: Whether this workflow needs human approval
                approvers: Comma-separated list of approver roles (if requires_approval)

            Returns:
                Generated workflow specification
            """
            import uuid

            try:
                trigger = json.loads(trigger_config) if isinstance(trigger_config, str) else trigger_config
                step_list = json.loads(steps) if isinstance(steps, str) else steps
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            workflow = {
                "name": workflow_name,
                "description": description,
                "trigger": {
                    "type": trigger_type,
                    "config": trigger,
                },
                "steps": step_list,
                "approval": {
                    "required": requires_approval,
                    "approvers": [a.strip() for a in approvers.split(",")] if approvers else [],
                },
                "error_handling": {
                    "retry_count": 3,
                    "notify_on_failure": True,
                },
            }

            namespace = ("engagements", engagement_id, "workflow")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": workflow,
                        "search_text": f"workflow {workflow_name} {trigger_type} {description}",
                    }
                )
                logger.info(f"Designed workflow: {workflow_name}")
                return f"Designed workflow: {workflow_name} with {len(step_list)} steps (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing workflow: {e}")
                return f"Error storing workflow: {str(e)}"

        @tool
        async def configure_integration(
            integration_name: str,
            integration_type: str,
            endpoint_config: str,
            auth_type: str,
            data_mapping: str = "",
        ) -> str:
            """
            Configure an external system integration.

            Use this to set up connections to external APIs, databases, or services.

            Args:
                integration_name: Name for the integration
                integration_type: Type (rest_api, graphql, database, webhook)
                endpoint_config: JSON configuration for the endpoint
                    e.g., '{"base_url": "https://api.example.com", "timeout": 30}'
                auth_type: Authentication type (none, api_key, oauth2, basic)
                data_mapping: Optional JSON data mapping configuration

            Returns:
                Generated integration configuration
            """
            import uuid

            try:
                endpoint = json.loads(endpoint_config) if isinstance(endpoint_config, str) else endpoint_config
                mapping = json.loads(data_mapping) if data_mapping else {}
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            integration = {
                "name": integration_name,
                "type": integration_type,
                "endpoint": endpoint,
                "auth": {
                    "type": auth_type,
                    "credentials_ref": f"secrets/{integration_name.lower().replace(' ', '_')}_credentials",
                },
                "data_mapping": mapping,
                "health_check": {
                    "enabled": True,
                    "interval_seconds": 60,
                },
            }

            namespace = ("engagements", engagement_id, "integration")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": integration,
                        "search_text": f"integration {integration_name} {integration_type} {auth_type}",
                    }
                )
                logger.info(f"Configured integration: {integration_name}")
                return f"Configured integration: {integration_name} ({integration_type}) (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing integration: {e}")
                return f"Error storing integration: {str(e)}"

        @tool
        async def generate_deployment_config(
            app_name: str,
            replicas: int = 2,
            cpu_limit: str = "500m",
            memory_limit: str = "512Mi",
            environment: str = "production",
            ingress_host: str = "",
        ) -> str:
            """
            Generate Kubernetes deployment configuration.

            Use this to create deployment manifests for the application.

            Args:
                app_name: Name of the application
                replicas: Number of pod replicas
                cpu_limit: CPU resource limit (e.g., "500m")
                memory_limit: Memory resource limit (e.g., "512Mi")
                environment: Deployment environment (dev, staging, production)
                ingress_host: Optional ingress hostname

            Returns:
                Generated Kubernetes deployment YAML
            """
            import uuid

            k8s_name = app_name.lower().replace(" ", "-").replace("_", "-")

            deployment = {
                "app_name": app_name,
                "k8s_name": k8s_name,
                "environment": environment,
                "deployment": {
                    "replicas": replicas,
                    "resources": {
                        "limits": {
                            "cpu": cpu_limit,
                            "memory": memory_limit,
                        },
                        "requests": {
                            "cpu": str(int(cpu_limit.replace("m", "")) // 2) + "m" if "m" in cpu_limit else cpu_limit,
                            "memory": str(int(memory_limit.replace("Mi", "")) // 2) + "Mi" if "Mi" in memory_limit else memory_limit,
                        },
                    },
                },
                "service": {
                    "type": "ClusterIP",
                    "port": 80,
                    "targetPort": 8080,
                },
                "ingress": {
                    "enabled": bool(ingress_host),
                    "host": ingress_host,
                    "tls": True if ingress_host else False,
                },
            }

            # Generate YAML manifest
            yaml_manifest = f"""---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {k8s_name}
  namespace: {environment}
  labels:
    app: {k8s_name}
    environment: {environment}
spec:
  replicas: {replicas}
  selector:
    matchLabels:
      app: {k8s_name}
  template:
    metadata:
      labels:
        app: {k8s_name}
    spec:
      containers:
      - name: {k8s_name}
        image: openforge/{k8s_name}:latest
        ports:
        - containerPort: 8080
        resources:
          limits:
            cpu: {cpu_limit}
            memory: {memory_limit}
          requests:
            cpu: {str(int(cpu_limit.replace('m', '')) // 2)}m
            memory: {str(int(memory_limit.replace('Mi', '')) // 2)}Mi
        livenessProbe:
          httpGet:
            path: /health
            port: 8080
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8080
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: {k8s_name}
  namespace: {environment}
spec:
  selector:
    app: {k8s_name}
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP
"""
            if ingress_host:
                yaml_manifest += f"""---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {k8s_name}
  namespace: {environment}
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - {ingress_host}
    secretName: {k8s_name}-tls
  rules:
  - host: {ingress_host}
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: {k8s_name}
            port:
              number: 80
"""

            deployment["yaml_manifest"] = yaml_manifest

            namespace_store = ("engagements", engagement_id, "deployment")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace_store,
                    key,
                    {
                        "content": deployment,
                        "search_text": f"deployment {app_name} kubernetes {environment}",
                    }
                )
                logger.info(f"Generated deployment config: {app_name}")
                return f"Generated deployment configuration for {app_name} ({environment})\n\n```yaml\n{yaml_manifest}\n```"
            except Exception as e:
                logger.error(f"Error storing deployment: {e}")
                return f"Error storing deployment: {str(e)}"

        @tool
        async def compile_app_specification() -> str:
            """
            Compile all generated artifacts into a complete application specification.

            Use this to create a summary of all UI components, workflows,
            integrations, and deployment configs.

            Returns:
                Complete application specification summary
            """
            spec_parts = ["# Application Specification\n"]

            # Get UI components
            try:
                namespace = ("engagements", engagement_id, "ui_component")
                components = await store.alist(namespace=namespace, limit=50)
                if components:
                    spec_parts.append("## UI Components")
                    for item in components:
                        content = item.value.get("content", {})
                        spec_parts.append(f"- **{content.get('name')}** ({content.get('type')}) - {content.get('entity')}")
                    spec_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting UI components: {e}")

            # Get workflows
            try:
                namespace = ("engagements", engagement_id, "workflow")
                workflows = await store.alist(namespace=namespace, limit=50)
                if workflows:
                    spec_parts.append("## Workflows")
                    for item in workflows:
                        content = item.value.get("content", {})
                        trigger = content.get("trigger", {})
                        spec_parts.append(f"- **{content.get('name')}** (trigger: {trigger.get('type')})")
                    spec_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting workflows: {e}")

            # Get integrations
            try:
                namespace = ("engagements", engagement_id, "integration")
                integrations = await store.alist(namespace=namespace, limit=50)
                if integrations:
                    spec_parts.append("## Integrations")
                    for item in integrations:
                        content = item.value.get("content", {})
                        spec_parts.append(f"- **{content.get('name')}** ({content.get('type')})")
                    spec_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting integrations: {e}")

            # Get deployments
            try:
                namespace = ("engagements", engagement_id, "deployment")
                deployments = await store.alist(namespace=namespace, limit=50)
                if deployments:
                    spec_parts.append("## Deployment Configurations")
                    for item in deployments:
                        content = item.value.get("content", {})
                        spec_parts.append(f"- **{content.get('app_name')}** ({content.get('environment')})")
                    spec_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting deployments: {e}")

            if len(spec_parts) == 1:
                return "No application artifacts generated yet."

            return "\n".join(spec_parts)

        return [
            generate_form_component,
            generate_table_component,
            design_workflow,
            configure_integration,
            generate_deployment_config,
            compile_app_specification,
        ]

    def get_system_prompt(self) -> str:
        """Get the app builder agent system prompt."""
        return APP_BUILDER_SYSTEM_PROMPT


# Factory function for easier instantiation
def create_app_builder_react_agent(
    llm: BaseChatModel,
    checkpointer: PostgresSaver,
    store: PostgresStore,
    engagement_id: str,
    agent_id: str = "app_builder_react",
) -> AppBuilderReActAgent:
    """
    Create a configured App Builder ReAct agent.

    Args:
        llm: The language model to use
        checkpointer: PostgresSaver for thread checkpoints
        store: PostgresStore for long-term memory
        engagement_id: The engagement this agent operates within
        agent_id: Optional custom agent ID

    Returns:
        Configured AppBuilderReActAgent instance
    """
    return AppBuilderReActAgent(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        engagement_id=engagement_id,
        agent_id=agent_id,
    )
