# Track C: Forge AI - AI Platform Design

**Date:** 2026-01-20
**Status:** Approved
**Track:** C (AI Platform)
**Goal:** Build comprehensive AI platform with multi-LLM support, no-code functions, visual agents, and evaluation

---

## Executive Summary

Forge AI is the AI platform enabling LLM-powered features across Open Forge. It provides multi-provider model access via LiteLLM, no-code function building, visual agent creation compiled to LangGraph, comprehensive evaluation, and RAG capabilities.

### Key Decisions

1. **Hybrid LiteLLM + Custom**: LiteLLM for 100+ providers, custom layer for Forge-specific features
2. **Hybrid Context Injection**: Schema in system prompt + RAG for content + Tools for dynamic queries
3. **Prompt Builder + Output Schema**: Visual prompt builder with JSON schema outputs for Forge Logic
4. **Visual + Code Escape**: Visual agent config with code blocks for custom logic in Agent Builder
5. **Multi-Strategy Evaluation**: Exact match, semantic similarity, LLM-as-judge, and custom evaluators
6. **pgvector Default + Pluggable**: Zero-config default with enterprise vector DB options

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FORGE AI                                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    APPLICATION LAYER                             │    │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐           │    │
│  │  │  Logic   │ │  Agent   │ │ Evaluate │ │ Copilot  │           │    │
│  │  │ (no-code)│ │ Builder  │ │ (testing)│ │(assistant)│           │    │
│  │  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘           │    │
│  │       │            │            │            │                  │    │
│  │       └────────────┴────────────┴────────────┘                  │    │
│  │                          │                                       │    │
│  └──────────────────────────┼───────────────────────────────────────┘    │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    CORE SERVICES                                 │    │
│  │                                                                  │    │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌────────────────┐  │    │
│  │  │  AI Core        │  │  Forge Vectors  │  │  Forge ML      │  │    │
│  │  │  (Multi-LLM)    │  │  (RAG/Embed)    │  │  (Model Ops)   │  │    │
│  │  │                 │  │                 │  │                │  │    │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ ┌────────────┐ │  │    │
│  │  │ │   LiteLLM   │ │  │ │  pgvector   │ │  │ │  Registry  │ │  │    │
│  │  │ │  (100+ LLM) │ │  │ │  (default)  │ │  │ │  Deploy    │ │  │    │
│  │  │ └─────────────┘ │  │ └─────────────┘ │  │ │  Monitor   │ │  │    │
│  │  │ ┌─────────────┐ │  │ ┌─────────────┐ │  │ └────────────┘ │  │    │
│  │  │ │  Guardrails │ │  │ │Qdrant/Pine- │ │  │                │  │    │
│  │  │ │  PII Filter │ │  │ │cone/Weaviate│ │  │                │  │    │
│  │  │ └─────────────┘ │  │ └─────────────┘ │  │                │  │    │
│  │  └─────────────────┘  └─────────────────┘  └────────────────┘  │    │
│  │                                                                  │    │
│  └──────────────────────────────────────────────────────────────────┘    │
│                             │                                            │
│                             ▼                                            │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                 ONTOLOGY INTEGRATION                             │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │    │
│  │  │Schema Inject│  │  RAG Index  │  │  Tools (query, traverse)│  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────┘    │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AI Core (Multi-LLM Abstraction)

### Provider Architecture

```python
# packages/forge-ai-core/src/providers/base.py

from abc import ABC, abstractmethod
from typing import AsyncIterator
from pydantic import BaseModel

class Message(BaseModel):
    role: str  # 'system', 'user', 'assistant', 'tool'
    content: str | list[ContentBlock]
    tool_calls: list[ToolCall] | None = None

class CompletionRequest(BaseModel):
    messages: list[Message]
    model: str
    temperature: float = 0.7
    max_tokens: int | None = None
    tools: list[ToolDefinition] | None = None
    response_format: ResponseFormat | None = None
    stream: bool = False

class CompletionResponse(BaseModel):
    content: str
    tool_calls: list[ToolCall] | None = None
    usage: TokenUsage
    model: str
    finish_reason: str

class ForgeAIClient:
    """Main entry point for all LLM interactions"""

    def __init__(
        self,
        config: AIConfig,
        ontology: OntologyClient,
        guardrails: GuardrailsEngine,
        audit: AuditLogger
    ):
        self.litellm = LiteLLMWrapper(config)
        self.ontology = ontology
        self.guardrails = guardrails
        self.audit = audit
        self.context_builder = ContextBuilder(ontology)

    async def complete(
        self,
        request: CompletionRequest,
        context: ContextConfig | None = None
    ) -> CompletionResponse:
        """Execute LLM completion with Forge enhancements"""

        # 1. Build ontology context
        if context:
            request = await self.context_builder.inject(request, context)

        # 2. Apply input guardrails
        request = await self.guardrails.filter_input(request)

        # 3. Call LLM via LiteLLM
        response = await self.litellm.complete(request)

        # 4. Apply output guardrails
        response = await self.guardrails.filter_output(response)

        # 5. Audit log
        await self.audit.log(request, response)

        return response

    async def stream(
        self,
        request: CompletionRequest,
        context: ContextConfig | None = None
    ) -> AsyncIterator[StreamChunk]:
        """Streaming completion"""
        request.stream = True
        async for chunk in self.litellm.stream(request):
            yield chunk
```

