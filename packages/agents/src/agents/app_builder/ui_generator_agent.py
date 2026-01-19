"""
UI Generator Agent

Generates UI components from ontology definitions.
Creates forms, tables, dashboards as React/TypeScript component specs.
"""
from typing import Any, Dict, List, Optional, Type, TypedDict
from datetime import datetime
import re
import json

from jinja2 import Template
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    AppBuilderState,
    Decision,
    Message,
    add_decision,
    mark_for_review
)

from agents.app_builder.templates.component_templates import (
    FORM_TEMPLATE,
    TABLE_TEMPLATE,
    DASHBOARD_TEMPLATE,
    TYPES_TEMPLATE,
    HOOKS_TEMPLATE,
    API_CLIENT_TEMPLATE,
    ZOD_SCHEMA_TEMPLATE,
)


# =============================================================================
# Type Definitions for Component Specs
# =============================================================================

class ComponentFile(TypedDict):
    """Represents a generated component file."""
    entity: str
    code: str
    filename: str


class ComponentSpecs(TypedDict):
    """Complete output specification for all generated components."""
    forms: List[ComponentFile]
    tables: List[ComponentFile]
    dashboards: List[ComponentFile]
    types: List[ComponentFile]
    hooks: List[ComponentFile]
    api_clients: List[ComponentFile]
    zod_schemas: List[ComponentFile]


class EntityProperty(TypedDict, total=False):
    """Property definition from ontology."""
    name: str
    type: str
    ts_type: str
    zod_type: str
    required: bool
    description: str
    validation: Optional[str]
    default_value: Optional[Any]
    enum_values: Optional[List[str]]
    min: Optional[int]
    max: Optional[int]
    pattern: Optional[str]


class EntityDefinition(TypedDict):
    """Entity definition from ontology."""
    name: str
    display_name: str
    description: str
    properties: List[EntityProperty]
    primary_key: str
    display_field: str
    secondary_display_field: Optional[str]
    status_field: Optional[str]
    date_field: str
    relationships: List[Dict[str, Any]]


# =============================================================================
# Utility Functions
# =============================================================================

def to_kebab_case(name: str) -> str:
    """Convert PascalCase or camelCase to kebab-case."""
    s1 = re.sub('(.)([A-Z][a-z]+)', r'\1-\2', name)
    return re.sub('([a-z0-9])([A-Z])', r'\1-\2', s1).lower()


def to_camel_case(name: str) -> str:
    """Convert PascalCase to camelCase."""
    return name[0].lower() + name[1:] if name else name


def pluralize(name: str) -> str:
    """Simple pluralization for entity names."""
    if name.endswith('y'):
        return name[:-1] + 'ies'
    elif name.endswith('s') or name.endswith('x') or name.endswith('ch') or name.endswith('sh'):
        return name + 'es'
    else:
        return name + 's'


def get_ts_type(ontology_type: str) -> str:
    """Map ontology type to TypeScript type."""
    type_map = {
        'string': 'string',
        'text': 'string',
        'integer': 'number',
        'float': 'number',
        'decimal': 'number',
        'number': 'number',
        'boolean': 'boolean',
        'date': 'string',
        'datetime': 'string',
        'timestamp': 'string',
        'uuid': 'string',
        'json': 'Record<string, unknown>',
        'object': 'Record<string, unknown>',
        'array': 'unknown[]',
        'enum': 'string',  # Will be replaced with actual enum type
    }
    return type_map.get(ontology_type.lower(), 'unknown')


def get_zod_type(ontology_type: str) -> str:
    """Map ontology type to Zod validation type."""
    type_map = {
        'string': 'z.string()',
        'text': 'z.string()',
        'integer': 'z.number().int()',
        'float': 'z.number()',
        'decimal': 'z.number()',
        'number': 'z.number()',
        'boolean': 'z.boolean()',
        'date': 'z.string().datetime()',
        'datetime': 'z.string().datetime()',
        'timestamp': 'z.string().datetime()',
        'uuid': 'z.string().uuid()',
        'json': 'z.record(z.unknown())',
        'object': 'z.record(z.unknown())',
        'array': 'z.array(z.unknown())',
        'enum': 'z.string()',  # Will be replaced with actual enum schema
    }
    return type_map.get(ontology_type.lower(), 'z.unknown()')


def get_form_field_type(ontology_type: str) -> str:
    """Map ontology type to form field type."""
    type_map = {
        'string': 'text',
        'text': 'textarea',
        'integer': 'number',
        'float': 'number',
        'decimal': 'number',
        'number': 'number',
        'boolean': 'switch',
        'date': 'date',
        'datetime': 'date',
        'timestamp': 'date',
        'uuid': 'text',
        'email': 'email',
        'url': 'text',
        'phone': 'text',
        'enum': 'select',
    }
    return type_map.get(ontology_type.lower(), 'text')


