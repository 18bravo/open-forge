"""
Enablement ReAct Agent using LangGraph's create_react_agent pattern.

This agent handles documentation, training materials, and support content
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


# Enablement system prompt
ENABLEMENT_SYSTEM_PROMPT = """You are the Enablement Agent for Open Forge, an enterprise data platform.

## Your Role
You create comprehensive documentation, training materials, and support content
that enables users to successfully adopt and use the data platform.

## Capabilities
1. **Documentation**: Generate API documentation, user guides, and operational
   runbooks that help users understand and use the system.

2. **Training Materials**: Create training curricula, tutorials, and quickstart
   guides for different skill levels and roles.

3. **Support Content**: Develop FAQs, troubleshooting guides, and knowledge base
   articles that help users solve common problems.

## Output Formats
- API docs should follow OpenAPI/Swagger conventions where applicable
- User guides should be structured markdown with clear navigation
- Training materials should include objectives, prerequisites, and exercises
- FAQs should be organized by topic with clear questions and answers

## Best Practices
- Write for your audience - adjust technical depth accordingly
- Include practical examples and use cases
- Keep content up to date with system changes
- Cross-reference related documentation
- Include visual aids where helpful (describe diagrams)

## Content Guidelines
- Use clear, concise language
- Follow a consistent style and formatting
- Include code samples where appropriate
- Provide step-by-step instructions for procedures
- Test all documented procedures before publishing
"""


@register_agent(
    name="enablement_react",
    category=AgentCategory.ENABLEMENT,
    description="Enablement agent using ReAct pattern for documentation, "
                "training materials, and support content generation",
    version="1.0.0",
    required_inputs=["engagement_id"],
    output_keys=["documentation", "training_materials", "support_content"],
    capabilities=["api_documentation", "user_guides", "training_curricula", "faq_generation"],
    dependencies=["app_builder_react"],
    is_react_agent=True,
    is_memory_aware=True,
)
class EnablementReActAgent(MemoryAwareAgent):
    """
    Enablement agent using LangGraph's ReAct pattern with memory capabilities.

    This agent combines:
    - ReAct pattern for systematic content creation
    - Memory tools for persisting documentation artifacts
    - Specialized tools for documentation, training, and support

    Example:
        agent = EnablementReActAgent(
            llm=ChatAnthropic(model="claude-sonnet-4-20250514"),
            checkpointer=PostgresSaver.from_conn_string(conn_str),
            store=PostgresStore.from_conn_string(conn_str),
            engagement_id="eng_123",
            agent_id="enablement_1"
        )

        result = await agent.run(
            "Create API documentation for the Customer entity endpoints",
            thread_id="create_api_docs_1"
        )
    """

    def get_tools(self) -> List[BaseTool]:
        """
        Get enablement-specific tools.

        Returns:
            List of tools for documentation, training, and support content
        """
        engagement_id = self.engagement_id
        store = self.store

        @tool
        async def create_api_documentation(
            endpoint_path: str,
            http_method: str,
            description: str,
            request_body: str = "",
            response_schema: str = "",
            path_parameters: str = "",
            query_parameters: str = "",
            auth_required: bool = True,
            example_request: str = "",
            example_response: str = "",
        ) -> str:
            """
            Create API documentation for an endpoint.

            Use this to document REST API endpoints with full request/response details.

            Args:
                endpoint_path: The API endpoint path (e.g., "/api/v1/customers")
                http_method: HTTP method (GET, POST, PUT, DELETE, PATCH)
                description: What this endpoint does
                request_body: JSON schema of request body (for POST/PUT/PATCH)
                response_schema: JSON schema of response
                path_parameters: JSON array of path parameters
                    e.g., '[{"name": "id", "type": "string", "description": "Customer ID"}]'
                query_parameters: JSON array of query parameters
                auth_required: Whether authentication is required
                example_request: Example request body (JSON)
                example_response: Example response body (JSON)

            Returns:
                Generated API documentation
            """
            import uuid

            try:
                path_params = json.loads(path_parameters) if path_parameters else []
                query_params = json.loads(query_parameters) if query_parameters else []
                req_schema = json.loads(request_body) if request_body else None
                resp_schema = json.loads(response_schema) if response_schema else None
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            api_doc = {
                "path": endpoint_path,
                "method": http_method.upper(),
                "description": description,
                "auth_required": auth_required,
                "path_parameters": path_params,
                "query_parameters": query_params,
                "request_body": req_schema,
                "response_schema": resp_schema,
                "examples": {
                    "request": example_request,
                    "response": example_response,
                },
            }

            # Generate markdown documentation
            doc_md = f"""## {http_method.upper()} {endpoint_path}