### LiteLLM Wrapper

```python
# packages/forge-ai-core/src/providers/litellm_wrapper.py

import litellm
from litellm import acompletion

class LiteLLMWrapper:
    """Thin wrapper around LiteLLM with Forge defaults"""

    def __init__(self, config: AIConfig):
        self._setup_credentials(config)
        litellm.set_verbose = config.debug
        litellm.drop_params = True

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        response = await acompletion(
            model=request.model,
            messages=[m.dict() for m in request.messages],
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            tools=request.tools,
            response_format=request.response_format,
            stream=request.stream
        )
        return self._parse_response(response)

    def supported_models(self) -> list[ModelInfo]:
        return [
            ModelInfo(id="gpt-4o", provider="openai", capabilities=["chat", "vision", "tools"]),
            ModelInfo(id="gpt-4o-mini", provider="openai", capabilities=["chat", "tools"]),
            ModelInfo(id="claude-3-5-sonnet", provider="anthropic", capabilities=["chat", "vision", "tools"]),
            ModelInfo(id="claude-3-5-haiku", provider="anthropic", capabilities=["chat", "tools"]),
            ModelInfo(id="gemini-1.5-pro", provider="google", capabilities=["chat", "vision", "tools"]),
            ModelInfo(id="gemini-1.5-flash", provider="google", capabilities=["chat", "vision", "tools"]),
            ModelInfo(id="llama-3.1-70b", provider="together", capabilities=["chat", "tools"]),
            ModelInfo(id="mistral-large", provider="mistral", capabilities=["chat", "tools"]),
        ]
```

### Model Routing

```python
# packages/forge-ai-core/src/routing/router.py

class ModelRouter:
    """Intelligent model selection and fallback"""

    def __init__(self, config: RoutingConfig):
        self.default_model = config.default_model
        self.fallback_chain = config.fallback_chain
        self.cost_limits = config.cost_limits

    async def select_model(
        self,
        request: CompletionRequest,
        preferences: ModelPreferences | None = None
    ) -> str:
        if request.model:
            return request.model

        if request.tools:
            return self._select_with_capability("tools")
        if self._has_images(request):
            return self._select_with_capability("vision")

        return self.default_model

    async def with_fallback(
        self,
        fn: Callable,
        request: CompletionRequest
    ) -> CompletionResponse:
        for model in [request.model] + self.fallback_chain:
            try:
                request.model = model
                return await fn(request)
            except (RateLimitError, ModelNotAvailableError):
                continue
        raise AllModelsFailedError()
```

---

## Ontology Context Integration

### Context Builder

```python
# packages/forge-ai-core/src/context/builder.py

class ContextConfig(BaseModel):
    ontology_id: str
    include_schema: bool = True
    rag_query: str | None = None
    rag_object_types: list[str] | None = None
    rag_top_k: int = 5
    enable_tools: bool = True

class ContextBuilder:
    """Builds ontology-aware context for LLM requests"""

    def __init__(self, ontology: OntologyClient, vectors: VectorStore):
        self.ontology = ontology
        self.vectors = vectors

    async def inject(
        self,
        request: CompletionRequest,
        config: ContextConfig
    ) -> CompletionRequest:
        system_parts = []

        # 1. Schema injection
        if config.include_schema:
            schema = await self.ontology.get_schema(config.ontology_id)
            system_parts.append(self._format_schema(schema))

        # 2. RAG retrieval
        if config.rag_query:
            chunks = await self.vectors.search(
                query=config.rag_query,
                ontology_id=config.ontology_id,
                object_types=config.rag_object_types,
                top_k=config.rag_top_k
            )
            system_parts.append(self._format_rag_results(chunks))

        # 3. Tool definitions
        if config.enable_tools:
            request.tools = request.tools or []
            request.tools.extend(self._ontology_tools(config.ontology_id))

        if system_parts:
            request = self._prepend_system(request, "\n\n".join(system_parts))

        return request

    def _ontology_tools(self, ontology_id: str) -> list[ToolDefinition]:
        return [
            ToolDefinition(
                name="get_object",
                description="Retrieve a specific object by type and ID",
                parameters={
                    "object_type": {"type": "string"},
                    "object_id": {"type": "string"}
                }
            ),
            ToolDefinition(
                name="search_objects",
                description="Search for objects matching criteria",
                parameters={
                    "object_type": {"type": "string"},
                    "filters": {"type": "object"},
                    "limit": {"type": "integer", "default": 10}
                }
            ),
            ToolDefinition(
                name="traverse_links",
                description="Follow links from an object to related objects",
                parameters={
                    "object_type": {"type": "string"},
                    "object_id": {"type": "string"},
                    "link_type": {"type": "string"}
                }
            )
        ]
```

