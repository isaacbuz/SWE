"""
Base Agent Framework

Provides abstract base class and common functionality for all agents in the system.
Integrates with MoE Router for intelligent model selection and evidence tracking.
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Type
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import logging
import asyncio
from anthropic import AsyncAnthropic
from openai import AsyncOpenAI

# Import from MoE Router
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "moe_router"))
from models import (
    TaskType, RoutingRequest, RoutingDecision, Evidence, Provider
)


class AgentStatus(str, Enum):
    """Agent execution status"""
    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class Priority(str, Enum):
    """Task priority levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class Tool:
    """Tool definition for agent capabilities"""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[callable] = None


@dataclass
class Task:
    """Task definition for agent execution"""
    id: str
    type: TaskType
    description: str
    input_data: Dict[str, Any]
    priority: Priority = Priority.MEDIUM
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Context:
    """Execution context for agents"""
    project_path: str
    config: Dict[str, Any] = field(default_factory=dict)
    shared_state: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Evidence] = field(default_factory=list)
    parent_task_id: Optional[str] = None
    user_id: Optional[str] = None  # User ID for Skills execution logging
    agent_id: Optional[str] = None  # Agent ID for Skills execution logging
    task_id: Optional[str] = None  # Task ID for Skills execution logging
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentResult:
    """Result of agent execution"""
    success: bool
    output: Dict[str, Any]
    evidence: List[Evidence]
    artifacts: List[str] = field(default_factory=list)  # File paths
    sub_tasks: List[Task] = field(default_factory=list)
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_time_ms: Optional[int] = None
    model_used: Optional[str] = None
    cost: Optional[float] = None


