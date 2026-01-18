"""
数据仓库（Repository）

提供数据访问的高级接口
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import uuid

from sqlalchemy import func, and_, or_, desc
from sqlalchemy.orm import Session

from .models import (
    ExecutionRecord,
    SessionRecord,
    AuditLog,
    MetricSnapshot,
    SkillRecord,
    RecordingSession,
)
from .database import session_scope


class BaseRepository:
    """Repository 基类"""

    def __init__(self, session: Optional[Session] = None):
        self._session = session

    @property
    def session(self) -> Session:
        if self._session is None:
            raise RuntimeError("Session not provided. Use with session_scope() or pass session to constructor.")
        return self._session


class ExecutionRepository(BaseRepository):
    """执行记录仓库"""

    def create(
        self,
        execution_type: str,
        target_id: str,
        target_name: str = None,
        session_id: str = None,
        input_params: dict = None,
        **kwargs
    ) -> ExecutionRecord:
        """创建执行记录"""
        record = ExecutionRecord(
            execution_id=str(uuid.uuid4())[:8],
            execution_type=execution_type,
            target_id=target_id,
            target_name=target_name,
            session_id=session_id,
            input_params=input_params,
            status="pending",
            **kwargs
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, execution_id: str) -> Optional[ExecutionRecord]:
        """根据 ID 获取执行记录"""
        return self.session.query(ExecutionRecord).filter(
            ExecutionRecord.execution_id == execution_id
        ).first()

    def update_status(
        self,
        execution_id: str,
        status: str,
        output_result: Any = None,
        error_message: str = None,
        **kwargs
    ) -> Optional[ExecutionRecord]:
        """更新执行状态"""
        record = self.get_by_id(execution_id)
        if record:
            record.status = status
            if output_result is not None:
                record.output_result = output_result
            if error_message:
                record.error_message = error_message
            if status in ("success", "error", "completed"):
                record.completed_at = datetime.utcnow()
                if record.started_at:
                    record.duration_ms = (record.completed_at - record.started_at).total_seconds() * 1000

            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)

            self.session.flush()
        return record

    def list_by_session(self, session_id: str) -> List[ExecutionRecord]:
        """获取会话的所有执行记录"""
        return self.session.query(ExecutionRecord).filter(
            ExecutionRecord.session_id == session_id
        ).order_by(ExecutionRecord.started_at).all()

    def list_by_type(
        self,
        execution_type: str,
        status: str = None,
        limit: int = 100
    ) -> List[ExecutionRecord]:
        """按类型获取执行记录"""
        query = self.session.query(ExecutionRecord).filter(
            ExecutionRecord.execution_type == execution_type
        )
        if status:
            query = query.filter(ExecutionRecord.status == status)
        return query.order_by(desc(ExecutionRecord.started_at)).limit(limit).all()

    def get_recent(
        self,
        hours: int = 24,
        execution_type: str = None
    ) -> List[ExecutionRecord]:
        """获取最近的执行记录"""
        since = datetime.utcnow() - timedelta(hours=hours)
        query = self.session.query(ExecutionRecord).filter(
            ExecutionRecord.started_at >= since
        )
        if execution_type:
            query = query.filter(ExecutionRecord.execution_type == execution_type)
        return query.order_by(desc(ExecutionRecord.started_at)).all()


class SessionRepository(BaseRepository):
    """会话记录仓库"""

    def create(
        self,
        user_input: str,
        user_id: str = None,
        **kwargs
    ) -> SessionRecord:
        """创建会话记录"""
        record = SessionRecord(
            session_id=str(uuid.uuid4())[:12],
            user_input=user_input,
            user_id=user_id,
            status="pending",
            **kwargs
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, session_id: str) -> Optional[SessionRecord]:
        """根据 ID 获取会话"""
        return self.session.query(SessionRecord).filter(
            SessionRecord.session_id == session_id
        ).first()

    def update(self, session_id: str, **kwargs) -> Optional[SessionRecord]:
        """更新会话"""
        record = self.get_by_id(session_id)
        if record:
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            self.session.flush()
        return record

    def list_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[SessionRecord]:
        """获取用户的会话列表"""
        return self.session.query(SessionRecord).filter(
            SessionRecord.user_id == user_id
        ).order_by(desc(SessionRecord.started_at)).limit(limit).all()

    def list_pending_approvals(self) -> List[SessionRecord]:
        """获取待审批的会话"""
        return self.session.query(SessionRecord).filter(
            SessionRecord.status == "awaiting_approval"
        ).order_by(SessionRecord.started_at).all()


class AuditRepository(BaseRepository):
    """审计日志仓库"""

    def log(
        self,
        event_type: str,
        action: str,
        session_id: str = None,
        execution_id: str = None,
        user_id: str = None,
        **kwargs
    ) -> AuditLog:
        """记录审计日志"""
        log = AuditLog(
            log_id=str(uuid.uuid4())[:16],
            event_type=event_type,
            action=action,
            session_id=session_id,
            execution_id=execution_id,
            user_id=user_id,
            **kwargs
        )
        self.session.add(log)
        self.session.flush()
        return log

    def get_by_session(self, session_id: str) -> List[AuditLog]:
        """获取会话的审计日志"""
        return self.session.query(AuditLog).filter(
            AuditLog.session_id == session_id
        ).order_by(AuditLog.timestamp).all()

    def get_by_execution(self, execution_id: str) -> List[AuditLog]:
        """获取执行的审计日志"""
        return self.session.query(AuditLog).filter(
            AuditLog.execution_id == execution_id
        ).order_by(AuditLog.timestamp).all()

    def search(
        self,
        event_type: str = None,
        event_category: str = None,
        user_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100
    ) -> List[AuditLog]:
        """搜索审计日志"""
        query = self.session.query(AuditLog)

        if event_type:
            query = query.filter(AuditLog.event_type == event_type)
        if event_category:
            query = query.filter(AuditLog.event_category == event_category)
        if user_id:
            query = query.filter(AuditLog.user_id == user_id)
        if start_time:
            query = query.filter(AuditLog.timestamp >= start_time)
        if end_time:
            query = query.filter(AuditLog.timestamp <= end_time)

        return query.order_by(desc(AuditLog.timestamp)).limit(limit).all()


class MetricsRepository(BaseRepository):
    """指标仓库"""

    def record_snapshot(
        self,
        metric_type: str,
        metric_scope: str,
        value: float,
        target_id: str = None,
        window_start: datetime = None,
        window_end: datetime = None,
        **kwargs
    ) -> MetricSnapshot:
        """记录指标快照"""
        now = datetime.utcnow()
        snapshot = MetricSnapshot(
            metric_type=metric_type,
            metric_scope=metric_scope,
            target_id=target_id,
            value=value,
            window_start=window_start or now - timedelta(minutes=1),
            window_end=window_end or now,
            **kwargs
        )
        self.session.add(snapshot)
        self.session.flush()
        return snapshot

    def get_latest(
        self,
        metric_type: str,
        metric_scope: str,
        target_id: str = None
    ) -> Optional[MetricSnapshot]:
        """获取最新的指标值"""
        query = self.session.query(MetricSnapshot).filter(
            MetricSnapshot.metric_type == metric_type,
            MetricSnapshot.metric_scope == metric_scope
        )
        if target_id:
            query = query.filter(MetricSnapshot.target_id == target_id)
        return query.order_by(desc(MetricSnapshot.window_end)).first()

    def get_time_series(
        self,
        metric_type: str,
        metric_scope: str,
        target_id: str = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 1000
    ) -> List[MetricSnapshot]:
        """获取时间序列数据"""
        query = self.session.query(MetricSnapshot).filter(
            MetricSnapshot.metric_type == metric_type,
            MetricSnapshot.metric_scope == metric_scope
        )
        if target_id:
            query = query.filter(MetricSnapshot.target_id == target_id)
        if start_time:
            query = query.filter(MetricSnapshot.window_start >= start_time)
        if end_time:
            query = query.filter(MetricSnapshot.window_end <= end_time)

        return query.order_by(MetricSnapshot.window_start).limit(limit).all()

    def calculate_success_rate(
        self,
        target_id: str = None,
        hours: int = 24
    ) -> float:
        """计算成功率"""
        since = datetime.utcnow() - timedelta(hours=hours)

        query = self.session.query(
            func.count(ExecutionRecord.id).label("total"),
            func.sum(
                func.case(
                    (ExecutionRecord.status == "success", 1),
                    else_=0
                )
            ).label("success")
        ).filter(ExecutionRecord.started_at >= since)

        if target_id:
            query = query.filter(ExecutionRecord.target_id == target_id)

        result = query.first()
        if result and result.total > 0:
            return result.success / result.total
        return 0.0


class SkillRepository(BaseRepository):
    """Skill 仓库"""

    def create(
        self,
        name: str,
        content: str,
        description: str = None,
        **kwargs
    ) -> SkillRecord:
        """创建 Skill 记录"""
        # 生成 skill_id
        skill_id = name.lower().replace(" ", "-").replace("_", "-")

        record = SkillRecord(
            skill_id=skill_id,
            name=name,
            description=description,
            content=content,
            status="active",
            **kwargs
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, skill_id: str) -> Optional[SkillRecord]:
        """根据 ID 获取 Skill"""
        return self.session.query(SkillRecord).filter(
            SkillRecord.skill_id == skill_id
        ).first()

    def get_by_name(self, name: str) -> Optional[SkillRecord]:
        """根据名称获取 Skill"""
        return self.session.query(SkillRecord).filter(
            SkillRecord.name == name
        ).first()

    def list_active(self, category: str = None) -> List[SkillRecord]:
        """获取活跃的 Skills"""
        query = self.session.query(SkillRecord).filter(
            SkillRecord.status == "active"
        )
        if category:
            query = query.filter(SkillRecord.category == category)
        return query.order_by(SkillRecord.name).all()

    def search(
        self,
        query_text: str,
        limit: int = 20
    ) -> List[SkillRecord]:
        """搜索 Skills"""
        pattern = f"%{query_text}%"
        return self.session.query(SkillRecord).filter(
            or_(
                SkillRecord.name.ilike(pattern),
                SkillRecord.description.ilike(pattern),
            )
        ).limit(limit).all()

    def update_stats(
        self,
        skill_id: str,
        success: bool,
        duration_ms: float
    ):
        """更新 Skill 统计信息"""
        record = self.get_by_id(skill_id)
        if record:
            record.execution_count = (record.execution_count or 0) + 1
            if success:
                record.success_count = (record.success_count or 0) + 1

            # 更新平均时长（移动平均）
            if record.avg_duration_ms:
                record.avg_duration_ms = (record.avg_duration_ms * 0.9) + (duration_ms * 0.1)
            else:
                record.avg_duration_ms = duration_ms

            self.session.flush()


class RecordingRepository(BaseRepository):
    """录制仓库"""

    def create(
        self,
        start_url: str = None,
        recorded_by: str = None,
        **kwargs
    ) -> RecordingSession:
        """创建录制会话"""
        record = RecordingSession(
            recording_id=str(uuid.uuid4())[:12],
            start_url=start_url,
            recorded_by=recorded_by,
            status="recording",
            actions=[],
            action_count=0,
            **kwargs
        )
        self.session.add(record)
        self.session.flush()
        return record

    def get_by_id(self, recording_id: str) -> Optional[RecordingSession]:
        """根据 ID 获取录制"""
        return self.session.query(RecordingSession).filter(
            RecordingSession.recording_id == recording_id
        ).first()

    def add_action(
        self,
        recording_id: str,
        action: dict
    ) -> Optional[RecordingSession]:
        """添加操作到录制"""
        record = self.get_by_id(recording_id)
        if record:
            actions = record.actions or []
            actions.append(action)
            record.actions = actions
            record.action_count = len(actions)
            self.session.flush()
        return record

    def complete(
        self,
        recording_id: str,
        skill_content: str = None
    ) -> Optional[RecordingSession]:
        """完成录制"""
        record = self.get_by_id(recording_id)
        if record:
            record.status = "completed"
            record.completed_at = datetime.utcnow()
            if record.started_at:
                record.duration_ms = (record.completed_at - record.started_at).total_seconds() * 1000
            if skill_content:
                record.skill_content = skill_content
            self.session.flush()
        return record

    def list_by_user(
        self,
        user_id: str,
        limit: int = 50
    ) -> List[RecordingSession]:
        """获取用户的录制列表"""
        return self.session.query(RecordingSession).filter(
            RecordingSession.recorded_by == user_id
        ).order_by(desc(RecordingSession.started_at)).limit(limit).all()
