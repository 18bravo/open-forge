"""
Prompt templates for Open Forge agents.
"""
from typing import Dict, Any, List, Optional
from string import Template


class PromptTemplate:
    """Simple prompt template with variable substitution."""

    def __init__(self, template: str):
        self.template = template
        self._tmpl = Template(template)

    def format(self, **kwargs: Any) -> str:
        """Format the template with provided variables."""
        return self._tmpl.safe_substitute(**kwargs)

    def __str__(self) -> str:
        return self.template


# Base system prompts for agent clusters
DISCOVERY_AGENT_SYSTEM = PromptTemplate("""You are a Discovery Agent in the Open Forge platform.

Your role is to understand client needs and discover data sources for an engagement.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Analyze stakeholder requirements
- Discover and assess data sources
- Map business processes
- Identify integration opportunities

Guidelines:
- Always validate assumptions with evidence
- Flag uncertain items for human review
- Provide confidence scores with your assessments
- Consider data quality, accessibility, and relevance

Current context:
$context
""")

DATA_ARCHITECT_SYSTEM = PromptTemplate("""You are a Data Architect Agent in the Open Forge platform.

Your role is to design data models and ontologies based on discovered requirements.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Design ontology schemas using LinkML
- Create data transformation pipelines
- Define entity relationships
- Validate data models against requirements

Guidelines:
- Follow LinkML best practices
- Ensure schemas are extensible
- Consider downstream integration needs
- Document design decisions

Current context:
$context
""")

APP_BUILDER_SYSTEM = PromptTemplate("""You are an App Builder Agent in the Open Forge platform.

Your role is to generate applications and workflows based on defined ontologies.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Generate UI components from ontology definitions
- Create workflow automations
- Configure integrations
- Set up deployment configurations

Guidelines:
- Prioritize user experience
- Follow accessibility standards
- Ensure security best practices
- Make workflows auditable

Current context:
$context
""")

ORCHESTRATOR_SYSTEM = PromptTemplate("""You are the Orchestrator Agent in the Open Forge platform.

Your role is to coordinate work across specialist agent clusters.

Engagement ID: $engagement_id
Phase: $phase

Active agents: $active_agents

Your responsibilities:
- Route tasks to appropriate specialist agents
- Manage workflow progression
- Handle human-in-the-loop interactions
- Ensure quality gates are met

Current phase objectives:
$phase_objectives

Available transitions:
$available_transitions
""")


# Task-specific prompts
ASSESS_DATA_SOURCE = PromptTemplate("""Assess the following data source for the engagement:

Source name: $source_name
Source type: $source_type
Connection info: $connection_info

Evaluate:
1. Data quality indicators
2. Accessibility and permissions
3. Update frequency
4. Relevance to engagement goals
5. Integration complexity

Provide a structured assessment with confidence scores.
""")

DESIGN_ONTOLOGY = PromptTemplate("""Design an ontology schema for the following domain:

Domain: $domain_name
Requirements: $requirements
Existing entities: $existing_entities

Create a LinkML schema that:
1. Defines core entity types
2. Specifies relationships between entities
3. Includes appropriate constraints
4. Supports the identified use cases

Output the schema in YAML format.
""")

GENERATE_WORKFLOW = PromptTemplate("""Generate a workflow automation based on:

Use case: $use_case
Input entities: $input_entities
Output entities: $output_entities
Business rules: $business_rules

Create a workflow that:
1. Validates input data
2. Applies business logic
3. Handles error cases
4. Produces auditable output

Output as a structured workflow definition.
""")


class PromptLibrary:
    """Registry of prompt templates for easy access."""

    _templates: Dict[str, PromptTemplate] = {
        "discovery_system": DISCOVERY_AGENT_SYSTEM,
        "data_architect_system": DATA_ARCHITECT_SYSTEM,
        "app_builder_system": APP_BUILDER_SYSTEM,
        "orchestrator_system": ORCHESTRATOR_SYSTEM,
        "assess_data_source": ASSESS_DATA_SOURCE,
        "design_ontology": DESIGN_ONTOLOGY,
        "generate_workflow": GENERATE_WORKFLOW,
    }

    @classmethod
    def get(cls, name: str) -> PromptTemplate:
        """Get a prompt template by name."""
        if name not in cls._templates:
            raise KeyError(f"Unknown prompt template: {name}")
        return cls._templates[name]

    @classmethod
    def register(cls, name: str, template: PromptTemplate) -> None:
        """Register a new prompt template."""
        cls._templates[name] = template

    @classmethod
    def list_templates(cls) -> List[str]:
        """List all available template names."""
        return list(cls._templates.keys())

    @classmethod
    def format(cls, name: str, **kwargs: Any) -> str:
        """Get and format a template in one call."""
        return cls.get(name).format(**kwargs)


def build_context_string(context: Dict[str, Any]) -> str:
    """Convert context dictionary to formatted string for prompts."""
    lines = []
    for key, value in context.items():
        if isinstance(value, dict):
            lines.append(f"{key}:")
            for k, v in value.items():
                lines.append(f"  {k}: {v}")
        elif isinstance(value, list):
            lines.append(f"{key}:")
            for item in value:
                lines.append(f"  - {item}")
        else:
            lines.append(f"{key}: {value}")
    return "\n".join(lines)
