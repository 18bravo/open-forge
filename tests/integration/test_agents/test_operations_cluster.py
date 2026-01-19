"""
Integration tests for the Operations Agent Cluster.

Tests the monitoring, scaling, maintenance, and incident agents and their orchestration.
"""
import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List
import json

from langgraph.checkpoint.memory import MemorySaver


pytestmark = pytest.mark.integration


# Custom mock LLM responses for operations agents
OPERATIONS_MOCK_RESPONSES = {
    # Monitoring agent responses
    "analyze the ontology": json.dumps({
        "entities": ["Customer", "Order"],
        "metrics_needed": ["request_count", "latency", "error_rate"],
        "relationships": ["Customer has many Orders"],
        "monitoring_requirements": ["Track entity CRUD operations"]
    }),
    "generate prometheus": json.dumps({
        "global": {"scrape_interval": "15s"},
        "scrape_configs": [
            {"job_name": "openforge-api", "static_configs": [{"targets": ["localhost:8000"]}]}
        ],
        "rule_files": ["alerts.yml"]
    }),
    "generate grafana": json.dumps([
        {
            "title": "Open Forge Dashboard",
            "panels": [
                {"title": "Request Rate", "type": "graph", "gridPos": {"x": 0, "y": 0, "w": 12, "h": 8}},
                {"title": "Error Rate", "type": "graph", "gridPos": {"x": 12, "y": 0, "w": 12, "h": 8}}
            ],
            "templating": {"list": []},
            "time": {"from": "now-1h", "to": "now"}
        }
    ]),
    "generate alerting rules": json.dumps([
        {
            "name": "HighErrorRate",
            "severity": "critical",
            "expr": "error_rate > 0.05",
            "for": "5m",
            "labels": {"severity": "critical"},
            "annotations": {"summary": "High error rate detected"}
        }
    ]),
    # Scaling agent responses
    "analyze workload": json.dumps({
        "current_load": {"requests_per_second": 100, "cpu_utilization": 0.6},
        "patterns": ["Daily peak at 2pm", "Weekend low"],
        "recommendations": {"min_replicas": 2, "max_replicas": 10}
    }),
    "generate kubernetes hpa": json.dumps([
        {
            "apiVersion": "autoscaling/v2",
            "kind": "HorizontalPodAutoscaler",
            "metadata": {"name": "openforge-api", "namespace": "default"},
            "spec": {
                "scaleTargetRef": {"apiVersion": "apps/v1", "kind": "Deployment", "name": "openforge-api"},
                "minReplicas": 2,
                "maxReplicas": 10,
                "metrics": [{"type": "Resource", "resource": {"name": "cpu", "target": {"type": "Utilization", "averageUtilization": 70}}}]
            }
        }
    ]),
    "generate load balancer": json.dumps({
        "ingress": {
            "apiVersion": "networking.k8s.io/v1",
            "kind": "Ingress",
            "metadata": {"name": "openforge-ingress"},
            "spec": {
                "rules": [{"host": "api.openforge.io", "http": {"paths": [{"path": "/", "pathType": "Prefix", "backend": {"service": {"name": "openforge-api", "port": {"number": 80}}}}]}}]
            }
        },
        "recommendations": {"use_cdn": True, "enable_rate_limiting": True}
    }),
    # Maintenance agent responses
    "analyze system components": json.dumps({
        "components": ["api", "database", "cache", "storage"],
        "backup_requirements": {"database": "daily", "storage": "weekly"},
        "maintenance_windows": ["Sunday 2-4 AM UTC"]
    }),
    "generate backup strategies": json.dumps([
        {
            "name": "Database Backup",
            "type": "database",
            "schedule": "0 2 * * *",
            "retention": "30d",
            "storage": "s3://backups/database",
            "method": "pg_dump"
        },
        {
            "name": "Configuration Backup",
            "type": "filesystem",
            "schedule": "0 3 * * 0",
            "retention": "90d",
            "storage": "s3://backups/config",
            "paths": ["/etc/openforge"]
        }
    ]),
    "generate maintenance schedules": json.dumps([
        {
            "name": "Routine Maintenance",
            "schedule": "0 3 * * 0",
            "type": "routine",
            "tasks": ["Clear logs", "Vacuum database", "Rotate secrets"],
            "duration_minutes": 30,
            "notification_required": True
        }
    ]),
    "generate health check": json.dumps([
        {
            "name": "API Health",
            "type": "http",
            "endpoint": "/health",
            "interval_seconds": 30,
            "timeout_seconds": 5,
            "expected_status": 200
        },
        {
            "name": "Database Health",
            "type": "tcp",
            "host": "localhost",
            "port": 5432,
            "interval_seconds": 30
        }
    ]),
    # Incident agent responses
    "analyze failure modes": json.dumps({
        "failure_modes": [
            {"type": "infrastructure", "examples": ["Database outage", "Network partition"]},
            {"type": "application", "examples": ["Memory leak", "Deadlock"]},
            {"type": "data", "examples": ["Corruption", "Invalid state"]}
        ],
        "critical_paths": ["User authentication", "Order processing"]
    }),
    "generate incident playbooks": json.dumps([
        {
            "name": "Database Outage",
            "severity": "SEV1",
            "symptoms": ["Connection errors", "Slow queries", "Timeouts"],
            "diagnosis_steps": ["Check database status", "Review logs", "Check disk space"],
            "resolution_steps": [
                {"step": 1, "action": "Verify database is running", "command": "systemctl status postgresql"},
                {"step": 2, "action": "Check connections", "command": "pg_isready"},
                {"step": 3, "action": "Restart if needed", "command": "systemctl restart postgresql"}
            ],
            "escalation": {"after_minutes": 15, "contact": "database-team"},
            "prevention": ["Monitor disk space", "Connection pool limits"]
        }
    ]),
    "generate escalation procedures": json.dumps([
        {
            "severity": "SEV1",
            "definition": "Critical service outage",
            "response_time_minutes": 15,
            "contacts": [
                {"role": "On-call Engineer", "method": "page"},
                {"role": "Engineering Manager", "method": "phone", "after_minutes": 30}
            ],
            "communication": {"channel": "#incidents", "update_frequency_minutes": 15}
        }
    ]),
    "generate postmortem templates": json.dumps([
        {
            "template_id": "comprehensive",
            "name": "Comprehensive Postmortem",
            "sections": [
                {"name": "Summary", "description": "Brief description of the incident"},
                {"name": "Impact", "description": "Who and what was affected"},
                {"name": "Timeline", "description": "Chronological events"},
                {"name": "Root Cause", "description": "What caused the incident"},
                {"name": "Resolution", "description": "How it was fixed"},
                {"name": "Action Items", "description": "Follow-up tasks"}
            ]
        }
    ]),
    # Validation responses
    "validate monitoring": json.dumps({
        "score": 0.85,
        "coverage": 0.9,
        "issues": [],
        "suggestions": ["Add custom metrics"],
        "requires_revision": False
    }),
    "validate scaling": json.dumps({
        "score": 0.88,
        "coverage": 0.85,
        "issues": [],
        "suggestions": ["Consider VPA"],
        "requires_revision": False
    }),
    "validate maintenance": json.dumps({
        "score": 0.82,
        "coverage": 0.8,
        "issues": [],
        "suggestions": ["Add disaster recovery tests"],
        "requires_revision": False
    }),
    "validate incident": json.dumps({
        "score": 0.86,
        "coverage": 0.85,
        "issues": [],
        "suggestions": ["Add runbook links"],
        "requires_revision": False
    }),
    # Consolidation response
    "consolidate all operations": json.dumps({
        "operations_readiness": "Ready for production",
        "key_configurations": ["Prometheus", "HPA", "Backup jobs", "Incident playbooks"],
        "integration_points": ["Grafana alerts to Slack", "HPA with custom metrics"],
        "deployment_recommendations": ["Deploy monitoring first", "Test backup restore"],
        "gaps": [],
        "recommended_actions": ["Train ops team on playbooks"],
        "training_recommendations": ["Incident response drill"]
    })
}


