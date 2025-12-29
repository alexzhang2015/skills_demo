"""
MCP (Model Context Protocol) 集成模块

提供与核心业务系统的标准化接口
"""

from .servers import MCPServerRegistry, MCPServer
from .tools import MCPToolRegistry, MCPTool, MCPToolResult
from .client import MCPClient

__all__ = [
    "MCPServerRegistry",
    "MCPServer",
    "MCPToolRegistry",
    "MCPTool",
    "MCPToolResult",
    "MCPClient",
]
