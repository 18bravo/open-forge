"""
Impact analysis for lineage changes.

Analyzes the downstream impact of changes to data assets.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from forge_data.lineage.graph import LineageGraph, LineageNode, NodeType
from forge_data.lineage.query import LineageQuery, TraversalDirection


@dataclass
class ImpactedAsset:
    """An asset impacted by a change."""

    node: LineageNode
    distance: int  # Hops from the changed asset
    impact_path: list[str]  # Node IDs in the path from change to this asset


@dataclass
class ImpactReport:
    """
    Report of impact from a proposed change.

    Categorizes impacted assets by type and calculates risk score.
    """

    changed_node_id: str
    changed_node_name: str
    analysis_timestamp: datetime = field(default_factory=datetime.utcnow)

    # Impacted assets by type
    impacted_columns: list[ImpactedAsset] = field(default_factory=list)
    impacted_tables: list[ImpactedAsset] = field(default_factory=list)
    impacted_transforms: list[ImpactedAsset] = field(default_factory=list)
    impacted_pipelines: list[ImpactedAsset] = field(default_factory=list)
    impacted_models: list[ImpactedAsset] = field(default_factory=list)

    # Summary metrics
    total_impacted: int = 0
    max_distance: int = 0
    risk_score: float = 0.0  # 0-100 scale
    risk_factors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "changed_node_id": self.changed_node_id,
            "changed_node_name": self.changed_node_name,
            "analysis_timestamp": self.analysis_timestamp.isoformat(),
            "summary": {
                "total_impacted": self.total_impacted,
                "max_distance": self.max_distance,
                "risk_score": self.risk_score,
                "risk_factors": self.risk_factors,
            },
            "impacted_assets": {
                "columns": len(self.impacted_columns),
                "tables": len(self.impacted_tables),
                "transforms": len(self.impacted_transforms),
                "pipelines": len(self.impacted_pipelines),
                "models": len(self.impacted_models),
            },
        }


class ImpactAnalyzer:
    """
    Analyzes impact of changes to data assets.

    Uses bounded lineage queries to find downstream dependencies
    and calculates risk scores based on impact breadth and depth.

    Example:
        analyzer = ImpactAnalyzer(graph)
        report = await analyzer.analyze_change("column:users.email")

        print(f"Risk score: {report.risk_score}")
        print(f"Impacted assets: {report.total_impacted}")
    """

    # Risk weights for different asset types
    RISK_WEIGHTS = {
        NodeType.MODEL: 10.0,  # ML models are high risk
        NodeType.PIPELINE: 5.0,  # Pipelines are medium-high risk
        NodeType.TABLE: 3.0,  # Tables are medium risk
        NodeType.COLUMN: 1.0,  # Columns are base risk
        NodeType.TRANSFORM: 2.0,  # Transforms are medium-low risk
    }

    def __init__(
        self,
        graph: LineageGraph,
        max_depth: int = 10,
        max_nodes: int = 1000,
    ):
        """
        Initialize the impact analyzer.

        Args:
            graph: The lineage graph to analyze
            max_depth: Maximum traversal depth (default: 10)
            max_nodes: Maximum nodes to consider (default: 1000)
        """
        self.graph = graph
        self.max_depth = max_depth
        self.max_nodes = max_nodes

    async def analyze_change(self, node_id: str) -> ImpactReport:
        """
        Analyze the impact of changing a node.

        Args:
            node_id: ID of the node being changed

        Returns:
            ImpactReport with all impacted assets and risk score
        """
        node = self.graph.get_node(node_id)
        if node is None:
            return ImpactReport(
                changed_node_id=node_id,
                changed_node_name="Unknown",
                risk_factors=["Node not found in lineage graph"],
            )

        # Run bounded downstream query
        query = LineageQuery(
            root_node_id=node_id,
            direction=TraversalDirection.DOWNSTREAM,
            max_depth=self.max_depth,
            max_nodes=self.max_nodes,
        )
        result = await query.execute(self.graph)

        # Categorize impacted assets
        report = ImpactReport(
            changed_node_id=node_id,
            changed_node_name=node.name,
        )

        # Track distances from BFS
        distances: dict[str, int] = {node_id: 0}
        for depth in range(1, result.depth_reached + 1):
            for result_node in result.graph.nodes():
                if result_node.id not in distances:
                    # Check if any parent is at depth-1
                    for edge in result.graph.get_incoming_edges(result_node.id):
                        if distances.get(edge.source_id) == depth - 1:
                            distances[result_node.id] = depth
                            break

        # Categorize by type
        for result_node in result.graph.nodes():
            if result_node.id == node_id:
                continue  # Skip the root node

            distance = distances.get(result_node.id, result.depth_reached)
            asset = ImpactedAsset(
                node=result_node,
                distance=distance,
                impact_path=[],  # Full path tracking would require more complex logic
            )

            if result_node.type == NodeType.COLUMN:
                report.impacted_columns.append(asset)
            elif result_node.type == NodeType.TABLE:
                report.impacted_tables.append(asset)
            elif result_node.type == NodeType.TRANSFORM:
                report.impacted_transforms.append(asset)
            elif result_node.type == NodeType.PIPELINE:
                report.impacted_pipelines.append(asset)
            elif result_node.type == NodeType.MODEL:
                report.impacted_models.append(asset)

        # Calculate summary metrics
        report.total_impacted = (
            len(report.impacted_columns)
            + len(report.impacted_tables)
            + len(report.impacted_transforms)
            + len(report.impacted_pipelines)
            + len(report.impacted_models)
        )
        report.max_distance = result.depth_reached

        # Calculate risk score
        report.risk_score = self._calculate_risk_score(report)
        report.risk_factors = self._identify_risk_factors(report, result)

        return report

    def _calculate_risk_score(self, report: ImpactReport) -> float:
        """
        Calculate risk score based on impacted assets.

        Score is 0-100 based on:
        - Number and type of impacted assets
        - Distance from change
        - Asset criticality weights
        """
        if report.total_impacted == 0:
            return 0.0

        weighted_sum = 0.0

        for asset in report.impacted_columns:
            weighted_sum += self.RISK_WEIGHTS[NodeType.COLUMN] / (asset.distance + 1)

        for asset in report.impacted_tables:
            weighted_sum += self.RISK_WEIGHTS[NodeType.TABLE] / (asset.distance + 1)

        for asset in report.impacted_transforms:
            weighted_sum += self.RISK_WEIGHTS[NodeType.TRANSFORM] / (asset.distance + 1)

        for asset in report.impacted_pipelines:
            weighted_sum += self.RISK_WEIGHTS[NodeType.PIPELINE] / (asset.distance + 1)

        for asset in report.impacted_models:
            weighted_sum += self.RISK_WEIGHTS[NodeType.MODEL] / (asset.distance + 1)

        # Normalize to 0-100 scale (cap at 100)
        # Using log scale to prevent very large numbers
        import math

        score = min(100.0, 10 * math.log1p(weighted_sum))
        return round(score, 2)

    def _identify_risk_factors(
        self,
        report: ImpactReport,
        query_result: Any,
    ) -> list[str]:
        """Identify specific risk factors for the change."""
        factors = []

        if report.impacted_models:
            factors.append(
                f"Impacts {len(report.impacted_models)} ML model(s) - may affect predictions"
            )

        if report.impacted_pipelines:
            factors.append(
                f"Impacts {len(report.impacted_pipelines)} pipeline(s) - may cause job failures"
            )

        if report.total_impacted > 50:
            factors.append(f"High blast radius: {report.total_impacted} assets impacted")

        if report.max_distance >= 5:
            factors.append(f"Deep dependency chain: {report.max_distance} levels")

        if query_result.truncated:
            factors.append(
                f"Analysis was truncated: {query_result.truncation_reason} - "
                "actual impact may be larger"
            )

        return factors

    async def compare_schemas(
        self,
        node_id: str,
        old_schema: dict[str, Any],
        new_schema: dict[str, Any],
    ) -> ImpactReport:
        """
        Analyze impact of a schema change.

        Args:
            node_id: ID of the node with schema change
            old_schema: Previous schema
            new_schema: New schema

        Returns:
            ImpactReport for the schema change
        """
        # Identify changed columns
        old_columns = set(old_schema.get("columns", {}).keys())
        new_columns = set(new_schema.get("columns", {}).keys())

        removed = old_columns - new_columns
        added = new_columns - old_columns
        modified = set()

        for col in old_columns & new_columns:
            if old_schema["columns"][col] != new_schema["columns"][col]:
                modified.add(col)

        # Analyze impact for removed/modified columns
        combined_report = await self.analyze_change(node_id)

        if removed:
            combined_report.risk_factors.append(
                f"Removing columns: {', '.join(removed)}"
            )
            combined_report.risk_score = min(100.0, combined_report.risk_score * 1.5)

        if modified:
            combined_report.risk_factors.append(
                f"Modifying columns: {', '.join(modified)}"
            )
            combined_report.risk_score = min(100.0, combined_report.risk_score * 1.2)

        return combined_report
