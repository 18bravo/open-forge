"""
E2E Test Scenario: Data Platform Use Case.

Tests building an enterprise data platform with multiple data sources,
complex transformations, and analytics capabilities.

Scenario Overview:
1. Create engagement for enterprise data platform
2. Discovery: Multiple databases, data lakes, and streaming sources
3. Design: Complex ontology with dimensional modeling
4. Build: Data pipelines, transformations, and analytics
5. Deploy: Multi-environment deployment with monitoring

Expected total duration: 5-8 minutes
"""
import json
import pytest
from datetime import datetime

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalType, ApprovalStatus

from ..conftest import MockLLM, MockEventBus
from ..utils import (
    get_phase_requirements_status,
    complete_phase_requirements,
    force_phase_transition,
    submit_approval,
    generate_test_engagement_name,
)


class TestDataPlatformScenario:
    """Complete enterprise data platform scenario."""

    @pytest.fixture
    def data_platform_responses(self):
        """Mock LLM responses for data platform use case."""
        return {
            # Discovery responses
            "stakeholder": json.dumps([
                {
                    "name": "Emily Watson",
                    "role": "Chief Data Officer",
                    "department": "Data & Analytics",
                    "influence_level": "high",
                    "data_needs": [
                        "Enterprise data catalog",
                        "Data quality metrics",
                        "Data lineage tracking",
                        "Compliance reporting",
                    ],
                    "success_criteria": "Single source of truth for enterprise data",
                },
                {
                    "name": "David Kim",
                    "role": "Head of Data Engineering",
                    "department": "Engineering",
                    "influence_level": "high",
                    "data_needs": [
                        "Scalable data pipelines",
                        "Real-time processing",
                        "Schema evolution support",
                        "Pipeline monitoring",
                    ],
                    "success_criteria": "Sub-minute data latency",
                },
                {
                    "name": "Rachel Foster",
                    "role": "Lead Data Scientist",
                    "department": "Data Science",
                    "influence_level": "medium",
                    "data_needs": [
                        "Feature store",
                        "ML model serving",
                        "A/B test data",
                        "Historical data access",
                    ],
                    "success_criteria": "Self-service data access for ML",
                },
                {
                    "name": "James Mitchell",
                    "role": "Compliance Officer",
                    "department": "Legal & Compliance",
                    "influence_level": "high",
                    "data_needs": [
                        "PII tracking",
                        "Data retention policies",
                        "Audit trails",
                        "GDPR compliance",
                    ],
                    "success_criteria": "Zero compliance violations",
                },
            ]),
            "discover": json.dumps([
                {
                    "name": "Transactional Database",
                    "source_type": "database",
                    "technology": "PostgreSQL 14",
                    "description": "Primary OLTP database for transactions",
                    "volume": "2TB",
                    "tables": 250,
                    "update_frequency": "Real-time",
                },
                {
                    "name": "Data Warehouse",
                    "source_type": "data_warehouse",
                    "technology": "Snowflake",
                    "description": "Existing analytics warehouse",
                    "volume": "50TB",
                    "tables": 500,
                    "update_frequency": "Daily",
                },
                {
                    "name": "Data Lake",
                    "source_type": "cloud_storage",
                    "technology": "S3 + Delta Lake",
                    "description": "Raw and processed data lake",
                    "volume": "200TB",
                    "partitions": 10000,
                    "update_frequency": "Hourly",
                },
                {
                    "name": "Event Stream",
                    "source_type": "streaming",
                    "technology": "Apache Kafka",
                    "description": "Real-time event streaming",
                    "topics": 150,
                    "messages_per_day": "500M",
                },
                {
                    "name": "Legacy ERP",
                    "source_type": "legacy_system",
                    "technology": "Oracle 12c",
                    "description": "Legacy ERP system",
                    "volume": "5TB",
                    "update_frequency": "Batch nightly",
                },
            ]),
            # Design responses
            "ontology": json.dumps({
                "name": "Enterprise Data Platform Ontology",
                "version": "1.0.0",
                "domains": [
                    {
                        "name": "core",
                        "description": "Core business entities",
                        "entities": [
                            {
                                "name": "Customer",
                                "type": "dimension",
                                "attributes": [
                                    {"name": "customer_key", "type": "bigint", "primary_key": True},
                                    {"name": "customer_id", "type": "string", "business_key": True},
                                    {"name": "name", "type": "string"},
                                    {"name": "email", "type": "string", "pii": True},
                                    {"name": "segment", "type": "string"},
                                    {"name": "effective_date", "type": "date", "scd": True},
                                    {"name": "end_date", "type": "date", "scd": True},
                                ],
                            },
                            {
                                "name": "Product",
                                "type": "dimension",
                                "attributes": [
                                    {"name": "product_key", "type": "bigint", "primary_key": True},
                                    {"name": "sku", "type": "string", "business_key": True},
                                    {"name": "name", "type": "string"},
                                    {"name": "category", "type": "string"},
                                    {"name": "price", "type": "decimal"},
                                ],
                            },
                            {
                                "name": "Transaction",
                                "type": "fact",
                                "grain": "transaction",
                                "attributes": [
                                    {"name": "transaction_id", "type": "string", "primary_key": True},
                                    {"name": "customer_key", "type": "bigint", "foreign_key": "Customer.customer_key"},
                                    {"name": "product_key", "type": "bigint", "foreign_key": "Product.product_key"},
                                    {"name": "date_key", "type": "int", "foreign_key": "Date.date_key"},
                                    {"name": "quantity", "type": "int", "measure": True},
                                    {"name": "amount", "type": "decimal", "measure": True},
                                    {"name": "discount", "type": "decimal", "measure": True},
                                ],
                            },
                        ],
                    },
                    {
                        "name": "events",
                        "description": "Event data",
                        "entities": [
                            {
                                "name": "ClickstreamEvent",
                                "type": "event",
                                "attributes": [
                                    {"name": "event_id", "type": "uuid"},
                                    {"name": "session_id", "type": "string"},
                                    {"name": "user_id", "type": "string"},
                                    {"name": "event_type", "type": "string"},
                                    {"name": "page_url", "type": "string"},
                                    {"name": "event_timestamp", "type": "timestamp"},
                                ],
                            },
                        ],
                    },
                ],
            }),
            "transformation": json.dumps({
                "layers": [
                    {
                        "name": "bronze",
                        "description": "Raw data ingestion",
                        "transformations": [
                            {"name": "ingest_postgres", "source": "Transactional Database", "format": "delta"},
                            {"name": "ingest_kafka", "source": "Event Stream", "format": "delta"},
                            {"name": "ingest_oracle", "source": "Legacy ERP", "format": "delta"},
                        ],
                    },
                    {
                        "name": "silver",
                        "description": "Cleaned and conformed data",
                        "transformations": [
                            {"name": "clean_customers", "source": "bronze.customers", "operations": ["dedupe", "standardize", "validate"]},
                            {"name": "clean_transactions", "source": "bronze.transactions", "operations": ["validate", "enrich"]},
                            {"name": "conform_products", "source": ["bronze.products_pg", "bronze.products_oracle"], "operations": ["merge", "reconcile"]},
                        ],
                    },
                    {
                        "name": "gold",
                        "description": "Business-level aggregates",
                        "transformations": [
                            {"name": "customer_360", "sources": ["silver.customers", "silver.transactions", "silver.events"], "type": "aggregate"},
                            {"name": "sales_summary", "sources": ["silver.transactions"], "type": "aggregate", "grain": "daily"},
                            {"name": "product_performance", "sources": ["silver.transactions", "silver.products"], "type": "aggregate"},
                        ],
                    },
                ],
            }),
            # Build responses
            "pipeline": json.dumps({
                "pipelines": [
                    {
                        "name": "batch_ingestion",
                        "schedule": "0 2 * * *",
                        "steps": [
                            {"name": "extract_postgres", "type": "extract", "source": "postgres"},
                            {"name": "extract_oracle", "type": "extract", "source": "oracle"},
                            {"name": "load_bronze", "type": "load", "target": "bronze"},
                            {"name": "transform_silver", "type": "transform", "target": "silver"},
                            {"name": "aggregate_gold", "type": "transform", "target": "gold"},
                            {"name": "validate", "type": "quality", "checks": ["row_count", "schema", "freshness"]},
                        ],
                    },
                    {
                        "name": "streaming_ingestion",
                        "trigger": "continuous",
                        "steps": [
                            {"name": "consume_kafka", "type": "stream", "source": "kafka"},
                            {"name": "transform", "type": "stream_transform"},
                            {"name": "write_delta", "type": "stream_sink", "target": "bronze.events"},
                        ],
                    },
                    {
                        "name": "ml_feature_pipeline",
                        "schedule": "0 6 * * *",
                        "steps": [
                            {"name": "compute_features", "type": "feature_engineering"},
                            {"name": "write_feature_store", "type": "feature_store"},
                            {"name": "validate_features", "type": "quality"},
                        ],
                    },
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_data_platform_discovery(
        self,
        phase_manager,
        approval_manager,
        data_platform_responses,
    ):
        """
        Test data platform - Discovery Phase.

        Expected duration: ~30 seconds
        """
        # 1. Identify stakeholders
        stakeholders = json.loads(data_platform_responses["stakeholder"])
        assert len(stakeholders) == 4
        assert any(s["role"] == "Chief Data Officer" for s in stakeholders)

        # 2. Discover sources
        sources = json.loads(data_platform_responses["discover"])
        assert len(sources) == 5
        source_types = {s["source_type"] for s in sources}
        assert "streaming" in source_types
        assert "legacy_system" in source_types

        # 3. Complete phase
        complete_phase_requirements(
            phase_manager,
            outputs=["stakeholder_map", "requirements", "discovered_sources", "source_assessments", "source_recommendations"],
            gates=["stakeholder_coverage", "data_sources_validated", "requirements_documented"],
            approvals=["discovery_sign_off"],
        )

        # 4. Transition
        result = phase_manager.transition_to(EngagementPhase.DESIGN, approved_by="cdo")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_data_platform_design(
        self,
        phase_manager,
        data_platform_responses,
    ):
        """
        Test data platform - Design Phase.

        Expected duration: ~30 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # 1. Verify ontology structure
        ontology = json.loads(data_platform_responses["ontology"])
        assert "domains" in ontology
        assert len(ontology["domains"]) >= 2

        # Verify dimensional modeling
        core_domain = next(d for d in ontology["domains"] if d["name"] == "core")
        entity_types = {e["type"] for e in core_domain["entities"]}
        assert "dimension" in entity_types
        assert "fact" in entity_types

        # 2. Verify transformation layers
        transformations = json.loads(data_platform_responses["transformation"])
        assert "layers" in transformations
        layer_names = [l["name"] for l in transformations["layers"]]
        assert layer_names == ["bronze", "silver", "gold"]  # Medallion architecture

        # 3. Complete phase
        complete_phase_requirements(
            phase_manager,
            outputs=["ontology_draft", "schema_definitions", "data_models", "transformation_specs", "validation_rules"],
            gates=["ontology_validated", "schema_completeness", "data_model_review"],
            approvals=["design_approval"],
            phase=EngagementPhase.DESIGN,
        )

        result = phase_manager.transition_to(EngagementPhase.BUILD, approved_by="data_architect")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_data_platform_build(
        self,
        phase_manager,
        data_platform_responses,
    ):
        """
        Test data platform - Build Phase.

        Expected duration: ~30 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        # 1. Verify pipeline structure
        pipelines = json.loads(data_platform_responses["pipeline"])
        assert len(pipelines["pipelines"]) >= 3

        # Verify streaming pipeline
        streaming = next(p for p in pipelines["pipelines"] if p["name"] == "streaming_ingestion")
        assert streaming["trigger"] == "continuous"

        # Verify ML pipeline
        ml_pipeline = next(p for p in pipelines["pipelines"] if "ml" in p["name"].lower() or "feature" in p["name"].lower())
        assert any("feature" in s["type"].lower() for s in ml_pipeline["steps"])

        # 2. Complete phase
        complete_phase_requirements(
            phase_manager,
            outputs=["compiled_ontology", "data_pipelines", "ui_components", "workflows", "integrations"],
            gates=["pipeline_tested", "ui_validated", "security_review"],
            approvals=["build_approval", "security_sign_off"],
            phase=EngagementPhase.BUILD,
        )

        result = phase_manager.transition_to(EngagementPhase.DEPLOY, approved_by="tech_lead")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_data_platform_deploy(
        self,
        phase_manager,
    ):
        """
        Test data platform - Deploy Phase.

        Expected duration: ~30 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DEPLOY)

        # Complete deployment
        complete_phase_requirements(
            phase_manager,
            outputs=["deployment_config", "environment_setup", "deployment_verification", "documentation", "training_materials"],
            gates=["deployment_validated", "documentation_complete", "user_acceptance"],
            approvals=["deployment_approval", "client_sign_off"],
            phase=EngagementPhase.DEPLOY,
        )

        result = phase_manager.transition_to(EngagementPhase.COMPLETE, approved_by="cdo")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_data_platform_full_lifecycle(
        self,
        e2e_client,
        phase_manager,
        approval_manager,
        mock_event_bus,
        data_platform_responses,
    ):
        """
        Test complete data platform lifecycle.

        This tests the full journey of building an enterprise data platform.

        Expected duration: 5-8 minutes
        """
        # ===== CREATE ENGAGEMENT =====
        engagement = await e2e_client.create_engagement(
            name=generate_test_engagement_name("Enterprise Data Platform"),
            objective="Build enterprise data platform with real-time and batch processing",
            description=(
                "Unified data platform supporting: "
                "- Multi-source data integration "
                "- Real-time streaming "
                "- Data quality and governance "
                "- ML feature store"
            ),
            priority="critical",
        )

        # ===== DISCOVERY =====
        complete_phase_requirements(
            phase_manager,
            outputs=["stakeholder_map", "requirements", "discovered_sources", "source_assessments", "source_recommendations"],
            gates=["stakeholder_coverage", "data_sources_validated", "requirements_documented"],
            approvals=["discovery_sign_off"],
        )
        phase_manager.transition_to(EngagementPhase.DESIGN, approved_by="cdo")

        # ===== DESIGN =====
        complete_phase_requirements(
            phase_manager,
            outputs=["ontology_draft", "schema_definitions", "data_models", "transformation_specs", "validation_rules"],
            gates=["ontology_validated", "schema_completeness", "data_model_review"],
            approvals=["design_approval"],
            phase=EngagementPhase.DESIGN,
        )
        phase_manager.transition_to(EngagementPhase.BUILD, approved_by="data_architect")

        # ===== BUILD =====
        complete_phase_requirements(
            phase_manager,
            outputs=["compiled_ontology", "data_pipelines", "ui_components", "workflows", "integrations"],
            gates=["pipeline_tested", "ui_validated", "security_review"],
            approvals=["build_approval", "security_sign_off"],
            phase=EngagementPhase.BUILD,
        )
        phase_manager.transition_to(EngagementPhase.DEPLOY, approved_by="eng_lead")

        # ===== DEPLOY =====
        complete_phase_requirements(
            phase_manager,
            outputs=["deployment_config", "environment_setup", "deployment_verification", "documentation", "training_materials"],
            gates=["deployment_validated", "documentation_complete", "user_acceptance"],
            approvals=["deployment_approval", "client_sign_off"],
            phase=EngagementPhase.DEPLOY,
        )
        phase_manager.transition_to(EngagementPhase.COMPLETE, approved_by="cdo")

        # ===== VERIFY =====
        assert phase_manager.get_current_phase() == EngagementPhase.COMPLETE

        summary = phase_manager.get_phase_summary()
        assert len(summary["history"]) == 4

        # All phases should be complete
        for phase in [EngagementPhase.DISCOVERY, EngagementPhase.DESIGN, EngagementPhase.BUILD, EngagementPhase.DEPLOY]:
            assert summary["phases"][phase.value]["is_complete"]


class TestDataPlatformEdgeCases:
    """Edge cases and error scenarios for data platform."""

    @pytest.mark.asyncio
    async def test_legacy_system_compatibility_review(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test handling of legacy system compatibility concerns.

        Expected duration: ~15 seconds
        """
        # Simulate discovery finding legacy system issues
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # Create approval for special handling
        approval = await approval_manager.create_request(
            engagement_id="legacy-test",
            approval_type=ApprovalType.CONFIGURATION,
            title="Legacy ERP Integration Approach",
            description="Review integration approach for Oracle 12c legacy system",
            requested_by="source_discovery_agent",
            context_data={
                "system": "Oracle 12c",
                "concerns": [
                    "Character encoding issues",
                    "Custom data types",
                    "Performance constraints",
                ],
                "recommended_approach": "Batch CDC with reconciliation",
            },
        )

        # Approve with conditions
        await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            comments="Approved with recommendation to add extra validation checks",
        )

    @pytest.mark.asyncio
    async def test_streaming_vs_batch_conflict(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test resolution of streaming vs batch requirements conflict.

        Expected duration: ~15 seconds
        """
        # Stakeholders have conflicting requirements
        conflict_data = {
            "stakeholder_a": "Needs real-time updates (< 1 minute latency)",
            "stakeholder_b": "Needs consistent daily snapshots",
            "resolution": "Lambda architecture with both streaming and batch layers",
        }

        # Create approval to resolve conflict
        approval = await approval_manager.create_request(
            engagement_id="conflict-test",
            approval_type=ApprovalType.CONFIGURATION,
            title="Resolve Streaming vs Batch Requirements",
            description="Approve lambda architecture approach",
            requested_by="discovery_agent",
            context_data=conflict_data,
        )

        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            comments="Lambda architecture approved - implement both streaming and batch",
        )

        assert result["success"]