### Tool Executor

```python
# packages/forge-ai-core/src/context/tool_executor.py

class OntologyToolExecutor:
    """Executes ontology tools called by LLM"""

    def __init__(self, ontology: OntologyClient):
        self.ontology = ontology

    async def execute(
        self,
        tool_call: ToolCall,
        ontology_id: str
    ) -> ToolResult:
        match tool_call.name:
            case "get_object":
                obj = await self.ontology.get_object(
                    ontology_id=ontology_id,
                    object_type=tool_call.args["object_type"],
                    object_id=tool_call.args["object_id"]
                )
                return ToolResult(content=obj.to_json())

            case "search_objects":
                results = await self.ontology.search(
                    ontology_id=ontology_id,
                    object_type=tool_call.args["object_type"],
                    filters=tool_call.args.get("filters"),
                    limit=tool_call.args.get("limit", 10)
                )
                return ToolResult(content=results.to_json())

            case "traverse_links":
                linked = await self.ontology.traverse(
                    ontology_id=ontology_id,
                    object_type=tool_call.args["object_type"],
                    object_id=tool_call.args["object_id"],
                    link_type=tool_call.args["link_type"]
                )
                return ToolResult(content=linked.to_json())

            case _:
                raise UnknownToolError(tool_call.name)
```

---

## Forge Logic (No-Code LLM Functions)

### Function Definition Model

```python
# packages/forge-logic/src/models.py

class VariableBinding(BaseModel):
    name: str
    source: str  # 'ontology_object', 'ontology_property', 'user_input', 'constant'
    object_type: str | None = None
    property_path: str | None = None
    description: str | None = None

class OutputField(BaseModel):
    name: str
    type: str  # 'string', 'number', 'boolean', 'array', 'object'
    description: str
    enum: list[str] | None = None
    items: 'OutputField | None' = None

class LogicFunction(BaseModel):
    id: str
    name: str
    description: str
    ontology_id: str

    model: str = "gpt-4o"
    temperature: float = 0.3
    max_tokens: int | None = None

    variables: list[VariableBinding]
    prompt_template: str
    output_schema: list[OutputField]

    include_schema: bool = True
    rag_enabled: bool = False
    rag_query_template: str | None = None

    created_by: str
    created_at: datetime
    version: int = 1
    published: bool = False
```

### Function Executor

```python
# packages/forge-logic/src/executor.py

class LogicFunctionExecutor:
    """Executes no-code LLM functions"""

    def __init__(self, ai_client: ForgeAIClient, ontology: OntologyClient):
        self.ai = ai_client
        self.ontology = ontology
        self.jinja = Environment(autoescape=True)

    async def execute(
        self,
        function: LogicFunction,
        inputs: dict[str, Any]
    ) -> LogicFunctionResult:
        # 1. Resolve variable bindings
        resolved = await self._resolve_variables(function, inputs)

        # 2. Render prompt template
        template = self.jinja.from_string(function.prompt_template)
        prompt = template.render(**resolved)

        # 3. Build request with JSON schema output
        request = CompletionRequest(
            model=function.model,
            temperature=function.temperature,
            max_tokens=function.max_tokens,
            messages=[Message(role="user", content=prompt)],
            response_format=ResponseFormat(
                type="json_schema",
                json_schema=self._build_json_schema(function.output_schema)
            )
        )

        # 4. Build context config
        context = ContextConfig(
            ontology_id=function.ontology_id,
            include_schema=function.include_schema,
            rag_query=self._render_rag_query(function, resolved) if function.rag_enabled else None
        )

        # 5. Execute
        response = await self.ai.complete(request, context)

        # 6. Parse structured output
        output = json.loads(response.content)

        return LogicFunctionResult(
            success=True,
            output=output,
            usage=response.usage
        )
```

---

## Forge Agent Builder

### Agent Definition Model

```python
# packages/forge-agent-builder/src/models.py

class AgentPersona(BaseModel):
    name: str
    description: str
    system_prompt: str
    tone: str = "professional"

class AgentTool(BaseModel):
    type: str  # 'ontology', 'logic_function', 'external_api', 'custom'
    tool_id: str | None = None
    custom_definition: ToolDefinition | None = None

class AgentGuardrail(BaseModel):
    type: str  # 'topic_restriction', 'pii_filter', 'output_validation', 'custom'
    config: dict

class AgentDefinition(BaseModel):
    id: str
    name: str
    description: str
    ontology_id: str

    persona: AgentPersona
    model: str = "gpt-4o"

    tools: list[AgentTool]
    enable_ontology_tools: bool = True
    enable_rag: bool = True

    guardrails: list[AgentGuardrail]
    require_approval_for: list[str] = []

    custom_router: str | None = None
    custom_state: dict | None = None

    states: list[str] = ["main"]
    transitions: list[AgentTransition] = []

    version: int = 1
    published: bool = False
```

### Agent Compiler (to LangGraph)