{description}

### Authentication

{"**Required** - Include bearer token in Authorization header" if auth_required else "Not required"}

"""
            if path_params:
                doc_md += "### Path Parameters\n\n"
                doc_md += "| Name | Type | Description |\n"
                doc_md += "|------|------|-------------|\n"
                for param in path_params:
                    doc_md += f"| {param.get('name')} | {param.get('type')} | {param.get('description', '')} |\n"
                doc_md += "\n"

            if query_params:
                doc_md += "### Query Parameters\n\n"
                doc_md += "| Name | Type | Required | Description |\n"
                doc_md += "|------|------|----------|-------------|\n"
                for param in query_params:
                    doc_md += f"| {param.get('name')} | {param.get('type')} | {param.get('required', False)} | {param.get('description', '')} |\n"
                doc_md += "\n"

            if req_schema:
                doc_md += "### Request Body\n\n"
                doc_md += f"```json\n{json.dumps(req_schema, indent=2)}\n```\n\n"

            if resp_schema:
                doc_md += "### Response\n\n"
                doc_md += f"```json\n{json.dumps(resp_schema, indent=2)}\n```\n\n"

            if example_request or example_response:
                doc_md += "### Example\n\n"
                if example_request:
                    doc_md += "**Request:**\n```json\n" + example_request + "\n```\n\n"
                if example_response:
                    doc_md += "**Response:**\n```json\n" + example_response + "\n```\n\n"

            api_doc["markdown"] = doc_md

            namespace = ("engagements", engagement_id, "api_documentation")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": api_doc,
                        "search_text": f"api {http_method} {endpoint_path} {description}",
                    }
                )
                logger.info(f"Created API documentation: {http_method} {endpoint_path}")
                return f"Created API documentation: {http_method.upper()} {endpoint_path} (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing API doc: {e}")
                return f"Error storing API doc: {str(e)}"

        @tool
        async def create_user_guide(
            guide_title: str,
            target_audience: str,
            sections: str,
            prerequisites: str = "",
            related_guides: str = "",
        ) -> str:
            """
            Create a user guide document.

            Use this to create comprehensive user guides for specific features or workflows.

            Args:
                guide_title: Title of the guide
                target_audience: Who this guide is for (e.g., "Data Engineers", "Business Analysts")
                sections: JSON array of guide sections
                    e.g., '[{"title": "Getting Started", "content": "..."}, {"title": "Configuration", "content": "..."}]'
                prerequisites: What users need before following this guide
                related_guides: Comma-separated list of related guide titles

            Returns:
                Generated user guide
            """
            import uuid

            try:
                section_list = json.loads(sections) if isinstance(sections, str) else sections
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in sections: {e}"

            guide = {
                "title": guide_title,
                "target_audience": target_audience,
                "sections": section_list,
                "prerequisites": prerequisites,
                "related_guides": [g.strip() for g in related_guides.split(",") if g.strip()],
            }

            # Generate markdown guide
            guide_md = f"""# {guide_title}

**Target Audience:** {target_audience}

"""
            if prerequisites:
                guide_md += f"""## Prerequisites

{prerequisites}

