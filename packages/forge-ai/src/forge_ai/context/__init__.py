"""
Context module - Ontology context injection and RAG retrieval.

This module provides:
- ContextBuilder: Builds ontology-aware context for LLM requests
- ContextConfig: Configuration for context injection
- RAG integration for retrieval-augmented generation
"""

from forge_ai.context.builder import (
    ContextBuilder,
    ContextConfig,
    OntologyContext,
)
from forge_ai.context.ontology import (
    OntologyClient,
    OntologySchema,
    OntologyObject,
)
from forge_ai.context.rag import (
    RAGRetriever,
    RAGConfig,
    RAGResult,
)

__all__ = [
    "ContextBuilder",
    "ContextConfig",
    "OntologyContext",
    "OntologyClient",
    "OntologySchema",
    "OntologyObject",
    "RAGRetriever",
    "RAGConfig",
    "RAGResult",
]
