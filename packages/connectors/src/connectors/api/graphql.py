"""
GraphQL API connector for Open Forge.
Provides async GraphQL client for data sources.
"""
import logging
import time
from typing import Any, Dict, List, Optional

import httpx
from pydantic import Field

logger = logging.getLogger(__name__)

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorRegistry,
    ConnectionStatus,
    ConnectionTestResult,
    DataSchema,
    SchemaField,
    SampleData,
)


class GraphQLConfig(ConnectorConfig):
    """Configuration for GraphQL API connector."""
    connector_type: str = Field(default="graphql", frozen=True)
    endpoint: str = Field(..., description="GraphQL endpoint URL")
    auth_type: Optional[str] = Field(
        default=None,
        description="Authentication type: bearer, basic, api_key"
    )
    auth_token: Optional[str] = Field(default=None, description="Bearer token or API key")
    auth_username: Optional[str] = Field(default=None, description="Username for basic auth")
    auth_password: Optional[str] = Field(default=None, description="Password for basic auth")
    api_key_header: str = Field(default="X-API-Key", description="Header name for API key auth")
    default_headers: Dict[str, str] = Field(
        default_factory=dict,
        description="Default headers to include in all requests"
    )
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    # Introspection settings
    introspection_enabled: bool = Field(
        default=True,
        description="Whether to allow schema introspection"
    )


# Standard GraphQL introspection query
INTROSPECTION_QUERY = """
query IntrospectionQuery {
    __schema {
        queryType { name }
        mutationType { name }
        types {
            kind
            name
            description
            fields(includeDeprecated: true) {
                name
                description
                args {
                    name
                    description
                    type {
                        kind
                        name
                        ofType {
                            kind
                            name
                            ofType {
                                kind
                                name
                            }
                        }
                    }
                }
                type {
                    kind
                    name
                    ofType {
                        kind
                        name
                        ofType {
                            kind
                            name
                        }
                    }
                }
            }
        }
    }
}
"""


