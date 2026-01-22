"""
Ontology client stub for context integration.

This module provides stub implementations for ontology operations.
The actual implementation would integrate with the forge-ontology package.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel


class OntologyProperty(BaseModel):
    """A property in an ontology object type."""

    name: str
    type: str  # 'string', 'number', 'boolean', 'date', 'object', 'array'
    description: str | None = None
    required: bool = False
    indexed: bool = False


class OntologyLink(BaseModel):
    """A link type between ontology objects."""

    name: str
    source_type: str
    target_type: str
    description: str | None = None
    cardinality: str = "many"  # 'one', 'many'


class OntologyObjectType(BaseModel):
    """An object type in the ontology."""

    name: str
    description: str | None = None
    properties: list[OntologyProperty] = []
    primary_key: str = "id"


class OntologySchema(BaseModel):
    """The schema of an ontology."""

    id: str
    name: str
    description: str | None = None
    object_types: list[OntologyObjectType] = []
    link_types: list[OntologyLink] = []
    version: int = 1


@dataclass
class OntologyObject:
    """An object instance from the ontology."""

    id: str
    object_type: str
    ontology_id: str
    properties: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        """Convert to JSON string."""
        import json

        return json.dumps(
            {
                "id": self.id,
                "object_type": self.object_type,
                "ontology_id": self.ontology_id,
                "properties": self.properties,
            }
        )

    def get(self, property_name: str, default: Any = None) -> Any:
        """Get a property value."""
        return self.properties.get(property_name, default)


class OntologyClient(ABC):
    """
    Abstract client for ontology operations.

    This defines the interface that the actual ontology client
    (from forge-ontology) should implement.
    """

    @abstractmethod
    async def get_schema(self, ontology_id: str) -> OntologySchema:
        """Get the schema for an ontology."""
        ...

    @abstractmethod
    async def get_object(
        self,
        ontology_id: str,
        object_type: str,
        object_id: str,
    ) -> OntologyObject | None:
        """Get a specific object from the ontology."""
        ...

    @abstractmethod
    async def search(
        self,
        ontology_id: str,
        object_type: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[OntologyObject]:
        """Search for objects in the ontology."""
        ...

    @abstractmethod
    async def traverse(
        self,
        ontology_id: str,
        object_type: str,
        object_id: str,
        link_type: str,
    ) -> list[OntologyObject]:
        """Traverse links from an object to related objects."""
        ...


class StubOntologyClient(OntologyClient):
    """
    Stub ontology client for testing and development.

    Returns empty/mock data for all operations.
    """

    def __init__(self):
        self._schemas: dict[str, OntologySchema] = {}
        self._objects: dict[str, dict[str, OntologyObject]] = {}

    async def get_schema(self, ontology_id: str) -> OntologySchema:
        """Get the schema for an ontology."""
        if ontology_id in self._schemas:
            return self._schemas[ontology_id]

        # Return empty schema
        return OntologySchema(
            id=ontology_id,
            name=f"Ontology {ontology_id}",
            description="Stub ontology schema",
        )

    async def get_object(
        self,
        ontology_id: str,
        object_type: str,
        object_id: str,
    ) -> OntologyObject | None:
        """Get a specific object from the ontology."""
        key = f"{ontology_id}:{object_type}:{object_id}"
        return self._objects.get(key)

    async def search(
        self,
        ontology_id: str,
        object_type: str,
        filters: dict[str, Any] | None = None,
        limit: int = 10,
    ) -> list[OntologyObject]:
        """Search for objects in the ontology."""
        # Return empty list in stub
        return []

    async def traverse(
        self,
        ontology_id: str,
        object_type: str,
        object_id: str,
        link_type: str,
    ) -> list[OntologyObject]:
        """Traverse links from an object to related objects."""
        # Return empty list in stub
        return []

    # Helper methods for testing

    def add_schema(self, schema: OntologySchema) -> None:
        """Add a schema to the stub."""
        self._schemas[schema.id] = schema

    def add_object(self, obj: OntologyObject) -> None:
        """Add an object to the stub."""
        key = f"{obj.ontology_id}:{obj.object_type}:{obj.id}"
        self._objects[key] = obj