"""

            guide_md += "## Table of Contents\n\n"
            for i, section in enumerate(section_list, 1):
                title = section.get("title", f"Section {i}")
                anchor = title.lower().replace(" ", "-")
                guide_md += f"{i}. [{title}](#{anchor})\n"
            guide_md += "\n---\n\n"

            for section in section_list:
                title = section.get("title", "Untitled Section")
                content = section.get("content", "")
                guide_md += f"## {title}\n\n{content}\n\n"

            if guide.get("related_guides"):
                guide_md += "## Related Guides\n\n"
                for related in guide["related_guides"]:
                    guide_md += f"- {related}\n"

            guide["markdown"] = guide_md

            namespace = ("engagements", engagement_id, "user_guide")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": guide,
                        "search_text": f"guide {guide_title} {target_audience}",
                    }
                )
                logger.info(f"Created user guide: {guide_title}")
                return f"Created user guide: {guide_title} with {len(section_list)} sections (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing user guide: {e}")
                return f"Error storing user guide: {str(e)}"

        @tool
        async def create_tutorial(
            tutorial_title: str,
            skill_level: str,
            estimated_time: str,
            learning_objectives: str,
            steps: str,
            exercises: str = "",
            quiz_questions: str = "",
        ) -> str:
            """
            Create a hands-on tutorial.

            Use this to create step-by-step tutorials that teach specific skills.

            Args:
                tutorial_title: Title of the tutorial
                skill_level: Required skill level (beginner, intermediate, advanced)
                estimated_time: Estimated completion time (e.g., "30 minutes")
                learning_objectives: JSON array of learning objectives
                steps: JSON array of tutorial steps
                    e.g., '[{"title": "Step 1", "content": "...", "code": "..."}]'
                exercises: Optional JSON array of practice exercises
                quiz_questions: Optional JSON array of quiz questions

            Returns:
                Generated tutorial
            """
            import uuid

            try:
                objectives = json.loads(learning_objectives) if isinstance(learning_objectives, str) else learning_objectives
                step_list = json.loads(steps) if isinstance(steps, str) else steps
                exercise_list = json.loads(exercises) if exercises else []
                quiz_list = json.loads(quiz_questions) if quiz_questions else []
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            tutorial = {
                "title": tutorial_title,
                "skill_level": skill_level,
                "estimated_time": estimated_time,
                "objectives": objectives,
                "steps": step_list,
                "exercises": exercise_list,
                "quiz": quiz_list,
            }

            # Generate markdown tutorial
            tutorial_md = f"""# {tutorial_title}

**Skill Level:** {skill_level}
**Estimated Time:** {estimated_time}

## Learning Objectives

By the end of this tutorial, you will be able to:

{chr(10).join(f"- {obj}" for obj in objectives)}

---

"""
            for i, step in enumerate(step_list, 1):
                title = step.get("title", f"Step {i}")
                content = step.get("content", "")
                code = step.get("code", "")

                tutorial_md += f"## Step {i}: {title}\n\n{content}\n\n"
                if code:
                    lang = step.get("language", "")
                    tutorial_md += f"```{lang}\n{code}\n```\n\n"

            if exercise_list:
                tutorial_md += "## Practice Exercises\n\n"
                for i, exercise in enumerate(exercise_list, 1):
                    tutorial_md += f"### Exercise {i}: {exercise.get('title', '')}\n\n"
                    tutorial_md += f"{exercise.get('description', '')}\n\n"

            if quiz_list:
                tutorial_md += "## Knowledge Check\n\n"
                for i, q in enumerate(quiz_list, 1):
                    tutorial_md += f"{i}. {q.get('question', '')}\n"

            tutorial["markdown"] = tutorial_md

            namespace = ("engagements", engagement_id, "tutorial")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": tutorial,
                        "search_text": f"tutorial {tutorial_title} {skill_level}",
                    }
                )
                logger.info(f"Created tutorial: {tutorial_title}")
                return f"Created tutorial: {tutorial_title} ({skill_level}, {estimated_time}) (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing tutorial: {e}")
                return f"Error storing tutorial: {str(e)}"

        @tool
        async def create_faq_document(
            topic: str,
            questions_and_answers: str,
        ) -> str:
            """
            Create a FAQ document for a topic.

            Use this to document frequently asked questions and their answers.

            Args:
                topic: The topic this FAQ covers
                questions_and_answers: JSON array of Q&A pairs
                    e.g., '[{"question": "How do I...", "answer": "You can..."}]'

            Returns:
                Generated FAQ document
            """
            import uuid

            try:
                qa_list = json.loads(questions_and_answers) if isinstance(questions_and_answers, str) else questions_and_answers
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in questions_and_answers: {e}"

            faq = {
                "topic": topic,
                "questions": qa_list,
            }

            # Generate markdown FAQ
            faq_md = f"""# Frequently Asked Questions: {topic}