def get_table_cell_type(ontology_type: str) -> str:
    """Map ontology type to table cell renderer type."""
    type_map = {
        'string': 'text',
        'text': 'text',
        'integer': 'number',
        'float': 'number',
        'decimal': 'currency',
        'number': 'number',
        'boolean': 'badge',
        'date': 'date',
        'datetime': 'datetime',
        'timestamp': 'datetime',
        'enum': 'badge',
        'status': 'badge',
    }
    return type_map.get(ontology_type.lower(), 'text')


# =============================================================================
# System Prompt
# =============================================================================

UI_GENERATOR_SYSTEM_PROMPT = """You are an expert UI Generator Agent for Open Forge, an enterprise data platform.

Your role is to generate React/TypeScript UI component specifications from ontology definitions.

## Your Capabilities:
1. Generate form components from entity definitions
2. Create table/grid components for data display
3. Design dashboard layouts with widgets
4. Produce React/TypeScript component specifications
5. Create type-safe component interfaces

## Component Generation Principles:
1. Follow React best practices and modern patterns
2. Use TypeScript for type safety
3. Generate accessible components (WCAG 2.1 AA)
4. Design for responsiveness (mobile-first)
5. Support theming and customization
6. Include proper validation for forms
7. Optimize for performance (lazy loading, virtualization)

## Output Format:
Generate component specifications as structured JSON with:
- Component name and type
- Props interface definition
- State requirements
- Event handlers
- Styling guidelines
- Accessibility attributes
- Usage examples

## Component Types:
- Forms: Input fields, validation, submission handling
- Tables: Sorting, filtering, pagination, row actions
- Dashboards: Widget layout, data binding, refresh logic
- Detail Views: Entity display, related data, actions
- Lists: Virtualized lists, search, bulk actions

## Design System Integration:
- Use consistent spacing and typography
- Follow color palette guidelines
- Support dark/light themes
- Include loading and error states
"""


# =============================================================================
# UI Generator Agent
# =============================================================================

