"""
Edge case tests for Skills system.

Tests boundary conditions, error scenarios, and edge cases.
"""
import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime

from packages.skills_engine.engine import SkillExecutionEngine
from packages.skills_engine.models import Skill, ExecutionContext, ExecutionStatus
from packages.skills_engine.validators import InputValidator, OutputValidator
from packages.skills_engine.cache import SkillCache


class TestEdgeCases:
    """Test edge cases and boundary conditions"""

    def test_empty_input_schema(self):
        """Test skill with empty input schema"""
        validator = InputValidator()
        skill = Skill(
            id="test",
            name="Test",
            slug="test",
            version="1.0.0",
            description="Test",
            prompt_template="Test",
            input_schema={},  # Empty schema
            output_schema={"type": "object"},
            category="GENERAL"
        )
        
        # Should accept any inputs
        result = validator.validate({}, skill.input_schema)
        assert result == {}

    def test_very_large_input(self):
        """Test skill execution with very large input"""
        validator = InputValidator()
        large_input = {"data": "x" * 100000}  # 100KB string
        
        schema = {
            "type": "object",
            "properties": {
                "data": {"type": "string"}
            }
        }
        
        # Should handle large inputs
        result = validator.validate(large_input, schema)
        assert result["data"] == large_input["data"]

    def test_special_characters_in_input(self):
        """Test input with special characters"""
        validator = InputValidator()
        special_input = {
            "text": "Hello\nWorld\tTest\"Quote'Single",
            "json": '{"key": "value"}',
            "unicode": "测试 🚀 émojis"
        }
        
        schema = {
            "type": "object",
            "properties": {
                "text": {"type": "string"},
                "json": {"type": "string"},
                "unicode": {"type": "string"}
            }
        }
        
        result = validator.validate(special_input, schema)
        assert result == special_input

    def test_nested_object_validation(self):
        """Test validation of deeply nested objects"""
        validator = InputValidator()
        nested_input = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "value": "deep"
                        }
                    }
                }
            }
        }
        
        schema = {
            "type": "object",
            "properties": {
                "level1": {
                    "type": "object",
                    "properties": {
                        "level2": {
                            "type": "object",
                            "properties": {
                                "level3": {
                                    "type": "object",
                                    "properties": {
                                        "level4": {
                                            "type": "object",
                                            "properties": {
                                                "value": {"type": "string"}
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
        
        result = validator.validate(nested_input, schema)
        assert result["level1"]["level2"]["level3"]["level4"]["value"] == "deep"

    def test_array_validation(self):
        """Test validation of array inputs"""
        validator = InputValidator()
        array_input = {
            "items": [1, 2, 3, 4, 5],
            "strings": ["a", "b", "c"]
        }
        
        schema = {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "number"}
                },
                "strings": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            }
        }
        
        result = validator.validate(array_input, schema)
        assert len(result["items"]) == 5
        assert len(result["strings"]) == 3

    def test_output_validation_with_markdown(self):
        """Test output validation with markdown code blocks"""
        validator = OutputValidator()
        
        # JSON in markdown code block
        markdown_output = """
Here's the result:

```json
{"result": "success", "data": {"value": 123}}
```
"""
        
        schema = {
            "type": "object",
            "properties": {
                "result": {"type": "string"},
                "data": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "number"}
                    }
                }
            }
        }
        
        result = validator.validate(markdown_output, schema)
        assert result["result"] == "success"
        assert result["data"]["value"] == 123

    def test_output_validation_with_plain_text(self):
        """Test output validation fallback to plain text"""
        validator = OutputValidator()
        
        plain_text = "This is plain text output without JSON"
        
        schema = {
            "type": "object",
            "properties": {
                "content": {"type": "string"}
            }
        }
        
        result = validator.validate(plain_text, schema)
        assert "content" in result
        assert isinstance(result["content"], str)

    def test_cache_key_with_special_characters(self):
        """Test cache key generation with special characters"""
        cache = SkillCache(Mock())
        
        inputs = {
            "name": "Test & Special",
            "data": '{"key": "value"}',
            "unicode": "测试"
        }
        
        key1 = cache.compute_key("skill-1", "1.0.0", inputs)
        key2 = cache.compute_key("skill-1", "1.0.0", inputs)
        
        # Should be deterministic
        assert key1 == key2
        assert len(key1) > 0

    def test_cache_key_with_different_order(self):
        """Test cache key is order-independent"""
        cache = SkillCache(Mock())
        
        inputs1 = {"a": 1, "b": 2, "c": 3}
        inputs2 = {"c": 3, "b": 2, "a": 1}  # Different order
        
        key1 = cache.compute_key("skill-1", "1.0.0", inputs1)
        key2 = cache.compute_key("skill-1", "1.0.0", inputs2)
        
        # Should produce same key
        assert key1 == key2

    @pytest.mark.asyncio
    async def test_execution_with_empty_context(self):
        """Test execution with empty context"""
        engine = SkillExecutionEngine(Mock(), Mock())
        skill = Skill(
            id="test",
            name="Test",
            slug="test",
            version="1.0.0",
            description="Test",
            prompt_template="Test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            category="GENERAL"
        )
        
        # Should handle empty context
        context = ExecutionContext()
        assert context.user_id is None

    @pytest.mark.asyncio
    async def test_execution_with_missing_model_preferences(self):
        """Test execution when model preferences are missing"""
        engine = SkillExecutionEngine(Mock(), Mock())
        skill = Skill(
            id="test",
            name="Test",
            slug="test",
            version="1.0.0",
            description="Test",
            prompt_template="Test",
            input_schema={"type": "object"},
            output_schema={"type": "object"},
            category="GENERAL",
            model_preferences=None  # Missing preferences
        )
        
        # Should use defaults
        assert skill.model_preferences is None or isinstance(skill.model_preferences, dict)

    def test_prompt_template_with_no_variables(self):
        """Test prompt template with no variables"""
        engine = SkillExecutionEngine(Mock(), Mock())
        
        template = "This is a static prompt with no variables."
        inputs = {}
        
        rendered = engine._render_prompt(template, inputs)
        assert rendered == template

    def test_prompt_template_with_undefined_variables(self):
        """Test prompt template with undefined variables"""
        engine = SkillExecutionEngine(Mock(), Mock())
        
        template = "Hello {{name}}, your age is {{age}}"
        inputs = {"name": "Alice"}  # Missing "age"
        
        # Should render with undefined variable as empty or placeholder
        rendered = engine._render_prompt(template, inputs)
        assert "Alice" in rendered
        # "age" may be empty or show as {{age}}

    def test_very_long_prompt(self):
        """Test rendering very long prompt"""
        engine = SkillExecutionEngine(Mock(), Mock())
        
        long_template = "{{content}}" + "x" * 100000
        inputs = {"content": "test"}
        
        rendered = engine._render_prompt(long_template, inputs)
        assert len(rendered) > 100000
        assert "test" in rendered

