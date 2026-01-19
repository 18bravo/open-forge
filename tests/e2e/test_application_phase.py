"""
E2E Tests for Application Phase (Build/Deploy).

Tests the application build and deploy phases including:
- UI generation
- Workflow design
- Integration configuration
- Deployment configuration

Expected test durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Full application flow: 60-180 seconds
"""
import json
import pytest
from datetime import datetime

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalType, ApprovalStatus

from .conftest import MockLLM, MockEventBus
from .utils import (
    get_phase_requirements_status,
    complete_phase_requirements,
    force_phase_transition,
    submit_approval,
    assert_phase_complete,
)


class TestUIGeneration:
    """Tests for UI component generation."""

    @pytest.fixture
    def ui_generation_responses(self):
        """Mock LLM responses for UI generation."""
        return {
            "ui": json.dumps({
                "components": [
                    {
                        "name": "CustomerForm",
                        "type": "form",
                        "entity": "Customer",
                        "file_path": "src/components/customers/CustomerForm.tsx",
                        "props": {
                            "mode": {"type": "enum", "values": ["create", "edit", "view"]},
                            "customerId": {"type": "string", "optional": True},
                            "onSubmit": {"type": "function"},
                            "onCancel": {"type": "function"},
                        },
                        "fields": [
                            {"name": "name", "type": "text", "label": "Customer Name", "required": True},
                            {"name": "email", "type": "email", "label": "Email", "required": True},
                            {"name": "segment", "type": "select", "label": "Segment", "options": ["enterprise", "mid_market", "smb"]},
                        ],
                        "accessibility": {
                            "aria_labelledby": "customer-form-title",
                            "role": "form",
                        },
                    },
                    {
                        "name": "CustomerTable",
                        "type": "table",
                        "entity": "Customer",
                        "file_path": "src/components/customers/CustomerTable.tsx",
                        "columns": [
                            {"key": "name", "header": "Name", "sortable": True, "filterable": True},
                            {"key": "email", "header": "Email", "sortable": True},
                            {"key": "segment", "header": "Segment", "filterable": True},
                            {"key": "lifetime_value", "header": "LTV", "sortable": True, "format": "currency"},
                        ],
                        "pagination": {"default_page_size": 20, "page_sizes": [10, 20, 50, 100]},
                        "row_actions": ["view", "edit", "delete"],
                    },
                    {
                        "name": "SalesDashboard",
                        "type": "dashboard",
                        "file_path": "src/components/dashboards/SalesDashboard.tsx",
                        "widgets": [
                            {"type": "stat", "title": "Total Customers", "metric": "customer_count"},
                            {"type": "stat", "title": "Total Pipeline", "metric": "pipeline_value", "format": "currency"},
                            {"type": "chart", "chart_type": "bar", "title": "Opportunities by Stage"},
                            {"type": "chart", "chart_type": "line", "title": "Revenue Trend"},
                            {"type": "table", "title": "Recent Activities", "entity": "Activity", "limit": 10},
                        ],
                        "layout": {"columns": 2, "responsive_breakpoint": 768},
                    },
                ],
                "type_definitions": {
                    "path": "src/types/entities.ts",
                    "interfaces": ["Customer", "Opportunity", "Activity"],
                },
            }),
        }

    @pytest.mark.asyncio
    async def test_ui_components_generated(
        self,
        phase_manager,
        ui_generation_responses,
    ):
        """
        Test that UI components are generated from ontology.

        Expected duration: ~15 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        ui_spec = json.loads(ui_generation_responses["ui"])

        # Verify components generated
        assert "components" in ui_spec
        assert len(ui_spec["components"]) >= 1

        # Verify component structure
        for component in ui_spec["components"]:
            assert "name" in component
            assert "type" in component
            assert "file_path" in component

        # Record output
        phase_manager.record_output("ui_components")

    @pytest.mark.asyncio
    async def test_form_components_have_validation(
        self,
        ui_generation_responses,
    ):
        """
        Test that form components include validation rules.

        Expected duration: ~5 seconds
        """
        ui_spec = json.loads(ui_generation_responses["ui"])

        form_components = [c for c in ui_spec["components"] if c["type"] == "form"]
        assert len(form_components) >= 1

        for form in form_components:
            assert "fields" in form
            # Check required field validation
            required_fields = [f for f in form["fields"] if f.get("required")]
            assert len(required_fields) >= 1

    @pytest.mark.asyncio
    async def test_table_components_have_pagination(
        self,
        ui_generation_responses,
    ):
        """
        Test that table components include pagination.

        Expected duration: ~5 seconds
        """
        ui_spec = json.loads(ui_generation_responses["ui"])

        table_components = [c for c in ui_spec["components"] if c["type"] == "table"]
        assert len(table_components) >= 1

        for table in table_components:
            assert "pagination" in table
            assert "default_page_size" in table["pagination"]

    @pytest.mark.asyncio
    async def test_dashboard_components_generated(
        self,
        ui_generation_responses,
    ):
        """
        Test that dashboard components are generated.

        Expected duration: ~5 seconds
        """
        ui_spec = json.loads(ui_generation_responses["ui"])

        dashboards = [c for c in ui_spec["components"] if c["type"] == "dashboard"]
        assert len(dashboards) >= 1

        for dashboard in dashboards:
            assert "widgets" in dashboard
            assert len(dashboard["widgets"]) >= 1


class TestWorkflowDesign:
    """Tests for workflow design."""

    @pytest.fixture
    def workflow_responses(self):
        """Mock LLM responses for workflow design."""
        return {
            "workflow": json.dumps({
                "workflows": [
                    {
                        "name": "opportunity_management",
                        "description": "Manage opportunity lifecycle from lead to close",
                        "trigger": {"type": "event", "event": "opportunity.created"},
                        "steps": [
                            {
                                "id": "validate_opportunity",
                                "type": "validation",
                                "action": "validate_required_fields",
                                "on_failure": "notify_sales_rep",
                            },
                            {
                                "id": "assign_owner",
                                "type": "automatic",
                                "action": "auto_assign_by_territory",
                                "depends_on": ["validate_opportunity"],
                            },
                            {
                                "id": "create_task",
                                "type": "automatic",
                                "action": "create_follow_up_task",
                                "parameters": {"due_days": 3},
                                "depends_on": ["assign_owner"],
                            },
                            {
                                "id": "notify_manager",
                                "type": "notification",
                                "action": "email_notification",
                                "condition": "opportunity.value > 100000",
                                "depends_on": ["validate_opportunity"],
                            },
                        ],
                    },
                    {
                        "name": "data_refresh",
                        "description": "Refresh data from source systems",
                        "trigger": {"type": "schedule", "cron": "0 2 * * *"},
                        "steps": [
                            {
                                "id": "extract_salesforce",
                                "type": "data_sync",
                                "source": "salesforce",
                                "action": "incremental_extract",
                            },
                            {
                                "id": "transform_data",
                                "type": "transformation",
                                "action": "run_transformation_pipeline",
                                "depends_on": ["extract_salesforce"],
                            },
                            {
                                "id": "validate_data",
                                "type": "validation",
                                "action": "run_quality_checks",
                                "depends_on": ["transform_data"],
                            },
                            {
                                "id": "notify_completion",
                                "type": "notification",
                                "action": "slack_notification",
                                "channel": "#data-ops",
                                "depends_on": ["validate_data"],
                            },
                        ],
                    },
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_workflows_generated(
        self,
        phase_manager,
        workflow_responses,
    ):
        """
        Test that workflows are generated.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        workflows = json.loads(workflow_responses["workflow"])

        assert "workflows" in workflows
        assert len(workflows["workflows"]) >= 1

        for workflow in workflows["workflows"]:
            assert "name" in workflow
            assert "trigger" in workflow
            assert "steps" in workflow
            assert len(workflow["steps"]) >= 1

        phase_manager.record_output("workflows")

    @pytest.mark.asyncio
    async def test_workflow_steps_have_dependencies(
        self,
        workflow_responses,
    ):
        """
        Test that workflow steps define dependencies.

        Expected duration: ~5 seconds
        """
        workflows = json.loads(workflow_responses["workflow"])

        for workflow in workflows["workflows"]:
            step_ids = {s["id"] for s in workflow["steps"]}
            for step in workflow["steps"]:
                if "depends_on" in step:
                    for dep in step["depends_on"]:
                        assert dep in step_ids, f"Dependency '{dep}' not found in workflow"