```python
# packages/forge-agent-builder/src/compiler.py

from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

class AgentCompiler:
    """Compiles visual agent definition to LangGraph"""

    def __init__(self, ai_client: ForgeAIClient, tool_registry: ToolRegistry):
        self.ai = ai_client
        self.tools = tool_registry

    def compile(self, definition: AgentDefinition) -> CompiledAgent:
        tools = self._build_tools(definition)
        state_schema = self._build_state_schema(definition)

        graph = StateGraph(state_schema)

        graph.add_node("agent", self._create_agent_node(definition, tools))
        graph.add_node("tools", ToolNode(tools))

        if definition.require_approval_for:
            graph.add_node("approval", self._create_approval_node(definition))

        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            self._create_router(definition),
            {
                "tools": "tools",
                "approval": "approval" if definition.require_approval_for else "tools",
                "end": END
            }
        )
        graph.add_edge("tools", "agent")

        if definition.require_approval_for:
            graph.add_edge("approval", "tools")

        return CompiledAgent(
            definition=definition,
            graph=graph.compile(),
            tools=tools
        )
```

### Agent Runtime

```python
# packages/forge-agent-builder/src/runtime.py

class AgentRuntime:
    """Executes compiled agents"""

    async def run(
        self,
        agent: CompiledAgent,
        input_message: str,
        session_id: str | None = None
    ) -> AsyncIterator[AgentEvent]:
        state = await self._load_session(session_id) if session_id else AgentState()
        state.messages.append({"role": "user", "content": input_message})

        async for event in agent.graph.astream(state):
            yield AgentEvent(
                type=event.type,
                content=event.content,
                tool_calls=event.tool_calls,
                requires_approval=event.requires_approval
            )

        if session_id:
            await self._save_session(session_id, state)

    async def approve_tool(
        self,
        session_id: str,
        tool_call_id: str,
        approved: bool,
        modified_args: dict | None = None
    ) -> AsyncIterator[AgentEvent]:
        """Handle human approval for tool execution"""
        ...
```

---

## Forge Evaluate (LLM Testing)

### Evaluation Models

```python
# packages/forge-evaluate/src/models.py

class TestCase(BaseModel):
    id: str
    name: str
    input: dict
    expected: dict | None = None
    criteria: list[str] | None = None
    tags: list[str] = []

class EvaluatorConfig(BaseModel):
    type: str  # 'exact_match', 'semantic_similarity', 'llm_judge', 'custom'
    field: str | None = None
    threshold: float = 0.8
    config: dict = {}

class EvalSuite(BaseModel):
    id: str
    name: str
    description: str
    target_type: str  # 'logic_function', 'agent'
    target_id: str

    test_cases: list[TestCase]
    evaluators: list[EvaluatorConfig]
    perturbations: list[PerturbationConfig] = []

    parallel: bool = True
    max_workers: int = 5
    timeout_seconds: int = 60
```

### Evaluator Implementations

```python
# packages/forge-evaluate/src/evaluators/

class ExactMatchEvaluator(BaseEvaluator):
    async def evaluate(self, actual, expected, criteria) -> EvaluatorResult:
        if isinstance(expected, str):
            score = 1.0 if actual.strip().lower() == expected.strip().lower() else 0.0
        else:
            score = 1.0 if actual == expected else 0.0
        return EvaluatorResult(score=score)

class SemanticSimilarityEvaluator(BaseEvaluator):
    def __init__(self, vectors: VectorStore, threshold: float = 0.8):
        self.vectors = vectors
        self.threshold = threshold

    async def evaluate(self, actual, expected, criteria) -> EvaluatorResult:
        actual_emb = await self.vectors.embed(str(actual))
        expected_emb = await self.vectors.embed(str(expected))
        similarity = cosine_similarity(actual_emb, expected_emb)
        return EvaluatorResult(score=similarity)

class LLMJudgeEvaluator(BaseEvaluator):
    def __init__(self, ai_client: ForgeAIClient, judge_model: str = "gpt-4o"):
        self.ai = ai_client
        self.model = judge_model

    async def evaluate(self, actual, expected, criteria) -> EvaluatorResult:
        prompt = f"""Evaluate the output against criteria.
Output: {json.dumps(actual)}
Criteria: {criteria}
Score 0.0-1.0 in JSON: {{"overall": score, "reasoning": "..."}}"""

        response = await self.ai.complete(CompletionRequest(
            model=self.model,
            messages=[Message(role="user", content=prompt)],
            response_format=ResponseFormat(type="json_object")
        ))
        result = json.loads(response.content)
        return EvaluatorResult(score=result["overall"], details=result)

class CustomEvaluator(BaseEvaluator):
    def __init__(self, code: str):
        self.fn = self._compile_function(code)

    async def evaluate(self, actual, expected, criteria) -> EvaluatorResult:
        score = self.fn(actual, expected)
        return EvaluatorResult(score=score)
```

### Perturbation Testing

