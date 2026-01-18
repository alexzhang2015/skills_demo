"""
安全隔离系统

实现读写分离、权限控制、危险操作拦截
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Set, Any
from enum import Enum
import re


class OperationType(str, Enum):
    """操作类型（读写分离）"""
    READ = "read"           # 只读操作
    WRITE = "write"         # 写操作
    EXECUTE = "execute"     # 执行操作
    ADMIN = "admin"         # 管理操作
    DANGEROUS = "dangerous" # 危险操作


class PermissionLevel(str, Enum):
    """权限级别"""
    NONE = "none"           # 无权限
    READ_ONLY = "read_only" # 只读
    READ_WRITE = "read_write" # 读写
    EXECUTE = "execute"     # 可执行
    ADMIN = "admin"         # 管理员


@dataclass
class SecurityContext:
    """安全上下文"""
    user_id: Optional[str] = None
    user_role: str = "user"
    permission_level: PermissionLevel = PermissionLevel.READ_ONLY
    allowed_operations: Set[OperationType] = field(default_factory=set)
    denied_tools: Set[str] = field(default_factory=set)
    session_id: Optional[str] = None


@dataclass
class SecurityCheckResult:
    """安全检查结果"""
    allowed: bool
    reason: Optional[str] = None
    requires_confirmation: bool = False
    confirmation_message: Optional[str] = None
    warnings: List[str] = field(default_factory=list)


class SafetyGuard:
    """
    安全守卫

    功能：
    - 操作类型分类（读写分离）
    - 权限检查
    - 危险操作拦截
    - 敏感数据保护
    """

    # 操作类型关键词
    READ_KEYWORDS = {
        "get", "list", "query", "fetch", "search", "find", "check",
        "read", "view", "show", "describe", "analyze", "report"
    }

    WRITE_KEYWORDS = {
        "create", "update", "delete", "set", "add", "remove", "modify",
        "write", "save", "insert", "change", "edit", "patch", "put"
    }

    EXECUTE_KEYWORDS = {
        "execute", "run", "trigger", "start", "stop", "restart",
        "sync", "send", "publish", "deploy", "launch", "process"
    }

    DANGEROUS_KEYWORDS = {
        "drop", "truncate", "destroy", "purge", "reset", "force",
        "wipe", "clear_all", "delete_all", "rm -rf"
    }

    # 危险命令模式
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",           # 删除根目录
        r"dd\s+if=",                # 磁盘写入
        r"mkfs",                    # 格式化
        r":\(\)\{:\|:&\};:",       # Fork 炸弹
        r">\s*/dev/sd",             # 覆盖设备
        r"chmod\s+-R\s+777",        # 危险权限
        r"DROP\s+DATABASE",         # 删库
        r"TRUNCATE\s+TABLE",        # 清表
        r"DELETE\s+FROM\s+\w+\s*;$", # 无条件删除
    ]

    # 敏感数据模式
    SENSITIVE_PATTERNS = [
        r"password[s]?\s*[=:]",
        r"api[_-]?key\s*[=:]",
        r"secret[_-]?key\s*[=:]",
        r"access[_-]?token\s*[=:]",
        r"private[_-]?key",
        r"BEGIN\s+(?:RSA\s+)?PRIVATE\s+KEY",
    ]

    def __init__(self):
        self._dangerous_patterns = [re.compile(p, re.IGNORECASE) for p in self.DANGEROUS_PATTERNS]
        self._sensitive_patterns = [re.compile(p, re.IGNORECASE) for p in self.SENSITIVE_PATTERNS]

    def classify_operation(self, tool_name: str, params: Dict[str, Any] = None) -> OperationType:
        """
        分类操作类型

        Args:
            tool_name: 工具名称
            params: 工具参数

        Returns:
            操作类型
        """
        name_lower = tool_name.lower()

        # 检查危险关键词
        if any(kw in name_lower for kw in self.DANGEROUS_KEYWORDS):
            return OperationType.DANGEROUS

        # 检查参数中的危险模式
        if params:
            params_str = str(params)
            for pattern in self._dangerous_patterns:
                if pattern.search(params_str):
                    return OperationType.DANGEROUS

        # 检查执行关键词
        if any(kw in name_lower for kw in self.EXECUTE_KEYWORDS):
            return OperationType.EXECUTE

        # 检查写关键词
        if any(kw in name_lower for kw in self.WRITE_KEYWORDS):
            return OperationType.WRITE

        # 检查读关键词
        if any(kw in name_lower for kw in self.READ_KEYWORDS):
            return OperationType.READ

        # 默认为执行操作（保守）
        return OperationType.EXECUTE

    def check_permission(
        self,
        context: SecurityContext,
        tool_name: str,
        params: Dict[str, Any] = None
    ) -> SecurityCheckResult:
        """
        检查操作权限

        Args:
            context: 安全上下文
            tool_name: 工具名称
            params: 工具参数

        Returns:
            检查结果
        """
        warnings = []

        # 检查工具是否被禁止
        if tool_name in context.denied_tools:
            return SecurityCheckResult(
                allowed=False,
                reason=f"工具 '{tool_name}' 被禁止使用"
            )

        # 分类操作
        op_type = self.classify_operation(tool_name, params)

        # 危险操作需要特殊处理
        if op_type == OperationType.DANGEROUS:
            return SecurityCheckResult(
                allowed=False,
                reason=f"检测到危险操作: {tool_name}",
                requires_confirmation=True,
                confirmation_message="此操作可能导致数据丢失或系统损坏，需要管理员确认"
            )

        # 检查操作是否被允许
        if context.allowed_operations and op_type not in context.allowed_operations:
            return SecurityCheckResult(
                allowed=False,
                reason=f"操作类型 '{op_type.value}' 未被授权"
            )

        # 检查权限级别
        if not self._check_permission_level(context.permission_level, op_type):
            return SecurityCheckResult(
                allowed=False,
                reason=f"权限级别 '{context.permission_level.value}' 不足以执行 '{op_type.value}' 操作"
            )

        # 检查敏感数据
        if params:
            sensitive_found = self._check_sensitive_data(str(params))
            if sensitive_found:
                warnings.append(f"检测到敏感数据模式: {sensitive_found}")

        # 写操作和执行操作需要确认
        requires_confirmation = op_type in (OperationType.WRITE, OperationType.EXECUTE)

        return SecurityCheckResult(
            allowed=True,
            requires_confirmation=requires_confirmation,
            confirmation_message=f"确认执行 {op_type.value} 操作: {tool_name}?" if requires_confirmation else None,
            warnings=warnings
        )

    def _check_permission_level(
        self,
        level: PermissionLevel,
        op_type: OperationType
    ) -> bool:
        """检查权限级别是否足够"""
        permission_map = {
            PermissionLevel.NONE: set(),
            PermissionLevel.READ_ONLY: {OperationType.READ},
            PermissionLevel.READ_WRITE: {OperationType.READ, OperationType.WRITE},
            PermissionLevel.EXECUTE: {OperationType.READ, OperationType.WRITE, OperationType.EXECUTE},
            PermissionLevel.ADMIN: {OperationType.READ, OperationType.WRITE, OperationType.EXECUTE, OperationType.ADMIN},
        }

        allowed_ops = permission_map.get(level, set())
        return op_type in allowed_ops

    def _check_sensitive_data(self, content: str) -> Optional[str]:
        """检查是否包含敏感数据"""
        for pattern in self._sensitive_patterns:
            match = pattern.search(content)
            if match:
                return match.group(0)
        return None

    def sanitize_output(self, output: str) -> str:
        """
        清理输出中的敏感数据

        Args:
            output: 原始输出

        Returns:
            清理后的输出
        """
        sanitized = output

        for pattern in self._sensitive_patterns:
            # 替换敏感数据为占位符
            sanitized = pattern.sub("[REDACTED]", sanitized)

        return sanitized

    def validate_bash_command(self, command: str) -> SecurityCheckResult:
        """
        验证 Bash 命令安全性

        Args:
            command: Bash 命令

        Returns:
            检查结果
        """
        warnings = []

        # 检查危险模式
        for pattern in self._dangerous_patterns:
            if pattern.search(command):
                return SecurityCheckResult(
                    allowed=False,
                    reason=f"检测到危险命令模式",
                    requires_confirmation=True,
                    confirmation_message=f"命令 '{command[:50]}...' 可能导致系统损坏"
                )

        # 检查管道和重定向
        if "|" in command:
            warnings.append("命令包含管道操作")
        if ">" in command or ">>" in command:
            warnings.append("命令包含重定向操作")

        # 检查 sudo
        if command.strip().startswith("sudo"):
            return SecurityCheckResult(
                allowed=False,
                reason="不允许使用 sudo 命令",
                requires_confirmation=True
            )

        # 检查网络操作
        network_cmds = ["curl", "wget", "nc", "netcat", "ssh", "scp"]
        if any(cmd in command for cmd in network_cmds):
            warnings.append("命令包含网络操作")

        return SecurityCheckResult(
            allowed=True,
            requires_confirmation=len(warnings) > 0,
            warnings=warnings
        )

    def create_readonly_context(self, user_id: str = None) -> SecurityContext:
        """创建只读安全上下文"""
        return SecurityContext(
            user_id=user_id,
            user_role="readonly",
            permission_level=PermissionLevel.READ_ONLY,
            allowed_operations={OperationType.READ}
        )

    def create_standard_context(self, user_id: str = None) -> SecurityContext:
        """创建标准安全上下文"""
        return SecurityContext(
            user_id=user_id,
            user_role="user",
            permission_level=PermissionLevel.EXECUTE,
            allowed_operations={OperationType.READ, OperationType.WRITE, OperationType.EXECUTE}
        )

    def create_admin_context(self, user_id: str = None) -> SecurityContext:
        """创建管理员安全上下文"""
        return SecurityContext(
            user_id=user_id,
            user_role="admin",
            permission_level=PermissionLevel.ADMIN,
            allowed_operations={OperationType.READ, OperationType.WRITE, OperationType.EXECUTE, OperationType.ADMIN}
        )


# 全局安全守卫
_guard: Optional[SafetyGuard] = None


def get_safety_guard() -> SafetyGuard:
    """获取安全守卫实例"""
    global _guard
    if _guard is None:
        _guard = SafetyGuard()
    return _guard
