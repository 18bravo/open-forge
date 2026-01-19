# Agent Canvas Guide

This guide covers using Langflow for creating and customizing AI agent workflows in Open Forge.

## Table of Contents

- [Introduction](#introduction)
- [Langflow Overview](#langflow-overview)
- [Creating Agent Workflows](#creating-agent-workflows)
- [Open Forge Components](#open-forge-components)
- [Workflow Patterns](#workflow-patterns)
- [Integration with Engagements](#integration-with-engagements)
- [Best Practices](#best-practices)

---

## Introduction

The **Agent Canvas** is Open Forge's visual interface for designing AI agent workflows, powered by [Langflow](https://www.langflow.org/). It allows you to:

- Visually design agent workflows
- Chain multiple agents together
- Add custom tools and integrations
- Test workflows interactively
- Export workflows for production use

```
┌─────────────────────────────────────────────────────────────┐
│                     Agent Canvas                            │
│  ┌─────────┐     ┌─────────┐     ┌─────────┐               │
│  │  Input  │────▶│  Agent  │────▶│  Tool   │               │
│  └─────────┘     └─────────┘     └─────────┘               │
│                       │                                     │
│                       ▼                                     │
│                  ┌─────────┐     ┌─────────┐               │
│                  │  Agent  │────▶│ Output  │               │
│                  └─────────┘     └─────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Langflow Overview

### Accessing the Canvas

The Agent Canvas is available at:

```
http://localhost:7860
```

Or through the Open Forge UI under **Tools > Agent Canvas**.

### Interface Components

| Component | Description |
|-----------|-------------|
| **Node Panel** | Drag-and-drop components |
| **Canvas** | Visual workflow editor |
| **Chat Panel** | Interactive testing |
| **Settings** | Workflow configuration |
| **API** | Export endpoints |

### Node Types

| Category | Examples |
|----------|----------|
| **Inputs** | Chat Input, Text Input, File Upload |
| **Agents** | LLM, OpenAI Agent, Custom Agent |
| **Tools** | Code Executor, SQL, API Call |
| **Memory** | Conversation Buffer, Vector Store |
| **Outputs** | Chat Output, File Output |
| **Utilities** | Prompts, Parsers, Splitters |

---

## Creating Agent Workflows

### Basic Workflow: Question Answering

Create a simple Q&A agent:

1. **Add Chat Input**
   - Drag "Chat Input" to canvas
   - This receives user questions

2. **Add LLM Node**
   - Drag "Anthropic" node
   - Configure with API key
   - Set model: `claude-sonnet-4-20250514`

3. **Add System Prompt**
   - Drag "Prompt" node
   - Connect to LLM
   - Add system instructions:
     ```
     You are a helpful assistant for Open Forge.
     Answer questions about data engineering and analytics.
     ```

4. **Add Chat Output**
   - Drag "Chat Output" node
   - Connect LLM output to it

5. **Connect Nodes**
   ```
   Chat Input ──▶ Prompt ──▶ LLM ──▶ Chat Output
   ```

### Adding Tools

Enhance the agent with tools:

1. **SQL Query Tool**
   ```
   ┌────────────┐
   │ SQL Query  │
   │            │
   │ Connection:│
   │ postgresql │
   └────────────┘
   ```

2. **Connect to Agent**
   ```
   Chat Input ──▶ Agent ──┬──▶ Chat Output
                          │
                          └──▶ SQL Tool
   ```

### Multi-Agent Workflow

Chain multiple specialized agents:

```
                    ┌──────────────┐
                    │   Router     │
                    │    Agent     │
                    └──────┬───────┘
                           │
           ┌───────────────┼───────────────┐
           ▼               ▼               ▼
    ┌────────────┐  ┌────────────┐  ┌────────────┐
    │  Research  │  │   Code     │  │   Data     │
    │   Agent    │  │   Agent    │  │   Agent    │
    └────────────┘  └────────────┘  └────────────┘
           │               │               │
           └───────────────┼───────────────┘
                           ▼
                    ┌──────────────┐
                    │   Output     │
                    │   Merger     │
                    └──────────────┘
```

---

## Open Forge Components

Open Forge provides custom Langflow components for integration.

### Engagement Context

Access engagement data in workflows:

```python
# packages/langflow-components/engagement_context.py

from langflow import CustomComponent
from langflow.field_typing import Data

class EngagementContext(CustomComponent):
    display_name = "Engagement Context"
    description = "Load context from an Open Forge engagement"

    def build_config(self):
        return {
            "engagement_id": {
                "display_name": "Engagement ID",
                "required": True,
            }
        }

    def build(self, engagement_id: str) -> Data:
        from openforge import OpenForgeClient

        client = OpenForgeClient()
        engagement = client.engagements.get(engagement_id)

        return Data(
            value={
                "id": engagement.id,
                "name": engagement.name,
                "objective": engagement.objective,
                "phase": engagement.current_phase,
                "data_sources": [ds.id for ds in engagement.data_sources]
            }
        )
```

### Ontology Loader

Load ontology schemas:

```python
# packages/langflow-components/ontology_loader.py

class OntologyLoader(CustomComponent):
    display_name = "Ontology Loader"
    description = "Load an ontology schema"

    def build_config(self):
        return {
            "ontology_id": {
                "display_name": "Ontology ID",
                "required": True,
            },
            "format": {
                "display_name": "Output Format",
                "options": ["yaml", "json", "summary"],
                "default": "summary"
            }
        }

    def build(self, ontology_id: str, format: str) -> str:
        from openforge import OpenForgeClient

        client = OpenForgeClient()
        ontology = client.ontologies.get(ontology_id)

        if format == "yaml":
            return ontology.to_yaml()
        elif format == "json":
            return ontology.to_json()
        else:
            return ontology.get_summary()
```

### Data Source Query

Query connected data sources:

```python
# packages/langflow-components/data_source_query.py

class DataSourceQuery(CustomComponent):
    display_name = "Data Source Query"
    description = "Execute a query against a data source"

    def build_config(self):
        return {
            "source_id": {
                "display_name": "Data Source ID",
                "required": True,
            },
            "query": {
                "display_name": "Query",
                "multiline": True,
                "required": True,
            },
            "limit": {
                "display_name": "Row Limit",
                "default": 100,
            }
        }

    def build(self, source_id: str, query: str, limit: int) -> Data:
        from openforge import OpenForgeClient
        import polars as pl

        client = OpenForgeClient()
        result = client.data_sources.query(
            source_id,
            query,
            limit=limit
        )

        return Data(
            value=result.to_dicts(),
            metadata={
                "row_count": len(result),
                "columns": result.columns
            }
        )
```

### Pipeline Trigger

Trigger Dagster pipelines:

```python
# packages/langflow-components/pipeline_trigger.py

class PipelineTrigger(CustomComponent):
    display_name = "Pipeline Trigger"
    description = "Trigger a Dagster pipeline job"

    def build_config(self):
        return {
            "job_name": {
                "display_name": "Job Name",
                "required": True,
            },
            "run_config": {
                "display_name": "Run Configuration",
                "multiline": True,
                "default": "{}",
            },
            "wait_for_completion": {
                "display_name": "Wait for Completion",
                "default": False,
            }
        }

    def build(
        self,
        job_name: str,
        run_config: str,
        wait_for_completion: bool
    ) -> Data:
        import json
        from openforge import OpenForgeClient

        client = OpenForgeClient()
        config = json.loads(run_config) if run_config else {}

        run = client.pipelines.trigger(
            job_name,
            run_config=config
        )

        if wait_for_completion:
            run = client.pipelines.wait_for_run(run.id)

        return Data(
            value={
                "run_id": run.id,
                "status": run.status,
                "started_at": run.started_at.isoformat()
            }
        )
```

### Approval Request

Create human-in-the-loop approval points:

```python
# packages/langflow-components/approval_request.py

class ApprovalRequest(CustomComponent):
    display_name = "Approval Request"
    description = "Request human approval before proceeding"

    def build_config(self):
        return {
            "title": {
                "display_name": "Title",
                "required": True,
            },
            "description": {
                "display_name": "Description",
                "multiline": True,
            },
            "items_to_review": {
                "display_name": "Items to Review",
                "multiline": True,
            },
            "timeout_minutes": {
                "display_name": "Timeout (minutes)",
                "default": 60,
            }
        }

    def build(
        self,
        title: str,
        description: str,
        items_to_review: str,
        timeout_minutes: int
    ) -> Data:
        from openforge import OpenForgeClient
        import json

        client = OpenForgeClient()
        items = json.loads(items_to_review) if items_to_review else []

        approval = client.approvals.create(
            title=title,
            description=description,
            items_to_review=items,
            timeout_minutes=timeout_minutes
        )

        # Wait for decision
        result = client.approvals.wait_for_decision(approval.id)

        return Data(
            value={
                "approved": result.status == "approved",
                "decision_by": result.decided_by,
                "comment": result.comment
            }
        )
```

---

## Workflow Patterns

### Pattern 1: Research and Summarize

```
┌─────────────┐
│    Input    │
│   (Topic)   │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│   Search    │────▶│   Filter    │
│    Agent    │     │  Relevant   │
└─────────────┘     └──────┬──────┘
                           │
       ┌───────────────────┴───────────────────┐
       ▼                                       ▼
┌─────────────┐                         ┌─────────────┐
│   Source    │                         │   Source    │
│   Reader 1  │                         │   Reader N  │
└──────┬──────┘                         └──────┬──────┘
       │                                       │
       └───────────────────┬───────────────────┘
                           ▼
                    ┌─────────────┐
                    │  Summarize  │
                    │    Agent    │
                    └──────┬──────┘
                           │
                           ▼
                    ┌─────────────┐
                    │   Output    │
                    │  (Summary)  │
                    └─────────────┘
```

### Pattern 2: Code Generation with Review

```
┌─────────────┐
│Requirements │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│    Code     │
│  Generator  │
└──────┬──────┘
       │
       ▼
┌─────────────┐     ┌─────────────┐
│    Code     │────▶│   Tests     │
│   Reviewer  │     │  Generator  │
└──────┬──────┘     └──────┬──────┘
       │                    │
       │         ┌──────────┘
       ▼         ▼
┌─────────────────────┐
│   Human Approval    │
│   (if needed)       │
└──────────┬──────────┘
           │
           ▼
    ┌─────────────┐
    │   Output    │
    │    Code     │
    └─────────────┘
```

### Pattern 3: Data Analysis Pipeline

```
┌─────────────┐
│   Question  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Query     │
│  Planner    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  Data Source│
│   Query     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Data      │
│  Analyzer   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Visualization│
│  Generator   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Report    │
│  Generator  │
└─────────────┘
```

### Pattern 4: Iterative Refinement

```
┌─────────────┐
│   Initial   │
│   Request   │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   Draft     │
│  Generator  │◀──────────────┐
└──────┬──────┘               │
       │                      │
       ▼                      │
┌─────────────┐               │
│   Quality   │               │
│   Checker   │               │
└──────┬──────┘               │
       │                      │
       ▼                      │
   ┌───────┐                  │
   │ Pass? │──No──▶ ┌─────────┴─────────┐
   └───┬───┘        │    Feedback       │
       │            │    Generator      │
      Yes           └───────────────────┘
       │
       ▼
┌─────────────┐
│   Final     │
│   Output    │
└─────────────┘
```

---

## Integration with Engagements

### Workflow as Agent Task

Export workflows for use in engagements:

1. **Export from Langflow**
   - Click "API" in the canvas
   - Copy the flow ID or export JSON

2. **Register as Agent**
   ```python
   from openforge import OpenForgeClient

   client = OpenForgeClient()

   # Register custom workflow
   agent = client.agents.register_workflow(
       name="custom_research_agent",
       description="Research and summarize topics",
       langflow_flow_id="flow_abc123",
       input_schema={
           "topic": {"type": "string", "required": True},
           "depth": {"type": "string", "enum": ["brief", "detailed"]}
       },
       output_schema={
           "summary": {"type": "string"},
           "sources": {"type": "array"}
       }
   )
   ```

3. **Use in Engagement**
   ```python
   task = client.agents.create_task(
       engagement_id=engagement.id,
       task_type="custom_research_agent",
       description="Research competitor analytics tools",
       input_data={
           "topic": "business intelligence platforms",
           "depth": "detailed"
       }
   )
   ```

### Embedding Context

Pass engagement context to workflows:

```python
# In Langflow component
class EngagementAwareAgent(CustomComponent):
    def build(self, engagement_id: str, user_input: str) -> str:
        from openforge import OpenForgeClient

        client = OpenForgeClient()
        engagement = client.engagements.get(engagement_id)

        # Build context
        context = f"""
        Engagement: {engagement.name}
        Objective: {engagement.objective}
        Current Phase: {engagement.current_phase}
        Data Sources: {', '.join(ds.name for ds in engagement.data_sources)}
        """

        # Use context in LLM call
        response = self.llm.invoke(
            system=f"Context:\n{context}",
            user=user_input
        )

        return response
```

---

## Best Practices

### 1. Start Simple

Begin with basic workflows and add complexity gradually:

```
# Good: Start with
Input ──▶ Agent ──▶ Output

# Then expand to
Input ──▶ Agent ──▶ Tool ──▶ Agent ──▶ Output
```

### 2. Use Clear Naming

Name nodes descriptively:

```
# Good
"Customer Query Parser"
"Sales Data Analyzer"
"Report Formatter"

# Bad
"Node 1"
"Agent"
"Output"
```

### 3. Add Error Handling

Include fallback paths:

```
                 ┌─────────────┐
                 │    Main     │
                 │   Process   │
                 └──────┬──────┘
                        │
                        ▼
                   ┌────────┐
                   │ Error? │
                   └────┬───┘
                        │
           ┌────────────┼────────────┐
          No            │           Yes
           │            │            │
           ▼            │            ▼
    ┌─────────────┐     │     ┌─────────────┐
    │   Output    │     │     │   Fallback  │
    └─────────────┘     │     │   Handler   │
                        │     └──────┬──────┘
                        │            │
                        └────────────┘
```

### 4. Test Iteratively

Use the chat panel to test each addition:

1. Add one component
2. Test with sample input
3. Verify output
4. Add next component
5. Repeat

### 5. Document Workflows

Add descriptions to components:

```python
class MyComponent(CustomComponent):
    display_name = "My Component"
    description = """
    This component does X.

    Inputs:
    - input_a: Description of input A
    - input_b: Description of input B

    Outputs:
    - Processed result with schema {...}

    Example:
    Input: "..."
    Output: "..."
    """
```

### 6. Version Your Workflows

Export and version control workflows:

```bash
# Export workflow
langflow export --flow-id abc123 --output workflows/research_v1.json

# Track in git
git add workflows/research_v1.json
git commit -m "Add research workflow v1"
```

---

## Related Documentation

- [Getting Started](./getting-started.md)
- [Engagement Workflow](./engagement-workflow.md)
- [Pipeline Creation](./pipeline-creation.md)
- [Architecture Overview](../development/architecture.md)