```python
# packages/forge-evaluate/src/perturbations.py

class PerturbationConfig(BaseModel):
    type: str  # 'typo', 'paraphrase', 'adversarial', 'language'
    field: str
    intensity: float = 0.5

class PerturbationEngine:
    async def perturb(self, test_case: TestCase, config: PerturbationConfig) -> list[TestCase]:
        match config.type:
            case 'typo':
                return self._add_typos(test_case, config)
            case 'paraphrase':
                return await self._paraphrase(test_case, config)
            case 'adversarial':
                return await self._adversarial(test_case, config)
            case 'language':
                return await self._translate(test_case, config)
```

### Suite Runner

```python
# packages/forge-evaluate/src/runner.py

class EvalSuiteRunner:
    async def run(self, suite: EvalSuite) -> EvalSuiteResult:
        target = await self._load_target(suite.target_type, suite.target_id)

        all_cases = list(suite.test_cases)
        for case in suite.test_cases:
            for perturb_config in suite.perturbations:
                all_cases.extend(await self.perturbation_engine.perturb(case, perturb_config))

        if suite.parallel:
            results = await asyncio.gather(*[
                self._evaluate_case(target, case, suite.evaluators)
                for case in all_cases
            ])
        else:
            results = [await self._evaluate_case(target, case, suite.evaluators) for case in all_cases]

        return EvalSuiteResult(
            suite_id=suite.id,
            total_cases=len(results),
            passed=sum(1 for r in results if r.passed),
            failed=sum(1 for r in results if not r.passed),
            avg_score=sum(r.scores.get("overall", 0) for r in results) / len(results),
            results=results
        )
```

---

## Forge Vectors (Embeddings & RAG)

### Vector Store Abstraction

```python
# packages/forge-vectors/src/stores/base.py

class VectorDocument(BaseModel):
    id: str
    content: str
    embedding: list[float] | None = None
    metadata: dict = {}
    ontology_id: str | None = None
    object_type: str | None = None
    object_id: str | None = None

class VectorStore(ABC):
    @abstractmethod
    async def upsert(self, documents: list[VectorDocument]) -> None: ...

    @abstractmethod
    async def search(self, query: str | list[float], top_k: int = 10, filters: dict | None = None) -> list[SearchResult]: ...

    @abstractmethod
    async def delete(self, ids: list[str]) -> None: ...
```

### Store Implementations

```python
# packages/forge-vectors/src/stores/pgvector.py

class PgVectorStore(VectorStore):
    """PostgreSQL + pgvector (default)"""

    async def search(self, query, top_k=10, filters=None) -> list[SearchResult]:
        query_embedding = await self.embedder.embed(query) if isinstance(query, str) else query
        filter_clause, filter_params = self._build_filters(filters)

        rows = await self.conn.fetch(f"""
            SELECT *, 1 - (embedding <=> $1::vector) as score
            FROM forge_vectors WHERE 1=1 {filter_clause}
            ORDER BY embedding <=> $1::vector LIMIT $2
        """, query_embedding, top_k, *filter_params)

        return [SearchResult(document=VectorDocument(**dict(row)), score=row['score']) for row in rows]

# packages/forge-vectors/src/stores/qdrant.py

class QdrantStore(VectorStore):
    """Qdrant vector database"""

    async def search(self, query, top_k=10, filters=None) -> list[SearchResult]:
        query_embedding = await self.embedder.embed(query) if isinstance(query, str) else query
        results = self.client.search(
            collection_name="forge_vectors",
            query_vector=query_embedding,
            limit=top_k,
            query_filter=self._build_qdrant_filter(filters)
        )
        return [self._to_search_result(r) for r in results]

# Also: PineconeStore, WeaviateStore
```

### Embedder Implementations

```python
# packages/forge-vectors/src/embedders/

class OpenAIEmbedder(Embedder):
    def __init__(self, model: str = "text-embedding-3-small"):
        self.model = model
        self.client = AsyncOpenAI()

    async def embed(self, text: str) -> list[float]:
        response = await self.client.embeddings.create(model=self.model, input=text)
        return response.data[0].embedding

class SentenceTransformerEmbedder(Embedder):
    """Local embedding (no API)"""
    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        from sentence_transformers import SentenceTransformer
        self.model = SentenceTransformer(model)

    async def embed(self, text: str) -> list[float]:
        return self.model.encode(text).tolist()
```

### RAG Pipeline

```python
# packages/forge-vectors/src/rag/pipeline.py

class RAGPipeline:
    def __init__(self, vector_store: VectorStore, embedder: Embedder, chunker: ChunkingStrategy):
        self.store = vector_store
        self.embedder = embedder
        self.chunker = chunker

    async def index_object(self, obj: OntologyObject, fields_to_index: list[str]) -> None:
        text_content = "\n\n".join(f"{field}: {getattr(obj, field)}" for field in fields_to_index if getattr(obj, field))
        chunks = self.chunker.chunk(text_content)

        documents = [
            VectorDocument(
                id=f"{obj.object_type}:{obj.id}:chunk_{i}",
                content=chunk.content,
                ontology_id=obj.ontology_id,
                object_type=obj.object_type,
                object_id=obj.id
            )
            for i, chunk in enumerate(chunks)
        ]
        await self.store.upsert(documents)

    async def retrieve(self, query: str, ontology_id: str, object_types: list[str] | None = None, top_k: int = 5) -> list[RAGResult]:
        filters = {"ontology_id": ontology_id}
        if object_types:
            filters["object_type"] = {"$in": object_types}

        results = await self.store.search(query, top_k=top_k, filters=filters)
        return [RAGResult(content=r.document.content, score=r.score, object_type=r.document.object_type, object_id=r.document.object_id) for r in results]
```

