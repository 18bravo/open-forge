"""
Dagster assets for Open Forge pipelines.
"""
from pipelines.assets.ingestion import (
    raw_source_data,
    validated_source_data,
    staged_source_data,
)
from pipelines.assets.transformation import (
    cleaned_data,
    enriched_data,
    aggregated_data,
)
from pipelines.assets.ontology import (
    ontology_definitions,
    compiled_ontology,
    ontology_validation_report,
)

__all__ = [
    # Ingestion
    "raw_source_data",
    "validated_source_data",
    "staged_source_data",
    # Transformation
    "cleaned_data",
    "enriched_data",
    "aggregated_data",
    # Ontology
    "ontology_definitions",
    "compiled_ontology",
    "ontology_validation_report",
]
