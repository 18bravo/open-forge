"""
Data source discovery and profiling for Open Forge.
Provides schema introspection, sample data retrieval, and data profiling.
"""
import asyncio
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union
from enum import Enum

from pydantic import BaseModel, Field

from connectors.base import (
    BaseConnector,
    ConnectorConfig,
    ConnectorRegistry,
    DataSchema,
    SampleData,
    SchemaField,
)


class DataType(str, Enum):
    """Normalized data types for profiling."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATE = "date"
    TIMESTAMP = "timestamp"
    BINARY = "binary"
    ARRAY = "array"
    OBJECT = "object"
    NULL = "null"
    UNKNOWN = "unknown"


class FieldStatistics(BaseModel):
    """Statistics for a single field."""
    field_name: str
    data_type: str
    null_count: int = 0
    null_percentage: float = 0.0
    distinct_count: Optional[int] = None
    distinct_percentage: Optional[float] = None

    # Numeric statistics
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    std_dev: Optional[float] = None

    # String statistics
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None

    # Value distribution
    top_values: List[Dict[str, Any]] = Field(default_factory=list)
    sample_values: List[Any] = Field(default_factory=list)


class DataProfile(BaseModel):
    """Complete data profile for a data source."""
    source_name: str
    schema_: DataSchema = Field(..., alias="schema")
    row_count: int
    column_count: int
    field_statistics: List[FieldStatistics]
    profiled_at: datetime
    sample_size: int
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"populate_by_name": True}


class DiscoveryResult(BaseModel):
    """Result of data source discovery."""
    connector_name: str
    connector_type: str
    schemas: List[DataSchema]
    discovered_at: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataDiscovery:
    """
    Data source discovery and profiling service.

    Provides schema introspection, sample data retrieval,
    and statistical profiling for connected data sources.

    Example:
        discovery = DataDiscovery()

        # Discover all schemas from a connector
        async with PostgresConnector(config) as conn:
            result = await discovery.discover(conn)
            print(f"Found {len(result.schemas)} tables")

        # Profile a specific table
        async with PostgresConnector(config) as conn:
            profile = await discovery.profile(conn, "users", sample_size=1000)
            for stat in profile.field_statistics:
                print(f"{stat.field_name}: {stat.null_percentage}% nulls")
    """

    def __init__(
        self,
        default_sample_size: int = 1000,
        max_distinct_values: int = 100,
        top_values_count: int = 10
    ):
        """
        Initialize the discovery service.

        Args:
            default_sample_size: Default number of rows to sample for profiling.
            max_distinct_values: Maximum distinct values to track per field.
            top_values_count: Number of top values to include in statistics.
        """
        self.default_sample_size = default_sample_size
        self.max_distinct_values = max_distinct_values
        self.top_values_count = top_values_count

    async def discover(
        self,
        connector: BaseConnector,
        sources: Optional[List[str]] = None
    ) -> DiscoveryResult:
        """
        Discover schemas from a data source.

        Args:
            connector: Connected data connector.
            sources: Optional list of specific sources to discover.
                    If None, discovers all available sources.

        Returns:
            DiscoveryResult with discovered schemas.
        """
        if not connector.is_connected:
            raise RuntimeError("Connector must be connected before discovery")

        schemas = []

        if sources:
            for source in sources:
                source_schemas = await connector.fetch_schema(source)
                schemas.extend(source_schemas)
        else:
            schemas = await connector.fetch_schema()

        return DiscoveryResult(
            connector_name=connector.name,
            connector_type=connector.connector_type,
            schemas=schemas,
            discovered_at=datetime.utcnow(),
            metadata={
                "source_count": len(sources) if sources else "all",
                "schema_count": len(schemas),
            }
        )

    async def profile(
        self,
        connector: BaseConnector,
        source: str,
        sample_size: Optional[int] = None
    ) -> DataProfile:
        """
        Profile a data source with statistical analysis.

        Args:
            connector: Connected data connector.
            source: Source identifier (table name, endpoint, etc.).
            sample_size: Number of rows to sample (default: default_sample_size).

        Returns:
            DataProfile with statistics for each field.
        """
        if not connector.is_connected:
            raise RuntimeError("Connector must be connected before profiling")

        sample_size = sample_size or self.default_sample_size

        # Fetch sample data
        sample = await connector.fetch_sample(source, limit=sample_size)

        # Calculate statistics for each field
        field_stats = []
        for schema_field in sample.schema_.fields:
            stats = self._calculate_field_statistics(
                schema_field,
                sample.rows
            )
            field_stats.append(stats)

        return DataProfile(
            source_name=source,
            schema=sample.schema_,
            row_count=sample.total_count or len(sample.rows),
            column_count=len(sample.schema_.fields),
            field_statistics=field_stats,
            profiled_at=datetime.utcnow(),
            sample_size=len(sample.rows),
            metadata={
                "connector_type": connector.connector_type,
                "connector_name": connector.name,
            }
        )

    def _calculate_field_statistics(
        self,
        field: SchemaField,
        rows: List[Dict[str, Any]]
    ) -> FieldStatistics:
        """Calculate statistics for a single field."""
        values = [row.get(field.name) for row in rows]
        total_count = len(values)

        # Null statistics
        null_count = sum(1 for v in values if v is None)
        null_percentage = (null_count / total_count * 100) if total_count > 0 else 0.0

        # Non-null values
        non_null_values = [v for v in values if v is not None]

        stats = FieldStatistics(
            field_name=field.name,
            data_type=field.data_type,
            null_count=null_count,
            null_percentage=round(null_percentage, 2),
        )

        if not non_null_values:
            return stats

        # Distinct values
        try:
            # Convert unhashable types for counting
            hashable_values = []
            for v in non_null_values:
                if isinstance(v, (dict, list)):
                    hashable_values.append(str(v))
                else:
                    hashable_values.append(v)

            distinct_count = len(set(hashable_values[:self.max_distinct_values]))
            stats.distinct_count = distinct_count
            stats.distinct_percentage = round(
                distinct_count / len(non_null_values) * 100, 2
            )

            # Top values
            value_counts = Counter(hashable_values)
            top_values = value_counts.most_common(self.top_values_count)
            stats.top_values = [
                {"value": v, "count": c, "percentage": round(c / total_count * 100, 2)}
                for v, c in top_values
            ]
        except Exception:
            pass

        # Sample values
        stats.sample_values = non_null_values[:5]

        # Type-specific statistics
        normalized_type = self._normalize_type(field.data_type)

        if normalized_type in (DataType.INTEGER, DataType.FLOAT):
            stats = self._calculate_numeric_stats(stats, non_null_values)
        elif normalized_type == DataType.STRING:
            stats = self._calculate_string_stats(stats, non_null_values)

        return stats

    def _normalize_type(self, type_str: str) -> DataType:
        """Normalize a type string to DataType enum."""
        type_lower = type_str.lower()

        if type_lower in ("int", "integer", "long", "short", "byte", "bigint", "smallint"):
            return DataType.INTEGER
        elif type_lower in ("float", "double", "decimal", "numeric", "real"):
            return DataType.FLOAT
        elif type_lower in ("bool", "boolean"):
            return DataType.BOOLEAN
        elif type_lower == "date":
            return DataType.DATE
        elif type_lower in ("timestamp", "datetime", "timestamp_tz"):
            return DataType.TIMESTAMP
        elif type_lower in ("binary", "bytes", "blob"):
            return DataType.BINARY
        elif type_lower in ("array", "list"):
            return DataType.ARRAY
        elif type_lower in ("object", "struct", "map", "json"):
            return DataType.OBJECT
        elif type_lower in ("null", "none"):
            return DataType.NULL
        elif type_lower in ("string", "text", "varchar", "char"):
            return DataType.STRING
        else:
            return DataType.UNKNOWN

    def _calculate_numeric_stats(
        self,
        stats: FieldStatistics,
        values: List[Any]
    ) -> FieldStatistics:
        """Calculate numeric statistics."""
        try:
            numeric_values = [float(v) for v in values if v is not None]
            if not numeric_values:
                return stats

            stats.min_value = min(numeric_values)
            stats.max_value = max(numeric_values)
            stats.mean_value = round(sum(numeric_values) / len(numeric_values), 4)

            # Median
            sorted_values = sorted(numeric_values)
            n = len(sorted_values)
            mid = n // 2
            if n % 2 == 0:
                stats.median_value = (sorted_values[mid - 1] + sorted_values[mid]) / 2
            else:
                stats.median_value = sorted_values[mid]

            # Standard deviation
            if len(numeric_values) > 1:
                mean = stats.mean_value
                variance = sum((x - mean) ** 2 for x in numeric_values) / len(numeric_values)
                stats.std_dev = round(variance ** 0.5, 4)

        except (ValueError, TypeError):
            pass

        return stats

    def _calculate_string_stats(
        self,
        stats: FieldStatistics,
        values: List[Any]
    ) -> FieldStatistics:
        """Calculate string statistics."""
        try:
            string_values = [str(v) for v in values if v is not None]
            if not string_values:
                return stats

            lengths = [len(s) for s in string_values]
            stats.min_length = min(lengths)
            stats.max_length = max(lengths)
            stats.avg_length = round(sum(lengths) / len(lengths), 2)

        except Exception:
            pass

        return stats


class DataSourceScanner:
    """
    Scans multiple data sources and builds a unified catalog.

    Example:
        scanner = DataSourceScanner()

        # Add connectors to scan
        scanner.add_connector(postgres_config)
        scanner.add_connector(mysql_config)
        scanner.add_connector(s3_config)

        # Scan all sources
        catalog = await scanner.scan_all()
    """

    def __init__(self):
        self._configs: List[ConnectorConfig] = []
        self._discovery = DataDiscovery()

    def add_connector(self, config: ConnectorConfig) -> None:
        """Add a connector configuration to scan."""
        self._configs.append(config)

    async def scan_all(
        self,
        parallel: bool = True
    ) -> List[DiscoveryResult]:
        """
        Scan all configured data sources.

        Args:
            parallel: Whether to scan sources in parallel.

        Returns:
            List of DiscoveryResult for each source.
        """
        if parallel:
            tasks = [self._scan_source(config) for config in self._configs]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            return [r for r in results if isinstance(r, DiscoveryResult)]
        else:
            results = []
            for config in self._configs:
                try:
                    result = await self._scan_source(config)
                    results.append(result)
                except Exception:
                    continue
            return results

    async def _scan_source(self, config: ConnectorConfig) -> DiscoveryResult:
        """Scan a single data source."""
        connector_class = ConnectorRegistry.get(config.connector_type)
        if not connector_class:
            raise ValueError(f"Unknown connector type: {config.connector_type}")

        connector = connector_class(config)
        async with connector:
            return await self._discovery.discover(connector)

    async def profile_source(
        self,
        config: ConnectorConfig,
        source: str,
        sample_size: int = 1000
    ) -> DataProfile:
        """
        Profile a specific source from a connector.

        Args:
            config: Connector configuration.
            source: Source identifier.
            sample_size: Number of rows to sample.

        Returns:
            DataProfile with statistics.
        """
        connector_class = ConnectorRegistry.get(config.connector_type)
        if not connector_class:
            raise ValueError(f"Unknown connector type: {config.connector_type}")

        connector = connector_class(config)
        async with connector:
            return await self._discovery.profile(connector, source, sample_size)


class SchemaComparator:
    """
    Compares schemas between data sources.

    Useful for detecting schema drift or validating data migrations.
    """

    @staticmethod
    def compare(
        schema1: DataSchema,
        schema2: DataSchema
    ) -> Dict[str, Any]:
        """
        Compare two schemas and return differences.

        Args:
            schema1: First schema.
            schema2: Second schema.

        Returns:
            Dictionary describing the differences.
        """
        fields1 = {f.name: f for f in schema1.fields}
        fields2 = {f.name: f for f in schema2.fields}

        added = set(fields2.keys()) - set(fields1.keys())
        removed = set(fields1.keys()) - set(fields2.keys())
        common = set(fields1.keys()) & set(fields2.keys())

        changed = []
        for name in common:
            f1 = fields1[name]
            f2 = fields2[name]

            changes = {}
            if f1.data_type != f2.data_type:
                changes["data_type"] = {"from": f1.data_type, "to": f2.data_type}
            if f1.nullable != f2.nullable:
                changes["nullable"] = {"from": f1.nullable, "to": f2.nullable}

            if changes:
                changed.append({"field": name, "changes": changes})

        return {
            "schema1_name": schema1.name,
            "schema2_name": schema2.name,
            "added_fields": list(added),
            "removed_fields": list(removed),
            "changed_fields": changed,
            "is_compatible": len(removed) == 0 and len(changed) == 0,
            "is_identical": len(added) == 0 and len(removed) == 0 and len(changed) == 0,
        }


class DataQualityChecker:
    """
    Performs data quality checks on profiled data.
    """

    @staticmethod
    def check_completeness(
        profile: DataProfile,
        max_null_percentage: float = 10.0
    ) -> Dict[str, Any]:
        """
        Check data completeness based on null percentages.

        Args:
            profile: Data profile to check.
            max_null_percentage: Maximum acceptable null percentage.

        Returns:
            Check results with failing fields.
        """
        failing_fields = []
        for stat in profile.field_statistics:
            if stat.null_percentage > max_null_percentage:
                failing_fields.append({
                    "field": stat.field_name,
                    "null_percentage": stat.null_percentage,
                    "threshold": max_null_percentage,
                })

        return {
            "check": "completeness",
            "passed": len(failing_fields) == 0,
            "failing_fields": failing_fields,
            "total_fields": len(profile.field_statistics),
            "failing_count": len(failing_fields),
        }

    @staticmethod
    def check_uniqueness(
        profile: DataProfile,
        fields: List[str],
        min_uniqueness: float = 100.0
    ) -> Dict[str, Any]:
        """
        Check uniqueness for specified fields.

        Args:
            profile: Data profile to check.
            fields: Fields to check for uniqueness.
            min_uniqueness: Minimum distinct percentage required.

        Returns:
            Check results with failing fields.
        """
        stats_by_name = {s.field_name: s for s in profile.field_statistics}
        failing_fields = []

        for field_name in fields:
            stat = stats_by_name.get(field_name)
            if not stat:
                continue

            if stat.distinct_percentage is not None:
                if stat.distinct_percentage < min_uniqueness:
                    failing_fields.append({
                        "field": field_name,
                        "distinct_percentage": stat.distinct_percentage,
                        "threshold": min_uniqueness,
                    })

        return {
            "check": "uniqueness",
            "passed": len(failing_fields) == 0,
            "failing_fields": failing_fields,
            "checked_fields": fields,
            "failing_count": len(failing_fields),
        }

    @staticmethod
    def check_value_range(
        profile: DataProfile,
        field: str,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Check that numeric values fall within expected range.

        Args:
            profile: Data profile to check.
            field: Field name to check.
            min_value: Minimum expected value.
            max_value: Maximum expected value.

        Returns:
            Check results.
        """
        stats = next(
            (s for s in profile.field_statistics if s.field_name == field),
            None
        )

        if not stats:
            return {
                "check": "value_range",
                "passed": False,
                "error": f"Field not found: {field}",
            }

        issues = []

        if min_value is not None and stats.min_value is not None:
            if stats.min_value < min_value:
                issues.append({
                    "type": "below_minimum",
                    "actual_min": stats.min_value,
                    "expected_min": min_value,
                })

        if max_value is not None and stats.max_value is not None:
            if stats.max_value > max_value:
                issues.append({
                    "type": "above_maximum",
                    "actual_max": stats.max_value,
                    "expected_max": max_value,
                })

        return {
            "check": "value_range",
            "field": field,
            "passed": len(issues) == 0,
            "issues": issues,
            "actual_range": {
                "min": stats.min_value,
                "max": stats.max_value,
            },
            "expected_range": {
                "min": min_value,
                "max": max_value,
            },
        }