---

## Guardrails & Security

### Guardrails Engine

```python
# packages/forge-ai-core/src/guardrails/engine.py

class GuardrailsEngine:
    """Apply safety guardrails to LLM inputs/outputs"""

    def __init__(self, config: GuardrailsConfig):
        self.pii_detector = PIIDetector(config.pii_patterns)
        self.topic_filter = TopicFilter(config.blocked_topics)
        self.injection_detector = InjectionDetector()

    async def filter_input(self, request: CompletionRequest) -> CompletionRequest:
        for message in request.messages:
            if message.role == "user":
                # Detect prompt injection
                if self.injection_detector.detect(message.content):
                    raise PromptInjectionError("Potential prompt injection detected")

                # Mask PII if configured
                message.content = self.pii_detector.mask(message.content)

        return request

    async def filter_output(self, response: CompletionResponse) -> CompletionResponse:
        # Check for blocked topics in output
        if self.topic_filter.contains_blocked(response.content):
            response.content = "[Content filtered due to policy violation]"

        # Mask any PII in output
        response.content = self.pii_detector.mask(response.content)

        return response

class PIIDetector:
    """Detect and mask personally identifiable information"""

    PATTERNS = {
        'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
        'phone': r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
        'ssn': r'\b\d{3}-\d{2}-\d{4}\b',
        'credit_card': r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
    }

    def mask(self, text: str) -> str:
        for pii_type, pattern in self.PATTERNS.items():
            text = re.sub(pattern, f'[{pii_type.upper()}_REDACTED]', text)
        return text

class InjectionDetector:
    """Detect prompt injection attempts"""

    INJECTION_PATTERNS = [
        r'ignore previous instructions',
        r'disregard all prior',
        r'you are now',
        r'new instructions:',
        r'system prompt:',
    ]

    def detect(self, text: str) -> bool:
        text_lower = text.lower()
        return any(re.search(p, text_lower) for p in self.INJECTION_PATTERNS)
```

### Audit Logging

```python
# packages/forge-ai-core/src/audit/logger.py

class AuditLogger:
    """Log all LLM interactions for compliance"""

    def __init__(self, store: AuditStore):
        self.store = store

    async def log(self, request: CompletionRequest, response: CompletionResponse) -> None:
        await self.store.save(AuditEntry(
            id=str(uuid4()),
            timestamp=datetime.utcnow(),
            model=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            latency_ms=response.latency_ms,
            request_hash=self._hash_request(request),  # Don't store raw prompts
            success=response.finish_reason != "error",
            user_id=get_current_user_id(),
            ontology_id=request.context.ontology_id if request.context else None,
        ))
```

---

## Forge Copilot (AI Assistant)

### Copilot Service

```python
# packages/forge-copilot/src/service.py

class ForgeCopilot:
    """AI assistant for the Forge platform"""

    def __init__(
        self,
        ai_client: ForgeAIClient,
        docs_index: VectorStore,
        code_index: VectorStore
    ):
        self.ai = ai_client
        self.docs_index = docs_index
        self.code_index = code_index

    async def ask(
        self,
        question: str,
        context_type: str = "general",  # 'general', 'code', 'ontology', 'pipeline'
        current_file: str | None = None
    ) -> CopilotResponse:
        # Retrieve relevant context
        if context_type == "code":
            context_docs = await self.code_index.search(question, top_k=5)
        else:
            context_docs = await self.docs_index.search(question, top_k=5)

        system_prompt = """You are Forge Copilot, an AI assistant for the Open Forge platform.
You help users with:
- Understanding and using the platform
- Writing ontology schemas
- Building data pipelines
- Creating Forge Logic functions
- Debugging issues

Be concise and provide code examples when helpful."""

        messages = [
            Message(role="system", content=system_prompt),
            Message(role="system", content=f"Relevant documentation:\n{self._format_context(context_docs)}"),
            Message(role="user", content=question)
        ]

        response = await self.ai.complete(CompletionRequest(
            model="gpt-4o",
            messages=messages
        ))

        return CopilotResponse(
            answer=response.content,
            sources=[d.metadata.get("source") for d in context_docs]
        )

    async def explain_code(self, code: str, language: str) -> str:
        """Explain what code does"""
        ...

    async def suggest_fix(self, code: str, error: str) -> str:
        """Suggest fix for error"""
        ...

    async def generate_code(self, description: str, language: str) -> str:
        """Generate code from description"""
        ...
```

---

## Forge ML (Model Operations)

### Model Registry

