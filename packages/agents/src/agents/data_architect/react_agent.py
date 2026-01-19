"""
Data Architect ReAct Agent using LangGraph's create_react_agent pattern.

This agent handles ontology design, schema creation, and ETL specification
with memory-aware capabilities.
"""
from typing import List, Dict, Any, Optional
import json
import logging

from langchain_core.language_models import BaseChatModel
from langchain_core.tools import tool, BaseTool
from langgraph.checkpoint.postgres import PostgresSaver
from langgraph.store.postgres import PostgresStore

from agent_framework.agents import MemoryAwareAgent
from orchestration.registry.agent_registry import register_agent, AgentCategory

logger = logging.getLogger(__name__)


# Data Architect system prompt
DATA_ARCHITECT_SYSTEM_PROMPT = """You are the Data Architect Agent for Open Forge, an enterprise data platform.

## Your Role
You design data models, ontologies, and transformation specifications that form the backbone
of enterprise data solutions. You work with requirements from the Discovery phase to create
LinkML-compatible schemas and ETL specifications.

## Capabilities
1. **Ontology Design**: Create semantic data models using LinkML that capture entities,
   relationships, and attributes for the domain.

2. **Schema Definition**: Define database schemas, validation rules, and constraints
   that implement the ontology.

3. **ETL Specification**: Design data transformation pipelines that map source data
   to the target ontology.

## Output Formats
- Ontologies should be in LinkML YAML format
- Schemas should follow standard SQL or document store conventions
- ETL specs should be declarative YAML with source-to-target mappings

## Best Practices
- Start with core entities before adding relationships
- Use semantic naming conventions (PascalCase for classes, snake_case for attributes)
- Include validation rules for data quality
- Document design decisions and rationale
- Flag complex transformations that may need review

## LinkML Guidelines
- Define a schema prefix and namespace
- Use slots for reusable attributes
- Define enums for constrained values
- Add descriptions to all elements
"""


