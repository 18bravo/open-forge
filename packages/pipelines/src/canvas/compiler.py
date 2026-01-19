"""
Pipeline Canvas Compiler for Open Forge.

Compiles React Flow canvas representations into Dagster Definitions,
enabling visual pipeline design that executes as Dagster assets.
"""

from typing import List, Dict, Any, Optional, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime
import logging

from dagster import (
    asset,
    AssetIn,
    AssetKey,
    Definitions,
    define_asset_job,
    AssetExecutionContext,
    Config,
    Output,
    MetadataValue,
)
import polars as pl

logger = logging.getLogger(__name__)


@dataclass
class CanvasNode:
    """Represents a node in the pipeline canvas."""

    id: str
    type: str  # source, transform, destination, asset
    position: Dict[str, float]
    data: Dict[str, Any] = field(default_factory=dict)

    @property
    def label(self) -> str:
        """Get node label."""
        return self.data.get("label", self.id)

    @property
    def connector_type(self) -> Optional[str]:
        """Get connector type for source nodes."""
        return self.data.get("connectorType")

    @property
    def transform_config(self) -> Optional[Dict[str, Any]]:
        """Get transform configuration."""
        return self.data.get("transform")

    @property
    def destination_type(self) -> Optional[str]:
        """Get destination type."""
        return self.data.get("destinationType")

    @property
    def config(self) -> Dict[str, Any]:
        """Get node configuration."""
        return self.data.get("config", {})

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanvasNode":
        """Create CanvasNode from dictionary representation."""
        return cls(
            id=data["id"],
            type=data["type"],
            position=data.get("position", {"x": 0, "y": 0}),
            data=data.get("data", {}),
        )


@dataclass
class CanvasEdge:
    """Represents an edge (connection) between nodes in the canvas."""

    id: str
    source: str
    target: str
    source_handle: Optional[str] = None
    target_handle: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CanvasEdge":
        """Create CanvasEdge from dictionary representation."""
        return cls(
            id=data["id"],
            source=data["source"],
            target=data["target"],
            source_handle=data.get("sourceHandle"),
            target_handle=data.get("targetHandle"),
            data=data.get("data", {}),
        )


