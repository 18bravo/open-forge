# Track A: Forge Connect - Connector Framework Design

**Date:** 2026-01-20
**Status:** Approved
**Track:** A (Connectors)
**Goal:** Build connector framework supporting 200+ data sources with batch, CDC, streaming, and reverse ETL

---

## Executive Summary

Forge Connect is the connector framework enabling Open Forge to ingest data from 200+ sources, perform CDC/streaming, and write back to operational systems. The design uses a hybrid plugin architecture with category-specific base classes, supporting all sync modes required for operational applications.

### Key Decisions

1. **Hybrid Architecture**: Category base classes (SQL, Streaming, API) loaded as plugins
2. **All Sync Modes**: Batch, Incremental, CDC, Streaming, and Reverse ETL
3. **Hybrid Secrets**: DB stores config metadata, external secrets manager stores credentials
4. **Phased Delivery**: A1 (Core+SQL) → A2 (Warehouses) → A3 (Streaming+ERP) → A4 (CRM+NoSQL+API)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FORGE CONNECT                                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    CONNECTOR REGISTRY                            │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │   SQL    │ │Warehouse │ │Streaming │ │   API    │  ...      │    │
│  │  │ Plugins  │ │ Plugins  │ │ Plugins  │ │ Plugins  │           │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │    │
│  │       │            │            │            │                  │    │
│  │       └────────────┴────────────┴────────────┘                  │    │
│  │                          │                                       │    │
│  │                          ▼                                       │    │
│  │              ┌───────────────────────┐                          │    │
│  │              │   Category Base       │                          │    │
│  │              │   Classes             │                          │    │
│  │              │  ┌─────┐ ┌─────────┐  │                          │    │
│  │              │  │ SQL │ │Streaming│  │                          │    │
│  │              │  │Base │ │  Base   │  │                          │    │
│  │              │  └─────┘ └─────────┘  │                          │    │
│  │              └───────────┬───────────┘                          │    │
│  │                          │                                       │    │
│  │                          ▼                                       │    │
│  │              ┌───────────────────────┐                          │    │
│  │              │   BaseConnector       │                          │    │
│  │              │   (Abstract)          │                          │    │
│  │              └───────────────────────┘                          │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────────┐   │
│  │   Sync Engine    │  │  Secrets Manager │  │   Schema Discovery   │   │
│  │  (Batch/CDC/     │  │  (Vault/AWS SM/  │  │   & Profiler         │   │
│  │   Stream/Write)  │  │   K8s Secrets)   │  │                      │   │
│  └──────────────────┘  └──────────────────┘  └──────────────────────┘   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Forge Pipelines   │
                         │   (Dagster Assets)  │
                         └─────────────────────┘
```

**Key Design Principles:**
- **Plugin-based discovery**: Connectors register themselves at startup via entry points
- **Category inheritance**: SQL, Streaming, API connectors share base logic
- **Secrets abstraction**: Credentials never stored in connector code
- **Sync engine decoupling**: Same connector works for batch, CDC, and streaming

---

## Connector Class Hierarchy

### Base Classes

```python
# packages/connectors-core/src/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator, Optional
from pydantic import BaseModel

class ConnectorConfig(BaseModel):
    """Base configuration - extended by each connector"""
    connector_type: str
    name: str
    secrets_ref: Optional[str] = None  # Reference to external secrets

class SyncState(BaseModel):
    """Checkpoint for incremental syncs"""
    cursor: Optional[str] = None
    last_sync_at: Optional[datetime] = None
    metadata: dict = {}

class SchemaObject(BaseModel):
    """Discovered table/object/endpoint"""
    name: str
    schema_name: Optional[str] = None
    object_type: str  # 'table', 'view', 'collection', 'endpoint'
    columns: list[ColumnInfo]
    primary_key: Optional[list[str]] = None
    supports_cdc: bool = False
    supports_incremental: bool = False

