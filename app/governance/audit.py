"""
审计日志系统

记录所有重要操作，支持审计追溯
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
import threading
import json


class AuditEventType(str, Enum):
    """审计事件类型"""
    # 执行相关
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    EXECUTION_ERROR = "execution_error"

    # 工具调用
    TOOL_CALL = "tool_call"
    TOOL_RESULT = "tool_result"
    TOOL_ERROR = "tool_error"

    # 审批相关
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    APPROVAL_DENIED = "approval_denied"

    # Skill 相关
    SKILL_CREATED = "skill_created"
    SKILL_UPDATED = "skill_updated"
    SKILL_DELETED = "skill_deleted"
    SKILL_EXECUTED = "skill_executed"

    # 录制相关
    RECORDING_START = "recording_start"
    RECORDING_END = "recording_end"
    RECORDING_ACTION = "recording_action"

    # 系统相关
    SYSTEM_ERROR = "system_error"
    CONFIG_CHANGED = "config_changed"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"


class AuditEventCategory(str, Enum):
    """审计事件分类"""
    EXECUTION = "execution"
    TOOL = "tool"
    APPROVAL = "approval"
    SKILL = "skill"
    RECORDING = "recording"
    SYSTEM = "system"
    USER = "user"


@dataclass
class AuditEvent:
    """审计事件"""
    event_id: str
    event_type: AuditEventType
    event_category: AuditEventCategory

    action: str  # 操作描述
    target: Optional[str] = None  # 操作目标

    # 关联 ID
    session_id: Optional[str] = None
    execution_id: Optional[str] = None
    trace_id: Optional[str] = None

    # 结果
    status: str = "success"  # success, failure, pending
    error_message: Optional[str] = None

    # 详情
    details: Dict[str, Any] = field(default_factory=dict)

    # 用户信息
    user_id: Optional[str] = None
    user_name: Optional[str] = None
    user_role: Optional[str] = None

    # 来源信息
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    source: str = "system"  # api, web, cli, system

    # 时间戳
    timestamp: datetime = field(default_factory=datetime.utcnow)

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "event_category": self.event_category.value,
            "action": self.action,
            "target": self.target,
            "session_id": self.session_id,
            "execution_id": self.execution_id,
            "trace_id": self.trace_id,
            "status": self.status,
            "error_message": self.error_message,
            "details": self.details,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "user_role": self.user_role,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "source": self.source,
            "timestamp": self.timestamp.isoformat(),
        }


class AuditLogger:
    """
    审计日志记录器

    功能：
    - 记录所有重要操作
    - 支持多种存储后端（内存、数据库、文件）
    - 提供查询和导出能力
    """

    # 事件类型到分类的映射
    EVENT_CATEGORY_MAP = {
        AuditEventType.EXECUTION_START: AuditEventCategory.EXECUTION,
        AuditEventType.EXECUTION_END: AuditEventCategory.EXECUTION,
        AuditEventType.EXECUTION_ERROR: AuditEventCategory.EXECUTION,
        AuditEventType.TOOL_CALL: AuditEventCategory.TOOL,
        AuditEventType.TOOL_RESULT: AuditEventCategory.TOOL,
        AuditEventType.TOOL_ERROR: AuditEventCategory.TOOL,
        AuditEventType.APPROVAL_REQUESTED: AuditEventCategory.APPROVAL,
        AuditEventType.APPROVAL_GRANTED: AuditEventCategory.APPROVAL,
        AuditEventType.APPROVAL_DENIED: AuditEventCategory.APPROVAL,
        AuditEventType.SKILL_CREATED: AuditEventCategory.SKILL,
        AuditEventType.SKILL_UPDATED: AuditEventCategory.SKILL,
        AuditEventType.SKILL_DELETED: AuditEventCategory.SKILL,
        AuditEventType.SKILL_EXECUTED: AuditEventCategory.SKILL,
        AuditEventType.RECORDING_START: AuditEventCategory.RECORDING,
        AuditEventType.RECORDING_END: AuditEventCategory.RECORDING,
        AuditEventType.RECORDING_ACTION: AuditEventCategory.RECORDING,
        AuditEventType.SYSTEM_ERROR: AuditEventCategory.SYSTEM,
        AuditEventType.CONFIG_CHANGED: AuditEventCategory.SYSTEM,
        AuditEventType.USER_LOGIN: AuditEventCategory.USER,
        AuditEventType.USER_LOGOUT: AuditEventCategory.USER,
    }

    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()

        # 事件处理器（用于扩展）
        self._handlers: List[callable] = []

    def log(
        self,
        event_type: AuditEventType,
        action: str,
        target: str = None,
        session_id: str = None,
        execution_id: str = None,
        trace_id: str = None,
        status: str = "success",
        error_message: str = None,
        details: Dict[str, Any] = None,
        user_id: str = None,
        user_name: str = None,
        **kwargs
    ) -> AuditEvent:
        """记录审计事件"""
        event = AuditEvent(
            event_id=str(uuid.uuid4())[:16],
            event_type=event_type,
            event_category=self.EVENT_CATEGORY_MAP.get(event_type, AuditEventCategory.SYSTEM),
            action=action,
            target=target,
            session_id=session_id,
            execution_id=execution_id,
            trace_id=trace_id,
            status=status,
            error_message=error_message,
            details=details or {},
            user_id=user_id,
            user_name=user_name,
            **kwargs
        )

        with self._lock:
            self._events.append(event)
            # 保持事件数量在限制内
            if len(self._events) > self.max_events:
                self._events = self._events[-self.max_events:]

        # 调用处理器
        for handler in self._handlers:
            try:
                handler(event)
            except Exception:
                pass  # 处理器错误不影响主流程

        return event

    def log_execution_start(
        self,
        execution_id: str,
        target_type: str,
        target_id: str,
        input_params: Any = None,
        **kwargs
    ) -> AuditEvent:
        """记录执行开始"""
        return self.log(
            event_type=AuditEventType.EXECUTION_START,
            action=f"开始执行 {target_type}: {target_id}",
            target=target_id,
            execution_id=execution_id,
            details={"target_type": target_type, "input_params": input_params},
            **kwargs
        )

    def log_execution_end(
        self,
        execution_id: str,
        target_type: str,
        target_id: str,
        success: bool,
        duration_ms: float,
        output: Any = None,
        error: str = None,
        **kwargs
    ) -> AuditEvent:
        """记录执行结束"""
        return self.log(
            event_type=AuditEventType.EXECUTION_END if success else AuditEventType.EXECUTION_ERROR,
            action=f"{'完成' if success else '失败'} {target_type}: {target_id}",
            target=target_id,
            execution_id=execution_id,
            status="success" if success else "failure",
            error_message=error,
            details={
                "target_type": target_type,
                "duration_ms": duration_ms,
                "output": output,
            },
            **kwargs
        )

    def log_tool_call(
        self,
        tool_name: str,
        params: Dict[str, Any],
        execution_id: str = None,
        **kwargs
    ) -> AuditEvent:
        """记录工具调用"""
        return self.log(
            event_type=AuditEventType.TOOL_CALL,
            action=f"调用工具: {tool_name}",
            target=tool_name,
            execution_id=execution_id,
            details={"params": params},
            **kwargs
        )

    def log_approval(
        self,
        approval_type: str,
        target: str,
        approved: bool,
        approver: str,
        reason: str = None,
        **kwargs
    ) -> AuditEvent:
        """记录审批操作"""
        event_type = AuditEventType.APPROVAL_GRANTED if approved else AuditEventType.APPROVAL_DENIED
        return self.log(
            event_type=event_type,
            action=f"{'批准' if approved else '拒绝'} {approval_type}: {target}",
            target=target,
            status="success" if approved else "rejected",
            details={
                "approval_type": approval_type,
                "approver": approver,
                "reason": reason,
            },
            user_name=approver,
            **kwargs
        )

    def get_events(
        self,
        event_type: AuditEventType = None,
        event_category: AuditEventCategory = None,
        session_id: str = None,
        execution_id: str = None,
        user_id: str = None,
        limit: int = 100
    ) -> List[AuditEvent]:
        """获取审计事件"""
        with self._lock:
            events = list(self._events)

        if event_type:
            events = [e for e in events if e.event_type == event_type]
        if event_category:
            events = [e for e in events if e.event_category == event_category]
        if session_id:
            events = [e for e in events if e.session_id == session_id]
        if execution_id:
            events = [e for e in events if e.execution_id == execution_id]
        if user_id:
            events = [e for e in events if e.user_id == user_id]

        # 按时间倒序
        events.sort(key=lambda e: e.timestamp, reverse=True)

        return events[:limit]

    def get_audit_trail(self, session_id: str) -> List[AuditEvent]:
        """获取会话的完整审计轨迹"""
        return self.get_events(session_id=session_id, limit=1000)

    def add_handler(self, handler: callable):
        """添加事件处理器"""
        self._handlers.append(handler)

    def export_to_db(self, session, events: List[AuditEvent] = None):
        """导出到数据库"""
        from ..storage.repository import AuditRepository

        repo = AuditRepository(session)
        events = events or self._events

        for event in events:
            repo.log(
                event_type=event.event_type.value,
                action=event.action,
                session_id=event.session_id,
                execution_id=event.execution_id,
                user_id=event.user_id,
                target=event.target,
                details=event.details,
                status=event.status,
                error_message=event.error_message,
                trace_id=event.trace_id,
                event_category=event.event_category.value,
                user_name=event.user_name,
                user_role=event.user_role,
                ip_address=event.ip_address,
                source=event.source,
            )

    def export_to_file(self, filepath: str):
        """导出到文件"""
        with self._lock:
            events = [e.to_dict() for e in self._events]

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(events, f, ensure_ascii=False, indent=2)


# 全局审计日志器
_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """获取审计日志器实例"""
    global _logger
    if _logger is None:
        _logger = AuditLogger()
    return _logger
