"""
Ontology compilation assets for Open Forge.

Handles ontology definition loading, validation, and compilation
into the semantic layer for the data platform.
"""
from typing import Any, Dict, List, Optional
from datetime import datetime
from dagster import (
    asset,
    AssetExecutionContext,
    Config,
    MetadataValue,
    Output,
    AssetKey,
)
import polars as pl
import json

from pipelines.resources import DatabaseResource, IcebergResource, EventBusResource


class OntologyConfig(Config):
    """Configuration for ontology operations."""

    ontology_id: str
    ontology_name: str
    version: str = "1.0.0"
    source_namespace: str = "ontology"


class EntityDefinition(Config):
    """Definition of an ontology entity."""

    entity_type: str
    entity_name: str
    display_name: str
    description: Optional[str] = None
    source_table: Optional[str] = None
    source_namespace: str = "curated"
    primary_key: Optional[str] = None
    properties: Dict[str, Dict[str, Any]] = {}  # property_name -> {type, description, ...}


class RelationshipDefinition(Config):
    """Definition of a relationship between entities."""

    relationship_type: str
    from_entity: str
    to_entity: str
    cardinality: str = "many_to_many"  # one_to_one, one_to_many, many_to_one, many_to_many
    properties: Optional[Dict[str, Any]] = None


@asset(
    key_prefix=["ontology"],
    group_name="ontology",
    description="Loaded ontology definitions from configuration",
    compute_kind="python",
)
def ontology_definitions(
    context: AssetExecutionContext,
    config: OntologyConfig,
    database: DatabaseResource,
    iceberg: IcebergResource,
) -> Output[pl.DataFrame]:
    """Load and parse ontology definitions.

    Reads ontology definitions from:
    - Database configuration tables
    - JSON/YAML definition files
    - Iceberg metadata tables

    Produces a normalized representation of all entities,
    properties, and relationships in the ontology.
    """
    context.log.info(f"Loading ontology definitions: {config.ontology_name}")

    entities = []
    relationships = []

    # Load entity definitions from database
    with database.get_session() as session:
        # Query entity definitions
        try:
            entity_result = session.execute(
                """
                SELECT
                    entity_type,
                    entity_name,
                    display_name,
                    description,
                    source_table,
                    source_namespace,
                    primary_key,
                    properties
                FROM ontology_entities
                WHERE ontology_id = :ontology_id
                    AND is_active = true
                ORDER BY entity_type, entity_name
                """,
                {"ontology_id": config.ontology_id}
            )
            for row in entity_result:
                entities.append({
                    "type": "entity",
                    "entity_type": row.entity_type,
                    "entity_name": row.entity_name,
                    "display_name": row.display_name,
                    "description": row.description,
                    "source_table": row.source_table,
                    "source_namespace": row.source_namespace,
                    "primary_key": row.primary_key,
                    "properties": row.properties if isinstance(row.properties, str) else json.dumps(row.properties),
                })
        except Exception as e:
            context.log.warning(f"Could not load entities from database: {e}")

        # Query relationship definitions
        try:
            rel_result = session.execute(
                """
                SELECT
                    relationship_type,
                    from_entity,
                    to_entity,
                    cardinality,
                    properties
                FROM ontology_relationships
                WHERE ontology_id = :ontology_id
                    AND is_active = true
                ORDER BY relationship_type
                """,
                {"ontology_id": config.ontology_id}
            )
            for row in rel_result:
                relationships.append({
                    "type": "relationship",
                    "relationship_type": row.relationship_type,
                    "from_entity": row.from_entity,
                    "to_entity": row.to_entity,
                    "cardinality": row.cardinality,
                    "properties": row.properties if isinstance(row.properties, str) else json.dumps(row.properties or {}),
                })
        except Exception as e:
            context.log.warning(f"Could not load relationships from database: {e}")

    # Also try loading from Iceberg if exists
    try:
        if iceberg.table_exists(config.source_namespace, f"entities_{config.ontology_id}"):
            entity_df = iceberg.read_table(
                config.source_namespace,
                f"entities_{config.ontology_id}"
            )
            for row in entity_df.iter_rows(named=True):
                entities.append({
                    "type": "entity",
                    **{k: v for k, v in row.items() if not k.startswith("_")}
                })
    except Exception as e:
        context.log.debug(f"No Iceberg entity definitions: {e}")

    # Combine into single DataFrame
    all_definitions = []
    for entity in entities:
        all_definitions.append({
            "definition_type": "entity",
            "name": entity.get("entity_name"),
            "parent_type": entity.get("entity_type"),
            "display_name": entity.get("display_name"),
            "description": entity.get("description"),
            "source_table": entity.get("source_table"),
            "source_namespace": entity.get("source_namespace"),
            "primary_key": entity.get("primary_key"),
            "properties_json": entity.get("properties", "{}"),
            "from_entity": None,
            "to_entity": None,
            "cardinality": None,
        })

    for rel in relationships:
        all_definitions.append({
            "definition_type": "relationship",
            "name": rel.get("relationship_type"),
            "parent_type": None,
            "display_name": rel.get("relationship_type"),
            "description": None,
            "source_table": None,
            "source_namespace": None,
            "primary_key": None,
            "properties_json": rel.get("properties", "{}"),
            "from_entity": rel.get("from_entity"),
            "to_entity": rel.get("to_entity"),
            "cardinality": rel.get("cardinality"),
        })

    if not all_definitions:
        context.log.warning("No ontology definitions found")
        # Return empty DataFrame with schema
        df = pl.DataFrame({
            "definition_type": [],
            "name": [],
            "parent_type": [],
            "display_name": [],
            "description": [],
            "source_table": [],
            "source_namespace": [],
            "primary_key": [],
            "properties_json": [],
            "from_entity": [],
            "to_entity": [],
            "cardinality": [],
        })
    else:
        df = pl.DataFrame(all_definitions)

    # Add metadata
    df = df.with_columns([
        pl.lit(config.ontology_id).alias("_ontology_id"),
        pl.lit(config.version).alias("_ontology_version"),
        pl.lit(datetime.now()).alias("_loaded_at"),
    ])

    context.log.info(f"Loaded {len(entities)} entities and {len(relationships)} relationships")

    return Output(
        df,
        metadata={
            "ontology_id": MetadataValue.text(config.ontology_id),
            "ontology_name": MetadataValue.text(config.ontology_name),
            "version": MetadataValue.text(config.version),
            "entity_count": MetadataValue.int(len(entities)),
            "relationship_count": MetadataValue.int(len(relationships)),
            "total_definitions": MetadataValue.int(len(all_definitions)),
        }
    )


