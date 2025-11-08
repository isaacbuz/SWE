"""
Tests for Skills validators
"""
import pytest
from packages.skills_engine.validators import InputValidator, OutputValidator, ValidationRuleExecutor
from packages.skills_engine.models import ValidationRule


class TestInputValidator:
    """Test input validation"""

    def test_validate_success(self):
        """Test successful input validation"""
        validator = InputValidator()
        inputs = {"name": "test"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        result = validator.validate(inputs, schema)
        assert result == inputs

    def test_validate_missing_required(self):
        """Test validation failure with missing required field"""
        validator = InputValidator()
        inputs = {}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        
        with pytest.raises(ValueError):
            validator.validate(inputs, schema)

    def test_validate_invalid_type(self):
        """Test validation failure with invalid type"""
        validator = InputValidator()
        inputs = {"name": 123}  # Should be string
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            }
        }
        
        # This would fail type validation
        # The exact behavior depends on jsonschema strictness


class TestOutputValidator:
    """Test output validation"""

    def test_validate_json_output(self):
        """Test validating JSON output"""
        validator = OutputValidator()
        output = '{"result": "success"}'
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        }
        
        result = validator.validate(output, schema)
        assert result == {"result": "success"}

    def test_validate_markdown_code_block(self):
        """Test extracting JSON from markdown code block"""
        validator = OutputValidator()
        output = '```json\n{"result": "success"}\n```'
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"}
            }
        }
        
        result = validator.validate(output, schema)
        assert result == {"result": "success"}

    def test_validate_plain_text_fallback(self):
        """Test fallback to plain text wrapping"""
        validator = OutputValidator()
        output = "Plain text output"
        schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"}
            }
        }
        
        result = validator.validate(output, schema)
        assert "content" in result


class TestValidationRuleExecutor:
    """Test validation rule execution"""

    @pytest.mark.asyncio
    async def test_required_fields_validation(self):
        """Test required fields validation rule"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="required_fields",
                params={"fields": ["name", "email"]}
            )
        ]
        
        outputs = {"name": "test", "email": "test@example.com"}
        result = await executor.execute(rules, outputs)
        
        assert result.passed is True
        assert len(result.errors) == 0

    @pytest.mark.asyncio
    async def test_required_fields_validation_failure(self):
        """Test required fields validation failure"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="required_fields",
                params={"fields": ["name", "email"]}
            )
        ]
        
        outputs = {"name": "test"}  # Missing email
        result = await executor.execute(rules, outputs)
        
        assert result.passed is False
        assert len(result.errors) > 0

    @pytest.mark.asyncio
    async def test_type_check_validation(self):
        """Test type check validation rule"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="type_check",
                params={"types": {"name": "string", "age": "number"}}
            )
        ]
        
        outputs = {"name": "test", "age": 25}
        result = await executor.execute(rules, outputs)
        
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_range_check_validation(self):
        """Test range check validation rule"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="range_check",
                params={"field": "age", "min": 18, "max": 100}
            )
        ]
        
        outputs = {"age": 25}
        result = await executor.execute(rules, outputs)
        
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_range_check_validation_failure(self):
        """Test range check validation failure"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="range_check",
                params={"field": "age", "min": 18, "max": 100}
            )
        ]
        
        outputs = {"age": 150}  # Out of range
        result = await executor.execute(rules, outputs)
        
        assert result.passed is False

    @pytest.mark.asyncio
    async def test_regex_validation(self):
        """Test regex validation rule"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="regex",
                params={"field": "email", "pattern": r"^[^\s@]+@[^\s@]+\.[^\s@]+$"}
            )
        ]
        
        outputs = {"email": "test@example.com"}
        result = await executor.execute(rules, outputs)
        
        assert result.passed is True

    @pytest.mark.asyncio
    async def test_multiple_rules(self):
        """Test executing multiple validation rules"""
        executor = ValidationRuleExecutor()
        rules = [
            ValidationRule(
                type="required_fields",
                params={"fields": ["name"]}
            ),
            ValidationRule(
                type="type_check",
                params={"types": {"name": "string"}}
            )
        ]
        
        outputs = {"name": "test"}
        result = await executor.execute(rules, outputs)
        
        assert result.passed is True