class UIGeneratorAgent(BaseOpenForgeAgent):
    """
    Agent that generates UI components from ontology definitions.

    This agent analyzes ontology schemas and requirements to generate
    React/TypeScript component specifications for forms, tables,
    dashboards, and other UI elements.
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)

        # Initialize Jinja2 templates
        self._form_template = Template(FORM_TEMPLATE)
        self._table_template = Template(TABLE_TEMPLATE)
        self._dashboard_template = Template(DASHBOARD_TEMPLATE)
        self._types_template = Template(TYPES_TEMPLATE)
        self._hooks_template = Template(HOOKS_TEMPLATE)
        self._api_template = Template(API_CLIENT_TEMPLATE)
        self._zod_template = Template(ZOD_SCHEMA_TEMPLATE)

    @property
    def name(self) -> str:
        return "ui_generator"

    @property
    def description(self) -> str:
        return "Generates React/TypeScript UI component specifications from ontology definitions, creating forms, tables, and dashboards."

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema", "ui_requirements"]

    @property
    def output_keys(self) -> List[str]:
        return ["component_specs", "form_definitions", "table_definitions", "dashboard_layouts", "type_definitions"]

    @property
    def state_class(self) -> Type[AppBuilderState]:
        return AppBuilderState

    def get_system_prompt(self) -> str:
        return UI_GENERATOR_SYSTEM_PROMPT

    def get_tools(self) -> List[Any]:
        """Return tools for UI generation."""
        return []  # LLM-only agent for now

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for UI generation."""
        graph = StateGraph(AppBuilderState)

        # Add nodes
        graph.add_node("analyze_ontology", self._analyze_ontology)
        graph.add_node("generate_types", self._generate_types)
        graph.add_node("generate_forms", self._generate_forms)
        graph.add_node("generate_tables", self._generate_tables)
        graph.add_node("generate_dashboards", self._generate_dashboards)
        graph.add_node("generate_hooks", self._generate_hooks)
        graph.add_node("compile_specs", self._compile_specs)
        graph.add_node("validate_components", self._validate_components)

        # Define edges
        graph.set_entry_point("analyze_ontology")
        graph.add_edge("analyze_ontology", "generate_types")
        graph.add_edge("generate_types", "generate_forms")
        graph.add_edge("generate_forms", "generate_tables")
        graph.add_edge("generate_tables", "generate_dashboards")
        graph.add_edge("generate_dashboards", "generate_hooks")
        graph.add_edge("generate_hooks", "compile_specs")
        graph.add_edge("compile_specs", "validate_components")
        graph.add_conditional_edges(
            "validate_components",
            self._should_refine,
            {
                "refine": "generate_forms",
                "complete": END
            }
        )

        return graph

    def _parse_ontology_schema(self, ontology_schema: Dict[str, Any]) -> List[EntityDefinition]:
        """Parse ontology schema into entity definitions."""
        entities: List[EntityDefinition] = []

        # Handle different ontology schema formats
        entity_list = ontology_schema.get('entities', [])
        if not entity_list and 'types' in ontology_schema:
            entity_list = ontology_schema.get('types', [])

        for entity_data in entity_list:
            properties: List[EntityProperty] = []

            for prop_data in entity_data.get('properties', []):
                prop_type = prop_data.get('type', 'string')
                prop: EntityProperty = {
                    'name': prop_data.get('name', ''),
                    'type': prop_type,
                    'ts_type': get_ts_type(prop_type),
                    'zod_type': get_zod_type(prop_type),
                    'required': prop_data.get('required', False),
                    'description': prop_data.get('description', ''),
                }

                # Add validation rules
                if 'min' in prop_data:
                    prop['min'] = prop_data['min']
                if 'max' in prop_data:
                    prop['max'] = prop_data['max']
                if 'pattern' in prop_data:
                    prop['pattern'] = prop_data['pattern']
                if 'enum' in prop_data or 'values' in prop_data:
                    prop['enum_values'] = prop_data.get('enum', prop_data.get('values', []))
                if 'default' in prop_data:
                    prop['default_value'] = prop_data['default']

                properties.append(prop)

            entity_name = entity_data.get('name', '')
            entity: EntityDefinition = {
                'name': entity_name,
                'display_name': entity_data.get('display_name', entity_name),
                'description': entity_data.get('description', f'{entity_name} entity'),
                'properties': properties,
                'primary_key': entity_data.get('primary_key', 'id'),
                'display_field': entity_data.get('display_field', 'name'),
                'secondary_display_field': entity_data.get('secondary_display_field'),
                'status_field': entity_data.get('status_field'),
                'date_field': entity_data.get('date_field', 'created_at'),
                'relationships': entity_data.get('relationships', []),
            }

            entities.append(entity)

        return entities

    def _generate_entity_types(self, entity: EntityDefinition) -> str:
        """Generate TypeScript type definitions for an entity."""
        context = {
            'entity_name': entity['name'],
            'description': entity['description'],
            'properties': entity['properties'],
            'summary_properties': [p for p in entity['properties']
                                   if p['name'] in ['id', entity['display_field'],
                                                   entity.get('status_field', ''),
                                                   entity['date_field']]
                                   or p.get('required', False)],
            'create_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'update_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'enums': [{'name': f"{entity['name']}{p['name'].title()}",
                      'description': p.get('description', ''),
                      'values': p.get('enum_values', [])}
                     for p in entity['properties'] if p.get('enum_values')],
        }

        return self._types_template.render(**context)

    def _generate_entity_zod_schema(self, entity: EntityDefinition) -> str:
        """Generate Zod validation schema for an entity."""
        context = {
            'entity_name': entity['name'],
            'create_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'update_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'enums': [{'name': f"{entity['name']}{p['name'].title()}",
                      'values': p.get('enum_values', [])}
                     for p in entity['properties'] if p.get('enum_values')],
        }

        return self._zod_template.render(**context)

    def _generate_entity_form(self, entity: EntityDefinition) -> str:
        """Generate React form component for an entity."""
        # Build field definitions for the form
        fields = []
        field_sections = [{'title': '', 'fields': []}]

        for prop in entity['properties']:
            if prop['name'] in ['id', 'created_at', 'updated_at']:
                continue

            field_type = get_form_field_type(prop['type'])

            field = {
                'name': prop['name'],
                'label': prop['name'].replace('_', ' ').title(),
                'type': field_type,
                'placeholder': f"Enter {prop['name'].replace('_', ' ')}",
                'required': prop.get('required', False),
                'description': prop.get('description', ''),
                'zod_schema': prop['zod_type'],
            }

            # Add type-specific properties
            if field_type == 'select' and prop.get('enum_values'):
                field['options'] = [{'value': v, 'label': v.replace('_', ' ').title()}
                                   for v in prop['enum_values']]

            if field_type == 'number':
                if 'min' in prop:
                    field['min'] = prop['min']
                if 'max' in prop:
                    field['max'] = prop['max']

            if field_type == 'switch':
                field['switch_label'] = field['label']
                field['switch_description'] = prop.get('description', f'Enable {field["label"]}')

            if prop.get('default_value') is not None:
                field['default_value'] = json.dumps(prop['default_value'])

            fields.append(field)
            field_sections[0]['fields'].append(field)

        # Check for date fields
        has_date_fields = any(p['type'] in ['date', 'datetime', 'timestamp']
                             for p in entity['properties'])

        context = {
            'entity_name': entity['name'],
            'entity_name_display': entity['display_name'],
            'entity_name_kebab': to_kebab_case(entity['name']),
            'fields': fields,
            'field_sections': field_sections,
            'has_date_fields': has_date_fields,
        }

        return self._form_template.render(**context)

    def _generate_entity_table(self, entity: EntityDefinition) -> str:
        """Generate React table component for an entity."""
        # Build column definitions
        columns = []
        status_column = None
        status_colors = {}
        status_options = []

        for prop in entity['properties']:
            if prop['name'] in ['created_at', 'updated_at'] and prop['name'] != entity['date_field']:
                continue

            cell_type = get_table_cell_type(prop['type'])

            # First column (usually name/title) should be a link
            if prop['name'] == entity['display_field']:
                cell_type = 'link'

            column = {
                'key': prop['name'],
                'header': prop['name'].replace('_', ' ').title(),
                'cell_type': cell_type,
                'sortable': prop['type'] not in ['json', 'object', 'array'],
            }

            # Handle status columns
            if prop['name'] == entity.get('status_field'):
                status_column = column
                if prop.get('enum_values'):
                    for value in prop['enum_values']:
                        # Assign colors based on common status patterns
                        if value in ['active', 'completed', 'success', 'approved', 'healthy']:
                            status_colors[value] = 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-400'
                        elif value in ['pending', 'in_progress', 'running', 'processing']:
                            status_colors[value] = 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-400'
                        elif value in ['warning', 'degraded', 'paused']:
                            status_colors[value] = 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-400'
                        elif value in ['error', 'failed', 'cancelled', 'rejected', 'inactive']:
                            status_colors[value] = 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
                        else:
                            status_colors[value] = 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-400'

                        status_options.append({'value': value, 'label': value.replace('_', ' ').title()})

            columns.append(column)

        context = {
            'entity_name': entity['name'],
            'entity_name_display': entity['display_name'],
            'entity_name_display_plural': pluralize(entity['display_name']),
            'entity_name_kebab': to_kebab_case(entity['name']),
            'entity_name_kebab_plural': to_kebab_case(pluralize(entity['name'])),
            'entity_name_plural': pluralize(entity['name']),
            'columns': columns,
            'status_column': status_column,
            'status_colors': status_colors,
            'status_options': status_options,
            'default_sort_column': entity['date_field'],
            'default_sort_desc': 'true',
            'default_page_size': 20,
            'selectable_default': False,
        }

        return self._table_template.render(**context)

    def _generate_entity_dashboard(self, entity: EntityDefinition) -> str:
        """Generate React dashboard component for an entity."""
        # Build metrics based on entity properties
        metrics = []
        metric_icons = set(['BarChart3', 'TrendingUp'])

        # Total count metric
        metrics.append({
            'title': f'Total {pluralize(entity["display_name"])}',
            'key': 'total',
            'change_key': 'total_change',
            'change_label': 'from last month',
            'icon': 'BarChart3',
            'href': f'/{to_kebab_case(pluralize(entity["name"]))}',
            'color': 'text-muted-foreground',
        })
        metric_icons.add('BarChart3')

        # Status-based metrics if status field exists
        if entity.get('status_field'):
            status_prop = next((p for p in entity['properties']
                               if p['name'] == entity['status_field']), None)
            if status_prop and status_prop.get('enum_values'):
                for status in status_prop['enum_values'][:3]:  # Limit to 3 status metrics
                    icon = 'CheckCircle2' if status in ['active', 'completed', 'approved'] else (
                        'Clock' if status in ['pending', 'in_progress'] else 'AlertCircle'
                    )
                    metrics.append({
                        'title': f'{status.replace("_", " ").title()} {pluralize(entity["display_name"])}',
                        'key': f'{status}_count',
                        'change_key': f'{status}_change',
                        'change_label': 'from last week',
                        'icon': icon,
                        'href': f'/{to_kebab_case(pluralize(entity["name"]))}?status={status}',
                        'color': 'text-muted-foreground',
                    })
                    metric_icons.add(icon)

        context = {
            'entity_name': entity['name'],
            'entity_name_display': entity['display_name'],
            'entity_name_display_plural': pluralize(entity['display_name']),
            'entity_name_kebab': to_kebab_case(entity['name']),
            'entity_name_kebab_plural': to_kebab_case(pluralize(entity['name'])),
            'entity_name_plural': pluralize(entity['name']),
            'metrics': metrics,
            'metric_icons': sorted(metric_icons),
            'primary_display_field': entity['display_field'],
            'secondary_display_field': entity.get('secondary_display_field'),
            'status_field': entity.get('status_field'),
            'date_display_field': entity['date_field'],
        }

        return self._dashboard_template.render(**context)

    def _generate_entity_hooks(self, entity: EntityDefinition) -> str:
        """Generate React Query hooks for an entity."""
        # Build list parameters from filterable properties
        list_params = []

        if entity.get('status_field'):
            list_params.append({
                'name': 'status',
                'type': 'string',
            })

        # Add search parameter
        list_params.append({
            'name': 'search',
            'type': 'string',
        })

        # Determine if entity has stats endpoint
        has_stats = entity.get('status_field') is not None

        # Build custom mutations based on status field
        custom_mutations = []
        if entity.get('status_field'):
            status_prop = next((p for p in entity['properties']
                               if p['name'] == entity['status_field']), None)
            if status_prop:
                custom_mutations.append({
                    'name': f'Update{entity["name"]}Status',
                    'description': f'Update the status of a {entity["display_name"].lower()}',
                    'params': f'{{ id, status, reason }}: {{ id: string; status: string; reason?: string }}',
                    'api_call': f'update{entity["name"]}Status(id, status, reason)',
                })

        context = {
            'entity_name': entity['name'],
            'entity_name_display': entity['display_name'],
            'entity_name_display_plural': pluralize(entity['display_name']),
            'entity_name_camel': to_camel_case(entity['name']),
            'entity_name_kebab': to_kebab_case(entity['name']),
            'entity_name_plural': pluralize(entity['name']),
            'list_params': list_params,
            'has_stats': has_stats,
            'custom_mutations': custom_mutations,
        }

        return self._hooks_template.render(**context)

    def _generate_entity_api_client(self, entity: EntityDefinition) -> str:
        """Generate API client functions for an entity."""
        # Build list parameters
        list_params = []

        if entity.get('status_field'):
            list_params.append({
                'name': 'status',
                'type': 'string',
                'api_name': 'status',
            })

        list_params.append({
            'name': 'search',
            'type': 'string',
            'api_name': 'search',
        })

        # Determine if entity has stats endpoint
        has_stats = entity.get('status_field') is not None

        # Build stats properties
        stats_properties = []
        if has_stats:
            stats_properties = [
                {'name': 'total', 'ts_type': 'number'},
                {'name': 'total_change', 'ts_type': 'number'},
            ]
            status_prop = next((p for p in entity['properties']
                               if p['name'] == entity['status_field']), None)
            if status_prop and status_prop.get('enum_values'):
                for status in status_prop['enum_values']:
                    stats_properties.append({'name': f'{status}_count', 'ts_type': 'number'})
                    stats_properties.append({'name': f'{status}_change', 'ts_type': 'number'})

        # Build custom endpoints
        custom_endpoints = []
        if entity.get('status_field'):
            custom_endpoints.append({
                'name': f'update{entity["name"]}Status',
                'description': f'Update the status of a {entity["display_name"].lower()}',
                'params': 'id: string, status: string, reason?: string',
                'return_type': entity['name'],
                'path': f'/{to_kebab_case(pluralize(entity["name"]))}/${{id}}/status',
                'method': 'POST',
                'has_body': True,
                'body_param': '{ status, reason }',
            })

        context = {
            'entity_name': entity['name'],
            'entity_name_display': entity['display_name'],
            'entity_name_display_plural': pluralize(entity['display_name']),
            'entity_name_plural': pluralize(entity['name']),
            'api_endpoint': to_kebab_case(pluralize(entity['name'])),
            'properties': entity['properties'],
            'summary_properties': [p for p in entity['properties']
                                   if p['name'] in ['id', entity['display_field'],
                                                   entity.get('status_field', ''),
                                                   entity['date_field']]
                                   or p.get('required', False)],
            'create_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'update_properties': [p for p in entity['properties']
                                  if p['name'] not in ['id', 'created_at', 'updated_at']],
            'list_params': list_params,
            'has_stats': has_stats,
            'stats_properties': stats_properties,
            'custom_endpoints': custom_endpoints,
        }

        return self._api_template.render(**context)

    async def _analyze_ontology(self, state: AppBuilderState) -> Dict[str, Any]:
        """Analyze ontology to identify UI component needs."""
        context = state.get("agent_context", {})
        ontology_schema = context.get("ontology_schema", {})
        ui_requirements = context.get("ui_requirements", {})

        # Parse ontology into entity definitions
        entities = self._parse_ontology_schema(ontology_schema)

        # Use LLM to enhance entity definitions with UI recommendations
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Analyze the following ontology schema to identify UI components needed.