```python
# packages/forge-ml/src/registry.py

class ModelVersion(BaseModel):
    id: str
    model_id: str
    version: int
    artifact_path: str  # S3/MinIO path
    framework: str  # 'sklearn', 'pytorch', 'tensorflow', 'onnx'
    metrics: dict[str, float]
    parameters: dict
    created_at: datetime
    created_by: str
    stage: str = "development"  # 'development', 'staging', 'production'

class ModelRegistry:
    """Track and version ML models"""

    async def register(
        self,
        name: str,
        artifact: bytes | str,
        framework: str,
        metrics: dict,
        parameters: dict
    ) -> ModelVersion:
        model = await self._get_or_create_model(name)
        version = model.latest_version + 1

        artifact_path = await self._upload_artifact(model.id, version, artifact)

        return await self.store.create_version(ModelVersion(
            id=str(uuid4()),
            model_id=model.id,
            version=version,
            artifact_path=artifact_path,
            framework=framework,
            metrics=metrics,
            parameters=parameters,
            created_at=datetime.utcnow(),
            created_by=get_current_user_id()
        ))

    async def promote(self, model_id: str, version: int, stage: str) -> None:
        """Promote model version to stage"""
        ...

    async def load(self, model_id: str, version: int | None = None) -> Any:
        """Load model for inference"""
        ...
```

### Model Deployment

```python
# packages/forge-ml/src/deployment.py

class ModelDeployment(BaseModel):
    id: str
    model_id: str
    version: int
    deployment_type: str  # 'batch', 'realtime'
    endpoint_url: str | None = None
    status: str  # 'deploying', 'running', 'stopped', 'failed'
    replicas: int = 1
    resources: ResourceConfig

class ModelDeployer:
    """Deploy models for inference"""

    async def deploy_realtime(
        self,
        model_id: str,
        version: int,
        replicas: int = 1
    ) -> ModelDeployment:
        """Deploy model as REST endpoint"""
        model_version = await self.registry.get_version(model_id, version)

        # Create Kubernetes deployment
        deployment = await self.k8s.create_deployment(
            name=f"model-{model_id}-v{version}",
            image=self._get_serving_image(model_version.framework),
            env={"MODEL_PATH": model_version.artifact_path},
            replicas=replicas
        )

        # Create service
        service = await self.k8s.create_service(deployment.name)

        return ModelDeployment(
            id=str(uuid4()),
            model_id=model_id,
            version=version,
            deployment_type="realtime",
            endpoint_url=service.url,
            status="running",
            replicas=replicas
        )

    async def run_batch(
        self,
        model_id: str,
        version: int,
        input_dataset: str,
        output_dataset: str
    ) -> BatchJob:
        """Run batch inference"""
        ...
```

---

## Package Structure

```
packages/forge-ai-core/
├── src/
│   ├── __init__.py
│   ├── client.py                  # ForgeAIClient
│   ├── providers/
│   │   ├── base.py
│   │   ├── litellm_wrapper.py
│   │   └── models.py
│   ├── routing/
│   │   ├── router.py
│   │   └── fallback.py
│   ├── context/
│   │   ├── builder.py
│   │   └── tool_executor.py
│   ├── guardrails/
│   │   ├── engine.py
│   │   ├── pii.py
│   │   └── injection.py
│   ├── audit/
│   │   └── logger.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-logic/
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── executor.py
│   ├── validator.py
│   ├── storage.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-agent-builder/
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── compiler.py
│   ├── runtime.py
│   ├── tools/
│   │   ├── registry.py
│   │   └── builtin.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-evaluate/
├── src/
│   ├── __init__.py
│   ├── models.py
│   ├── runner.py
│   ├── evaluators/
│   │   ├── base.py
│   │   ├── exact_match.py
│   │   ├── semantic.py
│   │   ├── llm_judge.py
│   │   └── custom.py
│   ├── perturbations.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-copilot/
├── src/
│   ├── __init__.py
│   ├── service.py
│   ├── indexer.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-automate/
├── src/
│   ├── __init__.py
│   ├── workflow.py
│   ├── triggers.py
│   ├── scheduler.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-vectors/
├── src/
│   ├── __init__.py
│   ├── stores/
│   │   ├── base.py
│   │   ├── pgvector.py
│   │   ├── qdrant.py
│   │   ├── pinecone.py
│   │   └── weaviate.py
│   ├── embedders/
│   │   ├── base.py
│   │   ├── openai.py
│   │   └── sentence.py
│   ├── chunking/
│   │   └── strategies.py
│   ├── rag/
│   │   └── pipeline.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml

packages/forge-ml/
├── src/
│   ├── __init__.py
│   ├── registry.py
│   ├── deployment.py
│   ├── monitoring.py
│   └── api/
│       └── routes.py
├── tests/
└── pyproject.toml
```

---

## API Endpoints