class BaseConnector(ABC):
    """Abstract base for all connectors"""

    connector_type: str  # e.g., 'postgresql', 'snowflake'
    category: str        # e.g., 'sql', 'warehouse', 'streaming'

    @abstractmethod
    async def test_connection(self) -> ConnectionTestResult: ...

    @abstractmethod
    async def discover_schema(self) -> list[SchemaObject]: ...

    @abstractmethod
    async def get_sample_data(self, object_name: str, limit: int = 100) -> DataFrame: ...

    @abstractmethod
    async def read_batch(
        self,
        object_name: str,
        state: Optional[SyncState] = None
    ) -> AsyncIterator[RecordBatch]: ...

    @abstractmethod
    async def get_sync_state(self, object_name: str) -> SyncState: ...

    @abstractmethod
    async def health_check(self) -> HealthStatus: ...

    # Optional capabilities (raise NotImplementedError if not supported)
    async def profile_data(self, object_name: str) -> DataProfile: ...
    async def read_cdc(self, object_name: str, state: SyncState) -> AsyncIterator[CDCEvent]: ...
    async def read_stream(self, object_name: str) -> AsyncIterator[Record]: ...
    async def write_batch(self, object_name: str, records: list[Record]) -> WriteResult: ...
    async def write_record(self, object_name: str, record: Record) -> WriteResult: ...
```

### Category Base Classes

```python
# packages/connectors-core/src/categories/sql.py

class SQLConnector(BaseConnector):
    """Base for SQL databases (PostgreSQL, MySQL, etc.)"""

    category = "sql"

    # Shared SQL capabilities
    async def execute_query(self, query: str) -> DataFrame: ...
    async def get_table_ddl(self, table_name: str) -> str: ...
    async def get_row_count(self, table_name: str) -> int: ...

    # Default implementations using SQL
    async def discover_schema(self) -> list[SchemaObject]:
        # Query information_schema (overridable)
        ...

    async def read_batch(self, object_name: str, state: Optional[SyncState] = None):
        # SELECT with cursor-based pagination (overridable)
        ...


# packages/connectors-core/src/categories/streaming.py

class StreamingConnector(BaseConnector):
    """Base for streaming sources (Kafka, Kinesis, etc.)"""

    category = "streaming"

    # Shared streaming capabilities
    async def get_consumer_group_lag(self) -> dict[str, int]: ...
    async def commit_offset(self, offset: Offset) -> None: ...
    async def seek_to_timestamp(self, timestamp: datetime) -> None: ...

    # Streaming sources must implement read_stream
    @abstractmethod
    async def read_stream(self, topic: str) -> AsyncIterator[Record]: ...
```

---

## Plugin Registry & Discovery

### Connector Registration

```python
# packages/connectors-core/src/registry.py

from typing import Type
import importlib.metadata

class ConnectorRegistry:
    """Central registry for all connector plugins"""

    _connectors: dict[str, Type[BaseConnector]] = {}
    _categories: dict[str, list[str]] = {}

    @classmethod
    def register(cls, connector_type: str, category: str):
        """Decorator to register a connector"""
        def decorator(connector_class: Type[BaseConnector]):
            cls._connectors[connector_type] = connector_class
            cls._categories.setdefault(category, []).append(connector_type)
            connector_class.connector_type = connector_type
            connector_class.category = category
            return connector_class
        return decorator

    @classmethod
    def get(cls, connector_type: str) -> Type[BaseConnector]:
        if connector_type not in cls._connectors:
            raise ConnectorNotFoundError(f"Unknown connector: {connector_type}")
        return cls._connectors[connector_type]

    @classmethod
    def list_all(cls) -> list[ConnectorInfo]:
        return [
            ConnectorInfo(
                type=ct,
                category=cc.category,
                capabilities=cc.get_capabilities()
            )
            for ct, cc in cls._connectors.items()
        ]

    @classmethod
    def discover_plugins(cls):
        """Auto-discover connectors via entry points"""
        for ep in importlib.metadata.entry_points(group='forge.connectors'):
            ep.load()  # Loading triggers @register decorator
