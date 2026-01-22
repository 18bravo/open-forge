"""
FastAPI routes for forge-ai.

This module provides HTTP endpoints for AI operations.
Stub implementation - would be fully implemented with FastAPI in production.
"""

from typing import Any


def create_router(
    llm_provider: Any | None = None,
    guardrails_engine: Any | None = None,
    audit_logger: Any | None = None,
) -> Any:
    """
    Create a FastAPI router for forge-ai endpoints.

    Args:
        llm_provider: The LLM provider instance.
        guardrails_engine: The guardrails engine instance.
        audit_logger: The audit logger instance.

    Returns:
        FastAPI APIRouter instance.

    Example usage:
        ```python
        from fastapi import FastAPI
        from forge_ai.api import create_router
        from forge_ai.providers import LiteLLMProvider

        app = FastAPI()
        provider = LiteLLMProvider()
        router = create_router(llm_provider=provider)
        app.include_router(router, prefix="/api/v1/ai")
        ```
    """
    try:
        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel

        router = APIRouter(tags=["ai"])

        # Request/Response models
        class CompletionRequestModel(BaseModel):
            model: str = "gpt-4o"
            messages: list[dict[str, Any]]
            temperature: float = 0.7
            max_tokens: int | None = None
            stream: bool = False

        class CompletionResponseModel(BaseModel):
            content: str
            model: str
            finish_reason: str
            usage: dict[str, int]

        @router.post("/completions", response_model=CompletionResponseModel)
        async def create_completion(request: CompletionRequestModel):
            """Execute an LLM completion."""
            if llm_provider is None:
                raise HTTPException(status_code=503, detail="LLM provider not configured")

            from forge_ai.providers.base import CompletionRequest, Message

            # Convert to internal format
            messages = [
                Message(role=m["role"], content=m["content"])
                for m in request.messages
            ]

            completion_request = CompletionRequest(
                model=request.model,
                messages=messages,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )

            # Apply guardrails if available
            if guardrails_engine:
                for msg in messages:
                    if msg.role == "user":
                        result = await guardrails_engine.filter_input(msg.content)
                        if result.was_blocked:
                            raise HTTPException(
                                status_code=400,
                                detail="Request blocked by security guardrails"
                            )

            # Execute completion
            response = await llm_provider.complete(completion_request)

            # Apply output guardrails
            if guardrails_engine:
                output_result = await guardrails_engine.filter_output(response.content)
                if output_result.was_modified:
                    response.content = output_result.filtered_content

            # Log to audit
            if audit_logger:
                await audit_logger.log_request(completion_request, response)

            return CompletionResponseModel(
                content=response.content,
                model=response.model,
                finish_reason=response.finish_reason,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            )

        @router.get("/models")
        async def list_models():
            """List available LLM models."""
            if llm_provider is None:
                raise HTTPException(status_code=503, detail="LLM provider not configured")

            models = llm_provider.supported_models()
            return {
                "models": [m.model_dump() for m in models]
            }

        @router.get("/health")
        async def health_check():
            """Check the health of the AI service."""
            healthy = True
            details = {}

            if llm_provider:
                try:
                    provider_healthy = await llm_provider.health_check()
                    details["llm_provider"] = "healthy" if provider_healthy else "unhealthy"
                    healthy = healthy and provider_healthy
                except Exception as e:
                    details["llm_provider"] = f"error: {e}"
                    healthy = False
            else:
                details["llm_provider"] = "not configured"

            return {
                "status": "healthy" if healthy else "unhealthy",
                "details": details,
            }

        return router

    except ImportError:
        # FastAPI not installed - return None
        return None
