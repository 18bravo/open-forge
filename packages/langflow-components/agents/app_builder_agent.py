"""
App Builder Agent Component for Langflow

Wraps the Open Forge App Builder cluster as a Langflow component,
enabling visual workflow design for application generation from
ontology definitions.
"""
from typing import Any, Dict, List, Optional
import json

from langflow.custom import Component
from langflow.io import (
    MessageTextInput,
    StrInput,
    SecretStrInput,
    DictInput,
    Output,
    BoolInput,
    IntInput,
)
from langflow.schema import Message


class AppBuilderAgentComponent(Component):
    """
    Open Forge App Builder Agent for Langflow.

    This component wraps the App Builder cluster which coordinates:
    - UI Generator Agent
    - Workflow Designer Agent
    - Integration Agent
    - Deployment Agent

    The App Builder Agent generates complete application specifications:
    - React/TypeScript UI component specifications
    - Workflow definitions and approval flows
    - Integration configurations
    - Kubernetes deployment manifests
    - CI/CD pipeline configurations
    """

    display_name = "App Builder Agent"
    description = "Application generation agent cluster for UI, workflows, and deployment"
    icon = "code"
    name = "AppBuilderAgent"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input",
            info="Build instructions or modification request",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context identifier",
            required=True,
        ),
        MessageTextInput(
            name="ontology_schema",
            display_name="Ontology Schema",
            info="The ontology schema (YAML) from Data Architect",
            required=True,
        ),
        DictInput(
            name="requirements",
            display_name="Requirements",
            info="Application requirements from discovery phase",
            required=True,
        ),
        DictInput(
            name="ui_preferences",
            display_name="UI Preferences",
            info="UI styling and component preferences (optional)",
            required=False,
        ),
        DictInput(
            name="integration_config",
            display_name="Integration Config",
            info="External integration requirements (optional)",
            required=False,
        ),
        StrInput(
            name="target_platform",
            display_name="Target Platform",
            info="Target deployment platform",
            value="kubernetes",
            advanced=True,
        ),
        StrInput(
            name="openforge_api_url",
            display_name="Open Forge API URL",
            info="URL of the Open Forge API",
            value="http://localhost:8000",
            advanced=True,
        ),
        SecretStrInput(
            name="openforge_api_key",
            display_name="Open Forge API Key",
            info="API key for Open Forge authentication",
            advanced=True,
        ),
        IntInput(
            name="max_iterations",
            display_name="Max Iterations",
            info="Maximum validation iterations",
            value=2,
            advanced=True,
        ),
        IntInput(
            name="timeout_seconds",
            display_name="Timeout (seconds)",
            info="Maximum execution time in seconds",
            value=900,
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            display_name="App Specification",
            name="app_specification",
            method="run_builder",
        ),
        Output(
            display_name="UI Components",
            name="ui_components",
            method="get_ui_components",
        ),
        Output(
            display_name="Workflows",
            name="workflows",
            method="get_workflows",
        ),
        Output(
            display_name="Integrations",
            name="integrations",
            method="get_integrations",
        ),
        Output(
            display_name="Deployment Config",
            name="deployment_config",
            method="get_deployment_config",
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._result: Optional[Dict[str, Any]] = None

    async def _execute_builder(self) -> Dict[str, Any]:
        """Execute the app builder cluster and cache results."""
        if self._result is not None:
            return self._result

        # Import here to avoid circular dependencies
        from agents.app_builder.cluster import AppBuilderCluster
        from contracts.agent_interface import AgentInput
        from langchain_anthropic import ChatAnthropic

        # Initialize LLM
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
        )

        # Create the app builder cluster
        cluster = AppBuilderCluster(
            llm=llm,
            config={"max_iterations": self.max_iterations},
        )

        # Build context from inputs
        context = {
            "ontology_schema": self.ontology_schema,
            "requirements": self.requirements or {},
            "ui_preferences": self.ui_preferences or {},
            "integration_config": self.integration_config or {},
            "target_platform": self.target_platform,
            "user_input": self.input_text,
        }

        # Create agent input
        agent_input = AgentInput(
            engagement_id=self.engagement_id,
            phase="app_building",
            context=context,
        )

        # Execute the cluster
        try:
            result = await cluster.run(agent_input)

            self._result = {
                "success": result.success,
                "outputs": result.outputs,
                "decisions": result.decisions,
                "confidence": result.confidence,
                "requires_human_review": result.requires_human_review,
                "review_items": result.review_items,
                "errors": result.errors,
                "next_suggested_action": result.next_suggested_action,
            }
        except Exception as e:
            self._result = {
                "success": False,
                "outputs": {},
                "decisions": [],
                "confidence": 0.0,
                "requires_human_review": True,
                "review_items": [
                    {
                        "type": "error",
                        "description": f"App builder execution failed: {str(e)}",
                        "priority": "high",
                    }
                ],
                "errors": [str(e)],
                "next_suggested_action": "handle_error",
            }

        return self._result

    async def run_builder(self) -> Message:
        """
        Execute the app builder agent cluster.

        Returns the complete application specification including
        UI components, workflows, integrations, and deployment config.
        """
        result = await self._execute_builder()

        # Format output as message
        if result["success"]:
            outputs = result["outputs"]
            content = json.dumps(
                {
                    "app_specification": outputs.get("app_specification", {}),
                    "build_summary": outputs.get("build_summary", {}),
                    "validation_result": outputs.get("validation_result", ""),
                    "confidence": result["confidence"],
                    "decisions_count": len(result["decisions"]),
                },
                indent=2,
                default=str,
            )
        else:
            content = json.dumps(
                {
                    "error": "App building failed",
                    "errors": result["errors"],
                    "review_items": result["review_items"],
                },
                indent=2,
            )

        return Message(
            text=content,
            sender="AppBuilderAgent",
            sender_name="App Builder Agent",
        )

    async def get_ui_components(self) -> Message:
        """Extract and return UI component specifications."""
        result = await self._execute_builder()

        ui_components = result["outputs"].get("ui_generation_result", {}).get(
            "component_specs", []
        )

        return Message(
            text=json.dumps(ui_components, indent=2, default=str),
            sender="AppBuilderAgent",
            sender_name="App Builder Agent - UI Components",
        )

    async def get_workflows(self) -> Message:
        """Extract and return workflow definitions."""
        result = await self._execute_builder()

        workflows = result["outputs"].get("workflow_design_result", {}).get(
            "workflow_definitions", []
        )

        return Message(
            text=json.dumps(workflows, indent=2, default=str),
            sender="AppBuilderAgent",
            sender_name="App Builder Agent - Workflows",
        )

    async def get_integrations(self) -> Message:
        """Extract and return integration configurations."""
        result = await self._execute_builder()

        integrations = result["outputs"].get("integration_config_result", {}).get(
            "connector_specs", {}
        )

        return Message(
            text=json.dumps(integrations, indent=2, default=str),
            sender="AppBuilderAgent",
            sender_name="App Builder Agent - Integrations",
        )

    async def get_deployment_config(self) -> Message:
        """Extract and return deployment configuration."""
        result = await self._execute_builder()

        deployment = result["outputs"].get("deployment_setup_result", {}).get(
            "infrastructure_spec", {}
        )

        return Message(
            text=json.dumps(deployment, indent=2, default=str),
            sender="AppBuilderAgent",
            sender_name="App Builder Agent - Deployment Config",
        )