```
/api/v1/ai/
│
├── completions/
│   ├── POST   /                    # Execute completion
│   └── POST   /stream              # Streaming completion
│
├── models/
│   ├── GET    /                    # List available models
│   └── GET    /:id                 # Get model details
│
├── logic/
│   ├── POST   /functions           # Create function
│   ├── GET    /functions           # List functions
│   ├── GET    /functions/:id       # Get function
│   ├── PATCH  /functions/:id       # Update function
│   ├── DELETE /functions/:id       # Delete function
│   ├── POST   /functions/:id/execute  # Execute function
│   └── POST   /functions/:id/publish  # Publish function
│
├── agents/
│   ├── POST   /                    # Create agent
│   ├── GET    /                    # List agents
│   ├── GET    /:id                 # Get agent
│   ├── PATCH  /:id                 # Update agent
│   ├── DELETE /:id                 # Delete agent
│   ├── POST   /:id/publish         # Publish agent
│   ├── POST   /:id/sessions        # Start session
│   ├── POST   /:id/sessions/:sid/message  # Send message
│   └── POST   /:id/sessions/:sid/approve  # Approve tool
│
├── evaluate/
│   ├── POST   /suites              # Create eval suite
│   ├── GET    /suites              # List suites
│   ├── GET    /suites/:id          # Get suite
│   ├── POST   /suites/:id/run      # Run evaluation
│   └── GET    /suites/:id/results  # Get results
│
├── vectors/
│   ├── POST   /index               # Index documents
│   ├── POST   /search              # Search vectors
│   └── DELETE /                    # Delete vectors
│
├── copilot/
│   ├── POST   /ask                 # Ask question
│   ├── POST   /explain             # Explain code
│   └── POST   /generate            # Generate code
│
└── ml/
    ├── models/
    │   ├── POST   /                # Register model
    │   ├── GET    /                # List models
    │   ├── GET    /:id             # Get model
    │   ├── GET    /:id/versions    # List versions
    │   └── POST   /:id/promote     # Promote version
    └── deployments/
        ├── POST   /                # Create deployment
        ├── GET    /                # List deployments
        ├── GET    /:id             # Get deployment
        └── DELETE /:id             # Delete deployment
```

---

## Implementation Roadmap

### Phase C1: AI Core + Vectors (Week 1-3)

| Package | Deliverables |
|---------|--------------|
| forge-ai-core | LiteLLM integration, context builder, guardrails, audit |
| forge-vectors | pgvector store, OpenAI embedder, RAG pipeline |

**Acceptance Criteria:**
- [ ] Multi-model completions via LiteLLM
- [ ] Ontology schema injection working
- [ ] RAG retrieval from pgvector
- [ ] PII detection and masking
- [ ] Audit logging to database

### Phase C2: Logic + Agent Builder (Week 4-6)

| Package | Deliverables |
|---------|--------------|
| forge-logic | Function model, executor, storage, API |
| forge-agent-builder | Agent model, compiler to LangGraph, runtime |

**Acceptance Criteria:**
- [ ] Create and execute no-code functions
- [ ] JSON schema output validation
- [ ] Visual agent compiles to working LangGraph
- [ ] Human-in-the-loop approval working
- [ ] Agent sessions with persistence

### Phase C3: Evaluate + Automate (Week 7-8)

| Package | Deliverables |
|---------|--------------|
| forge-evaluate | Evaluators, perturbations, suite runner |
| forge-automate | Workflow engine, triggers, scheduler |

**Acceptance Criteria:**
- [ ] Run eval suites with multiple evaluators
- [ ] LLM-as-judge working
- [ ] Perturbation testing generating variants
- [ ] Scheduled automation workflows

### Phase C4: Copilot + ML (Week 9-10)

| Package | Deliverables |
|---------|--------------|
| forge-copilot | Docs indexing, code assistance |
| forge-ml | Model registry, deployment |

**Acceptance Criteria:**
- [ ] Copilot answering platform questions
- [ ] Code explanation and generation
- [ ] Model versioning and promotion
- [ ] Batch and realtime deployment

---

## Dependencies

```toml
# packages/forge-ai-core/pyproject.toml

[project]
name = "forge-ai-core"
dependencies = [
    "litellm>=1.30",
    "pydantic>=2.0",
    "structlog>=24.0",
    "presidio-analyzer>=2.2",  # PII detection
    "presidio-anonymizer>=2.2",
]

# packages/forge-vectors/pyproject.toml

[project]
name = "forge-vectors"
dependencies = [
    "pgvector>=0.2",
    "asyncpg>=0.29",
    "openai>=1.0",
    "sentence-transformers>=2.2",
]

[project.optional-dependencies]
qdrant = ["qdrant-client>=1.7"]
pinecone = ["pinecone-client>=3.0"]
weaviate = ["weaviate-client>=4.0"]

# packages/forge-agent-builder/pyproject.toml

[project]
name = "forge-agent-builder"
dependencies = [
    "langgraph>=0.2",
    "langchain-core>=0.2",
]
```

---

## Next Steps

1. **Immediate**: Begin Phase C1 (forge-ai-core, forge-vectors)
2. **Parallel**: Can run alongside Track A (Connectors) and Track B (Data)
3. **Integration**: Connect to Forge Logic functions from Forge Studio
4. **Testing**: Build comprehensive eval suites for all AI features
