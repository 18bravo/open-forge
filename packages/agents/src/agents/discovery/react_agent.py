"""
Discovery ReAct Agent using LangGraph's create_react_agent pattern.

This agent handles stakeholder interviews, data source discovery, and
requirements gathering with memory-aware capabilities.
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


# Discovery system prompt
DISCOVERY_SYSTEM_PROMPT = """You are the Discovery Agent for Open Forge, an enterprise data platform.

## Your Role
You help organizations understand their data landscape, stakeholder needs, and requirements
for building enterprise data solutions. You conduct interviews, discover data sources,
and document requirements systematically.

## Capabilities
1. **Stakeholder Analysis**: Interview stakeholders to understand their roles, responsibilities,
   data needs, pain points, and priorities.

2. **Data Source Discovery**: Identify and catalog existing data sources including databases,
   APIs, files, and third-party systems.

3. **Requirements Gathering**: Synthesize information from stakeholders into clear,
   prioritized requirements with acceptance criteria.

## Best Practices
- Ask clarifying questions when requirements are ambiguous
- Document assumptions and decisions made during discovery
- Identify dependencies and integration points early
- Flag items that need human review or approval
- Use memory tools to build a persistent knowledge base

## Output Formats
- Stakeholder profiles should include: role, responsibilities, data needs, priorities
- Data sources should include: name, type, connection info, data quality notes
- Requirements should include: description, priority, acceptance criteria, dependencies