```

### Connector Plugin Example

```python
# packages/connectors-sql/src/postgresql.py

from connectors_core import ConnectorRegistry, SQLConnector
import asyncpg

@ConnectorRegistry.register('postgresql', 'sql')
class PostgreSQLConnector(SQLConnector):
    """PostgreSQL connector with CDC support via logical replication"""

    class Config(SQLConnectorConfig):
        host: str
        port: int = 5432
        database: str
        schema: str = 'public'
        ssl_mode: str = 'prefer'
        # secrets_ref points to external secrets for user/password

    def __init__(self, config: Config, secrets: SecretsProvider):
        self.config = config
        self._secrets = secrets
        self._pool: Optional[asyncpg.Pool] = None

    async def _get_pool(self) -> asyncpg.Pool:
        if not self._pool:
            creds = await self._secrets.get(self.config.secrets_ref)
            self._pool = await asyncpg.create_pool(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=creds['username'],
                password=creds['password'],
                ssl=self.config.ssl_mode
            )
        return self._pool

    async def test_connection(self) -> ConnectionTestResult:
        try:
            pool = await self._get_pool()
            async with pool.acquire() as conn:
                await conn.fetchval('SELECT 1')
            return ConnectionTestResult(success=True)
        except Exception as e:
            return ConnectionTestResult(success=False, error=str(e))

    async def read_cdc(self, table: str, state: SyncState) -> AsyncIterator[CDCEvent]:
        """CDC via logical replication slots"""
        # Implementation using pg_logical or wal2json
        ...

    @classmethod
    def get_capabilities(cls) -> list[str]:
        return ['batch', 'incremental', 'cdc', 'write_batch', 'write_record']
```

### Entry Point Configuration

```toml
# packages/connectors-sql/pyproject.toml

[project.entry-points."forge.connectors"]
postgresql = "connectors_sql.postgresql:PostgreSQLConnector"
mysql = "connectors_sql.mysql:MySQLConnector"
sqlserver = "connectors_sql.sqlserver:SQLServerConnector"
oracle = "connectors_sql.oracle:OracleConnector"
```

---

## Secrets Management

### Secrets Provider Interface

```python
# packages/connectors-core/src/secrets/base.py

from abc import ABC, abstractmethod

class SecretsProvider(ABC):
    """Abstract interface for secrets backends"""

    @abstractmethod
    async def get(self, secret_ref: str) -> dict[str, str]:
        """Retrieve secret by reference"""
        ...

    @abstractmethod
    async def set(self, secret_ref: str, values: dict[str, str]) -> None:
        """Store secret (for OAuth token refresh, etc.)"""
        ...

    @abstractmethod
    async def delete(self, secret_ref: str) -> None:
        """Remove secret"""
        ...

    @abstractmethod
    async def exists(self, secret_ref: str) -> bool:
        """Check if secret exists"""
        ...
```

### Backend Implementations

```python
# packages/connectors-core/src/secrets/vault.py

class VaultSecretsProvider(SecretsProvider):
    """HashiCorp Vault backend"""

    def __init__(self, vault_addr: str, auth_method: str, mount_path: str = "secret"):
        self.client = hvac.Client(url=vault_addr)
        self._authenticate(auth_method)
        self.mount = mount_path

    async def get(self, secret_ref: str) -> dict[str, str]:
        response = self.client.secrets.kv.v2.read_secret_version(
            path=secret_ref, mount_point=self.mount
        )
        return response['data']['data']


# packages/connectors-core/src/secrets/aws.py

class AWSSecretsProvider(SecretsProvider):
    """AWS Secrets Manager backend"""

    def __init__(self, region: str = None):
        self.client = boto3.client('secretsmanager', region_name=region)

    async def get(self, secret_ref: str) -> dict[str, str]:
        response = self.client.get_secret_value(SecretId=secret_ref)
        return json.loads(response['SecretString'])


