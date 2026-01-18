"""
统一 Skills 执行引擎

整合 LLM Provider、Tool Router、Governance、Capture 等模块
提供完整的 Skills 执行能力
"""

import os
import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Generator
from pathlib import Path

from .providers import get_provider, BaseLLMProvider, Message, ToolDefinition, ToolCall
from .tool_router import get_tool_router as get_router, ToolRouter, ToolResult, ToolAccessLevel as AccessLevel
from .governance.metrics import get_metrics_collector, MetricsCollector, MetricScope
from .governance.audit import get_audit_logger, AuditLogger
from .governance.safety import get_safety_guard, SafetyGuard, SecurityContext
from .governance.alerts import get_alert_manager, AlertManager
from .capture.repository import get_repository, KnowledgeRepository, SkillEntry
from .capture.vector_store import get_vector_store, SkillVectorStore


@dataclass
class SkillExecutionContext:
    """Skill 执行上下文"""
    execution_id: str
    skill_id: str
    skill_name: str

    # 用户信息
    user_id: Optional[str] = None
    session_id: Optional[str] = None

    # 输入参数
    parameters: Dict[str, Any] = field(default_factory=dict)

    # 安全上下文
    access_levels: List[AccessLevel] = field(default_factory=lambda: [AccessLevel.READ])
    requires_approval: bool = False

    # 执行配置
    max_turns: int = 20
    timeout_ms: int = 300000

    # 状态
    started_at: datetime = field(default_factory=datetime.utcnow)
    current_turn: int = 0

    # 消息历史
    messages: List[Message] = field(default_factory=list)

    # 工具调用记录
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)

    def to_security_context(self) -> SecurityContext:
        """转换为安全上下文"""
        return SecurityContext(
            user_id=self.user_id or "anonymous",
            session_id=self.session_id or self.execution_id,
            skill_id=self.skill_id,
            access_levels=self.access_levels,
        )


@dataclass
class SkillExecutionResult:
    """Skill 执行结果"""
    execution_id: str
    skill_id: str
    success: bool

    # 结果
    result: Optional[str] = None
    error: Optional[str] = None

    # 统计
    turns: int = 0
    tool_calls_count: int = 0
    duration_ms: float = 0

    # 详情
    messages: List[Dict[str, Any]] = field(default_factory=list)
    tool_results: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "execution_id": self.execution_id,
            "skill_id": self.skill_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "turns": self.turns,
            "tool_calls_count": self.tool_calls_count,
            "duration_ms": self.duration_ms,
        }


