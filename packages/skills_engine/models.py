"""
Data models for Skills Execution Engine
"""
from typing import Dict, Any, List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum
import uuid


class SkillStatus(str, Enum):
    """Skill status"""
    DRAFT = "draft"
    ACTIVE = "active"
    DEPRECATED = "deprecated"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    """Execution status"""
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELED = "canceled"


class Skill(BaseModel):
    """Skill definition model"""
    id: str = Field(..., description="Skill UUID")
    name: str = Field(..., description="Skill name")
    slug: str = Field(..., description="URL-friendly identifier")
    version: str = Field(..., description="Semantic version")
    description: str = Field(..., description="Short description")
    
    # Execution configuration
    prompt_template: str = Field(..., description="Jinja2 prompt template")
    input_schema: Dict[str, Any] = Field(..., description="JSON Schema for inputs")
    output_schema: Dict[str, Any] = Field(..., description="JSON Schema for outputs")
    
    # Model preferences
    model_preferences: Dict[str, Any] = Field(
        default_factory=lambda: {
            "preferred_models": [],
            "min_quality": 0.7,
            "max_cost": None,
            "temperature": 0.7,
        },
        description="Model selection preferences"
    )
    
    # Validation
    validation_rules: Optional[List[Dict[str, Any]]] = Field(
        None, description="Validation rules"
    )
    
    # Category
    category: str = Field(..., description="Skill category")
    
    # Metadata
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class ExecutionContext(BaseModel):
    """Context for skill execution"""
    user_id: Optional[str] = Field(None, description="User ID")
    agent_id: Optional[str] = Field(None, description="Agent ID")
    workflow_id: Optional[str] = Field(None, description="Temporal workflow ID")
    parent_execution_id: Optional[str] = Field(None, description="Parent execution ID")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ValidationRule(BaseModel):
    """Validation rule definition"""
    type: str = Field(..., description="Rule type")
    params: Dict[str, Any] = Field(default_factory=dict, description="Rule parameters")
    error_message: Optional[str] = Field(None, description="Custom error message")


class ValidationResult(BaseModel):
    """Result of validation"""
    passed: bool = Field(..., description="Whether validation passed")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional details")


class SkillResult(BaseModel):
    """Result of skill execution"""
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Execution ID")
    skill_id: str = Field(..., description="Skill ID")
    skill_version: str = Field(..., description="Skill version")
    
    # Inputs and outputs
    inputs: Dict[str, Any] = Field(..., description="Validated inputs")
    outputs: Optional[Dict[str, Any]] = Field(None, description="Validated outputs")
    rendered_prompt: Optional[str] = Field(None, description="Rendered prompt")
    
    # Execution details
    status: ExecutionStatus = Field(..., description="Execution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    
    # Validation
    validation_passed: bool = Field(False, description="Whether validation passed")
    validation_result: Optional[ValidationResult] = Field(None, description="Validation details")
    
    # Model information
    model_id: Optional[str] = Field(None, description="Model used")
    model_provider: Optional[str] = Field(None, description="Model provider")
    
    # Performance metrics
    latency_ms: Optional[int] = Field(None, description="Execution latency in ms")
    tokens_input: Optional[int] = Field(None, description="Input tokens")
    tokens_output: Optional[int] = Field(None, description="Output tokens")
    cost_usd: Optional[float] = Field(None, description="Cost in USD")
    
    # Caching
    cache_hit: bool = Field(False, description="Whether result was from cache")
    cache_key: Optional[str] = Field(None, description="Cache key used")
    
    # Timestamps
    executed_at: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    
    # Context
    context: Optional[ExecutionContext] = Field(None, description="Execution context")

