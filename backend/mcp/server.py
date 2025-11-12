"""
MCP Server implementation with streamable HTTP server.
"""

import json
from typing import Dict, Any, List, Optional, AsyncIterator
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from backend.mcp.tools.route_management_tools import RouteManagementTools, ROUTE_MANAGEMENT_STATE
from backend.mcp.tools.bus_dashboard_tools import BusDashboardTools, BUS_DASHBOARD_STATE


class MCPServer:
    """
    MCP Server that provides tools for transport management.
    Supports streamable HTTP responses.
    """
    
    def __init__(self):
        self.route_tools = RouteManagementTools()
        self.bus_tools = BusDashboardTools()
        self._tool_registry: Dict[str, Any] = {}
        self._register_tools()
    
    def _register_tools(self):
        """Register all available tools"""
        # Register route management tools
        for tool in self.route_tools.get_tools():
            self._tool_registry[tool.name] = {
                "tool": tool,
                "handler": self.route_tools.call_tool,
                "state": ROUTE_MANAGEMENT_STATE
            }
        
        # Register bus dashboard tools
        for tool in self.bus_tools.get_tools():
            self._tool_registry[tool.name] = {
                "tool": tool,
                "handler": self.bus_tools.call_tool,
                "state": BUS_DASHBOARD_STATE
            }
    
    def get_tools_for_state(self, state: str) -> List[Dict[str, Any]]:
        """Get tools available for a specific state"""
        tools = []
        for name, registry in self._tool_registry.items():
            if registry["state"] == state:
                tools.append(registry["tool"].model_dump())
        return tools
    
    async def list_tools(self, state: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all available tools, optionally filtered by state"""
        if state:
            return self.get_tools_for_state(state)
        
        return [registry["tool"].model_dump() for registry in self._tool_registry.values()]
    
    async def call_tool(
        self,
        name: str,
        arguments: Dict[str, Any],
        state: str
    ) -> List[Dict[str, Any]]:
        """
        Call a tool by name with arguments and state.
        
        Args:
            name: Tool name
            arguments: Tool arguments
            state: Current state (route_management or bus_dashboard)
            
        Returns:
            List of text content dictionaries
        """
        if name not in self._tool_registry:
            return [{"type": "text", "text": f"Unknown tool: {name}"}]
        
        registry = self._tool_registry[name]
        handler = registry["handler"]
        
        # Execute tool
        result = await handler(name, arguments, state)
        
        # Convert TextContent objects to dicts
        return [content.model_dump() if hasattr(content, "model_dump") else content for content in result]
    
    async def stream_tool_call(
        self,
        name: str,
        arguments: Dict[str, Any],
        state: str
    ) -> AsyncIterator[str]:
        """
        Stream tool execution results.
        
        Yields:
            JSON strings with tool execution progress and results
        """
        try:
            # Send start event
            yield f"data: {json.dumps({'type': 'tool_start', 'tool': name})}\n\n"
            
            # Execute tool
            results = await self.call_tool(name, arguments, state)
            
            # Send progress events
            for i, result in enumerate(results):
                yield f"data: {json.dumps({'type': 'tool_progress', 'index': i, 'result': result})}\n\n"
            
            # Send completion event
            yield f"data: {json.dumps({'type': 'tool_complete', 'results': results})}\n\n"
            
        except Exception as e:
            # Send error event
            yield f"data: {json.dumps({'type': 'tool_error', 'error': str(e)})}\n\n"


# Global MCP server instance
mcp_server = MCPServer()