class UnifiedSkillsEngine:
    """
    统一 Skills 执行引擎

    功能：
    - 多 LLM Provider 支持
    - 工具路由和权限控制
    - 执行监控和审计
    - 知识库 RAG 增强
    - 安全隔离
    """

    def __init__(
        self,
        provider_name: str = None,
        model: str = None,
        skills_dir: str = None,
    ):
        # LLM Provider
        self._provider_name = provider_name or os.environ.get("LLM_PROVIDER", "claude")
        self._model = model
        self._provider: Optional[BaseLLMProvider] = None

        # 组件
        self._tool_router: Optional[ToolRouter] = None
        self._metrics: Optional[MetricsCollector] = None
        self._audit: Optional[AuditLogger] = None
        self._safety: Optional[SafetyGuard] = None
        self._alerts: Optional[AlertManager] = None
        self._repository: Optional[KnowledgeRepository] = None
        self._vector_store: Optional[SkillVectorStore] = None

        # Skills 目录
        self._skills_dir = Path(skills_dir) if skills_dir else Path(".claude/skills")

        # 活跃执行
        self._active_executions: Dict[str, SkillExecutionContext] = {}

    def _init_components(self):
        """延迟初始化组件"""
        if self._provider is None:
            self._provider = get_provider(self._provider_name, model=self._model)
        if self._tool_router is None:
            self._tool_router = get_router()
        if self._metrics is None:
            self._metrics = get_metrics_collector()
        if self._audit is None:
            self._audit = get_audit_logger()
        if self._safety is None:
            self._safety = get_safety_guard()
        if self._alerts is None:
            self._alerts = get_alert_manager()
        if self._repository is None:
            self._repository = get_repository(str(self._skills_dir))
        if self._vector_store is None:
            self._vector_store = get_vector_store()

    # ==================== Skill 管理 ====================

    def load_skill(self, skill_id: str) -> Optional[SkillEntry]:
        """加载 Skill"""
        self._init_components()
        return self._repository.get_skill(skill_id)

    def list_skills(
        self,
        category: str = None,
        tags: List[str] = None
    ) -> List[SkillEntry]:
        """列出 Skills"""
        self._init_components()
        return self._repository.list_skills(category=category, tags=tags)

    def search_skills(
        self,
        query: str,
        top_k: int = 5,
        use_vector: bool = True
    ) -> List[SkillEntry]:
        """搜索 Skills（支持语义搜索）"""
        self._init_components()

        if use_vector and self._vector_store.count() > 0:
            # 使用向量搜索
            matches = self._vector_store.search_skills(query, top_k=top_k)
            return [
                self._repository.get_skill(m.metadata.get("skill_id"))
                for m in matches
                if m.metadata.get("skill_id")
            ]
        else:
            # 使用文本搜索
            results = self._repository.search(query, limit=top_k)
            return [r.entry for r in results]

    def index_skill(self, skill: SkillEntry):
        """索引 Skill 到向量库"""
        self._init_components()
        self._vector_store.add_skill(
            skill_id=skill.skill_id,
            name=skill.name,
            description=skill.description,
            content=skill.content or "",
            category=skill.category,
            tags=skill.tags,
        )

    # ==================== Skill 执行 ====================

    def execute(
        self,
        skill_id: str,
        parameters: Dict[str, Any] = None,
        user_id: str = None,
        session_id: str = None,
        access_levels: List[AccessLevel] = None,
        stream: bool = False,
    ) -> SkillExecutionResult:
        """
        执行 Skill

        Args:
            skill_id: Skill ID
            parameters: 输入参数
            user_id: 用户 ID
            session_id: 会话 ID
            access_levels: 访问级别
            stream: 是否流式输出

        Returns:
            执行结果
        """
        self._init_components()

        # 加载 Skill
        skill = self.load_skill(skill_id)
        if not skill:
            return SkillExecutionResult(
                execution_id=str(uuid.uuid4())[:12],
                skill_id=skill_id,
                success=False,
                error=f"Skill '{skill_id}' not found",
            )

        # 创建执行上下文
        context = SkillExecutionContext(
            execution_id=str(uuid.uuid4())[:12],
            skill_id=skill_id,
            skill_name=skill.name,
            user_id=user_id,
            session_id=session_id,
            parameters=parameters or {},
            access_levels=access_levels or [AccessLevel.READ],
        )

        self._active_executions[context.execution_id] = context

        # 审计日志
        self._audit.log_execution_start(
            execution_id=context.execution_id,
            skill_id=skill_id,
            user_id=user_id,
            parameters=parameters,
        )

        try:
            # 执行
            if stream:
                result = self._execute_stream(context, skill)
            else:
                result = self._execute_sync(context, skill)

            # 更新统计
            self._metrics.record(
                execution_id=context.execution_id,
                scope=MetricScope.SKILL,
                target_id=skill_id,
                success=result.success,
                duration_ms=result.duration_ms,
                metadata={
                    "turns": result.turns,
                    "tool_calls": result.tool_calls_count,
                },
            )

            # 更新知识库统计
            self._repository.update_stats(
                skill_id=skill_id,
                success=result.success,
                duration_ms=result.duration_ms,
            )

            # 检查告警
            self._alerts.check_and_trigger()

            # 审计日志
            self._audit.log_execution_end(
                execution_id=context.execution_id,
                success=result.success,
                result=result.result,
                error=result.error,
            )

            return result

        except Exception as e:
            error_msg = str(e)

            # 记录失败
            self._metrics.record(
                execution_id=context.execution_id,
                scope=MetricScope.SKILL,
                target_id=skill_id,
                success=False,
                duration_ms=(datetime.utcnow() - context.started_at).total_seconds() * 1000,
                error=error_msg,
            )

            self._audit.log_execution_end(
                execution_id=context.execution_id,
                success=False,
                error=error_msg,
            )

            return SkillExecutionResult(
                execution_id=context.execution_id,
                skill_id=skill_id,
                success=False,
                error=error_msg,
                duration_ms=(datetime.utcnow() - context.started_at).total_seconds() * 1000,
            )

        finally:
            del self._active_executions[context.execution_id]

    def _execute_sync(
        self,
        context: SkillExecutionContext,
        skill: SkillEntry
    ) -> SkillExecutionResult:
        """同步执行"""
        # 构建系统消息
        system_message = self._build_system_message(skill, context.parameters)

        # 初始化消息
        context.messages = [
            Message(role="user", content=system_message)
        ]

        # 获取可用工具
        tools = self._get_available_tools(skill, context)

        # 执行循环
        while context.current_turn < context.max_turns:
            context.current_turn += 1

            # 调用 LLM
            response = self._provider.chat(
                messages=context.messages,
                tools=tools if tools else None,
            )

            # 添加助手消息
            context.messages.append(Message(
                role="assistant",
                content=response.content,
            ))

            # 检查是否有工具调用
            if not response.tool_calls:
                # 没有工具调用，执行完成
                break

            # 处理工具调用
            for tool_call in response.tool_calls:
                tool_result = self._execute_tool(context, tool_call)

                # 添加工具结果消息
                context.messages.append(Message(
                    role="user",
                    content=f"Tool result for {tool_call.name}:\n{tool_result.output}",
                ))

                context.tool_calls.append({
                    "tool": tool_call.name,
                    "arguments": tool_call.arguments,
                    "result": tool_result.to_dict(),
                })

        # 构建结果
        duration_ms = (datetime.utcnow() - context.started_at).total_seconds() * 1000

        # 获取最终结果
        final_content = ""
        for msg in reversed(context.messages):
            if msg.role == "assistant" and msg.content:
                final_content = msg.content
                break

        return SkillExecutionResult(
            execution_id=context.execution_id,
            skill_id=context.skill_id,
            success=True,
            result=final_content,
            turns=context.current_turn,
            tool_calls_count=len(context.tool_calls),
            duration_ms=duration_ms,
            messages=[{"role": m.role, "content": m.content} for m in context.messages],
            tool_results=context.tool_calls,
        )

    def _execute_stream(
        self,
        context: SkillExecutionContext,
        skill: SkillEntry
    ) -> SkillExecutionResult:
        """流式执行（简化版，返回最终结果）"""
        # 目前简化为同步执行
        return self._execute_sync(context, skill)

    def _build_system_message(
        self,
        skill: SkillEntry,
        parameters: Dict[str, Any]
    ) -> str:
        """构建系统消息"""
        # 加载 Skill 内容
        content = skill.content or ""

        # 替换参数
        for key, value in parameters.items():
            content = content.replace(f"${{{key}}}", str(value))

        return f"""You are executing a skill. Follow the instructions below carefully.

## Skill: {skill.name}

{content}

## Parameters
{self._format_parameters(parameters)}

Please execute the skill step by step and report the results.
"""

    def _format_parameters(self, parameters: Dict[str, Any]) -> str:
        """格式化参数"""
        if not parameters:
            return "No parameters provided."

        lines = []
        for key, value in parameters.items():
            lines.append(f"- {key}: {value}")
        return "\n".join(lines)

    def _get_available_tools(
        self,
        skill: SkillEntry,
        context: SkillExecutionContext
    ) -> List[ToolDefinition]:
        """获取可用工具"""
        # 从 Skill 元数据获取允许的工具
        allowed_tools = []

        # 解析 SKILL.md 中的 allowed-tools
        if skill.content:
            import re
            match = re.search(r"allowed-tools:\s*\n((?:\s+-\s+\S+\n)+)", skill.content)
            if match:
                tools_text = match.group(1)
                for line in tools_text.strip().split("\n"):
                    tool = line.strip().lstrip("- ").strip()
                    if tool:
                        allowed_tools.append(tool)

        if not allowed_tools:
            # 默认工具
            allowed_tools = ["Read", "Glob", "Grep"]

        return self._tool_router.get_tool_definitions(
            allowed_tools=allowed_tools,
            access_levels=context.access_levels,
        )

    def _execute_tool(
        self,
        context: SkillExecutionContext,
        tool_call: ToolCall
    ) -> ToolResult:
        """执行工具调用"""
        # 安全检查
        security_context = context.to_security_context()
        check_result = self._safety.check_permission(
            context=security_context,
            tool_name=tool_call.name,
            params=tool_call.arguments,
        )

        if not check_result.allowed:
            self._audit.log_tool_call(
                execution_id=context.execution_id,
                tool_name=tool_call.name,
                arguments=tool_call.arguments,
                success=False,
                error=check_result.reason,
            )

            return ToolResult(
                tool_name=tool_call.name,
                success=False,
                output="",
                error=f"Permission denied: {check_result.reason}",
            )

        # 执行工具
        result = self._tool_router.execute(tool_call)

        # 审计日志
        self._audit.log_tool_call(
            execution_id=context.execution_id,
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            success=result.success,
            result=result.output[:500] if result.output else None,
            error=result.error,
        )

        return result

    # ==================== 监控和统计 ====================

    def get_metrics(self) -> Dict[str, Any]:
        """获取监控指标"""
        self._init_components()
        dashboard = self._metrics.get_dashboard()
        return {
            "global_success_rate": dashboard.global_success_rate,
            "total_executions": dashboard.total_executions,
            "skills": dashboard.skills,
            "active_alerts": len(self._alerts.get_active_alerts()),
        }

    def get_skill_stats(self, skill_id: str) -> Dict[str, Any]:
        """获取 Skill 统计"""
        self._init_components()

        skill = self._repository.get_skill(skill_id)
        if not skill:
            return {}

        success_rate = self._metrics.get_success_rate(
            scope=MetricScope.SKILL,
            target_id=skill_id,
        )

        return {
            "skill_id": skill_id,
            "name": skill.name,
            "execution_count": skill.execution_count,
            "success_rate": success_rate,
            "avg_duration_ms": skill.avg_duration_ms,
        }

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """获取活跃告警"""
        self._init_components()
        alerts = self._alerts.get_active_alerts()
        return [a.to_dict() for a in alerts]

    # ==================== 配置 ====================

    def set_provider(self, provider_name: str, model: str = None):
        """切换 LLM Provider"""
        self._provider_name = provider_name
        self._model = model
        self._provider = None  # 重置，下次使用时重新创建

    def get_provider_info(self) -> Dict[str, Any]:
        """获取当前 Provider 信息"""
        self._init_components()
        return {
            "provider": self._provider_name,
            "model": self._provider.model if self._provider else None,
        }


# 全局引擎实例
_engine: Optional[UnifiedSkillsEngine] = None


def get_skills_engine(
    provider_name: str = None,
    model: str = None,
) -> UnifiedSkillsEngine:
    """获取 Skills 引擎实例"""
    global _engine
    if _engine is None:
        _engine = UnifiedSkillsEngine(
            provider_name=provider_name,
            model=model,
        )
    return _engine
