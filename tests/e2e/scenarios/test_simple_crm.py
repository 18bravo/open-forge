"""
E2E Test Scenario: Simple CRM Use Case.

Tests a complete CRM analytics platform build from start to finish.
This represents a typical customer engagement scenario.

Scenario Overview:
1. Create engagement for CRM analytics platform
2. Discovery: Identify Salesforce and internal DB as sources
3. Design: Create Customer, Contact, Opportunity ontology
4. Build: Generate UI components and data pipelines
5. Deploy: Configure and verify deployment

Expected total duration: 3-5 minutes
"""
import json
import pytest
from datetime import datetime

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalType, ApprovalStatus

from ..conftest import MockLLM, MockEventBus
from ..utils import (
    wait_for_phase,
    get_phase_requirements_status,
    complete_phase_requirements,
    force_phase_transition,
    submit_approval,
    generate_test_engagement_name,
)


class TestSimpleCRMScenario:
    """Complete CRM analytics platform scenario."""

    @pytest.fixture
    def crm_mock_llm_responses(self):
        """Mock LLM responses specific to CRM use case."""
        return {
            # Discovery phase responses
            "stakeholder": json.dumps([
                {
                    "name": "Sarah Johnson",
                    "role": "VP of Sales",
                    "department": "Sales",
                    "influence_level": "high",
                    "data_needs": [
                        "Real-time pipeline visibility",
                        "Customer 360 view",
                        "Sales forecasting",
                        "Win/loss analysis",
                    ],
                    "success_criteria": "Reduce time to close by 20%",
                },
                {
                    "name": "Mike Chen",
                    "role": "Sales Operations Manager",
                    "department": "Sales Ops",
                    "influence_level": "medium",
                    "data_needs": [
                        "Territory performance",
                        "Rep productivity metrics",
                        "Lead conversion rates",
                    ],
                    "success_criteria": "Automated weekly reports",
                },
                {
                    "name": "Lisa Park",
                    "role": "Customer Success Lead",
                    "department": "Customer Success",
                    "influence_level": "medium",
                    "data_needs": [
                        "Customer health scores",
                        "Churn prediction",
                        "Renewal pipeline",
                    ],
                    "success_criteria": "Reduce churn by 15%",
                },
            ]),
            "discover": json.dumps([
                {
                    "name": "Salesforce CRM",
                    "source_type": "saas_application",
                    "technology": "Salesforce REST API",
                    "description": "Primary CRM with accounts, contacts, opportunities",
                    "owner": "Sales Operations",
                    "estimated_volume": "500GB",
                    "update_frequency": "Real-time",
                    "tables": ["Account", "Contact", "Opportunity", "Task", "Event"],
                },
                {
                    "name": "Customer Success DB",
                    "source_type": "database",
                    "technology": "PostgreSQL",
                    "description": "Customer health and support data",
                    "owner": "Customer Success",
                    "estimated_volume": "50GB",
                    "update_frequency": "Hourly",
                    "tables": ["health_scores", "support_tickets", "nps_responses"],
                },
                {
                    "name": "Marketing Automation",
                    "source_type": "api",
                    "technology": "HubSpot API",
                    "description": "Marketing engagement and lead data",
                    "owner": "Marketing",
                    "estimated_volume": "100GB",
                    "update_frequency": "Daily",
                },
            ]),
            "requirements": json.dumps({
                "explicit_requirements": [
                    {"id": "REQ-CRM-001", "description": "Unified customer view across all touchpoints", "priority": "high"},
                    {"id": "REQ-CRM-002", "description": "Real-time opportunity pipeline dashboard", "priority": "high"},
                    {"id": "REQ-CRM-003", "description": "Automated sales forecasting", "priority": "medium"},
                    {"id": "REQ-CRM-004", "description": "Customer health score calculation", "priority": "high"},
                    {"id": "REQ-CRM-005", "description": "Self-service reporting for sales reps", "priority": "medium"},
                ],
                "implicit_requirements": [
                    {"id": "REQ-CRM-I01", "description": "Mobile-responsive dashboards"},
                    {"id": "REQ-CRM-I02", "description": "Role-based access control"},
                    {"id": "REQ-CRM-I03", "description": "Data refresh SLA of 1 hour"},
                ],
            }),
            # Design phase responses
            "ontology": json.dumps({
                "name": "CRM Analytics Ontology",
                "version": "1.0.0",
                "entities": [
                    {
                        "name": "Customer",
                        "attributes": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "industry", "type": "string"},
                            {"name": "segment", "type": "enum", "values": ["enterprise", "mid_market", "smb"]},
                            {"name": "health_score", "type": "decimal"},
                            {"name": "lifetime_value", "type": "decimal"},
                            {"name": "created_at", "type": "datetime"},
                        ],
                    },
                    {
                        "name": "Contact",
                        "attributes": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "customer_id", "type": "uuid", "foreign_key": "Customer.id"},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "email", "type": "email"},
                            {"name": "role", "type": "string"},
                            {"name": "is_primary", "type": "boolean"},
                        ],
                    },
                    {
                        "name": "Opportunity",
                        "attributes": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "customer_id", "type": "uuid", "foreign_key": "Customer.id"},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "amount", "type": "decimal"},
                            {"name": "stage", "type": "enum", "values": ["prospecting", "qualification", "proposal", "negotiation", "closed_won", "closed_lost"]},
                            {"name": "probability", "type": "decimal"},
                            {"name": "close_date", "type": "date"},
                            {"name": "owner_id", "type": "string"},
                        ],
                    },
                    {
                        "name": "Activity",
                        "attributes": [
                            {"name": "id", "type": "uuid", "primary_key": True},
                            {"name": "customer_id", "type": "uuid", "foreign_key": "Customer.id"},
                            {"name": "contact_id", "type": "uuid", "foreign_key": "Contact.id"},
                            {"name": "type", "type": "enum", "values": ["call", "email", "meeting", "demo"]},
                            {"name": "subject", "type": "string"},
                            {"name": "occurred_at", "type": "datetime"},
                        ],
                    },
                ],
                "relationships": [
                    {"from": "Customer", "to": "Contact", "type": "one_to_many"},
                    {"from": "Customer", "to": "Opportunity", "type": "one_to_many"},
                    {"from": "Customer", "to": "Activity", "type": "one_to_many"},
                ],
            }),
            # Build phase responses
            "ui": json.dumps({
                "components": [
                    {"name": "CustomerDashboard", "type": "dashboard", "widgets": ["pipeline_chart", "health_summary", "activity_feed"]},
                    {"name": "CustomerForm", "type": "form", "entity": "Customer", "fields": ["name", "industry", "segment"]},
                    {"name": "CustomerTable", "type": "table", "entity": "Customer", "columns": ["name", "segment", "health_score", "ltv"]},
                    {"name": "OpportunityKanban", "type": "kanban", "entity": "Opportunity", "stages": ["prospecting", "qualification", "proposal", "negotiation", "closed"]},
                    {"name": "ActivityTimeline", "type": "timeline", "entity": "Activity"},
                ],
            }),
            "workflow": json.dumps({
                "workflows": [
                    {"name": "data_sync", "trigger": "schedule", "cron": "0 * * * *", "steps": ["extract", "transform", "load", "validate"]},
                    {"name": "health_score_calc", "trigger": "event", "event": "customer.updated", "steps": ["gather_metrics", "calculate_score", "update_customer"]},
                    {"name": "lead_assignment", "trigger": "event", "event": "lead.created", "steps": ["score_lead", "assign_territory", "notify_rep"]},
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_crm_scenario_discovery_phase(
        self,
        e2e_client,
        phase_manager,
        approval_manager,
        crm_mock_llm_responses,
    ):
        """
        Test CRM scenario - Discovery Phase.

        Expected duration: ~30 seconds
        """
        # 1. Create engagement
        engagement = await e2e_client.create_engagement(
            name=generate_test_engagement_name("CRM Analytics Platform"),
            objective="Build unified CRM analytics platform with real-time dashboards",
            description="Integrate Salesforce, Customer Success DB, and Marketing automation",
            priority="high",
            data_sources=[
                {"source_id": "salesforce-crm", "source_type": "saas_application", "access_mode": "read"},
                {"source_id": "cs-postgres", "source_type": "database", "access_mode": "read"},
            ],
        )

        # 2. Verify starting phase
        assert phase_manager.get_current_phase() == EngagementPhase.DISCOVERY

        # 3. Simulate stakeholder analysis
        stakeholders = json.loads(crm_mock_llm_responses["stakeholder"])
        assert len(stakeholders) == 3
        phase_manager.record_output("stakeholder_map")

        # 4. Simulate source discovery
        sources = json.loads(crm_mock_llm_responses["discover"])
        assert len(sources) == 3
        phase_manager.record_output("discovered_sources")
        phase_manager.record_output("source_assessments")
        phase_manager.record_output("source_recommendations")

        # 5. Simulate requirements gathering
        requirements = json.loads(crm_mock_llm_responses["requirements"])
        assert len(requirements["explicit_requirements"]) >= 5
        phase_manager.record_output("requirements")

        # 6. Pass quality gates
        phase_manager.pass_quality_gate("stakeholder_coverage", evidence={"count": 3})
        phase_manager.pass_quality_gate("data_sources_validated", evidence={"count": 3})
        phase_manager.pass_quality_gate("requirements_documented", evidence={"count": 8})

        # 7. Get approval
        approval = await approval_manager.create_request(
            engagement_id=engagement["id"],
            approval_type=ApprovalType.CONFIGURATION,
            title="CRM Discovery Phase Sign-off",
            description="Approve discovery outputs for CRM analytics platform",
            requested_by="discovery_agent",
        )

        await submit_approval(approval_manager, approval.id, True, "vp_sales")
        phase_manager.receive_approval("discovery_sign_off", "vp_sales")

        # 8. Verify and transition
        status = get_phase_requirements_status(phase_manager)
        assert status["completion_percentage"] == 100.0

        result = phase_manager.transition_to(EngagementPhase.DESIGN, approved_by="vp_sales")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_crm_scenario_design_phase(
        self,
        phase_manager,
        approval_manager,
        crm_mock_llm_responses,
    ):
        """
        Test CRM scenario - Design Phase.

        Expected duration: ~30 seconds
        """
        # Start in design phase
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # 1. Generate ontology
        ontology = json.loads(crm_mock_llm_responses["ontology"])
        assert len(ontology["entities"]) == 4  # Customer, Contact, Opportunity, Activity
        phase_manager.record_output("ontology_draft")

        # 2. Define schemas
        phase_manager.record_output("schema_definitions")
        phase_manager.record_output("data_models")

        # 3. Design transformations
        phase_manager.record_output("transformation_specs")
        phase_manager.record_output("validation_rules")

        # 4. Pass quality gates
        phase_manager.pass_quality_gate("ontology_validated", evidence={"linkml_valid": True})
        phase_manager.pass_quality_gate("schema_completeness", evidence={"coverage": 1.0})
        phase_manager.pass_quality_gate("data_model_review", evidence={"reviewed": True})

        # 5. Get approval
        approval = await approval_manager.create_request(
            engagement_id="crm-test",
            approval_type=ApprovalType.CONFIGURATION,
            title="CRM Ontology Approval",
            description="Approve CRM data model",
            requested_by="ontology_designer",
        )

        await submit_approval(approval_manager, approval.id, True, "data_architect")
        phase_manager.receive_approval("design_approval", "data_architect")

        # 6. Transition to build
        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert status["completion_percentage"] == 100.0

        result = phase_manager.transition_to(EngagementPhase.BUILD, approved_by="data_architect")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_crm_scenario_build_phase(
        self,
        phase_manager,
        approval_manager,
        crm_mock_llm_responses,
    ):
        """
        Test CRM scenario - Build Phase.

        Expected duration: ~30 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        # 1. Compile ontology
        phase_manager.record_output("compiled_ontology")

        # 2. Build data pipelines
        phase_manager.record_output("data_pipelines")

        # 3. Generate UI
        ui_spec = json.loads(crm_mock_llm_responses["ui"])
        assert len(ui_spec["components"]) >= 5
        phase_manager.record_output("ui_components")

        # 4. Design workflows
        workflows = json.loads(crm_mock_llm_responses["workflow"])
        assert len(workflows["workflows"]) >= 3
        phase_manager.record_output("workflows")

        # 5. Configure integrations
        phase_manager.record_output("integrations")

        # 6. Pass quality gates
        phase_manager.pass_quality_gate("pipeline_tested", evidence={"tests_passed": 45})
        phase_manager.pass_quality_gate("ui_validated", evidence={"a11y_score": 95})
        phase_manager.pass_quality_gate("security_review", evidence={"vulnerabilities": 0})

        # 7. Get approvals
        phase_manager.receive_approval("build_approval", "tech_lead")
        phase_manager.receive_approval("security_sign_off", "security_team")

        # 8. Transition to deploy
        result = phase_manager.transition_to(EngagementPhase.DEPLOY, approved_by="tech_lead")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_crm_scenario_deploy_phase(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test CRM scenario - Deploy Phase.

        Expected duration: ~30 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DEPLOY)

        # 1. Generate deployment config
        phase_manager.record_output("deployment_config")

        # 2. Setup environment
        phase_manager.record_output("environment_setup")

        # 3. Verify deployment
        phase_manager.record_output("deployment_verification")

        # 4. Complete documentation
        phase_manager.record_output("documentation")
        phase_manager.record_output("training_materials")

        # 5. Pass quality gates
        phase_manager.pass_quality_gate("deployment_validated", evidence={"health_check": "passed"})
        phase_manager.pass_quality_gate("documentation_complete", evidence={"pages": 25})
        phase_manager.pass_quality_gate("user_acceptance", evidence={"uat_passed": True})

        # 6. Get approvals
        phase_manager.receive_approval("deployment_approval", "ops_lead")
        phase_manager.receive_approval("client_sign_off", "vp_sales")

        # 7. Complete engagement
        result = phase_manager.transition_to(EngagementPhase.COMPLETE, approved_by="vp_sales")
        assert result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.COMPLETE

    @pytest.mark.asyncio
    async def test_crm_scenario_full_lifecycle(
        self,
        e2e_client,
        phase_manager,
        approval_manager,
        mock_event_bus,
        crm_mock_llm_responses,
    ):
        """
        Test complete CRM scenario from start to finish.

        This is the main integration test for the CRM use case.

        Expected duration: 3-5 minutes
        """
        # ===== 1. CREATE ENGAGEMENT =====
        engagement = await e2e_client.create_engagement(
            name=generate_test_engagement_name("Full CRM Lifecycle"),
            objective="Complete CRM analytics platform implementation",
            priority="high",
        )
        engagement_id = engagement["id"]

        # ===== 2. DISCOVERY PHASE =====
        assert phase_manager.get_current_phase() == EngagementPhase.DISCOVERY

        complete_phase_requirements(
            phase_manager,
            outputs=["stakeholder_map", "requirements", "discovered_sources", "source_assessments", "source_recommendations"],
            gates=["stakeholder_coverage", "data_sources_validated", "requirements_documented"],
            approvals=["discovery_sign_off"],
        )

        phase_manager.transition_to(EngagementPhase.DESIGN, approved_by="test")

        # ===== 3. DESIGN PHASE =====
        assert phase_manager.get_current_phase() == EngagementPhase.DESIGN

        complete_phase_requirements(
            phase_manager,
            outputs=["ontology_draft", "schema_definitions", "data_models", "transformation_specs", "validation_rules"],
            gates=["ontology_validated", "schema_completeness", "data_model_review"],
            approvals=["design_approval"],
            phase=EngagementPhase.DESIGN,
        )

        phase_manager.transition_to(EngagementPhase.BUILD, approved_by="test")

        # ===== 4. BUILD PHASE =====
        assert phase_manager.get_current_phase() == EngagementPhase.BUILD

        complete_phase_requirements(
            phase_manager,
            outputs=["compiled_ontology", "data_pipelines", "ui_components", "workflows", "integrations"],
            gates=["pipeline_tested", "ui_validated", "security_review"],
            approvals=["build_approval", "security_sign_off"],
            phase=EngagementPhase.BUILD,
        )

        phase_manager.transition_to(EngagementPhase.DEPLOY, approved_by="test")

        # ===== 5. DEPLOY PHASE =====
        assert phase_manager.get_current_phase() == EngagementPhase.DEPLOY

        complete_phase_requirements(
            phase_manager,
            outputs=["deployment_config", "environment_setup", "deployment_verification", "documentation", "training_materials"],
            gates=["deployment_validated", "documentation_complete", "user_acceptance"],
            approvals=["deployment_approval", "client_sign_off"],
            phase=EngagementPhase.DEPLOY,
        )

        phase_manager.transition_to(EngagementPhase.COMPLETE, approved_by="test")

        # ===== 6. VERIFY COMPLETION =====
        assert phase_manager.get_current_phase() == EngagementPhase.COMPLETE

        summary = phase_manager.get_phase_summary()
        assert len(summary["history"]) == 4  # 4 phase transitions

        # Verify all phases completed
        for phase in [EngagementPhase.DISCOVERY, EngagementPhase.DESIGN, EngagementPhase.BUILD, EngagementPhase.DEPLOY]:
            phase_data = summary["phases"][phase.value]
            assert phase_data["is_complete"]
            assert phase_data["completion_percentage"] == 100.0
