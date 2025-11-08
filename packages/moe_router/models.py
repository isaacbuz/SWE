"""
Model Registry and Data Models for MoE Router

Defines the core data structures for models, routing decisions, and performance tracking.
"""
from typing import List, Optional, Dict, Any, Literal
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum


class TaskType(str, Enum):
    """Supported task types for routing decisions"""
    REASONING = "reasoning"
    CODE_GENERATION = "code_generation"
    CODE_REVIEW = "code_review"
    PLANNING = "planning"
    ANALYSIS = "analysis"
    DOCUMENTATION = "documentation"
    TESTING = "testing"
    REFACTORING = "refactoring"
    SECURITY_AUDIT = "security_audit"
    TOOL_USE = "tool_use"
    MULTIMODAL = "multimodal"
    LONG_CONTEXT = "long_context"


class Provider(str, Enum):
    """Supported AI providers"""
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    MISTRAL = "mistral"
    COHERE = "cohere"
    META = "meta"


class ModelCapability(str, Enum):
    """Model capabilities for matching tasks"""
    REASONING = "reasoning"
    CODE = "code"
    TOOLS = "tools"
    VISION = "vision"
    LONG_CONTEXT = "long_context"
    JSON_MODE = "json_mode"
    FUNCTION_CALLING = "function_calling"
    STREAMING = "streaming"


class ModelDefinition(BaseModel):
    """Model configuration and metadata"""
    id: str = Field(..., description="Unique model identifier")
    provider: Provider = Field(..., description="AI provider")
    capabilities: List[ModelCapability] = Field(..., description="Model capabilities")
    cost_per_1k_input: float = Field(..., description="Cost per 1K input tokens in USD")
    cost_per_1k_output: float = Field(..., description="Cost per 1K output tokens in USD")
    context_window: int = Field(..., description="Maximum context window size")
    quality_score: float = Field(..., ge=0.0, le=1.0, description="Base quality score (0-1)")
    max_output_tokens: Optional[int] = Field(None, description="Maximum output tokens")
    supports_system_prompt: bool = Field(True, description="Supports system prompts")
    supports_streaming: bool = Field(True, description="Supports streaming responses")
    rate_limit_rpm: Optional[int] = Field(None, description="Rate limit requests per minute")
    rate_limit_tpm: Optional[int] = Field(None, description="Rate limit tokens per minute")
    latency_p50_ms: Optional[int] = Field(None, description="P50 latency in milliseconds")
    latency_p95_ms: Optional[int] = Field(None, description="P95 latency in milliseconds")
    enabled: bool = Field(True, description="Whether model is enabled")
    fallback_models: List[str] = Field(default_factory=list, description="Fallback model IDs")
    tags: List[str] = Field(default_factory=list, description="Additional tags for filtering")

    class Config:
        use_enum_values = True


