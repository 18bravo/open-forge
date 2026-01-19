## 7. Detailed Work Packages

---

### STREAM 1: Infrastructure (Agent CC-01)

**Duration**: Weeks 1-2
**Dependencies**: None
**Outputs**: Running infrastructure, Docker configs, scripts

#### Work Package S1-WP1: Database Infrastructure

**Objective**: Set up all database infrastructure with proper schemas.

**Files to Create**:
```
infrastructure/
├── docker/
│   ├── Dockerfile.postgres      # PostgreSQL + pgvector + AGE
│   ├── Dockerfile.redis
│   ├── init-scripts/
│   │   ├── 01-extensions.sql    # Enable extensions
│   │   ├── 02-schemas.sql       # Create schemas
│   │   ├── 03-age-setup.sql     # Initialize AGE graph
│   │   └── 04-seed-data.sql     # Seed data for testing
│   └── redis.conf
├── docker-compose.yml
├── docker-compose.dev.yml
└── docker-compose.test.yml
```

**PostgreSQL Setup Requirements**:
```sql
-- 01-extensions.sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS age;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

LOAD 'age';
SET search_path = ag_catalog, "$user", public;

-- 02-schemas.sql
CREATE SCHEMA IF NOT EXISTS engagements;
CREATE SCHEMA IF NOT EXISTS ontology;
CREATE SCHEMA IF NOT EXISTS pipelines;
CREATE SCHEMA IF NOT EXISTS agents;
CREATE SCHEMA IF NOT EXISTS audit;

-- Core tables
CREATE TABLE engagements.engagements (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    customer_id VARCHAR(255) NOT NULL,
    customer_name VARCHAR(255) NOT NULL,
    current_phase VARCHAR(50) NOT NULL,
    status VARCHAR(50) NOT NULL,
    state JSONB NOT NULL DEFAULT '{}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE engagements.checkpoints (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID REFERENCES engagements.engagements(id),
    thread_id VARCHAR(255) NOT NULL,
    checkpoint_data JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE agents.registry (
    agent_id VARCHAR(255) PRIMARY KEY,
    agent_name VARCHAR(255) NOT NULL,
    description TEXT,
    version VARCHAR(50) NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE audit.agent_executions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    engagement_id UUID,
    agent_id VARCHAR(255),
    input_data JSONB,
    output_data JSONB,
    status VARCHAR(50),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT
);

-- 03-age-setup.sql
SELECT create_graph('ontology_graph');
```

**Docker Compose**:
```yaml
# docker-compose.yml
version: '3.8'

services:
  postgres:
    build:
      context: ./infrastructure/docker
      dockerfile: Dockerfile.postgres
    environment:
      POSTGRES_DB: autonomous_fde
      POSTGRES_USER: ${POSTGRES_USER:-fde}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-fdepass}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infrastructure/docker/init-scripts:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U fde -d autonomous_fde"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
      - ./infrastructure/docker/redis.conf:/usr/local/etc/redis/redis.conf
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  minio:
    image: minio/minio:latest
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: ${MINIO_USER:-minioadmin}
      MINIO_ROOT_PASSWORD: ${MINIO_PASSWORD:-minioadmin}
    ports:
      - "9000:9000"
      - "9001:9001"
    volumes:
      - minio_data:/data
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:9000/minio/health/live"]
      interval: 10s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
  redis_data:
  minio_data:
```

**Acceptance Criteria**:
- [ ] `docker compose up` starts all services
- [ ] PostgreSQL accessible with all extensions loaded
- [ ] AGE graph created and queryable
- [ ] Redis accepting connections
- [ ] MinIO console accessible
- [ ] Health checks passing for all services

---

#### Work Package S1-WP2: Development Environment

**Objective**: Set up development tooling and scripts.

**Files to Create**:
```
Makefile
pyproject.toml
.env.example
.gitignore
infrastructure/
└── scripts/
    ├── setup-dev.sh
    ├── reset-db.sh
    ├── run-tests.sh
    └── generate-types.sh
```

**Makefile**:
```makefile
.PHONY: help setup infra-up infra-down test lint format

help:
	@echo "Available commands:"
	@echo "  setup        - Set up development environment"
	@echo "  infra-up     - Start infrastructure services"
	@echo "  infra-down   - Stop infrastructure services"
	@echo "  test         - Run all tests"
	@echo "  test-unit    - Run unit tests"
	@echo "  test-int     - Run integration tests"
	@echo "  lint         - Run linters"
	@echo "  format       - Format code"

setup:
	./infrastructure/scripts/setup-dev.sh

infra-up:
	docker compose up -d
	@echo "Waiting for services to be healthy..."
	@sleep 10
	docker compose ps

infra-down:
	docker compose down

infra-test:
	@echo "Testing PostgreSQL..."
	docker compose exec postgres pg_isready
	@echo "Testing Redis..."
	docker compose exec redis redis-cli ping
	@echo "Testing MinIO..."
	curl -s http://localhost:9000/minio/health/live
	@echo "All services healthy!"

test: test-unit test-int

test-unit:
	pytest tests/unit -v

test-int:
	pytest tests/integration -v

test-core:
	pytest tests/unit/core -v
	pytest tests/integration/core -v

test-agents:
	pytest tests/unit/agents -v
	pytest tests/integration/agents -v

test-orchestration:
	pytest tests/unit/orchestration -v
	pytest tests/integration/orchestration -v

e2e-test:
	pytest tests/e2e -v

lint:
	ruff check .
	mypy .

format:
	ruff format .
	isort .
```

