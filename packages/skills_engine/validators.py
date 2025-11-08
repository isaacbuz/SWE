"""
Input/output validation for Skills
"""
import json
import logging
from typing import Dict, Any, List, Optional
from jsonschema import validate, ValidationError as JSONSchemaValidationError
from jsonschema.exceptions import SchemaError
from pydantic import BaseModel, ValidationError as PydanticValidationError

from .models import ValidationRule, ValidationResult

logger = logging.getLogger(__name__)


class InputValidator:
    """Validates skill inputs against JSON Schema"""
    
    def validate(self, inputs: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate inputs against JSON Schema
        
        Args:
            inputs: Input dictionary
            schema: JSON Schema definition
            
        Returns:
            Validated inputs
            
        Raises:
            ValueError: If validation fails
        """
        try:
            # Validate against JSON Schema
            validate(instance=inputs, schema=schema)
            return inputs
        except JSONSchemaValidationError as e:
            error_msg = f"Input validation failed: {e.message}"
            if e.path:
                error_msg += f" at path: {'.'.join(str(p) for p in e.path)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except SchemaError as e:
            error_msg = f"Invalid schema definition: {e.message}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e


class OutputValidator:
    """Validates and parses skill outputs"""
    
    def validate(self, output: str, schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse and validate output against JSON Schema
        
        Args:
            output: Raw output string (may be JSON, YAML, or plain text)
            schema: JSON Schema definition
            
        Returns:
            Validated output dictionary
            
        Raises:
            ValueError: If parsing or validation fails
        """
        # Try to parse as JSON first
        parsed = self._parse_output(output)
        
        try:
            # Validate against JSON Schema
            validate(instance=parsed, schema=schema)
            return parsed
        except JSONSchemaValidationError as e:
            error_msg = f"Output validation failed: {e.message}"
            if e.path:
                error_msg += f" at path: {'.'.join(str(p) for p in e.path)}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
        except SchemaError as e:
            error_msg = f"Invalid schema definition: {e.message}"
            logger.error(error_msg)
            raise ValueError(error_msg) from e
    
    def _parse_output(self, output: str) -> Dict[str, Any]:
        """Parse output string into dictionary"""
        # Try JSON first
        try:
            return json.loads(output)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from markdown code blocks
        import re
        json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', output, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try YAML (if pyyaml is available)
        try:
            import yaml
            return yaml.safe_load(output)
        except (ImportError, yaml.YAMLError):
            pass
        
        # If all parsing fails, wrap in a simple structure
        # This allows skills with free-form text output
        return {"content": output.strip()}


class ValidationRuleExecutor:
    """Executes validation rules on outputs"""
    
    def __init__(self):
        self.validators = {
            "required_fields": self._validate_required_fields,
            "type_check": self._validate_types,
            "range_check": self._validate_range,
            "regex": self._validate_regex,
            "custom": self._validate_custom,
        }
    
    async def execute(
        self,
        rules: List[ValidationRule],
        outputs: Dict[str, Any]
    ) -> ValidationResult:
        """
        Execute validation rules
        
        Args:
            rules: List of validation rules
            outputs: Output dictionary to validate
            
        Returns:
            ValidationResult with pass/fail status and details
        """
        errors = []
        warnings = []
        details = {}
        
        for rule in rules:
            validator_func = self.validators.get(rule.type)
            if not validator_func:
                warnings.append(f"Unknown validation rule type: {rule.type}")
                continue
            
            try:
                result = await validator_func(outputs, rule.params)
                if not result.get("passed", False):
                    error_msg = rule.error_message or result.get("error", "Validation failed")
                    errors.append(f"{rule.type}: {error_msg}")
                details[rule.type] = result
            except Exception as e:
                logger.error(f"Validation rule {rule.type} failed: {e}")
                errors.append(f"{rule.type}: {str(e)}")
        
        return ValidationResult(
            passed=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            details=details
        )
    
    async def _validate_required_fields(
        self,
        outputs: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate required fields are present"""
        required = params.get("fields", [])
        missing = [field for field in required if field not in outputs]
        
        return {
            "passed": len(missing) == 0,
            "error": f"Missing required fields: {', '.join(missing)}" if missing else None,
            "missing_fields": missing
        }
    
    async def _validate_types(
        self,
        outputs: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate field types"""
        type_map = params.get("types", {})
        errors = []
        
        for field, expected_type in type_map.items():
            if field not in outputs:
                continue
            
            value = outputs[field]
            type_name = expected_type.lower()
            
            if type_name == "string" and not isinstance(value, str):
                errors.append(f"{field} must be a string")
            elif type_name == "number" and not isinstance(value, (int, float)):
                errors.append(f"{field} must be a number")
            elif type_name == "boolean" and not isinstance(value, bool):
                errors.append(f"{field} must be a boolean")
            elif type_name == "array" and not isinstance(value, list):
                errors.append(f"{field} must be an array")
            elif type_name == "object" and not isinstance(value, dict):
                errors.append(f"{field} must be an object")
        
        return {
            "passed": len(errors) == 0,
            "error": "; ".join(errors) if errors else None,
            "errors": errors
        }
    
    async def _validate_range(
        self,
        outputs: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate numeric ranges"""
        field = params.get("field")
        min_val = params.get("min")
        max_val = params.get("max")
        
        if field not in outputs:
            return {"passed": True}
        
        value = outputs[field]
        if not isinstance(value, (int, float)):
            return {"passed": False, "error": f"{field} must be a number"}
        
        if min_val is not None and value < min_val:
            return {"passed": False, "error": f"{field} must be >= {min_val}"}
        
        if max_val is not None and value > max_val:
            return {"passed": False, "error": f"{field} must be <= {max_val}"}
        
        return {"passed": True}
    
    async def _validate_regex(
        self,
        outputs: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate regex patterns"""
        import re
        
        field = params.get("field")
        pattern = params.get("pattern")
        
        if field not in outputs:
            return {"passed": True}
        
        value = outputs[field]
        if not isinstance(value, str):
            return {"passed": False, "error": f"{field} must be a string"}
        
        if not re.match(pattern, value):
            return {"passed": False, "error": f"{field} does not match pattern"}
        
        return {"passed": True}
    
    async def _validate_custom(
        self,
        outputs: Dict[str, Any],
        params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Custom validation (placeholder for future extension)"""
        # This would execute custom Python code or call external validators
        # For now, just return passed
        return {"passed": True, "note": "Custom validation not implemented"}