# packages/connectors-core/src/secrets/kubernetes.py

class K8sSecretsProvider(SecretsProvider):
    """Kubernetes Secrets backend"""

    def __init__(self, namespace: str = "default"):
        config.load_incluster_config()
        self.v1 = client.CoreV1Api()
        self.namespace = namespace

    async def get(self, secret_ref: str) -> dict[str, str]:
        secret = self.v1.read_namespaced_secret(secret_ref, self.namespace)
        return {k: base64.b64decode(v).decode() for k, v in secret.data.items()}


# packages/connectors-core/src/secrets/env.py

class EnvSecretsProvider(SecretsProvider):
    """Environment variables backend (for simple deployments)"""

    async def get(self, secret_ref: str) -> dict[str, str]:
        prefix = f"FORGE_SECRET_{secret_ref.upper()}_"
        return {
            k.replace(prefix, '').lower(): v
            for k, v in os.environ.items()
            if k.startswith(prefix)
        }
```

### Secrets Factory

```python
# packages/connectors-core/src/secrets/factory.py

class SecretsFactory:
    """Create secrets provider based on configuration"""

    @staticmethod
    def create(config: SecretsConfig) -> SecretsProvider:
        match config.backend:
            case "vault":
                return VaultSecretsProvider(
                    vault_addr=config.vault_addr,
                    auth_method=config.vault_auth_method
                )
            case "aws":
                return AWSSecretsProvider(region=config.aws_region)
            case "kubernetes":
                return K8sSecretsProvider(namespace=config.k8s_namespace)
            case "env":
                return EnvSecretsProvider()
            case _:
                raise ValueError(f"Unknown secrets backend: {config.backend}")
```

---

## Sync Engine

### Sync Modes

```python
# packages/connectors-core/src/sync/engine.py

from enum import Enum
from dataclasses import dataclass

class SyncMode(Enum):
    FULL = "full"              # Complete extraction
    INCREMENTAL = "incremental" # Cursor-based incremental
    CDC = "cdc"                # Change data capture
    STREAMING = "streaming"    # Continuous stream

@dataclass
class SyncJob:
    id: str
    connection_id: str
    connector_type: str
    object_name: str
    mode: SyncMode
    destination: str           # Iceberg table path
    state: Optional[SyncState] = None
    schedule: Optional[str] = None  # Cron expression

class SyncEngine:
    """Orchestrates data sync across all modes"""

    def __init__(
        self,
        registry: ConnectorRegistry,
        secrets: SecretsProvider,
        state_store: StateStore,
        writer: DataWriter
    ):
        self.registry = registry
        self.secrets = secrets
        self.state_store = state_store
        self.writer = writer

    async def execute_sync(self, job: SyncJob) -> SyncResult:
        """Execute a sync job"""
        connector = await self._create_connector(job)
        state = await self.state_store.get(job.id) or SyncState()

        match job.mode:
            case SyncMode.FULL:
                return await self._sync_full(connector, job, state)
            case SyncMode.INCREMENTAL:
                return await self._sync_incremental(connector, job, state)
            case SyncMode.CDC:
                return await self._sync_cdc(connector, job, state)
            case SyncMode.STREAMING:
                return await self._sync_streaming(connector, job, state)

    async def _sync_full(self, connector, job, state) -> SyncResult:
        """Full table extraction"""
        records_written = 0
        async for batch in connector.read_batch(job.object_name):
            await self.writer.write(job.destination, batch)
            records_written += len(batch)

        new_state = await connector.get_sync_state(job.object_name)
        await self.state_store.save(job.id, new_state)

        return SyncResult(
            success=True,
            records_written=records_written,
            mode=SyncMode.FULL
        )

    async def _sync_incremental(self, connector, job, state) -> SyncResult:
        """Incremental extraction using cursor"""
        records_written = 0
        async for batch in connector.read_batch(job.object_name, state=state):
            await self.writer.write(job.destination, batch, mode='append')
            records_written += len(batch)
            # Checkpoint periodically
            if records_written % 10000 == 0:
                await self.state_store.save(job.id, batch.state)

        return SyncResult(success=True, records_written=records_written)

    async def _sync_cdc(self, connector, job, state) -> SyncResult:
        """Change data capture sync"""
        changes = {'inserts': 0, 'updates': 0, 'deletes': 0}

        async for event in connector.read_cdc(job.object_name, state):
            match event.operation:
                case 'INSERT':
                    await self.writer.write(job.destination, event.record, mode='append')
                    changes['inserts'] += 1
                case 'UPDATE':
                    await self.writer.merge(job.destination, event.record, event.key)
                    changes['updates'] += 1
                case 'DELETE':
                    await self.writer.delete(job.destination, event.key)
                    changes['deletes'] += 1

            await self.state_store.save(job.id, event.state)

        return SyncResult(success=True, changes=changes)