"""
            for i, qa in enumerate(qa_list, 1):
                question = qa.get("question", "")
                answer = qa.get("answer", "")
                faq_md += f"## {i}. {question}\n\n{answer}\n\n---\n\n"

            faq["markdown"] = faq_md

            namespace = ("engagements", engagement_id, "faq")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": faq,
                        "search_text": f"faq {topic} " + " ".join(qa.get("question", "") for qa in qa_list[:5]),
                    }
                )
                logger.info(f"Created FAQ document: {topic}")
                return f"Created FAQ document: {topic} with {len(qa_list)} questions (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing FAQ: {e}")
                return f"Error storing FAQ: {str(e)}"

        @tool
        async def create_troubleshooting_guide(
            issue_title: str,
            symptoms: str,
            possible_causes: str,
            diagnostic_steps: str,
            resolution_steps: str,
            prevention_tips: str = "",
        ) -> str:
            """
            Create a troubleshooting guide for a specific issue.

            Use this to document how to diagnose and resolve common problems.

            Args:
                issue_title: Title describing the issue
                symptoms: JSON array of symptoms users might see
                possible_causes: JSON array of possible causes
                diagnostic_steps: JSON array of diagnostic steps
                resolution_steps: JSON array of resolution steps
                prevention_tips: Optional tips to prevent this issue

            Returns:
                Generated troubleshooting guide
            """
            import uuid

            try:
                symptom_list = json.loads(symptoms) if isinstance(symptoms, str) else symptoms
                cause_list = json.loads(possible_causes) if isinstance(possible_causes, str) else possible_causes
                diag_list = json.loads(diagnostic_steps) if isinstance(diagnostic_steps, str) else diagnostic_steps
                res_list = json.loads(resolution_steps) if isinstance(resolution_steps, str) else resolution_steps
            except json.JSONDecodeError as e:
                return f"Error: invalid JSON in parameters: {e}"

            guide = {
                "title": issue_title,
                "symptoms": symptom_list,
                "causes": cause_list,
                "diagnostics": diag_list,
                "resolution": res_list,
                "prevention": prevention_tips,
            }

            # Generate markdown guide
            guide_md = f"""# Troubleshooting: {issue_title}

## Symptoms

{chr(10).join(f"- {s}" for s in symptom_list)}

## Possible Causes

{chr(10).join(f"- {c}" for c in cause_list)}

## Diagnostic Steps

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(diag_list))}

## Resolution Steps

{chr(10).join(f"{i+1}. {step}" for i, step in enumerate(res_list))}

