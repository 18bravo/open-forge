"""
Code Generation API endpoints.

Provides endpoints for generating code artifacts from ontology definitions,
including FastAPI routers, ORM models, tests, and lifecycle hooks.
"""
from typing import List, Optional
from uuid import uuid4
from datetime import datetime
from enum import Enum
from io import BytesIO
import zipfile

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from api.dependencies import DbSession, CurrentUser, EventBusDep
from core.observability.tracing import traced, add_span_attribute


router = APIRouter(prefix="/codegen", tags=["Code Generation"])


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class GenerationTarget(str, Enum):
    """Code generation targets."""
    FASTAPI = "fastapi"
    ORM = "orm"
    TESTS = "tests"
    HOOKS = "hooks"
    PYDANTIC = "pydantic"
    GRAPHQL = "graphql"


class JobStatus(str, Enum):
    """Generation job status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TemplateCategory(str, Enum):
    """Template categories."""
    API = "api"
    DATABASE = "database"
    TESTING = "testing"
    INFRASTRUCTURE = "infrastructure"


# -----------------------------------------------------------------------------
# Pydantic Models - Requests
# -----------------------------------------------------------------------------

class GenerateRequest(BaseModel):
    """Request to generate code from an ontology."""
    ontology_id: str = Field(description="ID of the ontology to generate code from")
    targets: List[GenerationTarget] = Field(
        description="List of generation targets (fastapi, orm, tests, hooks, etc.)"
    )
    options: dict = Field(
        default_factory=dict,
        description="Additional generation options"
    )
    output_format: Optional[str] = Field(
        default="python",
        description="Output format (python, typescript, etc.)"
    )
    include_comments: bool = Field(
        default=True,
        description="Whether to include docstrings and comments"
    )
    dry_run: bool = Field(
        default=False,
        description="If true, validate but don't persist generated files"
    )


class PreviewRequest(BaseModel):
    """Request to preview generated code without saving."""
    ontology_id: str = Field(description="ID of the ontology to generate code from")
    target: GenerationTarget = Field(description="Single target to preview")
    entity_name: Optional[str] = Field(
        default=None,
        description="Specific entity to generate (optional, generates all if not specified)"
    )
    options: dict = Field(
        default_factory=dict,
        description="Additional generation options"
    )


# -----------------------------------------------------------------------------
# Pydantic Models - Responses
# -----------------------------------------------------------------------------

class GenerateResponse(BaseModel):
    """Response from code generation request."""
    job_id: str = Field(description="Unique job ID for tracking")
    status: JobStatus = Field(description="Current job status")
    message: str = Field(description="Status message")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    estimated_duration_seconds: Optional[int] = Field(
        default=None,
        description="Estimated time to complete"
    )


class PreviewResponse(BaseModel):
    """Response containing previewed code."""
    ontology_id: str = Field(description="Source ontology ID")
    target: GenerationTarget = Field(description="Generation target")
    entity_name: Optional[str] = Field(description="Entity name if specific entity was requested")
    code: str = Field(description="Generated code content")
    language: str = Field(description="Programming language")
    warnings: List[str] = Field(default_factory=list, description="Any warnings during generation")


class GeneratedFile(BaseModel):
    """Information about a generated file."""
    filename: str = Field(description="File name with path")
    size_bytes: int = Field(description="File size in bytes")
    target: GenerationTarget = Field(description="Generation target this file belongs to")
    entity_name: Optional[str] = Field(default=None, description="Entity name if applicable")
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class JobStatusResponse(BaseModel):
    """Status response for a generation job."""
    job_id: str = Field(description="Job ID")
    status: JobStatus = Field(description="Current status")
    progress_percent: int = Field(ge=0, le=100, description="Completion percentage")
    message: str = Field(description="Status message")
    started_at: Optional[datetime] = Field(default=None, description="Job start time")
    completed_at: Optional[datetime] = Field(default=None, description="Job completion time")
    files_generated: List[GeneratedFile] = Field(
        default_factory=list,
        description="List of generated files"
    )
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")
    warnings: List[str] = Field(default_factory=list, description="Any warnings")


class TemplateOption(BaseModel):
    """Option for a generation template."""
    name: str = Field(description="Option name")
    type: str = Field(description="Option type (string, boolean, number, select)")
    description: str = Field(description="Option description")
    default: Optional[str] = Field(default=None, description="Default value")
    choices: Optional[List[str]] = Field(default=None, description="Available choices for select type")
    required: bool = Field(default=False, description="Whether option is required")


class TemplateInfo(BaseModel):
    """Information about a generation template."""
    id: str = Field(description="Template ID")
    name: str = Field(description="Display name")
    description: str = Field(description="Template description")
    category: TemplateCategory = Field(description="Template category")
    targets: List[GenerationTarget] = Field(description="Supported generation targets")
    version: str = Field(description="Template version")
    options: List[TemplateOption] = Field(default_factory=list, description="Available options")
    languages: List[str] = Field(description="Supported output languages")
    created_at: datetime = Field(description="Template creation date")
    updated_at: datetime = Field(description="Last update date")


class TemplateListResponse(BaseModel):
    """Response containing list of templates."""
    templates: List[TemplateInfo] = Field(description="Available templates")
    total: int = Field(description="Total number of templates")


# -----------------------------------------------------------------------------
# In-memory job storage (would be replaced with proper storage in production)
# -----------------------------------------------------------------------------

_generation_jobs: dict[str, JobStatusResponse] = {}
_generated_files_content: dict[str, dict[str, str]] = {}  # job_id -> {filename: content}


# -----------------------------------------------------------------------------
# Background task functions
# -----------------------------------------------------------------------------

async def run_code_generation(
    job_id: str,
    ontology_id: str,
    targets: List[GenerationTarget],
    options: dict,
    event_bus: EventBusDep,
) -> None:
    """
    Background task to run code generation.

    In a real implementation, this would:
    1. Load the ontology from the database
    2. For each target, generate the appropriate code
    3. Save generated files to storage
    4. Update job status
    """
    import asyncio

    job = _generation_jobs.get(job_id)
    if not job:
        return

    try:
        job.status = JobStatus.RUNNING
        job.started_at = datetime.utcnow()
        job.message = "Generating code..."

        _generated_files_content[job_id] = {}
        total_targets = len(targets)

        for idx, target in enumerate(targets):
            # Simulate generation time
            await asyncio.sleep(0.5)

            # Generate mock files based on target
            if target == GenerationTarget.FASTAPI:
                filename = f"routers/{ontology_id}_router.py"
                content = _generate_mock_fastapi_code(ontology_id)
            elif target == GenerationTarget.ORM:
                filename = f"models/{ontology_id}_models.py"
                content = _generate_mock_orm_code(ontology_id)
            elif target == GenerationTarget.TESTS:
                filename = f"tests/test_{ontology_id}.py"
                content = _generate_mock_test_code(ontology_id)
            elif target == GenerationTarget.HOOKS:
                filename = f"hooks/{ontology_id}_hooks.py"
                content = _generate_mock_hooks_code(ontology_id)
            elif target == GenerationTarget.PYDANTIC:
                filename = f"schemas/{ontology_id}_schemas.py"
                content = _generate_mock_pydantic_code(ontology_id)
            elif target == GenerationTarget.GRAPHQL:
                filename = f"graphql/{ontology_id}_types.py"
                content = _generate_mock_graphql_code(ontology_id)
            else:
                continue

            _generated_files_content[job_id][filename] = content

            job.files_generated.append(GeneratedFile(
                filename=filename,
                size_bytes=len(content.encode('utf-8')),
                target=target,
                generated_at=datetime.utcnow()
            ))

            job.progress_percent = int(((idx + 1) / total_targets) * 100)
            job.message = f"Generated {target.value} ({idx + 1}/{total_targets})"

        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()
        job.message = f"Successfully generated {len(job.files_generated)} files"

        # Emit completion event
        await event_bus.publish(
            "codegen.job_completed",
            {
                "job_id": job_id,
                "ontology_id": ontology_id,
                "files_count": len(job.files_generated),
            }
        )

    except Exception as e:
        job.status = JobStatus.FAILED
        job.completed_at = datetime.utcnow()
        job.message = f"Generation failed: {str(e)}"
        job.errors.append(str(e))


def _generate_mock_fastapi_code(ontology_id: str) -> str:
    """Generate mock FastAPI router code."""
    return f'''"""