```

### Reverse ETL (Writeback)

```python
# packages/connectors-core/src/sync/writeback.py

@dataclass
class WritebackJob:
    id: str
    connection_id: str
    connector_type: str
    target_object: str       # e.g., 'salesforce.Contact'
    source_query: str        # Query against ontology
    mapping: dict[str, str]  # Ontology field → target field
    mode: WriteMode          # 'upsert', 'insert', 'update'
    batch_size: int = 100

class WritebackEngine:
    """Push data back to source systems"""

    async def execute_writeback(self, job: WritebackJob) -> WritebackResult:
        connector = await self._create_connector(job)

        # Query ontology for records to write
        records = await self.ontology.query(job.source_query)

        # Map ontology fields to target fields
        mapped_records = [self._map_record(r, job.mapping) for r in records]

        # Write in batches
        results = {'success': 0, 'failed': 0, 'errors': []}
        for batch in chunked(mapped_records, job.batch_size):
            try:
                result = await connector.write_batch(job.target_object, batch)
                results['success'] += result.success_count
                results['failed'] += result.failure_count
                results['errors'].extend(result.errors)
            except Exception as e:
                results['errors'].append(str(e))
                results['failed'] += len(batch)

        return WritebackResult(**results)
```

---

## Package Structure

```
packages/connectors-core/           # Foundation (Phase A1)
├── src/
│   ├── __init__.py
│   ├── base.py                    # BaseConnector, SyncState, etc.
│   ├── registry.py                # ConnectorRegistry
│   ├── categories/
│   │   ├── sql.py                 # SQLConnector base
│   │   ├── warehouse.py           # WarehouseConnector base
│   │   ├── streaming.py           # StreamingConnector base
│   │   ├── api.py                 # APIConnector base
│   │   └── file.py                # FileConnector base
│   ├── secrets/
│   │   ├── base.py
│   │   ├── vault.py
│   │   ├── aws.py
│   │   ├── kubernetes.py
│   │   └── env.py
│   ├── sync/
│   │   ├── engine.py              # SyncEngine
│   │   ├── writeback.py           # WritebackEngine
│   │   ├── state.py               # StateStore
│   │   └── scheduler.py           # Cron scheduling
│   ├── discovery/
│   │   ├── schema.py              # Schema introspection
│   │   └── profiler.py            # Data profiling
│   ├── auth/
│   │   ├── oauth.py               # OAuth2 flows
│   │   └── service_account.py
│   └── api/
│       └── routes.py              # FastAPI endpoints
├── tests/
└── pyproject.toml

