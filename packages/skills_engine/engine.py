"""
Skills Execution Engine

Executes Skills with validation, caching, and MoE router integration.
"""
import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
import jinja2
from jinja2 import Template, TemplateError

from packages.moe_router import MoERouter, RoutingRequest, TaskType
from packages.moe_router.models import Provider
from packages.integrations.ai_providers import (
    AIProvider,
    AnthropicClient,
    OpenAIClient,
    GoogleClient,
    IBMClient,
    LocalClient,
    Message,
    Completion,
)
from packages.db.redis import RedisClient

from .models import (
    Skill,
    SkillResult,
    ExecutionContext,
    ExecutionStatus,
    ValidationResult,
    ValidationRule,
)
from .validators import InputValidator, OutputValidator, ValidationRuleExecutor
from .cache import SkillCache

logger = logging.getLogger(__name__)


class SkillExecutionError(Exception):
    """Base exception for skill execution errors"""
    pass


class SkillInputValidationError(SkillExecutionError):
    """Raised when input validation fails"""
    pass


class SkillOutputValidationError(SkillExecutionError):
    """Raised when output validation fails"""
    pass


class SkillExecutionEngine:
    """
    Executes Skills with validation, caching, and MoE router integration.
    """
    
    def __init__(
        self,
        moe_router: MoERouter,
        redis_client: Optional[RedisClient] = None,
        enable_caching: bool = True,
        default_cache_ttl: int = 3600
    ):
        """
        Initialize Skills Execution Engine
        
        Args:
            moe_router: MoE Router instance for model selection
            redis_client: Redis client for caching (optional)
            enable_caching: Whether to enable result caching
            default_cache_ttl: Default cache TTL in seconds
        """
        self.moe_router = moe_router
        self.enable_caching = enable_caching
        
        # Initialize components
        self.input_validator = InputValidator()
        self.output_validator = OutputValidator()
        self.validation_executor = ValidationRuleExecutor()
        
        # Initialize cache if enabled
        self.cache = None
        if enable_caching:
            self.cache = SkillCache(redis_client, default_ttl=default_cache_ttl)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True
        )
        
        # Provider registry for invoking models
        self._provider_clients: Dict[str, AIProvider] = {}
        
        logger.info(
            f"Skills Execution Engine initialized (caching={'enabled' if enable_caching else 'disabled'})"
        )
    
    def _get_provider_client(self, provider: Provider) -> AIProvider:
        """Get or create AI provider client"""
        provider_key = provider.value
        
        if provider_key not in self._provider_clients:
            if provider == Provider.ANTHROPIC:
                self._provider_clients[provider_key] = AnthropicClient()
            elif provider == Provider.OPENAI:
                self._provider_clients[provider_key] = OpenAIClient()
            elif provider == Provider.GOOGLE:
                self._provider_clients[provider_key] = GoogleClient()
            elif provider == Provider.META:  # IBM Granite
                self._provider_clients[provider_key] = IBMClient()
            else:
                # Default to local for unknown providers
                self._provider_clients[provider_key] = LocalClient()
        
        return self._provider_clients[provider_key]
    
    async def execute_skill(
        self,
        skill: Skill,
        inputs: Dict[str, Any],
        context: Optional[ExecutionContext] = None
    ) -> SkillResult:
        """
        Execute a Skill with validation and caching
        
        Args:
            skill: Skill definition
            inputs: Input dictionary
            context: Execution context (optional)
            
        Returns:
            SkillResult with execution details
            
        Raises:
            SkillInputValidationError: If input validation fails
            SkillOutputValidationError: If output validation fails
            SkillExecutionError: For other execution errors
        """
        execution_start = time.time()
        execution_id = None
        
        try:
            # 1. Validate inputs
            logger.debug(f"Validating inputs for skill {skill.id}")
            validated_inputs = self._validate_inputs(skill, inputs)
            
            # 2. Check cache
            cache_key = None
            cached_result = None
            if self.enable_caching and self.cache:
                cache_key = self.cache.compute_key(skill.id, skill.version, validated_inputs)
                cached_result = await self.cache.get(cache_key)
                
                if cached_result:
                    logger.info(f"Cache hit for skill {skill.id}")
                    # Convert cached dict back to SkillResult
                    result = SkillResult(**cached_result)
                    result.cache_hit = True
                    result.cache_key = cache_key
                    return result
            
            # 3. Render prompt template
            logger.debug(f"Rendering prompt template for skill {skill.id}")
            rendered_prompt = self._render_prompt(skill.prompt_template, validated_inputs)
            
            # 4. Select model via MoE router
            logger.debug(f"Selecting model for skill {skill.id}")
            model_decision = await self._select_model(skill, rendered_prompt)
            selected_model = model_decision.selected_model
            
            # 5. Execute with selected model
            logger.info(f"Executing skill {skill.id} with model {selected_model.id}")
            model_response = await self._invoke_model(
                selected_model,
                rendered_prompt,
                skill.model_preferences
            )
            
            # 6. Validate outputs
            logger.debug(f"Validating outputs for skill {skill.id}")
            validated_outputs = self._validate_outputs(skill, model_response.content)
            
            # 7. Run validation rules
            validation_result = None
            if skill.validation_rules:
                logger.debug(f"Running validation rules for skill {skill.id}")
                rules = [ValidationRule(**rule) for rule in skill.validation_rules]
                validation_result = await self.validation_executor.execute(
                    rules,
                    validated_outputs
                )
            else:
                validation_result = ValidationResult(passed=True)
            
            # 8. Calculate execution time
            execution_time = time.time() - execution_start
            latency_ms = int(execution_time * 1000)
            
            # 9. Create result
            result = SkillResult(
                execution_id=execution_id or f"exec_{int(time.time())}",
                skill_id=skill.id,
                skill_version=skill.version,
                inputs=validated_inputs,
                outputs=validated_outputs,
                rendered_prompt=rendered_prompt,
                status=ExecutionStatus.SUCCESS,
                validation_passed=validation_result.passed,
                validation_result=validation_result,
                model_id=selected_model.id,
                model_provider=selected_model.provider.value,
                latency_ms=latency_ms,
                tokens_input=model_response.usage.input_tokens if model_response.usage else None,
                tokens_output=model_response.usage.output_tokens if model_response.usage else None,
                cost_usd=model_response.cost if hasattr(model_response, 'cost') else None,
                cache_hit=False,
                cache_key=cache_key,
                executed_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                context=context
            )
            
            # 10. Cache result if validation passed
            if validation_result.passed and self.enable_caching and self.cache and cache_key:
                await self.cache.set(cache_key, result.dict())
            
            logger.info(
                f"Skill {skill.id} executed successfully "
                f"(latency: {latency_ms}ms, cost: ${result.cost_usd or 0:.6f})"
            )
            
            return result
            
        except ValueError as e:
            # Input/output validation errors
            error_msg = str(e)
            logger.error(f"Skill {skill.id} validation failed: {error_msg}")
            
            execution_time = time.time() - execution_start
            return SkillResult(
                execution_id=execution_id or f"exec_{int(time.time())}",
                skill_id=skill.id,
                skill_version=skill.version,
                inputs=inputs,
                status=ExecutionStatus.FAILED,
                error_message=error_msg,
                validation_passed=False,
                latency_ms=int(execution_time * 1000),
                executed_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                context=context
            )
            
        except Exception as e:
            # Other execution errors
            error_msg = str(e)
            logger.error(f"Skill {skill.id} execution failed: {error_msg}", exc_info=True)
            
            execution_time = time.time() - execution_start
            return SkillResult(
                execution_id=execution_id or f"exec_{int(time.time())}",
                skill_id=skill.id,
                skill_version=skill.version,
                inputs=inputs,
                status=ExecutionStatus.FAILED,
                error_message=error_msg,
                validation_passed=False,
                latency_ms=int(execution_time * 1000),
                executed_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                context=context
            )
    
    def _validate_inputs(self, skill: Skill, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Validate inputs against schema"""
        try:
            return self.input_validator.validate(inputs, skill.input_schema)
        except ValueError as e:
            raise SkillInputValidationError(str(e)) from e
    
    def _validate_outputs(self, skill: Skill, output: str) -> Dict[str, Any]:
        """Parse and validate outputs"""
        try:
            return self.output_validator.validate(output, skill.output_schema)
        except ValueError as e:
            raise SkillOutputValidationError(str(e)) from e
    
    def _render_prompt(self, template_str: str, inputs: Dict[str, Any]) -> str:
        """Render Jinja2 prompt template"""
        try:
            template = self.jinja_env.from_string(template_str)
            return template.render(**inputs)
        except TemplateError as e:
            raise SkillExecutionError(f"Template rendering failed: {e}") from e
    
    async def _select_model(self, skill: Skill, prompt: str):
        """Select model using MoE router"""
        # Map skill category to TaskType
        category_to_task_type = {
            "CODE_GENERATION": TaskType.CODE_GENERATION,
            "TESTING": TaskType.TESTING,
            "CODE_REVIEW": TaskType.CODE_REVIEW,
            "SECURITY": TaskType.SECURITY_AUDIT,
            "DOCUMENTATION": TaskType.DOCUMENTATION,
            "PLANNING": TaskType.PLANNING,
            "ANALYSIS": TaskType.ANALYSIS,
            "REFACTORING": TaskType.REFACTORING,
        }
        
        task_type = category_to_task_type.get(
            skill.category.upper(),
            TaskType.CODE_GENERATION  # Default
        )
        
        # Get model preferences
        prefs = skill.model_preferences or {}
        preferred_models = prefs.get("preferred_models", [])
        min_quality = prefs.get("min_quality", 0.7)
        max_cost = prefs.get("max_cost")
        temperature = prefs.get("temperature", 0.7)
        
        # Create routing request
        request = RoutingRequest(
            task_type=task_type,
            task_description=skill.description,
            quality_requirement=min_quality,
            cost_budget=max_cost,
            metadata={
                "skill_id": skill.id,
                "skill_category": skill.category,
                "preferred_models": preferred_models,
                "temperature": temperature,
            }
        )
        
        # Select model
        decision = self.moe_router.select_model(request)
        return decision
    
    async def _invoke_model(
        self,
        model_definition,
        prompt: str,
        model_preferences: Dict[str, Any]
    ) -> Completion:
        """Invoke AI model with prompt"""
        # Get provider client
        provider = Provider(model_definition.provider)
        client = self._get_provider_client(provider)
        
        # Prepare messages
        messages = [Message(role="user", content=prompt)]
        
        # Get temperature from preferences
        temperature = model_preferences.get("temperature", 0.7)
        
        # Check if output schema requires JSON mode
        json_mode = False  # Could be determined from skill.output_schema
        
        # Invoke model
        completion = await client.complete(
            messages=messages,
            model=model_definition.id,
            temperature=temperature,
            max_tokens=model_definition.max_output_tokens or 4096,
            json_mode=json_mode
        )
        
        return completion
