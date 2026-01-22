"""
Git-like dataset branching.

Provides branch and commit abstractions for versioning datasets.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class BranchStatus(str, Enum):
    """Status of a branch."""

    ACTIVE = "active"
    MERGED = "merged"
    DELETED = "deleted"
    PROTECTED = "protected"


class Commit(BaseModel):
    """
    A commit representing a point-in-time snapshot of a dataset.

    Commits are immutable and identified by a unique hash.
    """

    id: str  # Commit hash
    branch_id: str
    dataset_id: str
    parent_id: str | None = None  # None for initial commit
    message: str
    author: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Snapshot reference (implementation-specific)
    snapshot_id: str | None = None  # Iceberg snapshot ID or Delta version

    # Statistics
    row_count: int | None = None
    size_bytes: int | None = None


class Branch(BaseModel):
    """
    A branch representing a line of development for a dataset.

    Branches allow parallel experimentation without affecting
    the main dataset.
    """

    id: str
    name: str
    dataset_id: str
    status: BranchStatus = BranchStatus.ACTIVE
    head_commit_id: str | None = None  # Current commit
    base_commit_id: str | None = None  # Commit branched from
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: str | None = None
    description: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    # Protection settings
    protected: bool = False
    require_review: bool = False


class BranchManager:
    """
    Manager for dataset branches.

    Provides operations for creating, listing, and managing branches
    with an underlying storage backend.

    Example:
        manager = BranchManager(backend=IcebergBackend(catalog))

        # Create a feature branch
        branch = await manager.create_branch(
            dataset_id="my_dataset",
            name="feature/new-schema",
            base_branch="main"
        )

        # Make changes and commit
        await manager.commit(
            branch_id=branch.id,
            message="Add new columns"
        )

        # Merge back to main
        result = await manager.merge(
            source_branch=branch.id,
            target_branch="main"
        )
    """

    def __init__(self, backend: "StorageBackend"):
        """
        Initialize the branch manager.

        Args:
            backend: Storage backend (Iceberg, Delta, etc.)
        """
        self.backend = backend
        self._branches: dict[str, Branch] = {}
        self._commits: dict[str, Commit] = {}

    async def create_branch(
        self,
        dataset_id: str,
        name: str,
        base_branch: str | None = None,
        description: str | None = None,
        created_by: str | None = None,
    ) -> Branch:
        """
        Create a new branch.

        Args:
            dataset_id: Dataset to branch
            name: Branch name
            base_branch: Branch to base from (default: main)
            description: Branch description
            created_by: User creating the branch

        Returns:
            The created Branch
        """
        import hashlib

        branch_id = hashlib.sha256(
            f"{dataset_id}:{name}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        # Get base commit from base branch
        base_commit_id = None
        if base_branch:
            base_branch_obj = await self.get_branch(dataset_id, base_branch)
            if base_branch_obj:
                base_commit_id = base_branch_obj.head_commit_id

        branch = Branch(
            id=branch_id,
            name=name,
            dataset_id=dataset_id,
            head_commit_id=base_commit_id,
            base_commit_id=base_commit_id,
            created_by=created_by,
            description=description,
        )

        self._branches[branch_id] = branch

        # Create branch in storage backend
        await self.backend.create_branch(dataset_id, branch)

        return branch

    async def get_branch(
        self,
        dataset_id: str,
        name: str,
    ) -> Branch | None:
        """
        Get a branch by name.

        Args:
            dataset_id: Dataset ID
            name: Branch name

        Returns:
            Branch if found, None otherwise
        """
        for branch in self._branches.values():
            if branch.dataset_id == dataset_id and branch.name == name:
                return branch
        return None

    async def list_branches(
        self,
        dataset_id: str,
        status: BranchStatus | None = None,
    ) -> list[Branch]:
        """
        List all branches for a dataset.

        Args:
            dataset_id: Dataset ID
            status: Filter by status (optional)

        Returns:
            List of branches
        """
        branches = [
            b for b in self._branches.values()
            if b.dataset_id == dataset_id
        ]

        if status:
            branches = [b for b in branches if b.status == status]

        return branches

    async def delete_branch(
        self,
        branch_id: str,
        force: bool = False,
    ) -> bool:
        """
        Delete a branch.

        Args:
            branch_id: Branch ID to delete
            force: Force delete even if not merged

        Returns:
            True if deleted
        """
        branch = self._branches.get(branch_id)
        if not branch:
            return False

        if branch.protected and not force:
            raise ValueError("Cannot delete protected branch")

        if branch.status != BranchStatus.MERGED and not force:
            raise ValueError("Branch has unmerged changes. Use force=True to delete.")

        branch.status = BranchStatus.DELETED
        branch.updated_at = datetime.utcnow()

        await self.backend.delete_branch(branch.dataset_id, branch)

        return True

    async def commit(
        self,
        branch_id: str,
        message: str,
        author: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Commit:
        """
        Create a commit on a branch.

        Args:
            branch_id: Branch ID
            message: Commit message
            author: Commit author
            metadata: Additional metadata

        Returns:
            The created Commit

        Note: This is a stub. Full implementation would:
        1. Capture current dataset state
        2. Create snapshot in storage backend
        3. Update branch head
        """
        import hashlib

        branch = self._branches.get(branch_id)
        if not branch:
            raise ValueError(f"Branch not found: {branch_id}")

        commit_id = hashlib.sha256(
            f"{branch_id}:{message}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:12]

        commit = Commit(
            id=commit_id,
            branch_id=branch_id,
            dataset_id=branch.dataset_id,
            parent_id=branch.head_commit_id,
            message=message,
            author=author or "unknown",
            metadata=metadata or {},
        )

        # Create snapshot in backend
        snapshot_id = await self.backend.create_snapshot(branch.dataset_id, commit)
        commit.snapshot_id = snapshot_id

        self._commits[commit_id] = commit

        # Update branch head
        branch.head_commit_id = commit_id
        branch.updated_at = datetime.utcnow()

        return commit

    async def get_commit(self, commit_id: str) -> Commit | None:
        """Get a commit by ID."""
        return self._commits.get(commit_id)

    async def list_commits(
        self,
        branch_id: str,
        limit: int = 50,
    ) -> list[Commit]:
        """
        List commits on a branch in reverse chronological order.

        Args:
            branch_id: Branch ID
            limit: Maximum commits to return

        Returns:
            List of commits
        """
        commits = [
            c for c in self._commits.values()
            if c.branch_id == branch_id
        ]
        commits.sort(key=lambda c: c.created_at, reverse=True)
        return commits[:limit]

    async def checkout(
        self,
        dataset_id: str,
        ref: str,
    ) -> None:
        """
        Checkout a branch or commit.

        Args:
            dataset_id: Dataset ID
            ref: Branch name or commit ID
        """
        # Try as branch name first
        branch = await self.get_branch(dataset_id, ref)
        if branch:
            await self.backend.checkout(dataset_id, branch.head_commit_id)
            return

        # Try as commit ID
        commit = await self.get_commit(ref)
        if commit and commit.dataset_id == dataset_id:
            await self.backend.checkout(dataset_id, ref)
            return

        raise ValueError(f"Unknown ref: {ref}")

    async def rollback(
        self,
        dataset_id: str,
        commit_id: str,
    ) -> Commit:
        """
        Rollback a dataset to a previous commit.

        Args:
            dataset_id: Dataset ID
            commit_id: Commit ID to rollback to

        Returns:
            New commit representing the rollback
        """
        # Get main branch
        main_branch = await self.get_branch(dataset_id, "main")
        if not main_branch:
            raise ValueError("Main branch not found")

        # Create rollback commit
        return await self.commit(
            branch_id=main_branch.id,
            message=f"Rollback to {commit_id}",
            metadata={"rollback_to": commit_id},
        )

    async def diff(
        self,
        commit_a: str,
        commit_b: str,
    ) -> dict[str, Any]:
        """
        Compare two commits.

        Args:
            commit_a: First commit ID
            commit_b: Second commit ID

        Returns:
            Diff information

        Note: This is a stub. Full implementation would compute
        actual data differences.
        """
        return {
            "commit_a": commit_a,
            "commit_b": commit_b,
            "rows_added": 0,
            "rows_removed": 0,
            "rows_modified": 0,
            "schema_changes": [],
        }