packages/connectors-sql/            # SQL Databases (Phase A1)
├── src/
│   ├── __init__.py
│   ├── postgresql.py              # PostgreSQL + pgvector
│   ├── mysql.py                   # MySQL / MariaDB
│   ├── sqlserver.py               # SQL Server
│   ├── oracle.py                  # Oracle Database
│   └── common/
│       ├── query_builder.py       # SQL generation utilities
│       └── type_mapping.py        # DB type → Arrow type
├── tests/
└── pyproject.toml

packages/connectors-warehouse/      # Cloud Warehouses (Phase A2)
├── src/
│   ├── __init__.py
│   ├── snowflake.py               # Snowflake
│   ├── bigquery.py                # Google BigQuery
│   ├── redshift.py                # AWS Redshift
│   ├── databricks.py              # Databricks SQL
│   ├── synapse.py                 # Azure Synapse
│   └── common/
│       ├── pushdown.py            # Query pushdown optimization
│       └── staging.py             # Cloud staging (S3/GCS/Azure)
├── tests/
└── pyproject.toml

packages/connectors-streaming/      # Streaming (Phase A3)
├── src/
│   ├── __init__.py
│   ├── kafka.py                   # Apache Kafka
│   ├── kinesis.py                 # AWS Kinesis
│   ├── pubsub.py                  # Google Pub/Sub
│   ├── eventhub.py                # Azure Event Hub
│   ├── rabbitmq.py                # RabbitMQ
│   └── common/
│       ├── offset_manager.py      # Consumer offset tracking
│       ├── schema_registry.py     # Avro/Protobuf schemas
│       └── exactly_once.py        # Exactly-once semantics
├── tests/
└── pyproject.toml

packages/connectors-erp/            # Enterprise (Phase A3)
├── src/
│   ├── __init__.py
│   ├── sap/
│   │   ├── rfc.py                 # SAP RFC/BAPI
│   │   ├── odata.py               # SAP OData
│   │   └── hana.py                # SAP HANA direct
│   ├── oracle_ebs.py              # Oracle E-Business Suite
│   ├── netsuite.py                # NetSuite (REST/SOAP)
│   ├── dynamics365.py             # Microsoft Dynamics 365
│   └── workday.py                 # Workday
├── tests/
└── pyproject.toml

packages/connectors-crm/            # CRM Systems (Phase A4)
├── src/
│   ├── __init__.py
│   ├── salesforce.py              # Salesforce (REST + Bulk API)
│   ├── hubspot.py                 # HubSpot
│   ├── dynamics_crm.py            # Dynamics 365 CRM
│   ├── zoho.py                    # Zoho CRM
│   └── pipedrive.py               # Pipedrive
├── tests/
└── pyproject.toml

packages/connectors-nosql/          # NoSQL (Phase A4)
├── src/
│   ├── __init__.py
│   ├── mongodb.py                 # MongoDB
│   ├── cassandra.py               # Apache Cassandra
│   ├── dynamodb.py                # AWS DynamoDB
│   ├── cosmosdb.py                # Azure CosmosDB
│   ├── couchbase.py               # Couchbase
│   └── elasticsearch.py           # Elasticsearch
├── tests/
└── pyproject.toml

packages/connectors-cloud/          # Cloud Storage (Phase A1)
├── src/
│   ├── __init__.py
│   ├── s3.py                      # AWS S3
│   ├── gcs.py                     # Google Cloud Storage
│   ├── azure_blob.py              # Azure Blob Storage
│   ├── minio.py                   # MinIO
│   └── common/
│       ├── glob_pattern.py        # File pattern matching
│       └── incremental.py         # New file detection
├── tests/
└── pyproject.toml

packages/connectors-files/          # File Formats (Phase A2)
├── src/
│   ├── __init__.py
│   ├── parquet.py                 # Parquet files
│   ├── csv.py                     # CSV/TSV
│   ├── json.py                    # JSON/JSONL
│   ├── avro.py                    # Avro files
│   ├── excel.py                   # Excel (xlsx)
│   ├── xml.py                     # XML
│   └── sftp.py                    # SFTP file transfer
├── tests/
└── pyproject.toml

