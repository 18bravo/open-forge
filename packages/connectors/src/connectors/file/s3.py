"""
S3/MinIO connector for Open Forge.
Provides async S3-compatible object storage access.
"""
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from typing import Any, AsyncIterator, Dict, List, Optional

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


class S3Config(ConnectorConfig):
    """Configuration for S3/MinIO connector."""
    connector_type: str = Field(default="s3", frozen=True)
    endpoint_url: Optional[str] = Field(
        default=None,
        description="S3-compatible endpoint URL (for MinIO, LocalStack, etc.)"
    )
    region_name: str = Field(default="us-east-1", description="AWS region")
    access_key_id: str = Field(..., description="AWS access key ID")
    secret_access_key: str = Field(..., description="AWS secret access key")
    bucket: str = Field(..., description="S3 bucket name")
    prefix: str = Field(default="", description="Key prefix for filtering objects")
    # Connection settings
    use_ssl: bool = Field(default=True, description="Use SSL for connections")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
    # Thread pool settings
    max_workers: int = Field(default=4, description="Max worker threads for I/O")


@ConnectorRegistry.register("s3")
class S3Connector(BaseConnector):
    """
    S3/MinIO object storage connector.

    Provides async access to S3-compatible storage with support
    for listing, reading, and streaming objects.

    Requires boto3 to be installed.

    Example:
        config = S3Config(
            name="my-s3",
            endpoint_url="http://localhost:9000",  # For MinIO
            access_key_id="minio",
            secret_access_key="minio123",
            bucket="my-bucket"
        )
        async with S3Connector(config) as conn:
            files = await conn.list_objects()
            data = await conn.read_object("data.csv")
    """

    def __init__(self, config: S3Config):
        super().__init__(config)
        self.config: S3Config = config
        self._client: Any = None
        self._executor: Optional[ThreadPoolExecutor] = None

    def _import_boto3(self):
        """Import boto3 with helpful error message."""
        try:
            import boto3
            return boto3
        except ImportError:
            raise ImportError(
                "boto3 is required for S3 support. "
                "Install it with: pip install boto3"
            )

    async def connect(self) -> None:
        """Create the S3 client."""
        self._status = ConnectionStatus.CONNECTING
        try:
            boto3 = self._import_boto3()
            self._executor = ThreadPoolExecutor(max_workers=self.config.max_workers)

            # Create S3 client
            client_kwargs = {
                "service_name": "s3",
                "region_name": self.config.region_name,
                "aws_access_key_id": self.config.access_key_id,
                "aws_secret_access_key": self.config.secret_access_key,
                "use_ssl": self.config.use_ssl,
            }

            if self.config.endpoint_url:
                client_kwargs["endpoint_url"] = self.config.endpoint_url

            if not self.config.verify_ssl:
                client_kwargs["verify"] = False

            self._client = boto3.client(**client_kwargs)

            # Test connection by listing bucket
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self._executor,
                lambda: self._client.head_bucket(Bucket=self.config.bucket)
            )

            self._status = ConnectionStatus.CONNECTED
        except Exception as e:
            self._status = ConnectionStatus.ERROR
            raise RuntimeError(f"Failed to connect to S3: {e}") from e

    async def disconnect(self) -> None:
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        self._client = None
        self._status = ConnectionStatus.DISCONNECTED

    async def test_connection(self) -> ConnectionTestResult:
        """Test the S3 connection."""
        start_time = time.time()
        try:
            boto3 = self._import_boto3()

            client_kwargs = {
                "service_name": "s3",
                "region_name": self.config.region_name,
                "aws_access_key_id": self.config.access_key_id,
                "aws_secret_access_key": self.config.secret_access_key,
                "use_ssl": self.config.use_ssl,
            }

            if self.config.endpoint_url:
                client_kwargs["endpoint_url"] = self.config.endpoint_url

            if not self.config.verify_ssl:
                client_kwargs["verify"] = False

            client = boto3.client(**client_kwargs)

            # Try to access bucket
            loop = asyncio.get_event_loop()
            executor = ThreadPoolExecutor(max_workers=1)

            try:
                response = await loop.run_in_executor(
                    executor,
                    lambda: client.head_bucket(Bucket=self.config.bucket)
                )

                latency_ms = (time.time() - start_time) * 1000
                return ConnectionTestResult(
                    success=True,
                    message="Bucket accessible",
                    latency_ms=latency_ms,
                    details={
                        "bucket": self.config.bucket,
                        "endpoint": self.config.endpoint_url or "AWS S3",
                        "region": self.config.region_name,
                    }
                )
            finally:
                executor.shutdown(wait=False)

        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            error_msg = str(e)

            # Handle common errors
            if "NoSuchBucket" in error_msg:
                error_msg = f"Bucket does not exist: {self.config.bucket}"
            elif "AccessDenied" in error_msg:
                error_msg = "Access denied - check credentials and permissions"
            elif "InvalidAccessKeyId" in error_msg:
                error_msg = "Invalid access key ID"

            return ConnectionTestResult(
                success=False,
                message=f"Connection failed: {error_msg}",
                latency_ms=latency_ms,
                details={"error": str(e)}
            )

    async def list_objects(
        self,
        prefix: Optional[str] = None,
        max_keys: int = 1000,
        continuation_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        List objects in the bucket.

        Args:
            prefix: Key prefix filter (defaults to config prefix).
            max_keys: Maximum number of keys to return.
            continuation_token: Token for pagination.

        Returns:
            Dictionary with objects list and pagination info.
        """
        loop = asyncio.get_event_loop()
        use_prefix = prefix if prefix is not None else self.config.prefix

        def list_objects_sync():
            params = {
                "Bucket": self.config.bucket,
                "MaxKeys": max_keys,
            }
            if use_prefix:
                params["Prefix"] = use_prefix
            if continuation_token:
                params["ContinuationToken"] = continuation_token

            return self._client.list_objects_v2(**params)

        response = await loop.run_in_executor(self._executor, list_objects_sync)

        objects = []
        for obj in response.get("Contents", []):
            objects.append({
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj["LastModified"].isoformat(),
                "etag": obj.get("ETag", "").strip('"'),
                "storage_class": obj.get("StorageClass", "STANDARD"),
            })

        return {
            "objects": objects,
            "is_truncated": response.get("IsTruncated", False),
            "next_token": response.get("NextContinuationToken"),
            "key_count": response.get("KeyCount", len(objects)),
        }

    async def read_object(
        self,
        key: str,
        range_bytes: Optional[tuple[int, int]] = None
    ) -> bytes:
        """
        Read an object from S3.

        Args:
            key: Object key.
            range_bytes: Optional byte range (start, end) for partial read.

        Returns:
            Object content as bytes.
        """
        loop = asyncio.get_event_loop()

        def read_sync():
            params = {"Bucket": self.config.bucket, "Key": key}
            if range_bytes:
                params["Range"] = f"bytes={range_bytes[0]}-{range_bytes[1]}"

            response = self._client.get_object(**params)
            return response["Body"].read()

        return await loop.run_in_executor(self._executor, read_sync)

    async def read_object_stream(
        self,
        key: str,
        chunk_size: int = 8192
    ) -> AsyncIterator[bytes]:
        """
        Stream an object from S3.

        Args:
            key: Object key.
            chunk_size: Size of each chunk.

        Yields:
            Chunks of object data.
        """
        loop = asyncio.get_event_loop()

        def get_streaming_body():
            response = self._client.get_object(
                Bucket=self.config.bucket,
                Key=key
            )
            return response["Body"]

        body = await loop.run_in_executor(self._executor, get_streaming_body)

        while True:
            chunk = await loop.run_in_executor(
                self._executor,
                lambda: body.read(chunk_size)
            )
            if not chunk:
                break
            yield chunk

    async def get_object_metadata(self, key: str) -> Dict[str, Any]:
        """
        Get metadata for an object.

        Args:
            key: Object key.

        Returns:
            Object metadata.
        """
        loop = asyncio.get_event_loop()

        def head_sync():
            return self._client.head_object(
                Bucket=self.config.bucket,
                Key=key
            )

        response = await loop.run_in_executor(self._executor, head_sync)

        return {
            "key": key,
            "content_type": response.get("ContentType"),
            "content_length": response.get("ContentLength"),
            "last_modified": response.get("LastModified").isoformat() if response.get("LastModified") else None,
            "etag": response.get("ETag", "").strip('"'),
            "metadata": response.get("Metadata", {}),
        }

    async def fetch_schema(self, source: Optional[str] = None) -> List[DataSchema]:
        """
        Fetch schema information for S3 objects.

        For S3, schema is inferred from file extensions and metadata.
        CSV and Parquet files will have their schemas extracted.

        Args:
            source: Optional object key. If None, returns schemas for common data files.

        Returns:
            List of DataSchema objects.
        """
        schemas = []

        if source:
            keys = [source]
        else:
            # List data files
            result = await self.list_objects(max_keys=100)
            data_extensions = {".csv", ".parquet", ".json", ".jsonl"}
            keys = [
                obj["key"] for obj in result["objects"]
                if any(obj["key"].lower().endswith(ext) for ext in data_extensions)
            ]

        for key in keys:
            try:
                metadata = await self.get_object_metadata(key)
                extension = key.lower().split(".")[-1] if "." in key else ""

                fields = [
                    SchemaField(
                        name="content",
                        data_type=self._get_content_type(extension),
                        nullable=False,
                    )
                ]

                schemas.append(DataSchema(
                    name=key.split("/")[-1],
                    fields=fields,
                    metadata={
                        "key": key,
                        "content_type": metadata.get("content_type"),
                        "content_length": metadata.get("content_length"),
                        "extension": extension,
                    }
                ))
            except Exception:
                continue

        return schemas

    def _get_content_type(self, extension: str) -> str:
        """Map file extension to content type."""
        type_map = {
            "csv": "text/csv",
            "json": "application/json",
            "jsonl": "application/jsonlines",
            "parquet": "application/parquet",
            "txt": "text/plain",
            "xml": "application/xml",
            "avro": "application/avro",
        }
        return type_map.get(extension, "application/octet-stream")

    async def fetch_sample(
        self,
        source: str,
        limit: int = 100
    ) -> SampleData:
        """
        Fetch sample data from an S3 object.

        Supports CSV and JSON files. For other formats, returns raw content info.

        Args:
            source: Object key.
            limit: Maximum number of rows for CSV/JSON.

        Returns:
            SampleData with schema and rows.
        """
        import json
        import csv
        from io import StringIO

        content = await self.read_object(source)
        extension = source.lower().split(".")[-1] if "." in source else ""

        if extension == "csv":
            # Parse CSV
            text = content.decode("utf-8")
            reader = csv.DictReader(StringIO(text))
            rows = []
            field_names = reader.fieldnames or []

            for i, row in enumerate(reader):
                if i >= limit:
                    break
                rows.append(row)

            fields = [
                SchemaField(name=name, data_type="string", nullable=True)
                for name in field_names
            ]

            return SampleData(
                schema=DataSchema(
                    name=source.split("/")[-1],
                    fields=fields,
                    metadata={"key": source, "format": "csv"}
                ),
                rows=rows,
                sample_size=len(rows)
            )

        elif extension in ("json", "jsonl"):
            # Parse JSON
            text = content.decode("utf-8")

            if extension == "jsonl":
                # JSON Lines format
                rows = []
                for line in text.strip().split("\n")[:limit]:
                    if line:
                        rows.append(json.loads(line))
            else:
                data = json.loads(text)
                if isinstance(data, list):
                    rows = data[:limit]
                else:
                    rows = [data]

            # Infer fields from first row
            if rows:
                fields = [
                    SchemaField(
                        name=k,
                        data_type=self._infer_json_type(v),
                        nullable=True
                    )
                    for k, v in rows[0].items()
                ]
            else:
                fields = []

            return SampleData(
                schema=DataSchema(
                    name=source.split("/")[-1],
                    fields=fields,
                    metadata={"key": source, "format": extension}
                ),
                rows=rows,
                sample_size=len(rows)
            )

        else:
            # Return metadata for other formats
            metadata = await self.get_object_metadata(source)

            return SampleData(
                schema=DataSchema(
                    name=source.split("/")[-1],
                    fields=[
                        SchemaField(name="content", data_type="binary", nullable=False)
                    ],
                    metadata={
                        "key": source,
                        "content_type": metadata.get("content_type"),
                        "content_length": metadata.get("content_length"),
                    }
                ),
                rows=[{"content_length": metadata.get("content_length")}],
                sample_size=1
            )

    def _infer_json_type(self, value: Any) -> str:
        """Infer type from a JSON value."""
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

    async def write_object(
        self,
        key: str,
        data: bytes,
        content_type: Optional[str] = None,
        metadata: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Write an object to S3.

        Args:
            key: Object key.
            data: Object content.
            content_type: MIME type.
            metadata: User metadata.

        Returns:
            Response metadata.
        """
        loop = asyncio.get_event_loop()

        def put_sync():
            params = {
                "Bucket": self.config.bucket,
                "Key": key,
                "Body": data,
            }
            if content_type:
                params["ContentType"] = content_type
            if metadata:
                params["Metadata"] = metadata

            return self._client.put_object(**params)

        response = await loop.run_in_executor(self._executor, put_sync)

        return {
            "key": key,
            "etag": response.get("ETag", "").strip('"'),
            "version_id": response.get("VersionId"),
        }

    async def delete_object(self, key: str) -> bool:
        """
        Delete an object from S3.

        Args:
            key: Object key.

        Returns:
            True if successful.
        """
        loop = asyncio.get_event_loop()

        def delete_sync():
            self._client.delete_object(
                Bucket=self.config.bucket,
                Key=key
            )
            return True

        return await loop.run_in_executor(self._executor, delete_sync)

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600,
        http_method: str = "GET"
    ) -> str:
        """
        Generate a presigned URL for an object.

        Args:
            key: Object key.
            expires_in: URL expiration time in seconds.
            http_method: HTTP method (GET or PUT).

        Returns:
            Presigned URL.
        """
        loop = asyncio.get_event_loop()

        def generate_sync():
            client_method = "get_object" if http_method == "GET" else "put_object"
            return self._client.generate_presigned_url(
                client_method,
                Params={"Bucket": self.config.bucket, "Key": key},
                ExpiresIn=expires_in
            )

        return await loop.run_in_executor(self._executor, generate_sync)
