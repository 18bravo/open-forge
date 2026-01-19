"""
Open Forge Tool Components for Langflow

These components provide tools for interacting with Open Forge
infrastructure from within Langflow workflows.
"""

from langflow_components.tools.ontology_tool import OntologyToolComponent
from langflow_components.tools.pipeline_tool import PipelineToolComponent

__all__ = [
    "OntologyToolComponent",
    "PipelineToolComponent",
]
