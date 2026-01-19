# Engagement Workflow Guide

This guide explains how to run an engagement end-to-end in Open Forge, from initial discovery through deployment.

## Table of Contents

- [Engagement Overview](#engagement-overview)
- [Phase 1: Discovery](#phase-1-discovery)
- [Phase 2: Design](#phase-2-design)
- [Phase 3: Build](#phase-3-build)
- [Phase 4: Deploy](#phase-4-deploy)
- [Quality Gates](#quality-gates)
- [Human-in-the-Loop](#human-in-the-loop)
- [Monitoring Progress](#monitoring-progress)

---

## Engagement Overview

An engagement in Open Forge follows a structured lifecycle:

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  Discovery   │───▶│    Design    │───▶│    Build     │───▶│   Deploy     │
│              │    │              │    │              │    │              │
│ - Stakeholder│    │ - Ontology   │    │ - Pipelines  │    │ - Deploy     │
│ - Requirements    │ - Schema     │    │ - Transform  │    │ - Integrate  │
│ - Sources    │    │ - Validate   │    │ - UI         │    │ - Monitor    │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
       │                   │                   │                   │
       ▼                   ▼                   ▼                   ▼
   Quality Gate        Quality Gate        Quality Gate        Quality Gate
```

### Engagement States

| State | Description |
|-------|-------------|
| `draft` | Initial state, being configured |
| `pending_approval` | Waiting for stakeholder approval |
| `approved` | Approved, ready to start |
| `in_progress` | Actively running agents |
| `paused` | Temporarily paused |
| `completed` | Successfully completed |
| `cancelled` | Cancelled by user |
| `failed` | Failed with errors |

---

## Phase 1: Discovery

The Discovery phase gathers requirements and identifies data sources.

### Agents Involved

| Agent | Responsibility |
|-------|----------------|
| **Stakeholder Agent** | Analyzes stakeholder needs and priorities |
| **Requirements Agent** | Documents functional and technical requirements |
| **Source Discovery Agent** | Identifies and catalogs data sources |

### Starting Discovery

```python
from openforge import OpenForgeClient

client = OpenForgeClient(api_key="your_key")

# Create engagement
engagement = client.engagements.create(
    name="Sales Analytics Platform",
    objective="Build a comprehensive sales analytics dashboard",
    description="""
    We need to:
    - Analyze sales trends across regions
    - Track customer behavior patterns
    - Generate weekly performance reports
    """,
    priority="high"
)

# Start stakeholder analysis
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="stakeholder_analysis",
    description="Analyze key stakeholders and their requirements",
    input_data={
        "stakeholders": [
            {"name": "Sales VP", "role": "executive_sponsor"},
            {"name": "Regional Managers", "role": "primary_users"},
            {"name": "Data Team", "role": "technical_support"}
        ],
        "initial_requirements": [
            "Real-time sales dashboard",
            "Regional comparison views",
            "Export capabilities"
        ]
    }
)
```

### Discovery Outputs

The Discovery phase produces:

1. **Stakeholder Analysis Report**
   - Key stakeholders identified
   - Priority matrix
   - Communication preferences

2. **Requirements Document**
   - Functional requirements
   - Non-functional requirements
   - Acceptance criteria

3. **Data Source Catalog**
   - Available data sources
   - Schema summaries
   - Data quality assessment

### Discovery Quality Gate

Before transitioning to Design, the following must be complete:

| Requirement | Description |
|-------------|-------------|
| Stakeholder analysis | At least one stakeholder documented |
| Requirements gathered | Core requirements documented |
| Data sources identified | At least one data source connected |
| Human approval | Stakeholder signs off on requirements |

```python
# Check phase transition readiness
readiness = client.engagements.check_transition(
    engagement_id=engagement.id,
    target_phase="design"
)

print(f"Ready: {readiness['evaluation']['ready']}")
print(f"Missing: {readiness['remaining_work']}")
```

---

## Phase 2: Design

The Design phase creates the data model and transformation logic.

### Agents Involved

| Agent | Responsibility |
|-------|----------------|
| **Ontology Designer** | Creates LinkML schema from requirements |
| **Schema Validator** | Validates schema against data sources |
| **Transformation Agent** | Designs data transformation logic |

### Ontology Design

The Ontology Designer agent creates a LinkML schema:

```python
# Start ontology design
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="ontology_design",
    description="Design sales analytics ontology",
    input_data={
        "domain": "sales_analytics",
        "requirements_doc_id": requirements_doc.id,
        "data_sources": [
            {"id": "ds_001", "type": "postgresql"},
            {"id": "ds_002", "type": "csv"}
        ]
    }
)
```

The agent produces a LinkML schema:

```yaml
id: https://example.org/sales
name: sales_ontology
prefixes:
  linkml: https://w3id.org/linkml/
  sales: https://example.org/sales/

classes:
  Customer:
    attributes:
      customer_id:
        identifier: true
        range: string
      name:
        range: string
        required: true
      region:
        range: Region
      lifetime_value:
        range: decimal

  Sale:
    attributes:
      sale_id:
        identifier: true
      customer:
        range: Customer
        required: true
      amount:
        range: decimal
      sale_date:
        range: date

  Region:
    attributes:
      region_code:
        identifier: true
      name:
        range: string
```

### Schema Validation

The Schema Validator checks the ontology against actual data:

```python
# Validate schema against data sources
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="schema_validation",
    description="Validate ontology against source data",
    input_data={
        "schema_id": ontology.id,
        "validation_rules": [
            "type_compatibility",
            "null_handling",
            "referential_integrity"
        ]
    }
)
```

### Design Quality Gate

| Requirement | Description |
|-------------|-------------|
| Ontology defined | Valid LinkML schema created |
| Schema validated | Schema passes validation against data |
| Transformations designed | Mapping from sources to ontology |
| Human approval | Schema review and approval |

---

## Phase 3: Build

The Build phase implements pipelines, transformations, and applications.

### Agents Involved

| Agent | Responsibility |
|-------|----------------|
| **Workflow Agent** | Creates Dagster pipelines |
| **Integration Agent** | Builds API integrations |
| **UI Generator** | Generates frontend components |

### Pipeline Creation

```python
# Create data pipeline
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="pipeline_creation",
    description="Build sales data ingestion pipeline",
    input_data={
        "ontology_id": ontology.id,
        "sources": source_mappings,
        "schedule": "0 * * * *",  # Hourly
        "transformations": [
            {
                "name": "normalize_regions",
                "type": "mapping",
                "source_field": "region_code",
                "target_field": "region"
            },
            {
                "name": "calculate_ltv",
                "type": "aggregation",
                "logic": "SUM(amount) OVER (PARTITION BY customer_id)"
            }
        ]
    }
)
```

### UI Generation

```python
# Generate dashboard UI
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="ui_generation",
    description="Generate sales analytics dashboard",
    input_data={
        "ontology_id": ontology.id,
        "ui_type": "dashboard",
        "components": [
            {
                "type": "kpi_card",
                "metric": "total_sales",
                "title": "Total Sales"
            },
            {
                "type": "chart",
                "chart_type": "line",
                "x_axis": "sale_date",
                "y_axis": "amount",
                "group_by": "region"
            },
            {
                "type": "data_table",
                "entity": "Sale",
                "columns": ["sale_id", "customer", "amount", "sale_date"]
            }
        ]
    }
)
```

### Build Quality Gate

| Requirement | Description |
|-------------|-------------|
| Pipelines created | Dagster jobs defined and tested |
| Transformations validated | Data quality checks pass |
| UI components built | React components generated |
| Integration tests pass | End-to-end data flow verified |

---

## Phase 4: Deploy

The Deploy phase packages and deploys the solution.

### Agents Involved

| Agent | Responsibility |
|-------|----------------|
| **Deployment Agent** | Packages and deploys application |
| **Integration Agent** | Configures production integrations |

### Deployment Configuration

```python
# Configure deployment
task = client.agents.create_task(
    engagement_id=engagement.id,
    task_type="deployment_config",
    description="Deploy sales analytics to production",
    input_data={
        "environment": "production",
        "deployment_type": "kubernetes",
        "resources": {
            "cpu": "2",
            "memory": "4Gi",
            "replicas": 3
        },
        "scaling": {
            "min_replicas": 2,
            "max_replicas": 10,
            "target_cpu_utilization": 70
        }
    }
)
```

### Deploy Quality Gate

| Requirement | Description |
|-------------|-------------|
| Deployment config | Valid Kubernetes/Docker config |
| Security review | Credentials and access reviewed |
| Performance test | Load testing completed |
| Human approval | Final deployment approval |

---

## Quality Gates

Quality gates ensure each phase is complete before proceeding.

### Checking Gate Status

```python
# Get phase status
status = client.engagements.get_phase_status(engagement.id)

print(f"Current Phase: {status['phase']}")
print(f"Outputs Completed: {status['outputs_completed']}")
print(f"Gates Passed: {status['gates_passed']}")
print(f"Approvals Received: {status['approvals_received']}")
```

### Passing a Quality Gate

Quality gates can be passed programmatically or through agent validation:

```python
# Pass a quality gate
client.engagements.pass_quality_gate(
    engagement_id=engagement.id,
    gate_id="ontology_validated",
    validator="schema_validator_agent",
    evidence={
        "validation_report_id": report.id,
        "passed_checks": 15,
        "failed_checks": 0
    }
)
```

### Forcing Phase Transition

In exceptional cases, you can force a phase transition:

```python
# Force transition (requires admin)
result = client.engagements.transition_phase(
    engagement_id=engagement.id,
    target_phase="build",
    approved_by="admin_user",
    force=True  # Skip incomplete requirements
)
```

---

## Human-in-the-Loop

Open Forge integrates human oversight at key decision points.

### Approval Types

| Type | Trigger | Required Action |
|------|---------|-----------------|
| `phase_transition` | Phase boundary | Review and approve transition |
| `schema_change` | Ontology modification | Review schema changes |
| `deployment` | Production deployment | Final deployment approval |
| `tool_execution` | Sensitive operation | Approve agent tool use |

### Handling Approvals

```python
# List pending approvals
approvals = client.approvals.list(engagement_id=engagement.id)

for approval in approvals:
    print(f"Type: {approval['type']}")
    print(f"Title: {approval['title']}")
    print(f"Description: {approval['description']}")

    # Review items
    for item in approval['items_to_review']:
        print(f"  - {item['name']}: {item['summary']}")

    # Make decision
    if user_approves():
        client.approvals.approve(
            approval_id=approval['id'],
            comment="Approved after review"
        )
    else:
        client.approvals.reject(
            approval_id=approval['id'],
            comment="Needs revision: see notes"
        )
```

### Configuring Approval Requirements

```python
# Create engagement with custom approval settings
engagement = client.engagements.create(
    name="High Security Project",
    objective="...",
    agent_config={
        "approval_settings": {
            "phase_transitions": True,
            "schema_changes": True,
            "data_access": True,
            "deployments": True,
            "tool_executions": ["execute_sql", "write_file"]
        }
    }
)
```

---

## Monitoring Progress

### Real-Time Task Streaming

```python
# Stream task events
for event in client.agents.stream_task(task.id):
    if event['type'] == 'progress':
        print(f"Progress: {event['step']} - {event['message']}")
    elif event['type'] == 'tool_call':
        print(f"Tool: {event['tool']} - {event['status']}")
    elif event['type'] == 'completed':
        print(f"Completed: {event['result']}")
```

### Engagement Dashboard

```python
# Get engagement summary
summary = client.engagements.get_summary(engagement.id)

print(f"""
Engagement: {summary['name']}
Phase: {summary['current_phase']}
Progress: {summary['progress_percent']}%

Tasks:
  - Completed: {summary['tasks']['completed']}
  - Running: {summary['tasks']['running']}
  - Pending: {summary['tasks']['pending']}
  - Failed: {summary['tasks']['failed']}

Quality Gates:
  - Passed: {summary['quality_gates']['passed']}
  - Remaining: {summary['quality_gates']['remaining']}
""")
```

### Viewing Agent Logs

```python
# Get task conversation history
messages = client.agents.get_task_messages(task.id)

for msg in messages:
    print(f"[{msg['role']}] {msg['content'][:200]}...")

    if msg.get('tool_calls'):
        for call in msg['tool_calls']:
            print(f"  Tool: {call['name']}")
            print(f"  Args: {call['arguments']}")
```

---

## Best Practices

### 1. Start with Clear Objectives

Define measurable, specific objectives:

```python
# Good
objective = "Build a dashboard showing weekly sales by region with 24-hour data freshness"

# Bad
objective = "Make a sales dashboard"
```

### 2. Connect Data Sources Early

Validate data access before starting discovery:

```python
# Connect and test sources first
for source_config in data_sources:
    source = client.data_sources.create(**source_config)
    result = client.data_sources.test(source.id)

    if not result['success']:
        print(f"Warning: {source.name} connection failed")
```

### 3. Review Agent Outputs

Don't auto-approve everything:

```python
# Configure approval thresholds
engagement = client.engagements.create(
    name="...",
    agent_config={
        "auto_approve_threshold": 0.95,  # Only auto-approve high confidence
        "always_require_approval": [
            "schema_change",
            "deployment"
        ]
    }
)
```

### 4. Use Incremental Development

Break large engagements into iterations:

```python
# Phase 1: Core data model
# Phase 2: Basic dashboard
# Phase 3: Advanced analytics
# Phase 4: Production deployment
```

---

## Related Documentation

- [Getting Started](./getting-started.md)
- [Ontology Design](./ontology-design.md)
- [Pipeline Creation](./pipeline-creation.md)
- [Troubleshooting](../runbooks/troubleshooting.md)