@register_agent(
    name="data_architect_react",
    category=AgentCategory.DATA_ARCHITECT,
    description="Data Architect agent using ReAct pattern for ontology design, "
                "schema creation, and ETL specification",
    version="1.0.0",
    required_inputs=["engagement_id"],
    output_keys=["ontology_schema", "entity_definitions", "etl_specification"],
    capabilities=["ontology_design", "schema_validation", "etl_specification"],
    dependencies=["discovery_react"],
    is_react_agent=True,
    is_memory_aware=True,
)
class DataArchitectReActAgent(MemoryAwareAgent):
    """
    Data Architect agent using LangGraph's ReAct pattern with memory capabilities.

    This agent combines:
    - ReAct pattern for iterative schema design
    - Memory tools for persisting design artifacts
    - Specialized tools for ontology and ETL creation

    Example:
        agent = DataArchitectReActAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="data_architect_1"
        )

        result = await agent.run(
            "Design an ontology for customer order management",
            thread_id="design_orders_1"
        )
    """

    def get_tools(self) -> List[BaseTool]:
        """
        Get data architect-specific tools.

        Returns:
            List of tools for ontology design, schema creation, and ETL
        """
        engagement_id = self.engagement_id
        store = self.store

        @tool
        async def design_entity(
            entity_name: str,
            description: str,
            attributes: str,
            primary_key: str,
            is_abstract: bool = False,
            parent_entity: str = "",
        ) -> str:
            """
            Design and document an entity for the ontology.

            Use this to define individual entities (classes) that will be
            part of the domain ontology.

            Args:
                entity_name: Name of the entity (PascalCase)
                description: What this entity represents
                attributes: JSON string of attribute definitions
                    e.g., '{"name": {"type": "string", "required": true}, "age": {"type": "integer"}}'
                primary_key: The attribute that uniquely identifies instances
                is_abstract: Whether this is an abstract base entity
                parent_entity: Optional parent entity for inheritance

            Returns:
                Confirmation with the entity definition
            """
            import uuid

            try:
                attrs = json.loads(attributes) if isinstance(attributes, str) else attributes
            except json.JSONDecodeError:
                return f"Error: attributes must be valid JSON. Got: {attributes}"

            entity = {
                "name": entity_name,
                "description": description,
                "attributes": attrs,
                "primary_key": primary_key,
                "is_abstract": is_abstract,
                "parent_entity": parent_entity,
            }

            namespace = ("engagements", engagement_id, "entity")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": entity,
                        "search_text": f"{entity_name} {description} {' '.join(attrs.keys())}",
                    }
                )
                logger.info(f"Designed entity: {entity_name}")
                return f"Designed entity: {entity_name} with {len(attrs)} attributes (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing entity: {e}")
                return f"Error storing entity: {str(e)}"

        @tool
        async def define_relationship(
            relationship_name: str,
            source_entity: str,
            target_entity: str,
            cardinality: str,
            description: str,
            is_bidirectional: bool = False,
            inverse_name: str = "",
        ) -> str:
            """
            Define a relationship between two entities.

            Use this to capture how entities relate to each other in the domain.

            Args:
                relationship_name: Name of the relationship (snake_case)
                source_entity: The entity this relationship originates from
                target_entity: The entity this relationship points to
                cardinality: Relationship cardinality (one_to_one, one_to_many, many_to_many)
                description: What this relationship represents
                is_bidirectional: Whether the relationship works both ways
                inverse_name: Name of the inverse relationship (if bidirectional)

            Returns:
                Confirmation with the relationship definition
            """
            import uuid

            relationship = {
                "name": relationship_name,
                "source": source_entity,
                "target": target_entity,
                "cardinality": cardinality,
                "description": description,
                "bidirectional": is_bidirectional,
                "inverse_name": inverse_name,
            }

            namespace = ("engagements", engagement_id, "relationship")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": relationship,
                        "search_text": f"{relationship_name} {source_entity} {target_entity} {description}",
                    }
                )
                logger.info(f"Defined relationship: {relationship_name}")
                return f"Defined relationship: {source_entity} --[{relationship_name}]--> {target_entity} (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing relationship: {e}")
                return f"Error storing relationship: {str(e)}"

        @tool
        async def generate_linkml_schema(
            schema_name: str,
            schema_prefix: str,
            description: str,
        ) -> str:
            """
            Generate a LinkML schema from all defined entities and relationships.

            Use this to compile all entity and relationship definitions into
            a complete LinkML ontology schema.

            Args:
                schema_name: Name for the schema (e.g., "CustomerDomain")
                schema_prefix: Short prefix for the schema (e.g., "cust")
                description: Description of what the schema covers

            Returns:
                The generated LinkML YAML schema
            """
            import uuid

            # Gather all entities
            entities = []
            try:
                namespace = ("engagements", engagement_id, "entity")
                entity_items = await store.alist(namespace=namespace, limit=100)
                for item in entity_items:
                    entities.append(item.value.get("content", {}))
            except Exception as e:
                logger.warning(f"Error getting entities: {e}")

            # Gather all relationships
            relationships = []
            try:
                namespace = ("engagements", engagement_id, "relationship")
                rel_items = await store.alist(namespace=namespace, limit=100)
                for item in rel_items:
                    relationships.append(item.value.get("content", {}))
            except Exception as e:
                logger.warning(f"Error getting relationships: {e}")

            if not entities:
                return "No entities defined yet. Use design_entity to create entities first."

            # Build LinkML schema
            schema_lines = [
                f"id: https://openforge.io/schemas/{schema_prefix}",
                f"name: {schema_name}",
                f"prefixes:",
                f"  linkml: https://w3id.org/linkml/",
                f"  {schema_prefix}: https://openforge.io/schemas/{schema_prefix}/",
                f"default_prefix: {schema_prefix}",
                f"default_range: string",
                f"",
                f"description: |",
                f"  {description}",
                f"",
                f"classes:",
            ]

            # Add entity classes
            for entity in entities:
                name = entity.get("name", "Unknown")
                desc = entity.get("description", "")
                attrs = entity.get("attributes", {})
                parent = entity.get("parent_entity", "")
                is_abstract = entity.get("is_abstract", False)

                schema_lines.append(f"  {name}:")
                if desc:
                    schema_lines.append(f"    description: {desc}")
                if is_abstract:
                    schema_lines.append(f"    abstract: true")
                if parent:
                    schema_lines.append(f"    is_a: {parent}")

                if attrs:
                    schema_lines.append(f"    attributes:")
                    for attr_name, attr_def in attrs.items():
                        schema_lines.append(f"      {attr_name}:")
                        if isinstance(attr_def, dict):
                            attr_type = attr_def.get("type", "string")
                            required = attr_def.get("required", False)
                            attr_desc = attr_def.get("description", "")
                            schema_lines.append(f"        range: {attr_type}")
                            if required:
                                schema_lines.append(f"        required: true")
                            if attr_desc:
                                schema_lines.append(f"        description: {attr_desc}")
                        else:
                            schema_lines.append(f"        range: {attr_def}")

                # Add relationships as attributes
                entity_rels = [r for r in relationships if r.get("source") == name]
                for rel in entity_rels:
                    rel_name = rel.get("name", "related_to")
                    target = rel.get("target", "")
                    cardinality = rel.get("cardinality", "one_to_one")
                    rel_desc = rel.get("description", "")

                    schema_lines.append(f"      {rel_name}:")
                    schema_lines.append(f"        range: {target}")
                    if "many" in cardinality:
                        schema_lines.append(f"        multivalued: true")
                    if rel_desc:
                        schema_lines.append(f"        description: {rel_desc}")

                schema_lines.append("")

            schema_yaml = "\n".join(schema_lines)

            # Store the schema
            namespace = ("engagements", engagement_id, "artifact")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": {
                            "type": "linkml_schema",
                            "name": schema_name,
                            "yaml": schema_yaml,
                        },
                        "search_text": f"linkml schema {schema_name} ontology",
                    }
                )
                logger.info(f"Generated LinkML schema: {schema_name}")
            except Exception as e:
                logger.warning(f"Error storing schema: {e}")

            return f"Generated LinkML Schema:\n\n```yaml\n{schema_yaml}\n```"

        @tool
        async def create_etl_mapping(
            source_name: str,
            source_type: str,
            target_entity: str,
            field_mappings: str,
            transformation_rules: str = "",
            validation_rules: str = "",
        ) -> str:
            """
            Create an ETL mapping specification for a data source.

            Use this to define how source data should be transformed and
            loaded into the target ontology.

            Args:
                source_name: Name of the source system/table
                source_type: Type of source (database, api, file)
                target_entity: Target entity in the ontology
                field_mappings: JSON mapping of source fields to target attributes
                    e.g., '{"customer_id": "id", "cust_name": "name"}'
                transformation_rules: JSON array of transformation rules
                    e.g., '[{"type": "concat", "source": ["first", "last"], "target": "full_name"}]'
                validation_rules: JSON array of validation rules
                    e.g., '[{"field": "email", "rule": "email_format"}]'

            Returns:
                Confirmation with the ETL mapping specification
            """
            import uuid

            try:
                mappings = json.loads(field_mappings) if isinstance(field_mappings, str) else field_mappings
                transforms = json.loads(transformation_rules) if transformation_rules else []
                validations = json.loads(validation_rules) if validation_rules else []
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            etl_spec = {
                "source": {
                    "name": source_name,
                    "type": source_type,
                },
                "target": {
                    "entity": target_entity,
                },
                "mappings": mappings,
                "transformations": transforms,
                "validations": validations,
            }

            namespace = ("engagements", engagement_id, "etl_mapping")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": etl_spec,
                        "search_text": f"etl {source_name} to {target_entity} mapping transformation",
                    }
                )
                logger.info(f"Created ETL mapping: {source_name} -> {target_entity}")
                return f"Created ETL mapping: {source_name} -> {target_entity} with {len(mappings)} field mappings (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing ETL mapping: {e}")
                return f"Error storing ETL mapping: {str(e)}"

        @tool
        async def validate_schema_design(
            check_completeness: bool = True,
            check_relationships: bool = True,
            check_naming: bool = True,
        ) -> str:
            """
            Validate the current schema design for completeness and consistency.

            Use this to check the schema design before finalizing.

            Args:
                check_completeness: Check if all entities have required attributes
                check_relationships: Check if all relationships reference valid entities
                check_naming: Check if naming conventions are followed

            Returns:
                Validation report with findings
            """
            findings = []
            warnings = []
            entity_names = set()

            # Get all entities
            try:
                namespace = ("engagements", engagement_id, "entity")
                entity_items = await store.alist(namespace=namespace, limit=100)
                entities = [item.value.get("content", {}) for item in entity_items]
            except Exception:
                entities = []

            for entity in entities:
                name = entity.get("name", "")
                entity_names.add(name)

                if check_completeness:
                    attrs = entity.get("attributes", {})
                    if not attrs:
                        warnings.append(f"Entity '{name}' has no attributes defined")
                    if not entity.get("primary_key"):
                        warnings.append(f"Entity '{name}' has no primary key defined")
                    if not entity.get("description"):
                        warnings.append(f"Entity '{name}' is missing a description")

                if check_naming:
                    if not name[0].isupper():
                        warnings.append(f"Entity '{name}' should use PascalCase")
                    for attr_name in entity.get("attributes", {}).keys():
                        if attr_name != attr_name.lower():
                            warnings.append(f"Attribute '{attr_name}' in {name} should use snake_case")

            # Get all relationships
            try:
                namespace = ("engagements", engagement_id, "relationship")
                rel_items = await store.alist(namespace=namespace, limit=100)
                relationships = [item.value.get("content", {}) for item in rel_items]
            except Exception:
                relationships = []

            if check_relationships:
                for rel in relationships:
                    source = rel.get("source", "")
                    target = rel.get("target", "")
                    if source not in entity_names:
                        findings.append(f"Relationship '{rel.get('name')}' references unknown source entity '{source}'")
                    if target not in entity_names:
                        findings.append(f"Relationship '{rel.get('name')}' references unknown target entity '{target}'")

            # Build report
            report_lines = ["## Schema Validation Report\n"]
            report_lines.append(f"- Entities: {len(entities)}")
            report_lines.append(f"- Relationships: {len(relationships)}\n")

            if findings:
                report_lines.append("### Errors (must fix)")
                for f in findings:
                    report_lines.append(f"- {f}")
                report_lines.append("")

            if warnings:
                report_lines.append("### Warnings (should review)")
                for w in warnings:
                    report_lines.append(f"- {w}")
                report_lines.append("")

            if not findings and not warnings:
                report_lines.append("Schema validation passed with no issues.")

            return "\n".join(report_lines)

        return [
            design_entity,
            define_relationship,
            generate_linkml_schema,
            create_etl_mapping,
            validate_schema_design,
        ]

    def get_system_prompt(self) -> str:
        """Get the data architect agent system prompt."""
        return DATA_ARCHITECT_SYSTEM_PROMPT


# Factory function for easier instantiation
def create_data_architect_react_agent(
    llm: BaseChatModel,
    checkpointer: PostgresSaver,
    store: PostgresStore,
    engagement_id: str,
    agent_id: str = "data_architect_react",
) -> DataArchitectReActAgent:
    """
    Create a configured Data Architect ReAct agent.

    Args:
        llm: The language model to use
        checkpointer: PostgresSaver for thread checkpoints
        store: PostgresStore for long-term memory
        engagement_id: The engagement this agent operates within
        agent_id: Optional custom agent ID

    Returns:
        Configured DataArchitectReActAgent instance
    """
    return DataArchitectReActAgent(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        engagement_id=engagement_id,
        agent_id=agent_id,
    )