**pyproject.toml**:
```toml
[project]
name = "autonomous-fde-platform"
version = "0.1.0"
description = "AI-powered platform replacing Forward Deployed Engineer functions"
requires-python = ">=3.11"
dependencies = [
    # Core
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    
    # LLM & Agents
    "langchain>=0.3",
    "langchain-anthropic>=0.3",
    "langgraph>=0.2",
    "langsmith>=0.1",
    
    # Data
    "polars>=1.0",
    "sqlalchemy>=2.0",
    "asyncpg>=0.29",
    "redis>=5.0",
    "minio>=7.0",
    
    # Pipeline
    "dagster>=1.7",
    "dagster-postgres>=0.23",
    
    # API
    "fastapi>=0.110",
    "uvicorn>=0.27",
    "websockets>=12.0",
    "strawberry-graphql>=0.220",
    
    # Utilities
    "httpx>=0.27",
    "pyyaml>=6.0",
    "jinja2>=3.1",
    "python-multipart>=0.0.9",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.0",
    "ruff>=0.3",
    "mypy>=1.8",
    "isort>=5.13",
    "pre-commit>=3.6",
]

[tool.ruff]
line-length = 100
target-version = "py311"

[tool.mypy]
python_version = "3.11"
strict = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

---

### STREAM 2a: Ontology Engine (Agent CC-02)

**Duration**: Weeks 2-5
**Dependencies**: S1 (Infrastructure)
**Outputs**: Complete ontology engine with compiler

#### Work Package S2a-WP1: Ontology Parser

**Objective**: Parse LinkML-extended YAML into internal representation.

**Files to Create**:
```
core/ontology/
├── __init__.py
├── models.py           # Pydantic models for ontology
├── parser.py           # YAML parser
├── validator.py        # Schema validation
└── exceptions.py       # Custom exceptions
```

**models.py**:
```python
"""
Ontology data models.
Implements: packages/shared-types/python/ontology_interface.py
"""
from pydantic import BaseModel, Field, field_validator
from typing import List, Dict, Any, Optional
from enum import Enum
import re

class PropertyType(Enum):
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    DECIMAL = "decimal"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    ARRAY = "array"
    OBJECT = "object"
    UUID = "uuid"

class Cardinality(Enum):
    ONE_TO_ONE = "1:1"
    ONE_TO_MANY = "1:N"
    MANY_TO_ONE = "N:1"
    MANY_TO_MANY = "N:M"

class PropertyDefinition(BaseModel):
    """Definition of a single property."""
    name: str
    property_type: PropertyType
    description: Optional[str] = None
    required: bool = False
    is_identifier: bool = False
    is_unique: bool = False
    pattern: Optional[str] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    enum_values: Optional[List[str]] = None
    default_value: Optional[Any] = None
    array_item_type: Optional[PropertyType] = None
    
    @field_validator('pattern')
    @classmethod
    def validate_pattern(cls, v):
        if v:
            try:
                re.compile(v)
            except re.error:
                raise ValueError(f"Invalid regex pattern: {v}")
        return v

class ComputedProperty(BaseModel):
    """Definition of a computed/derived property."""
    name: str
    expression: str  # Expression to compute value
    return_type: PropertyType
    description: Optional[str] = None
    dependencies: List[str] = []  # Properties this depends on

class RelationshipDefinition(BaseModel):
    """Definition of a relationship between object types."""
    name: str
    description: Optional[str] = None
    source_type: str
    target_type: str
    cardinality: Cardinality
    inverse_name: Optional[str] = None
    edge_properties: List[PropertyDefinition] = []
    required: bool = False

class ActionParameter(BaseModel):
    """Parameter for an action type."""
    name: str
    parameter_type: PropertyType
    description: Optional[str] = None
    required: bool = True
    default_value: Optional[Any] = None

class ActionDefinition(BaseModel):
    """Definition of an action that can be performed."""
    name: str
    description: str
    target_type: str
    parameters: List[ActionParameter] = []
    preconditions: List[str] = []  # Validation expressions
    effects: List[str] = []  # What this action does
    requires_approval: bool = False
    audit_log: bool = True

class ObjectTypeDefinition(BaseModel):
    """Definition of an object type (entity)."""
    name: str
    description: Optional[str] = None
    properties: List[PropertyDefinition] = []
    computed_properties: List[ComputedProperty] = []
    relationships: List[RelationshipDefinition] = []
    actions: List[ActionDefinition] = []
    
    @property
    def identifier_property(self) -> Optional[PropertyDefinition]:
        """Get the identifier property."""
        for prop in self.properties:
            if prop.is_identifier:
                return prop
        return None

