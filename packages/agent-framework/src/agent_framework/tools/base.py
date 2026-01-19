"""
Base tool definitions and utilities.
"""
from typing import Any, Callable, Optional, Type
from langchain_core.tools import BaseTool, StructuredTool
from pydantic import BaseModel, Field

def create_tool(
    name: str,
    description: str,
    func: Callable,
    args_schema: Optional[Type[BaseModel]] = None,
    return_direct: bool = False
) -> BaseTool:
    """Create a tool from a function."""
    return StructuredTool.from_function(
        func=func,
        name=name,
        description=description,
        args_schema=args_schema,
        return_direct=return_direct
    )

class WebSearchInput(BaseModel):
    """Input for web search tool."""
    query: str = Field(description="The search query")
    num_results: int = Field(default=5, description="Number of results to return")

class FileReadInput(BaseModel):
    """Input for file read tool."""
    path: str = Field(description="Path to the file to read")

class FileWriteInput(BaseModel):
    """Input for file write tool."""
    path: str = Field(description="Path to write the file")
    content: str = Field(description="Content to write")

class CodeExecutionInput(BaseModel):
    """Input for code execution tool."""
    code: str = Field(description="Python code to execute")
    timeout: int = Field(default=30, description="Timeout in seconds")