"""
            if prevention_tips:
                guide_md += f"## Prevention\n\n{prevention_tips}\n"

            guide["markdown"] = guide_md

            namespace = ("engagements", engagement_id, "troubleshooting")
            key = str(uuid.uuid4())

            try:
                await store.aput(
                    namespace,
                    key,
                    {
                        "content": guide,
                        "search_text": f"troubleshooting {issue_title} " + " ".join(symptom_list[:3]),
                    }
                )
                logger.info(f"Created troubleshooting guide: {issue_title}")
                return f"Created troubleshooting guide: {issue_title} (ID: {key})"
            except Exception as e:
                logger.error(f"Error storing troubleshooting guide: {e}")
                return f"Error storing troubleshooting guide: {str(e)}"

        @tool
        async def generate_enablement_summary() -> str:
            """
            Generate a summary of all enablement content.

            Use this to compile a comprehensive summary of documentation,
            training materials, and support content.

            Returns:
                Complete enablement content summary
            """
            summary_parts = ["# Enablement Content Summary\n"]

            # Get API documentation
            try:
                namespace = ("engagements", engagement_id, "api_documentation")
                api_docs = await store.alist(namespace=namespace, limit=50)
                if api_docs:
                    summary_parts.append("## API Documentation")
                    for item in api_docs:
                        content = item.value.get("content", {})
                        summary_parts.append(f"- **{content.get('method')} {content.get('path')}**")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting API docs: {e}")

            # Get user guides
            try:
                namespace = ("engagements", engagement_id, "user_guide")
                guides = await store.alist(namespace=namespace, limit=50)
                if guides:
                    summary_parts.append("## User Guides")
                    for item in guides:
                        content = item.value.get("content", {})
                        summary_parts.append(f"- **{content.get('title')}** (Audience: {content.get('target_audience')})")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting user guides: {e}")

            # Get tutorials
            try:
                namespace = ("engagements", engagement_id, "tutorial")
                tutorials = await store.alist(namespace=namespace, limit=50)
                if tutorials:
                    summary_parts.append("## Tutorials")
                    for item in tutorials:
                        content = item.value.get("content", {})
                        summary_parts.append(
                            f"- **{content.get('title')}** ({content.get('skill_level')}, {content.get('estimated_time')})"
                        )
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting tutorials: {e}")

            # Get FAQs
            try:
                namespace = ("engagements", engagement_id, "faq")
                faqs = await store.alist(namespace=namespace, limit=50)
                if faqs:
                    summary_parts.append("## FAQ Documents")
                    for item in faqs:
                        content = item.value.get("content", {})
                        q_count = len(content.get("questions", []))
                        summary_parts.append(f"- **{content.get('topic')}** ({q_count} questions)")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting FAQs: {e}")

            # Get troubleshooting guides
            try:
                namespace = ("engagements", engagement_id, "troubleshooting")
                troubleshooting = await store.alist(namespace=namespace, limit=50)
                if troubleshooting:
                    summary_parts.append("## Troubleshooting Guides")
                    for item in troubleshooting:
                        content = item.value.get("content", {})
                        summary_parts.append(f"- **{content.get('title')}**")
                    summary_parts.append("")
            except Exception as e:
                logger.warning(f"Error getting troubleshooting guides: {e}")

            if len(summary_parts) == 1:
                return "No enablement content created yet."

            return "\n".join(summary_parts)

        return [
            create_api_documentation,
            create_user_guide,
            create_tutorial,
            create_faq_document,
            create_troubleshooting_guide,
            generate_enablement_summary,
        ]

    def get_system_prompt(self) -> str:
        """Get the enablement agent system prompt."""
        return ENABLEMENT_SYSTEM_PROMPT


# Factory function for easier instantiation
def create_enablement_react_agent(
    llm: BaseChatModel,
    checkpointer: PostgresSaver,
    store: PostgresStore,
    engagement_id: str,
    agent_id: str = "enablement_react",
) -> EnablementReActAgent:
    """
    Create a configured Enablement ReAct agent.

    Args:
        llm: The language model to use
        checkpointer: PostgresSaver for thread checkpoints
        store: PostgresStore for long-term memory
        engagement_id: The engagement this agent operates within
        agent_id: Optional custom agent ID

    Returns:
        Configured EnablementReActAgent instance
    """
    return EnablementReActAgent(
        llm=llm,
        checkpointer=checkpointer,
        store=store,
        engagement_id=engagement_id,
        agent_id=agent_id,
    )