packages/connectors-api/            # Generic APIs (Phase A4)
├── src/
│   ├── __init__.py
│   ├── rest.py                    # Generic REST connector
│   ├── graphql.py                 # Generic GraphQL connector
│   ├── soap.py                    # SOAP/WSDL connector
│   ├── odata.py                   # OData connector
│   ├── webhook.py                 # Webhook receiver
│   └── common/
│       ├── pagination.py          # Pagination strategies
│       ├── rate_limiter.py        # Rate limiting
│       └── retry.py               # Retry with backoff
├── tests/
└── pyproject.toml
```

---

## API Endpoints

### Connector Management API

```
/api/v1/connectors/
│
├── types/
│   ├── GET    /                    # List available connector types
│   └── GET    /:type               # Get connector type details & config schema
│
├── connections/
│   ├── POST   /                    # Create new connection
│   ├── GET    /                    # List connections (paginated)
│   ├── GET    /:id                 # Get connection details
│   ├── PATCH  /:id                 # Update connection config
│   ├── DELETE /:id                 # Delete connection
│   ├── POST   /:id/test            # Test connection
│   └── GET    /:id/health          # Health check status
│
├── discovery/
│   ├── GET    /:connection_id/schema           # Discover all objects
│   ├── GET    /:connection_id/schema/:object   # Get object schema details
│   ├── GET    /:connection_id/sample/:object   # Get sample data
│   └── POST   /:connection_id/profile/:object  # Run data profiling
│
├── sync/
│   ├── POST   /jobs                # Create sync job
│   ├── GET    /jobs                # List sync jobs
│   ├── GET    /jobs/:id            # Get job details
│   ├── POST   /jobs/:id/run        # Trigger job execution
│   ├── POST   /jobs/:id/cancel     # Cancel running job
│   ├── GET    /jobs/:id/runs       # List job run history
│   └── GET    /jobs/:id/runs/:run  # Get run details & logs
│
└── writeback/
    ├── POST   /jobs                # Create writeback job
    ├── GET    /jobs                # List writeback jobs
    ├── POST   /jobs/:id/run        # Trigger writeback
    └── GET    /jobs/:id/runs       # List writeback history
```

### Request/Response Examples

```python
# POST /api/v1/connectors/connections
{
    "name": "Production PostgreSQL",
    "connector_type": "postgresql",
    "config": {
        "host": "db.example.com",
        "port": 5432,
        "database": "production",
        "schema": "public",
        "ssl_mode": "require"
    },
    "secrets_ref": "forge/connections/prod-postgres"  # Vault path
}

# Response
{
    "id": "conn_abc123",
    "name": "Production PostgreSQL",
    "connector_type": "postgresql",
    "category": "sql",
    "capabilities": ["batch", "incremental", "cdc", "write_batch"],
    "status": "pending_test",
    "created_at": "2026-01-20T10:00:00Z"
}

