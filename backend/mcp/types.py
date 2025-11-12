"""
MCP Types for Movi transport management system.
Custom types for MCP server implementation.
"""

from typing import Dict, Any, List, Optional
from pydantic import BaseModel


class Tool(BaseModel):
    """MCP Tool definition"""
    name: str
    description: str
    inputSchema: Dict[str, Any]


class TextContent(BaseModel):
    """Text content for tool responses"""
    type: str = "text"
    text: str


class ToolResult(BaseModel):
    """Result from tool execution"""
    content: List[TextContent]
    isError: bool = False

