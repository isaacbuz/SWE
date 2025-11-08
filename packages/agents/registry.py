"""
Agent Registry

Manages agent lifecycle, discovery, orchestration, capability tracking,
status monitoring, and load balancing for all agents in the system.
"""
from typing import Dict, List, Optional, Type, Any
from dataclasses import dataclass, field
from datetime import datetime
import logging
import asyncio
from collections import defaultdict
from enum import Enum

from .base import BaseAgent, Task, Context, AgentResult, TaskType, AgentStatus
from .protocol import AgentState, MessageBus


class AgentCapability(str, Enum):
    """Agent capability types for fine-grained matching"""
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    TESTING = "testing"
    SECURITY_AUDIT = "security_audit"
    DEPLOYMENT = "deployment"
    PLANNING = "planning"
    ARCHITECTURE = "architecture"
    REFACTORING = "refactoring"
    MIGRATION = "migration"
    INCIDENT_RESPONSE = "incident_response"
    TECH_DEBT_ANALYSIS = "tech_debt_analysis"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    DOCUMENTATION = "documentation"
    COORDINATION = "coordination"
    CONFLICT_RESOLUTION = "conflict_resolution"


@dataclass
class AgentRegistration:
    """Agent registration metadata with capability tracking"""
    agent_id: str
    agent_class: Type[BaseAgent]
    task_types: List[TaskType]
    description: str
    priority: int = 50  # Higher = higher priority
    enabled: bool = True
    tags: List[str] = field(default_factory=list)
    capabilities: List[AgentCapability] = field(default_factory=list)
    max_concurrent_tasks: int = 5
    current_load: int = 0
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    avg_execution_time_ms: float = 0.0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)

    def is_available(self) -> bool:
        """Check if agent is available for work"""
        return self.enabled and self.current_load < self.max_concurrent_tasks

    def update_stats(self, success: bool, execution_time_ms: int) -> None:
        """Update agent statistics"""
        total = self.total_tasks_completed + self.total_tasks_failed

        if success:
            self.total_tasks_completed += 1
        else:
            self.total_tasks_failed += 1

        new_total = total + 1
        self.success_rate = self.total_tasks_completed / new_total
        self.avg_execution_time_ms = (
            (self.avg_execution_time_ms * total + execution_time_ms) / new_total
        )


