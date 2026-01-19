"""
Support Agent

Generates FAQ documents, troubleshooting guides, and knowledge base articles
from ontology definitions, system documentation, and common issues.
"""
from typing import Any, Dict, List, Optional, Type
from datetime import datetime
import json
import re

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from agent_framework.base_agent import BaseOpenForgeAgent, NodeBuilder
from agent_framework.state_management import (
    EnablementState,
    Decision,
    add_decision,
    mark_for_review,
)
from agent_framework.graph_builder import WorkflowBuilder
from agent_framework.prompts import PromptTemplate, PromptLibrary, build_context_string


# Support-specific prompt templates
SUPPORT_SYSTEM = PromptTemplate("""You are a Support Agent in the Open Forge platform.

Your role is to generate customer support materials from ontology definitions and system documentation.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Generate comprehensive FAQ documents
- Create troubleshooting guides for common issues
- Produce knowledge base articles for self-service support
- Design support workflows and escalation paths
- Analyze common issues and create resolution guides

Guidelines:
- Write in clear, user-friendly language
- Anticipate user questions and pain points
- Provide step-by-step resolution instructions
- Include visual descriptions and screenshots where helpful
- Categorize content for easy discovery
- Reference related documentation and training materials

Current context:
$context
""")

GENERATE_FAQ = PromptTemplate("""Generate a comprehensive FAQ document for the following system.

Ontology Schema:
$ontology_schema

System Features:
$system_features

Common User Tasks:
$common_tasks

Historical Issues (if available):
$historical_issues

Create an FAQ document organized by category:
1. Getting Started questions
2. Account and Access questions
3. Feature-specific questions
4. Data and Integration questions
5. Troubleshooting questions
6. Billing and Administration questions (if applicable)

For each FAQ entry, include:
- Clear question phrasing
- Concise, helpful answer
- Related links/references
- Tags for searchability

Output as a structured JSON object:
{
    "title": "Frequently Asked Questions",
    "description": "...",
    "categories": [
        {
            "category_id": "CAT1",
            "name": "...",
            "description": "...",
            "faqs": [
                {
                    "faq_id": "FAQ001",
                    "question": "...",
                    "answer": "...",
                    "related_links": [...],
                    "tags": [...],
                    "helpful_count": 0
                }
            ]
        }
    ],
    "generated_at": "...",
    "total_faqs": 0
}
""")

GENERATE_TROUBLESHOOTING = PromptTemplate("""Create troubleshooting guides for the following system.

Ontology Schema:
$ontology_schema

System Architecture:
$system_architecture

Known Issue Categories:
$issue_categories

Error Codes (if available):
$error_codes

Create troubleshooting guides that include:
1. Issue identification (symptoms, error messages)
2. Root cause analysis steps
3. Step-by-step resolution procedures
4. Prevention recommendations
5. When to escalate to support

Output as a structured JSON object:
{
    "title": "Troubleshooting Guide",
    "description": "...",
    "issue_categories": [
        {
            "category_id": "TS1",
            "name": "...",
            "description": "...",
            "issues": [
                {
                    "issue_id": "ISS001",
                    "title": "...",
                    "symptoms": [...],
                    "error_codes": [...],
                    "severity": "low|medium|high|critical",
                    "diagnosis_steps": [...],
                    "resolution_steps": [
                        {
                            "step_number": 1,
                            "action": "...",
                            "expected_result": "...",
                            "if_fails": "..."
                        }
                    ],
                    "prevention": [...],
                    "escalation_criteria": "...",
                    "estimated_resolution_time": "..."
                }
            ]
        }
    ],
    "escalation_paths": [...],
    "generated_at": "..."
}
""")

