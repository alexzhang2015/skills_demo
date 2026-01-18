"""
数据库 ORM 模型

定义所有持久化实体
"""

from datetime import datetime
from typing import Optional
import json

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Float,
    Boolean, ForeignKey, JSON, Enum as SQLEnum, Index
)
from sqlalchemy.orm import relationship

from .database import Base


class ExecutionRecord(Base):
    """
    执行记录表

    记录 Skill/Workflow/Agent 的执行历史
    """
    __tablename__ = "execution_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(64), unique=True, nullable=False, index=True)

    # 执行类型和目标
    execution_type = Column(String(32), nullable=False)  # skill, workflow, agent, master
    target_id = Column(String(128), nullable=False)      # skill_id, workflow_id, etc.
    target_name = Column(String(256))

    # 执行上下文
    session_id = Column(String(64), index=True)          # 关联的 Master Session
    parent_execution_id = Column(String(64))             # 父执行（用于嵌套）
    trace_id = Column(String(64), index=True)            # 链路追踪 ID

    # 输入输出
    input_params = Column(JSON)
    output_result = Column(JSON)
    context = Column(JSON)                               # 执行上下文数据

    # 状态和错误
    status = Column(String(32), nullable=False, default="pending")
    error_message = Column(Text)
    error_details = Column(JSON)

    # 时间统计
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)

    # 工具调用记录
    tool_calls = Column(JSON)                            # [{tool, params, result, duration}]

    # 重试信息
    retry_count = Column(Integer, default=0)
    max_retries = Column(Integer, default=3)

    # 元数据
    provider = Column(String(32))                        # LLM provider used
    model = Column(String(64))                           # Model used
    tokens_used = Column(JSON)                           # {input, output, total}
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 索引
    __table_args__ = (
        Index("ix_execution_records_type_status", "execution_type", "status"),
        Index("ix_execution_records_target", "target_id"),
        Index("ix_execution_records_time", "started_at"),
    )


class SessionRecord(Base):
    """
    会话记录表

    记录 Master Agent 会话
    """
    __tablename__ = "session_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(64), unique=True, nullable=False, index=True)

    # 用户输入
    user_input = Column(Text, nullable=False)
    enriched_input = Column(Text)                        # 丰富化后的输入

    # 意图分析
    intent_type = Column(String(64))
    intent_confidence = Column(Float)
    entities = Column(JSON)                              # 提取的实体

    # 执行计划
    execution_plan = Column(JSON)
    matched_template = Column(String(128))

    # 执行结果
    status = Column(String(32), nullable=False, default="pending")
    final_result = Column(Text)
    summary = Column(Text)

    # 审批信息
    pending_approvals = Column(JSON)                     # 待审批项
    approved_by = Column(String(128))
    approved_at = Column(DateTime)
    approval_notes = Column(Text)

    # 关联的执行
    agent_tasks = Column(JSON)                           # 分配给 Agent 的任务
    execution_ids = Column(JSON)                         # 关联的执行 ID 列表

    # 时间统计
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)

    # 用户信息
    user_id = Column(String(64))
    user_name = Column(String(128))

    # 元数据
    provider = Column(String(32))
    model = Column(String(64))
    tokens_used = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_session_records_status", "status"),
        Index("ix_session_records_user", "user_id"),
        Index("ix_session_records_time", "started_at"),
    )


class AuditLog(Base):
    """
    审计日志表

    记录所有重要操作
    """
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    log_id = Column(String(64), unique=True, nullable=False, index=True)

    # 事件类型
    event_type = Column(String(64), nullable=False)      # execution_start, tool_call, approval, error
    event_category = Column(String(32))                  # skill, workflow, agent, system

    # 关联 ID
    session_id = Column(String(64), index=True)
    execution_id = Column(String(64), index=True)
    trace_id = Column(String(64), index=True)

    # 事件详情
    action = Column(String(256), nullable=False)         # 操作描述
    target = Column(String(256))                         # 操作目标
    details = Column(JSON)                               # 详细信息

    # 结果
    status = Column(String(32))                          # success, failure, pending
    error_message = Column(Text)

    # 用户信息
    user_id = Column(String(64))
    user_name = Column(String(128))
    user_role = Column(String(64))

    # 来源信息
    ip_address = Column(String(64))
    user_agent = Column(String(512))
    source = Column(String(64))                          # api, web, cli

    # 时间
    timestamp = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = (
        Index("ix_audit_logs_event", "event_type", "event_category"),
        Index("ix_audit_logs_session", "session_id"),
    )


