"""
End-to-End Tests for Open Forge.

This package contains comprehensive E2E tests that verify the complete
user journey through the Open Forge platform.

Test Categories:
- test_engagement_lifecycle.py: Full engagement lifecycle tests
- test_discovery_phase.py: Discovery phase E2E tests
- test_data_foundation_phase.py: Data foundation/design phase tests
- test_application_phase.py: Build and deploy phase tests
- test_human_interaction.py: Human-in-the-loop tests
- test_api_e2e.py: REST and GraphQL API tests

Scenarios:
- scenarios/test_simple_crm.py: Complete CRM use case
- scenarios/test_data_platform.py: Enterprise data platform use case

Fixtures:
- fixtures/sample_engagement.json: Sample engagement configuration
- fixtures/sample_ontology.yaml: Sample LinkML ontology
- fixtures/mock_data_source.json: Mock data source configurations

Running Tests:
    # Run all E2E tests
    pytest tests/e2e -v

    # Run specific test file
    pytest tests/e2e/test_engagement_lifecycle.py -v

    # Run scenario tests
    pytest tests/e2e/scenarios -v

    # Run with coverage
    pytest tests/e2e -v --cov=packages

Expected Test Durations:
- Quick tests: 5 seconds
- Standard tests: 30 seconds
- Extended tests: 60-120 seconds
- Full scenario tests: 3-8 minutes
"""