@pytest.fixture
def operations_mock_llm(mock_llm_with_custom_responses):
    """Create a mock LLM with operations-specific responses."""
    return mock_llm_with_custom_responses(OPERATIONS_MOCK_RESPONSES)


@pytest.fixture
def sample_operations_context(sample_ontology_yaml):
    """Create sample context for operations agents."""
    return {
        "ontology_schema": sample_ontology_yaml,
        "system_architecture": {
            "type": "microservices",
            "components": ["api", "database", "cache", "queue"],
            "deployment": "kubernetes",
            "cloud_provider": "aws"
        },
        "system_requirements": {
            "availability": "99.9%",
            "latency_p99_ms": 200,
            "throughput_rps": 1000
        },
        "workload_specs": {
            "average_load": {"rps": 100, "cpu": 0.5},
            "peak_load": {"rps": 500, "cpu": 0.9},
            "patterns": ["Business hours peak"]
        },
        "system_components": {
            "api": {"replicas": 3, "cpu": "1000m", "memory": "2Gi"},
            "database": {"type": "postgresql", "version": "15"},
            "cache": {"type": "redis", "version": "7"}
        },
        "team_structure": {
            "on_call": "platform-team",
            "escalation": ["team-lead", "eng-manager", "director"]
        },
        "namespace": "openforge",
        "domain": "openforge.io"
    }


