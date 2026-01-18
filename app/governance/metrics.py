"""
指标收集和统计系统

收集执行指标，提供成功率、耗时等统计
"""

import time
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from collections import defaultdict
from enum import Enum
import threading


class MetricType(str, Enum):
    """指标类型"""
    SUCCESS_RATE = "success_rate"
    DURATION = "duration"
    THROUGHPUT = "throughput"
    ERROR_COUNT = "error_count"
    LATENCY_P50 = "latency_p50"
    LATENCY_P90 = "latency_p90"
    LATENCY_P99 = "latency_p99"


class MetricScope(str, Enum):
    """指标范围"""
    SKILL = "skill"
    WORKFLOW = "workflow"
    AGENT = "agent"
    SYSTEM = "system"
    TOOL = "tool"


@dataclass
class ExecutionMetric:
    """单次执行的指标"""
    execution_id: str
    scope: MetricScope
    target_id: str
    target_name: str
    success: bool
    duration_ms: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    error_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AggregatedMetrics:
    """聚合后的指标"""
    scope: MetricScope
    target_id: str
    time_window: str  # 1min, 5min, 1hour, 24hour

    total_count: int = 0
    success_count: int = 0
    error_count: int = 0

    avg_duration_ms: float = 0.0
    min_duration_ms: float = 0.0
    max_duration_ms: float = 0.0
    p50_duration_ms: float = 0.0
    p90_duration_ms: float = 0.0
    p99_duration_ms: float = 0.0

    @property
    def success_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.success_count / self.total_count

    @property
    def error_rate(self) -> float:
        if self.total_count == 0:
            return 0.0
        return self.error_count / self.total_count


@dataclass
class MetricsDashboard:
    """指标仪表盘"""
    timestamp: datetime
    overall_success_rate: float
    overall_avg_duration_ms: float
    total_executions_24h: int

    skills_metrics: Dict[str, AggregatedMetrics]
    workflows_metrics: Dict[str, AggregatedMetrics]
    agents_metrics: Dict[str, AggregatedMetrics]

    alerts: List[Dict[str, Any]]
    top_errors: List[Dict[str, Any]]