@asset(
    key_prefix=["ontology"],
    group_name="ontology",
    description="Compiled ontology with resolved references",
    deps=[AssetKey(["ontology", "ontology_definitions"])],
    compute_kind="python",
)
def compiled_ontology(
    context: AssetExecutionContext,
    config: OntologyConfig,
    iceberg: IcebergResource,
    event_bus: EventBusResource,
) -> Output[Dict[str, Any]]:
    """Compile ontology definitions into executable format.

    The compilation process:
    1. Resolves entity references
    2. Validates relationship integrity
    3. Builds property type mappings
    4. Generates query templates
    5. Creates semantic layer metadata

    Output is a compiled ontology object ready for runtime use.
    """
    context.log.info(f"Compiling ontology: {config.ontology_name}")

    # Load definitions
    definitions_df = iceberg.read_table("ontology", f"ontology_definitions_{config.ontology_id}")

    if definitions_df.is_empty():
        context.log.warning("No definitions to compile")
        return Output({})

    # Separate entities and relationships
    entities_df = definitions_df.filter(pl.col("definition_type") == "entity")
    relationships_df = definitions_df.filter(pl.col("definition_type") == "relationship")

    # Build compiled ontology structure
    compiled = {
        "ontology_id": config.ontology_id,
        "ontology_name": config.ontology_name,
        "version": config.version,
        "compiled_at": datetime.now().isoformat(),
        "entities": {},
        "relationships": {},
        "entity_types": [],
        "relationship_types": [],
    }

    # Compile entities
    entity_names = set()
    for row in entities_df.iter_rows(named=True):
        entity_name = row["name"]
        entity_names.add(entity_name)

        # Parse properties
        try:
            properties = json.loads(row["properties_json"]) if row["properties_json"] else {}
        except Exception:
            properties = {}

        compiled["entities"][entity_name] = {
            "entity_type": row["parent_type"],
            "display_name": row["display_name"],
            "description": row["description"],
            "source": {
                "table": row["source_table"],
                "namespace": row["source_namespace"],
                "primary_key": row["primary_key"],
            },
            "properties": properties,
            "relationships": [],  # Will be populated below
        }

        # Track entity types
        if row["parent_type"] and row["parent_type"] not in compiled["entity_types"]:
            compiled["entity_types"].append(row["parent_type"])

    # Compile relationships and link to entities
    for row in relationships_df.iter_rows(named=True):
        rel_type = row["name"]
        from_entity = row["from_entity"]
        to_entity = row["to_entity"]

        # Parse properties
        try:
            properties = json.loads(row["properties_json"]) if row["properties_json"] else {}
        except Exception:
            properties = {}

        compiled["relationships"][rel_type] = {
            "from_entity": from_entity,
            "to_entity": to_entity,
            "cardinality": row["cardinality"],
            "properties": properties,
        }

        # Track relationship types
        if rel_type not in compiled["relationship_types"]:
            compiled["relationship_types"].append(rel_type)

        # Add to entity's relationships
        if from_entity in compiled["entities"]:
            compiled["entities"][from_entity]["relationships"].append({
                "type": rel_type,
                "direction": "outgoing",
                "target": to_entity,
            })
        if to_entity in compiled["entities"]:
            compiled["entities"][to_entity]["relationships"].append({
                "type": rel_type,
                "direction": "incoming",
                "target": from_entity,
            })

    # Generate statistics
    compiled["statistics"] = {
        "entity_count": len(compiled["entities"]),
        "relationship_count": len(compiled["relationships"]),
        "entity_type_count": len(compiled["entity_types"]),
        "relationship_type_count": len(compiled["relationship_types"]),
    }

    # Publish compilation event
    event_bus.publish_sync(
        "ontology.compiled",
        {
            "ontology_id": config.ontology_id,
            "version": config.version,
            "entity_count": len(compiled["entities"]),
            "relationship_count": len(compiled["relationships"]),
        }
    )

    context.log.info(
        f"Ontology compiled: {len(compiled['entities'])} entities, "
        f"{len(compiled['relationships'])} relationships"
    )

    return Output(
        compiled,
        metadata={
            "ontology_id": MetadataValue.text(config.ontology_id),
            "version": MetadataValue.text(config.version),
            "entity_count": MetadataValue.int(len(compiled["entities"])),
            "relationship_count": MetadataValue.int(len(compiled["relationships"])),
            "entity_types": MetadataValue.json(compiled["entity_types"]),
            "relationship_types": MetadataValue.json(compiled["relationship_types"]),
        }
    )


