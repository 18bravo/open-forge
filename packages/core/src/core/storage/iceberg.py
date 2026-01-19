"""
Apache Iceberg data lake operations.
"""
from typing import Any, Dict, List, Optional
from pyiceberg.catalog import load_catalog
from pyiceberg.schema import Schema
from pyiceberg.types import (
    NestedField, StringType, LongType, TimestampType,
    DecimalType, BooleanType, DoubleType, ListType, MapType
)
from pyiceberg.partitioning import PartitionSpec, PartitionField
from pyiceberg.transforms import DayTransform, IdentityTransform
import polars as pl
from core.config import get_settings

settings = get_settings()

class IcebergCatalog:
    """Apache Iceberg catalog operations."""
    
    def __init__(self):
        self.catalog = load_catalog(
            "foundry",
            **{
                "type": "rest",
                "uri": settings.iceberg.catalog_uri,
                "warehouse": settings.iceberg.warehouse_path,
                "s3.endpoint": settings.iceberg.s3_endpoint,
                "s3.access-key-id": settings.iceberg.s3_access_key,
                "s3.secret-access-key": settings.iceberg.s3_secret_key,
            }
        )
    
    def create_namespace(self, namespace: str) -> None:
        """Create a namespace if it doesn't exist."""
        try:
            self.catalog.create_namespace(namespace)
        except Exception:
            pass  # Namespace exists
    
    def create_table(
        self,
        namespace: str,
        table_name: str,
        schema_fields: List[Dict[str, Any]],
        partition_by: Optional[List[str]] = None
    ) -> None:
        """Create an Iceberg table."""
        # Convert schema fields to Iceberg types
        fields = []
        for i, field in enumerate(schema_fields):
            iceberg_type = self._map_type(field["type"])
            fields.append(NestedField(
                field_id=i + 1,
                name=field["name"],
                field_type=iceberg_type,
                required=field.get("required", False)
            ))
        
        # Add metadata fields
        fields.extend([
            NestedField(1000, "_created_at", TimestampType(), required=True),
            NestedField(1001, "_updated_at", TimestampType(), required=True),
            NestedField(1002, "_version", LongType(), required=True),
        ])
        
        schema = Schema(*fields)
        
        # Build partition spec
        partition_spec = PartitionSpec()
        if partition_by:
            for i, col in enumerate(partition_by):
                field_id = next(f.field_id for f in fields if f.name == col)
                partition_spec = partition_spec.add_field(
                    PartitionField(
                        source_id=field_id,
                        field_id=2000 + i,
                        transform=IdentityTransform(),
                        name=f"{col}_partition"
                    )
                )
        else:
            # Default: partition by day on _created_at
            partition_spec = PartitionSpec(
                PartitionField(
                    source_id=1000,
                    field_id=2000,
                    transform=DayTransform(),
                    name="day"
                )
            )
        
        # Create table
        self.catalog.create_table(
            identifier=f"{namespace}.{table_name}",
            schema=schema,
            partition_spec=partition_spec,
            properties={
                "write.format.default": "parquet",
                "write.parquet.compression-codec": "zstd",
            }
        )
    
    def append_data(
        self,
        namespace: str,
        table_name: str,
        df: pl.DataFrame
    ) -> None:
        """Append data to an Iceberg table."""
        table = self.catalog.load_table(f"{namespace}.{table_name}")
        
        # Convert Polars to PyArrow
        arrow_table = df.to_arrow()
        
        # Append
        table.append(arrow_table)
    
    def read_table(
        self,
        namespace: str,
        table_name: str,
        filter_expr: Optional[str] = None
    ) -> pl.DataFrame:
        """Read data from an Iceberg table."""
        table = self.catalog.load_table(f"{namespace}.{table_name}")
        
        scan = table.scan()
        if filter_expr:
            scan = scan.filter(filter_expr)
        
        arrow_table = scan.to_arrow()
        return pl.from_arrow(arrow_table)
    
    def _map_type(self, type_str: str):
        """Map string type to Iceberg type."""
        mapping = {
            "string": StringType(),
            "integer": LongType(),
            "long": LongType(),
            "float": DoubleType(),
            "double": DoubleType(),
            "decimal": DecimalType(precision=18, scale=4),
            "boolean": BooleanType(),
            "timestamp": TimestampType(),
            "datetime": TimestampType(),
        }
        return mapping.get(type_str.lower(), StringType())