class TestMonitoringAgent:
    """Tests for the Monitoring Agent."""

    @pytest.mark.asyncio
    async def test_monitoring_agent_creation(self, operations_mock_llm, mock_memory_saver):
        """Test creating a monitoring agent."""
        from agents.operations.monitoring_agent import MonitoringAgent

        agent = MonitoringAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "monitoring_agent"
        assert "ontology_schema" in agent.required_inputs

    @pytest.mark.asyncio
    async def test_monitoring_agent_graph_compilation(self, operations_mock_llm, mock_memory_saver):
        """Test that monitoring agent graph compiles."""
        from agents.operations.monitoring_agent import MonitoringAgent

        agent = MonitoringAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_monitoring_agent_execution(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test monitoring agent execution with mock LLM."""
        from agents.operations.monitoring_agent import MonitoringAgent
        from contracts.agent_interface import AgentInput

        agent = MonitoringAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="monitoring",
            context=sample_operations_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "monitoring_agent"
        assert len(result.decisions) > 0


class TestScalingAgent:
    """Tests for the Scaling Agent."""

    @pytest.mark.asyncio
    async def test_scaling_agent_creation(self, operations_mock_llm, mock_memory_saver):
        """Test creating a scaling agent."""
        from agents.operations.scaling_agent import ScalingAgent

        agent = ScalingAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "scaling_agent"

    @pytest.mark.asyncio
    async def test_scaling_agent_graph_compilation(self, operations_mock_llm, mock_memory_saver):
        """Test that scaling agent graph compiles."""
        from agents.operations.scaling_agent import ScalingAgent

        agent = ScalingAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_scaling_agent_execution(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test scaling agent execution with mock LLM."""
        from agents.operations.scaling_agent import ScalingAgent
        from contracts.agent_interface import AgentInput

        agent = ScalingAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="scaling",
            context=sample_operations_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "scaling_agent"
        assert len(result.decisions) > 0


class TestMaintenanceAgent:
    """Tests for the Maintenance Agent."""

    @pytest.mark.asyncio
    async def test_maintenance_agent_creation(self, operations_mock_llm, mock_memory_saver):
        """Test creating a maintenance agent."""
        from agents.operations.maintenance_agent import MaintenanceAgent

        agent = MaintenanceAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "maintenance_agent"

    @pytest.mark.asyncio
    async def test_maintenance_agent_graph_compilation(self, operations_mock_llm, mock_memory_saver):
        """Test that maintenance agent graph compiles."""
        from agents.operations.maintenance_agent import MaintenanceAgent

        agent = MaintenanceAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_maintenance_agent_execution(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test maintenance agent execution with mock LLM."""
        from agents.operations.maintenance_agent import MaintenanceAgent
        from contracts.agent_interface import AgentInput

        agent = MaintenanceAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="maintenance",
            context=sample_operations_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "maintenance_agent"
        assert len(result.decisions) > 0


class TestIncidentAgent:
    """Tests for the Incident Agent."""

    @pytest.mark.asyncio
    async def test_incident_agent_creation(self, operations_mock_llm, mock_memory_saver):
        """Test creating an incident agent."""
        from agents.operations.incident_agent import IncidentAgent

        agent = IncidentAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        assert agent.name == "incident_agent"

    @pytest.mark.asyncio
    async def test_incident_agent_graph_compilation(self, operations_mock_llm, mock_memory_saver):
        """Test that incident agent graph compiles."""
        from agents.operations.incident_agent import IncidentAgent

        agent = IncidentAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        graph = agent.build_graph()
        assert graph is not None

        compiled = agent.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_incident_agent_execution(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test incident agent execution with mock LLM."""
        from agents.operations.incident_agent import IncidentAgent
        from contracts.agent_interface import AgentInput

        agent = IncidentAgent(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="incident",
            context=sample_operations_context
        )

        result = await agent.run(agent_input)

        assert result.success is True
        assert result.agent_name == "incident_agent"
        assert len(result.decisions) > 0


class TestOperationsCluster:
    """Tests for the Operations Cluster orchestration."""

    @pytest.mark.asyncio
    async def test_operations_cluster_creation(self, operations_mock_llm, mock_memory_saver):
        """Test creating an operations cluster."""
        from agents.operations.cluster import OperationsCluster

        cluster = OperationsCluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        assert cluster.name == "operations_cluster"
        assert len(cluster.agents) == 4

    @pytest.mark.asyncio
    async def test_operations_cluster_graph_compilation(self, operations_mock_llm, mock_memory_saver):
        """Test that operations cluster graph compiles."""
        from agents.operations.cluster import OperationsCluster

        cluster = OperationsCluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        graph = cluster.get_graph()
        assert graph is not None

        compiled = cluster.compile()
        assert compiled is not None

    @pytest.mark.asyncio
    async def test_operations_cluster_missing_inputs(
        self,
        operations_mock_llm,
        mock_memory_saver
    ):
        """Test operations cluster fails gracefully with missing inputs."""
        from agents.operations.cluster import OperationsCluster
        from contracts.agent_interface import AgentInput

        cluster = OperationsCluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        # Missing required inputs
        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="operations",
            context={"other_field": "value"}
        )

        result = await cluster.run(agent_input)

        assert result.success is False
        assert "Missing required inputs" in str(result.errors)

    @pytest.mark.asyncio
    async def test_operations_cluster_full_execution(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test full operations cluster execution."""
        from agents.operations.cluster import OperationsCluster
        from contracts.agent_interface import AgentInput

        cluster = OperationsCluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="operations",
            context=sample_operations_context
        )

        result = await cluster.run(agent_input)

        assert result.success is True
        assert result.agent_name == "operations_cluster"
        assert result.confidence > 0
        assert len(result.decisions) > 0

    @pytest.mark.asyncio
    async def test_operations_cluster_report_extraction(
        self,
        operations_mock_llm,
        mock_memory_saver,
        sample_operations_context
    ):
        """Test extracting operations report from cluster outputs."""
        from agents.operations.cluster import OperationsCluster, OperationsReport
        from contracts.agent_interface import AgentInput

        cluster = OperationsCluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver
        )

        agent_input = AgentInput(
            engagement_id="test-operations-001",
            phase="operations",
            context=sample_operations_context
        )

        result = await cluster.run(agent_input)

        if result.success and "operations_report" in result.outputs:
            report = cluster.get_report(result.outputs)
            assert report is not None
            assert isinstance(report, OperationsReport)


class TestOperationsConvenienceFunctions:
    """Tests for operations convenience functions."""

    @pytest.mark.asyncio
    async def test_create_operations_cluster(self, operations_mock_llm, mock_memory_saver):
        """Test the create_operations_cluster convenience function."""
        from agents.operations.cluster import create_operations_cluster

        cluster = create_operations_cluster(
            llm=operations_mock_llm,
            memory=mock_memory_saver,
            config={"max_iterations": 5}
        )

        assert cluster is not None
        assert cluster.name == "operations_cluster"
        assert cluster.config.get("max_iterations") == 5

    @pytest.mark.asyncio
    async def test_run_operations_function_exists(self):
        """Test the run_operations convenience function exists."""
        from agents.operations.cluster import run_operations

        assert run_operations is not None
        assert callable(run_operations)