FastAPI router generated from ontology: {ontology_id}
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/{ontology_id}", tags=["{ontology_id.title()}"])


class {ontology_id.title()}Create(BaseModel):
    """Create request model."""
    name: str
    description: Optional[str] = None


class {ontology_id.title()}Response(BaseModel):
    """Response model."""
    id: str
    name: str
    description: Optional[str] = None


@router.post("", response_model={ontology_id.title()}Response)
async def create_{ontology_id}(data: {ontology_id.title()}Create):
    """Create a new {ontology_id}."""
    # TODO: Implement creation logic
    pass


@router.get("", response_model=List[{ontology_id.title()}Response])
async def list_{ontology_id}s():
    """List all {ontology_id}s."""
    # TODO: Implement listing logic
    pass


@router.get("/{{item_id}}", response_model={ontology_id.title()}Response)
async def get_{ontology_id}(item_id: str):
    """Get a specific {ontology_id}."""
    # TODO: Implement get logic
    pass


@router.delete("/{{item_id}}")
async def delete_{ontology_id}(item_id: str):
    """Delete a {ontology_id}."""
    # TODO: Implement deletion logic
    pass
'''


def _generate_mock_orm_code(ontology_id: str) -> str:
    """Generate mock SQLAlchemy ORM code."""
    return f'''"""
SQLAlchemy models generated from ontology: {ontology_id}
"""
from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from datetime import datetime