class OntologyDefinition(BaseModel):
    """Complete ontology definition."""
    id: str
    name: str
    version: str
    description: Optional[str] = None
    prefixes: Dict[str, str] = {}
    object_types: List[ObjectTypeDefinition] = []
    global_relationships: List[RelationshipDefinition] = []
    global_actions: List[ActionDefinition] = []
    enums: Dict[str, List[str]] = {}
    
    def get_object_type(self, name: str) -> Optional[ObjectTypeDefinition]:
        """Get object type by name."""
        for ot in self.object_types:
            if ot.name == name:
                return ot
        return None
    
    def get_all_relationships(self) -> List[RelationshipDefinition]:
        """Get all relationships from all object types."""
        rels = list(self.global_relationships)
        for ot in self.object_types:
            rels.extend(ot.relationships)
        return rels
```

**parser.py**:
```python
"""
YAML parser for ontology definitions.
"""
import yaml
from typing import Any, Dict
from .models import (
    OntologyDefinition, ObjectTypeDefinition, PropertyDefinition,
    RelationshipDefinition, ActionDefinition, PropertyType, Cardinality,
    ComputedProperty, ActionParameter
)
from .exceptions import OntologyParseError

class OntologyParser:
    """Parser for LinkML-extended ontology YAML."""
    
    def parse(self, yaml_content: str) -> OntologyDefinition:
        """Parse YAML string into OntologyDefinition."""
        try:
            data = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise OntologyParseError(f"Invalid YAML: {e}")
        
        return self._parse_ontology(data)
    
    def parse_file(self, file_path: str) -> OntologyDefinition:
        """Parse YAML file into OntologyDefinition."""
        with open(file_path, 'r') as f:
            return self.parse(f.read())
    
    def _parse_ontology(self, data: Dict[str, Any]) -> OntologyDefinition:
        """Parse top-level ontology structure."""
        # Parse object types (classes in LinkML)
        object_types = []
        for name, class_def in data.get('classes', {}).items():
            object_types.append(self._parse_object_type(name, class_def))
        
        # Parse enums
        enums = {}
        for name, enum_def in data.get('enums', {}).items():
            if 'permissible_values' in enum_def:
                enums[name] = list(enum_def['permissible_values'].keys())
            else:
                enums[name] = enum_def.get('values', [])
        
        return OntologyDefinition(
            id=data.get('id', 'default'),
            name=data.get('name', 'Untitled Ontology'),
            version=data.get('version', '1.0.0'),
            description=data.get('description'),
            prefixes=data.get('prefixes', {}),
            object_types=object_types,
            enums=enums,
        )
    
    def _parse_object_type(
        self, 
        name: str, 
        data: Dict[str, Any]
    ) -> ObjectTypeDefinition:
        """Parse an object type definition."""
        # Parse properties (attributes in LinkML)
        properties = []
        for prop_name, prop_def in data.get('attributes', {}).items():
            properties.append(self._parse_property(prop_name, prop_def))
        
        # Parse relationships
        relationships = []
        for rel_name, rel_def in data.get('relationships', {}).items():
            relationships.append(
                self._parse_relationship(rel_name, rel_def, name)
            )
        
        # Parse computed properties
        computed = []
        for comp_name, comp_def in data.get('computed', {}).items():
            computed.append(self._parse_computed(comp_name, comp_def))
        
        # Parse actions
        actions = []
        for action_name, action_def in data.get('actions', {}).items():
            actions.append(self._parse_action(action_name, action_def, name))
        
        return ObjectTypeDefinition(
            name=name,
            description=data.get('description'),
            properties=properties,
            computed_properties=computed,
            relationships=relationships,
            actions=actions,
        )
    
    def _parse_property(
        self, 
        name: str, 
        data: Dict[str, Any]
    ) -> PropertyDefinition:
        """Parse a property definition."""
        range_type = data.get('range', 'string')
        property_type = self._map_range_to_type(range_type)
        
        return PropertyDefinition(
            name=name,
            property_type=property_type,
            description=data.get('description'),
            required=data.get('required', False),
            is_identifier=data.get('identifier', False),
            is_unique=data.get('unique', False),
            pattern=data.get('pattern'),
            min_value=data.get('minimum_value'),
            max_value=data.get('maximum_value'),
            min_length=data.get('minimum_length'),
            max_length=data.get('maximum_length'),
            default_value=data.get('default'),
        )
    
    def _parse_relationship(
        self,
        name: str,
        data: Dict[str, Any],
        source_type: str
    ) -> RelationshipDefinition:
        """Parse a relationship definition."""
        cardinality_str = data.get('cardinality', '0..*')
        cardinality = self._map_cardinality(cardinality_str)
        
        # Parse edge properties
        edge_props = []
        for prop_data in data.get('edge_properties', []):
            if isinstance(prop_data, dict):
                for prop_name, prop_type in prop_data.items():
                    edge_props.append(PropertyDefinition(
                        name=prop_name,
                        property_type=self._map_range_to_type(prop_type),
                    ))
        
        return RelationshipDefinition(
            name=name,
            description=data.get('description'),
            source_type=source_type,
            target_type=data.get('range', 'unknown'),
            cardinality=cardinality,
            inverse_name=data.get('inverse'),
            edge_properties=edge_props,
            required=data.get('required', False),
        )
    
    def _parse_action(
        self,
        name: str,
        data: Dict[str, Any],
        target_type: str
    ) -> ActionDefinition:
        """Parse an action definition."""
        parameters = []
        for param in data.get('parameters', []):
            if isinstance(param, dict):
                for param_name, param_type in param.items():
                    parameters.append(ActionParameter(
                        name=param_name,
                        parameter_type=self._map_range_to_type(param_type),
                    ))
        
        return ActionDefinition(
            name=name,
            description=data.get('description', ''),
            target_type=target_type,
            parameters=parameters,
            preconditions=data.get('preconditions', []),
            effects=data.get('effects', []),
            requires_approval=data.get('requires_approval', False),
            audit_log=data.get('audit_log', True),
        )
    
    def _map_range_to_type(self, range_str: str) -> PropertyType:
        """Map LinkML range to PropertyType."""
        mapping = {
            'string': PropertyType.STRING,
            'str': PropertyType.STRING,
            'integer': PropertyType.INTEGER,
            'int': PropertyType.INTEGER,
            'float': PropertyType.FLOAT,
            'decimal': PropertyType.DECIMAL,
            'boolean': PropertyType.BOOLEAN,
            'bool': PropertyType.BOOLEAN,
            'datetime': PropertyType.DATETIME,
            'date': PropertyType.DATE,
            'time': PropertyType.TIME,
            'uuid': PropertyType.UUID,
        }
        return mapping.get(range_str.lower(), PropertyType.STRING)
    
    def _map_cardinality(self, card_str: str) -> Cardinality:
        """Map cardinality string to enum."""
        if card_str in ('1', '1..1'):
            return Cardinality.ONE_TO_ONE
        elif card_str in ('1..*', '1..n'):
            return Cardinality.ONE_TO_MANY
        elif card_str in ('*..1', 'n..1'):
            return Cardinality.MANY_TO_ONE
        else:
            return Cardinality.MANY_TO_MANY
    
    def _parse_computed(
        self,
        name: str,
        data: Dict[str, Any]
    ) -> ComputedProperty:
        """Parse a computed property."""
        return ComputedProperty(
            name=name,
            expression=data.get('expression', ''),
            return_type=self._map_range_to_type(data.get('range', 'string')),
            description=data.get('description'),
        )
