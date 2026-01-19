"""
Base Pydantic models for ontology entities.
Defines the core types for representing ontology schemas.
"""
from typing import Any, Dict, List, Optional, Union
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field, field_validator


class PropertyType(str, Enum):
    """Supported property data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    DATE = "date"
    TIME = "time"
    UUID = "uuid"
    JSON = "json"
    ARRAY = "array"
    ENUM = "enum"


class Cardinality(str, Enum):
    """Relationship cardinality."""
    ONE_TO_ONE = "one_to_one"
    ONE_TO_MANY = "one_to_many"
    MANY_TO_ONE = "many_to_one"
    MANY_TO_MANY = "many_to_many"


class ConstraintType(str, Enum):
    """Types of constraints that can be applied to properties."""
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    PRIMARY_KEY = "primary_key"
    FOREIGN_KEY = "foreign_key"
    CHECK = "check"
    DEFAULT = "default"
    MIN_VALUE = "min_value"
    MAX_VALUE = "max_value"
    MIN_LENGTH = "min_length"
    MAX_LENGTH = "max_length"
    PATTERN = "pattern"
    ENUM_VALUES = "enum_values"


class Constraint(BaseModel):
    """Represents a constraint on a property or type."""
    constraint_type: ConstraintType
    value: Optional[Any] = None
    message: Optional[str] = Field(
        default=None,
        description="Custom error message for constraint violation"
    )

    model_config = {"use_enum_values": True}


class Property(BaseModel):
    """Represents a property in an ontology type."""
    name: str = Field(..., description="Property name")
    property_type: PropertyType = Field(..., description="Data type of the property")
    description: Optional[str] = Field(default=None, description="Property description")
    required: bool = Field(default=False, description="Whether the property is required")
    constraints: List[Constraint] = Field(default_factory=list, description="Property constraints")
    default_value: Optional[Any] = Field(default=None, description="Default value")
    array_item_type: Optional[PropertyType] = Field(
        default=None,
        description="Type of array items if property_type is ARRAY"
    )
    enum_values: Optional[List[str]] = Field(
        default=None,
        description="Allowed values if property_type is ENUM"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"use_enum_values": True}

    @field_validator("enum_values")
    @classmethod
    def validate_enum_values(cls, v: Optional[List[str]], info) -> Optional[List[str]]:
        """Ensure enum_values is provided when property_type is ENUM."""
        if info.data.get("property_type") == PropertyType.ENUM and not v:
            raise ValueError("enum_values must be provided for ENUM property type")
        return v


class Relationship(BaseModel):
    """Represents a relationship between ontology types."""
    name: str = Field(..., description="Relationship name")
    source_type: str = Field(..., description="Source ontology type name")
    target_type: str = Field(..., description="Target ontology type name")
    cardinality: Cardinality = Field(..., description="Relationship cardinality")
    description: Optional[str] = Field(default=None, description="Relationship description")
    inverse_name: Optional[str] = Field(
        default=None,
        description="Name of the inverse relationship"
    )
    required: bool = Field(default=False, description="Whether the relationship is required")
    properties: List[Property] = Field(
        default_factory=list,
        description="Properties on the relationship edge"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    model_config = {"use_enum_values": True}


class OntologyType(BaseModel):
    """Represents an ontology type (class/entity)."""
    name: str = Field(..., description="Type name")
    description: Optional[str] = Field(default=None, description="Type description")
    properties: List[Property] = Field(default_factory=list, description="Type properties")
    primary_key: Optional[str] = Field(default=None, description="Primary key property name")
    mixins: List[str] = Field(
        default_factory=list,
        description="List of mixin type names to inherit from"
    )
    abstract: bool = Field(default=False, description="Whether this is an abstract type")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("primary_key")
    @classmethod
    def validate_primary_key(cls, v: Optional[str], info) -> Optional[str]:
        """Validate that primary_key references an existing property."""
        if v is not None:
            properties = info.data.get("properties", [])
            property_names = [p.name if isinstance(p, Property) else p.get("name") for p in properties]
            if v not in property_names:
                raise ValueError(f"Primary key '{v}' must reference an existing property")
        return v


class OntologySchema(BaseModel):
    """Represents a complete ontology schema."""
    name: str = Field(..., description="Schema name")
    version: str = Field(..., description="Schema version (semver)")
    description: Optional[str] = Field(default=None, description="Schema description")
    namespace: str = Field(default="", description="Schema namespace/prefix")
    types: List[OntologyType] = Field(default_factory=list, description="Ontology types")
    relationships: List[Relationship] = Field(
        default_factory=list,
        description="Relationships between types"
    )
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("version")
    @classmethod
    def validate_version(cls, v: str) -> str:
        """Validate semver format."""
        import re
        pattern = r"^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?(\+[a-zA-Z0-9]+)?$"
        if not re.match(pattern, v):
            raise ValueError(f"Version '{v}' must be in semver format (e.g., 1.0.0)")
        return v

    def get_type(self, name: str) -> Optional[OntologyType]:
        """Get a type by name."""
        for t in self.types:
            if t.name == name:
                return t
        return None

    def get_relationships_for_type(self, type_name: str) -> List[Relationship]:
        """Get all relationships where the given type is the source."""
        return [r for r in self.relationships if r.source_type == type_name]

    def get_incoming_relationships(self, type_name: str) -> List[Relationship]:
        """Get all relationships where the given type is the target."""
        return [r for r in self.relationships if r.target_type == type_name]


class SchemaVersion(BaseModel):
    """Represents a versioned schema record."""
    schema_id: str = Field(..., description="Unique schema identifier")
    version: str = Field(..., description="Schema version")
    schema_content: OntologySchema = Field(..., description="The schema content")
    created_at: datetime = Field(default_factory=datetime.now)
    created_by: Optional[str] = Field(default=None, description="User who created this version")
    changelog: Optional[str] = Field(default=None, description="Description of changes")
    is_published: bool = Field(default=False, description="Whether this version is published")
    parent_version: Optional[str] = Field(
        default=None,
        description="Previous version this was derived from"
    )


class SchemaValidationError(BaseModel):
    """Represents a schema validation error."""
    path: str = Field(..., description="Path to the error location")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="error", description="error, warning, or info")


class SchemaValidationResult(BaseModel):
    """Result of schema validation."""
    is_valid: bool = Field(..., description="Whether the schema is valid")
    errors: List[SchemaValidationError] = Field(
        default_factory=list,
        description="List of validation errors"
    )
    warnings: List[SchemaValidationError] = Field(
        default_factory=list,
        description="List of validation warnings"
    )
