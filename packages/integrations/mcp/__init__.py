"""
MCP (Model Context Protocol) Integration

Provides MCP protocol implementation:
- Tool registration and discovery
- MCP server management
- Dynamic tool invocation
"""

from .client import MCPClient
from .server import MCPServer
from .tools import ToolRegistry

__all__ = [
    "MCPClient",
    "MCPServer",
    "ToolRegistry",
]
