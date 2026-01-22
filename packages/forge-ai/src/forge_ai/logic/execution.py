"""
Logic function execution engine.

This module provides the execution engine for running logic functions
with variable resolution, template rendering, and output parsing.
"""

import json
import time
from typing import Any

import structlog

from forge_ai.logic.functions import (
    LogicFunction,
    LogicFunctionResult,
    VariableSource,
)

logger = structlog.get_logger(__name__)


class FunctionExecutionError(Exception):
    """Error during function execution."""

    def __init__(self, message: str, function_id: str, details: dict[str, Any] | None = None):
        self.function_id = function_id
        self.details = details or {}
        super().__init__(f"[{function_id}] {message}")


class FunctionExecutor:
    """
    Executor for logic functions.

    Handles:
    - Variable resolution from ontology, user inputs, etc.
    - Template rendering with Jinja2
    - LLM completion with structured output
    - Output parsing and validation
    """

    def __init__(
        self,
        llm_provider: Any | None = None,  # LLMProvider
        ontology_client: Any | None = None,  # OntologyClient
        context_builder: Any | None = None,  # ContextBuilder
    ):
        """
        Initialize the function executor.

        Args:
            llm_provider: The LLM provider for completions.
            ontology_client: Client for ontology queries.
            context_builder: Builder for ontology context injection.
        """
        self.llm_provider = llm_provider
        self.ontology_client = ontology_client
        self.context_builder = context_builder

        # Initialize Jinja2 environment
        try:
            from jinja2 import Environment, StrictUndefined

            self.jinja = Environment(
                autoescape=True,
                undefined=StrictUndefined,
            )
        except ImportError:
            logger.warning("Jinja2 not available, template rendering will be limited")
            self.jinja = None

    async def execute(
        self,
        function: LogicFunction,
        inputs: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> LogicFunctionResult:
        """
        Execute a logic function.

        Args:
            function: The logic function to execute.
            inputs: User-provided inputs for variables.
            context: Additional context (e.g., current user, session).

        Returns:
            LogicFunctionResult with the output or error.
        """
        start_time = time.perf_counter()

        try:
            # 1. Resolve variable bindings
            resolved_variables = await self._resolve_variables(function, inputs, context)

            # 2. Render prompt template
            prompt = self._render_template(function.prompt_template, resolved_variables)

            # 3. Build completion request
            request = self._build_request(function, prompt)

            # 4. Execute completion
            if self.llm_provider is None:
                raise FunctionExecutionError(
                    "LLM provider not configured",
                    function.id,
                )

            response = await self.llm_provider.complete(request)

            # 5. Parse structured output
            output = self._parse_output(response.content, function)

            latency_ms = (time.perf_counter() - start_time) * 1000

            return LogicFunctionResult(
                success=True,
                output=output,
                function_id=function.id,
                function_version=function.version,
                input_tokens=response.usage.input_tokens,
                output_tokens=response.usage.output_tokens,
                total_tokens=response.usage.total_tokens,
                latency_ms=latency_ms,
                resolved_variables=resolved_variables,
                raw_response=response.content,
            )

        except FunctionExecutionError:
            raise
        except Exception as e:
            latency_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                "Function execution failed",
                function_id=function.id,
                error=str(e),
            )
            return LogicFunctionResult(
                success=False,
                error=str(e),
                function_id=function.id,
                function_version=function.version,
                latency_ms=latency_ms,
            )

    async def _resolve_variables(
        self,
        function: LogicFunction,
        inputs: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Resolve all variable bindings for the function."""
        resolved: dict[str, Any] = {}
        context = context or {}

        for variable in function.variables:
            value = None

            if variable.source == VariableSource.USER_INPUT:
                if variable.name in inputs:
                    value = inputs[variable.name]
                elif variable.default_value is not None:
                    value = variable.default_value
                elif variable.required:
                    raise FunctionExecutionError(
                        f"Required input variable '{variable.name}' not provided",
                        function.id,
                    )

            elif variable.source == VariableSource.CONSTANT:
                value = variable.default_value

            elif variable.source == VariableSource.CONTEXT:
                if variable.name in context:
                    value = context[variable.name]
                elif variable.property_path and variable.property_path in context:
                    value = context[variable.property_path]

            elif variable.source == VariableSource.ONTOLOGY_OBJECT:
                if self.ontology_client is None:
                    raise FunctionExecutionError(
                        "Ontology client not configured for ontology variable",
                        function.id,
                    )
                # Fetch object from ontology
                object_id = inputs.get(f"{variable.name}_id") or inputs.get(variable.name)
                if object_id and variable.object_type:
                    value = await self._fetch_ontology_object(
                        function.ontology_id,
                        variable.object_type,
                        object_id,
                        variable.property_path,
                    )

            elif variable.source == VariableSource.ONTOLOGY_PROPERTY:
                if self.ontology_client is None:
                    raise FunctionExecutionError(
                        "Ontology client not configured for ontology variable",
                        function.id,
                    )
                object_id = inputs.get(f"{variable.name}_id") or inputs.get(variable.name)
                if object_id and variable.object_type and variable.property_path:
                    obj = await self._fetch_ontology_object(
                        function.ontology_id,
                        variable.object_type,
                        object_id,
                    )
                    if obj:
                        value = self._get_nested_value(obj, variable.property_path)

            elif variable.source == VariableSource.PREVIOUS_OUTPUT:
                # Get from context (would be set by workflow engine)
                if variable.name in context.get("previous_outputs", {}):
                    value = context["previous_outputs"][variable.name]

            if value is None and variable.required:
                raise FunctionExecutionError(
                    f"Could not resolve required variable '{variable.name}'",
                    function.id,
                )

            resolved[variable.name] = value

        return resolved

    async def _fetch_ontology_object(
        self,
        ontology_id: str,
        object_type: str,
        object_id: str,
        property_path: str | None = None,
    ) -> Any:
        """Fetch an object from the ontology."""
        # Stub implementation - would use actual ontology client
        logger.debug(
            "Fetching ontology object",
            ontology_id=ontology_id,
            object_type=object_type,
            object_id=object_id,
        )

        if self.ontology_client is None:
            return None

        # This would be implemented by the actual ontology client
        try:
            obj = await self.ontology_client.get_object(
                ontology_id=ontology_id,
                object_type=object_type,
                object_id=object_id,
            )
            if property_path:
                return self._get_nested_value(obj, property_path)
            return obj
        except Exception as e:
            logger.warning("Failed to fetch ontology object", error=str(e))
            return None

    def _get_nested_value(self, obj: Any, path: str) -> Any:
        """Get a nested value from an object using dot notation."""
        parts = path.split(".")
        value = obj

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None

            if value is None:
                return None

        return value

    def _render_template(self, template: str, variables: dict[str, Any]) -> str:
        """Render a Jinja2 template with variables."""
        if self.jinja is None:
            # Fallback to simple string formatting
            result = template
            for name, value in variables.items():
                result = result.replace(f"{{{{ {name} }}}}", str(value))
            return result

        try:
            jinja_template = self.jinja.from_string(template)
            return jinja_template.render(**variables)
        except Exception as e:
            raise FunctionExecutionError(
                f"Template rendering failed: {e}",
                "",
                {"template_error": str(e)},
            )

    def _build_request(self, function: LogicFunction, prompt: str) -> Any:
        """Build a completion request for the function."""
        from forge_ai.providers.base import (
            CompletionRequest,
            Message,
            ResponseFormat,
        )

        messages = [Message(role="user", content=prompt)]

        # Add JSON schema for structured output
        response_format = None
        if function.output_schema:
            response_format = ResponseFormat(
                type="json_schema",
                json_schema=function.get_json_schema(),
            )

        return CompletionRequest(
            model=function.model,
            messages=messages,
            temperature=function.temperature,
            max_tokens=function.max_tokens,
            response_format=response_format,
            ontology_id=function.ontology_id,
        )

    def _parse_output(self, content: str, function: LogicFunction) -> dict[str, Any]:
        """Parse the LLM output into structured format."""
        if not function.output_schema:
            return {"result": content}

        try:
            output = json.loads(content)

            # Validate against schema (basic validation)
            for field in function.output_schema:
                if field.required and field.name not in output:
                    logger.warning(
                        "Missing required output field",
                        field=field.name,
                        function_id=function.id,
                    )

            return output

        except json.JSONDecodeError as e:
            logger.warning(
                "Failed to parse output as JSON",
                error=str(e),
                content_preview=content[:200],
            )
            # Return raw content if JSON parsing fails
            return {"result": content, "_parse_error": str(e)}

    async def validate_function(self, function: LogicFunction) -> list[str]:
        """
        Validate a logic function definition.

        Returns a list of validation errors (empty if valid).
        """
        errors: list[str] = []

        if not function.name:
            errors.append("Function name is required")

        if not function.ontology_id:
            errors.append("Ontology ID is required")

        if not function.prompt_template:
            errors.append("Prompt template is required")

        # Check that all template variables are defined
        if self.jinja:
            from jinja2 import meta

            try:
                ast = self.jinja.parse(function.prompt_template)
                template_vars = meta.find_undeclared_variables(ast)
                defined_vars = {v.name for v in function.variables}

                undefined = template_vars - defined_vars
                if undefined:
                    errors.append(f"Undefined template variables: {', '.join(undefined)}")
            except Exception as e:
                errors.append(f"Invalid template syntax: {e}")

        return errors
