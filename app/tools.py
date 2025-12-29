"""
工具系统实现
提供 Bash、Read、Write 等工具供 Claude 调用
"""
import os
import subprocess
import shlex
from pathlib import Path
from typing import Any
from dataclasses import dataclass
from enum import Enum


class ToolType(str, Enum):
    BASH = "bash"
    READ = "read"
    WRITE = "write"
    GLOB = "glob"
    GREP = "grep"


@dataclass
class ToolResult:
    """工具执行结果"""
    success: bool
    output: str
    error: Optional[str] = None
    tool_name: str = ""
    duration_ms: float = 0


# Claude API 工具定义
TOOL_DEFINITIONS = [
    {
        "name": "bash",
        "description": "Execute a bash command. Use for running scripts, git commands, file operations, etc.",
        "input_schema": {
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
        }
    },
    {
        "name": "read",
        "description": "Read the contents of a file. Use to view file contents before making changes.",
        "input_schema": {
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
        }
    },
    {
        "name": "write",
        "description": "Write content to a file. Creates the file if it doesn't exist.",
        "input_schema": {
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
        }
    },
    {
        "name": "glob",
        "description": "Find files matching a glob pattern.",
        "input_schema": {
            "type": "object",
            "properties": {
                "pattern": {
                    "type": "string",
                    "description": "Glob pattern to match (e.g., '**/*.py')"
                },
                "path": {
                    "type": "string",
                    "description": "Base path to search in (optional, defaults to current directory)"
                }
            },
            "required": ["pattern"]
        }
    },
    {
        "name": "grep",
        "description": "Search for text patterns in files.",
        "input_schema": {
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
        }
    }
]


class ToolExecutor:
    """工具执行器"""

    def __init__(self, working_dir: str = None, allowed_tools: list[str] = None):
        self.working_dir = working_dir or os.getcwd()
        self.allowed_tools = allowed_tools  # None 表示允许所有工具

    def is_tool_allowed(self, tool_name: str) -> bool:
        """检查工具是否被允许"""
        if self.allowed_tools is None:
            return True
        return tool_name.lower() in [t.lower() for t in self.allowed_tools]

    def execute(self, tool_name: str, tool_input: dict[str, Any]) -> ToolResult:
        """执行工具调用"""
        import time
        start_time = time.time()

        if not self.is_tool_allowed(tool_name):
            return ToolResult(
                success=False,
                output="",
                error=f"Tool '{tool_name}' is not allowed for this skill",
                tool_name=tool_name
            )

        try:
            if tool_name == "bash":
                result = self._execute_bash(tool_input)
            elif tool_name == "read":
                result = self._execute_read(tool_input)
            elif tool_name == "write":
                result = self._execute_write(tool_input)
            elif tool_name == "glob":
                result = self._execute_glob(tool_input)
            elif tool_name == "grep":
                result = self._execute_grep(tool_input)
            else:
                result = ToolResult(
                    success=False,
                    output="",
                    error=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            result = ToolResult(
                success=False,
                output="",
                error=str(e)
            )

        result.tool_name = tool_name
        result.duration_ms = (time.time() - start_time) * 1000
        return result

    def _execute_bash(self, params: dict) -> ToolResult:
        """执行 Bash 命令"""
        command = params.get("command", "")
        working_dir = params.get("working_dir", self.working_dir)

        if not command:
            return ToolResult(success=False, output="", error="No command provided")

        # 安全检查：禁止危险命令
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
                timeout=30  # 30 秒超时
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
        """读取文件内容"""
        file_path = params.get("file_path", "")
        start_line = params.get("start_line")
        end_line = params.get("end_line")

        if not file_path:
            return ToolResult(success=False, output="", error="No file path provided")

        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.working_dir, file_path)

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # 处理行号范围
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

        # 处理相对路径
        if not os.path.isabs(file_path):
            file_path = os.path.join(self.working_dir, file_path)

        try:
            # 确保目录存在
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
        """查找匹配的文件"""
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
        """搜索文本模式"""
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
            # 限制输出行数
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


def get_tool_definitions(allowed_tools: list[str] = None) -> list[dict]:
    """获取工具定义列表（用于 Claude API）"""
    if allowed_tools is None:
        return TOOL_DEFINITIONS

    allowed_lower = [t.lower() for t in allowed_tools]
    return [t for t in TOOL_DEFINITIONS if t["name"].lower() in allowed_lower]


# 补充 Optional 导入
from typing import Optional
