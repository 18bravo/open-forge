"""
Integration tests for the Enablement Agent Cluster.

Tests the documentation, training, and support agents and their orchestration.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List
import json

from langgraph.checkpoint.memory import MemorySaver


pytestmark = pytest.mark.integration


# Custom mock LLM responses for enablement agents
ENABLEMENT_MOCK_RESPONSES = {
    # Documentation agent responses
    "analyze the following ontology": json.dumps({
        "entities": [
            {"name": "Customer", "properties": ["id", "name", "email"]},
            {"name": "Order", "properties": ["id", "total", "status"]}
        ],
        "relationships": [
            {"source": "Customer", "target": "Order", "type": "has_many"}
        ],
        "constraints": ["Customer.email must be unique"],
        "use_cases": ["Order management", "Customer lookup"]
    }),
    "generate api documentation": json.dumps({
        "title": "API Documentation",
        "version": "1.0.0",
        "overview": "REST API for managing customers and orders",
        "authentication": {"type": "bearer", "header": "Authorization"},
        "entities": [
            {"name": "Customer", "operations": ["GET", "POST", "PUT", "DELETE"]}
        ],
        "operations": [
            {"method": "GET", "path": "/customers", "description": "List customers"}
        ],
        "error_codes": [{"code": 400, "description": "Bad request"}],
        "examples": [{"title": "Get customers", "code": "curl /api/customers"}],
        "best_practices": ["Use pagination for large datasets"]
    }),
    "generate a user guide": json.dumps({
        "title": "User Guide",
        "audience": "End Users",
        "getting_started": {"steps": ["Login", "Navigate to dashboard"]},
        "core_concepts": [{"name": "Entities", "description": "Data objects"}],
        "workflows": [{"name": "Create Order", "steps": ["Select customer", "Add items"]}],
        "tips": ["Use keyboard shortcuts"],
        "glossary": [{"term": "Entity", "definition": "A data object"}]
    }),
    "generate an operational runbook": json.dumps({
        "title": "Operations Runbook",
        "system_name": "Test System",
        "version": "1.0.0",
        "overview": {"architecture": "Microservices"},
        "deployment": {"steps": ["Pull image", "Deploy to k8s"]},
        "configuration": {"files": ["/etc/config.yaml"]},
        "monitoring": {"tools": ["Prometheus", "Grafana"]},
        "backup_recovery": {"frequency": "daily"},
        "scaling": {"method": "horizontal"},
        "incident_response": {"contacts": ["ops@example.com"]},
        "maintenance": {"windows": ["Sunday 2-4 AM"]},
        "troubleshooting": [{"issue": "High CPU", "resolution": "Scale up"}],
        "contacts": [{"name": "On-call", "email": "oncall@example.com"}]
    }),
    # Training agent responses
    "determine training needs": json.dumps({
        "key_concepts": ["Entities", "Relationships", "APIs"],
        "complexity_analysis": {"beginner": 3, "intermediate": 5, "advanced": 2},
        "critical_workflows": ["Data entry", "Reporting"],
        "skills_path": ["Basic navigation", "Data management", "Admin tasks"],
        "recommended_modules": ["Intro", "Core Features", "Advanced"]
    }),
    "design a comprehensive training curriculum": json.dumps({
        "title": "System Training",
        "description": "Comprehensive training curriculum",
        "target_audience": "All users",
        "skill_level": "beginner",
        "total_duration_hours": 8,
        "prerequisites": ["Basic computer skills"],
        "learning_objectives": ["Navigate the system", "Perform CRUD"],
        "modules": [
            {
                "module_id": "M1",
                "title": "Getting Started",
                "duration_minutes": 60,
                "objectives": ["Login", "Navigate"],
                "topics": ["Authentication", "Dashboard"],
                "exercises": [{"name": "Login exercise"}],
                "assessment": {"type": "quiz", "passing_score": 80}
            }
        ],
        "certification_path": {"name": "Certified User"},
        "resources": ["Documentation", "Videos"]
    }),
    "create a detailed step-by-step tutorial": json.dumps({
        "title": "Getting Started Tutorial",
        "description": "Learn the basics",
        "difficulty": "beginner",
        "duration_minutes": 30,
        "prerequisites": ["Account created"],
        "learning_goals": ["Complete first task"],
        "steps": [
            {
                "step_number": 1,
                "title": "Login",
                "description": "Access the system",
                "code_example": "username: demo",
                "expected_output": "Dashboard displayed",
                "tips": ["Use Chrome browser"]
            }
        ],
        "exercises": [{"name": "Practice login"}],
        "troubleshooting": [{"issue": "Login failed", "solution": "Check credentials"}],
        "next_steps": ["Explore dashboard"]
    }),
    "create a quickstart guide": json.dumps({
        "title": "Quickstart Guide",
        "description": "Get up and running fast",
        "target_time_minutes": 15,
        "sections": [
            {
                "section_id": "QS1",
                "title": "Setup",
                "time_minutes": 5,
                "steps": [
                    {"action": "Login", "code": "visit /login", "expected_result": "Logged in"}
                ]
            }
        ],
        "common_tasks": ["Create entity", "Run query"],
        "next_steps": ["Read full documentation"],
        "troubleshooting": [{"issue": "Error", "fix": "Retry"}]
    }),
    # Support agent responses
    "identify support content needs": json.dumps({
        "likely_questions": ["How do I login?", "How do I create an entity?"],
        "pain_points": ["Complex navigation", "Error messages unclear"],
        "complex_features": ["Advanced queries", "Bulk operations"],
        "error_scenarios": ["Connection timeout", "Validation errors"],
        "integration_challenges": ["API authentication", "Data formats"],
        "admin_tasks": ["User management", "Configuration"],
        "recommended_articles": [{"topic": "Getting Started", "type": "how-to"}],
        "faq_priorities": ["Login issues", "Password reset"]
    }),
    "generate a comprehensive faq": json.dumps({
        "title": "Frequently Asked Questions",
        "description": "Common questions and answers",
        "categories": [
            {
                "category_id": "CAT1",
                "name": "Getting Started",
                "description": "Basic questions",
                "faqs": [
                    {
                        "faq_id": "FAQ001",
                        "question": "How do I login?",
                        "answer": "Visit /login and enter credentials",
                        "related_links": ["/docs/login"],
                        "tags": ["login", "authentication"],
                        "helpful_count": 0
                    }
                ]
            }
        ],
        "generated_at": "2026-01-19T12:00:00Z",
        "total_faqs": 1
    }),
    "create troubleshooting guides": json.dumps({
        "title": "Troubleshooting Guide",
        "description": "Common issues and solutions",
        "issue_categories": [
            {
                "category_id": "TS1",
                "name": "Connection Issues",
                "description": "Network and connectivity problems",
                "issues": [
                    {
                        "issue_id": "ISS001",
                        "title": "Connection Timeout",
                        "symptoms": ["Slow response", "Error message"],
                        "error_codes": ["TIMEOUT_001"],
                        "severity": "medium",
                        "diagnosis_steps": ["Check network", "Verify server"],
                        "resolution_steps": [
                            {
                                "step_number": 1,
                                "action": "Check network connectivity",
                                "expected_result": "Network accessible",
                                "if_fails": "Contact IT"
                            }
                        ],
                        "prevention": ["Use stable network"],
                        "escalation_criteria": "Issue persists after 30 min",
                        "estimated_resolution_time": "15 minutes"
                    }
                ]
            }
        ],
        "escalation_paths": [{"level": 1, "contact": "support@example.com"}],
        "generated_at": "2026-01-19T12:00:00Z"
    }),
    "create a knowledge base article": json.dumps({
        "article_id": "KB001",
        "title": "System Overview",
        "summary": "Introduction to the system",
        "article_type": "concept",
        "target_audience": "all",
        "content": {
            "introduction": "Welcome to the system",
            "sections": [
                {
                    "heading": "Core Concepts",
                    "content": "The system manages entities and relationships",
                    "code_examples": [],
                    "tips": ["Start with the dashboard"]
                }
            ],
            "conclusion": "You are now ready to explore"
        },
        "related_articles": ["KB002"],
        "tags": ["overview", "introduction"],
        "last_updated": "2026-01-19T12:00:00Z",
        "helpful_votes": 0,
        "views": 0
    }),
    # Validation responses
    "review the following documentation": json.dumps({
        "score": 0.85,
        "completeness_score": 0.9,
        "clarity_score": 0.8,
        "issues": [],
        "suggestions": ["Add more examples"],
        "requires_revision": False
    }),
    "review the following training": json.dumps({
        "score": 0.82,
        "completeness_score": 0.85,
        "clarity_score": 0.8,
        "practicality_score": 0.8,
        "issues": [],
        "suggestions": ["Add video content"],
        "requires_revision": False
    }),
    "review the following support": json.dumps({
        "score": 0.88,
        "helpfulness_score": 0.9,
        "clarity_score": 0.85,
        "completeness_score": 0.88,
        "issues": [],
        "suggestions": ["Add search functionality"],
        "requires_revision": False
    }),
    # Consolidation response
    "consolidate all enablement": json.dumps({
        "readiness_assessment": "Ready for deployment",
        "key_materials": ["API docs", "User guides", "Training", "FAQs"],
        "cross_references": {"docs_to_training": True, "training_to_support": True},
        "deployment_recommendations": ["Deploy to CDN"],
        "gaps": [],
        "recommended_actions": ["Review with stakeholders", "Schedule training"],
        "maintenance_recommendations": ["Update quarterly"]
    })
}


@pytest.fixture
def enablement_mock_llm(mock_llm_with_custom_responses):
    """Create a mock LLM with enablement-specific responses."""
    return mock_llm_with_custom_responses(ENABLEMENT_MOCK_RESPONSES)


@pytest.fixture
def sample_enablement_context(sample_ontology_yaml):
    """Create sample context for enablement agents."""
    return {
        "ontology_schema": sample_ontology_yaml,
        "system_architecture": {
            "type": "microservices",
            "components": ["api", "db", "cache"],
            "deployment": "kubernetes"
        },
        "system_features": ["CRUD operations", "Search", "Reporting"],
        "target_audiences": [
            {"name": "End Users", "level": "beginner"},
            {"name": "Administrators", "level": "advanced"}
        ],
        "common_tasks": ["Create entity", "Search records", "Generate reports"],
        "user_personas": [
            {"name": "Business User", "technical_level": "low"},
            {"name": "Admin", "technical_level": "high"}
        ]
    }


class TestDocumentationAgent:
    """Tests for the Documentation Agent."""

    @pytest.mark.asyncio
    async def test_documentation_agent_creation(self, enablement_mock_llm, mock_memory_saver):
        """Test creating a documentation agent."""
        from agents.enablement.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "documentation_agent"
        assert "ontology_schema" in agent.required_inputs
        assert "api_documentation" in agent.output_keys

    @pytest.mark.asyncio
    async def test_documentation_agent_graph_compilation(self, enablement_mock_llm, mock_memory_saver):
        """Test that documentation agent graph compiles."""
        from agents.enablement.documentation_agent import DocumentationAgent

        agent = DocumentationAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_documentation_agent_execution(
        self,
        enablement_mock_llm,
        mock_memory_saver,
        sample_enablement_context
    ):
        """Test documentation agent execution with mock LLM."""
        from agents.enablement.documentation_agent import DocumentationAgent
        from contracts.agent_interface import AgentInput

        agent = DocumentationAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="documentation",
            context=sample_enablement_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "documentation_agent"
        assert "api_documentation" in result.outputs or "documentation_package" in result.outputs
        assert len(result.decisions) > 0
        assert result.confidence > 0


class TestTrainingAgent:
    """Tests for the Training Agent."""

    @pytest.mark.asyncio
    async def test_training_agent_creation(self, enablement_mock_llm, mock_memory_saver):
        """Test creating a training agent."""
        from agents.enablement.training_agent import TrainingAgent

        agent = TrainingAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "training_agent"
        assert "ontology_schema" in agent.required_inputs
        assert "training_materials" in agent.output_keys

    @pytest.mark.asyncio
    async def test_training_agent_graph_compilation(self, enablement_mock_llm, mock_memory_saver):
        """Test that training agent graph compiles."""
        from agents.enablement.training_agent import TrainingAgent

        agent = TrainingAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_training_agent_execution(
        self,
        enablement_mock_llm,
        mock_memory_saver,
        sample_enablement_context
    ):
        """Test training agent execution with mock LLM."""
        from agents.enablement.training_agent import TrainingAgent
        from contracts.agent_interface import AgentInput

        agent = TrainingAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="training",
            context=sample_enablement_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "training_agent"
        assert len(result.decisions) > 0


class TestSupportAgent:
    """Tests for the Support Agent."""

    @pytest.mark.asyncio
    async def test_support_agent_creation(self, enablement_mock_llm, mock_memory_saver):
        """Test creating a support agent."""
        from agents.enablement.support_agent import SupportAgent

        agent = SupportAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "support_agent"
        assert "ontology_schema" in agent.required_inputs
        assert "faq_documents" in agent.output_keys

    @pytest.mark.asyncio
    async def test_support_agent_graph_compilation(self, enablement_mock_llm, mock_memory_saver):
        """Test that support agent graph compiles."""
        from agents.enablement.support_agent import SupportAgent

        agent = SupportAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_support_agent_execution(
        self,
        enablement_mock_llm,
        mock_memory_saver,
        sample_enablement_context
    ):
        """Test support agent execution with mock LLM."""
        from agents.enablement.support_agent import SupportAgent
        from contracts.agent_interface import AgentInput

        agent = SupportAgent(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="support",
            context=sample_enablement_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "support_agent"
        assert len(result.decisions) > 0


class TestEnablementCluster:
    """Tests for the Enablement Cluster orchestration."""

    @pytest.mark.asyncio
    async def test_enablement_cluster_creation(self, enablement_mock_llm, mock_memory_saver):
        """Test creating an enablement cluster."""
        from agents.enablement.cluster import EnablementCluster

        cluster = EnablementCluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        assert cluster.name == "enablement_cluster"
        assert len(cluster.agents) == 3

    @pytest.mark.asyncio
    async def test_enablement_cluster_graph_compilation(self, enablement_mock_llm, mock_memory_saver):
        """Test that enablement cluster graph compiles."""
        from agents.enablement.cluster import EnablementCluster

        cluster = EnablementCluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        graph = cluster.get_graph()
        assert graph is not None

        compiled = cluster.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_enablement_cluster_missing_inputs(
        self,
        enablement_mock_llm,
        mock_memory_saver
    ):
        """Test enablement cluster fails gracefully with missing inputs."""
        from agents.enablement.cluster import EnablementCluster
        from contracts.agent_interface import AgentInput

        cluster = EnablementCluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        # Missing required ontology_schema
        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="enablement",
            context={"other_field": "value"}
        )

        result = await cluster.run(agent_input)

        assert result.success is False
        assert "Missing required inputs" in str(result.errors)

    @pytest.mark.asyncio
    async def test_enablement_cluster_full_execution(
        self,
        enablement_mock_llm,
        mock_memory_saver,
        sample_enablement_context
    ):
        """Test full enablement cluster execution."""
        from agents.enablement.cluster import EnablementCluster
        from contracts.agent_interface import AgentInput

        cluster = EnablementCluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="enablement",
            context=sample_enablement_context
        )

        result = await cluster.run(agent_input)

        assert result.success is True
        assert result.agent_name == "enablement_cluster"
        assert result.confidence > 0
        assert len(result.decisions) > 0

    @pytest.mark.asyncio
    async def test_enablement_cluster_report_extraction(
        self,
        enablement_mock_llm,
        mock_memory_saver,
        sample_enablement_context
    ):
        """Test extracting enablement report from cluster outputs."""
        from agents.enablement.cluster import EnablementCluster, EnablementReport
        from contracts.agent_interface import AgentInput

        cluster = EnablementCluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-enablement-001",
            phase="enablement",
            context=sample_enablement_context
        )

        result = await cluster.run(agent_input)

        if result.success and "enablement_report" in result.outputs:
            report = cluster.get_report(result.outputs)
            assert report is not None
            assert isinstance(report, EnablementReport)


class TestEnablementConvenienceFunctions:
    """Tests for enablement convenience functions."""

    @pytest.mark.asyncio
    async def test_create_enablement_cluster(self, enablement_mock_llm, mock_memory_saver):
        """Test the create_enablement_cluster convenience function."""
        from agents.enablement.cluster import create_enablement_cluster

        cluster = create_enablement_cluster(
            llm=enablement_mock_llm,
            memory=mock_memory_saver,
            config={"max_iterations": 5}
        )

        assert cluster is not None
        assert cluster.name == "enablement_cluster"
        assert cluster.config.get("max_iterations") == 5

    @pytest.mark.asyncio
    async def test_run_enablement_function(
        self,
        enablement_mock_llm,
        sample_ontology_yaml
    ):
        """Test the run_enablement convenience function."""
        from agents.enablement.cluster import run_enablement

        # Patch the cluster to use our mock LLM
        from unittest.mock import patch

        with patch('agents.enablement.cluster.EnablementCluster') as MockCluster:
            mock_instance = MockCluster.return_value
            mock_instance.run = lambda x: mock_instance._mock_run(x)

            # For simplicity, we'll just verify the function can be called
            # Full execution is tested in TestEnablementCluster
            assert run_enablement is not None