GENERATE_KB_ARTICLE = PromptTemplate("""Create a knowledge base article on the following topic.

Topic: $topic
Ontology Schema:
$ontology_schema

Related Entities:
$related_entities

Article Type: $article_type
Target Audience: $target_audience

Create a comprehensive knowledge base article that includes:
1. Clear title and summary
2. Problem or topic description
3. Detailed explanation or solution
4. Step-by-step instructions (if applicable)
5. Code examples or configurations
6. Related articles and resources
7. Feedback mechanism

Output as a structured JSON object:
{
    "article_id": "KB001",
    "title": "...",
    "summary": "...",
    "article_type": "how-to|concept|reference|troubleshooting",
    "target_audience": "...",
    "content": {
        "introduction": "...",
        "sections": [
            {
                "heading": "...",
                "content": "...",
                "code_examples": [...],
                "tips": [...]
            }
        ],
        "conclusion": "..."
    },
    "related_articles": [...],
    "tags": [...],
    "last_updated": "...",
    "helpful_votes": 0,
    "views": 0
}
""")

ANALYZE_SUPPORT_NEEDS = PromptTemplate("""Analyze the system to identify support content needs.

Ontology Schema:
$ontology_schema

System Features:
$system_features

User Personas:
$user_personas

Analyze and identify:
1. Most likely user questions
2. Potential pain points and confusion areas
3. Complex features requiring explanation
4. Common error scenarios
5. Integration and data challenges
6. Administrative tasks needing documentation

Output as JSON:
{
    "likely_questions": [...],
    "pain_points": [...],
    "complex_features": [...],
    "error_scenarios": [...],
    "integration_challenges": [...],
    "admin_tasks": [...],
    "recommended_articles": [...],
    "faq_priorities": [...]
}
""")

VALIDATE_SUPPORT_CONTENT = PromptTemplate("""Review the following support content for quality.

Content Type: $content_type
Support Content: $support_content

Evaluate:
1. Helpfulness - Does it solve user problems?
2. Clarity - Is it easy to understand?
3. Completeness - Are all scenarios covered?
4. Accuracy - Is the information correct?
5. Searchability - Can users find it easily?
6. Actionability - Can users follow the steps?

Output as JSON:
{
    "score": 0.0-1.0,
    "helpfulness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "issues": [...],
    "suggestions": [...],
    "requires_revision": true/false
}
""")