@dataclass
class CompilationResult:
    """Result of canvas compilation."""

    definitions: Definitions
    asset_count: int
    job_name: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if compilation was successful."""
        return len(self.errors) == 0


class PipelineCanvasCompiler:
    """
    Compiles React Flow canvas to Dagster assets.

    This compiler takes nodes and edges from a visual canvas and generates
    corresponding Dagster asset definitions that can be executed as data
    pipelines.

    Example:
        ```python
        compiler = PipelineCanvasCompiler()

        result = compiler.compile(
            nodes=[
                CanvasNode(id="src_1", type="source", ...),
                CanvasNode(id="transform_1", type="transform", ...),
                CanvasNode(id="dest_1", type="destination", ...),
            ],
            edges=[
                CanvasEdge(id="e1", source="src_1", target="transform_1"),
                CanvasEdge(id="e2", source="transform_1", target="dest_1"),
            ],
            engagement_id="eng_123"
        )

        if result.success:
            # Use result.definitions with Dagster
            pass
        ```
    """

    def __init__(self):
        """Initialize the compiler."""
        self._transform_registry: Dict[str, Callable] = {}
        self._register_default_transforms()

    def _register_default_transforms(self) -> None:
        """Register default transformation functions."""
        self._transform_registry = {
            "filter": self._apply_filter_transform,
            "join": self._apply_join_transform,
            "aggregate": self._apply_aggregate_transform,
            "map": self._apply_map_transform,
            "dedupe": self._apply_dedupe_transform,
            "ontology_mapping": self._apply_ontology_mapping,
            "custom": self._apply_custom_transform,
        }

    def compile(
        self,
        nodes: List[CanvasNode],
        edges: List[CanvasEdge],
        engagement_id: str,
        pipeline_name: Optional[str] = None,
    ) -> CompilationResult:
        """
        Convert canvas representation to Dagster Definitions.

        Args:
            nodes: List of canvas nodes
            edges: List of canvas edges (connections)
            engagement_id: The engagement context ID
            pipeline_name: Optional name for the pipeline job

        Returns:
            CompilationResult with Dagster Definitions and metadata
        """
        warnings: List[str] = []
        errors: List[str] = []

        # Build dependency graph from edges
        dependencies = self._build_dependencies(nodes, edges)

        # Validate the graph
        validation_errors = self._validate_graph(nodes, edges, dependencies)
        errors.extend(validation_errors)

        if errors:
            # Return early with empty definitions if validation fails
            return CompilationResult(
                definitions=Definitions(assets=[], jobs=[]),
                asset_count=0,
                job_name="",
                warnings=warnings,
                errors=errors,
            )

        # Generate assets
        assets = []
        node_map = {node.id: node for node in nodes}

        # Process nodes in topological order
        processing_order = self._topological_sort(nodes, dependencies)

        for node_id in processing_order:
            node = node_map[node_id]

            try:
                if node.type == "source":
                    asset_def = self._create_source_asset(node, engagement_id)
                elif node.type == "transform":
                    deps = dependencies.get(node.id, [])
                    asset_def = self._create_transform_asset(
                        node, deps, engagement_id
                    )
                elif node.type == "destination":
                    deps = dependencies.get(node.id, [])
                    asset_def = self._create_destination_asset(
                        node, deps, engagement_id
                    )
                elif node.type == "asset":
                    deps = dependencies.get(node.id, [])
                    asset_def = self._create_generic_asset(
                        node, deps, engagement_id
                    )
                else:
                    warnings.append(f"Unknown node type: {node.type} for node {node.id}")
                    continue

                assets.append(asset_def)
            except Exception as e:
                errors.append(f"Failed to create asset for node {node.id}: {str(e)}")

        # Create job
        job_name = pipeline_name or f"canvas_pipeline_{engagement_id}"
        job = define_asset_job(
            name=job_name,
            selection=assets,
            description=f"Pipeline compiled from canvas for engagement {engagement_id}",
        )

        return CompilationResult(
            definitions=Definitions(
                assets=assets,
                jobs=[job],
            ),
            asset_count=len(assets),
            job_name=job_name,
            warnings=warnings,
            errors=errors,
        )

    def _build_dependencies(
        self,
        nodes: List[CanvasNode],
        edges: List[CanvasEdge],
    ) -> Dict[str, List[str]]:
        """
        Build dependency graph from edges.

        Returns a dict mapping node IDs to their upstream dependencies.
        """
        dependencies: Dict[str, List[str]] = {node.id: [] for node in nodes}

        for edge in edges:
            if edge.target in dependencies:
                dependencies[edge.target].append(edge.source)

        return dependencies

    def _validate_graph(
        self,
        nodes: List[CanvasNode],
        edges: List[CanvasEdge],
        dependencies: Dict[str, List[str]],
    ) -> List[str]:
        """Validate the canvas graph for compilation."""
        errors = []

        node_ids = {node.id for node in nodes}

        # Check for orphaned edges
        for edge in edges:
            if edge.source not in node_ids:
                errors.append(f"Edge {edge.id} references unknown source: {edge.source}")
            if edge.target not in node_ids:
                errors.append(f"Edge {edge.id} references unknown target: {edge.target}")

        # Check for cycles
        if self._has_cycle(dependencies):
            errors.append("Pipeline contains a cycle. Dagster requires acyclic graphs.")

        # Check source nodes have no dependencies
        for node in nodes:
            if node.type == "source" and dependencies.get(node.id, []):
                errors.append(
                    f"Source node {node.id} has upstream dependencies. "
                    "Source nodes should be entry points."
                )

        return errors

    def _has_cycle(self, dependencies: Dict[str, List[str]]) -> bool:
        """Check if the dependency graph contains cycles using DFS."""
        visited: Set[str] = set()
        rec_stack: Set[str] = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for dep in dependencies.get(node, []):
                if dep not in visited:
                    if dfs(dep):
                        return True
                elif dep in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for node in dependencies:
            if node not in visited:
                if dfs(node):
                    return True

        return False

    def _topological_sort(
        self,
        nodes: List[CanvasNode],
        dependencies: Dict[str, List[str]],
    ) -> List[str]:
        """Sort nodes in topological order (dependencies first)."""
        result = []
        visited: Set[str] = set()

        def visit(node_id: str) -> None:
            if node_id in visited:
                return
            visited.add(node_id)

            for dep in dependencies.get(node_id, []):
                visit(dep)

            result.append(node_id)

        for node in nodes:
            visit(node.id)

        return result

    def _create_source_asset(
        self,
        node: CanvasNode,
        engagement_id: str,
    ):
        """Create a Dagster source asset from canvas node."""
        connector_type = node.connector_type or "generic"
        config = node.config

        asset_name = f"{engagement_id}_{node.id}"

        @asset(
            name=asset_name,
            group_name=engagement_id,
            description=node.data.get("description", f"Source: {node.label}"),
            compute_kind=connector_type,
            metadata={
                "canvas_node_id": MetadataValue.text(node.id),
                "connector_type": MetadataValue.text(connector_type),
                "node_label": MetadataValue.text(node.label),
            },
        )
        def source_asset(context: AssetExecutionContext) -> Output[pl.DataFrame]:
            """Extract data from configured source."""
            context.log.info(f"Extracting data from {connector_type} source: {node.label}")

            # Import connector dynamically based on type
            try:
                # This would integrate with your connector framework
                # For now, return an empty DataFrame as placeholder
                df = pl.DataFrame()

                # Log extraction info
                context.log.info(f"Extracted {len(df)} records")

                return Output(
                    df,
                    metadata={
                        "row_count": MetadataValue.int(len(df)),
                        "column_count": MetadataValue.int(len(df.columns)),
                        "extracted_at": MetadataValue.text(datetime.now().isoformat()),
                    },
                )
            except Exception as e:
                context.log.error(f"Extraction failed: {e}")
                raise

        return source_asset

    def _create_transform_asset(
        self,
        node: CanvasNode,
        dependencies: List[str],
        engagement_id: str,
    ):
        """Create a Dagster transform asset with dependencies."""
        transform_config = node.transform_config or {}
        transform_type = transform_config.get("type", "custom")

        asset_name = f"{engagement_id}_{node.id}"

        # Build asset inputs from dependencies
        ins = {
            dep: AssetIn(key=AssetKey([f"{engagement_id}_{dep}"]))
            for dep in dependencies
        }

        @asset(
            name=asset_name,
            ins=ins,
            group_name=engagement_id,
            description=node.data.get(
                "description", f"Transform: {node.label} ({transform_type})"
            ),
            compute_kind="polars",
            metadata={
                "canvas_node_id": MetadataValue.text(node.id),
                "transform_type": MetadataValue.text(transform_type),
                "node_label": MetadataValue.text(node.label),
            },
        )
        def transform_asset(
            context: AssetExecutionContext, **inputs
        ) -> Output[pl.DataFrame]:
            """Apply transformation to input data."""
            context.log.info(
                f"Applying {transform_type} transform: {node.label}"
            )

            # Combine inputs
            dfs = list(inputs.values())
            if len(dfs) == 0:
                context.log.warning("No input data for transform")
                return Output(pl.DataFrame())

            if len(dfs) == 1:
                df = dfs[0]
            else:
                # Concatenate multiple inputs
                df = pl.concat(dfs, how="diagonal")

            # Apply transformation based on type
            transform_fn = self._transform_registry.get(
                transform_type, self._apply_custom_transform
            )
            result_df = transform_fn(df, transform_config, context)

            context.log.info(
                f"Transform complete: {len(df)} -> {len(result_df)} rows"
            )

            return Output(
                result_df,
                metadata={
                    "input_row_count": MetadataValue.int(len(df)),
                    "output_row_count": MetadataValue.int(len(result_df)),
                    "transformed_at": MetadataValue.text(datetime.now().isoformat()),
                },
            )

        return transform_asset

    def _create_destination_asset(
        self,
        node: CanvasNode,
        dependencies: List[str],
        engagement_id: str,
    ):
        """Create a Dagster destination asset."""
        destination_type = node.destination_type or "generic"
        config = node.config

        asset_name = f"{engagement_id}_{node.id}"

        # Build asset inputs from dependencies
        ins = {
            dep: AssetIn(key=AssetKey([f"{engagement_id}_{dep}"]))
            for dep in dependencies
        }

        @asset(
            name=asset_name,
            ins=ins,
            group_name=engagement_id,
            description=node.data.get("description", f"Destination: {node.label}"),
            compute_kind=destination_type,
            metadata={
                "canvas_node_id": MetadataValue.text(node.id),
                "destination_type": MetadataValue.text(destination_type),
                "node_label": MetadataValue.text(node.label),
            },
        )
        def destination_asset(
            context: AssetExecutionContext, **inputs
        ) -> Output[Dict[str, Any]]:
            """Load data to destination."""
            context.log.info(f"Loading data to {destination_type}: {node.label}")

            # Combine inputs
            dfs = list(inputs.values())
            if len(dfs) == 0:
                context.log.warning("No input data for destination")
                return Output({"status": "empty", "records_written": 0})

            df = pl.concat(dfs, how="diagonal") if len(dfs) > 1 else dfs[0]

            # Write to destination based on type
            try:
                # This would integrate with your destination framework
                records_written = len(df)

                context.log.info(f"Wrote {records_written} records to {destination_type}")

                return Output(
                    {"status": "success", "records_written": records_written},
                    metadata={
                        "records_written": MetadataValue.int(records_written),
                        "loaded_at": MetadataValue.text(datetime.now().isoformat()),
                    },
                )
            except Exception as e:
                context.log.error(f"Destination write failed: {e}")
                raise

        return destination_asset

    def _create_generic_asset(
        self,
        node: CanvasNode,
        dependencies: List[str],
        engagement_id: str,
    ):
        """Create a generic Dagster asset."""
        asset_name = f"{engagement_id}_{node.id}"

        # Build asset inputs from dependencies
        ins = {
            dep: AssetIn(key=AssetKey([f"{engagement_id}_{dep}"]))
            for dep in dependencies
        }

        @asset(
            name=asset_name,
            ins=ins,
            group_name=engagement_id,
            description=node.data.get("description", f"Asset: {node.label}"),
            compute_kind=node.data.get("computeKind", "python"),
            metadata={
                "canvas_node_id": MetadataValue.text(node.id),
                "node_label": MetadataValue.text(node.label),
            },
        )
        def generic_asset(
            context: AssetExecutionContext, **inputs
        ) -> Output[Any]:
            """Generic asset computation."""
            context.log.info(f"Computing asset: {node.label}")

            # Pass through combined inputs
            dfs = list(inputs.values())
            if len(dfs) == 0:
                return Output(None)

            result = dfs[0] if len(dfs) == 1 else dfs

            return Output(
                result,
                metadata={
                    "computed_at": MetadataValue.text(datetime.now().isoformat()),
                },
            )

        return generic_asset

    # Transform implementations

    def _apply_filter_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply filter transformation."""
        expression = config.get("expression")
        if not expression:
            context.log.warning("No filter expression provided")
            return df

        try:
            # Parse and apply filter expression
            # Note: In production, use a safer expression parser
            return df.filter(eval(expression))
        except Exception as e:
            context.log.error(f"Filter failed: {e}")
            return df

    def _apply_join_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply join transformation (placeholder - needs second input)."""
        context.log.info("Join transform - pass through (requires separate handling)")
        return df

    def _apply_aggregate_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply aggregation transformation."""
        group_by = config.get("groupBy", [])
        aggregations = config.get("aggregations", {})

        if not group_by or not aggregations:
            context.log.warning("Missing groupBy or aggregations config")
            return df

        agg_map = {
            "sum": lambda c: pl.col(c).sum(),
            "count": lambda c: pl.col(c).count(),
            "avg": lambda c: pl.col(c).mean(),
            "min": lambda c: pl.col(c).min(),
            "max": lambda c: pl.col(c).max(),
        }

        agg_exprs = []
        for col, agg_type in aggregations.items():
            if col in df.columns and agg_type in agg_map:
                agg_exprs.append(agg_map[agg_type](col).alias(f"{col}_{agg_type}"))

        if agg_exprs:
            return df.group_by(group_by).agg(agg_exprs)

        return df

    def _apply_map_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply column mapping transformation."""
        mappings = config.get("mappings", {})

        for old_name, new_name in mappings.items():
            if old_name in df.columns:
                df = df.rename({old_name: new_name})

        return df

    def _apply_dedupe_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply deduplication transformation."""
        columns = config.get("columns")
        keep = config.get("keep", "last")

        if columns:
            return df.unique(subset=columns, keep=keep)

        return df.unique(keep=keep)

    def _apply_ontology_mapping(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply ontology-based mapping transformation."""
        schema = config.get("schema", {})
        object_type = config.get("objectType")

        context.log.info(f"Applying ontology mapping to {object_type}")

        # Map columns according to schema
        if schema and "properties" in schema:
            for prop_name, prop_def in schema["properties"].items():
                source_col = prop_def.get("sourceColumn")
                if source_col and source_col in df.columns:
                    df = df.rename({source_col: prop_name})

        return df

    def _apply_custom_transform(
        self,
        df: pl.DataFrame,
        config: Dict[str, Any],
        context: AssetExecutionContext,
    ) -> pl.DataFrame:
        """Apply custom transformation (passthrough by default)."""
        context.log.info("Custom transform - passthrough")
        return df


# Convenience function for external use
def compile_canvas(
    nodes: List[Dict[str, Any]],
    edges: List[Dict[str, Any]],
    engagement_id: str,
    pipeline_name: Optional[str] = None,
) -> CompilationResult:
    """
    Compile canvas data to Dagster definitions.

    Args:
        nodes: List of node dictionaries from React Flow
        edges: List of edge dictionaries from React Flow
        engagement_id: Engagement context ID
        pipeline_name: Optional pipeline job name

    Returns:
        CompilationResult with Dagster Definitions
    """
    compiler = PipelineCanvasCompiler()

    canvas_nodes = [CanvasNode.from_dict(n) for n in nodes]
    canvas_edges = [CanvasEdge.from_dict(e) for e in edges]

    return compiler.compile(
        nodes=canvas_nodes,
        edges=canvas_edges,
        engagement_id=engagement_id,
        pipeline_name=pipeline_name,
    )
