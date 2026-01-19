"""
Discovery Agent Cluster

Agents for understanding client needs and discovering data sources.

This cluster contains:
- StakeholderAnalysisAgent: Analyzes stakeholder requirements and maps business processes
- SourceDiscoveryAgent: Discovers and assesses data sources
- RequirementsGatheringAgent: Synthesizes and prioritizes requirements
- DiscoveryCluster: Orchestrates the discovery workflow

Usage:
    from agents.discovery import DiscoveryCluster, run_discovery

    # Using the cluster directly
    cluster = DiscoveryCluster(llm=my_llm)
    result = await cluster.run(input)

    # Using the convenience function
    result = await run_discovery(
        llm=my_llm,
        engagement_id="eng-001",
        organization="Acme Corp",
        project_description="Data platform modernization"
    )
"""

from .stakeholder_agent import (
    StakeholderAnalysisAgent,
    STAKEHOLDER_ANALYSIS_SYSTEM,
    IDENTIFY_STAKEHOLDERS,
    MAP_BUSINESS_PROCESS,
    ANALYZE_REQUIREMENTS,
)

from .source_discovery_agent import (
    SourceDiscoveryAgent,
    DataSourceType,
    DataQualityDimension,
    SOURCE_DISCOVERY_SYSTEM,
    DISCOVER_SOURCES,
    CATALOG_SOURCE,
    ASSESS_QUALITY,
    EVALUATE_INTEGRATION,
)

from .requirements_agent import (
    RequirementsGatheringAgent,
    RequirementPriority,
    RequirementType,
    RequirementStatus,
    REQUIREMENTS_SYSTEM,
    SYNTHESIZE_REQUIREMENTS,
    PRIORITIZE_REQUIREMENTS,
    IDENTIFY_INTEGRATIONS,
    VALIDATE_REQUIREMENTS,
    GENERATE_REQUIREMENTS_DOC,
)

from .cluster import (
    DiscoveryCluster,
    DiscoveryPhase,
    DiscoveryReport,
    run_discovery,
)

__all__ = [
    # Main cluster
    "DiscoveryCluster",
    "DiscoveryPhase",
    "DiscoveryReport",
    "run_discovery",
    # Stakeholder agent
    "StakeholderAnalysisAgent",
    "STAKEHOLDER_ANALYSIS_SYSTEM",
    "IDENTIFY_STAKEHOLDERS",
    "MAP_BUSINESS_PROCESS",
    "ANALYZE_REQUIREMENTS",
    # Source discovery agent
    "SourceDiscoveryAgent",
    "DataSourceType",
    "DataQualityDimension",
    "SOURCE_DISCOVERY_SYSTEM",
    "DISCOVER_SOURCES",
    "CATALOG_SOURCE",
    "ASSESS_QUALITY",
    "EVALUATE_INTEGRATION",
    # Requirements agent
    "RequirementsGatheringAgent",
    "RequirementPriority",
    "RequirementType",
    "RequirementStatus",
    "REQUIREMENTS_SYSTEM",
    "SYNTHESIZE_REQUIREMENTS",
    "PRIORITIZE_REQUIREMENTS",
    "IDENTIFY_INTEGRATIONS",
    "VALIDATE_REQUIREMENTS",
    "GENERATE_REQUIREMENTS_DOC",
]
