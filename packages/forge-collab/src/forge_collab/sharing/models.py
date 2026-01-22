"""Sharing models - Permission levels and resource types."""

from enum import Enum


class PermissionLevel(str, Enum):
    """Permission levels for access control."""

    NONE = "none"
    VIEW = "view"
    EDIT = "edit"
    MANAGE = "manage"
    OWNER = "owner"


class ResourceType(str, Enum):
    """Resource types that can have permissions."""

    DATASET = "dataset"
    ONTOLOGY = "ontology"
    PIPELINE = "pipeline"
    APP = "app"
    COLLECTION = "collection"
    WORKSPACE = "workspace"
    DASHBOARD = "dashboard"
    REPORT = "report"