from core.database.base import Base


class {ontology_id.title()}(Base):
    """
    {ontology_id.title()} database model.

    Generated from ontology definition.
    """
    __tablename__ = "{ontology_id}s"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<{ontology_id.title()}(id={{self.id}}, name={{self.name}})>"
'''


def _generate_mock_test_code(ontology_id: str) -> str:
    """Generate mock test code."""
    return f'''"""
Tests for {ontology_id} endpoints.
"""
import pytest
from httpx import AsyncClient
from fastapi import status


@pytest.mark.asyncio
class Test{ontology_id.title()}Endpoints:
    """Test suite for {ontology_id} API endpoints."""

    async def test_create_{ontology_id}(self, client: AsyncClient):
        """Test creating a new {ontology_id}."""
        response = await client.post(
            "/{ontology_id}",
            json={{"name": "Test {ontology_id.title()}", "description": "Test description"}}
        )
        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert "id" in data
        assert data["name"] == "Test {ontology_id.title()}"

    async def test_list_{ontology_id}s(self, client: AsyncClient):
        """Test listing {ontology_id}s."""
        response = await client.get("/{ontology_id}")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)

    async def test_get_{ontology_id}_not_found(self, client: AsyncClient):
        """Test getting a non-existent {ontology_id}."""
        response = await client.get("/{ontology_id}/non-existent-id")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    async def test_delete_{ontology_id}(self, client: AsyncClient):
        """Test deleting a {ontology_id}."""
        # First create one
        create_response = await client.post(
            "/{ontology_id}",
            json={{"name": "To Delete"}}
        )
        item_id = create_response.json()["id"]

        # Then delete it
        delete_response = await client.delete(f"/{ontology_id}/{{item_id}}")
        assert delete_response.status_code == status.HTTP_204_NO_CONTENT
'''


def _generate_mock_hooks_code(ontology_id: str) -> str:
    """Generate mock lifecycle hooks code."""
    return f'''"""
Lifecycle hooks for {ontology_id}.
"""
from typing import Any, Dict, Optional
from datetime import datetime


class {ontology_id.title()}Hooks:
    """
    Lifecycle hooks for {ontology_id} entity.

    These hooks are called at various points in the entity lifecycle.
    """

    @staticmethod
    async def before_create(data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called before creating a new {ontology_id}.

        Args:
            data: The creation data

        Returns:
            Modified data to be used for creation
        """
        data["created_at"] = datetime.utcnow()
        return data

    @staticmethod
    async def after_create(entity: Any) -> None:
        """
        Called after successfully creating a {ontology_id}.

        Args:
            entity: The created entity
        """
        # TODO: Implement post-creation logic (e.g., send notifications)
        pass

    @staticmethod
    async def before_update(entity: Any, changes: Dict[str, Any]) -> Dict[str, Any]:
        """
        Called before updating a {ontology_id}.

        Args:
            entity: The existing entity
            changes: The proposed changes

        Returns:
            Modified changes to apply
        """
        changes["updated_at"] = datetime.utcnow()
        return changes

    @staticmethod
    async def after_update(entity: Any, old_values: Dict[str, Any]) -> None:
        """
        Called after successfully updating a {ontology_id}.

        Args:
            entity: The updated entity
            old_values: The previous values
        """
        # TODO: Implement post-update logic (e.g., audit logging)
        pass

    @staticmethod
    async def before_delete(entity: Any) -> bool:
        """
        Called before deleting a {ontology_id}.

        Args:
            entity: The entity to be deleted

        Returns:
            True to allow deletion, False to prevent
        """
        # TODO: Implement pre-deletion validation
        return True

    @staticmethod
    async def after_delete(entity_id: str, entity_data: Dict[str, Any]) -> None:
        """
        Called after successfully deleting a {ontology_id}.

        Args:
            entity_id: The ID of the deleted entity
            entity_data: Snapshot of the entity data before deletion
        """
        # TODO: Implement post-deletion logic (e.g., cascade cleanup)
        pass
'''


def _generate_mock_pydantic_code(ontology_id: str) -> str:
    """Generate mock Pydantic schema code."""
    return f'''"""
Pydantic schemas for {ontology_id}.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class {ontology_id.title()}Base(BaseModel):
    """Base schema with shared attributes."""
    name: str = Field(min_length=1, max_length=255, description="Name of the {ontology_id}")
    description: Optional[str] = Field(default=None, max_length=2000, description="Description")


class {ontology_id.title()}Create({ontology_id.title()}Base):
    """Schema for creating a {ontology_id}."""
    pass


class {ontology_id.title()}Update(BaseModel):
    """Schema for updating a {ontology_id}."""
    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=2000)