```

**Acceptance Criteria**:
- [ ] Parse valid LinkML YAML without errors
- [ ] Extract all object types with properties
- [ ] Extract all relationships
- [ ] Extract all actions
- [ ] Handle missing optional fields gracefully
- [ ] Raise clear errors for invalid YAML

---

#### Work Package S2a-WP2: Ontology Compiler

**Objective**: Compile ontology to all target artifacts.

**Files to Create**:
```
core/ontology/
├── compiler/
│   ├── __init__.py
│   ├── base.py              # Base compiler class
│   ├── sql_compiler.py      # SQL DDL generation
│   ├── cypher_compiler.py   # Cypher DDL for AGE
│   ├── python_compiler.py   # Pydantic models
│   ├── typescript_compiler.py
│   ├── graphql_compiler.py
│   └── openapi_compiler.py
├── templates/
│   ├── sql/
│   │   ├── create_table.sql.j2
│   │   ├── create_index.sql.j2
│   │   └── create_edge_table.sql.j2
│   ├── python/
│   │   ├── pydantic_model.py.j2
│   │   └── pydantic_validators.py.j2
│   ├── typescript/
│   │   └── types.ts.j2
│   └── graphql/
│       └── schema.graphql.j2
└── engine.py                # Main engine combining all
```

**engine.py (Main Ontology Engine)**:
```python
"""
Main ontology engine - combines parser, validator, and compilers.
Implements: BaseOntologyEngine from shared interfaces.
"""
from typing import List, Dict, Any, Optional
from .models import OntologyDefinition, CompiledArtifacts
from .parser import OntologyParser
from .validator import OntologyValidator
from .compiler import (
    SQLCompiler, CypherCompiler, PythonCompiler,
    TypeScriptCompiler, GraphQLCompiler, OpenAPICompiler
)
from .exceptions import OntologyError