class MetricsCollector:
    """
    指标收集器

    功能：
    - 收集执行指标
    - 计算成功率、耗时等统计
    - 支持多种时间窗口的聚合
    - 提供仪表盘数据
    """

    def __init__(self, retention_hours: int = 24):
        self.retention_hours = retention_hours
        self._metrics: List[ExecutionMetric] = []
        self._lock = threading.Lock()

        # 内存中的聚合缓存
        self._aggregated_cache: Dict[str, AggregatedMetrics] = {}
        self._cache_timestamp: Optional[datetime] = None

    def record(
        self,
        execution_id: str,
        scope: MetricScope,
        target_id: str,
        target_name: str,
        success: bool,
        duration_ms: float,
        error_type: str = None,
        **metadata
    ):
        """记录执行指标"""
        metric = ExecutionMetric(
            execution_id=execution_id,
            scope=scope,
            target_id=target_id,
            target_name=target_name,
            success=success,
            duration_ms=duration_ms,
            error_type=error_type,
            metadata=metadata
        )

        with self._lock:
            self._metrics.append(metric)
            self._cleanup_old_metrics()
            self._cache_timestamp = None  # 使缓存失效

    def _cleanup_old_metrics(self):
        """清理过期的指标"""
        cutoff = datetime.utcnow() - timedelta(hours=self.retention_hours)
        self._metrics = [m for m in self._metrics if m.timestamp > cutoff]

    def get_success_rate(
        self,
        scope: MetricScope = None,
        target_id: str = None,
        hours: int = 24
    ) -> float:
        """获取成功率"""
        metrics = self._filter_metrics(scope, target_id, hours)

        if not metrics:
            return 0.0

        success_count = sum(1 for m in metrics if m.success)
        return success_count / len(metrics)

    def get_avg_duration(
        self,
        scope: MetricScope = None,
        target_id: str = None,
        hours: int = 24
    ) -> float:
        """获取平均耗时"""
        metrics = self._filter_metrics(scope, target_id, hours)

        if not metrics:
            return 0.0

        return sum(m.duration_ms for m in metrics) / len(metrics)

    def get_percentile_duration(
        self,
        percentile: int,
        scope: MetricScope = None,
        target_id: str = None,
        hours: int = 24
    ) -> float:
        """获取耗时百分位数"""
        metrics = self._filter_metrics(scope, target_id, hours)

        if not metrics:
            return 0.0

        durations = sorted([m.duration_ms for m in metrics])
        index = int(len(durations) * percentile / 100)
        return durations[min(index, len(durations) - 1)]

    def _filter_metrics(
        self,
        scope: MetricScope = None,
        target_id: str = None,
        hours: int = 24
    ) -> List[ExecutionMetric]:
        """过滤指标"""
        cutoff = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            metrics = [m for m in self._metrics if m.timestamp > cutoff]

        if scope:
            metrics = [m for m in metrics if m.scope == scope]
        if target_id:
            metrics = [m for m in metrics if m.target_id == target_id]

        return metrics

    def get_aggregated_metrics(
        self,
        scope: MetricScope,
        target_id: str = None,
        time_window: str = "1hour"
    ) -> AggregatedMetrics:
        """获取聚合指标"""
        # 时间窗口映射
        window_hours = {
            "1min": 1 / 60,
            "5min": 5 / 60,
            "1hour": 1,
            "24hour": 24,
        }
        hours = window_hours.get(time_window, 1)

        metrics = self._filter_metrics(scope, target_id, hours)

        if not metrics:
            return AggregatedMetrics(
                scope=scope,
                target_id=target_id or "all",
                time_window=time_window
            )

        durations = sorted([m.duration_ms for m in metrics])

        return AggregatedMetrics(
            scope=scope,
            target_id=target_id or "all",
            time_window=time_window,
            total_count=len(metrics),
            success_count=sum(1 for m in metrics if m.success),
            error_count=sum(1 for m in metrics if not m.success),
            avg_duration_ms=sum(durations) / len(durations),
            min_duration_ms=min(durations),
            max_duration_ms=max(durations),
            p50_duration_ms=durations[len(durations) // 2],
            p90_duration_ms=durations[int(len(durations) * 0.9)],
            p99_duration_ms=durations[int(len(durations) * 0.99)] if len(durations) >= 100 else durations[-1],
        )

    def get_top_errors(self, limit: int = 10, hours: int = 24) -> List[Dict[str, Any]]:
        """获取最常见的错误"""
        metrics = self._filter_metrics(hours=hours)
        error_metrics = [m for m in metrics if not m.success and m.error_type]

        error_counts = defaultdict(int)
        for m in error_metrics:
            key = (m.scope.value, m.target_id, m.error_type)
            error_counts[key] += 1

        sorted_errors = sorted(error_counts.items(), key=lambda x: x[1], reverse=True)

        return [
            {
                "scope": key[0],
                "target_id": key[1],
                "error_type": key[2],
                "count": count
            }
            for key, count in sorted_errors[:limit]
        ]

    def get_dashboard(self) -> MetricsDashboard:
        """获取指标仪表盘"""
        now = datetime.utcnow()

        # 计算整体指标
        all_metrics = self._filter_metrics(hours=24)
        overall_success_rate = self.get_success_rate(hours=24)
        overall_avg_duration = self.get_avg_duration(hours=24)

        # 按 Scope 聚合
        skills_metrics = {}
        workflows_metrics = {}
        agents_metrics = {}

        # 获取唯一的 target_id
        skill_ids = set(m.target_id for m in all_metrics if m.scope == MetricScope.SKILL)
        workflow_ids = set(m.target_id for m in all_metrics if m.scope == MetricScope.WORKFLOW)
        agent_ids = set(m.target_id for m in all_metrics if m.scope == MetricScope.AGENT)

        for sid in skill_ids:
            skills_metrics[sid] = self.get_aggregated_metrics(MetricScope.SKILL, sid, "24hour")

        for wid in workflow_ids:
            workflows_metrics[wid] = self.get_aggregated_metrics(MetricScope.WORKFLOW, wid, "24hour")

        for aid in agent_ids:
            agents_metrics[aid] = self.get_aggregated_metrics(MetricScope.AGENT, aid, "24hour")

        # 获取错误和告警
        top_errors = self.get_top_errors()
        alerts = self._generate_alerts(overall_success_rate, skills_metrics)

        return MetricsDashboard(
            timestamp=now,
            overall_success_rate=overall_success_rate,
            overall_avg_duration_ms=overall_avg_duration,
            total_executions_24h=len(all_metrics),
            skills_metrics=skills_metrics,
            workflows_metrics=workflows_metrics,
            agents_metrics=agents_metrics,
            alerts=alerts,
            top_errors=top_errors,
        )

    def _generate_alerts(
        self,
        overall_success_rate: float,
        skills_metrics: Dict[str, AggregatedMetrics]
    ) -> List[Dict[str, Any]]:
        """生成告警"""
        alerts = []

        # 整体成功率告警
        if overall_success_rate < 0.9:
            alerts.append({
                "level": "warning" if overall_success_rate >= 0.8 else "critical",
                "type": "success_rate",
                "message": f"整体成功率 {overall_success_rate:.1%} 低于阈值 90%",
                "value": overall_success_rate,
                "threshold": 0.9,
            })

        # 单个 Skill 成功率告警
        for skill_id, metrics in skills_metrics.items():
            if metrics.total_count >= 10 and metrics.success_rate < 0.9:
                alerts.append({
                    "level": "warning",
                    "type": "skill_success_rate",
                    "skill_id": skill_id,
                    "message": f"Skill '{skill_id}' 成功率 {metrics.success_rate:.1%} 低于阈值",
                    "value": metrics.success_rate,
                    "threshold": 0.9,
                })

        return alerts

    def export_to_db(self, session):
        """导出指标到数据库"""
        from ..storage.repository import MetricsRepository

        repo = MetricsRepository(session)

        # 导出每个 scope 的聚合指标
        for scope in MetricScope:
            metrics = self.get_aggregated_metrics(scope, time_window="1hour")
            if metrics.total_count > 0:
                repo.record_snapshot(
                    metric_type=MetricType.SUCCESS_RATE.value,
                    metric_scope=scope.value,
                    value=metrics.success_rate,
                    count=metrics.total_count,
                    avg_value=metrics.avg_duration_ms,
                    p50_value=metrics.p50_duration_ms,
                    p90_value=metrics.p90_duration_ms,
                    p99_value=metrics.p99_duration_ms,
                )


# 全局指标收集器
_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """获取指标收集器实例"""
    global _collector
    if _collector is None:
        _collector = MetricsCollector()
    return _collector
