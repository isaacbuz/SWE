"""
MCP Tool Registry

Provides tool registration and management for MCP servers.
"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class Tool:
    """Tool definition for MCP protocol"""

    name: str
    description: str
    parameters: Dict[str, Any]  # JSON Schema
    handler: Callable

    def to_dict(self) -> Dict[str, Any]:
        """Convert tool to dictionary format"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """
    Registry for managing MCP tools

    Features:
    - Tool registration and discovery
    - Tool invocation with validation
    - Tool metadata management
    """

    def __init__(self):
        """Initialize tool registry"""
        self._tools: Dict[str, Tool] = {}
        self.logger = logging.getLogger(f"{__name__}.ToolRegistry")

    def register(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ) -> None:
        """
        Register a tool

        Args:
            name: Tool name (must be unique)
            description: Tool description
            parameters: JSON Schema for parameters
            handler: Async function to handle tool invocation

        Raises:
            ValueError: If tool name already exists
        """
        if name in self._tools:
            raise ValueError(f"Tool '{name}' is already registered")

        tool = Tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

        self._tools[name] = tool
        self.logger.info(f"Registered tool: {name}")

    def unregister(self, name: str) -> bool:
        """
        Unregister a tool

        Args:
            name: Tool name

        Returns:
            True if tool was removed, False if not found
        """
        if name in self._tools:
            del self._tools[name]
            self.logger.info(f"Unregistered tool: {name}")
            return True
        return False

    def get_tool(self, name: str) -> Optional[Tool]:
        """
        Get tool by name

        Args:
            name: Tool name

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(name)

    def list_tools(self) -> List[Tool]:
        """
        List all registered tools

        Returns:
            List of Tool instances
        """
        return list(self._tools.values())

    def list_tool_names(self) -> List[str]:
        """
        List all registered tool names

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    async def invoke(
        self,
        name: str,
        arguments: Dict[str, Any],
    ) -> Any:
        """
        Invoke a tool

        Args:
            name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found
            TypeError: If handler is not callable
        """
        tool = self.get_tool(name)
        if not tool:
            raise ValueError(f"Tool '{name}' not found")

        if not callable(tool.handler):
            raise TypeError(f"Tool '{name}' handler is not callable")

        try:
            # Call handler with arguments
            if asyncio.iscoroutinefunction(tool.handler):
                result = await tool.handler(**arguments)
            else:
                result = tool.handler(**arguments)

            self.logger.debug(f"Tool '{name}' executed successfully")
            return result

        except Exception as e:
            self.logger.error(f"Error invoking tool '{name}': {e}", exc_info=True)
            raise

    def has_tool(self, name: str) -> bool:
        """
        Check if tool is registered

        Args:
            name: Tool name

        Returns:
            True if tool exists, False otherwise
        """
        return name in self._tools

    def count(self) -> int:
        """
        Get number of registered tools

        Returns:
            Number of tools
        """
        return len(self._tools)

    def clear(self) -> None:
        """Clear all registered tools"""
        self._tools.clear()
        self.logger.info("Cleared all tools")


# Import asyncio for coroutine check
import asyncio