class {ontology_id.title()}Response({ontology_id.title()}Base):
    """Schema for {ontology_id} responses."""
    id: str = Field(description="Unique identifier")
    created_at: datetime = Field(description="Creation timestamp")
    updated_at: datetime = Field(description="Last update timestamp")

    model_config = {{"from_attributes": True}}


class {ontology_id.title()}List(BaseModel):
    """Schema for paginated list of {ontology_id}s."""
    items: List[{ontology_id.title()}Response]
    total: int
    page: int
    page_size: int
'''


def _generate_mock_graphql_code(ontology_id: str) -> str:
    """Generate mock GraphQL type code."""
    return f'''"""
GraphQL types for {ontology_id}.
"""
import strawberry
from typing import Optional, List
from datetime import datetime


@strawberry.type
class {ontology_id.title()}Type:
    """GraphQL type for {ontology_id}."""
    id: str
    name: str
    description: Optional[str]
    created_at: datetime
    updated_at: datetime


@strawberry.input
class {ontology_id.title()}CreateInput:
    """Input type for creating a {ontology_id}."""
    name: str
    description: Optional[str] = None


@strawberry.input
class {ontology_id.title()}UpdateInput:
    """Input type for updating a {ontology_id}."""
    name: Optional[str] = None
    description: Optional[str] = None


@strawberry.type
class {ontology_id.title()}Connection:
    """Connection type for paginated {ontology_id} queries."""
    items: List[{ontology_id.title()}Type]
    total_count: int
    has_next_page: bool
    has_previous_page: bool
