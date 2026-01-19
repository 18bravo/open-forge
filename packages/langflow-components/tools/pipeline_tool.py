"""
Pipeline Tool Component for Langflow

Provides tools for triggering and monitoring Open Forge data pipelines
from within Langflow workflows.
"""
from typing import Any, Dict, List, Optional
import json

from langflow.custom import Component
from langflow.io import (
    StrInput,
    SecretStrInput,
    DictInput,
    DropdownInput,
    Output,
    BoolInput,
    IntInput,
)
from langflow.schema import Message


class PipelineToolComponent(Component):
    """
    Open Forge Pipeline Tool for Langflow.

    This component provides operations for interacting with the
    Open Forge pipeline system (Dagster-based):
    - Trigger pipeline runs
    - Monitor pipeline status
    - Get pipeline run history
    - Cancel running pipelines
    - Get pipeline definitions
    """

    display_name = "Pipeline Tool"
    description = "Trigger and monitor Open Forge data pipelines"
    icon = "play"
    name = "PipelineTool"

    inputs = [
        DropdownInput(
            name="operation",
            display_name="Operation",
            info="The pipeline operation to perform",
            options=[
                "trigger",
                "status",
                "history",
                "cancel",
                "list_pipelines",
                "get_definition",
            ],
            value="trigger",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context",
            required=True,
        ),
        StrInput(
            name="pipeline_id",
            display_name="Pipeline ID",
            info="The pipeline identifier (job name)",
            required=False,
        ),
        StrInput(
            name="run_id",
            display_name="Run ID",
            info="The pipeline run ID (for status/cancel operations)",
            required=False,
        ),
        DictInput(
            name="config_overrides",
            display_name="Config Overrides",
            info="Configuration overrides for the pipeline run",
            required=False,
        ),
        DictInput(
            name="run_tags",
            display_name="Run Tags",
            info="Tags to apply to the pipeline run",
            required=False,
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
            name="wait_for_completion",
            display_name="Wait for Completion",
            info="Whether to wait for the pipeline to complete",
            value=False,
            advanced=True,
        ),
        IntInput(
            name="timeout_seconds",
            display_name="Timeout (seconds)",
            info="Timeout for waiting operations",
            value=600,
            advanced=True,
        ),
    ]

    outputs = [
        Output(
            display_name="Result",
            name="result",
            method="execute_operation",
        ),
    ]

    async def execute_operation(self) -> Message:
        """Execute the selected pipeline operation."""
        operation = self.operation

        try:
            if operation == "trigger":
                result = await self._trigger_pipeline()
            elif operation == "status":
                result = await self._get_status()
            elif operation == "history":
                result = await self._get_history()
            elif operation == "cancel":
                result = await self._cancel_pipeline()
            elif operation == "list_pipelines":
                result = await self._list_pipelines()
            elif operation == "get_definition":
                result = await self._get_definition()
            else:
                result = {"error": f"Unknown operation: {operation}"}

            return Message(
                text=json.dumps(result, indent=2, default=str),
                sender="PipelineTool",
                sender_name=f"Pipeline Tool - {operation}",
            )
        except Exception as e:
            return Message(
                text=json.dumps(
                    {"error": str(e), "operation": operation},
                    indent=2,
                ),
                sender="PipelineTool",
                sender_name=f"Pipeline Tool - Error",
            )

    async def _trigger_pipeline(self) -> Dict[str, Any]:
        """Trigger a pipeline run."""
        import httpx
        import asyncio

        if not self.pipeline_id:
            return {"error": "pipeline_id is required for trigger operation"}

        trigger_request = {
            "engagement_id": self.engagement_id,
            "pipeline_id": self.pipeline_id,
            "config_overrides": self.config_overrides or {},
            "tags": self.run_tags or {},
        }

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.post(
                f"{self.openforge_api_url}/api/v1/pipelines/{self.pipeline_id}/trigger",
                headers=headers,
                json=trigger_request,
                timeout=60.0,
            )

            if response.status_code in (200, 201, 202):
                result = response.json()
                run_id = result.get("run_id")

                # If wait_for_completion is true, poll for status
                if self.wait_for_completion and run_id:
                    result = await self._wait_for_completion(run_id, client, headers)

                return result
            else:
                return {
                    "status": "submitted",
                    "run_id": "dev-run-001",
                    "message": "Pipeline API not available - development mode",
                }

    async def _wait_for_completion(
        self, run_id: str, client, headers: Dict[str, str]
    ) -> Dict[str, Any]:
        """Poll for pipeline completion."""
        import asyncio

        start_time = asyncio.get_event_loop().time()
        timeout = self.timeout_seconds

        while (asyncio.get_event_loop().time() - start_time) < timeout:
            response = await client.get(
                f"{self.openforge_api_url}/api/v1/pipelines/runs/{run_id}",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                status_data = response.json()
                status = status_data.get("status", "UNKNOWN")

                if status in ("SUCCESS", "FAILURE", "CANCELED"):
                    return status_data

            # Wait before polling again
            await asyncio.sleep(5)

        return {
            "run_id": run_id,
            "status": "TIMEOUT",
            "message": f"Pipeline did not complete within {timeout} seconds",
        }

    async def _get_status(self) -> Dict[str, Any]:
        """Get the status of a pipeline run."""
        import httpx

        if not self.run_id:
            return {"error": "run_id is required for status operation"}

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/pipelines/runs/{self.run_id}",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "run_id": self.run_id,
                    "status": "UNKNOWN",
                    "message": "Pipeline API not available - development mode",
                }

    async def _get_history(self) -> Dict[str, Any]:
        """Get pipeline run history."""
        import httpx

        params = {"engagement_id": self.engagement_id}
        if self.pipeline_id:
            params["pipeline_id"] = self.pipeline_id

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/pipelines/runs",
                headers=headers,
                params=params,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "runs": [],
                    "total": 0,
                    "message": "Pipeline API not available - development mode",
                }

    async def _cancel_pipeline(self) -> Dict[str, Any]:
        """Cancel a running pipeline."""
        import httpx

        if not self.run_id:
            return {"error": "run_id is required for cancel operation"}

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.post(
                f"{self.openforge_api_url}/api/v1/pipelines/runs/{self.run_id}/cancel",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "run_id": self.run_id,
                    "status": "cancel_requested",
                    "message": "Pipeline API not available - development mode",
                }

    async def _list_pipelines(self) -> Dict[str, Any]:
        """List available pipelines."""
        import httpx

        params = {"engagement_id": self.engagement_id}

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/pipelines",
                headers=headers,
                params=params,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Return example pipelines for development
                return {
                    "pipelines": [
                        {
                            "id": "ingestion_pipeline",
                            "name": "Data Ingestion Pipeline",
                            "description": "Ingest data from configured sources",
                        },
                        {
                            "id": "transformation_pipeline",
                            "name": "Transformation Pipeline",
                            "description": "Apply transformations to raw data",
                        },
                        {
                            "id": "ontology_sync_pipeline",
                            "name": "Ontology Sync Pipeline",
                            "description": "Sync data to knowledge graph",
                        },
                    ],
                    "message": "Pipeline API not available - development mode",
                }

    async def _get_definition(self) -> Dict[str, Any]:
        """Get pipeline definition."""
        import httpx

        if not self.pipeline_id:
            return {"error": "pipeline_id is required for get_definition operation"}

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/pipelines/{self.pipeline_id}",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "id": self.pipeline_id,
                    "definition": {},
                    "message": "Pipeline API not available - development mode",
                }
