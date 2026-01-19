"""
Discovery Agent Component for Langflow

Wraps the Open Forge Discovery cluster as a Langflow component,
enabling visual workflow design for stakeholder discovery and
requirements gathering.
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
from langflow.schema.dotdict import dotdict


class DiscoveryAgentComponent(Component):
    """
    Open Forge Discovery Agent for Langflow.

    This component wraps the Discovery cluster which coordinates:
    - Stakeholder Analysis Agent
    - Source Discovery Agent
    - Requirements Gathering Agent

    The Discovery Agent analyzes client context and produces:
    - Stakeholder map with roles and requirements
    - Discovered data sources with quality assessments
    - Prioritized requirements document
    - Recommended next steps
    """

    display_name = "Discovery Agent"
    description = "Stakeholder discovery and requirements gathering agent cluster"
    icon = "search"
    name = "DiscoveryAgent"

    inputs = [
        MessageTextInput(
            name="input_text",
            display_name="Input",
            info="The stakeholder context or question to analyze",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context identifier",
            required=True,
        ),
        StrInput(
            name="organization",
            display_name="Organization",
            info="Name of the client organization",
            required=True,
        ),
        MessageTextInput(
            name="project_description",
            display_name="Project Description",
            info="Description of the project/engagement",
            required=True,
        ),
        DictInput(
            name="known_systems",
            display_name="Known Systems",
            info="List of known systems in the organization (optional)",
            required=False,
            is_list=True,
        ),
        DictInput(
            name="initial_contacts",
            display_name="Initial Contacts",
            info="Initial stakeholder contacts (optional)",
            required=False,
            is_list=True,
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
        BoolInput(
            name="require_approval",
            display_name="Require Approval",
            info="Whether to require human approval before proceeding",
            value=True,
            advanced=True,
        ),
        IntInput(
            name="timeout_seconds",
            display_name="Timeout (seconds)",
            info="Maximum execution time in seconds",
            value=300,
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Discovery Report",
            name="discovery_report",
            method="run_discovery",
        ),
        Output(
            display_name="Stakeholder Map",
            name="stakeholder_map",
            method="get_stakeholder_map",
        ),
        Output(
            display_name="Discovered Sources",
            name="discovered_sources",
            method="get_discovered_sources",
        ),
        Output(
            display_name="Requirements",
            name="requirements",
            method="get_requirements",
        ),
    ]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._result: Optional[Dict[str, Any]] = None

    async def _execute_discovery(self) -> Dict[str, Any]:
        """Execute the discovery cluster and cache results."""
        if self._result is not None:
            return self._result

        # Import here to avoid circular dependencies
        from agents.discovery.cluster import DiscoveryCluster
        from contracts.agent_interface import AgentInput
        from langchain_anthropic import ChatAnthropic
        import os

        # Initialize LLM
        llm = ChatAnthropic(
            model="claude-sonnet-4-20250514",
            temperature=0,
        )

        # Create the discovery cluster
        cluster = DiscoveryCluster(llm=llm)

        # Build context from inputs
        context = {
            "organization": self.organization,
            "project_description": self.project_description,
            "known_systems": self.known_systems or [],
            "initial_contacts": self.initial_contacts or [],
            "user_input": self.input_text,
        }

        # Create agent input
        agent_input = AgentInput(
            engagement_id=self.engagement_id,
            phase="discovery",
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
                        "description": f"Discovery execution failed: {str(e)}",
                        "priority": "high",
                    }
                ],
                "errors": [str(e)],
                "next_suggested_action": "handle_error",
            }

        return self._result

    async def run_discovery(self) -> Message:
        """
        Execute the discovery agent cluster.

        Returns the complete discovery report including stakeholder map,
        discovered sources, and requirements.
        """
        result = await self._execute_discovery()

        # Format output as message
        if result["success"]:
            discovery_report = result["outputs"].get("discovery_report", {})
            content = json.dumps(discovery_report, indent=2, default=str)
        else:
            content = json.dumps(
                {
                    "error": "Discovery failed",
                    "errors": result["errors"],
                    "review_items": result["review_items"],
                },
                indent=2,
            )

        return Message(
            text=content,
            sender="DiscoveryAgent",
            sender_name="Discovery Agent",
        )

    async def get_stakeholder_map(self) -> Message:
        """Extract and return the stakeholder map from discovery results."""
        result = await self._execute_discovery()

        stakeholder_map = result["outputs"].get("discovery_report", {}).get(
            "stakeholder_map", {}
        )

        return Message(
            text=json.dumps(stakeholder_map, indent=2, default=str),
            sender="DiscoveryAgent",
            sender_name="Discovery Agent - Stakeholder Map",
        )

    async def get_discovered_sources(self) -> Message:
        """Extract and return discovered data sources."""
        result = await self._execute_discovery()

        discovered_sources = result["outputs"].get("discovery_report", {}).get(
            "discovered_sources", []
        )

        return Message(
            text=json.dumps(discovered_sources, indent=2, default=str),
            sender="DiscoveryAgent",
            sender_name="Discovery Agent - Discovered Sources",
        )

    async def get_requirements(self) -> Message:
        """Extract and return the requirements document."""
        result = await self._execute_discovery()

        requirements = result["outputs"].get("discovery_report", {}).get(
            "requirements", []
        )

        return Message(
            text=json.dumps(requirements, indent=2, default=str),
            sender="DiscoveryAgent",
            sender_name="Discovery Agent - Requirements",
        )
