"""
工具路由系统

统一管理内置工具和 MCP 工具，支持多 LLM 格式适配
"""

import os
import time
import subprocess
from pathlib import Path
from typing import Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .providers.base import ToolDefinition, ToolCall


class ToolCategory(str, Enum):
    """工具分类"""
    BUILTIN = "builtin"       # 内置工具
    MCP = "mcp"               # MCP 工具
    PLAYWRIGHT = "playwright"  # Playwright 浏览器工具
    CUSTOM = "custom"         # 自定义工具


class ToolAccessLevel(str, Enum):
    """工具访问级别（读写分离）"""
    READ = "read"        # 只读操作
    WRITE = "write"      # 写操作
    EXECUTE = "execute"  # 执行操作（可能有副作用）
    ADMIN = "admin"      # 管理操作


@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    parameters: dict  # JSON Schema
    category: ToolCategory = ToolCategory.BUILTIN
    access_level: ToolAccessLevel = ToolAccessLevel.READ
    requires_confirmation: bool = False  # 是否需要用户确认
    tags: list[str] = field(default_factory=list)


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    tool_name: str = ""
    duration_ms: float = 0
    metadata: dict = field(default_factory=dict)


class ToolRouter:
    """
    工具路由器

    统一管理所有工具的注册、查询、执行
    支持：
    - 内置工具 (bash, read, write, glob, grep)
    - MCP 工具 (通过 MCPClient)
    - Playwright 工具 (浏览器自动化)
    - 自定义工具
    """

    def __init__(self, working_dir: Optional[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self._tools: dict[str, ToolMetadata] = {}
        self._handlers: dict[str, Callable] = {}
        self._mcp_client = None

        # 注册内置工具
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """注册内置工具"""
        # Bash 工具
        self.register_tool(
            ToolMetadata(
                name="bash",
                description="Execute a bash command. Use for running scripts, git commands, file operations, etc.",
                parameters={
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute"
                        },
                        "working_dir": {
                            "type": "string",
                            "description": "Working directory for the command (optional)"
                        }
                    },
                    "required": ["command"]
                },
                category=ToolCategory.BUILTIN,
                access_level=ToolAccessLevel.EXECUTE,
                requires_confirmation=True,
                tags=["shell", "command", "execute"]
            ),
            self._execute_bash
        )

        # Read 工具
        self.register_tool(
            ToolMetadata(
                name="read",
                description="Read the contents of a file.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to read"
                        },
                        "start_line": {
                            "type": "integer",
                            "description": "Starting line number (1-indexed, optional)"
                        },
                        "end_line": {
                            "type": "integer",
                            "description": "Ending line number (inclusive, optional)"
                        }
                    },
                    "required": ["file_path"]
                },
                category=ToolCategory.BUILTIN,
                access_level=ToolAccessLevel.READ,
                tags=["file", "read"]
            ),
            self._execute_read
        )

        # Write 工具
        self.register_tool(
            ToolMetadata(
                name="write",
                description="Write content to a file. Creates the file if it doesn't exist.",
                parameters={
                    "type": "object",
                    "properties": {
                        "file_path": {
                            "type": "string",
                            "description": "Path to the file to write"
                        },
                        "content": {
                            "type": "string",
                            "description": "Content to write to the file"
                        }
                    },
                    "required": ["file_path", "content"]
                },
                category=ToolCategory.BUILTIN,
                access_level=ToolAccessLevel.WRITE,
                requires_confirmation=True,
                tags=["file", "write"]
            ),
            self._execute_write
        )

        # Glob 工具
        self.register_tool(
            ToolMetadata(
                name="glob",
                description="Find files matching a glob pattern.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Glob pattern to match (e.g., '**/*.py')"
                        },
                        "path": {
                            "type": "string",
                            "description": "Base path to search in (optional)"
                        }
                    },
                    "required": ["pattern"]
                },
                category=ToolCategory.BUILTIN,
                access_level=ToolAccessLevel.READ,
                tags=["file", "search", "glob"]
            ),
            self._execute_glob
        )

        # Grep 工具
        self.register_tool(
            ToolMetadata(
                name="grep",
                description="Search for text patterns in files.",
                parameters={
                    "type": "object",
                    "properties": {
                        "pattern": {
                            "type": "string",
                            "description": "Regular expression pattern to search for"
                        },
                        "path": {
                            "type": "string",
                            "description": "File or directory to search in"
                        },
                        "include": {
                            "type": "string",
                            "description": "File pattern to include (e.g., '*.py')"
                        }
                    },
                    "required": ["pattern"]
                },
                category=ToolCategory.BUILTIN,
                access_level=ToolAccessLevel.READ,
                tags=["search", "grep", "text"]
            ),
            self._execute_grep
        )

    def register_tool(
        self,
        metadata: ToolMetadata,
        handler: Callable[[dict], ToolResult]
    ):
        """注册工具"""
        self._tools[metadata.name] = metadata
        self._handlers[metadata.name] = handler

    def register_mcp_tools(self, mcp_client):
        """
        注册 MCP 工具

        从 MCPClient 动态加载所有 MCP 工具
        """
        self._mcp_client = mcp_client

        # 获取所有 MCP 工具
        for tool in mcp_client.get_available_tools():
            tool_name = f"mcp__{tool.server_id}__{tool.name.replace('.', '_')}"

            self.register_tool(
                ToolMetadata(
                    name=tool_name,
                    description=tool.description,
                    parameters=tool.input_schema or {
                        "type": "object",
                        "properties": {},
                    },
                    category=ToolCategory.MCP,
                    access_level=self._infer_access_level(tool.name),
                    tags=["mcp", tool.server_id]
                ),
                lambda params, tid=tool.id: self._execute_mcp_tool(tid, params)
            )

    def _infer_access_level(self, tool_name: str) -> ToolAccessLevel:
        """根据工具名称推断访问级别"""
        read_keywords = ["get", "list", "query", "fetch", "search", "find", "check"]
        write_keywords = ["create", "update", "delete", "set", "add", "remove", "modify"]
        execute_keywords = ["execute", "run", "trigger", "sync", "send", "publish"]

        name_lower = tool_name.lower()

        if any(kw in name_lower for kw in execute_keywords):
            return ToolAccessLevel.EXECUTE
        elif any(kw in name_lower for kw in write_keywords):
            return ToolAccessLevel.WRITE
        elif any(kw in name_lower for kw in read_keywords):
            return ToolAccessLevel.READ

        return ToolAccessLevel.EXECUTE

    def get_tool(self, name: str) -> Optional[ToolMetadata]:
        """获取工具元数据"""
        return self._tools.get(name)

    def list_tools(
        self,
        category: Optional[ToolCategory] = None,
        access_level: Optional[ToolAccessLevel] = None,
        tags: Optional[list[str]] = None
    ) -> list[ToolMetadata]:
        """列出工具（支持过滤）"""
        tools = list(self._tools.values())

        if category:
            tools = [t for t in tools if t.category == category]

        if access_level:
            tools = [t for t in tools if t.access_level == access_level]

        if tags:
            tools = [t for t in tools if any(tag in t.tags for tag in tags)]

        return tools

    def get_tool_definitions(
        self,
        allowed_tools: Optional[list[str]] = None,
        access_levels: Optional[list[ToolAccessLevel]] = None
    ) -> list[ToolDefinition]:
        """
        获取工具定义列表（用于 LLM API）

        Args:
            allowed_tools: 允许的工具名称列表
            access_levels: 允许的访问级别列表

        Returns:
            ToolDefinition 列表
        """
        tools = []

        for name, metadata in self._tools.items():
            # 检查是否在允许列表中
            if allowed_tools and name not in allowed_tools:
                # 检查是否匹配模式（如 mcp__playwright__*）
                if not any(self._match_tool_pattern(name, pattern) for pattern in allowed_tools):
                    continue

            # 检查访问级别
            if access_levels and metadata.access_level not in access_levels:
                continue

            tools.append(ToolDefinition(
                name=name,
                description=metadata.description,
                parameters=metadata.parameters
            ))

        return tools

    def _match_tool_pattern(self, tool_name: str, pattern: str) -> bool:
        """匹配工具模式（支持通配符）"""
        if "*" not in pattern:
            return tool_name == pattern

        # 简单通配符匹配
        if pattern.endswith("*"):
            return tool_name.startswith(pattern[:-1])

        return False

    def execute(
        self,
        tool_call: ToolCall,
        check_permission: bool = True
    ) -> ToolResult:
        """
        执行工具调用

        Args:
            tool_call: 工具调用对象
            check_permission: 是否检查权限

        Returns:
            ToolResult
        """
        tool_name = tool_call.name
        params = tool_call.arguments

        # 检查工具是否存在
        if tool_name not in self._tools:
            return ToolResult(
                success=False,
                output="",
                error=f"工具 '{tool_name}' 不存在",
                tool_name=tool_name
            )

        metadata = self._tools[tool_name]

        # 权限检查（可以在这里集成 SafetyGuard）
        if check_permission and metadata.requires_confirmation:
            # TODO: 集成确认机制
            pass

        # 获取处理函数
        handler = self._handlers.get(tool_name)
        if not handler:
            return ToolResult(
                success=False,
                output="",
                error=f"工具 '{tool_name}' 没有注册处理函数",
                tool_name=tool_name
            )

        # 执行
        start_time = time.time()
        try:
            result = handler(params)
            result.tool_name = tool_name
            result.duration_ms = (time.time() - start_time) * 1000
            return result
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                error=str(e),
                tool_name=tool_name,
                duration_ms=(time.time() - start_time) * 1000
            )

    # ==================== 内置工具实现 ====================

    def _execute_bash(self, params: dict) -> ToolResult:
        """执行 Bash 命令"""
        command = params.get("command", "")
        working_dir = params.get("working_dir", self.working_dir)

        if not command:
            return ToolResult(success=False, output="", error="No command provided")

        # 安全检查
        dangerous_patterns = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if="]
        for pattern in dangerous_patterns:
            if pattern in command:
                return ToolResult(
                    success=False,
                    output="",
                    error=f"Dangerous command pattern detected: {pattern}"
                )

        try:
            result = subprocess.run(
                command,
                shell=True,
                cwd=working_dir,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout
            if result.stderr:
                output += f"\n[stderr]\n{result.stderr}"

            return ToolResult(
                success=result.returncode == 0,
                output=output.strip(),
                error=None if result.returncode == 0 else f"Exit code: {result.returncode}"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Command timed out (30s)")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _execute_read(self, params: dict) -> ToolResult:
        """读取文件"""
        file_path = params.get("file_path", "")
        start_line = params.get("start_line")
        end_line = params.get("end_line")

        if not file_path:
            return ToolResult(success=False, output="", error="No file path provided")

        if not os.path.isabs(file_path):
            file_path = os.path.join(self.working_dir, file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            if start_line is not None or end_line is not None:
                start_idx = (start_line - 1) if start_line else 0
                end_idx = end_line if end_line else len(lines)
                lines = lines[start_idx:end_idx]

            content = ''.join(lines)
            return ToolResult(success=True, output=content)
        except FileNotFoundError:
            return ToolResult(success=False, output="", error=f"File not found: {file_path}")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _execute_write(self, params: dict) -> ToolResult:
        """写入文件"""
        file_path = params.get("file_path", "")
        content = params.get("content", "")

        if not file_path:
            return ToolResult(success=False, output="", error="No file path provided")

        if not os.path.isabs(file_path):
            file_path = os.path.join(self.working_dir, file_path)

        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)

            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} bytes to {file_path}"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _execute_glob(self, params: dict) -> ToolResult:
        """查找文件"""
        pattern = params.get("pattern", "")
        base_path = params.get("path", self.working_dir)

        if not pattern:
            return ToolResult(success=False, output="", error="No pattern provided")

        try:
            path = Path(base_path)
            matches = list(path.glob(pattern))
            result = "\n".join(str(m.relative_to(base_path)) for m in matches[:100])

            if len(matches) > 100:
                result += f"\n... and {len(matches) - 100} more files"

            return ToolResult(
                success=True,
                output=result if result else "No matches found"
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _execute_grep(self, params: dict) -> ToolResult:
        """搜索文本"""
        pattern = params.get("pattern", "")
        search_path = params.get("path", self.working_dir)
        include = params.get("include", "")

        if not pattern:
            return ToolResult(success=False, output="", error="No pattern provided")

        try:
            cmd = ["grep", "-rn", pattern, search_path]
            if include:
                cmd.extend(["--include", include])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )

            output = result.stdout.strip()
            lines = output.split('\n')
            if len(lines) > 50:
                output = '\n'.join(lines[:50]) + f"\n... and {len(lines) - 50} more matches"

            return ToolResult(
                success=True,
                output=output if output else "No matches found"
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, output="", error="Search timed out")
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))

    def _execute_mcp_tool(self, tool_id: str, params: dict) -> ToolResult:
        """执行 MCP 工具"""
        if not self._mcp_client:
            return ToolResult(
                success=False,
                output="",
                error="MCP client not initialized"
            )

        try:
            mcp_result = self._mcp_client.call_tool(tool_id, params)

            return ToolResult(
                success=mcp_result.status.value == "success",
                output=str(mcp_result.output_data) if mcp_result.output_data else "",
                error=mcp_result.error_message,
                duration_ms=mcp_result.duration_ms,
                metadata={
                    "server_id": mcp_result.server_id,
                    "request_id": mcp_result.request_id,
                    "trace_id": mcp_result.trace_id,
                }
            )
        except Exception as e:
            return ToolResult(success=False, output="", error=str(e))


# 全局工具路由器实例
_router: Optional[ToolRouter] = None


def get_tool_router(working_dir: Optional[str] = None) -> ToolRouter:
    """获取或创建工具路由器实例"""
    global _router
    if _router is None:
        _router = ToolRouter(working_dir)
    return _router
