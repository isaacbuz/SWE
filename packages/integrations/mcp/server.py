"""
MCP Server

Provides MCP server implementation for exposing tools via the MCP protocol.
"""

import asyncio
import json
from typing import Any, Callable, Dict, List, Optional

from .tools import ToolRegistry


class MCPServer:
    """
    MCP (Model Context Protocol) Server

    Exposes tools via the MCP protocol for use by AI agents.
    """

    def __init__(
        self,
        name: str = "MCP Server",
        version: str = "1.0.0",
        description: Optional[str] = None,
    ):
        """
        Initialize MCP server

        Args:
            name: Server name
            version: Server version
            description: Server description
        """
        self.name = name
        self.version = version
        self.description = description or "MCP Server"
        self.registry = ToolRegistry()

    def register_tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
        handler: Callable,
    ):
        """
        Register a tool

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
            handler: Async function to handle tool invocation
        """
        self.registry.register(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

    def tool(
        self,
        name: str,
        description: str,
        parameters: Dict[str, Any],
    ):
        """
        Decorator for registering tools

        Usage:
            @server.tool(
                name="search_code",
                description="Search code repositories",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                    },
                    "required": ["query"],
                }
            )
            async def search_code(query: str):
                return {"results": [...]}

        Args:
            name: Tool name
            description: Tool description
            parameters: JSON schema for parameters
        """
        def decorator(func: Callable):
            self.register_tool(name, description, parameters, func)
            return func

        return decorator

    async def handle_list_tools(self) -> Dict[str, Any]:
        """
        Handle list tools request

        Returns:
            Tool list response
        """
        tools = self.registry.list_tools()

        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
                for tool in tools
            ]
        }

    async def handle_get_tool(self, tool_name: str) -> Optional[Dict[str, Any]]:
        """
        Handle get tool request

        Args:
            tool_name: Tool name

        Returns:
            Tool definition or None
        """
        tool = self.registry.get_tool(tool_name)

        if not tool:
            return None

        return {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters,
        }

    async def handle_invoke_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Handle tool invocation request

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        try:
            result = await self.registry.invoke(tool_name, arguments)

            return {
                "success": True,
                "result": result,
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
            }

    async def handle_batch_invoke(
        self,
        invocations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Handle batch tool invocation

        Args:
            invocations: List of invocation dicts

        Returns:
            List of results
        """
        results = []

        # Execute in parallel
        tasks = []
        for inv in invocations:
            task = self.handle_invoke_tool(
                inv.get("tool_name", ""),
                inv.get("arguments", {}),
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Convert exceptions to error dicts
        formatted_results = []
        for result in results:
            if isinstance(result, Exception):
                formatted_results.append({
                    "success": False,
                    "error": str(result),
                })
            else:
                formatted_results.append(result)

        return formatted_results

    async def handle_get_info(self) -> Dict[str, Any]:
        """
        Handle server info request

        Returns:
            Server information
        """
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "protocol_version": "1.0",
            "capabilities": {
                "tools": True,
                "streaming": True,
                "batch": True,
            },
            "tool_count": len(self.registry.list_tools()),
        }

    async def handle_health_check(self) -> Dict[str, Any]:
        """
        Handle health check request

        Returns:
            Health status
        """
        return {
            "status": "healthy",
            "timestamp": asyncio.get_event_loop().time(),
        }

    # HTTP Server Integration (for FastAPI/Starlette)

    def create_fastapi_app(self):
        """
        Create FastAPI application for MCP server

        Returns:
            FastAPI app instance
        """
        from fastapi import FastAPI, HTTPException
        from fastapi.responses import JSONResponse, StreamingResponse
        from pydantic import BaseModel

        app = FastAPI(title=self.name, version=self.version)

        class InvokeRequest(BaseModel):
            arguments: Dict[str, Any] = {}

        class BatchInvokeRequest(BaseModel):
            invocations: List[Dict[str, Any]]

        @app.get("/tools")
        async def list_tools():
            return await self.handle_list_tools()

        @app.get("/tools/{tool_name}")
        async def get_tool(tool_name: str):
            result = await self.handle_get_tool(tool_name)
            if result is None:
                raise HTTPException(status_code=404, detail="Tool not found")
            return result

        @app.post("/tools/{tool_name}")
        async def invoke_tool(tool_name: str, request: InvokeRequest):
            return await self.handle_invoke_tool(tool_name, request.arguments)

        @app.post("/tools/{tool_name}/stream")
        async def invoke_tool_stream(tool_name: str, request: InvokeRequest):
            async def generate():
                try:
                    # Get tool
                    tool = self.registry.get_tool(tool_name)
                    if not tool:
                        yield f"data: {json.dumps({'error': 'Tool not found'})}\n\n"
                        return

                    # Check if tool supports streaming
                    result = await tool.handler(**request.arguments)

                    # If result is async generator, stream it
                    if hasattr(result, "__aiter__"):
                        async for chunk in result:
                            yield f"data: {json.dumps(chunk)}\n\n"
                    else:
                        # Single result
                        yield f"data: {json.dumps({'result': result})}\n\n"

                    yield "data: [DONE]\n\n"

                except Exception as e:
                    yield f"data: {json.dumps({'error': str(e)})}\n\n"

            return StreamingResponse(
                generate(),
                media_type="text/event-stream",
            )

        @app.post("/batch")
        async def batch_invoke(request: BatchInvokeRequest):
            results = await self.handle_batch_invoke(request.invocations)
            return {"results": results}

        @app.get("/info")
        async def get_info():
            return await self.handle_get_info()

        @app.get("/health")
        async def health_check():
            return await self.handle_health_check()

        return app

    def run(
        self,
        host: str = "0.0.0.0",
        port: int = 8000,
        **kwargs,
    ):
        """
        Run MCP server

        Args:
            host: Host to bind to
            port: Port to bind to
            **kwargs: Additional uvicorn arguments
        """
        import uvicorn

        app = self.create_fastapi_app()

        uvicorn.run(
            app,
            host=host,
            port=port,
            **kwargs,
        )


# Example MCP server setup
def create_example_server() -> MCPServer:
    """Create example MCP server with sample tools"""
    server = MCPServer(
        name="Example MCP Server",
        version="1.0.0",
        description="Example server with sample tools",
    )

    @server.tool(
        name="echo",
        description="Echo the input message",
        parameters={
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Message to echo",
                }
            },
            "required": ["message"],
        },
    )
    async def echo(message: str):
        return {"echo": message}

    @server.tool(
        name="calculate",
        description="Perform arithmetic calculation",
        parameters={
            "type": "object",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["add", "subtract", "multiply", "divide"],
                    "description": "Arithmetic operation",
                },
                "a": {"type": "number", "description": "First operand"},
                "b": {"type": "number", "description": "Second operand"},
            },
            "required": ["operation", "a", "b"],
        },
    )
    async def calculate(operation: str, a: float, b: float):
        ops = {
            "add": a + b,
            "subtract": a - b,
            "multiply": a * b,
            "divide": a / b if b != 0 else None,
        }
        result = ops.get(operation)
        return {"result": result}

    return server