class AgentRegistry:
    """
    Central registry for agent management

    Features:
    - Agent discovery and instantiation
    - Task routing to appropriate agents
    - Agent lifecycle management
    - Execution orchestration
    - Performance tracking
    - Capability-based agent selection
    - Load balancing
    - Health monitoring
    """

    def __init__(
        self,
        moe_router=None,
        anthropic_client=None,
        openai_client=None,
        redis_client=None,
        message_bus: Optional[MessageBus] = None
    ):
        """
        Initialize agent registry

        Args:
            moe_router: MoE Router instance
            anthropic_client: Anthropic API client
            openai_client: OpenAI API client
            redis_client: Redis client for distributed state
            message_bus: Message bus for agent communication
        """
        self.moe_router = moe_router
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client
        self.redis_client = redis_client
        self.message_bus = message_bus or MessageBus()

        self.registrations: Dict[str, AgentRegistration] = {}
        self.instances: Dict[str, BaseAgent] = {}
        self.agent_states: Dict[str, AgentState] = {}
        self.capability_index: Dict[AgentCapability, set] = defaultdict(set)

        self.logger = logging.getLogger("AgentRegistry")
        self._heartbeat_task: Optional[asyncio.Task] = None
        self.logger.info("Agent registry initialized")

    def register(
        self,
        agent_id: str,
        agent_class: Type[BaseAgent],
        task_types: List[TaskType],
        description: str,
        priority: int = 50,
        tags: Optional[List[str]] = None,
        capabilities: Optional[List[AgentCapability]] = None,
        max_concurrent_tasks: int = 5,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register an agent class

        Args:
            agent_id: Unique agent identifier
            agent_class: Agent class (subclass of BaseAgent)
            task_types: Task types this agent handles
            description: Agent description
            priority: Agent priority (higher = preferred)
            tags: Optional tags for filtering
            capabilities: Optional list of agent capabilities
            max_concurrent_tasks: Maximum concurrent tasks
            metadata: Optional metadata
        """
        if agent_id in self.registrations:
            self.logger.warning(f"Agent {agent_id} already registered, overwriting")

        registration = AgentRegistration(
            agent_id=agent_id,
            agent_class=agent_class,
            task_types=task_types,
            description=description,
            priority=priority,
            tags=tags or [],
            capabilities=capabilities or [],
            max_concurrent_tasks=max_concurrent_tasks,
            metadata=metadata or {}
        )

        self.registrations[agent_id] = registration

        # Update capability index
        for cap in capabilities or []:
            self.capability_index[cap].add(agent_id)

        # Initialize agent state
        self.agent_states[agent_id] = AgentState(
            agent_id=agent_id,
            status="idle"
        )

        self.logger.info(
            f"Registered agent {agent_id} for tasks: {[t.value for t in task_types]}, "
            f"capabilities: {[c.value for c in (capabilities or [])]}"
        )

    def unregister(self, agent_id: str):
        """Unregister an agent"""
        if agent_id in self.registrations:
            del self.registrations[agent_id]
            self.logger.info(f"Unregistered agent {agent_id}")

        if agent_id in self.instances:
            del self.instances[agent_id]

    def get_agent(
        self,
        agent_id: str,
        **kwargs
    ) -> Optional[BaseAgent]:
        """
        Get or create agent instance

        Args:
            agent_id: Agent identifier
            **kwargs: Additional initialization arguments

        Returns:
            Agent instance or None
        """
        # Return existing instance if available
        if agent_id in self.instances:
            return self.instances[agent_id]

        # Create new instance
        if agent_id not in self.registrations:
            self.logger.error(f"Agent {agent_id} not registered")
            return None

        registration = self.registrations[agent_id]

        try:
            # Merge kwargs with default clients
            init_kwargs = {
                "agent_id": agent_id,
                "moe_router": self.moe_router,
                "anthropic_client": self.anthropic_client,
                "openai_client": self.openai_client,
                **kwargs
            }

            agent = registration.agent_class(**init_kwargs)
            self.instances[agent_id] = agent

            self.logger.info(f"Created instance of {agent_id}")
            return agent

        except Exception as e:
            self.logger.error(f"Failed to create agent {agent_id}: {e}")
            return None

    def find_agents(
        self,
        task_type: Optional[TaskType] = None,
        tags: Optional[List[str]] = None,
        enabled_only: bool = True
    ) -> List[str]:
        """
        Find agents matching criteria

        Args:
            task_type: Filter by task type
            tags: Filter by tags (any match)
            enabled_only: Only return enabled agents

        Returns:
            List of agent IDs
        """
        matching = []

        for agent_id, reg in self.registrations.items():
            # Check enabled status
            if enabled_only and not reg.enabled:
                continue

            # Check task type
            if task_type and task_type not in reg.task_types:
                continue

            # Check tags
            if tags and not any(tag in reg.tags for tag in tags):
                continue

            matching.append(agent_id)

        # Sort by priority (descending)
        matching.sort(
            key=lambda aid: self.registrations[aid].priority,
            reverse=True
        )

        return matching

    def route_task(
        self,
        task: Task,
        preferred_agent: Optional[str] = None,
        tags: Optional[List[str]] = None
    ) -> Optional[str]:
        """
        Route task to appropriate agent

        Args:
            task: Task to route
            preferred_agent: Preferred agent ID
            tags: Filter agents by tags

        Returns:
            Agent ID or None
        """
        # Use preferred agent if specified and available
        if preferred_agent:
            if preferred_agent in self.registrations:
                reg = self.registrations[preferred_agent]
                if reg.enabled and task.type in reg.task_types:
                    return preferred_agent

        # Find matching agents
        candidates = self.find_agents(
            task_type=task.type,
            tags=tags,
            enabled_only=True
        )

        if not candidates:
            self.logger.warning(f"No agents found for task type {task.type.value}")
            return None

        # Return highest priority agent
        selected = candidates[0]

        self.logger.info(
            f"Routed task {task.id} ({task.type.value}) to {selected}"
        )

        return selected

    async def execute_task(
        self,
        task: Task,
        context: Context,
        preferred_agent: Optional[str] = None
    ) -> Optional[AgentResult]:
        """
        Execute task with appropriate agent

        Args:
            task: Task to execute
            context: Execution context
            preferred_agent: Preferred agent ID

        Returns:
            AgentResult or None
        """
        # Route to agent
        agent_id = self.route_task(task, preferred_agent=preferred_agent)
        if not agent_id:
            return None

        # Get agent instance
        agent = self.get_agent(agent_id)
        if not agent:
            return None

        # Execute task
        result = await agent.execute_with_tracking(task, context)

        return result

    async def execute_workflow(
        self,
        tasks: List[Task],
        context: Context,
        parallel: bool = False
    ) -> List[AgentResult]:
        """
        Execute workflow of multiple tasks

        Args:
            tasks: List of tasks to execute
            context: Shared execution context
            parallel: Execute tasks in parallel (if no dependencies)

        Returns:
            List of AgentResults
        """
        results = []
        completed_task_ids = set()

        if parallel:
            # Execute all tasks in parallel
            import asyncio
            async_results = await asyncio.gather(
                *[self.execute_task(task, context) for task in tasks],
                return_exceptions=True
            )
            results = [r for r in async_results if isinstance(r, AgentResult)]
        else:
            # Execute tasks sequentially, respecting dependencies
            for task in tasks:
                # Check dependencies
                if task.dependencies:
                    missing = set(task.dependencies) - completed_task_ids
                    if missing:
                        self.logger.warning(
                            f"Task {task.id} has missing dependencies: {missing}, skipping"
                        )
                        continue

                result = await self.execute_task(task, context)
                if result:
                    results.append(result)
                    if result.success:
                        completed_task_ids.add(task.id)

        return results

    def get_registry_stats(self) -> Dict[str, Any]:
        """Get registry statistics"""
        total_registered = len(self.registrations)
        enabled = sum(1 for r in self.registrations.values() if r.enabled)
        instances = len(self.instances)

        # Task type coverage
        task_type_coverage = {}
        for reg in self.registrations.values():
            for task_type in reg.task_types:
                task_type_coverage[task_type.value] = task_type_coverage.get(task_type.value, 0) + 1

        # Agent stats
        agent_stats = {}
        for agent_id, agent in self.instances.items():
            agent_stats[agent_id] = agent.get_stats()

        return {
            "total_registered": total_registered,
            "enabled": enabled,
            "active_instances": instances,
            "task_type_coverage": task_type_coverage,
            "agent_stats": agent_stats
        }

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all registered agents"""
        return [
            {
                "agent_id": reg.agent_id,
                "description": reg.description,
                "task_types": [t.value for t in reg.task_types],
                "priority": reg.priority,
                "enabled": reg.enabled,
                "tags": reg.tags,
                "status": self.instances[reg.agent_id].status.value if reg.agent_id in self.instances else "not_instantiated"
            }
            for reg in self.registrations.values()
        ]

    def enable_agent(self, agent_id: str):
        """Enable an agent"""
        if agent_id in self.registrations:
            self.registrations[agent_id].enabled = True
            self.logger.info(f"Enabled agent {agent_id}")

    def disable_agent(self, agent_id: str):
        """Disable an agent"""
        if agent_id in self.registrations:
            self.registrations[agent_id].enabled = False
            self.logger.info(f"Disabled agent {agent_id}")

    async def find_agents_by_capability(
        self,
        capability: AgentCapability,
        only_available: bool = True
    ) -> List[str]:
        """
        Find agents by capability

        Args:
            capability: Required capability
            only_available: Only return available agents

        Returns:
            List of agent IDs
        """
        agent_ids = self.capability_index.get(capability, set())
        matching = []

        for agent_id in agent_ids:
            if agent_id not in self.registrations:
                continue

            agent = self.registrations[agent_id]

            if only_available and not agent.is_available():
                continue

            matching.append(agent_id)

        # Sort by load and priority
        matching.sort(
            key=lambda aid: (
                self.registrations[aid].current_load,
                -self.registrations[aid].priority
            )
        )

        return matching

    async def acquire_agent(
        self,
        agent_id: str,
        task_id: str
    ) -> bool:
        """
        Acquire agent for a task

        Args:
            agent_id: Agent to acquire
            task_id: Task ID

        Returns:
            True if acquired successfully
        """
        if agent_id not in self.registrations:
            return False

        agent = self.registrations[agent_id]

        if not agent.is_available():
            return False

        # Increment load
        agent.current_load += 1
        agent.last_heartbeat = datetime.utcnow()

        # Update state
        if agent_id in self.agent_states:
            state = self.agent_states[agent_id]
            state.current_task_id = task_id
            state.status = "running"
            state.last_updated = datetime.utcnow()

        self.logger.info(
            f"Acquired agent {agent_id} for task {task_id} "
            f"(load={agent.current_load}/{agent.max_concurrent_tasks})"
        )

        return True

    async def release_agent(
        self,
        agent_id: str,
        task_id: str,
        success: bool,
        execution_time_ms: int
    ) -> None:
        """
        Release agent after task completion

        Args:
            agent_id: Agent to release
            task_id: Completed task ID
            success: Whether task succeeded
            execution_time_ms: Execution time in milliseconds
        """
        if agent_id not in self.registrations:
            return

        agent = self.registrations[agent_id]

        # Decrement load
        agent.current_load = max(0, agent.current_load - 1)

        # Update statistics
        agent.update_stats(success, execution_time_ms)

        # Update state
        if agent_id in self.agent_states:
            state = self.agent_states[agent_id]
            state.current_task_id = None
            state.status = "idle"
            state.last_updated = datetime.utcnow()

        self.logger.info(
            f"Released agent {agent_id} from task {task_id} "
            f"(success={success}, time={execution_time_ms}ms)"
        )

    async def start(self) -> None:
        """Start registry background tasks"""
        self._heartbeat_task = asyncio.create_task(self._heartbeat_monitor())
        self.logger.info("Agent registry started")

    async def stop(self) -> None:
        """Stop registry background tasks"""
        if self._heartbeat_task:
            self._heartbeat_task.cancel()
            try:
                await self._heartbeat_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Agent registry stopped")

    async def _heartbeat_monitor(self) -> None:
        """Monitor agent heartbeats"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute

                now = datetime.utcnow()
                for agent_id, agent in list(self.registrations.items()):
                    # If no heartbeat in 5 minutes, mark as offline
                    if (now - agent.last_heartbeat).total_seconds() > 300:
                        if agent.enabled:
                            self.logger.warning(
                                f"Agent {agent_id} heartbeat timeout"
                            )
                            agent.enabled = False

            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Heartbeat monitor error: {e}")