@ConnectorRegistry.register("graphql")
class GraphQLConnector(BaseConnector):
    """
    GraphQL API connector.

    Provides async GraphQL client with authentication and
    schema introspection support.

    Example:
        config = GraphQLConfig(
            name="my-graphql",
            endpoint="https://api.example.com/graphql",
            auth_type="bearer",
            auth_token="my-token"
        )
        async with GraphQLConnector(config) as conn:
            result = await conn.query("{ users { id name } }")
            schema = await conn.fetch_schema()
    """

    def __init__(self, config: GraphQLConfig):
        super().__init__(config)
        self.config: GraphQLConfig = config
        self._client: Optional[httpx.AsyncClient] = None
        self._schema_cache: Optional[Dict[str, Any]] = None

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the HTTP client."""
        if self._client is None:
            raise RuntimeError("Connector not connected. Call connect() first.")
        return self._client

    def _build_headers(self) -> Dict[str, str]:
        """Build request headers including authentication."""
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            **self.config.default_headers
        }

        if self.config.auth_type == "bearer" and self.config.auth_token:
            headers["Authorization"] = f"Bearer {self.config.auth_token}"
        elif self.config.auth_type == "api_key" and self.config.auth_token:
            headers[self.config.api_key_header] = self.config.auth_token

        return headers

    def _build_auth(self) -> Optional[httpx.BasicAuth]:
        """Build basic auth if configured."""
        if (
            self.config.auth_type == "basic"
            and self.config.auth_username
            and self.config.auth_password
        ):
            return httpx.BasicAuth(
                self.config.auth_username,
                self.config.auth_password
            )
        return None

    async def connect(self) -> None:
        """Create the HTTP client."""
        self._status = ConnectionStatus.CONNECTING
        try:
            self._client = httpx.AsyncClient(
                headers=self._build_headers(),
                auth=self._build_auth(),
                timeout=httpx.Timeout(self.config.timeout_seconds),
                verify=self.config.verify_ssl,
            )
            self._status = ConnectionStatus.CONNECTED
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            raise RuntimeError(f"Failed to create HTTP client: {e}") from e

    async def disconnect(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
        self._schema_cache = None
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test the GraphQL connection with a simple query."""
        start_time = time.time()
        try:
            client = self._client or httpx.AsyncClient(
                headers=self._build_headers(),
                auth=self._build_auth(),
                timeout=httpx.Timeout(self.config.timeout_seconds),
                verify=self.config.verify_ssl,
            )
            try:
                # Try a simple introspection query
                response = await client.post(
                    self.config.endpoint,
                    json={"query": "{ __typename }"}
                )
                latency_ms = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    result = response.json()
                    if "errors" in result and not "data" in result:
                        return ConnectionTestResult(
                            success=False,
                            message=f"GraphQL error: {result['errors'][0].get('message', 'Unknown error')}",
                            latency_ms=latency_ms,
                            details={"errors": result["errors"]}
                        )
                    return ConnectionTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        details={"endpoint": self.config.endpoint}
                    )
                else:
                    return ConnectionTestResult(
                        success=False,
                        message=f"HTTP {response.status_code}",
                        latency_ms=latency_ms,
                        details={"status_code": response.status_code}
                    )
            finally:
                if not self._client:
                    await client.aclose()
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {str(e)}",
                latency_ms=latency_ms,
                details={"error": str(e)}
            )

    async def query(
        self,
        query: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL query.

        Args:
            query: GraphQL query string.
            variables: Query variables.
            operation_name: Operation name (for multi-operation documents).

        Returns:
            Query result data.

        Raises:
            RuntimeError: If the query returns errors.
        """
        payload: Dict[str, Any] = {"query": query}
        if variables:
            payload["variables"] = variables
        if operation_name:
            payload["operationName"] = operation_name

        response = await self.client.post(self.config.endpoint, json=payload)
        response.raise_for_status()

        result = response.json()

        if "errors" in result:
            errors = result["errors"]
            error_messages = [e.get("message", str(e)) for e in errors]
            raise RuntimeError(f"GraphQL errors: {'; '.join(error_messages)}")

        return result.get("data", {})

    async def mutate(
        self,
        mutation: str,
        variables: Optional[Dict[str, Any]] = None,
        operation_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a GraphQL mutation.

        Args:
            mutation: GraphQL mutation string.
            variables: Mutation variables.
            operation_name: Operation name.

        Returns:
            Mutation result data.
        """
        return await self.query(mutation, variables, operation_name)

    async def introspect(self) -> Dict[str, Any]:
        """
        Fetch the GraphQL schema via introspection.

        Returns:
            Full introspection result.
        """
        if self._schema_cache:
            return self._schema_cache

        if not self.config.introspection_enabled:
            raise RuntimeError("Schema introspection is disabled")

        result = await self.query(INTROSPECTION_QUERY)
        self._schema_cache = result
        return result

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema information via GraphQL introspection.

        Args:
            source: Optional type name to filter. If None, returns all types.

        Returns:
            List of DataSchema objects for GraphQL types.
        """
        try:
            introspection = await self.introspect()
        except Exception:
            return []

        schema_data = introspection.get("__schema", {})
        types = schema_data.get("types", [])

        schemas = []
        for type_info in types:
            # Skip internal types (starting with __)
            type_name = type_info.get("name", "")
            if type_name.startswith("__"):
                continue

            # Filter by source if provided
            if source and type_name != source:
                continue

            # Only include OBJECT types with fields
            if type_info.get("kind") != "OBJECT":
                continue

            fields_data = type_info.get("fields", [])
            if not fields_data:
                continue

            fields = []
            for field_info in fields_data:
                field_type = self._resolve_type(field_info.get("type", {}))
                fields.append(SchemaField(
                    name=field_info.get("name", ""),
                    data_type=field_type,
                    nullable=not field_type.endswith("!"),
                    description=field_info.get("description"),
                ))

            schemas.append(DataSchema(
                name=type_name,
                fields=fields,
                description=type_info.get("description"),
                metadata={"kind": type_info.get("kind")}
            ))

        return schemas

    def _resolve_type(self, type_info: Dict[str, Any]) -> str:
        """Resolve GraphQL type to a string representation."""
        kind = type_info.get("kind")
        name = type_info.get("name")
        of_type = type_info.get("ofType")

        if kind == "NON_NULL":
            inner = self._resolve_type(of_type) if of_type else "Unknown"
            return f"{inner}!"
        elif kind == "LIST":
            inner = self._resolve_type(of_type) if of_type else "Unknown"
            return f"[{inner}]"
        elif name:
            return name
        else:
            return "Unknown"

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data for a GraphQL type.

        Note: This requires a query field that matches the type name
        (e.g., 'users' for 'User' type). The query must be constructed
        based on the actual API schema.

        Args:
            source: GraphQL type name or query field.
            limit: Maximum number of items.

        Returns:
            SampleData with schema and rows.
        """
        # Get schema for the type
        schemas = await self.fetch_schema(source)

        # If not found as type, it might be a query field
        if not schemas:
            # Try to infer schema from query result
            query_field = source.lower()
            fields_str = "id"  # Minimal field

            try:
                query = f"{{ {query_field}(first: {limit}) {{ {fields_str} }} }}"
                data = await self.query(query)
                items = data.get(query_field, [])

                if items and isinstance(items, list):
                    fields = self._infer_fields(items[0])
                    schema = DataSchema(
                        name=source,
                        fields=fields,
                        metadata={"query_field": query_field}
                    )
                    return SampleData(
                        schema=schema,
                        rows=items[:limit],
                        sample_size=len(items[:limit])
                    )
            except Exception as e:
                logger.debug("Failed to infer schema from query for %s: %s", source, e)

            # Return empty sample if unable to query
            return SampleData(
                schema=DataSchema(name=source, fields=[]),
                rows=[],
                sample_size=0
            )

        schema = schemas[0]

        # Build a query for the type
        field_names = [f.name for f in schema.fields[:20]]  # Limit fields
        fields_str = " ".join(field_names) if field_names else "id"
        query_field = source[0].lower() + source[1:] + "s"  # Naive pluralization

        try:
            query = f"{{ {query_field}(first: {limit}) {{ {fields_str} }} }}"
            data = await self.query(query)
            items = data.get(query_field, [])

            if not isinstance(items, list):
                items = [items] if items else []

            return SampleData(
                schema=schema,
                rows=items[:limit],
                sample_size=len(items[:limit])
            )
        except Exception:
            return SampleData(
                schema=schema,
                rows=[],
                sample_size=0
            )

    def _infer_fields(self, obj: Dict[str, Any]) -> List[SchemaField]:
        """Infer schema fields from a dictionary object."""
        fields = []
        for key, value in obj.items():
            field_type = self._infer_type(value)
            fields.append(SchemaField(
                name=key,
                data_type=field_type,
                nullable=True,
            ))
        return fields

    def _infer_type(self, value: Any) -> str:
        """Infer GraphQL type from a Python value."""
        if value is None:
            return "String"
        elif isinstance(value, bool):
            return "Boolean"
        elif isinstance(value, int):
            return "Int"
        elif isinstance(value, float):
            return "Float"
        elif isinstance(value, str):
            return "String"
        elif isinstance(value, list):
            if value:
                inner_type = self._infer_type(value[0])
                return f"[{inner_type}]"
            return "[String]"
        elif isinstance(value, dict):
            return "Object"
        else:
            return "String"
