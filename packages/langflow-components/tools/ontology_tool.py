"""
Ontology Tool Component for Langflow

Provides tools for querying and modifying the Open Forge ontology
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
    MessageTextInput,
    BoolInput,
)
from langflow.schema import Message


class OntologyToolComponent(Component):
    """
    Open Forge Ontology Tool for Langflow.

    This component provides operations for interacting with the
    Open Forge ontology system:
    - Query object types and their definitions
    - Query relationships between types
    - Search for entities matching criteria
    - Validate data against ontology schema
    - Modify ontology (with approval)
    """

    display_name = "Ontology Tool"
    description = "Query and modify Open Forge ontology"
    icon = "share-2"
    name = "OntologyTool"

    inputs = [
        DropdownInput(
            name="operation",
            display_name="Operation",
            info="The ontology operation to perform",
            options=[
                "query_types",
                "query_relationships",
                "search_entities",
                "validate_data",
                "get_schema",
                "modify_type",
            ],
            value="query_types",
            required=True,
        ),
        StrInput(
            name="engagement_id",
            display_name="Engagement ID",
            info="The Open Forge engagement context",
            required=True,
        ),
        StrInput(
            name="object_type",
            display_name="Object Type",
            info="The ontology object type to operate on",
            required=False,
        ),
        DictInput(
            name="filters",
            display_name="Filters",
            info="Filters to apply to queries (optional)",
            required=False,
        ),
        MessageTextInput(
            name="data",
            display_name="Data",
            info="Data for validation or modification operations",
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
            name="require_approval",
            display_name="Require Approval for Modifications",
            info="Whether to require human approval for modifications",
            value=True,
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
        """Execute the selected ontology operation."""
        operation = self.operation
        engagement_id = self.engagement_id

        try:
            if operation == "query_types":
                result = await self._query_types()
            elif operation == "query_relationships":
                result = await self._query_relationships()
            elif operation == "search_entities":
                result = await self._search_entities()
            elif operation == "validate_data":
                result = await self._validate_data()
            elif operation == "get_schema":
                result = await self._get_schema()
            elif operation == "modify_type":
                result = await self._modify_type()
            else:
                result = {"error": f"Unknown operation: {operation}"}

            return Message(
                text=json.dumps(result, indent=2, default=str),
                sender="OntologyTool",
                sender_name=f"Ontology Tool - {operation}",
            )
        except Exception as e:
            return Message(
                text=json.dumps(
                    {"error": str(e), "operation": operation},
                    indent=2,
                ),
                sender="OntologyTool",
                sender_name=f"Ontology Tool - Error",
            )

    async def _query_types(self) -> Dict[str, Any]:
        """Query available object types in the ontology."""
        import httpx

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/types",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                # Fallback for development/testing
                return {
                    "types": [],
                    "message": "Ontology API not available - development mode",
                    "status_code": response.status_code,
                }

    async def _query_relationships(self) -> Dict[str, Any]:
        """Query relationships between object types."""
        import httpx

        params = {}
        if self.object_type:
            params["object_type"] = self.object_type

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/relationships",
                headers=headers,
                params=params,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "relationships": [],
                    "message": "Ontology API not available - development mode",
                }

    async def _search_entities(self) -> Dict[str, Any]:
        """Search for entities matching criteria."""
        import httpx

        if not self.object_type:
            return {"error": "object_type is required for entity search"}

        search_params = {
            "object_type": self.object_type,
            "filters": self.filters or {},
        }

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.post(
                f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/search",
                headers=headers,
                json=search_params,
                timeout=60.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "entities": [],
                    "message": "Ontology API not available - development mode",
                }

    async def _validate_data(self) -> Dict[str, Any]:
        """Validate data against ontology schema."""
        import httpx

        if not self.object_type:
            return {"error": "object_type is required for validation"}
        if not self.data:
            return {"error": "data is required for validation"}

        # Parse data if it's a string
        data_to_validate = self.data
        if isinstance(data_to_validate, str):
            try:
                data_to_validate = json.loads(data_to_validate)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON data"}

        validation_request = {
            "object_type": self.object_type,
            "data": data_to_validate,
        }

        async with httpx.AsyncClient() as client:
            headers = {"Content-Type": "application/json"}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.post(
                f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/validate",
                headers=headers,
                json=validation_request,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "valid": False,
                    "message": "Ontology API not available - development mode",
                    "errors": [],
                }

    async def _get_schema(self) -> Dict[str, Any]:
        """Get the complete ontology schema."""
        import httpx

        async with httpx.AsyncClient() as client:
            headers = {}
            if self.openforge_api_key:
                headers["Authorization"] = f"Bearer {self.openforge_api_key}"

            response = await client.get(
                f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/schema",
                headers=headers,
                timeout=30.0,
            )

            if response.status_code == 200:
                return response.json()
            else:
                return {
                    "schema": {},
                    "message": "Ontology API not available - development mode",
                }

    async def _modify_type(self) -> Dict[str, Any]:
        """Modify an object type definition (requires approval)."""
        import httpx

        if not self.object_type:
            return {"error": "object_type is required for modification"}
        if not self.data:
            return {"error": "data (modification specification) is required"}

        # Parse data if it's a string
        modification = self.data
        if isinstance(modification, str):
            try:
                modification = json.loads(modification)
            except json.JSONDecodeError:
                return {"error": "Invalid JSON modification data"}

        # If approval is required, create an approval request instead
        if self.require_approval:
            approval_request = {
                "engagement_id": self.engagement_id,
                "operation": "modify_ontology_type",
                "object_type": self.object_type,
                "modification": modification,
                "requires_approval": True,
            }

            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/json"}
                if self.openforge_api_key:
                    headers["Authorization"] = f"Bearer {self.openforge_api_key}"

                response = await client.post(
                    f"{self.openforge_api_url}/api/v1/approvals/",
                    headers=headers,
                    json=approval_request,
                    timeout=30.0,
                )

                if response.status_code in (200, 201):
                    return {
                        "status": "pending_approval",
                        "approval_id": response.json().get("id"),
                        "message": "Modification request created and pending approval",
                    }
                else:
                    return {
                        "status": "pending_approval",
                        "message": "Approval API not available - development mode",
                    }
        else:
            # Direct modification (not recommended for production)
            async with httpx.AsyncClient() as client:
                headers = {"Content-Type": "application/json"}
                if self.openforge_api_key:
                    headers["Authorization"] = f"Bearer {self.openforge_api_key}"

                response = await client.put(
                    f"{self.openforge_api_url}/api/v1/ontology/{self.engagement_id}/types/{self.object_type}",
                    headers=headers,
                    json=modification,
                    timeout=30.0,
                )

                if response.status_code == 200:
                    return response.json()
                else:
                    return {
                        "status": "error",
                        "message": "Ontology API not available - development mode",
                    }
