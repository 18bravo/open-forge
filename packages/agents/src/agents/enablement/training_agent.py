"""
Training Agent

Generates training materials, tutorials, and quickstart guides
from ontology definitions and system documentation.
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


# Training-specific prompt templates
TRAINING_SYSTEM = PromptTemplate("""You are a Training Agent in the Open Forge platform.

Your role is to generate comprehensive training materials from ontology definitions and system documentation.

Engagement ID: $engagement_id
Phase: $phase

Your capabilities:
- Generate structured training curricula for different skill levels
- Create step-by-step tutorials with practical exercises
- Produce quickstart guides for rapid onboarding
- Design certification paths and assessments
- Create hands-on labs and exercises

Guidelines:
- Structure content for progressive learning (beginner to advanced)
- Include practical examples and real-world scenarios
- Provide clear learning objectives for each module
- Include knowledge checks and assessments
- Ensure accessibility and clarity for all audiences
- Reference related documentation where appropriate

Current context:
$context
""")

GENERATE_CURRICULUM = PromptTemplate("""Design a comprehensive training curriculum for the following system.

Ontology Schema:
$ontology_schema

System Features:
$system_features

API Documentation Summary:
$api_documentation

Target Audience: $target_audience
Skill Level: $skill_level

Create a training curriculum that includes:
1. Course overview and learning objectives
2. Prerequisites and recommended background
3. Module breakdown with topics and duration estimates
4. Hands-on exercises for each module
5. Assessment criteria and knowledge checks
6. Recommended learning path
7. Resources and reference materials

Output as a structured JSON object:
{
    "title": "Course Title",
    "description": "...",
    "target_audience": "...",
    "skill_level": "...",
    "total_duration_hours": 0,
    "prerequisites": [...],
    "learning_objectives": [...],
    "modules": [
        {
            "module_id": "M1",
            "title": "...",
            "duration_minutes": 0,
            "objectives": [...],
            "topics": [...],
            "exercises": [...],
            "assessment": {...}
        }
    ],
    "certification_path": {...},
    "resources": [...]
}
""")

GENERATE_TUTORIAL = PromptTemplate("""Create a detailed step-by-step tutorial.

Topic: $topic
Ontology Schema:
$ontology_schema

Related Entities:
$related_entities

Prerequisites: $prerequisites
Expected Duration: $duration

Create a comprehensive tutorial that includes:
1. Introduction and learning goals
2. Prerequisites and environment setup
3. Step-by-step instructions with code examples
4. Screenshots/diagrams descriptions
5. Common pitfalls and troubleshooting
6. Practice exercises
7. Next steps and further learning

Output as a structured JSON object:
{
    "title": "Tutorial Title",
    "description": "...",
    "difficulty": "beginner|intermediate|advanced",
    "duration_minutes": 0,
    "prerequisites": [...],
    "learning_goals": [...],
    "steps": [
        {
            "step_number": 1,
            "title": "...",
            "description": "...",
            "code_example": "...",
            "expected_output": "...",
            "tips": [...]
        }
    ],
    "exercises": [...],
    "troubleshooting": [...],
    "next_steps": [...]
}
""")

GENERATE_QUICKSTART = PromptTemplate("""Create a quickstart guide for rapid onboarding.

System Overview:
$system_overview

Ontology Schema:
$ontology_schema

Key Features:
$key_features

Target Completion Time: $target_time

Create a quickstart guide that:
1. Gets users up and running in minimal time
2. Covers essential operations only
3. Provides copy-paste code examples
4. Links to detailed documentation
5. Includes common first-day tasks

Output as a structured JSON object:
{
    "title": "Quickstart Guide",
    "description": "...",
    "target_time_minutes": 0,
    "sections": [
        {
            "section_id": "QS1",
            "title": "...",
            "time_minutes": 0,
            "steps": [
                {
                    "action": "...",
                    "code": "...",
                    "expected_result": "..."
                }
            ]
        }
    ],
    "common_tasks": [...],
    "next_steps": [...],
    "troubleshooting": [...]
}
""")

GENERATE_ASSESSMENT = PromptTemplate("""Create assessment questions and exercises.

Training Module:
$training_module

Ontology Schema:
$ontology_schema

Learning Objectives:
$learning_objectives

Assessment Type: $assessment_type

Create an assessment that includes:
1. Multiple choice questions
2. Short answer questions
3. Practical exercises
4. Scenario-based challenges
5. Grading criteria

