"""
告警管理系统

监控指标，触发告警
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any, Callable
from enum import Enum
import threading


class AlertLevel(str, Enum):
    """告警级别"""
    INFO = "info"           # 信息
    WARNING = "warning"     # 警告
    CRITICAL = "critical"   # 严重
    EMERGENCY = "emergency" # 紧急


class AlertStatus(str, Enum):
    """告警状态"""
    ACTIVE = "active"       # 活跃
    ACKNOWLEDGED = "acknowledged"  # 已确认
    RESOLVED = "resolved"   # 已解决
    SILENCED = "silenced"   # 已静默


@dataclass
class AlertRule:
    """告警规则"""
    rule_id: str
    name: str
    description: str
    level: AlertLevel

    # 规则条件
    metric_type: str        # 指标类型
    metric_scope: str       # 指标范围
    target_id: Optional[str] = None  # 具体目标（可选）

    # 阈值
    threshold: float = 0.0
    operator: str = "lt"    # lt, gt, eq, lte, gte

    # 时间窗口
    window_minutes: int = 5
    min_samples: int = 1    # 最小样本数

    # 告警设置
    cooldown_minutes: int = 10  # 冷却时间
    auto_resolve: bool = True   # 自动恢复

    # 是否启用
    enabled: bool = True


@dataclass
class Alert:
    """告警实例"""
    alert_id: str
    rule_id: str
    rule_name: str
    level: AlertLevel

    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    # 指标信息
    metric_type: str = ""
    metric_scope: str = ""
    target_id: Optional[str] = None
    current_value: float = 0.0
    threshold: float = 0.0

    # 状态
    status: AlertStatus = AlertStatus.ACTIVE
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None

    # 时间
    triggered_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)

    # 通知状态
    notified: bool = False


class AlertManager:
    """
    告警管理器

    功能：
    - 定义告警规则
    - 检查指标触发告警
    - 管理告警生命周期
    - 支持告警通知
    """

    def __init__(self):
        self._rules: Dict[str, AlertRule] = {}
        self._alerts: Dict[str, Alert] = {}
        self._handlers: List[Callable[[Alert], None]] = []
        self._lock = threading.Lock()
        self._last_check: Dict[str, datetime] = {}

        # 注册默认规则
        self._register_default_rules()

    def _register_default_rules(self):
        """注册默认告警规则"""
        default_rules = [
            AlertRule(
                rule_id="success_rate_low",
                name="整体成功率过低",
                description="系统整体成功率低于 90%",
                level=AlertLevel.WARNING,
                metric_type="success_rate",
                metric_scope="system",
                threshold=0.9,
                operator="lt",
                window_minutes=5,
                min_samples=10,
            ),
            AlertRule(
                rule_id="success_rate_critical",
                name="整体成功率严重过低",
                description="系统整体成功率低于 70%",
                level=AlertLevel.CRITICAL,
                metric_type="success_rate",
                metric_scope="system",
                threshold=0.7,
                operator="lt",
                window_minutes=5,
                min_samples=5,
            ),
            AlertRule(
                rule_id="high_latency",
                name="响应延迟过高",
                description="平均响应时间超过 5 秒",
                level=AlertLevel.WARNING,
                metric_type="duration",
                metric_scope="system",
                threshold=5000,
                operator="gt",
                window_minutes=5,
                min_samples=10,
            ),
            AlertRule(
                rule_id="skill_failure_rate",
                name="Skill 失败率过高",
                description="单个 Skill 失败率超过 20%",
                level=AlertLevel.WARNING,
                metric_type="error_rate",
                metric_scope="skill",
                threshold=0.2,
                operator="gt",
                window_minutes=10,
                min_samples=5,
            ),
        ]

        for rule in default_rules:
            self._rules[rule.rule_id] = rule

    def add_rule(self, rule: AlertRule):
        """添加告警规则"""
        with self._lock:
            self._rules[rule.rule_id] = rule

    def remove_rule(self, rule_id: str):
        """移除告警规则"""
        with self._lock:
            self._rules.pop(rule_id, None)

    def get_rules(self) -> List[AlertRule]:
        """获取所有规则"""
        return list(self._rules.values())

    def check_and_trigger(
        self,
        metric_type: str,
        metric_scope: str,
        value: float,
        target_id: str = None,
        sample_count: int = 1
    ):
        """
        检查指标并触发告警

        Args:
            metric_type: 指标类型
            metric_scope: 指标范围
            value: 当前值
            target_id: 目标 ID
            sample_count: 样本数量
        """
        now = datetime.utcnow()

        for rule_id, rule in self._rules.items():
            if not rule.enabled:
                continue

            # 匹配规则
            if rule.metric_type != metric_type:
                continue
            if rule.metric_scope != metric_scope:
                continue
            if rule.target_id and rule.target_id != target_id:
                continue

            # 检查样本数
            if sample_count < rule.min_samples:
                continue

            # 检查冷却时间
            last_check_key = f"{rule_id}:{target_id or 'all'}"
            last_check = self._last_check.get(last_check_key)
            if last_check and (now - last_check) < timedelta(minutes=rule.cooldown_minutes):
                continue

            # 评估条件
            triggered = self._evaluate_condition(value, rule.threshold, rule.operator)

            if triggered:
                self._trigger_alert(rule, value, target_id)
                self._last_check[last_check_key] = now
            elif rule.auto_resolve:
                self._resolve_alert_for_rule(rule_id, target_id)

    def _evaluate_condition(self, value: float, threshold: float, operator: str) -> bool:
        """评估条件"""
        if operator == "lt":
            return value < threshold
        elif operator == "gt":
            return value > threshold
        elif operator == "eq":
            return value == threshold
        elif operator == "lte":
            return value <= threshold
        elif operator == "gte":
            return value >= threshold
        return False

    def _trigger_alert(
        self,
        rule: AlertRule,
        value: float,
        target_id: str = None
    ):
        """触发告警"""
        import uuid

        alert_key = f"{rule.rule_id}:{target_id or 'all'}"

        with self._lock:
            # 检查是否已存在活跃告警
            existing = self._alerts.get(alert_key)
            if existing and existing.status == AlertStatus.ACTIVE:
                # 更新现有告警
                existing.current_value = value
                existing.last_updated = datetime.utcnow()
                return

            # 创建新告警
            alert = Alert(
                alert_id=str(uuid.uuid4())[:12],
                rule_id=rule.rule_id,
                rule_name=rule.name,
                level=rule.level,
                message=self._format_alert_message(rule, value, target_id),
                metric_type=rule.metric_type,
                metric_scope=rule.metric_scope,
                target_id=target_id,
                current_value=value,
                threshold=rule.threshold,
                details={
                    "description": rule.description,
                    "operator": rule.operator,
                }
            )

            self._alerts[alert_key] = alert

        # 通知处理器
        for handler in self._handlers:
            try:
                handler(alert)
            except Exception:
                pass

    def _format_alert_message(
        self,
        rule: AlertRule,
        value: float,
        target_id: str = None
    ) -> str:
        """格式化告警消息"""
        target_str = f" ({target_id})" if target_id else ""
        op_str = {
            "lt": "低于",
            "gt": "超过",
            "eq": "等于",
            "lte": "不超过",
            "gte": "不低于",
        }.get(rule.operator, rule.operator)

        if rule.metric_type == "success_rate":
            return f"{rule.metric_scope}{target_str} 成功率 {value:.1%} {op_str}阈值 {rule.threshold:.1%}"
        elif rule.metric_type == "duration":
            return f"{rule.metric_scope}{target_str} 响应时间 {value:.0f}ms {op_str}阈值 {rule.threshold:.0f}ms"
        else:
            return f"{rule.metric_scope}{target_str} {rule.metric_type} = {value} {op_str}阈值 {rule.threshold}"

    def _resolve_alert_for_rule(self, rule_id: str, target_id: str = None):
        """解决规则相关的告警"""
        alert_key = f"{rule_id}:{target_id or 'all'}"

        with self._lock:
            alert = self._alerts.get(alert_key)
            if alert and alert.status == AlertStatus.ACTIVE:
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = datetime.utcnow()
                alert.last_updated = datetime.utcnow()

    def acknowledge(self, alert_id: str, user: str) -> bool:
        """确认告警"""
        with self._lock:
            for alert in self._alerts.values():
                if alert.alert_id == alert_id:
                    alert.status = AlertStatus.ACKNOWLEDGED
                    alert.acknowledged_by = user
                    alert.acknowledged_at = datetime.utcnow()
                    alert.last_updated = datetime.utcnow()
                    return True
        return False

    def resolve(self, alert_id: str) -> bool:
        """解决告警"""
        with self._lock:
            for alert in self._alerts.values():
                if alert.alert_id == alert_id:
                    alert.status = AlertStatus.RESOLVED
                    alert.resolved_at = datetime.utcnow()
                    alert.last_updated = datetime.utcnow()
                    return True
        return False

    def silence(self, alert_id: str, duration_minutes: int = 60) -> bool:
        """静默告警"""
        with self._lock:
            for alert in self._alerts.values():
                if alert.alert_id == alert_id:
                    alert.status = AlertStatus.SILENCED
                    alert.last_updated = datetime.utcnow()
                    # TODO: 设置自动恢复定时器
                    return True
        return False

    def get_active_alerts(self, level: AlertLevel = None) -> List[Alert]:
        """获取活跃告警"""
        with self._lock:
            alerts = [a for a in self._alerts.values() if a.status == AlertStatus.ACTIVE]

        if level:
            alerts = [a for a in alerts if a.level == level]

        # 按级别和时间排序
        level_order = {
            AlertLevel.EMERGENCY: 0,
            AlertLevel.CRITICAL: 1,
            AlertLevel.WARNING: 2,
            AlertLevel.INFO: 3,
        }
        alerts.sort(key=lambda a: (level_order.get(a.level, 4), -a.triggered_at.timestamp()))

        return alerts

    def get_all_alerts(self, limit: int = 100) -> List[Alert]:
        """获取所有告警"""
        with self._lock:
            alerts = list(self._alerts.values())

        alerts.sort(key=lambda a: a.triggered_at, reverse=True)
        return alerts[:limit]

    def add_handler(self, handler: Callable[[Alert], None]):
        """添加告警处理器"""
        self._handlers.append(handler)

    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        alerts = self.get_all_alerts(limit=1000)

        return {
            "total": len(alerts),
            "active": len([a for a in alerts if a.status == AlertStatus.ACTIVE]),
            "acknowledged": len([a for a in alerts if a.status == AlertStatus.ACKNOWLEDGED]),
            "resolved": len([a for a in alerts if a.status == AlertStatus.RESOLVED]),
            "by_level": {
                "emergency": len([a for a in alerts if a.level == AlertLevel.EMERGENCY and a.status == AlertStatus.ACTIVE]),
                "critical": len([a for a in alerts if a.level == AlertLevel.CRITICAL and a.status == AlertStatus.ACTIVE]),
                "warning": len([a for a in alerts if a.level == AlertLevel.WARNING and a.status == AlertStatus.ACTIVE]),
                "info": len([a for a in alerts if a.level == AlertLevel.INFO and a.status == AlertStatus.ACTIVE]),
            }
        }


# 全局告警管理器
_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """获取告警管理器实例"""
    global _manager
    if _manager is None:
        _manager = AlertManager()
    return _manager