class OntologyEngine:
    """
    Main ontology engine for the Autonomous FDE platform.
    Handles parsing, validation, compilation, and diffing.
    """
    
    def __init__(self):
        self.parser = OntologyParser()
        self.validator = OntologyValidator()
        self.compilers = {
            'sql': SQLCompiler(),
            'cypher': CypherCompiler(),
            'python': PythonCompiler(),
            'typescript': TypeScriptCompiler(),
            'graphql': GraphQLCompiler(),
            'openapi': OpenAPICompiler(),
        }
    
    def parse(self, yaml_content: str) -> OntologyDefinition:
        """Parse YAML into OntologyDefinition."""
        return self.parser.parse(yaml_content)
    
    def validate(self, ontology: OntologyDefinition) -> List[str]:
        """
        Validate ontology definition.
        Returns list of error messages (empty if valid).
        """
        return self.validator.validate(ontology)
    
    def compile(
        self,
        ontology: OntologyDefinition,
        targets: Optional[List[str]] = None
    ) -> CompiledArtifacts:
        """
        Compile ontology to target artifacts.
        
        Args:
            ontology: Parsed ontology definition
            targets: List of targets to compile (default: all)
                    Options: sql, cypher, python, typescript, graphql, openapi
        
        Returns:
            CompiledArtifacts with all generated code
        """
        if targets is None:
            targets = list(self.compilers.keys())
        
        # Validate first
        errors = self.validate(ontology)
        if errors:
            raise OntologyError(f"Validation failed: {errors}")
        
        # Compile each target
        results = {}
        for target in targets:
            if target in self.compilers:
                results[target] = self.compilers[target].compile(ontology)
        
        return CompiledArtifacts(
            sql_ddl=results.get('sql', ''),
            cypher_ddl=results.get('cypher', ''),
            python_models=results.get('python', ''),
            typescript_types=results.get('typescript', ''),
            graphql_schema=results.get('graphql', ''),
            json_schemas=self._generate_json_schemas(ontology),
            openapi_spec=results.get('openapi', {}),
            pydantic_validators=self._generate_validators(ontology),
        )
    
    def diff(
        self,
        old_ontology: OntologyDefinition,
        new_ontology: OntologyDefinition
    ) -> Dict[str, Any]:
        """
        Compute differences between two ontology versions.
        Used for migration planning.
        """
        diff = {
            'added_types': [],
            'removed_types': [],
            'modified_types': [],
            'added_relationships': [],
            'removed_relationships': [],
            'added_properties': {},
            'removed_properties': {},
            'type_changes': {},
        }
        
        old_types = {ot.name for ot in old_ontology.object_types}
        new_types = {ot.name for ot in new_ontology.object_types}
        
        diff['added_types'] = list(new_types - old_types)
        diff['removed_types'] = list(old_types - new_types)
        
        # Check modified types
        common_types = old_types & new_types
        for type_name in common_types:
            old_ot = old_ontology.get_object_type(type_name)
            new_ot = new_ontology.get_object_type(type_name)
            
            if old_ot and new_ot:
                type_diff = self._diff_object_type(old_ot, new_ot)
                if type_diff:
                    diff['modified_types'].append({
                        'type': type_name,
                        'changes': type_diff
                    })
        
        return diff
    
    def migrate(
        self,
        from_version: OntologyDefinition,
        to_version: OntologyDefinition
    ) -> str:
        """
        Generate SQL migration script between versions.
        """
        diff = self.diff(from_version, to_version)
        
        migration_sql = []
        migration_sql.append("-- Auto-generated migration script")
        migration_sql.append(f"-- From: {from_version.version}")
        migration_sql.append(f"-- To: {to_version.version}")
        migration_sql.append("")
        
        # Add new tables
        for type_name in diff['added_types']:
            ot = to_version.get_object_type(type_name)
            if ot:
                migration_sql.append(
                    self.compilers['sql'].compile_object_type(ot)
                )
        
        # Add new columns
        for type_name, props in diff.get('added_properties', {}).items():
            for prop in props:
                migration_sql.append(
                    f"ALTER TABLE {type_name.lower()} "
                    f"ADD COLUMN {prop['name']} {prop['sql_type']};"
                )
        
        # Handle removed columns (commented out for safety)
        for type_name, props in diff.get('removed_properties', {}).items():
            for prop in props:
                migration_sql.append(
                    f"-- ALTER TABLE {type_name.lower()} "
                    f"DROP COLUMN {prop['name']}; -- MANUAL REVIEW REQUIRED"
                )
        
        return '\n'.join(migration_sql)
    
    def _diff_object_type(self, old_ot, new_ot) -> Optional[Dict[str, Any]]:
        """Compute diff between two object type versions."""
        changes = {}
        
        old_props = {p.name: p for p in old_ot.properties}
        new_props = {p.name: p for p in new_ot.properties}
        
        added = set(new_props.keys()) - set(old_props.keys())
        removed = set(old_props.keys()) - set(new_props.keys())
        
        if added:
            changes['added_properties'] = list(added)
        if removed:
            changes['removed_properties'] = list(removed)
        
        # Check for type changes
        for prop_name in set(old_props.keys()) & set(new_props.keys()):
            if old_props[prop_name].property_type != new_props[prop_name].property_type:
                changes.setdefault('type_changes', {})[prop_name] = {
                    'from': old_props[prop_name].property_type.value,
                    'to': new_props[prop_name].property_type.value,
                }
        
        return changes if changes else None
    
    def _generate_json_schemas(
        self, 
        ontology: OntologyDefinition
    ) -> Dict[str, Dict[str, Any]]:
        """Generate JSON Schema for each object type."""
        schemas = {}
        for ot in ontology.object_types:
            schemas[ot.name] = self._object_type_to_json_schema(ot)
        return schemas
    
    def _object_type_to_json_schema(self, ot) -> Dict[str, Any]:
        """Convert object type to JSON Schema."""
        type_mapping = {
            'string': 'string',
            'integer': 'integer',
            'float': 'number',
            'decimal': 'number',
            'boolean': 'boolean',
            'datetime': 'string',
            'date': 'string',
            'uuid': 'string',
        }
        
        properties = {}
        required = []
        
        for prop in ot.properties:
            prop_schema = {
                'type': type_mapping.get(prop.property_type.value, 'string')
            }
            if prop.description:
                prop_schema['description'] = prop.description
            if prop.pattern:
                prop_schema['pattern'] = prop.pattern
            if prop.min_value is not None:
                prop_schema['minimum'] = prop.min_value
            if prop.max_value is not None:
                prop_schema['maximum'] = prop.max_value
            if prop.enum_values:
                prop_schema['enum'] = prop.enum_values
                
            properties[prop.name] = prop_schema
            
            if prop.required:
                required.append(prop.name)
        
        return {
            '$schema': 'http://json-schema.org/draft-07/schema#',
            'title': ot.name,
            'description': ot.description,
            'type': 'object',
            'properties': properties,
            'required': required,
        }
    
    def _generate_validators(self, ontology: OntologyDefinition) -> str:
        """Generate Pydantic validators for all object types."""
        return self.compilers['python'].compile_validators(ontology)