Output as a structured JSON object:
{
    "assessment_id": "...",
    "title": "...",
    "type": "quiz|practical|mixed",
    "passing_score": 0.0,
    "time_limit_minutes": 0,
    "questions": [
        {
            "question_id": "Q1",
            "type": "multiple_choice|short_answer|practical",
            "question": "...",
            "options": [...],
            "correct_answer": "...",
            "explanation": "...",
            "points": 0
        }
    ],
    "practical_exercises": [...],
    "grading_rubric": {...}
}
""")

VALIDATE_TRAINING = PromptTemplate("""Review the following training material for quality and effectiveness.

Training Type: $training_type
Training Content: $training_content

Evaluate:
1. Completeness - Are all necessary topics covered?
2. Clarity - Is the content clear and understandable?
3. Progression - Does it build skills logically?
4. Practicality - Are there sufficient hands-on elements?
5. Assessments - Are knowledge checks appropriate?
6. Accessibility - Is it suitable for the target audience?

Output as JSON:
{
    "score": 0.0-1.0,
    "completeness_score": 0.0-1.0,
    "clarity_score": 0.0-1.0,
    "practicality_score": 0.0-1.0,
    "issues": [...],
    "suggestions": [...],
    "requires_revision": true/false
}
""")


class TrainingAgent(BaseOpenForgeAgent):
    """
    Agent for generating training materials from ontology and system documentation.

    This agent:
    - Generates structured training curricula
    - Creates step-by-step tutorials
    - Produces quickstart guides for rapid onboarding
    - Designs assessments and knowledge checks
    - Validates training material quality
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
        """Register training-specific prompts with the library."""
        PromptLibrary.register("training_system", TRAINING_SYSTEM)
        PromptLibrary.register("generate_curriculum", GENERATE_CURRICULUM)
        PromptLibrary.register("generate_tutorial", GENERATE_TUTORIAL)
        PromptLibrary.register("generate_quickstart", GENERATE_QUICKSTART)
        PromptLibrary.register("generate_assessment", GENERATE_ASSESSMENT)
        PromptLibrary.register("validate_training", VALIDATE_TRAINING)

    @property
    def name(self) -> str:
        return "training_agent"

    @property
    def description(self) -> str:
        return (
            "Generates training materials, tutorials, and quickstart guides "
            "from ontology definitions and system documentation."
        )

    @property
    def required_inputs(self) -> List[str]:
        return ["ontology_schema"]

    @property
    def output_keys(self) -> List[str]:
        return [
            "training_materials",
            "tutorials",
            "quickstart_guides",
            "training_quality_report"
        ]

    @property
    def state_class(self) -> Type[EnablementState]:
        return EnablementState

    def get_system_prompt(self) -> str:
        """Get the system prompt for this agent."""
        return TRAINING_SYSTEM.template

    def build_graph(self) -> StateGraph:
        """Build the LangGraph workflow for training content generation."""
        builder = WorkflowBuilder(EnablementState)

        async def analyze_training_needs(state: EnablementState) -> Dict[str, Any]:
            """Analyze the ontology and context to determine training needs."""
            context = state.get("agent_context", {})
            ontology_schema = context.get("ontology_schema", "")

            prompt = f"""Analyze the following ontology schema and determine training needs:

Ontology Schema:
{ontology_schema}

System Features:
{json.dumps(context.get("system_features", []))}

Identify:
1. Key concepts that need to be taught
2. Complexity levels for different user types
3. Critical workflows that require tutorials
4. Skills progression path
5. Recommended training modules

Output as JSON with keys: key_concepts, complexity_analysis, critical_workflows, skills_path, recommended_modules
"""
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
                decision_type="training_needs_analysis",
                description=f"Identified {len(analysis.get('recommended_modules', []))} training modules needed",
                confidence=0.85 if analysis.get('recommended_modules') else 0.4,
                reasoning="Analyzed ontology and context to determine training requirements"
            )

            return {
                "outputs": {"training_analysis": analysis},
                "decisions": [decision],
                "current_step": "needs_analyzed"
            }

        async def generate_training_curricula(state: EnablementState) -> Dict[str, Any]:
            """Generate training curricula for different skill levels."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})

            # Define skill levels
            skill_levels = context.get("skill_levels", [
                {"level": "beginner", "audience": "New Users", "focus": "core concepts and basic operations"},
                {"level": "intermediate", "audience": "Regular Users", "focus": "advanced features and workflows"},
                {"level": "advanced", "audience": "Power Users/Admins", "focus": "administration, customization, integration"}
            ])

            training_materials = []

            for skill_config in skill_levels:
                prompt = PromptLibrary.format(
                    "generate_curriculum",
                    ontology_schema=context.get("ontology_schema", ""),
                    system_features=json.dumps(context.get("system_features", [])),
                    api_documentation=json.dumps(context.get("api_documentation", {}))[:2000],
                    target_audience=skill_config["audience"],
                    skill_level=skill_config["level"]
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    curriculum = json.loads(response.content)
                except json.JSONDecodeError:
                    curriculum = self._extract_json_from_response(response.content)

                curriculum["skill_level"] = skill_config["level"]
                curriculum["target_audience"] = skill_config["audience"]
                curriculum["generated_at"] = datetime.utcnow().isoformat()
                training_materials.append(curriculum)

            decision = add_decision(
                state,
                decision_type="curriculum_generation",
                description=f"Generated {len(training_materials)} training curricula",
                confidence=0.8 if training_materials else 0.4,
                reasoning="Created skill-level appropriate training paths"
            )

            return {
                "outputs": {"training_materials": training_materials},
                "training_materials": training_materials,
                "decisions": [decision],
                "current_step": "curricula_generated"
            }

        async def generate_tutorials(state: EnablementState) -> Dict[str, Any]:
            """Generate step-by-step tutorials for key workflows."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})
            analysis = outputs.get("training_analysis", {})

            # Get critical workflows from analysis or use defaults
            workflows = analysis.get("critical_workflows", context.get("tutorial_topics", [
                {"topic": "Getting Started", "entities": [], "duration": "30 minutes"},
                {"topic": "Creating and Managing Entities", "entities": [], "duration": "45 minutes"},
                {"topic": "Working with Relationships", "entities": [], "duration": "30 minutes"},
                {"topic": "Using the API", "entities": [], "duration": "60 minutes"}
            ]))

            tutorials = []

            for workflow in workflows:
                if isinstance(workflow, str):
                    workflow = {"topic": workflow, "entities": [], "duration": "30 minutes"}

                prompt = PromptLibrary.format(
                    "generate_tutorial",
                    topic=workflow.get("topic", "General Tutorial"),
                    ontology_schema=context.get("ontology_schema", ""),
                    related_entities=json.dumps(workflow.get("entities", [])),
                    prerequisites=json.dumps(workflow.get("prerequisites", ["Basic system access"])),
                    duration=workflow.get("duration", "30 minutes")
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    tutorial = json.loads(response.content)
                except json.JSONDecodeError:
                    tutorial = self._extract_json_from_response(response.content)

                tutorial["workflow_topic"] = workflow.get("topic", "Unknown")
                tutorial["generated_at"] = datetime.utcnow().isoformat()
                tutorials.append(tutorial)

            decision = add_decision(
                state,
                decision_type="tutorial_generation",
                description=f"Generated {len(tutorials)} step-by-step tutorials",
                confidence=0.75 if tutorials else 0.4,
                reasoning="Created practical tutorials for key workflows"
            )

            return {
                "outputs": {"tutorials": tutorials},
                "tutorials": tutorials,
                "decisions": [decision],
                "current_step": "tutorials_generated"
            }

        async def generate_quickstarts(state: EnablementState) -> Dict[str, Any]:
            """Generate quickstart guides for rapid onboarding."""
            context = state.get("agent_context", {})
            outputs = state.get("outputs", {})

            # Define quickstart scenarios
            scenarios = context.get("quickstart_scenarios", [
                {"name": "Developer Quickstart", "target_time": "15 minutes", "focus": "API access and first request"},
                {"name": "End User Quickstart", "target_time": "10 minutes", "focus": "Basic navigation and tasks"},
                {"name": "Admin Quickstart", "target_time": "20 minutes", "focus": "Configuration and user management"}
            ])

            quickstart_guides = []

            for scenario in scenarios:
                prompt = PromptLibrary.format(
                    "generate_quickstart",
                    system_overview=json.dumps(context.get("system_overview", {})),
                    ontology_schema=context.get("ontology_schema", ""),
                    key_features=json.dumps(context.get("key_features", [])),
                    target_time=scenario.get("target_time", "15 minutes")
                )

                messages = [
                    SystemMessage(content=self.get_system_prompt()),
                    HumanMessage(content=prompt)
                ]

                response = await self.llm.ainvoke(messages)

                try:
                    quickstart = json.loads(response.content)
                except json.JSONDecodeError:
                    quickstart = self._extract_json_from_response(response.content)

                quickstart["scenario"] = scenario.get("name", "Unknown")
                quickstart["focus"] = scenario.get("focus", "")
                quickstart["generated_at"] = datetime.utcnow().isoformat()
                quickstart_guides.append(quickstart)

            decision = add_decision(
                state,
                decision_type="quickstart_generation",
                description=f"Generated {len(quickstart_guides)} quickstart guides",
                confidence=0.8 if quickstart_guides else 0.5,
                reasoning="Created rapid onboarding materials for different user types"
            )

            return {
                "outputs": {"quickstart_guides": quickstart_guides},
                "quickstart_guides": quickstart_guides,
                "decisions": [decision],
                "current_step": "quickstarts_generated"
            }

        async def validate_training_materials(state: EnablementState) -> Dict[str, Any]:
            """Validate all generated training materials for quality."""
            outputs = state.get("outputs", {})

            quality_reports = []
            requires_revision = False

            # Validate training curricula
            for curriculum in outputs.get("training_materials", []):
                validation = await self._validate_single_material(
                    f"Curriculum - {curriculum.get('skill_level', 'Unknown')}",
                    curriculum
                )
                quality_reports.append(validation)
                if validation.get("requires_revision"):
                    requires_revision = True

            # Validate tutorials
            for tutorial in outputs.get("tutorials", []):
                validation = await self._validate_single_material(
                    f"Tutorial - {tutorial.get('title', 'Unknown')}",
                    tutorial
                )
                quality_reports.append(validation)
                if validation.get("requires_revision"):
                    requires_revision = True

            # Validate quickstarts
            for quickstart in outputs.get("quickstart_guides", []):
                validation = await self._validate_single_material(
                    f"Quickstart - {quickstart.get('scenario', 'Unknown')}",
                    quickstart
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
                "material_reports": quality_reports,
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
                                item_type="training_quality",
                                item_id=f"training_review_{report.get('material_type', 'unknown')}",
                                description=f"Training material requires revision: {', '.join(report.get('issues', []))}",
                                priority="medium"
                            )
                        )

            decision = add_decision(
                state,
                decision_type="training_validation",
                description=f"Validated training materials quality: {avg_score:.2f} overall score",
                confidence=avg_score,
                reasoning="Assessed completeness, clarity, and practicality of training materials",
                requires_approval=requires_revision
            )

            return {
                "outputs": {"training_quality_report": quality_report},
                "decisions": [decision],
                "requires_human_review": requires_revision,
                "review_items": review_items,
                "current_step": "validation_complete"
            }

        async def compile_training_package(state: EnablementState) -> Dict[str, Any]:
            """Compile all training materials into a final package."""
            outputs = state.get("outputs", {})
            decisions = state.get("decisions", [])

            # Calculate overall confidence
            avg_confidence = (
                sum(d.confidence for d in decisions) / len(decisions)
                if decisions else 0.5
            )

            training_package = {
                "training_materials": outputs.get("training_materials", []),
                "tutorials": outputs.get("tutorials", []),
                "quickstart_guides": outputs.get("quickstart_guides", []),
                "quality_report": outputs.get("training_quality_report", {}),
                "metadata": {
                    "generated_at": datetime.utcnow().isoformat(),
                    "confidence_score": avg_confidence,
                    "total_items": (
                        len(outputs.get("training_materials", [])) +
                        len(outputs.get("tutorials", [])) +
                        len(outputs.get("quickstart_guides", []))
                    )
                }
            }

            decision = add_decision(
                state,
                decision_type="training_compilation",
                description="Compiled complete training package",
                confidence=avg_confidence,
                reasoning="Aggregated all training outputs"
            )

            return {
                "outputs": {"training_package": training_package},
                "decisions": [decision],
                "current_step": "complete"
            }

        def route_after_validation(state: EnablementState) -> str:
            """Route based on validation results."""
            if state.get("requires_human_review"):
                return "await_review"
            return "compile"

        async def await_human_review(state: EnablementState) -> Dict[str, Any]:
            """Wait for human review of training materials."""
            return {
                "current_step": "awaiting_human_review"
            }

        # Build the workflow
        graph = (builder
            .add_node("analyze_needs", analyze_training_needs)
            .add_node("generate_curricula", generate_training_curricula)
            .add_node("generate_tutorials", generate_tutorials)
            .add_node("generate_quickstarts", generate_quickstarts)
            .add_node("validate", validate_training_materials)
            .add_node("await_review", await_human_review)
            .add_node("compile", compile_training_package)
            .set_entry("analyze_needs")
            .add_edge("analyze_needs", "generate_curricula")
            .add_edge("generate_curricula", "generate_tutorials")
            .add_edge("generate_tutorials", "generate_quickstarts")
            .add_edge("generate_quickstarts", "validate")
            .add_conditional("validate", route_after_validation, {
                "await_review": "await_review",
                "compile": "compile"
            })
            .add_edge("await_review", "END")
            .add_edge("compile", "END")
            .build())

        return graph

    async def _validate_single_material(
        self,
        material_type: str,
        content: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate a single training material."""
        prompt = PromptLibrary.format(
            "validate_training",
            training_type=material_type,
            training_content=json.dumps(content, default=str)[:4000]
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

        validation["material_type"] = material_type
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