'''


# -----------------------------------------------------------------------------
# Endpoints
# -----------------------------------------------------------------------------

@router.post(
    "/generate",
    response_model=GenerateResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Generate code from ontology",
    description="Triggers code generation for selected targets based on ontology definition"
)
@traced("codegen.generate")
async def generate_code(
    request: GenerateRequest,
    background_tasks: BackgroundTasks,
    db: DbSession,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> GenerateResponse:
    """
    Trigger code generation from an ontology.

    Accepts an ontology ID and list of generation targets (FastAPI, ORM, tests, hooks, etc.)
    and returns a job ID for tracking the async generation process.
    """
    add_span_attribute("codegen.ontology_id", request.ontology_id)
    add_span_attribute("codegen.targets", [t.value for t in request.targets])
    add_span_attribute("codegen.dry_run", request.dry_run)
    add_span_attribute("user.id", user.user_id)

    # Validate ontology exists
    # TODO: Actually fetch and validate ontology from database
    if not request.ontology_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ontology_id is required"
        )

    if not request.targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least one generation target is required"
        )

    # Create job record
    job_id = str(uuid4())
    job = JobStatusResponse(
        job_id=job_id,
        status=JobStatus.PENDING,
        progress_percent=0,
        message="Job queued for processing",
        files_generated=[],
        errors=[],
        warnings=[]
    )
    _generation_jobs[job_id] = job

    # Queue background task (unless dry run)
    if not request.dry_run:
        background_tasks.add_task(
            run_code_generation,
            job_id,
            request.ontology_id,
            request.targets,
            request.options,
            event_bus
        )
    else:
        job.message = "Dry run - validation passed, no files generated"
        job.status = JobStatus.COMPLETED
        job.completed_at = datetime.utcnow()

    # Emit event
    await event_bus.publish(
        "codegen.job_created",
        {
            "job_id": job_id,
            "ontology_id": request.ontology_id,
            "targets": [t.value for t in request.targets],
            "user_id": user.user_id,
        }
    )

    return GenerateResponse(
        job_id=job_id,
        status=job.status,
        message=job.message,
        estimated_duration_seconds=len(request.targets) * 2  # Rough estimate
    )


@router.post(
    "/preview",
    response_model=PreviewResponse,
    summary="Preview generated code",
    description="Preview generated code without saving to storage"
)
@traced("codegen.preview")
async def preview_code(
    request: PreviewRequest,
    db: DbSession,
    user: CurrentUser,
) -> PreviewResponse:
    """
    Preview generated code without saving.

    Generates code for a single target and returns it as a string
    for display in the UI. Does not persist any files.
    """
    add_span_attribute("codegen.ontology_id", request.ontology_id)
    add_span_attribute("codegen.target", request.target.value)
    add_span_attribute("codegen.entity_name", request.entity_name)
    add_span_attribute("user.id", user.user_id)

    # Validate ontology exists
    # TODO: Actually fetch and validate ontology from database
    if not request.ontology_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ontology_id is required"
        )

    # Generate preview based on target
    warnings = []

    if request.target == GenerationTarget.FASTAPI:
        code = _generate_mock_fastapi_code(request.ontology_id)
    elif request.target == GenerationTarget.ORM:
        code = _generate_mock_orm_code(request.ontology_id)
    elif request.target == GenerationTarget.TESTS:
        code = _generate_mock_test_code(request.ontology_id)
    elif request.target == GenerationTarget.HOOKS:
        code = _generate_mock_hooks_code(request.ontology_id)
    elif request.target == GenerationTarget.PYDANTIC:
        code = _generate_mock_pydantic_code(request.ontology_id)
    elif request.target == GenerationTarget.GRAPHQL:
        code = _generate_mock_graphql_code(request.ontology_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported generation target: {request.target}"
        )

    return PreviewResponse(
        ontology_id=request.ontology_id,
        target=request.target,
        entity_name=request.entity_name,
        code=code,
        language="python",
        warnings=warnings
    )


@router.get(
    "/status/{job_id}",
    response_model=JobStatusResponse,
    summary="Get generation job status",
    description="Returns the current status and progress of a generation job"
)
@traced("codegen.status")
async def get_job_status(
    job_id: str,
    user: CurrentUser,
) -> JobStatusResponse:
    """
    Get the status of a code generation job.

    Returns progress percentage, completed files, and any errors.
    """
    add_span_attribute("codegen.job_id", job_id)
    add_span_attribute("user.id", user.user_id)

    job = _generation_jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    return job


@router.get(
    "/download/{job_id}",
    summary="Download generated files",
    description="Download all generated files as a ZIP archive"
)
@traced("codegen.download")
async def download_generated_files(
    job_id: str,
    user: CurrentUser,
) -> StreamingResponse:
    """
    Download generated files as a ZIP archive.

    Only available for completed jobs. Returns a ZIP file containing
    all generated artifacts.
    """
    add_span_attribute("codegen.job_id", job_id)
    add_span_attribute("user.id", user.user_id)

    job = _generation_jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed. Current status: {job.status.value}"
        )

    files_content = _generated_files_content.get(job_id, {})
    if not files_content:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Generated files not found. They may have been cleaned up."
        )

    # Create ZIP file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for filename, content in files_content.items():
            zip_file.writestr(filename, content)

    zip_buffer.seek(0)

    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename=codegen_{job_id}.zip"
        }
    )


@router.get(
    "/templates",
    response_model=TemplateListResponse,
    summary="List generation templates",
    description="Returns available code generation templates and their options"
)
@traced("codegen.templates")
async def list_templates(
    user: CurrentUser,
    category: Optional[TemplateCategory] = Query(default=None, description="Filter by category"),
) -> TemplateListResponse:
    """
    List available code generation templates.

    Returns template metadata including supported targets, options,
    and output languages.
    """
    add_span_attribute("user.id", user.user_id)
    add_span_attribute("filter.category", category.value if category else None)

    now = datetime.utcnow()

    # Return mock templates - would be loaded from configuration/database
    templates = [
        TemplateInfo(
            id="fastapi-crud",
            name="FastAPI CRUD Router",
            description="Generate complete CRUD endpoints with validation and error handling",
            category=TemplateCategory.API,
            targets=[GenerationTarget.FASTAPI, GenerationTarget.PYDANTIC],
            version="1.0.0",
            options=[
                TemplateOption(
                    name="include_pagination",
                    type="boolean",
                    description="Include pagination for list endpoints",
                    default="true"
                ),
                TemplateOption(
                    name="auth_required",
                    type="boolean",
                    description="Require authentication for all endpoints",
                    default="true"
                ),
            ],
            languages=["python"],
            created_at=now,
            updated_at=now
        ),
        TemplateInfo(
            id="sqlalchemy-models",
            name="SQLAlchemy ORM Models",
            description="Generate SQLAlchemy models with relationships and migrations",
            category=TemplateCategory.DATABASE,
            targets=[GenerationTarget.ORM],
            version="1.0.0",
            options=[
                TemplateOption(
                    name="include_timestamps",
                    type="boolean",
                    description="Include created_at and updated_at columns",
                    default="true"
                ),
                TemplateOption(
                    name="soft_delete",
                    type="boolean",
                    description="Use soft delete pattern",
                    default="false"
                ),
            ],
            languages=["python"],
            created_at=now,
            updated_at=now
        ),
        TemplateInfo(
            id="pytest-suite",
            name="Pytest Test Suite",
            description="Generate comprehensive pytest tests with fixtures",
            category=TemplateCategory.TESTING,
            targets=[GenerationTarget.TESTS],
            version="1.0.0",
            options=[
                TemplateOption(
                    name="include_fixtures",
                    type="boolean",
                    description="Generate shared fixtures",
                    default="true"
                ),
                TemplateOption(
                    name="coverage_target",
                    type="select",
                    description="Target code coverage level",
                    default="80",
                    choices=["60", "70", "80", "90", "100"]
                ),
            ],
            languages=["python"],
            created_at=now,
            updated_at=now
        ),
        TemplateInfo(
            id="lifecycle-hooks",
            name="Lifecycle Hooks",
            description="Generate entity lifecycle hooks for validation and side effects",
            category=TemplateCategory.API,
            targets=[GenerationTarget.HOOKS],
            version="1.0.0",
            options=[
                TemplateOption(
                    name="async_hooks",
                    type="boolean",
                    description="Generate async hooks",
                    default="true"
                ),
            ],
            languages=["python"],
            created_at=now,
            updated_at=now
        ),
        TemplateInfo(
            id="graphql-types",
            name="GraphQL Types (Strawberry)",
            description="Generate Strawberry GraphQL types and resolvers",
            category=TemplateCategory.API,
            targets=[GenerationTarget.GRAPHQL],
            version="1.0.0",
            options=[
                TemplateOption(
                    name="include_mutations",
                    type="boolean",
                    description="Generate mutation types",
                    default="true"
                ),
                TemplateOption(
                    name="include_subscriptions",
                    type="boolean",
                    description="Generate subscription types",
                    default="false"
                ),
            ],
            languages=["python"],
            created_at=now,
            updated_at=now
        ),
    ]

    # Filter by category if specified
    if category:
        templates = [t for t in templates if t.category == category]

    return TemplateListResponse(
        templates=templates,
        total=len(templates)
    )


@router.delete(
    "/jobs/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel or delete a job",
    description="Cancel a running job or delete a completed job"
)
@traced("codegen.delete_job")
async def delete_job(
    job_id: str,
    user: CurrentUser,
    event_bus: EventBusDep,
) -> None:
    """
    Cancel a running job or delete a completed job.

    If the job is running, it will be cancelled. If completed, the job
    record and generated files will be removed.
    """
    add_span_attribute("codegen.job_id", job_id)
    add_span_attribute("user.id", user.user_id)

    job = _generation_jobs.get(job_id)
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    # If running, mark as cancelled
    if job.status == JobStatus.RUNNING:
        job.status = JobStatus.CANCELLED
        job.message = "Job cancelled by user"
        job.completed_at = datetime.utcnow()

        await event_bus.publish(
            "codegen.job_cancelled",
            {
                "job_id": job_id,
                "user_id": user.user_id,
            }
        )

    # Clean up job and files
    _generation_jobs.pop(job_id, None)
    _generated_files_content.pop(job_id, None)