Ontology Schema:
{json.dumps(ontology_schema, indent=2)}

UI Requirements:
{json.dumps(ui_requirements, indent=2)}

Parsed Entities:
{json.dumps([{'name': e['name'], 'properties': [p['name'] for p in e['properties']]} for e in entities], indent=2)}

Identify:
1. Entity types that need CRUD forms
2. Entities that need list/table views
3. Relationships that need selection/linking UI
4. Data types and their appropriate input controls
5. Dashboard widgets needed for each entity type
6. Navigation structure based on entity relationships

Provide a structured analysis with component recommendations for each entity.""")
        ]

        response = await self.llm.ainvoke(messages)

        decision = add_decision(
            state,
            decision_type="ontology_analysis",
            description="Analyzed ontology for UI component requirements",
            confidence=0.85,
            reasoning="Identified entity types, relationships, and data types for UI generation"
        )

        return {
            "outputs": {
                "ontology_analysis": response.content,
                "parsed_entities": entities,
            },
            "decisions": [decision],
            "current_step": "analyze_ontology",
            "messages": [Message(role="assistant", content=response.content)]
        }

    async def _generate_types(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate TypeScript type definitions from ontology."""
        outputs = state.get("outputs", {})
        entities = outputs.get("parsed_entities", [])

        type_files: List[ComponentFile] = []
        zod_files: List[ComponentFile] = []

        for entity in entities:
            # Generate TypeScript types
            types_code = self._generate_entity_types(entity)
            type_files.append({
                'entity': entity['name'],
                'code': types_code,
                'filename': f"{to_kebab_case(entity['name'])}.types.ts",
            })

            # Generate Zod schemas
            zod_code = self._generate_entity_zod_schema(entity)
            zod_files.append({
                'entity': entity['name'],
                'code': zod_code,
                'filename': f"{to_kebab_case(entity['name'])}.schema.ts",
            })

        decision = add_decision(
            state,
            decision_type="type_generation",
            description=f"Generated TypeScript type definitions for {len(entities)} entities",
            confidence=0.90,
            reasoning="Created type-safe interfaces from ontology schema"
        )

        return {
            "outputs": {
                "type_files": type_files,
                "zod_files": zod_files,
            },
            "decisions": [decision],
            "current_step": "generate_types",
            "messages": [Message(role="assistant", content=f"Generated types for {len(entities)} entities")]
        }

    async def _generate_forms(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate form component specifications."""
        outputs = state.get("outputs", {})
        entities = outputs.get("parsed_entities", [])

        # Include validation feedback if present
        validation_feedback = outputs.get("validation_feedback", "")

        form_files: List[ComponentFile] = []

        for entity in entities:
            form_code = self._generate_entity_form(entity)
            form_files.append({
                'entity': entity['name'],
                'code': form_code,
                'filename': f"{entity['name']}Form.tsx",
            })

        decision = add_decision(
            state,
            decision_type="form_generation",
            description=f"Generated form components for {len(entities)} entities",
            confidence=0.85,
            reasoning="Created form specs with validation, accessibility, and relationship handling"
        )

        return {
            "outputs": {"form_files": form_files},
            "decisions": [decision],
            "current_step": "generate_forms",
            "messages": [Message(role="assistant", content=f"Generated forms for {len(entities)} entities")]
        }

    async def _generate_tables(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate table/grid component specifications."""
        outputs = state.get("outputs", {})
        entities = outputs.get("parsed_entities", [])

        table_files: List[ComponentFile] = []

        for entity in entities:
            table_code = self._generate_entity_table(entity)
            table_files.append({
                'entity': entity['name'],
                'code': table_code,
                'filename': f"{entity['name']}Table.tsx",
            })

        decision = add_decision(
            state,
            decision_type="table_generation",
            description=f"Generated table components for {len(entities)} entities",
            confidence=0.85,
            reasoning="Created data grid specs with sorting, filtering, and pagination"
        )

        return {
            "outputs": {"table_files": table_files},
            "decisions": [decision],
            "current_step": "generate_tables",
            "messages": [Message(role="assistant", content=f"Generated tables for {len(entities)} entities")]
        }

    async def _generate_dashboards(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate dashboard layout specifications."""
        outputs = state.get("outputs", {})
        entities = outputs.get("parsed_entities", [])

        dashboard_files: List[ComponentFile] = []

        for entity in entities:
            dashboard_code = self._generate_entity_dashboard(entity)
            dashboard_files.append({
                'entity': entity['name'],
                'code': dashboard_code,
                'filename': f"{entity['name']}Dashboard.tsx",
            })

        decision = add_decision(
            state,
            decision_type="dashboard_generation",
            description=f"Generated dashboard components for {len(entities)} entities",
            confidence=0.80,
            reasoning="Created dashboard layouts with widgets, charts, and data bindings"
        )

        return {
            "outputs": {"dashboard_files": dashboard_files},
            "decisions": [decision],
            "current_step": "generate_dashboards",
            "messages": [Message(role="assistant", content=f"Generated dashboards for {len(entities)} entities")]
        }

    async def _generate_hooks(self, state: AppBuilderState) -> Dict[str, Any]:
        """Generate React Query hooks and API client functions."""
        outputs = state.get("outputs", {})
        entities = outputs.get("parsed_entities", [])

        hook_files: List[ComponentFile] = []
        api_files: List[ComponentFile] = []

        for entity in entities:
            # Generate hooks
            hooks_code = self._generate_entity_hooks(entity)
            hook_files.append({
                'entity': entity['name'],
                'code': hooks_code,
                'filename': f"use-{to_kebab_case(entity['name'])}.ts",
            })

            # Generate API client
            api_code = self._generate_entity_api_client(entity)
            api_files.append({
                'entity': entity['name'],
                'code': api_code,
                'filename': f"{to_kebab_case(entity['name'])}.api.ts",
            })

        decision = add_decision(
            state,
            decision_type="hooks_generation",
            description=f"Generated React Query hooks for {len(entities)} entities",
            confidence=0.90,
            reasoning="Created hooks with proper cache invalidation and optimistic updates"
        )

        return {
            "outputs": {
                "hook_files": hook_files,
                "api_files": api_files,
            },
            "decisions": [decision],
            "current_step": "generate_hooks",
            "messages": [Message(role="assistant", content=f"Generated hooks for {len(entities)} entities")]
        }

    async def _compile_specs(self, state: AppBuilderState) -> Dict[str, Any]:
        """Compile all component specifications into a unified spec."""
        outputs = state.get("outputs", {})

        # Gather all generated files
        component_specs: ComponentSpecs = {
            'forms': outputs.get('form_files', []),
            'tables': outputs.get('table_files', []),
            'dashboards': outputs.get('dashboard_files', []),
            'types': outputs.get('type_files', []),
            'hooks': outputs.get('hook_files', []),
            'api_clients': outputs.get('api_files', []),
            'zod_schemas': outputs.get('zod_files', []),
        }

        # Generate summary
        summary = {
            'total_components': sum(len(v) for v in component_specs.values()),
            'entities': list(set(f['entity'] for f in component_specs['forms'])),
            'files': {
                'forms': [f['filename'] for f in component_specs['forms']],
                'tables': [f['filename'] for f in component_specs['tables']],
                'dashboards': [f['filename'] for f in component_specs['dashboards']],
                'types': [f['filename'] for f in component_specs['types']],
                'hooks': [f['filename'] for f in component_specs['hooks']],
                'api_clients': [f['filename'] for f in component_specs['api_clients']],
                'zod_schemas': [f['filename'] for f in component_specs['zod_schemas']],
            },
        }

        decision = add_decision(
            state,
            decision_type="spec_compilation",
            description="Compiled unified UI specification",
            confidence=0.85,
            reasoning="Combined all component specs into comprehensive UI specification"
        )

        # Store all component specs in the state
        ui_components = [
            {"type": "types", "content": component_specs['types']},
            {"type": "forms", "content": component_specs['forms']},
            {"type": "tables", "content": component_specs['tables']},
            {"type": "dashboards", "content": component_specs['dashboards']},
            {"type": "hooks", "content": component_specs['hooks']},
            {"type": "api_clients", "content": component_specs['api_clients']},
            {"type": "zod_schemas", "content": component_specs['zod_schemas']},
        ]

        return {
            "outputs": {
                "component_specs": component_specs,
                "component_summary": summary,
            },
            "ui_components": ui_components,
            "decisions": [decision],
            "current_step": "compile_specs",
            "messages": [Message(role="assistant", content=f"Compiled {summary['total_components']} components")]
        }

    async def _validate_components(self, state: AppBuilderState) -> Dict[str, Any]:
        """Validate the generated component specifications."""
        outputs = state.get("outputs", {})
        context = state.get("agent_context", {})
        component_specs = outputs.get("component_specs", {})
        component_summary = outputs.get("component_summary", {})
        ui_requirements = context.get("ui_requirements", {})

        # Use LLM to validate components against requirements
        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=f"""Validate the generated UI component specifications.

Component Summary:
{json.dumps(component_summary, indent=2)}

Original UI Requirements:
{json.dumps(ui_requirements, indent=2)}

Validate:
1. All required entities have CRUD forms
2. All entities have list/table views
3. Dashboard covers key metrics
4. Type definitions are complete and consistent
5. Component props are properly typed
6. Accessibility requirements are met
7. Responsive design is addressed
8. Validation rules are appropriate
9. Navigation structure is logical
10. API integration points are defined

Provide:
1. Validation status (PASS/FAIL)
2. Coverage report (which requirements are addressed)
3. List of any issues or gaps found
4. Recommendations for improvement
5. Confidence score (0-1)""")
        ]

        response = await self.llm.ainvoke(messages)

        # Parse validation result
        response_lower = response.content.lower()
        needs_refinement = "fail" in response_lower or "issue" in response_lower or "gap" in response_lower

        confidence = 0.90 if not needs_refinement else 0.70

        decision = add_decision(
            state,
            decision_type="ui_validation",
            description="Validated UI component specifications",
            confidence=confidence,
            reasoning=response.content[:500],
            requires_approval=needs_refinement
        )

        review_items = []
        if needs_refinement:
            review_items.append(mark_for_review(
                state,
                item_type="ui_components",
                item_id="validation_issues",
                description="UI component specifications have issues that may need review",
                priority="medium"
            ))

        return {
            "outputs": {
                "validation_result": response.content,
                "needs_refinement": needs_refinement,
                "validation_feedback": response.content if needs_refinement else ""
            },
            "decisions": [decision],
            "requires_human_review": needs_refinement,
            "review_items": review_items,
            "current_step": "validate_components",
            "messages": [Message(role="assistant", content=response.content)]
        }

    def _should_refine(self, state: AppBuilderState) -> str:
        """Determine if components need refinement."""
        outputs = state.get("outputs", {})
        needs_refinement = outputs.get("needs_refinement", False)

        # Track iterations to prevent infinite loops
        iteration_count = state.get("agent_context", {}).get("iteration_count", 0)
        max_iterations = self.config.get("max_iterations", 3)

        if needs_refinement and iteration_count < max_iterations:
            return "refine"
        return "complete"

    # =========================================================================
    # Public API for Component Generation
    # =========================================================================

    async def generate_components(
        self,
        ontology_schema: Dict[str, Any],
        ui_requirements: Optional[Dict[str, Any]] = None
    ) -> ComponentSpecs:
        """
        Generate all UI components from an ontology schema.

        Args:
            ontology_schema: The ontology definition with entities and properties
            ui_requirements: Optional UI requirements and preferences

        Returns:
            ComponentSpecs with all generated component files
        """
        initial_state: AppBuilderState = {
            "agent_context": {
                "ontology_schema": ontology_schema,
                "ui_requirements": ui_requirements or {},
                "iteration_count": 0,
            },
            "outputs": {},
            "decisions": [],
            "messages": [],
            "current_step": "",
            "requires_human_review": False,
            "review_items": [],
            "ui_components": [],
        }

        # Run the graph
        final_state = await self.run(initial_state)

        return final_state.get("outputs", {}).get("component_specs", {
            'forms': [],
            'tables': [],
            'dashboards': [],
            'types': [],
            'hooks': [],
            'api_clients': [],
            'zod_schemas': [],
        })

    def generate_form_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate a form component for an entity."""
        return self._generate_entity_form(entity)

    def generate_table_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate a table component for an entity."""
        return self._generate_entity_table(entity)

    def generate_dashboard_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate a dashboard component for an entity."""
        return self._generate_entity_dashboard(entity)

    def generate_types_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate TypeScript types for an entity."""
        return self._generate_entity_types(entity)

    def generate_hooks_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate React Query hooks for an entity."""
        return self._generate_entity_hooks(entity)

    def generate_api_client_sync(self, entity: EntityDefinition) -> str:
        """Synchronously generate API client for an entity."""
        return self._generate_entity_api_client(entity)
