"""
MCP Client

Provides client for connecting to MCP servers and invoking tools.
"""

import asyncio
import json
from typing import Any, Dict, List, Optional

import httpx


class MCPClient:
    """
    MCP (Model Context Protocol) Client

    Connects to MCP servers and provides tool invocation capabilities.
    """

    def __init__(
        self,
        server_url: str,
        timeout: int = 30,
    ):
        """
        Initialize MCP client

        Args:
            server_url: MCP server URL
            timeout: Request timeout in seconds
        """
        self.server_url = server_url.rstrip("/")
        self.timeout = timeout
        self.tools_cache: Optional[List[Dict[str, Any]]] = None

    async def list_tools(
        self,
        force_refresh: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        List available tools from MCP server

        Args:
            force_refresh: Force refresh from server

        Returns:
            List of tool definitions
        """
        if self.tools_cache is not None and not force_refresh:
            return self.tools_cache

        url = f"{self.server_url}/tools"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

            self.tools_cache = data.get("tools", [])
            return self.tools_cache

    async def get_tool(
        self,
        tool_name: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Get tool definition by name

        Args:
            tool_name: Tool name

        Returns:
            Tool definition or None
        """
        tools = await self.list_tools()

        for tool in tools:
            if tool.get("name") == tool_name:
                return tool

        return None

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a tool

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Returns:
            Tool execution result
        """
        url = f"{self.server_url}/tools/{tool_name}"

        payload = {
            "arguments": arguments or {},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()

    async def invoke_tool_stream(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
    ):
        """
        Invoke a tool with streaming response

        Args:
            tool_name: Tool name
            arguments: Tool arguments

        Yields:
            Stream chunks
        """
        url = f"{self.server_url}/tools/{tool_name}/stream"

        payload = {
            "arguments": arguments or {},
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            async with client.stream("POST", url, json=payload) as response:
                response.raise_for_status()

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:]  # Remove "data: " prefix
                        if data == "[DONE]":
                            break
                        yield json.loads(data)

    async def get_server_info(self) -> Dict[str, Any]:
        """
        Get MCP server information

        Returns:
            Server info including version and capabilities
        """
        url = f"{self.server_url}/info"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.json()

    async def health_check(self) -> bool:
        """
        Check if MCP server is healthy

        Returns:
            True if healthy, False otherwise
        """
        try:
            url = f"{self.server_url}/health"

            async with httpx.AsyncClient(timeout=5) as client:
                response = await client.get(url)
                return response.status_code == 200
        except Exception:
            return False

    async def discover_servers(
        self,
        registry_url: str = "https://mcp-registry.example.com",
    ) -> List[Dict[str, Any]]:
        """
        Discover available MCP servers from registry

        Args:
            registry_url: MCP registry URL

        Returns:
            List of available servers
        """
        url = f"{registry_url}/servers"

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()
            return data.get("servers", [])

    async def batch_invoke(
        self,
        invocations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Invoke multiple tools in batch

        Args:
            invocations: List of invocation dicts with tool_name and arguments

        Returns:
            List of results
        """
        url = f"{self.server_url}/batch"

        payload = {
            "invocations": invocations,
        }

        async with httpx.AsyncClient(timeout=self.timeout * 2) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("results", [])


class MCPToolProxy:
    """
    Proxy object for easier tool invocation

    Usage:
        tools = MCPToolProxy(client)
        result = await tools.search_code(query="function main")
    """

    def __init__(self, client: MCPClient):
        """
        Initialize tool proxy

        Args:
            client: MCPClient instance
        """
        self.client = client

    def __getattr__(self, tool_name: str):
        """
        Create callable for tool invocation

        Args:
            tool_name: Tool name

        Returns:
            Async callable for tool invocation
        """
        async def invoke(**kwargs):
            return await self.client.invoke_tool(tool_name, kwargs)

        return invoke


class MCPClientPool:
    """
    Pool of MCP clients for load balancing and failover
    """

    def __init__(
        self,
        server_urls: List[str],
        timeout: int = 30,
    ):
        """
        Initialize client pool

        Args:
            server_urls: List of MCP server URLs
            timeout: Request timeout
        """
        self.clients = [MCPClient(url, timeout) for url in server_urls]
        self.current_index = 0
        self.lock = asyncio.Lock()

    async def get_client(self) -> MCPClient:
        """
        Get next available client (round-robin)

        Returns:
            MCPClient instance
        """
        async with self.lock:
            # Try current client
            client = self.clients[self.current_index]

            if await client.health_check():
                self.current_index = (self.current_index + 1) % len(self.clients)
                return client

            # Try other clients
            for i in range(len(self.clients)):
                idx = (self.current_index + i) % len(self.clients)
                client = self.clients[idx]

                if await client.health_check():
                    self.current_index = (idx + 1) % len(self.clients)
                    return client

            # No healthy clients
            raise Exception("No healthy MCP servers available")

    async def invoke_tool(
        self,
        tool_name: str,
        arguments: Optional[Dict[str, Any]] = None,
        retry_count: int = 3,
    ) -> Dict[str, Any]:
        """
        Invoke tool with automatic failover

        Args:
            tool_name: Tool name
            arguments: Tool arguments
            retry_count: Number of retries

        Returns:
            Tool execution result
        """
        last_error = None

        for _ in range(retry_count):
            try:
                client = await self.get_client()
                return await client.invoke_tool(tool_name, arguments)
            except Exception as e:
                last_error = e
                continue

        raise Exception(f"Failed to invoke tool after {retry_count} retries: {last_error}")