class BaseAgent(ABC):
    """
    Abstract base class for all agents

    Features:
    - MoE Router integration for model selection
    - Evidence tracking for all decisions
    - Multi-model support (Anthropic Claude, OpenAI)
    - Tool use capabilities
    - Structured output generation
    - Performance tracking
    """

    def __init__(
        self,
        agent_id: str,
        task_type: TaskType,
        tools: Optional[List[Tool]] = None,
        moe_router = None,
        quality_requirement: float = 0.8,
        cost_budget: Optional[float] = None,
        anthropic_client: Optional[AsyncAnthropic] = None,
        openai_client: Optional[AsyncOpenAI] = None
    ):
        """
        Initialize base agent

        Args:
            agent_id: Unique agent identifier
            task_type: Primary task type this agent handles
            tools: Available tools for this agent
            moe_router: MoE Router instance for model selection
            quality_requirement: Minimum quality score for model selection
            cost_budget: Maximum cost budget per execution
            anthropic_client: Anthropic API client
            openai_client: OpenAI API client
        """
        self.agent_id = agent_id
        self.task_type = task_type
        self.tools = tools or []
        self.moe_router = moe_router
        self.quality_requirement = quality_requirement
        self.cost_budget = cost_budget

        # API clients
        self.anthropic_client = anthropic_client
        self.openai_client = openai_client

        # State
        self.status = AgentStatus.IDLE
        self.current_task: Optional[Task] = None
        self.execution_history: List[AgentResult] = []

        # Logging
        self.logger = logging.getLogger(f"Agent.{agent_id}")

        self.logger.info(
            f"Initialized {agent_id} for {task_type.value} "
            f"(quality>={quality_requirement}, tools={len(self.tools)})"
        )

    @abstractmethod
    async def execute(self, task: Task, context: Context) -> AgentResult:
        """
        Execute a task with given context

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            AgentResult with outputs and evidence
        """
        pass

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Get system prompt for this agent

        Returns:
            System prompt string
        """
        pass

    async def invoke_model(
        self,
        prompt: str,
        task: Task,
        context: Context,
        requires_tools: bool = False,
        requires_json: bool = False,
        max_tokens: int = 4096
    ) -> Dict[str, Any]:
        """
        Invoke model via MoE Router

        Args:
            prompt: User prompt
            task: Current task
            context: Execution context
            requires_tools: Whether tools are required
            requires_json: Whether JSON mode is required
            max_tokens: Maximum output tokens

        Returns:
            Dictionary with model response and metadata
        """
        start_time = datetime.utcnow()

        # Create routing request
        routing_request = RoutingRequest(
            task_type=self.task_type,
            task_description=task.description,
            estimated_output_tokens=max_tokens,
            quality_requirement=self.quality_requirement,
            cost_budget=self.cost_budget,
            requires_tools=requires_tools,
            requires_json_mode=requires_json,
            metadata={
                "agent_id": self.agent_id,
                "task_id": task.id
            }
        )

        # Get model selection from router
        if self.moe_router:
            decision = self.moe_router.select_model(routing_request)
            model_id = decision.selected_model

            # Add routing evidence to context
            context.evidence.extend(decision.evidence)

            self.logger.info(
                f"Router selected {model_id} with confidence {decision.confidence:.2f}"
            )
        else:
            # Default to Claude Sonnet if no router
            model_id = "claude-sonnet-4-5"
            decision = None

        # Get system prompt
        system_prompt = self.get_system_prompt()

        # Execute with appropriate client
        try:
            if "claude" in model_id.lower() or "anthropic" in model_id.lower():
                response = await self._invoke_anthropic(
                    model_id,
                    system_prompt,
                    prompt,
                    requires_tools,
                    max_tokens
                )
            elif "gpt" in model_id.lower() or "openai" in model_id.lower():
                response = await self._invoke_openai(
                    model_id,
                    system_prompt,
                    prompt,
                    requires_tools,
                    requires_json,
                    max_tokens
                )
            else:
                raise ValueError(f"Unsupported model: {model_id}")

            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)

            # Record success with router
            if self.moe_router and decision:
                self.moe_router.record_request_outcome(
                    model_id=model_id,
                    success=True,
                    latency_ms=execution_time,
                    cost=decision.estimated_cost
                )

            return {
                "content": response["content"],
                "model_used": model_id,
                "execution_time_ms": execution_time,
                "cost": decision.estimated_cost if decision else None,
                "routing_decision": decision,
                "tool_calls": response.get("tool_calls", [])
            }

        except Exception as e:
            self.logger.error(f"Model invocation failed: {e}")

            # Record failure with router
            if self.moe_router and decision:
                self.moe_router.record_request_outcome(
                    model_id=model_id,
                    success=False,
                    error=str(e)
                )

            raise

    async def _invoke_anthropic(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        use_tools: bool,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Invoke Anthropic Claude model"""
        if not self.anthropic_client:
            raise ValueError("Anthropic client not configured")

        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "system": system_prompt,
            "messages": [
                {"role": "user", "content": user_prompt}
            ]
        }

        # Add tools if needed
        if use_tools and self.tools:
            kwargs["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.input_schema
                }
                for tool in self.tools
            ]

        response = await self.anthropic_client.messages.create(**kwargs)

        # Extract content and tool calls
        content_blocks = []
        tool_calls = []

        for block in response.content:
            if block.type == "text":
                content_blocks.append(block.text)
            elif block.type == "tool_use":
                tool_calls.append({
                    "id": block.id,
                    "name": block.name,
                    "input": block.input
                })

        return {
            "content": "\n".join(content_blocks),
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }

    async def _invoke_openai(
        self,
        model_id: str,
        system_prompt: str,
        user_prompt: str,
        use_tools: bool,
        use_json: bool,
        max_tokens: int
    ) -> Dict[str, Any]:
        """Invoke OpenAI model"""
        if not self.openai_client:
            raise ValueError("OpenAI client not configured")

        kwargs = {
            "model": model_id,
            "max_tokens": max_tokens,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }

        # Add JSON mode if needed
        if use_json:
            kwargs["response_format"] = {"type": "json_object"}

        # Add tools if needed
        if use_tools and self.tools:
            kwargs["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.input_schema
                    }
                }
                for tool in self.tools
            ]

        response = await self.openai_client.chat.completions.create(**kwargs)

        message = response.choices[0].message

        # Extract tool calls
        tool_calls = []
        if message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "name": tc.function.name,
                    "input": tc.function.arguments
                }
                for tc in message.tool_calls
            ]

        return {
            "content": message.content or "",
            "tool_calls": tool_calls,
            "usage": {
                "input_tokens": response.usage.prompt_tokens,
                "output_tokens": response.usage.completion_tokens
            }
        }

    async def execute_with_tracking(
        self,
        task: Task,
        context: Context
    ) -> AgentResult:
        """
        Execute task with status tracking and error handling

        Args:
            task: Task to execute
            context: Execution context

        Returns:
            AgentResult
        """
        self.status = AgentStatus.RUNNING
        self.current_task = task
        start_time = datetime.utcnow()

        try:
            self.logger.info(f"Starting execution of task {task.id}")

            # Execute task
            result = await self.execute(task, context)

            # Calculate execution time
            execution_time = int((datetime.utcnow() - start_time).total_seconds() * 1000)
            result.execution_time_ms = execution_time

            # Update status
            self.status = AgentStatus.COMPLETED if result.success else AgentStatus.FAILED

            # Track in history
            self.execution_history.append(result)

            self.logger.info(
                f"Task {task.id} {'completed' if result.success else 'failed'} "
                f"in {execution_time}ms"
            )

            return result

        except Exception as e:
            self.logger.error(f"Task {task.id} failed with exception: {e}")
            self.status = AgentStatus.FAILED

            # Create error result
            result = AgentResult(
                success=False,
                output={},
                evidence=[],
                error=str(e),
                execution_time_ms=int((datetime.utcnow() - start_time).total_seconds() * 1000)
            )

            self.execution_history.append(result)
            return result

        finally:
            self.current_task = None

    def create_evidence(
        self,
        source: str,
        description: str,
        weight: float = 1.0
    ) -> Evidence:
        """
        Create evidence entry

        Args:
            source: Evidence source
            description: Evidence description
            weight: Evidence weight (0-1)

        Returns:
            Evidence object
        """
        return Evidence(
            id=f"{self.agent_id}_{len(self.execution_history)}_{source}",
            source=f"{self.agent_id}.{source}",
            description=description,
            weight=weight
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get agent statistics"""
        total = len(self.execution_history)
        if total == 0:
            return {"total_executions": 0}

        successful = sum(1 for r in self.execution_history if r.success)
        total_time = sum(r.execution_time_ms or 0 for r in self.execution_history)
        total_cost = sum(r.cost or 0 for r in self.execution_history)

        return {
            "agent_id": self.agent_id,
            "task_type": self.task_type.value,
            "status": self.status.value,
            "total_executions": total,
            "successful_executions": successful,
            "success_rate": successful / total,
            "avg_execution_time_ms": total_time / total,
            "total_cost": total_cost,
            "avg_cost": total_cost / total
        }
