"""
REST API connector for Open Forge.
Provides async HTTP client for REST API data sources.
"""
import time
from typing import Any, Dict, List, Optional, Union
from urllib.parse import urljoin

import httpx
from pydantic import Field

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


class RESTConfig(ConnectorConfig):
    """Configuration for REST API connector."""
    connector_type: str = Field(default="rest", frozen=True)
    base_url: str = Field(..., description="Base URL for the API")
    auth_type: Optional[str] = Field(
        default=None,
        description="Authentication type: bearer, basic, api_key, oauth2"
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
    follow_redirects: bool = Field(default=True, description="Follow HTTP redirects")
    # Pagination settings
    pagination_type: Optional[str] = Field(
        default=None,
        description="Pagination type: offset, cursor, page, link"
    )
    page_param: str = Field(default="page", description="Query parameter for page number")
    limit_param: str = Field(default="limit", description="Query parameter for page size")
    offset_param: str = Field(default="offset", description="Query parameter for offset")
    cursor_param: str = Field(default="cursor", description="Query parameter for cursor")
    # Response parsing
    data_path: Optional[str] = Field(
        default=None,
        description="JSON path to data array in response (e.g., 'data.items')"
    )
    total_path: Optional[str] = Field(
        default=None,
        description="JSON path to total count in response"
    )


@ConnectorRegistry.register("rest")
class RESTConnector(BaseConnector):
    """
    REST API connector.

    Provides async HTTP client with authentication, pagination,
    and schema inference support.

    Example:
        config = RESTConfig(
            name="my-api",
            base_url="https://api.example.com/v1",
            auth_type="bearer",
            auth_token="my-token"
        )
        async with RESTConnector(config) as conn:
            data = await conn.get("/users")
            sample = await conn.fetch_sample("/users")
    """

    def __init__(self, config: RESTConfig):
        super().__init__(config)
        self.config: RESTConfig = config
        self._client: Optional[httpx.AsyncClient] = None

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
                base_url=self.config.base_url,
                headers=self._build_headers(),
                auth=self._build_auth(),
                timeout=httpx.Timeout(self.config.timeout_seconds),
                verify=self.config.verify_ssl,
                follow_redirects=self.config.follow_redirects,
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
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test the API connection."""
        start_time = time.time()
        try:
            # Try to make a simple request to the base URL
            client = self._client or httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=self._build_headers(),
                auth=self._build_auth(),
                timeout=httpx.Timeout(self.config.timeout_seconds),
                verify=self.config.verify_ssl,
            )
            try:
                response = await client.get("/")
                latency_ms = (time.time() - start_time) * 1000

                # Consider 2xx and 3xx as success, also some APIs return 404 for root
                success = response.status_code < 500

                return ConnectionTestResult(
                    success=success,
                    message=f"HTTP {response.status_code}",
                    latency_ms=latency_ms,
                    details={
                        "status_code": response.status_code,
                        "base_url": self.config.base_url,
                    }
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

    def _extract_data(self, response_json: Any) -> Any:
        """Extract data from response using configured data_path."""
        if not self.config.data_path:
            return response_json

        data = response_json
        for key in self.config.data_path.split("."):
            if isinstance(data, dict):
                data = data.get(key, {})
            else:
                return response_json
        return data

    def _extract_total(self, response_json: Any) -> Optional[int]:
        """Extract total count from response using configured total_path."""
        if not self.config.total_path:
            return None

        data = response_json
        for key in self.config.total_path.split("."):
            if isinstance(data, dict):
                data = data.get(key)
            else:
                return None

        return int(data) if data is not None else None

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Make a GET request.

        Args:
            endpoint: API endpoint path.
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Parsed JSON response.
        """
        response = await self.client.get(endpoint, params=params, headers=headers)
        response.raise_for_status()
        return response.json()

    async def post(
        self,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None
    ) -> Any:
        """
        Make a POST request.

        Args:
            endpoint: API endpoint path.
            data: Request body.
            params: Query parameters.
            headers: Additional headers.

        Returns:
            Parsed JSON response.
        """
        response = await self.client.post(
            endpoint, json=data, params=params, headers=headers
        )
        response.raise_for_status()
        return response.json()

    async def fetch_paginated(
        self,
        endpoint: str,
        limit: int = 100,
        max_pages: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Fetch paginated data from an endpoint.

        Args:
            endpoint: API endpoint path.
            limit: Items per page.
            max_pages: Maximum number of pages to fetch.

        Returns:
            List of all fetched items.
        """
        all_items = []
        page = 1

        for _ in range(max_pages):
            params = {}

            if self.config.pagination_type == "offset":
                params[self.config.limit_param] = limit
                params[self.config.offset_param] = (page - 1) * limit
            elif self.config.pagination_type == "page":
                params[self.config.limit_param] = limit
                params[self.config.page_param] = page
            else:
                params[self.config.limit_param] = limit

            response = await self.get(endpoint, params=params)
            items = self._extract_data(response)

            if not isinstance(items, list):
                items = [items] if items else []

            all_items.extend(items)

            if len(items) < limit:
                break

            page += 1

        return all_items

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Infer schema from API response.

        Since REST APIs don't have formal schemas, this fetches sample
        data and infers the schema from the response structure.

        Args:
            source: API endpoint to fetch schema for.

        Returns:
            List containing inferred DataSchema.
        """
        if not source:
            return []

        try:
            response = await self.get(source, params={self.config.limit_param: 1})
            data = self._extract_data(response)

            if isinstance(data, list) and data:
                sample = data[0]
            elif isinstance(data, dict):
                sample = data
            else:
                return []

            fields = self._infer_fields(sample)
            return [DataSchema(
                name=source.strip("/").replace("/", "_"),
                fields=fields,
                metadata={"endpoint": source}
            )]
        except Exception:
            return []

    def _infer_fields(
        self,
        obj: Dict[str, Any],
        prefix: str = ""
    ) -> List[SchemaField]:
        """Infer schema fields from a dictionary object."""
        fields = []
        for key, value in obj.items():
            field_name = f"{prefix}{key}" if prefix else key
            field_type = self._infer_type(value)

            if isinstance(value, dict):
                # Flatten nested objects
                nested_fields = self._infer_fields(value, f"{field_name}.")
                fields.extend(nested_fields)
            else:
                fields.append(SchemaField(
                    name=field_name,
                    data_type=field_type,
                    nullable=True,
                ))
        return fields

    def _infer_type(self, value: Any) -> str:
        """Infer type from a Python value."""
        if value is None:
            return "null"
        elif isinstance(value, bool):
            return "boolean"
        elif isinstance(value, int):
            return "integer"
        elif isinstance(value, float):
            return "float"
        elif isinstance(value, str):
            return "string"
        elif isinstance(value, list):
            return "array"
        elif isinstance(value, dict):
            return "object"
        else:
            return "unknown"

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from an API endpoint.

        Args:
            source: API endpoint.
            limit: Maximum number of items.

        Returns:
            SampleData with inferred schema and rows.
        """
        params = {self.config.limit_param: limit}
        response = await self.get(source, params=params)

        data = self._extract_data(response)
        total = self._extract_total(response)

        if not isinstance(data, list):
            data = [data] if data else []

        # Infer schema from first item
        if data:
            fields = self._infer_fields(data[0])
        else:
            fields = []

        schema = DataSchema(
            name=source.strip("/").replace("/", "_"),
            fields=fields,
            metadata={"endpoint": source}
        )

        return SampleData(
            schema=schema,
            rows=data[:limit],
            total_count=total,
            sample_size=len(data[:limit])
        )
