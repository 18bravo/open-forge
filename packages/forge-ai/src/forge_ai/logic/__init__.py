"""
Logic module - No-code LLM function definitions and execution.

This module provides:
- LogicFunction: No-code LLM function definitions
- FunctionBuilder: Visual function builder support
- FunctionExecutor: Function execution engine
"""

from forge_ai.logic.functions import (
    LogicFunction,
    VariableBinding,
    OutputField,
    LogicFunctionResult,
)
from forge_ai.logic.builder import FunctionBuilder
from forge_ai.logic.execution import FunctionExecutor

__all__ = [
    "LogicFunction",
    "VariableBinding",
    "OutputField",
    "LogicFunctionResult",
    "FunctionBuilder",
    "FunctionExecutor",
]