class RoutingRequest(BaseModel):
    """Request for model routing decision"""
    task_type: TaskType = Field(..., description="Type of task to perform")
    task_description: str = Field(..., description="Description of the task")
    estimated_input_tokens: Optional[int] = Field(None, description="Estimated input tokens")
    estimated_output_tokens: Optional[int] = Field(500, description="Estimated output tokens")
    context_size: Optional[int] = Field(None, description="Required context window size")
    cost_budget: Optional[float] = Field(None, description="Maximum cost in USD")
    quality_requirement: float = Field(0.7, ge=0.0, le=1.0, description="Minimum quality score")
    latency_requirement_ms: Optional[int] = Field(None, description="Maximum latency in ms")
    requires_streaming: bool = Field(False, description="Requires streaming support")
    requires_tools: bool = Field(False, description="Requires tool/function calling")
    requires_vision: bool = Field(False, description="Requires vision capabilities")
    requires_json_mode: bool = Field(False, description="Requires JSON mode")
    vendor_preference: Optional[Provider] = Field(None, description="Preferred vendor")
    vendor_diversity: bool = Field(False, description="Prefer vendor diversity")
    enable_parallel: bool = Field(False, description="Enable parallel execution")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class Evidence(BaseModel):
    """Evidence supporting routing decision"""
    id: str = Field(..., description="Evidence identifier")
    source: str = Field(..., description="Source of evidence")
    description: str = Field(..., description="Evidence description")
    weight: float = Field(1.0, ge=0.0, le=1.0, description="Evidence weight")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class RoutingDecision(BaseModel):
    """Model selection decision with rationale"""
    selected_model: str = Field(..., description="Selected model ID")
    rationale: str = Field(..., description="Human-readable rationale")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    evidence_ids: List[str] = Field(default_factory=list, description="Supporting evidence IDs")
    evidence: List[Evidence] = Field(default_factory=list, description="Evidence objects")
    estimated_cost: float = Field(..., description="Estimated cost in USD")
    estimated_quality: float = Field(..., description="Estimated quality score")
    fallback_models: List[str] = Field(default_factory=list, description="Fallback model IDs")
    parallel_models: Optional[List[str]] = Field(None, description="Models for parallel execution")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    routing_strategy: str = Field("standard", description="Routing strategy used")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class PerformanceMetrics(BaseModel):
    """Performance metrics for a model+task combination"""
    model_id: str = Field(..., description="Model identifier")
    task_type: TaskType = Field(..., description="Task type")
    total_requests: int = Field(0, description="Total requests")
    successful_requests: int = Field(0, description="Successful requests")
    failed_requests: int = Field(0, description="Failed requests")
    avg_latency_ms: Optional[float] = Field(None, description="Average latency")
    avg_cost: Optional[float] = Field(None, description="Average cost")
    avg_quality: Optional[float] = Field(None, description="Average quality score")
    success_rate: float = Field(0.0, ge=0.0, le=1.0, description="Success rate")
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    @validator('success_rate', always=True)
    def calculate_success_rate(cls, v, values):
        """Calculate success rate from requests"""
        total = values.get('total_requests', 0)
        if total == 0:
            return 0.0
        successful = values.get('successful_requests', 0)
        return successful / total


class FeedbackData(BaseModel):
    """Feedback data for learning loop"""
    request_id: str = Field(..., description="Original request ID")
    model_id: str = Field(..., description="Model used")
    task_type: TaskType = Field(..., description="Task type")
    outcome: Literal["success", "failure", "partial"] = Field(..., description="Outcome")
    quality_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Quality score")
    actual_cost: Optional[float] = Field(None, description="Actual cost")
    actual_latency_ms: Optional[int] = Field(None, description="Actual latency")
    pr_merged: Optional[bool] = Field(None, description="Was PR merged?")
    pr_reverted: Optional[bool] = Field(None, description="Was PR reverted?")
    user_rating: Optional[int] = Field(None, ge=1, le=5, description="User rating 1-5")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    feedback_notes: Optional[str] = Field(None, description="Additional feedback")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CostPrediction(BaseModel):
    """Cost prediction for a routing request"""
    model_id: str = Field(..., description="Model identifier")
    estimated_input_tokens: int = Field(..., description="Estimated input tokens")
    estimated_output_tokens: int = Field(..., description="Estimated output tokens")
    min_cost: float = Field(..., description="Minimum estimated cost")
    max_cost: float = Field(..., description="Maximum estimated cost")
    expected_cost: float = Field(..., description="Expected cost")
    within_budget: bool = Field(..., description="Within budget constraint")
    cost_efficiency_score: float = Field(..., ge=0.0, le=1.0, description="Cost efficiency")


class CircuitBreakerState(BaseModel):
    """Circuit breaker state for a provider/model"""
    identifier: str = Field(..., description="Provider or model ID")
    state: Literal["closed", "open", "half_open"] = Field("closed", description="Circuit state")
    failure_count: int = Field(0, description="Consecutive failures")
    last_failure: Optional[datetime] = Field(None, description="Last failure timestamp")
    last_success: Optional[datetime] = Field(None, description="Last success timestamp")
    next_retry_at: Optional[datetime] = Field(None, description="Next retry timestamp")
    failure_threshold: int = Field(5, description="Failures before opening")
    retry_timeout_seconds: int = Field(60, description="Timeout before retry")