# POST /api/v1/connectors/sync/jobs
{
    "connection_id": "conn_abc123",
    "name": "Orders Sync",
    "objects": [
        {
            "source": "orders",
            "destination": "bronze.erp.orders",
            "mode": "incremental",
            "cursor_field": "updated_at"
        },
        {
            "source": "order_items",
            "destination": "bronze.erp.order_items",
            "mode": "cdc"
        }
    ],
    "schedule": "0 */6 * * *"  # Every 6 hours
}
```

---

## Implementation Roadmap

### Phase A1: Foundation (Week 1-3)

| Package | Deliverables | Dependencies |
|---------|--------------|--------------|
| connectors-core | BaseConnector, SQLConnector base, registry, secrets providers, sync engine | None |
| connectors-sql | PostgreSQL, MySQL connectors | connectors-core |
| connectors-cloud | S3, MinIO connectors | connectors-core |

**Acceptance Criteria A1:**
- [ ] PostgreSQL full sync working end-to-end to Iceberg
- [ ] Incremental sync with cursor checkpoint
- [ ] Connection test and schema discovery via API
- [ ] Secrets retrieved from at least one backend (env or Vault)
- [ ] 80% test coverage on core package

### Phase A2: Cloud Warehouses (Week 4-5)

| Package | Deliverables | Dependencies |
|---------|--------------|--------------|
| connectors-warehouse | Snowflake, BigQuery, Redshift | connectors-core |
| connectors-files | Parquet, CSV, SFTP | connectors-core, connectors-cloud |

**Acceptance Criteria A2:**
- [ ] Snowflake with query pushdown optimization
- [ ] BigQuery with GCS staging
- [ ] Parquet schema inference
- [ ] File arrival detection for incremental

### Phase A3: Streaming & ERP (Week 6-8)

| Package | Deliverables | Dependencies |
|---------|--------------|--------------|
| connectors-streaming | Kafka, Kinesis with exactly-once | connectors-core |
| connectors-erp | SAP RFC, Oracle EBS, NetSuite | connectors-core, connectors-api |

**Acceptance Criteria A3:**
- [ ] Kafka consumer with offset tracking
- [ ] CDC events flowing to Iceberg with merge
- [ ] SAP extracting via RFC/BAPI
- [ ] ERP writeback (reverse ETL) working

### Phase A4: CRM, NoSQL, APIs (Week 9-11)

| Package | Deliverables | Dependencies |
|---------|--------------|--------------|
| connectors-crm | Salesforce, HubSpot | connectors-core, connectors-api |
| connectors-nosql | MongoDB, DynamoDB, Elasticsearch | connectors-core |
| connectors-api | REST, GraphQL, SOAP, OData frameworks | connectors-core |

**Acceptance Criteria A4:**
- [ ] Salesforce Bulk API for large extracts
- [ ] MongoDB change streams for CDC
- [ ] Generic REST connector with pagination strategies
- [ ] Rate limiting and retry logic

---

## Connector Count by Phase

| Phase | Connectors | Cumulative |
|-------|------------|------------|
| A1 | PostgreSQL, MySQL, SQL Server, Oracle, S3, MinIO | 6 |
| A2 | Snowflake, BigQuery, Redshift, Databricks, Parquet, CSV, SFTP | 13 |
| A3 | Kafka, Kinesis, Pub/Sub, SAP, Oracle EBS, NetSuite | 19 |
| A4 | Salesforce, HubSpot, MongoDB, DynamoDB, REST, GraphQL | 25+ |

**Post-MVP Expansion:**
- Community-contributed connectors via plugin system
- Marketplace for premium/enterprise connectors
- Custom connector wizard in UI

---

## Dependencies

```toml
# packages/connectors-core/pyproject.toml

[project]
name = "forge-connectors-core"
dependencies = [
    "pydantic>=2.0",
    "pyarrow>=14.0",
    "asyncpg>=0.29",           # Async PostgreSQL
    "aiomysql>=0.2",           # Async MySQL
    "hvac>=2.0",               # HashiCorp Vault
    "boto3>=1.34",             # AWS SDK
    "kubernetes>=28.0",        # K8s client
    "croniter>=2.0",           # Cron parsing
    "structlog>=24.0",         # Logging
]

[project.optional-dependencies]
warehouse = [
    "snowflake-connector-python>=3.6",
    "google-cloud-bigquery>=3.0",
    "redshift-connector>=2.0",
]
streaming = [
    "aiokafka>=0.10",
    "amazon-kinesis-client>=2.0",
]
```

---

## Next Steps

1. **Immediate**: Begin Phase A1 implementation (connectors-core, connectors-sql)
2. **Parallel**: Track C (Forge AI) and Track B (Forge Data) can start simultaneously
3. **Integration**: Connect sync engine output to Dagster pipelines
4. **Testing**: Build connector test harness with Docker-based source databases