class SupportAgent(BaseOpenForgeAgent):
    """
    Agent for generating customer support materials.

    This agent:
    - Generates comprehensive FAQ documents
    - Creates troubleshooting guides for common issues
    - Produces knowledge base articles
    - Analyzes support needs from system documentation
    - Validates support content quality
    """

    def __init__(
        self,
        llm: BaseChatModel,
        memory: Optional[MemorySaver] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(llm, memory, config)
        self._register_prompts()

    def _register_prompts(self) -> None:
        """Register support-specific prompts with the library."""
        PromptLibrary.register("support_system", SUPPORT_SYSTEM)
        PromptLibrary.register("generate_faq", GENERATE_FAQ)
        PromptLibrary.register("generate_troubleshooting", GENERATE_TROUBLESHOOTING)
        PromptLibrary.register("generate_kb_article", GENERATE_KB_ARTICLE)
        PromptLibrary.register("analyze_support_needs", ANALYZE_SUPPORT_NEEDS)
        PromptLibrary.register("validate_support_content", VALIDATE_SUPPORT_CONTENT)

    @property
    def name(self) -> str:
        return "support_agent"

    @property
    def description(self) -> str:
        return (
            "Generates FAQ documents, troubleshooting guides, and knowledge base articles "
            "from ontology definitions and system documentation."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "faq_documents",
            "troubleshooting_guides",
            "knowledge_base_articles",
            "support_quality_report"
        ]

    @property
    def state_class(self) -> Type[EnablementState]:
        return EnablementState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return SUPPORT_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for support content generation."""
        builder = WorkflowBuilder(EnablementState)

        async def analyze_support_needs(state: EnablementState) -> Dict[str, Any]:
            """Analyze system to identify support content needs."""
            context = state.get("agent_context", {})

            prompt = PromptLibrary.format(
                "analyze_support_needs",
                ontology_schema=context.get("ontology_schema", ""),
                system_features=json.dumps(context.get("system_features", [])),
                user_personas=json.dumps(context.get("user_personas", [
                    {"name": "End User", "technical_level": "low"},
                    {"name": "Power User", "technical_level": "medium"},
                    {"name": "Administrator", "technical_level": "high"}
                ]))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                analysis = json.loads(response.content)
            except json.JSONDecodeError:
                analysis = self._extract_json_from_response(response.content)

            decision = add_decision(
                state,
                decision_type="support_needs_analysis",
                description=f"Identified {len(analysis.get('likely_questions', []))} likely user questions",
                confidence=0.85 if analysis.get('likely_questions') else 0.4,
                reasoning="Analyzed system to anticipate user support needs"
            )

            return {
                "outputs": {"support_analysis": analysis},
                "decisions": [decision],
                "current_step": "needs_analyzed"
            }

        async def generate_faq_documents(state: EnablementState) -> Dict[str, Any]:
            """Generate comprehensive FAQ documents."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            analysis = outputs.get("support_analysis", {})

            prompt = PromptLibrary.format(
                "generate_faq",
                ontology_schema=context.get("ontology_schema", ""),
                system_features=json.dumps(context.get("system_features", [])),
                common_tasks=json.dumps(context.get("common_tasks", [])),
                historical_issues=json.dumps(context.get("historical_issues", []))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                faq_doc = json.loads(response.content)
            except json.JSONDecodeError:
                faq_doc = self._extract_json_from_response(response.content)

            faq_doc["generated_at"] = datetime.utcnow().isoformat()

            # Enhance with analysis insights
            if analysis.get("faq_priorities"):
                faq_doc["priority_topics"] = analysis["faq_priorities"]

            faq_documents = [faq_doc]

            decision = add_decision(
                state,
                decision_type="faq_generation",
                description=f"Generated FAQ document with {faq_doc.get('total_faqs', 0)} entries",
                confidence=0.8 if faq_doc.get("categories") else 0.5,
                reasoning="Created comprehensive FAQ from system analysis"
            )

            return {
                "outputs": {"faq_documents": faq_documents},
                "faq_documents": faq_documents,
                "decisions": [decision],
                "current_step": "faq_generated"
            }

        async def generate_troubleshooting_guides(state: EnablementState) -> Dict[str, Any]:
            """Generate troubleshooting guides for common issues."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            analysis = outputs.get("support_analysis", {})

            # Define issue categories from analysis or defaults
            issue_categories = analysis.get("error_scenarios", context.get("issue_categories", [
                "Authentication and Access",
                "Data Operations",
                "API and Integration",
                "Performance",
                "Configuration"
            ]))

            prompt = PromptLibrary.format(
                "generate_troubleshooting",
                ontology_schema=context.get("ontology_schema", ""),
                system_architecture=json.dumps(context.get("system_architecture", {})),
                issue_categories=json.dumps(issue_categories),
                error_codes=json.dumps(context.get("error_codes", []))
            )

            messages = [
                SystemMessage(content=self.get_system_prompt()),
                HumanMessage(content=prompt)
            ]

            response = await self.llm.ainvoke(messages)

            try:
                troubleshooting_guide = json.loads(response.content)
            except json.JSONDecodeError:
                troubleshooting_guide = self._extract_json_from_response(response.content)

            troubleshooting_guide["generated_at"] = datetime.utcnow().isoformat()
            troubleshooting_guides = [troubleshooting_guide]

            decision = add_decision(
                state,
                decision_type="troubleshooting_generation",
                description=f"Generated troubleshooting guide with {len(troubleshooting_guide.get('issue_categories', []))} categories",
                confidence=0.75 if troubleshooting_guide.get("issue_categories") else 0.4,
                reasoning="Created issue resolution guides from system analysis"
            )

            return {
                "outputs": {"troubleshooting_guides": troubleshooting_guides},
                "troubleshooting_guides": troubleshooting_guides,
                "decisions": [decision],
                "current_step": "troubleshooting_generated"
            }

        async def generate_knowledge_base(state: EnablementState) -> Dict[str, Any]:
            """Generate knowledge base articles."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            analysis = outputs.get("support_analysis", {})

            # Determine KB articles to generate
            recommended_articles = analysis.get("recommended_articles", context.get("kb_topics", [
                {"topic": "System Overview", "type": "concept", "audience": "all"},
                {"topic": "API Authentication", "type": "how-to", "audience": "developers"},
                {"topic": "Data Import/Export", "type": "how-to", "audience": "all"},
                {"topic": "User Management", "type": "how-to", "audience": "administrators"},
                {"topic": "Best Practices", "type": "reference", "audience": "all"}
            ]))

            knowledge_base_articles = []

            for article_spec in recommended_articles:
                if isinstance(article_spec, str):
                    article_spec = {"topic": article_spec, "type": "how-to", "audience": "all"}

                prompt = PromptLibrary.format(
                    "generate_kb_article",
                    topic=article_spec.get("topic", "General"),
                    ontology_schema=context.get("ontology_schema", ""),
                    related_entities=json.dumps(article_spec.get("entities", [])),
                    article_type=article_spec.get("type", "how-to"),
                    target_audience=article_spec.get("audience", "all")
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    article = json.loads(response.content)
                except json.JSONDecodeError:
                    article = self._extract_json_from_response(response.content)

                article["generated_at"] = datetime.utcnow().isoformat()
                article["source_topic"] = article_spec.get("topic", "Unknown")
                knowledge_base_articles.append(article)

            decision = add_decision(
                state,
                decision_type="kb_generation",
                description=f"Generated {len(knowledge_base_articles)} knowledge base articles",
                confidence=0.8 if knowledge_base_articles else 0.5,
                reasoning="Created self-service support documentation"
            )

            return {
                "outputs": {"knowledge_base_articles": knowledge_base_articles},
                "knowledge_base_articles": knowledge_base_articles,
                "decisions": [decision],
                "current_step": "kb_generated"
            }

        async def validate_support_content(state: EnablementState) -> Dict[str, Any]:
            """Validate all generated support content for quality."""
            outputs = state.get("outputs", {})

            quality_reports = []
            requires_revision = False

            # Validate FAQ documents
            for faq_doc in outputs.get("faq_documents", []):
                validation = await self._validate_single_content(
                    "FAQ Document",
                    faq_doc
                )
                quality_reports.append(validation)
                if validation.get("requires_revision"):
                    requires_revision = True

            # Validate troubleshooting guides
            for ts_guide in outputs.get("troubleshooting_guides", []):
                validation = await self._validate_single_content(
                    "Troubleshooting Guide",
                    ts_guide
                )
                quality_reports.append(validation)
                if validation.get("requires_revision"):
                    requires_revision = True

            # Validate KB articles
            for article in outputs.get("knowledge_base_articles", []):
                validation = await self._validate_single_content(
                    f"KB Article - {article.get('title', 'Unknown')}",
                    article
                )
                quality_reports.append(validation)
                if validation.get("requires_revision"):
                    requires_revision = True

            # Calculate overall quality score
            if quality_reports:
                avg_score = sum(r.get("score", 0) for r in quality_reports) / len(quality_reports)
            else:
                avg_score = 0.0

            quality_report = {
                "overall_score": avg_score,
                "content_reports": quality_reports,
                "requires_revision": requires_revision,
                "generated_at": datetime.utcnow().isoformat()
            }

            review_items = []
            if requires_revision:
                for report in quality_reports:
                    if report.get("requires_revision"):
                        review_items.append(
                            mark_for_review(
                                state,
                                item_type="support_quality",
                                item_id=f"support_review_{report.get('content_type', 'unknown')}",
                                description=f"Support content requires revision: {', '.join(report.get('issues', []))}",
                                priority="medium"
                            )
                        )

            decision = add_decision(
                state,
                decision_type="support_validation",
                description=f"Validated support content quality: {avg_score:.2f} overall score",
                confidence=avg_score,
                reasoning="Assessed helpfulness, clarity, and completeness of support materials",
                requires_approval=requires_revision
            )

            return {
                "outputs": {"support_quality_report": quality_report},
                "decisions": [decision],
                "requires_human_review": requires_revision,
                "review_items": review_items,
                "current_step": "validation_complete"
            }

        async def compile_support_package(state: EnablementState) -> Dict[str, Any]:
            """Compile all support content into a final package."""
            outputs = state.get("outputs", {})
            decisions = state.get("decisions", [])

            # Calculate overall confidence
            avg_confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.5
            )

            support_package = {
                "faq_documents": outputs.get("faq_documents", []),
                "troubleshooting_guides": outputs.get("troubleshooting_guides", []),
                "knowledge_base_articles": outputs.get("knowledge_base_articles", []),
                "quality_report": outputs.get("support_quality_report", {}),
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "confidence_score": avg_confidence,
                    "total_items": (
                        len(outputs.get("faq_documents", [])) +
                        len(outputs.get("troubleshooting_guides", [])) +
                        len(outputs.get("knowledge_base_articles", []))
                    ),
                    "total_faq_entries": sum(
                        doc.get("total_faqs", 0)
                        for doc in outputs.get("faq_documents", [])
                    )
                }
            }

            decision = add_decision(
                state,
                decision_type="support_compilation",
                description="Compiled complete support package",
                confidence=avg_confidence,
                reasoning="Aggregated all support content outputs"
            )

            return {
                "outputs": {"support_package": support_package},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_validation(state: EnablementState) -> str:
            """Route based on validation results."""
            if state.get("requires_human_review"):
                return "await_review"
            return "compile"

        async def await_human_review(state: EnablementState) -> Dict[str, Any]:
            """Wait for human review of support content."""
            return {
                "current_step": "awaiting_human_review"
            }

        # Build the workflow
        graph = (builder
            .add_node("analyze_needs", analyze_support_needs)
            .add_node("generate_faq", generate_faq_documents)
            .add_node("generate_troubleshooting", generate_troubleshooting_guides)
            .add_node("generate_kb", generate_knowledge_base)
            .add_node("validate", validate_support_content)
            .add_node("await_review", await_human_review)
            .add_node("compile", compile_support_package)
            .set_entry("analyze_needs")
            .add_edge("analyze_needs", "generate_faq")
            .add_edge("generate_faq", "generate_troubleshooting")
            .add_edge("generate_troubleshooting", "generate_kb")
            .add_edge("generate_kb", "validate")
            .add_conditional("validate", route_after_validation, {
                "await_review": "await_review",
                "compile": "compile"
            })
            .add_edge("await_review", "END")
            .add_edge("compile", "END")
            .build())

        return graph

    async def _validate_single_content(
        self,
        content_type: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single support content item."""
        prompt = PromptLibrary.format(
            "validate_support_content",
            content_type=content_type,
            support_content=json.dumps(content, default=str)[:4000]
        )

        messages = [
            SystemMessage(content=self.get_system_prompt()),
            HumanMessage(content=prompt)
        ]

        response = await self.llm.ainvoke(messages)

        try:
            validation = json.loads(response.content)
        except json.JSONDecodeError:
            validation = self._extract_json_from_response(response.content)

        validation["content_type"] = content_type
        return validation

    def get_tools(self) -> List[Any]:
        """Return list of tools this agent uses."""
        return []

    def _extract_json_from_response(self, response: str) -> Any:
        """Extract JSON from an LLM response that may contain other text."""
        # Look for JSON array
        array_match = re.search(r'\[[\s\S]*\]', response)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass

        # Look for JSON object
        object_match = re.search(r'\{[\s\S]*\}', response)
        if object_match:
            try:
                return json.loads(object_match.group())
            except json.JSONDecodeError:
                pass

        # Return empty structure if no valid JSON found
        return {}
