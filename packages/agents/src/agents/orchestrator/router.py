"""
Task Router for Orchestrator

Intelligent routing of tasks to agent clusters with load balancing
and priority queue management.
"""
from typing import Any, Callable, Dict, List, Optional, Set
from enum import Enum
from datetime import datetime
import asyncio
import heapq
from dataclasses import dataclass, field
from pydantic import BaseModel, Field

from agents.orchestrator.phase_manager import EngagementPhase


class AgentCluster(str, Enum):
    """Available agent clusters."""
    DISCOVERY = "discovery"
    DATA_ARCHITECT = "data_architect"
    APP_BUILDER = "app_builder"


class TaskPriority(int, Enum):
    """Task priority levels (lower number = higher priority)."""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


class TaskStatus(str, Enum):
    """Task execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    BLOCKED = "blocked"


class TaskType(str, Enum):
    """Types of tasks that can be routed."""
    # Discovery cluster tasks
    STAKEHOLDER_ANALYSIS = "stakeholder_analysis"
    SOURCE_DISCOVERY = "source_discovery"
    REQUIREMENTS_GATHERING = "requirements_gathering"

    # Data Architect cluster tasks
    ONTOLOGY_DESIGN = "ontology_design"
    SCHEMA_VALIDATION = "schema_validation"
    DATA_TRANSFORMATION = "data_transformation"

    # App Builder cluster tasks
    UI_GENERATION = "ui_generation"
    WORKFLOW_AUTOMATION = "workflow_automation"
    INTEGRATION_SETUP = "integration_setup"
    DEPLOYMENT_CONFIG = "deployment_config"


# Mapping of task types to agent clusters
TASK_CLUSTER_MAPPING: Dict[TaskType, AgentCluster] = {
    # Discovery tasks
    TaskType.STAKEHOLDER_ANALYSIS: AgentCluster.DISCOVERY,
    TaskType.SOURCE_DISCOVERY: AgentCluster.DISCOVERY,
    TaskType.REQUIREMENTS_GATHERING: AgentCluster.DISCOVERY,

    # Data Architect tasks
    TaskType.ONTOLOGY_DESIGN: AgentCluster.DATA_ARCHITECT,
    TaskType.SCHEMA_VALIDATION: AgentCluster.DATA_ARCHITECT,
    TaskType.DATA_TRANSFORMATION: AgentCluster.DATA_ARCHITECT,

    # App Builder tasks
    TaskType.UI_GENERATION: AgentCluster.APP_BUILDER,
    TaskType.WORKFLOW_AUTOMATION: AgentCluster.APP_BUILDER,
    TaskType.INTEGRATION_SETUP: AgentCluster.APP_BUILDER,
    TaskType.DEPLOYMENT_CONFIG: AgentCluster.APP_BUILDER,
}

# Mapping of phases to primary clusters
PHASE_CLUSTER_MAPPING: Dict[EngagementPhase, List[AgentCluster]] = {
    EngagementPhase.DISCOVERY: [AgentCluster.DISCOVERY],
    EngagementPhase.DESIGN: [AgentCluster.DATA_ARCHITECT],
    EngagementPhase.BUILD: [AgentCluster.DATA_ARCHITECT, AgentCluster.APP_BUILDER],
    EngagementPhase.DEPLOY: [AgentCluster.APP_BUILDER],
    EngagementPhase.COMPLETE: [],
}


class Task(BaseModel):
    """A task to be routed and executed."""
    task_id: str
    task_type: TaskType
    engagement_id: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    context: Dict[str, Any] = Field(default_factory=dict)
    dependencies: List[str] = Field(default_factory=list)  # Task IDs this depends on
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    assigned_cluster: Optional[AgentCluster] = None
    assigned_agent: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


@dataclass(order=True)
class PrioritizedTask:
    """Wrapper for heap queue ordering."""
    priority: int
    created_at: datetime = field(compare=False)
    task: Task = field(compare=False)


class AgentStatus(BaseModel):
    """Status of an agent in a cluster."""
    agent_name: str
    cluster: AgentCluster
    is_available: bool = True
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_active: Optional[datetime] = None
    capabilities: Set[TaskType] = Field(default_factory=set)


class ClusterStatus(BaseModel):
    """Status of an agent cluster."""
    cluster: AgentCluster
    agents: Dict[str, AgentStatus] = Field(default_factory=dict)
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    is_healthy: bool = True


class TaskRouter:
    """
    Routes tasks to appropriate agent clusters with load balancing.

    Responsibilities:
    - Route tasks based on type and context
    - Manage priority queues per cluster
    - Load balance across agents
    - Track task dependencies
    - Handle retries and failures
    """

    def __init__(self, engagement_id: str):
        self.engagement_id = engagement_id

        # Task queues per cluster (using heaps for priority)
        self._queues: Dict[AgentCluster, List[PrioritizedTask]] = {
            cluster: [] for cluster in AgentCluster
        }

        # All tasks by ID
        self._tasks: Dict[str, Task] = {}

        # Completed tasks tracking
        self._completed_tasks: Set[str] = set()

        # Cluster and agent statuses
        self._cluster_statuses: Dict[AgentCluster, ClusterStatus] = {
            cluster: ClusterStatus(cluster=cluster) for cluster in AgentCluster
        }

        # Task completion callbacks
        self._callbacks: Dict[str, List[Callable]] = {}

        # Lock for thread-safe operations
        self._lock = asyncio.Lock()

    def register_agent(
        self,
        agent_name: str,
        cluster: AgentCluster,
        capabilities: Optional[Set[TaskType]] = None
    ) -> None:
        """Register an agent with a cluster."""
        agent_status = AgentStatus(
            agent_name=agent_name,
            cluster=cluster,
            capabilities=capabilities or set()
        )
        self._cluster_statuses[cluster].agents[agent_name] = agent_status

    def unregister_agent(self, agent_name: str, cluster: AgentCluster) -> None:
        """Unregister an agent from a cluster."""
        if agent_name in self._cluster_statuses[cluster].agents:
            del self._cluster_statuses[cluster].agents[agent_name]

    def get_cluster_for_task(self, task_type: TaskType) -> AgentCluster:
        """Determine which cluster should handle a task type."""
        return TASK_CLUSTER_MAPPING.get(task_type, AgentCluster.DISCOVERY)

    def get_clusters_for_phase(self, phase: EngagementPhase) -> List[AgentCluster]:
        """Get the primary clusters for a phase."""
        return PHASE_CLUSTER_MAPPING.get(phase, [])

    async def submit_task(
        self,
        task_id: str,
        task_type: TaskType,
        context: Optional[Dict[str, Any]] = None,
        priority: TaskPriority = TaskPriority.NORMAL,
        dependencies: Optional[List[str]] = None,
        callback: Optional[Callable] = None
    ) -> Task:
        """
        Submit a task for routing.

        Args:
            task_id: Unique identifier for the task
            task_type: Type of task
            context: Task context/input data
            priority: Task priority
            dependencies: List of task IDs this task depends on
            callback: Optional callback when task completes

        Returns:
            The submitted task
        """
        async with self._lock:
            # Create task
            task = Task(
                task_id=task_id,
                task_type=task_type,
                engagement_id=self.engagement_id,
                priority=priority,
                context=context or {},
                dependencies=dependencies or []
            )

            # Determine target cluster
            cluster = self.get_cluster_for_task(task_type)
            task.assigned_cluster = cluster

            # Store task
            self._tasks[task_id] = task

            # Register callback
            if callback:
                if task_id not in self._callbacks:
                    self._callbacks[task_id] = []
                self._callbacks[task_id].append(callback)

            # Check if dependencies are met
            if self._dependencies_met(task):
                task.status = TaskStatus.QUEUED
                self._enqueue_task(task, cluster)
            else:
                task.status = TaskStatus.BLOCKED

            # Update cluster status
            self._cluster_statuses[cluster].pending_tasks += 1

            return task

    def _dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self._completed_tasks:
                return False
        return True

    def _enqueue_task(self, task: Task, cluster: AgentCluster) -> None:
        """Add task to the cluster queue."""
        prioritized = PrioritizedTask(
            priority=task.priority.value,
            created_at=task.created_at,
            task=task
        )
        heapq.heappush(self._queues[cluster], prioritized)

    async def get_next_task(
        self,
        cluster: AgentCluster,
        agent_name: Optional[str] = None,
        capabilities: Optional[Set[TaskType]] = None
    ) -> Optional[Task]:
        """
        Get the next task for a cluster/agent.

        Args:
            cluster: The agent cluster
            agent_name: Optional specific agent name
            capabilities: Optional set of task types the agent can handle

        Returns:
            Next task to execute, or None if queue is empty
        """
        async with self._lock:
            queue = self._queues[cluster]

            if not queue:
                return None

            # Find a suitable task
            suitable_task = None
            temp_items = []

            while queue:
                prioritized = heapq.heappop(queue)
                task = prioritized.task

                # Check if agent can handle this task type
                if capabilities and task.task_type not in capabilities:
                    temp_items.append(prioritized)
                    continue

                # Check dependencies again (might have changed)
                if not self._dependencies_met(task):
                    task.status = TaskStatus.BLOCKED
                    temp_items.append(prioritized)
                    continue

                suitable_task = task
                break

            # Put back items we skipped
            for item in temp_items:
                heapq.heappush(queue, item)

            if suitable_task:
                suitable_task.status = TaskStatus.RUNNING
                suitable_task.started_at = datetime.utcnow()
                suitable_task.assigned_agent = agent_name

                # Update agent status
                if agent_name and agent_name in self._cluster_statuses[cluster].agents:
                    agent_status = self._cluster_statuses[cluster].agents[agent_name]
                    agent_status.is_available = False
                    agent_status.current_task = suitable_task.task_id
                    agent_status.last_active = datetime.utcnow()

                # Update cluster counts
                self._cluster_statuses[cluster].pending_tasks -= 1
                self._cluster_statuses[cluster].running_tasks += 1

            return suitable_task

    async def complete_task(
        self,
        task_id: str,
        result: Dict[str, Any],
        success: bool = True,
        error: Optional[str] = None
    ) -> None:
        """
        Mark a task as completed.

        Args:
            task_id: The task ID
            result: Task result/output
            success: Whether task succeeded
            error: Error message if failed
        """
        async with self._lock:
            if task_id not in self._tasks:
                return

            task = self._tasks[task_id]
            task.completed_at = datetime.utcnow()
            task.result = result

            if success:
                task.status = TaskStatus.COMPLETED
                self._completed_tasks.add(task_id)
            else:
                task.error = error
                if task.retry_count < task.max_retries:
                    # Retry the task
                    task.retry_count += 1
                    task.status = TaskStatus.QUEUED
                    task.started_at = None
                    self._enqueue_task(task, task.assigned_cluster)
                else:
                    task.status = TaskStatus.FAILED

            # Update cluster status
            cluster = task.assigned_cluster
            if cluster:
                self._cluster_statuses[cluster].running_tasks -= 1
                if success:
                    self._cluster_statuses[cluster].completed_tasks += 1

                # Update agent status
                if task.assigned_agent and task.assigned_agent in self._cluster_statuses[cluster].agents:
                    agent_status = self._cluster_statuses[cluster].agents[task.assigned_agent]
                    agent_status.is_available = True
                    agent_status.current_task = None
                    if success:
                        agent_status.tasks_completed += 1
                    else:
                        agent_status.tasks_failed += 1

            # Unblock dependent tasks
            if success:
                await self._unblock_dependent_tasks(task_id)

            # Execute callbacks
            if task_id in self._callbacks:
                for callback in self._callbacks[task_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(task)
                        else:
                            callback(task)
                    except Exception as e:
                        print(f"Callback error for task {task_id}: {e}")

    async def _unblock_dependent_tasks(self, completed_task_id: str) -> None:
        """Unblock tasks that were waiting on the completed task."""
        for task in self._tasks.values():
            if task.status == TaskStatus.BLOCKED:
                if completed_task_id in task.dependencies:
                    if self._dependencies_met(task):
                        task.status = TaskStatus.QUEUED
                        self._enqueue_task(task, task.assigned_cluster)

    async def cancel_task(self, task_id: str, reason: Optional[str] = None) -> bool:
        """Cancel a pending or queued task."""
        async with self._lock:
            if task_id not in self._tasks:
                return False

            task = self._tasks[task_id]

            if task.status in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]:
                return False

            if task.status == TaskStatus.RUNNING:
                # Can't cancel running task directly
                return False

            task.status = TaskStatus.CANCELLED
            task.error = reason or "Task cancelled"
            task.completed_at = datetime.utcnow()

            # Update cluster status
            if task.assigned_cluster:
                self._cluster_statuses[task.assigned_cluster].pending_tasks -= 1

            return True

    def get_task(self, task_id: str) -> Optional[Task]:
        """Get a task by ID."""
        return self._tasks.get(task_id)

    def get_tasks_by_status(self, status: TaskStatus) -> List[Task]:
        """Get all tasks with a specific status."""
        return [t for t in self._tasks.values() if t.status == status]

    def get_cluster_status(self, cluster: AgentCluster) -> ClusterStatus:
        """Get the status of a cluster."""
        return self._cluster_statuses[cluster]

    def get_available_agents(self, cluster: AgentCluster) -> List[str]:
        """Get available agents in a cluster."""
        return [
            name for name, status in self._cluster_statuses[cluster].agents.items()
            if status.is_available
        ]

    def get_routing_summary(self) -> Dict[str, Any]:
        """Get a summary of current routing state."""
        return {
            "engagement_id": self.engagement_id,
            "total_tasks": len(self._tasks),
            "completed_tasks": len(self._completed_tasks),
            "tasks_by_status": {
                status.value: len(self.get_tasks_by_status(status))
                for status in TaskStatus
            },
            "clusters": {
                cluster.value: {
                    "pending": self._cluster_statuses[cluster].pending_tasks,
                    "running": self._cluster_statuses[cluster].running_tasks,
                    "completed": self._cluster_statuses[cluster].completed_tasks,
                    "agents": len(self._cluster_statuses[cluster].agents),
                    "available_agents": len(self.get_available_agents(cluster)),
                    "queue_depth": len(self._queues[cluster])
                }
                for cluster in AgentCluster
            }
        }

    async def get_next_work_batch(
        self,
        cluster: AgentCluster,
        max_tasks: int = 5
    ) -> List[Task]:
        """
        Get a batch of tasks for parallel execution.

        Args:
            cluster: Target cluster
            max_tasks: Maximum tasks to return

        Returns:
            List of tasks that can be executed in parallel
        """
        tasks = []
        for _ in range(max_tasks):
            task = await self.get_next_task(cluster)
            if task:
                tasks.append(task)
            else:
                break
        return tasks

    def suggest_task_priority(
        self,
        task_type: TaskType,
        phase: EngagementPhase,
        context: Optional[Dict[str, Any]] = None
    ) -> TaskPriority:
        """
        Suggest priority for a task based on context.

        Args:
            task_type: Type of task
            phase: Current engagement phase
            context: Task context

        Returns:
            Suggested priority
        """
        # Phase-appropriate tasks get higher priority
        primary_clusters = self.get_clusters_for_phase(phase)
        task_cluster = self.get_cluster_for_task(task_type)

        if task_cluster in primary_clusters:
            return TaskPriority.HIGH

        # Check context for urgency indicators
        if context:
            if context.get("urgent"):
                return TaskPriority.CRITICAL
            if context.get("blocking"):
                return TaskPriority.HIGH
            if context.get("background"):
                return TaskPriority.BACKGROUND

        return TaskPriority.NORMAL
