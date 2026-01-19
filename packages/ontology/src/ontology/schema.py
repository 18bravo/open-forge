"""
Schema management for LinkML-based ontologies.
Handles loading, saving, versioning, and validation of ontology schemas.
"""
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from datetime import datetime
import hashlib
import json
import re

import yaml
from linkml_runtime.linkml_model import SchemaDefinition, ClassDefinition, SlotDefinition
from linkml_runtime.loaders import yaml_loader
from linkml_runtime.dumpers import yaml_dumper
from linkml.validators import JsonSchemaDataValidator

from ontology.models import (
    OntologySchema,
    OntologyType,
    Property,
    PropertyType,
    Relationship,
    Cardinality,
    Constraint,
    ConstraintType,
    SchemaVersion,
    SchemaValidationError,
    SchemaValidationResult,
)


# Mapping from LinkML types to our PropertyType enum
LINKML_TYPE_MAP: Dict[str, PropertyType] = {
    "string": PropertyType.STRING,
    "integer": PropertyType.INTEGER,
    "float": PropertyType.FLOAT,
    "double": PropertyType.FLOAT,
    "boolean": PropertyType.BOOLEAN,
    "datetime": PropertyType.DATETIME,
    "date": PropertyType.DATE,
    "time": PropertyType.TIME,
    "uri": PropertyType.STRING,
    "uriorcurie": PropertyType.STRING,
    "ncname": PropertyType.STRING,
    "jsonpointer": PropertyType.STRING,
    "jsonpath": PropertyType.STRING,
}

# Reverse mapping for generating LinkML from our types
PROPERTY_TYPE_TO_LINKML: Dict[PropertyType, str] = {
    PropertyType.STRING: "string",
    PropertyType.INTEGER: "integer",
    PropertyType.FLOAT: "float",
    PropertyType.BOOLEAN: "boolean",
    PropertyType.DATETIME: "datetime",
    PropertyType.DATE: "date",
    PropertyType.TIME: "time",
    PropertyType.UUID: "string",
    PropertyType.JSON: "string",
    PropertyType.ARRAY: "string",  # Arrays are handled separately
    PropertyType.ENUM: "string",  # Enums are handled separately
}