```

**Acceptance Criteria**:
- [ ] Compile ontology to valid SQL DDL
- [ ] Compile ontology to valid Cypher DDL
- [ ] Compile ontology to valid Pydantic models
- [ ] Compile ontology to valid TypeScript types
- [ ] Compile ontology to valid GraphQL schema
- [ ] Generate valid JSON schemas
- [ ] Diff two ontology versions correctly
- [ ] Generate migration scripts

---

### STREAM 2b: Pipeline Engine (Agent CC-03)

**Duration**: Weeks 2-5
**Dependencies**: S1 (Infrastructure)
**Outputs**: Dagster-based pipeline engine

#### Work Package S2b-WP1: Pipeline Definitions

**Objective**: Create the pipeline framework with Dagster.

**Files to Create**:
```
core/pipeline/
├── __init__.py
├── models.py           # Pipeline data models
├── engine.py           # Main pipeline engine
├── assets/
│   ├── __init__.py
│   ├── source_assets.py     # Source data assets
│   ├── transform_assets.py  # Transformation assets
│   └── ontology_assets.py   # Ontology sync assets
├── resources/
│   ├── __init__.py
│   ├── database.py     # Database resources
│   ├── connectors.py   # Data connector resources
│   └── graph.py        # Graph database resource
├── generators/
│   ├── __init__.py
│   └── asset_generator.py   # Generate assets from ontology
└── definitions.py      # Dagster definitions
```

**engine.py**:
```python
"""
Pipeline engine implementation using Dagster.
Implements: BasePipelineEngine from shared interfaces.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dagster import (
    Definitions, 
    AssetSelection,
    define_asset_job,
    RunRequest,
    RunConfig,
)
from .models import PipelineDefinition, PipelineRun, PipelineStatus, AssetDefinition
from .generators.asset_generator import AssetGenerator

class PipelineEngine:
    """
    Pipeline engine for the Autonomous FDE platform.
    Wraps Dagster for pipeline management.
    """
    
    def __init__(self, dagster_instance):
        self.instance = dagster_instance
        self.asset_generator = AssetGenerator()
        self._pipelines: Dict[str, PipelineDefinition] = {}
    
    async def create_pipeline(
        self, 
        definition: PipelineDefinition
    ) -> str:
        """Create a new pipeline from definition."""
        pipeline_id = definition.pipeline_id or str(uuid.uuid4())
        
        # Generate Dagster assets from definition
        assets = []
        for asset_def in definition.assets:
            asset = self.asset_generator.generate_asset(asset_def)
            assets.append(asset)
        
        # Create job
        job = define_asset_job(
            name=f"pipeline_{pipeline_id}",
            selection=AssetSelection.assets(*[a.key for a in assets]),
            description=definition.description,
        )
        
        # Store definition
        self._pipelines[pipeline_id] = definition
        
        return pipeline_id
    
    async def update_pipeline(
        self,
        pipeline_id: str,
        definition: PipelineDefinition
    ) -> None:
        """Update an existing pipeline."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        # Regenerate assets
        self._pipelines[pipeline_id] = definition
        # Dagster handles asset versioning automatically
    
    async def run_pipeline(
        self,
        pipeline_id: str,
        config_overrides: Optional[Dict[str, Any]] = None
    ) -> PipelineRun:
        """Execute a pipeline."""
        if pipeline_id not in self._pipelines:
            raise ValueError(f"Pipeline {pipeline_id} not found")
        
        run_id = str(uuid.uuid4())
        
        # Build run config
        run_config = RunConfig()
        if config_overrides:
            # Apply overrides
            pass
        
        # Submit to Dagster
        dagster_run = self.instance.submit_run(
            pipeline_name=f"pipeline_{pipeline_id}",
            run_config=run_config,
        )
        
        return PipelineRun(
            run_id=run_id,
            pipeline_id=pipeline_id,
            status=PipelineStatus.RUNNING,
            started_at=datetime.now(),
            completed_at=None,
            error_message=None,
            asset_results={},
        )
    
    async def get_run_status(self, run_id: str) -> PipelineRun:
        """Get status of a pipeline run."""
        dagster_run = self.instance.get_run_by_id(run_id)
        
        status_mapping = {
            'STARTED': PipelineStatus.RUNNING,
            'SUCCESS': PipelineStatus.SUCCESS,
            'FAILURE': PipelineStatus.FAILED,
            'CANCELED': PipelineStatus.CANCELLED,
        }
        
        return PipelineRun(
            run_id=run_id,
            pipeline_id=dagster_run.pipeline_name.replace('pipeline_', ''),
            status=status_mapping.get(
                dagster_run.status.value, 
                PipelineStatus.PENDING
            ),
            started_at=dagster_run.start_time,
            completed_at=dagster_run.end_time,
            error_message=dagster_run.failure_reason,
            asset_results={},
        )
    
    async def cancel_run(self, run_id: str) -> None:
        """Cancel a running pipeline."""
        self.instance.cancel_run(run_id)
    
    async def generate_pipeline_from_ontology(
        self,
        ontology: 'OntologyDefinition',
        source_mappings: List[Dict[str, Any]]
    ) -> PipelineDefinition:
        """
        Auto-generate a complete pipeline from ontology definition.
        This is a key feature for replacing FDE work.
        """
        assets = []
        
        # Generate source assets for each data source
        for mapping in source_mappings:
            source_asset = self.asset_generator.generate_source_asset(
                mapping['source_name'],
                mapping['connector_config'],
                mapping['query']
            )
            assets.append(source_asset)
        
        # Generate transform assets for each object type
        for obj_type in ontology.object_types:
            # Find the source mapping for this type
            type_mapping = next(
                (m for m in source_mappings 
                 if m.get('target_type') == obj_type.name),
                None
            )
            
            if type_mapping:
                transform_asset = self.asset_generator.generate_transform_asset(
                    obj_type,
                    type_mapping
                )
                assets.append(transform_asset)
        
        # Generate graph sync asset
        graph_asset = self.asset_generator.generate_graph_sync_asset(
            ontology,
            [a.asset_id for a in assets if 'transform' in a.asset_id]
        )
        assets.append(graph_asset)
        
        return PipelineDefinition(
            pipeline_id=f"ontology_{ontology.name}_{ontology.version}",
            name=f"Pipeline for {ontology.name}",
            description=f"Auto-generated pipeline for ontology {ontology.name}",
            assets=assets,
            schedule="0 * * * *",  # Hourly by default
            config={
                'ontology_id': ontology.id,
                'ontology_version': ontology.version,
            }
        )