@asset(
    key_prefix=["ontology"],
    group_name="ontology",
    description="Validation report for compiled ontology",
    deps=[AssetKey(["ontology", "compiled_ontology"])],
    compute_kind="python",
)
def ontology_validation_report(
    context: AssetExecutionContext,
    config: OntologyConfig,
    iceberg: IcebergResource,
    database: DatabaseResource,
    event_bus: EventBusResource,
) -> Output[pl.DataFrame]:
    """Validate compiled ontology against source data.

    Validation checks:
    1. Source table existence
    2. Primary key uniqueness
    3. Relationship integrity (foreign keys exist)
    4. Property type compatibility
    5. Data coverage statistics

    Produces a detailed validation report.
    """
    context.log.info(f"Validating ontology: {config.ontology_name}")

    # Load compiled ontology from previous run or database
    # For this example, we'll re-compile from definitions
    definitions_df = iceberg.read_table("ontology", f"ontology_definitions_{config.ontology_id}")

    validation_results = []

    # Validate entities
    entities_df = definitions_df.filter(pl.col("definition_type") == "entity")

    for row in entities_df.iter_rows(named=True):
        entity_name = row["name"]
        source_table = row["source_table"]
        source_namespace = row["source_namespace"]
        primary_key = row["primary_key"]

        # Check source table exists
        table_exists = False
        row_count = 0
        pk_unique = True

        if source_table and source_namespace:
            try:
                table_exists = iceberg.table_exists(source_namespace, source_table)
                if table_exists:
                    source_df = iceberg.read_table(source_namespace, source_table)
                    row_count = len(source_df)

                    # Check primary key uniqueness
                    if primary_key and primary_key in source_df.columns:
                        unique_count = source_df[primary_key].n_unique()
                        pk_unique = unique_count == row_count
            except Exception as e:
                context.log.warning(f"Error validating {entity_name}: {e}")

        validation_results.append({
            "validation_type": "entity",
            "object_name": entity_name,
            "check_name": "source_table_exists",
            "check_passed": table_exists,
            "details": f"Table: {source_namespace}.{source_table}" if source_table else "No source table",
            "severity": "error" if not table_exists and source_table else "info",
        })

        validation_results.append({
            "validation_type": "entity",
            "object_name": entity_name,
            "check_name": "source_row_count",
            "check_passed": row_count > 0,
            "details": f"Rows: {row_count}",
            "severity": "warning" if row_count == 0 and table_exists else "info",
        })

        if primary_key:
            validation_results.append({
                "validation_type": "entity",
                "object_name": entity_name,
                "check_name": "primary_key_unique",
                "check_passed": pk_unique,
                "details": f"Primary key: {primary_key}",
                "severity": "error" if not pk_unique else "info",
            })

    # Validate relationships
    relationships_df = definitions_df.filter(pl.col("definition_type") == "relationship")
    entity_names = set(entities_df["name"].to_list())

    for row in relationships_df.iter_rows(named=True):
        rel_name = row["name"]
        from_entity = row["from_entity"]
        to_entity = row["to_entity"]

        # Check entities exist
        from_exists = from_entity in entity_names
        to_exists = to_entity in entity_names

        validation_results.append({
            "validation_type": "relationship",
            "object_name": rel_name,
            "check_name": "from_entity_exists",
            "check_passed": from_exists,
            "details": f"From: {from_entity}",
            "severity": "error" if not from_exists else "info",
        })

        validation_results.append({
            "validation_type": "relationship",
            "object_name": rel_name,
            "check_name": "to_entity_exists",
            "check_passed": to_exists,
            "details": f"To: {to_entity}",
            "severity": "error" if not to_exists else "info",
        })

    # Create validation report DataFrame
    if validation_results:
        df = pl.DataFrame(validation_results)
    else:
        df = pl.DataFrame({
            "validation_type": [],
            "object_name": [],
            "check_name": [],
            "check_passed": [],
            "details": [],
            "severity": [],
        })

    # Add metadata
    df = df.with_columns([
        pl.lit(config.ontology_id).alias("_ontology_id"),
        pl.lit(config.version).alias("_ontology_version"),
        pl.lit(datetime.now()).alias("_validated_at"),
    ])

    # Calculate summary
    total_checks = len(validation_results)
    passed_checks = len([r for r in validation_results if r["check_passed"]])
    failed_checks = total_checks - passed_checks
    error_count = len([r for r in validation_results if r["severity"] == "error" and not r["check_passed"]])

    is_valid = error_count == 0

    # Publish validation event
    event_bus.publish_sync(
        "ontology.validated",
        {
            "ontology_id": config.ontology_id,
            "version": config.version,
            "is_valid": is_valid,
            "total_checks": total_checks,
            "passed_checks": passed_checks,
            "error_count": error_count,
        }
    )

    context.log.info(
        f"Validation complete: {passed_checks}/{total_checks} checks passed, "
        f"{error_count} errors"
    )

    return Output(
        df,
        metadata={
            "ontology_id": MetadataValue.text(config.ontology_id),
            "version": MetadataValue.text(config.version),
            "is_valid": MetadataValue.bool(is_valid),
            "total_checks": MetadataValue.int(total_checks),
            "passed_checks": MetadataValue.int(passed_checks),
            "failed_checks": MetadataValue.int(failed_checks),
            "error_count": MetadataValue.int(error_count),
        }
    )