Always be thorough but concise in your responses.
"""


@register_agent(
    name="discovery_react",
    category=AgentCategory.DISCOVERY,
    description="Discovery agent using ReAct pattern for stakeholder interviews, "
                "data source discovery, and requirements gathering",
    version="1.0.0",
    required_inputs=["engagement_id"],
    output_keys=["stakeholders", "data_sources", "requirements", "discovery_summary"],
    capabilities=["stakeholder_interview", "data_discovery", "requirements_gathering"],
    is_react_agent=True,
    is_memory_aware=True,
)
class DiscoveryReActAgent(MemoryAwareAgent):
    """
    Discovery agent using LangGraph's ReAct pattern with memory capabilities.

    This agent combines:
    - ReAct (Reasoning + Acting) pattern for step-by-step problem solving
    - Memory tools for persisting discovered information
    - Specialized tools for stakeholder interviews and data discovery

    Example:
        agent = DiscoveryReActAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="discovery_1"
        )

        result = await agent.run(
            "Interview the CTO about their data infrastructure priorities",
            thread_id="interview_cto_1"
        )
    """

    def get_tools(self) -> List[BaseTool]:
        """
        Get discovery-specific tools.

        Returns:
            List of tools for stakeholder interviews, data discovery, and requirements
        """
        engagement_id = self.engagement_id
        store = self.store

        @tool
        async def conduct_stakeholder_interview(
            stakeholder_name: str,
            role: str,
            interview_notes: str,
            key_priorities: str,
            data_needs: str,
            pain_points: str,
        ) -> str:
            """
            Document a stakeholder interview and store the profile.

            Use this after interviewing a stakeholder to record their information
            for future reference by other agents.

            Args:
                stakeholder_name: Full name of the stakeholder
                role: Their job title/role in the organization
                interview_notes: Summary of the interview conversation
                key_priorities: Their top priorities (comma-separated)
                data_needs: Their data requirements and needs
                pain_points: Current challenges they face

            Returns:
                Confirmation with the stored stakeholder profile ID
            """
            import uuid

            profile = {
                "name": stakeholder_name,
                "role": role,
                "interview_notes": interview_notes,
                "priorities": [p.strip() for p in key_priorities.split(",")],
                "data_needs": data_needs,
                "pain_points": pain_points,
                "interviewed_at": "now",
            }

            namespace = ("engagements", engagement_id, "stakeholder")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": profile,
                        "search_text": f"{stakeholder_name} {role} {interview_notes} {data_needs} {pain_points}",
                    }
                )
                logger.info(f"Stored stakeholder profile: {stakeholder_name}")
                return f"Stored stakeholder profile for {stakeholder_name} (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing stakeholder: {e}")
                return f"Error storing stakeholder profile: {str(e)}"

        @tool
        async def catalog_data_source(
            source_name: str,
            source_type: str,
            description: str,
            connection_info: str,
            data_quality_notes: str,
            owner: str,
            refresh_frequency: str = "unknown",
        ) -> str:
            """
            Catalog a discovered data source for the engagement.

            Use this when you identify a data source that should be included
            in the data platform.

            Args:
                source_name: Name/identifier for the data source
                source_type: Type (database, api, file, streaming, etc.)
                description: What data this source contains
                connection_info: How to connect (sanitized, no credentials)
                data_quality_notes: Notes on data quality, completeness, etc.
                owner: Who owns/maintains this data source
                refresh_frequency: How often the data is updated

            Returns:
                Confirmation with the cataloged source ID
            """
            import uuid

            source = {
                "name": source_name,
                "type": source_type,
                "description": description,
                "connection_info": connection_info,
                "quality_notes": data_quality_notes,
                "owner": owner,
                "refresh_frequency": refresh_frequency,
            }

            namespace = ("engagements", engagement_id, "data_source")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": source,
                        "search_text": f"{source_name} {source_type} {description} {owner}",
                    }
                )
                logger.info(f"Cataloged data source: {source_name}")
                return f"Cataloged data source: {source_name} (ID: {key})"
            except Exception as e:
                logger.error(f"Error cataloging data source: {e}")
                return f"Error cataloging data source: {str(e)}"

        @tool
        async def document_requirement(
            requirement_title: str,
            description: str,
            priority: str,
            source_stakeholder: str,
            acceptance_criteria: str,
            dependencies: str = "",
            notes: str = "",
        ) -> str:
            """
            Document a requirement discovered during the engagement.

            Use this to formally capture requirements that have been identified
            through stakeholder interviews or analysis.

            Args:
                requirement_title: Short title for the requirement
                description: Detailed description of what is needed
                priority: Priority level (critical, high, medium, low)
                source_stakeholder: Who requested/needs this requirement
                acceptance_criteria: How we know this requirement is met
                dependencies: Other requirements or systems this depends on
                notes: Additional context or implementation notes

            Returns:
                Confirmation with the requirement ID
            """
            import uuid

            requirement = {
                "title": requirement_title,
                "description": description,
                "priority": priority.lower(),
                "source_stakeholder": source_stakeholder,
                "acceptance_criteria": acceptance_criteria,
                "dependencies": [d.strip() for d in dependencies.split(",") if d.strip()],
                "notes": notes,
            }

            namespace = ("engagements", engagement_id, "requirement")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": requirement,
                        "search_text": f"{requirement_title} {description} {priority} {source_stakeholder}",
                    }
                )
                logger.info(f"Documented requirement: {requirement_title}")
                return f"Documented requirement: {requirement_title} (ID: {key})"
            except Exception as e:
                logger.error(f"Error documenting requirement: {e}")
                return f"Error documenting requirement: {str(e)}"

        @tool
        async def analyze_business_process(
            process_name: str,
            description: str,
            stakeholders_involved: str,
            data_inputs: str,
            data_outputs: str,
            pain_points: str,
            improvement_opportunities: str,
        ) -> str:
            """
            Document a business process that involves data.

            Use this to capture business processes that the data platform
            needs to support or improve.

            Args:
                process_name: Name of the business process
                description: What this process does
                stakeholders_involved: Who participates (comma-separated)
                data_inputs: What data goes into this process
                data_outputs: What data comes out of this process
                pain_points: Current challenges with this process
                improvement_opportunities: How the data platform could help

            Returns:
                Confirmation with the process ID
            """
            import uuid

            process = {
                "name": process_name,
                "description": description,
                "stakeholders": [s.strip() for s in stakeholders_involved.split(",")],
                "data_inputs": data_inputs,
                "data_outputs": data_outputs,
                "pain_points": pain_points,
                "improvement_opportunities": improvement_opportunities,
            }

            namespace = ("engagements", engagement_id, "business_process")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": process,
                        "search_text": f"{process_name} {description} {pain_points} {improvement_opportunities}",
                    }
                )
                logger.info(f"Analyzed business process: {process_name}")
                return f"Documented business process: {process_name} (ID: {key})"
            except Exception as e:
                logger.error(f"Error documenting business process: {e}")
                return f"Error documenting business process: {str(e)}"

        @tool
        async def generate_discovery_summary() -> str:
            """
            Generate a summary of all discovery findings for this engagement.

            Use this to compile a comprehensive summary of stakeholders,
            data sources, requirements, and business processes discovered.

            Returns:
                Formatted summary of all discovery findings
            """
            summary_parts = []

            # Get stakeholders
            try:
                namespace = ("engagements", engagement_id, "stakeholder")
                stakeholders = await store.alist(namespace=namespace, limit=50)
                if stakeholders:
                    summary_parts.append("## Stakeholders Interviewed")
                    for item in stakeholders:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('name', 'Unknown')}** ({content.get('role', 'Unknown role')})"
                        )
                        summary_parts.append(f"  Priorities: {', '.join(content.get('priorities', []))}")
            except Exception as e:
                logger.warning(f"Error getting stakeholders: {e}")

            # Get data sources
            try:
                namespace = ("engagements", engagement_id, "data_source")
                sources = await store.alist(namespace=namespace, limit=50)
                if sources:
                    summary_parts.append("\n## Data Sources Discovered")
                    for item in sources:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('name', 'Unknown')}** ({content.get('type', 'Unknown type')})"
                        )
                        summary_parts.append(f"  Owner: {content.get('owner', 'Unknown')}")
            except Exception as e:
                logger.warning(f"Error getting data sources: {e}")

            # Get requirements
            try:
                namespace = ("engagements", engagement_id, "requirement")
                requirements = await store.alist(namespace=namespace, limit=50)
                if requirements:
                    summary_parts.append("\n## Requirements Documented")
                    # Sort by priority
                    priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
                    sorted_reqs = sorted(
                        requirements,
                        key=lambda x: priority_order.get(
                            x.value.get("content", {}).get("priority", "low"), 4
                        )
                    )
                    for item in sorted_reqs:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- [{content.get('priority', 'medium').upper()}] "
                            f"**{content.get('title', 'Untitled')}**"
                        )
            except Exception as e:
                logger.warning(f"Error getting requirements: {e}")

            # Get business processes
            try:
                namespace = ("engagements", engagement_id, "business_process")
                processes = await store.alist(namespace=namespace, limit=50)
                if processes:
                    summary_parts.append("\n## Business Processes Analyzed")
                    for item in processes:
                        content = item.value.get("content", {})
                        summary_parts.append(f"- **{content.get('name', 'Unknown')}**")
            except Exception as e:
                logger.warning(f"Error getting business processes: {e}")

            if not summary_parts:
                return "No discovery findings recorded yet for this engagement."

            return "\n".join(summary_parts)

        return [
            conduct_stakeholder_interview,
            catalog_data_source,
            document_requirement,
            analyze_business_process,
            generate_discovery_summary,
        ]

    def get_system_prompt(self) -> str:
        """Get the discovery agent system prompt."""
        return DISCOVERY_SYSTEM_PROMPT


# Factory function for easier instantiation
def create_discovery_react_agent(
    llm: BaseChatModel,
    checkpointer: PostgresSaver,
    store: PostgresStore,
    engagement_id: str,
    agent_id: str = "discovery_react",
) -> DiscoveryReActAgent:
    """
    Create a configured Discovery ReAct agent.

    Args:
        llm: The language model to use
        checkpointer: PostgresSaver for thread checkpoints
        store: PostgresStore for long-term memory
        engagement_id: The engagement this agent operates within
        agent_id: Optional custom agent ID

    Returns:
        Configured DiscoveryReActAgent instance
    """
    return DiscoveryReActAgent(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        engagement_id=engagement_id,
        agent_id=agent_id,
    )