```

---

### STREAM 3: Orchestration Layer (Agent CC-05)

**Duration**: Weeks 4-8
**Dependencies**: S1, S2
**Outputs**: LangGraph orchestrator with state management

#### Work Package S3-WP1: LangGraph Workflow

**Objective**: Implement the main orchestration workflow.

**Files to Create**:
```
orchestration/
├── __init__.py
├── langgraph/
│   ├── __init__.py
│   ├── graphs/
│   │   ├── __init__.py
│   │   ├── main_workflow.py      # Main engagement workflow
│   │   ├── discovery_subgraph.py # Discovery phase
│   │   ├── data_foundation_subgraph.py
│   │   ├── application_subgraph.py
│   │   └── deployment_subgraph.py
│   ├── nodes/
│   │   ├── __init__.py
│   │   ├── phase_nodes.py        # Phase execution nodes
│   │   ├── approval_nodes.py     # Human approval nodes
│   │   └── utility_nodes.py      # Utility nodes
│   └── edges/
│       ├── __init__.py
│       └── routing.py            # Edge routing logic
├── state/
│   ├── __init__.py
│   ├── manager.py                # State management
│   └── persistence.py            # PostgreSQL persistence
├── registry/
│   ├── __init__.py
│   └── agent_registry.py         # Agent discovery/registration
└── orchestrator.py               # Main orchestrator class
```

**orchestrator.py (Main Implementation)**:
```python
"""
Main deployment orchestrator.
Implements: BaseOrchestrator from shared interfaces.
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_anthropic import ChatAnthropic

from packages.shared_types.python.orchestrator_interface import (
    EngagementState, EngagementPhase, EngagementStatus,
    OrchestratorCommand, OrchestratorResponse, BaseOrchestrator
)
from .langgraph.graphs.main_workflow import build_main_workflow
from .state.manager import StateManager
from .registry.agent_registry import AgentRegistry

class DeploymentOrchestrator(BaseOrchestrator):
    """
    Main orchestrator for FDE engagements.
    Uses LangGraph for workflow management with PostgreSQL checkpointing.
    """
    
    def __init__(
        self,
        db_connection_string: str,
        llm_model: str = "claude-sonnet-4-20250514"
    ):
        self.db_connection_string = db_connection_string
        self.llm = ChatAnthropic(model=llm_model, temperature=0)
        
        # Initialize components
        self.checkpointer = PostgresSaver.from_conn_string(db_connection_string)
        self.state_manager = StateManager(db_connection_string)
        self.agent_registry = AgentRegistry()
        
        # Build the workflow graph
        self.graph = build_main_workflow(
            llm=self.llm,
            agent_registry=self.agent_registry,
            checkpointer=self.checkpointer
        )
    
    async def start_engagement(
        self,
        customer_id: str,
        customer_name: str,
        initial_context: str,
        target_completion: Optional[datetime] = None
    ) -> OrchestratorResponse:
        """Start a new FDE engagement."""
        
        # Generate engagement ID
        engagement_id = f"eng_{customer_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create initial state
        initial_state = EngagementState(
            engagement_id=engagement_id,
            customer_id=customer_id,
            customer_name=customer_name,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            target_completion=target_completion,
            current_phase=EngagementPhase.DISCOVERY,
            status=EngagementStatus.ACTIVE,
            problem_statement=initial_context,
        )
        
        # Save initial state
        await self.state_manager.save_state(initial_state)
        
        # Start the workflow
        config = {"configurable": {"thread_id": engagement_id}}
        
        try:
            result = await self.graph.ainvoke(
                initial_state.model_dump(),
                config
            )
            
            return OrchestratorResponse(
                success=True,
                engagement_id=engagement_id,
                current_state=EngagementState(**result),
                message="Engagement started successfully",
                next_expected_action=self._get_next_action(result)
            )
        except Exception as e:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=initial_state,
                message=f"Failed to start engagement: {str(e)}",
                next_expected_action=None
            )
    
    async def continue_engagement(
        self,
        engagement_id: str,
        human_input: Optional[Dict[str, Any]] = None
    ) -> OrchestratorResponse:
        """Continue an existing engagement."""
        
        config = {"configurable": {"thread_id": engagement_id}}
        
        # Get current state
        state = await self.graph.aget_state(config)
        
        if state is None:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=None,
                message="Engagement not found",
                next_expected_action=None
            )
        
        # Add human input if provided
        if human_input:
            state.values["human_interactions"].append({
                "timestamp": datetime.now().isoformat(),
                "type": human_input.get("type", "input"),
                "content": human_input
            })
        
        # Continue execution
        try:
            result = await self.graph.ainvoke(state.values, config)
            
            # Update state in database
            updated_state = EngagementState(**result)
            await self.state_manager.save_state(updated_state)
            
            return OrchestratorResponse(
                success=True,
                engagement_id=engagement_id,
                current_state=updated_state,
                message="Engagement continued",
                next_expected_action=self._get_next_action(result)
            )
        except Exception as e:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=EngagementState(**state.values),
                message=f"Error continuing engagement: {str(e)}",
                next_expected_action=None
            )
    
    async def get_state(self, engagement_id: str) -> EngagementState:
        """Get current engagement state."""
        return await self.state_manager.get_state(engagement_id)
    
    async def pause_engagement(
        self, 
        engagement_id: str
    ) -> OrchestratorResponse:
        """Pause an engagement."""
        state = await self.state_manager.get_state(engagement_id)
        
        if state is None:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=None,
                message="Engagement not found",
                next_expected_action=None
            )
        
        state.status = EngagementStatus.PAUSED
        state.updated_at = datetime.now()
        await self.state_manager.save_state(state)
        
        return OrchestratorResponse(
            success=True,
            engagement_id=engagement_id,
            current_state=state,
            message="Engagement paused",
            next_expected_action="Resume engagement to continue"
        )
    
    async def resume_engagement(
        self, 
        engagement_id: str
    ) -> OrchestratorResponse:
        """Resume a paused engagement."""
        state = await self.state_manager.get_state(engagement_id)
        
        if state is None:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=None,
                message="Engagement not found",
                next_expected_action=None
            )
        
        if state.status != EngagementStatus.PAUSED:
            return OrchestratorResponse(
                success=False,
                engagement_id=engagement_id,
                current_state=state,
                message="Engagement is not paused",
                next_expected_action=None
            )
        
        state.status = EngagementStatus.ACTIVE
        state.updated_at = datetime.now()
        await self.state_manager.save_state(state)
        
        # Continue execution
        return await self.continue_engagement(engagement_id)
    
    async def submit_approval(
        self,
        engagement_id: str,
        approval_id: str,
        decision: str,
        feedback: Optional[str] = None
    ) -> OrchestratorResponse:
        """Submit a human approval decision."""
        
        human_input = {
            "type": "approval",
            "approval_id": approval_id,
            "decision": decision,
            "feedback": feedback,
            "submitted_at": datetime.now().isoformat()
        }
        
        return await self.continue_engagement(engagement_id, human_input)
    
    def _get_next_action(self, state: Dict[str, Any]) -> Optional[str]:
        """Determine the next expected action based on state."""
        status = state.get("status")
        phase = state.get("current_phase")
        
        if status == EngagementStatus.WAITING_APPROVAL.value:
            return "Awaiting human approval"
        
        action_map = {
            EngagementPhase.DISCOVERY.value: "Gathering requirements",
            EngagementPhase.DATA_FOUNDATION.value: "Building data foundation",
            EngagementPhase.APPLICATION.value: "Building applications",
            EngagementPhase.DEPLOYMENT.value: "Deploying solution",
            EngagementPhase.SUPPORT.value: "Providing support",
        }
        
        return action_map.get(phase, "Processing")
```

*Continued in Part 3...*