class SchemaManager:
    """Manages LinkML schema operations including loading, saving, and versioning."""

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize the schema manager.

        Args:
            storage_path: Optional path for storing schema versions.
        """
        self.storage_path = storage_path
        self._versions: Dict[str, List[SchemaVersion]] = {}

    def load_linkml_yaml(self, path: Union[str, Path]) -> SchemaDefinition:
        """
        Load a LinkML schema from a YAML file.

        Args:
            path: Path to the YAML file.

        Returns:
            LinkML SchemaDefinition object.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not valid LinkML YAML.
        """
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Schema file not found: {path}")

        try:
            schema = yaml_loader.load(str(path), SchemaDefinition)
            return schema
        except Exception as e:
            raise ValueError(f"Invalid LinkML schema: {e}")

    def load_linkml_from_string(self, yaml_content: str) -> SchemaDefinition:
        """
        Load a LinkML schema from a YAML string.

        Args:
            yaml_content: YAML string content.

        Returns:
            LinkML SchemaDefinition object.
        """
        try:
            data = yaml.safe_load(yaml_content)
            schema = SchemaDefinition(**data)
            return schema
        except Exception as e:
            raise ValueError(f"Invalid LinkML schema: {e}")

    def save_linkml_yaml(self, schema: SchemaDefinition, path: Union[str, Path]) -> None:
        """
        Save a LinkML schema to a YAML file.

        Args:
            schema: LinkML SchemaDefinition object.
            path: Path to save the YAML file.
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        yaml_dumper.dump(schema, str(path))

    def linkml_to_yaml_string(self, schema: SchemaDefinition) -> str:
        """
        Convert a LinkML schema to a YAML string.

        Args:
            schema: LinkML SchemaDefinition object.

        Returns:
            YAML string representation.
        """
        return yaml_dumper.dumps(schema)

    def linkml_to_ontology_schema(self, linkml_schema: SchemaDefinition) -> OntologySchema:
        """
        Convert a LinkML schema to our OntologySchema model.

        Args:
            linkml_schema: LinkML SchemaDefinition object.

        Returns:
            OntologySchema object.
        """
        types: List[OntologyType] = []
        relationships: List[Relationship] = []

        # Process classes
        if linkml_schema.classes:
            for class_name, class_def in linkml_schema.classes.items():
                if class_def is None:
                    continue

                ontology_type = self._convert_class_to_type(class_name, class_def, linkml_schema)
                types.append(ontology_type)

                # Extract relationships from slots
                if class_def.attributes:
                    for slot_name, slot_def in class_def.attributes.items():
                        if slot_def and slot_def.range and slot_def.range in (linkml_schema.classes or {}):
                            rel = self._convert_slot_to_relationship(
                                class_name, slot_name, slot_def, linkml_schema
                            )
                            if rel:
                                relationships.append(rel)

        return OntologySchema(
            name=linkml_schema.name or "unnamed",
            version=getattr(linkml_schema, "version", None) or "0.1.0",
            description=linkml_schema.description,
            namespace=linkml_schema.default_prefix or "",
            types=types,
            relationships=relationships,
            metadata={
                "prefixes": dict(linkml_schema.prefixes) if linkml_schema.prefixes else {},
                "default_range": linkml_schema.default_range,
            }
        )

    def _convert_class_to_type(
        self,
        class_name: str,
        class_def: ClassDefinition,
        schema: SchemaDefinition
    ) -> OntologyType:
        """Convert a LinkML class to an OntologyType."""
        properties: List[Property] = []
        primary_key: Optional[str] = None

        # Process attributes (slots defined inline)
        if class_def.attributes:
            for slot_name, slot_def in class_def.attributes.items():
                if slot_def is None:
                    continue
                # Skip slots that reference other classes (these become relationships)
                if slot_def.range and slot_def.range in (schema.classes or {}):
                    continue

                prop = self._convert_slot_to_property(slot_name, slot_def)
                properties.append(prop)

                # Check if this is an identifier
                if slot_def.identifier:
                    primary_key = slot_name

        # Process slots referenced by the class
        if class_def.slots:
            for slot_name in class_def.slots:
                if schema.slots and slot_name in schema.slots:
                    slot_def = schema.slots[slot_name]
                    if slot_def is None:
                        continue
                    # Skip slots that reference other classes
                    if slot_def.range and slot_def.range in (schema.classes or {}):
                        continue

                    prop = self._convert_slot_to_property(slot_name, slot_def)
                    properties.append(prop)

                    if slot_def.identifier:
                        primary_key = slot_name

        return OntologyType(
            name=class_name,
            description=class_def.description,
            properties=properties,
            primary_key=primary_key,
            mixins=[str(m) for m in (class_def.mixins or [])],
            abstract=class_def.abstract or False,
            metadata={
                "class_uri": str(class_def.class_uri) if class_def.class_uri else None,
            }
        )

    def _convert_slot_to_property(self, slot_name: str, slot_def: SlotDefinition) -> Property:
        """Convert a LinkML slot to a Property."""
        # Determine property type
        range_type = slot_def.range or "string"
        property_type = LINKML_TYPE_MAP.get(range_type, PropertyType.STRING)

        # Handle multivalued slots
        if slot_def.multivalued:
            array_item_type = property_type
            property_type = PropertyType.ARRAY
        else:
            array_item_type = None

        # Build constraints
        constraints: List[Constraint] = []

        if slot_def.required:
            constraints.append(Constraint(constraint_type=ConstraintType.NOT_NULL))

        if slot_def.identifier:
            constraints.append(Constraint(constraint_type=ConstraintType.PRIMARY_KEY))

        if slot_def.minimum_value is not None:
            constraints.append(Constraint(
                constraint_type=ConstraintType.MIN_VALUE,
                value=slot_def.minimum_value
            ))

        if slot_def.maximum_value is not None:
            constraints.append(Constraint(
                constraint_type=ConstraintType.MAX_VALUE,
                value=slot_def.maximum_value
            ))

        if slot_def.pattern:
            constraints.append(Constraint(
                constraint_type=ConstraintType.PATTERN,
                value=slot_def.pattern
            ))

        return Property(
            name=slot_name,
            property_type=property_type,
            description=slot_def.description,
            required=slot_def.required or False,
            constraints=constraints,
            default_value=slot_def.ifabsent,
            array_item_type=array_item_type,
            metadata={
                "slot_uri": str(slot_def.slot_uri) if slot_def.slot_uri else None,
            }
        )

    def _convert_slot_to_relationship(
        self,
        source_class: str,
        slot_name: str,
        slot_def: SlotDefinition,
        schema: SchemaDefinition
    ) -> Optional[Relationship]:
        """Convert a LinkML slot to a Relationship if it references another class."""
        if not slot_def.range:
            return None

        target_class = slot_def.range
        if target_class not in (schema.classes or {}):
            return None

        # Determine cardinality
        if slot_def.multivalued:
            cardinality = Cardinality.ONE_TO_MANY
        else:
            cardinality = Cardinality.MANY_TO_ONE

        return Relationship(
            name=slot_name,
            source_type=source_class,
            target_type=target_class,
            cardinality=cardinality,
            description=slot_def.description,
            inverse_name=str(slot_def.inverse) if slot_def.inverse else None,
            required=slot_def.required or False,
        )

    def ontology_schema_to_linkml(self, ontology_schema: OntologySchema) -> SchemaDefinition:
        """
        Convert our OntologySchema model to a LinkML schema.

        Args:
            ontology_schema: OntologySchema object.

        Returns:
            LinkML SchemaDefinition object.
        """
        classes: Dict[str, ClassDefinition] = {}
        slots: Dict[str, SlotDefinition] = {}

        # Convert types to classes
        for ontology_type in ontology_schema.types:
            class_def = self._convert_type_to_class(ontology_type)
            classes[ontology_type.name] = class_def

        # Add relationship slots to source classes
        for rel in ontology_schema.relationships:
            slot_def = self._convert_relationship_to_slot(rel)
            slot_name = rel.name

            # Add to global slots
            slots[slot_name] = slot_def

            # Add to source class
            if rel.source_type in classes:
                if classes[rel.source_type].slots is None:
                    classes[rel.source_type].slots = []
                classes[rel.source_type].slots.append(slot_name)

        schema = SchemaDefinition(
            id=f"https://openforge.io/schemas/{ontology_schema.name}",
            name=ontology_schema.name,
            description=ontology_schema.description,
            version=ontology_schema.version,
            default_prefix=ontology_schema.namespace or ontology_schema.name,
            classes=classes,
            slots=slots,
        )

        return schema

    def _convert_type_to_class(self, ontology_type: OntologyType) -> ClassDefinition:
        """Convert an OntologyType to a LinkML ClassDefinition."""
        attributes: Dict[str, SlotDefinition] = {}

        for prop in ontology_type.properties:
            slot_def = self._convert_property_to_slot(prop, ontology_type.primary_key)
            attributes[prop.name] = slot_def

        return ClassDefinition(
            name=ontology_type.name,
            description=ontology_type.description,
            attributes=attributes,
            mixins=ontology_type.mixins if ontology_type.mixins else None,
            abstract=ontology_type.abstract,
        )

    def _convert_property_to_slot(
        self,
        prop: Property,
        primary_key: Optional[str]
    ) -> SlotDefinition:
        """Convert a Property to a LinkML SlotDefinition."""
        # Determine range
        if prop.property_type == PropertyType.ARRAY and prop.array_item_type:
            range_type = PROPERTY_TYPE_TO_LINKML.get(prop.array_item_type, "string")
            multivalued = True
        elif prop.property_type == PropertyType.ENUM:
            range_type = "string"  # Enums will need additional handling
            multivalued = False
        else:
            range_type = PROPERTY_TYPE_TO_LINKML.get(prop.property_type, "string")
            multivalued = False

        # Extract constraint values
        minimum_value = None
        maximum_value = None
        pattern = None

        for constraint in prop.constraints:
            if constraint.constraint_type == ConstraintType.MIN_VALUE:
                minimum_value = constraint.value
            elif constraint.constraint_type == ConstraintType.MAX_VALUE:
                maximum_value = constraint.value
            elif constraint.constraint_type == ConstraintType.PATTERN:
                pattern = constraint.value

        return SlotDefinition(
            name=prop.name,
            description=prop.description,
            range=range_type,
            required=prop.required,
            multivalued=multivalued,
            identifier=prop.name == primary_key,
            ifabsent=str(prop.default_value) if prop.default_value is not None else None,
            minimum_value=minimum_value,
            maximum_value=maximum_value,
            pattern=pattern,
        )

    def _convert_relationship_to_slot(self, rel: Relationship) -> SlotDefinition:
        """Convert a Relationship to a LinkML SlotDefinition."""
        multivalued = rel.cardinality in [Cardinality.ONE_TO_MANY, Cardinality.MANY_TO_MANY]

        return SlotDefinition(
            name=rel.name,
            description=rel.description,
            range=rel.target_type,
            required=rel.required,
            multivalued=multivalued,
            inverse=rel.inverse_name,
        )

    def validate_schema(self, ontology_schema: OntologySchema) -> SchemaValidationResult:
        """
        Validate an ontology schema.

        Args:
            ontology_schema: OntologySchema to validate.

        Returns:
            SchemaValidationResult with validation errors and warnings.
        """
        errors: List[SchemaValidationError] = []
        warnings: List[SchemaValidationError] = []

        type_names = {t.name for t in ontology_schema.types}

        # Validate types
        for ontology_type in ontology_schema.types:
            # Check for duplicate property names
            prop_names = [p.name for p in ontology_type.properties]
            if len(prop_names) != len(set(prop_names)):
                errors.append(SchemaValidationError(
                    path=f"types.{ontology_type.name}.properties",
                    message="Duplicate property names found",
                    severity="error"
                ))

            # Check primary key references valid property
            if ontology_type.primary_key:
                if ontology_type.primary_key not in prop_names:
                    errors.append(SchemaValidationError(
                        path=f"types.{ontology_type.name}.primary_key",
                        message=f"Primary key '{ontology_type.primary_key}' does not reference a valid property",
                        severity="error"
                    ))

            # Check mixins reference valid types
            for mixin in ontology_type.mixins:
                if mixin not in type_names:
                    errors.append(SchemaValidationError(
                        path=f"types.{ontology_type.name}.mixins",
                        message=f"Mixin '{mixin}' does not reference a valid type",
                        severity="error"
                    ))

            # Warn about types without primary keys
            if not ontology_type.primary_key and not ontology_type.abstract:
                warnings.append(SchemaValidationError(
                    path=f"types.{ontology_type.name}",
                    message="Non-abstract type should have a primary key",
                    severity="warning"
                ))

        # Validate relationships
        for rel in ontology_schema.relationships:
            if rel.source_type not in type_names:
                errors.append(SchemaValidationError(
                    path=f"relationships.{rel.name}.source_type",
                    message=f"Source type '{rel.source_type}' does not exist",
                    severity="error"
                ))

            if rel.target_type not in type_names:
                errors.append(SchemaValidationError(
                    path=f"relationships.{rel.name}.target_type",
                    message=f"Target type '{rel.target_type}' does not exist",
                    severity="error"
                ))

        return SchemaValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )

    def create_version(
        self,
        schema: OntologySchema,
        created_by: Optional[str] = None,
        changelog: Optional[str] = None
    ) -> SchemaVersion:
        """
        Create a new version record for a schema.

        Args:
            schema: The ontology schema to version.
            created_by: User who created this version.
            changelog: Description of changes.

        Returns:
            SchemaVersion record.
        """
        # Generate schema ID from content hash
        schema_hash = hashlib.sha256(
            schema.model_dump_json().encode()
        ).hexdigest()[:12]
        schema_id = f"{schema.name}_{schema_hash}"

        # Find parent version
        parent_version: Optional[str] = None
        if schema.name in self._versions and self._versions[schema.name]:
            parent_version = self._versions[schema.name][-1].version

        version = SchemaVersion(
            schema_id=schema_id,
            version=schema.version,
            schema_content=schema,
            created_by=created_by,
            changelog=changelog,
            parent_version=parent_version
        )

        # Store version
        if schema.name not in self._versions:
            self._versions[schema.name] = []
        self._versions[schema.name].append(version)

        # Persist if storage path is configured
        if self.storage_path:
            self._persist_version(version)

        return version

    def get_version(self, schema_name: str, version: str) -> Optional[SchemaVersion]:
        """
        Get a specific version of a schema.

        Args:
            schema_name: Name of the schema.
            version: Version string.

        Returns:
            SchemaVersion if found, None otherwise.
        """
        if schema_name not in self._versions:
            return None

        for v in self._versions[schema_name]:
            if v.version == version:
                return v
        return None

    def get_latest_version(self, schema_name: str) -> Optional[SchemaVersion]:
        """
        Get the latest version of a schema.

        Args:
            schema_name: Name of the schema.

        Returns:
            Latest SchemaVersion if found, None otherwise.
        """
        if schema_name not in self._versions or not self._versions[schema_name]:
            return None
        return self._versions[schema_name][-1]

    def list_versions(self, schema_name: str) -> List[SchemaVersion]:
        """
        List all versions of a schema.

        Args:
            schema_name: Name of the schema.

        Returns:
            List of SchemaVersion records.
        """
        return self._versions.get(schema_name, [])

    def _persist_version(self, version: SchemaVersion) -> None:
        """Persist a schema version to storage."""
        if not self.storage_path:
            return

        schema_dir = self.storage_path / version.schema_content.name
        schema_dir.mkdir(parents=True, exist_ok=True)

        version_file = schema_dir / f"{version.version}.json"
        with open(version_file, "w") as f:
            f.write(version.model_dump_json(indent=2))

    def load_versions_from_storage(self, schema_name: str) -> List[SchemaVersion]:
        """
        Load all versions of a schema from storage.

        Args:
            schema_name: Name of the schema.

        Returns:
            List of SchemaVersion records.
        """
        if not self.storage_path:
            return []

        schema_dir = self.storage_path / schema_name
        if not schema_dir.exists():
            return []

        versions: List[SchemaVersion] = []
        for version_file in sorted(schema_dir.glob("*.json")):
            with open(version_file) as f:
                data = json.load(f)
                version = SchemaVersion.model_validate(data)
                versions.append(version)

        self._versions[schema_name] = versions
        return versions

    def compare_versions(
        self,
        schema_name: str,
        version_a: str,
        version_b: str
    ) -> Dict[str, Any]:
        """
        Compare two versions of a schema.

        Args:
            schema_name: Name of the schema.
            version_a: First version string.
            version_b: Second version string.

        Returns:
            Dictionary describing the differences.
        """
        va = self.get_version(schema_name, version_a)
        vb = self.get_version(schema_name, version_b)

        if not va or not vb:
            raise ValueError(f"One or both versions not found")

        schema_a = va.schema_content
        schema_b = vb.schema_content

        types_a = {t.name for t in schema_a.types}
        types_b = {t.name for t in schema_b.types}

        rels_a = {r.name for r in schema_a.relationships}
        rels_b = {r.name for r in schema_b.relationships}

        return {
            "types_added": list(types_b - types_a),
            "types_removed": list(types_a - types_b),
            "types_common": list(types_a & types_b),
            "relationships_added": list(rels_b - rels_a),
            "relationships_removed": list(rels_a - rels_b),
            "relationships_common": list(rels_a & rels_b),
        }