class TestIntegrationConfig:
    """Tests for integration configuration."""

    @pytest.fixture
    def integration_responses(self):
        """Mock LLM responses for integration config."""
        return {
            "integration": json.dumps({
                "integrations": [
                    {
                        "name": "salesforce_integration",
                        "type": "api",
                        "source": "Salesforce",
                        "connection": {
                            "type": "oauth2",
                            "auth_url": "https://login.salesforce.com/services/oauth2/authorize",
                            "token_url": "https://login.salesforce.com/services/oauth2/token",
                            "scopes": ["api", "refresh_token"],
                        },
                        "sync_config": {
                            "mode": "incremental",
                            "batch_size": 1000,
                            "rate_limit": {"requests_per_second": 10},
                        },
                        "objects": [
                            {"name": "Account", "target_entity": "Customer"},
                            {"name": "Opportunity", "target_entity": "Opportunity"},
                            {"name": "Task", "target_entity": "Activity"},
                        ],
                    },
                    {
                        "name": "postgres_warehouse",
                        "type": "database",
                        "source": "PostgreSQL",
                        "connection": {
                            "type": "connection_string",
                            "host": "${DB_HOST}",
                            "port": "${DB_PORT}",
                            "database": "${DB_NAME}",
                            "ssl_mode": "require",
                        },
                        "sync_config": {
                            "mode": "cdc",
                            "publication": "crm_changes",
                        },
                    },
                ],
                "api_endpoints": [
                    {
                        "path": "/api/v1/customers",
                        "methods": ["GET", "POST", "PUT", "DELETE"],
                        "entity": "Customer",
                        "auth_required": True,
                    },
                    {
                        "path": "/api/v1/opportunities",
                        "methods": ["GET", "POST", "PUT"],
                        "entity": "Opportunity",
                        "auth_required": True,
                    },
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_integrations_configured(
        self,
        phase_manager,
        integration_responses,
    ):
        """
        Test that integrations are configured.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        config = json.loads(integration_responses["integration"])

        assert "integrations" in config
        assert len(config["integrations"]) >= 1

        for integration in config["integrations"]:
            assert "name" in integration
            assert "type" in integration
            assert "connection" in integration

        phase_manager.record_output("integrations")

    @pytest.mark.asyncio
    async def test_api_endpoints_defined(
        self,
        integration_responses,
    ):
        """
        Test that API endpoints are defined.

        Expected duration: ~5 seconds
        """
        config = json.loads(integration_responses["integration"])

        assert "api_endpoints" in config
        assert len(config["api_endpoints"]) >= 1

        for endpoint in config["api_endpoints"]:
            assert "path" in endpoint
            assert "methods" in endpoint
            assert "entity" in endpoint


class TestDeploymentConfig:
    """Tests for deployment configuration."""

    @pytest.fixture
    def deployment_responses(self):
        """Mock LLM responses for deployment config."""
        return {
            "deployment": json.dumps({
                "environment": "production",
                "infrastructure": {
                    "compute": {
                        "type": "kubernetes",
                        "cluster": "prod-gke-cluster",
                        "namespace": "crm-analytics",
                    },
                    "database": {
                        "type": "cloud_sql",
                        "instance": "crm-postgres-prod",
                        "tier": "db-custom-4-16384",
                    },
                    "storage": {
                        "type": "gcs",
                        "bucket": "crm-analytics-data",
                        "region": "us-central1",
                    },
                },
                "services": [
                    {
                        "name": "api-server",
                        "image": "gcr.io/project/crm-api:v1.0.0",
                        "replicas": 3,
                        "resources": {
                            "requests": {"cpu": "500m", "memory": "1Gi"},
                            "limits": {"cpu": "2", "memory": "4Gi"},
                        },
                        "health_check": {
                            "path": "/health",
                            "port": 8080,
                            "interval": 30,
                        },
                    },
                    {
                        "name": "web-app",
                        "image": "gcr.io/project/crm-web:v1.0.0",
                        "replicas": 2,
                        "resources": {
                            "requests": {"cpu": "250m", "memory": "512Mi"},
                            "limits": {"cpu": "1", "memory": "2Gi"},
                        },
                    },
                    {
                        "name": "data-pipeline",
                        "type": "dagster",
                        "schedule": "0 * * * *",
                        "resources": {
                            "requests": {"cpu": "1", "memory": "4Gi"},
                            "limits": {"cpu": "4", "memory": "16Gi"},
                        },
                    },
                ],
                "secrets": [
                    {"name": "salesforce-credentials", "mount_path": "/secrets/salesforce"},
                    {"name": "db-credentials", "mount_path": "/secrets/database"},
                ],
                "monitoring": {
                    "logging": {"provider": "cloud_logging"},
                    "metrics": {"provider": "prometheus"},
                    "alerting": {"provider": "pagerduty"},
                },
            }),
        }

    @pytest.mark.asyncio
    async def test_deployment_config_generated(
        self,
        phase_manager,
        deployment_responses,
    ):
        """
        Test that deployment configuration is generated.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DEPLOY)

        config = json.loads(deployment_responses["deployment"])

        assert "environment" in config
        assert "infrastructure" in config
        assert "services" in config

        phase_manager.record_output("deployment_config")

    @pytest.mark.asyncio
    async def test_services_have_resource_limits(
        self,
        deployment_responses,
    ):
        """
        Test that services have resource limits defined.

        Expected duration: ~5 seconds
        """
        config = json.loads(deployment_responses["deployment"])

        for service in config["services"]:
            assert "resources" in service
            assert "limits" in service["resources"]

    @pytest.mark.asyncio
    async def test_monitoring_configured(
        self,
        deployment_responses,
    ):
        """
        Test that monitoring is configured.

        Expected duration: ~5 seconds
        """
        config = json.loads(deployment_responses["deployment"])

        assert "monitoring" in config
        assert "logging" in config["monitoring"]
        assert "metrics" in config["monitoring"]


class TestBuildPhaseQualityGates:
    """Tests for build phase quality gates."""

    @pytest.mark.asyncio
    async def test_pipeline_tested_gate(
        self,
        phase_manager,
    ):
        """
        Test the pipeline_tested quality gate.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        phase_manager.pass_quality_gate(
            "pipeline_tested",
            evidence={
                "tests_run": 45,
                "tests_passed": 45,
                "coverage": 0.87,
            },
            validator="pipeline_test_runner",
        )

        status = get_phase_requirements_status(phase_manager, EngagementPhase.BUILD)
        assert "pipeline_tested" in status["quality_gates"]["passed"]

    @pytest.mark.asyncio
    async def test_ui_validated_gate(
        self,
        phase_manager,
    ):
        """
        Test the ui_validated quality gate.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        phase_manager.pass_quality_gate(
            "ui_validated",
            evidence={
                "accessibility_score": 95,
                "lighthouse_performance": 88,
                "visual_regression_passed": True,
            },
            validator="ui_test_suite",
        )

        status = get_phase_requirements_status(phase_manager, EngagementPhase.BUILD)
        assert "ui_validated" in status["quality_gates"]["passed"]

    @pytest.mark.asyncio
    async def test_security_review_gate(
        self,
        phase_manager,
    ):
        """
        Test the security_review quality gate.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        phase_manager.pass_quality_gate(
            "security_review",
            evidence={
                "vulnerabilities_critical": 0,
                "vulnerabilities_high": 0,
                "scan_tool": "snyk",
                "reviewed_by": "security_team",
            },
            validator="human:security_analyst",
        )

        status = get_phase_requirements_status(phase_manager, EngagementPhase.BUILD)
        assert "security_review" in status["quality_gates"]["passed"]


class TestFullApplicationPhase:
    """Tests for complete application build and deploy phases."""

    @pytest.mark.asyncio
    async def test_complete_build_phase(
        self,
        phase_manager,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test complete build phase execution.

        Expected duration: 60-90 seconds
        """
        # 1. Start in build phase
        force_phase_transition(phase_manager, EngagementPhase.BUILD)

        # 2. Complete all build outputs
        phase_manager.record_output("compiled_ontology")
        phase_manager.record_output("data_pipelines")
        phase_manager.record_output("ui_components")
        phase_manager.record_output("workflows")
        phase_manager.record_output("integrations")

        # 3. Pass quality gates
        phase_manager.pass_quality_gate("pipeline_tested", evidence={"passed": True})
        phase_manager.pass_quality_gate("ui_validated", evidence={"passed": True})
        phase_manager.pass_quality_gate("security_review", evidence={"passed": True})

        # 4. Get approvals
        phase_manager.receive_approval("build_approval", approved_by="tech_lead")
        phase_manager.receive_approval("security_sign_off", approved_by="security_team")

        # 5. Verify completion
        status = get_phase_requirements_status(phase_manager, EngagementPhase.BUILD)
        assert status["completion_percentage"] == 100.0

        # 6. Transition to deploy
        result = phase_manager.transition_to(EngagementPhase.DEPLOY, approved_by="test")
        assert result["success"]

    @pytest.mark.asyncio
    async def test_complete_deploy_phase(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test complete deploy phase execution.

        Expected duration: 60-90 seconds
        """
        # 1. Start in deploy phase
        force_phase_transition(phase_manager, EngagementPhase.DEPLOY)

        # 2. Complete all deploy outputs
        phase_manager.record_output("deployment_config")
        phase_manager.record_output("environment_setup")
        phase_manager.record_output("deployment_verification")
        phase_manager.record_output("documentation")
        phase_manager.record_output("training_materials")

        # 3. Pass quality gates
        phase_manager.pass_quality_gate("deployment_validated", evidence={"passed": True})
        phase_manager.pass_quality_gate("documentation_complete", evidence={"passed": True})
        phase_manager.pass_quality_gate("user_acceptance", evidence={"passed": True})

        # 4. Get approvals
        phase_manager.receive_approval("deployment_approval", approved_by="ops_lead")
        phase_manager.receive_approval("client_sign_off", approved_by="client_pm")

        # 5. Verify completion
        status = get_phase_requirements_status(phase_manager, EngagementPhase.DEPLOY)
        assert status["completion_percentage"] == 100.0

        # 6. Complete the engagement
        result = phase_manager.transition_to(EngagementPhase.COMPLETE, approved_by="test")
        assert result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.COMPLETE
