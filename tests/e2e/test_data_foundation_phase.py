"""
E2E Tests for Data Foundation Phase (Design Phase).

Tests the data foundation/design phase including:
- Ontology design from requirements
- Schema validation
- Transformation design
- Ontology approval

Expected test durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Full design flow: 60-120 seconds
"""
import json
import pytest
from datetime import datetime

from agents.orchestrator.phase_manager import EngagementPhase, PhaseManager
from human_interaction.approvals import ApprovalManager, ApprovalType, ApprovalStatus

from .conftest import MockLLM, MockEventBus
from .utils import (
    wait_for_phase,
    get_phase_requirements_status,
    complete_phase_requirements,
    force_phase_transition,
    submit_approval,
    assert_phase_complete,
)


class TestOntologyDesign:
    """Tests for ontology design from requirements."""

    @pytest.fixture
    def ontology_design_responses(self):
        """Mock LLM responses for ontology design."""
        return {
            "ontology": json.dumps({
                "name": "CRM Analytics Ontology",
                "version": "1.0.0",
                "description": "Ontology for customer relationship management analytics",
                "entities": [
                    {
                        "name": "Customer",
                        "description": "A customer or prospect",
                        "attributes": [
                            {"name": "id", "type": "uuid", "required": True, "primary_key": True},
                            {"name": "name", "type": "string", "required": True, "max_length": 255},
                            {"name": "email", "type": "email", "required": True, "unique": True},
                            {"name": "segment", "type": "enum", "values": ["enterprise", "mid_market", "smb"]},
                            {"name": "created_at", "type": "datetime", "required": True},
                            {"name": "lifetime_value", "type": "decimal", "precision": 10, "scale": 2},
                        ],
                    },
                    {
                        "name": "Opportunity",
                        "description": "A sales opportunity",
                        "attributes": [
                            {"name": "id", "type": "uuid", "required": True, "primary_key": True},
                            {"name": "customer_id", "type": "uuid", "required": True, "foreign_key": "Customer.id"},
                            {"name": "name", "type": "string", "required": True},
                            {"name": "value", "type": "decimal", "required": True},
                            {"name": "stage", "type": "enum", "values": ["lead", "qualified", "proposal", "negotiation", "closed_won", "closed_lost"]},
                            {"name": "probability", "type": "decimal", "min": 0, "max": 1},
                            {"name": "expected_close_date", "type": "date"},
                        ],
                    },
                    {
                        "name": "Activity",
                        "description": "A customer interaction activity",
                        "attributes": [
                            {"name": "id", "type": "uuid", "required": True, "primary_key": True},
                            {"name": "customer_id", "type": "uuid", "required": True, "foreign_key": "Customer.id"},
                            {"name": "type", "type": "enum", "values": ["call", "email", "meeting", "demo"]},
                            {"name": "subject", "type": "string"},
                            {"name": "notes", "type": "text"},
                            {"name": "occurred_at", "type": "datetime", "required": True},
                        ],
                    },
                ],
                "relationships": [
                    {
                        "name": "customer_opportunities",
                        "from_entity": "Customer",
                        "to_entity": "Opportunity",
                        "type": "one_to_many",
                        "cascade_delete": False,
                    },
                    {
                        "name": "customer_activities",
                        "from_entity": "Customer",
                        "to_entity": "Activity",
                        "type": "one_to_many",
                        "cascade_delete": True,
                    },
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_ontology_generated_from_requirements(
        self,
        phase_manager,
        ontology_design_responses,
    ):
        """
        Test that ontology is generated from requirements.

        Expected duration: ~15 seconds
        """
        # First, move to design phase
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # Parse mock ontology response
        ontology = json.loads(ontology_design_responses["ontology"])

        # Verify ontology structure
        assert "name" in ontology
        assert "version" in ontology
        assert "entities" in ontology
        assert len(ontology["entities"]) >= 1

        # Verify entity structure
        for entity in ontology["entities"]:
            assert "name" in entity
            assert "attributes" in entity
            assert len(entity["attributes"]) >= 1

            # Verify attribute structure
            for attr in entity["attributes"]:
                assert "name" in attr
                assert "type" in attr

        # Verify relationships
        assert "relationships" in ontology
        for rel in ontology["relationships"]:
            assert "from_entity" in rel
            assert "to_entity" in rel
            assert "type" in rel

        # Record output
        phase_manager.record_output("ontology_draft")
        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert "ontology_draft" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_ontology_includes_all_identified_entities(
        self,
        phase_manager,
        ontology_design_responses,
    ):
        """
        Test that ontology includes all entities from requirements.

        Expected duration: ~10 seconds
        """
        ontology = json.loads(ontology_design_responses["ontology"])

        # Expected entities based on typical CRM requirements
        expected_entities = ["Customer", "Opportunity", "Activity"]

        entity_names = [e["name"] for e in ontology["entities"]]
        for expected in expected_entities:
            assert expected in entity_names, f"Expected entity '{expected}' not found"

    @pytest.mark.asyncio
    async def test_ontology_has_proper_relationships(
        self,
        ontology_design_responses,
    ):
        """
        Test that ontology relationships are properly defined.

        Expected duration: ~5 seconds
        """
        ontology = json.loads(ontology_design_responses["ontology"])

        # Verify relationships exist
        assert len(ontology["relationships"]) >= 1

        # Verify relationship entities exist
        entity_names = {e["name"] for e in ontology["entities"]}
        for rel in ontology["relationships"]:
            assert rel["from_entity"] in entity_names
            assert rel["to_entity"] in entity_names


class TestSchemaValidation:
    """Tests for schema validation."""

    @pytest.fixture
    def schema_validation_responses(self):
        """Mock LLM responses for schema validation."""
        return {
            "schema_valid": json.dumps({
                "valid": True,
                "entity_count": 3,
                "relationship_count": 2,
                "warnings": [
                    "Consider adding index on Customer.email for query performance",
                ],
                "suggestions": [
                    "Add updated_at timestamp to all entities",
                ],
            }),
            "schema_invalid": json.dumps({
                "valid": False,
                "errors": [
                    {
                        "type": "missing_primary_key",
                        "entity": "Activity",
                        "message": "Entity 'Activity' is missing a primary key",
                    },
                    {
                        "type": "invalid_foreign_key",
                        "entity": "Opportunity",
                        "field": "customer_id",
                        "message": "Foreign key references non-existent entity 'Customers'",
                    },
                ],
                "warnings": [],
            }),
        }

    @pytest.mark.asyncio
    async def test_valid_schema_passes_validation(
        self,
        phase_manager,
        schema_validation_responses,
    ):
        """
        Test that valid schema passes validation.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        validation = json.loads(schema_validation_responses["schema_valid"])

        assert validation["valid"]
        assert "errors" not in validation or len(validation.get("errors", [])) == 0

        # Record validation pass
        phase_manager.record_output("schema_definitions")
        phase_manager.pass_quality_gate(
            "schema_completeness",
            evidence={"entity_count": 3, "validation_passed": True},
        )

    @pytest.mark.asyncio
    async def test_invalid_schema_fails_validation(
        self,
        schema_validation_responses,
    ):
        """
        Test that invalid schema fails validation with errors.

        Expected duration: ~5 seconds
        """
        validation = json.loads(schema_validation_responses["schema_invalid"])

        assert not validation["valid"]
        assert len(validation["errors"]) > 0

        # Check error structure
        for error in validation["errors"]:
            assert "type" in error
            assert "message" in error

    @pytest.mark.asyncio
    async def test_validation_provides_warnings(
        self,
        schema_validation_responses,
    ):
        """
        Test that validation provides warnings for non-critical issues.

        Expected duration: ~5 seconds
        """
        validation = json.loads(schema_validation_responses["schema_valid"])

        assert "warnings" in validation
        # Warnings provide suggestions but don't block

    @pytest.mark.asyncio
    async def test_ontology_validation_gate(
        self,
        phase_manager,
    ):
        """
        Test the ontology_validated quality gate.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # Pass the ontology validation gate
        phase_manager.pass_quality_gate(
            "ontology_validated",
            evidence={
                "linkml_validation": "passed",
                "schema_consistency": "passed",
            },
            validator="schema_validator_agent",
        )

        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert "ontology_validated" in status["quality_gates"]["passed"]


class TestTransformationDesign:
    """Tests for data transformation design."""

    @pytest.fixture
    def transformation_responses(self):
        """Mock LLM responses for transformation design."""
        return {
            "transformation": json.dumps({
                "transformations": [
                    {
                        "name": "salesforce_to_customer",
                        "source": {
                            "system": "Salesforce",
                            "object": "Account",
                        },
                        "target": {
                            "entity": "Customer",
                        },
                        "mappings": [
                            {"source_field": "Id", "target_field": "id", "transform": "direct"},
                            {"source_field": "Name", "target_field": "name", "transform": "trim"},
                            {"source_field": "Email__c", "target_field": "email", "transform": "lowercase"},
                            {"source_field": "Industry", "target_field": "segment", "transform": "map_enum"},
                        ],
                        "filters": [
                            {"field": "IsDeleted", "operator": "equals", "value": False},
                        ],
                        "deduplication": {
                            "key_fields": ["email"],
                            "strategy": "keep_latest",
                        },
                    },
                    {
                        "name": "salesforce_to_opportunity",
                        "source": {
                            "system": "Salesforce",
                            "object": "Opportunity",
                        },
                        "target": {
                            "entity": "Opportunity",
                        },
                        "mappings": [
                            {"source_field": "Id", "target_field": "id", "transform": "direct"},
                            {"source_field": "AccountId", "target_field": "customer_id", "transform": "lookup"},
                            {"source_field": "Amount", "target_field": "value", "transform": "to_decimal"},
                            {"source_field": "StageName", "target_field": "stage", "transform": "map_enum"},
                        ],
                        "dependencies": ["salesforce_to_customer"],
                    },
                ],
                "validation_rules": [
                    {
                        "entity": "Customer",
                        "rule": "email_format",
                        "expression": "email MATCHES '^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$'",
                    },
                    {
                        "entity": "Opportunity",
                        "rule": "positive_value",
                        "expression": "value > 0",
                    },
                ],
            }),
        }

    @pytest.mark.asyncio
    async def test_transformations_defined_for_sources(
        self,
        phase_manager,
        transformation_responses,
    ):
        """
        Test that transformations are defined for discovered sources.

        Expected duration: ~15 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        transformations = json.loads(transformation_responses["transformation"])

        # Verify transformation structure
        assert "transformations" in transformations
        assert len(transformations["transformations"]) >= 1

        for xform in transformations["transformations"]:
            assert "name" in xform
            assert "source" in xform
            assert "target" in xform
            assert "mappings" in xform
            assert len(xform["mappings"]) >= 1

        # Record output
        phase_manager.record_output("transformation_specs")
        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert "transformation_specs" in status["outputs"]["completed"]

    @pytest.mark.asyncio
    async def test_transformation_includes_field_mappings(
        self,
        transformation_responses,
    ):
        """
        Test that transformations include proper field mappings.

        Expected duration: ~5 seconds
        """
        transformations = json.loads(transformation_responses["transformation"])

        for xform in transformations["transformations"]:
            for mapping in xform["mappings"]:
                assert "source_field" in mapping
                assert "target_field" in mapping
                assert "transform" in mapping

    @pytest.mark.asyncio
    async def test_validation_rules_defined(
        self,
        phase_manager,
        transformation_responses,
    ):
        """
        Test that validation rules are defined for data quality.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        transformations = json.loads(transformation_responses["transformation"])

        assert "validation_rules" in transformations
        assert len(transformations["validation_rules"]) >= 1

        for rule in transformations["validation_rules"]:
            assert "entity" in rule
            assert "rule" in rule
            assert "expression" in rule

        # Record output
        phase_manager.record_output("validation_rules")


class TestDataModelReview:
    """Tests for data model review and approval."""

    @pytest.mark.asyncio
    async def test_data_model_review_gate(
        self,
        phase_manager,
    ):
        """
        Test the data_model_review quality gate.

        Expected duration: ~10 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # This gate requires human review
        phase_manager.pass_quality_gate(
            "data_model_review",
            evidence={
                "reviewed_by": "data_architect",
                "review_comments": "Approved with minor suggestions",
                "review_date": datetime.utcnow().isoformat(),
            },
            validator="human:data_architect",
        )

        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert "data_model_review" in status["quality_gates"]["passed"]


class TestOntologyApproval:
    """Tests for ontology approval checkpoint."""

    @pytest.mark.asyncio
    async def test_ontology_approval_request_created(
        self,
        approval_manager,
        mock_event_bus,
    ):
        """
        Test that ontology approval request is created.

        Expected duration: ~5 seconds
        """
        approval = await approval_manager.create_request(
            engagement_id="test-engagement-001",
            approval_type=ApprovalType.CONFIGURATION,
            title="Ontology Design Approval",
            description="Review and approve the ontology design for CRM Analytics",
            requested_by="ontology_designer_agent",
            timeout_minutes=120,
            context_data={
                "entity_count": 3,
                "relationship_count": 2,
                "transformation_count": 2,
            },
        )

        assert approval.status == ApprovalStatus.PENDING
        assert "Ontology" in approval.title

    @pytest.mark.asyncio
    async def test_ontology_approval_enables_build_phase(
        self,
        phase_manager,
        approval_manager,
    ):
        """
        Test that ontology approval enables transition to BUILD.

        Expected duration: ~15 seconds
        """
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)

        # Complete all design outputs
        complete_phase_requirements(
            phase_manager,
            outputs=[
                "ontology_draft",
                "schema_definitions",
                "data_models",
                "transformation_specs",
                "validation_rules",
            ],
            gates=[
                "ontology_validated",
                "schema_completeness",
                "data_model_review",
            ],
            approvals=["design_approval"],
            phase=EngagementPhase.DESIGN,
        )

        # Verify transition is possible
        validation = phase_manager.validate_transition(EngagementPhase.BUILD)
        assert validation["valid"]

        # Perform transition
        result = phase_manager.transition_to(
            EngagementPhase.BUILD,
            approved_by="design_approver",
        )
        assert result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.BUILD


class TestFullDataFoundationPhase:
    """Tests for complete data foundation/design phase."""

    @pytest.mark.asyncio
    async def test_complete_design_phase(
        self,
        phase_manager,
        approval_manager,
        mock_event_bus,
        sample_ontology_data,
    ):
        """
        Test complete design phase from start to approval.

        Expected duration: 60-120 seconds
        """
        # 1. Start in design phase
        force_phase_transition(phase_manager, EngagementPhase.DESIGN)
        assert phase_manager.get_current_phase() == EngagementPhase.DESIGN

        # 2. Generate ontology draft
        phase_manager.record_output("ontology_draft")

        # 3. Create schema definitions
        phase_manager.record_output("schema_definitions")

        # 4. Define data models
        phase_manager.record_output("data_models")

        # 5. Design transformations
        phase_manager.record_output("transformation_specs")

        # 6. Define validation rules
        phase_manager.record_output("validation_rules")

        # 7. Pass quality gates
        phase_manager.pass_quality_gate(
            "ontology_validated",
            evidence={"linkml_valid": True},
            validator="schema_validator_agent",
        )
        phase_manager.pass_quality_gate(
            "schema_completeness",
            evidence={"coverage": 1.0},
            validator="schema_validator_agent",
        )
        phase_manager.pass_quality_gate(
            "data_model_review",
            evidence={"reviewed": True},
            validator="human:architect",
        )

        # 8. Create and process approval
        approval = await approval_manager.create_request(
            engagement_id="test-engagement-001",
            approval_type=ApprovalType.CONFIGURATION,
            title="Design Phase Approval",
            description="Approve ontology and transformation designs",
            requested_by="design_agent",
        )

        result = await submit_approval(
            approval_manager,
            approval.id,
            decision=True,
            decided_by="design_approver",
        )
        assert result["success"]

        # 9. Record approval
        phase_manager.receive_approval("design_approval", approved_by="design_approver")

        # 10. Verify completion
        status = get_phase_requirements_status(phase_manager, EngagementPhase.DESIGN)
        assert status["completion_percentage"] == 100.0

        # 11. Transition to build
        validation = phase_manager.validate_transition(EngagementPhase.BUILD)
        assert validation["valid"]

        result = phase_manager.transition_to(
            EngagementPhase.BUILD,
            approved_by="design_approver",
        )
        assert result["success"]
        assert phase_manager.get_current_phase() == EngagementPhase.BUILD
