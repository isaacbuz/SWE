"""
Tool execution service.

This service provides Python bindings for the TypeScript tool execution packages.
Calls the Node.js HTTP service for actual tool execution.
"""
import json
import httpx
from typing import Dict, Any, Optional, List
from pathlib import Path
import os

# Tool service URL (can be overridden via environment variable)
TOOL_SERVICE_URL = os.getenv("TOOL_SERVICE_URL", "http://localhost:3001")


class ToolRegistryService:
    """Service for managing tool registry."""
    
    def __init__(self, spec_paths: Optional[List[str]] = None):
        """
        Initialize tool registry service.
        
        Args:
            spec_paths: List of OpenAPI spec file paths
        """
        self.spec_paths = spec_paths or [
            str(Path(__file__).parent.parent.parent.parent / "tools" / "openapi" / "ai-dev-tools.yaml")
        ]
        self._tools: Dict[str, Dict[str, Any]] = {}
        self._load_tools()
    
    def _load_tools(self):
        """Load tools from OpenAPI specs."""
        try:
            # Call tool service HTTP API
            with httpx.Client(timeout=5.0) as client:
                response = client.get(f"{TOOL_SERVICE_URL}/tools")
                if response.status_code == 200:
                    data = response.json()
                    self._tools = {
                        tool["name"]: tool for tool in data.get("tools", [])
                    }
                else:
                    # Fallback to mock if service unavailable
                    self._load_mock_tools()
        except Exception:
            # Fallback to mock if service unavailable
            self._load_mock_tools()
    
    def _load_mock_tools(self):
        """Load mock tools as fallback."""
        self._tools = {
            "createIssues": {
                "name": "createIssues",
                "description": "Create multiple GitHub issues",
                "operationId": "createIssues",
                "endpoint": "/github/create-issues",
                "method": "POST",
                "tags": ["github"],
            }
        }
    
    def get_tool_specs(self) -> List[Dict[str, Any]]:
        """Get all tool specifications."""
        return list(self._tools.values())
    
    def get_tool_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool specification by name."""
        return self._tools.get(name)
    
    def get_tools_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Get tools by tag."""
        return [
            tool for tool in self._tools.values()
            if tag in (tool.get("tags") or [])
        ]


class ToolExecutorService:
    """Service for executing tools."""
    
    def __init__(self, registry: ToolRegistryService):
        """
        Initialize tool executor service.
        
        Args:
            registry: Tool registry service
        """
        self.registry = registry
        self._handlers: Dict[str, Any] = {}
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default tool handlers."""
        # Tool execution is handled via HTTP calls to the TypeScript ToolExecutor service
        # See execute() method for implementation
        # Mock handlers are kept for fallback/testing purposes
        self._handlers["createIssues"] = self._mock_create_issues
    
    async def execute(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        options: Optional[Dict[str, Any]] = None,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a tool.
        
        Args:
            tool_name: Name of the tool to execute
            arguments: Tool arguments
            options: Execution options
            user_id: User ID for permissions and audit logging
        
        Returns:
            Execution result
        """
        try:
            # Call tool service HTTP API
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{TOOL_SERVICE_URL}/tools/execute",
                    json={
                        "toolName": tool_name,
                        "arguments": arguments,
                        "userId": user_id,
                        "options": options,
                    },
                )
                
                if response.status_code == 200:
                    return {
                        "success": True,
                        "data": response.json().get("result"),
                    }
                elif response.status_code == 404:
                    return {
                        "success": False,
                        "error": f"Tool '{tool_name}' not found",
                    }
                elif response.status_code == 403:
                    return {
                        "success": False,
                        "error": "Permission denied",
                    }
                elif response.status_code == 429:
                    return {
                        "success": False,
                        "error": "Rate limit exceeded",
                    }
                else:
                    error_data = response.json() if response.content else {}
                    return {
                        "success": False,
                        "error": error_data.get("error", "Tool execution failed"),
                    }
        except httpx.TimeoutException:
            return {
                "success": False,
                "error": "Tool execution timeout",
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }


# Singleton instances
_tool_registry: Optional[ToolRegistryService] = None
_tool_executor: Optional[ToolExecutorService] = None


def get_tool_registry() -> ToolRegistryService:
    """Get singleton tool registry instance."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistryService()
    return _tool_registry


def get_tool_executor() -> ToolExecutorService:
    """Get singleton tool executor instance."""
    global _tool_executor
    if _tool_executor is None:
        _tool_executor = ToolExecutorService(get_tool_registry())
    return _tool_executor