class MetricSnapshot(Base):
    """
    指标快照表

    记录执行指标的时间序列数据
    """
    __tablename__ = "metric_snapshots"

    id = Column(Integer, primary_key=True, autoincrement=True)

    # 指标标识
    metric_type = Column(String(64), nullable=False)     # success_rate, duration, throughput
    metric_scope = Column(String(32), nullable=False)    # skill, workflow, agent, system
    target_id = Column(String(128))                      # 具体的 skill_id 等

    # 时间窗口
    window_start = Column(DateTime, nullable=False)
    window_end = Column(DateTime, nullable=False)
    window_size = Column(String(16))                     # 1min, 5min, 1hour, 1day

    # 指标值
    value = Column(Float, nullable=False)
    count = Column(Integer)                              # 样本数量

    # 详细统计
    min_value = Column(Float)
    max_value = Column(Float)
    avg_value = Column(Float)
    p50_value = Column(Float)
    p90_value = Column(Float)
    p99_value = Column(Float)

    # 额外数据
    labels = Column(JSON)                                # 标签（用于过滤）
    metadata = Column(JSON)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("ix_metric_snapshots_type", "metric_type", "metric_scope"),
        Index("ix_metric_snapshots_target", "target_id"),
        Index("ix_metric_snapshots_window", "window_start", "window_end"),
    )


class SkillRecord(Base):
    """
    Skill 记录表

    存储 Skill 定义和版本历史
    """
    __tablename__ = "skill_records"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(128), nullable=False, index=True)

    # 基本信息
    name = Column(String(256), nullable=False)
    description = Column(Text)
    version = Column(String(32), default="1.0")

    # 内容
    content = Column(Text, nullable=False)               # SKILL.md 完整内容
    parsed_data = Column(JSON)                           # 解析后的结构化数据

    # 分类和标签
    category = Column(String(64))
    tags = Column(JSON)

    # 配置
    allowed_tools = Column(JSON)
    input_schema = Column(JSON)
    output_schema = Column(JSON)

    # 来源
    source = Column(String(32))                          # file, recording, generated
    source_path = Column(String(512))                    # 文件路径
    recording_id = Column(String(64))                    # 关联的录制 ID

    # 状态
    status = Column(String(32), default="active")        # active, draft, archived
    is_published = Column(Boolean, default=False)

    # 统计
    execution_count = Column(Integer, default=0)
    success_count = Column(Integer, default=0)
    avg_duration_ms = Column(Float)

    # 所有者
    owner = Column(String(128))
    created_by = Column(String(64))
    updated_by = Column(String(64))

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_skill_records_name", "name"),
        Index("ix_skill_records_category", "category"),
        Index("ix_skill_records_status", "status"),
    )


class RecordingSession(Base):
    """
    录制会话表

    存储 Chrome 操作录制
    """
    __tablename__ = "recording_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    recording_id = Column(String(64), unique=True, nullable=False, index=True)

    # 基本信息
    name = Column(String(256))
    description = Column(Text)

    # 录制内容
    actions = Column(JSON, nullable=False)               # 操作序列
    action_count = Column(Integer, default=0)

    # 页面信息
    start_url = Column(String(1024))
    pages_visited = Column(JSON)                         # 访问过的页面列表

    # 生成的 Skill
    generated_skill_id = Column(String(128))             # 生成的 Skill ID
    skill_content = Column(Text)                         # 生成的 SKILL.md 内容

    # 状态
    status = Column(String(32), default="recording")     # recording, completed, processed, failed

    # 时间
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_ms = Column(Float)

    # 用户信息
    recorded_by = Column(String(64))

    # 元数据
    browser_info = Column(JSON)
    metadata = Column(JSON)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index("ix_recording_sessions_status", "status"),
        Index("ix_recording_sessions_user", "recorded_by"),
    )
