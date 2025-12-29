"""
Layer 4: Skills 执行层 (原子操作)

职责:
- 执行单一职责的原子技能
- 调用 MCP Tools 与后端系统交互
- 返回结构化执行结果
"""

import uuid
import time
from datetime import datetime
from typing import Optional, Any

from ..models import (
    AtomicSkill,
    SkillExecution,
    MCPToolCall,
    ExecutionStatus,
)
from ..mcp import MCPClient, MCPToolResult


class SkillExecutor:
    """原子技能执行器"""

    # 技能到MCP工具的映射
    SKILL_TO_MCP_TOOLS = {
        "create-sku": ["inventory.sku.create"],
        "config-pos-item": ["pos.product.create"],
        "sync-app-product": ["app.product.sync"],
        "update-menu-board": ["menuboard.content.update"],
        "calculate-price": ["pricing.calculate", "pricing.competitor.analyze"],
        "update-pos-price": ["pos.price.update"],
        "sync-app-price": ["app.price.sync"],
        "create-campaign": ["marketing.campaign.create"],
        "config-pos-discount": ["pos.discount.config"],
        "setup-member-points": ["crm.points.config"],
        "create-training-task": ["training.task.create"],
        "send-notification": ["app.notification.send"],
        "fetch-sales-data": ["analytics.sales.query"],
        "generate-report": ["analytics.report.generate"],
    }

    def __init__(self):
        self.skills: dict[str, AtomicSkill] = {}
        self.executions: dict[str, SkillExecution] = {}
        self.mcp_client = MCPClient()  # MCP客户端
        self._init_atomic_skills()

    def _init_atomic_skills(self):
        """初始化原子技能库"""
        atomic_skills = [
            # 产品管理相关
            AtomicSkill(
                id="create-sku",
                name="create-sku",
                description="创建商品SKU",
                category="product",
                target_systems=["INVENTORY"],
                input_schema={"product_name": "str", "price": "float", "category": "str"},
                output_schema={"sku_id": "str", "status": "str"},
            ),
            AtomicSkill(
                id="config-pos-item",
                name="config-pos-item",
                description="配置POS菜单项",
                category="product",
                target_systems=["POS"],
                input_schema={"sku_id": "str", "button_position": "str", "price": "float"},
                output_schema={"pos_item_id": "str", "affected_stores": "int"},
            ),
            AtomicSkill(
                id="sync-app-product",
                name="sync-app-product",
                description="同步App商品信息",
                category="product",
                target_systems=["APP"],
                input_schema={"sku_id": "str", "product_info": "dict"},
                output_schema={"app_product_id": "str", "status": "str"},
            ),
            AtomicSkill(
                id="update-menu-board",
                name="update-menu-board",
                description="更新菜单屏内容",
                category="product",
                target_systems=["MENU_BOARD"],
                input_schema={"product_id": "str", "display_config": "dict"},
                output_schema={"success_rate": "float", "failed_stores": "list"},
            ),

            # 定价相关
            AtomicSkill(
                id="calculate-price",
                name="calculate-price",
                description="计算最优价格",
                category="pricing",
                target_systems=["PRICING"],
                input_schema={"product_id": "str", "region": "str", "adjustment": "float"},
                output_schema={"suggested_price": "float", "elasticity": "float"},
            ),
            AtomicSkill(
                id="update-pos-price",
                name="update-pos-price",
                description="更新POS价格表",
                category="pricing",
                target_systems=["POS"],
                input_schema={"product_id": "str", "region": "str", "new_price": "float"},
                output_schema={"affected_stores": "int", "effective_time": "str"},
            ),
            AtomicSkill(
                id="sync-app-price",
                name="sync-app-price",
                description="同步App价格",
                category="pricing",
                target_systems=["APP"],
                input_schema={"product_id": "str", "new_price": "float"},
                output_schema={"cache_cleared": "bool"},
            ),

            # 营销相关
            AtomicSkill(
                id="create-campaign",
                name="create-campaign",
                description="创建营销活动",
                category="marketing",
                target_systems=["MARKETING"],
                input_schema={"campaign_type": "str", "rules": "dict", "duration": "dict"},
                output_schema={"campaign_id": "str", "status": "str"},
            ),
            AtomicSkill(
                id="config-pos-discount",
                name="config-pos-discount",
                description="配置POS折扣规则",
                category="marketing",
                target_systems=["POS"],
                input_schema={"campaign_id": "str", "discount_rules": "dict"},
                output_schema={"rule_id": "str", "effective": "bool"},
            ),
            AtomicSkill(
                id="setup-member-points",
                name="setup-member-points",
                description="设置会员积分规则",
                category="marketing",
                target_systems=["CRM"],
                input_schema={"campaign_id": "str", "points_config": "dict"},
                output_schema={"config_id": "str"},
            ),

            # 培训相关
            AtomicSkill(
                id="create-training-task",
                name="create-training-task",
                description="创建培训任务",
                category="training",
                target_systems=["TRAINING"],
                input_schema={"product_id": "str", "training_type": "str"},
                output_schema={"task_id": "str", "estimated_days": "int"},
            ),

            # 通知相关
            AtomicSkill(
                id="send-notification",
                name="send-notification",
                description="发送系统通知",
                category="notification",
                target_systems=["APP"],
                input_schema={"recipients": "list", "message": "str", "channel": "str"},
                output_schema={"sent_count": "int", "failed_count": "int"},
            ),

            # 报告相关
            AtomicSkill(
                id="fetch-sales-data",
                name="fetch-sales-data",
                description="获取销售数据",
                category="report",
                target_systems=["POS"],
                input_schema={"date_range": "dict", "region": "str"},
                output_schema={"total_sales": "float", "order_count": "int"},
            ),
            AtomicSkill(
                id="generate-report",
                name="generate-report",
                description="生成分析报告",
                category="report",
                target_systems=["APP"],
                input_schema={"report_type": "str", "data": "dict"},
                output_schema={"report_id": "str", "file_path": "str"},
            ),
        ]

        for skill in atomic_skills:
            self.skills[skill.id] = skill

    def get_skill(self, skill_id: str) -> Optional[AtomicSkill]:
        return self.skills.get(skill_id)

    def get_all_skills(self) -> list[AtomicSkill]:
        return list(self.skills.values())

    def get_skills_by_category(self, category: str) -> list[AtomicSkill]:
        return [s for s in self.skills.values() if s.category == category]

    def execute(self, skill_id: str, params: dict = {}) -> SkillExecution:
        """执行原子技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return SkillExecution(
                execution_id=str(uuid.uuid4())[:8],
                skill_id=skill_id,
                skill_name="unknown",
                status=ExecutionStatus.ERROR,
                error=f"Skill '{skill_id}' not found",
            )

        execution_id = str(uuid.uuid4())[:8]
        execution = SkillExecution(
            execution_id=execution_id,
            skill_id=skill.id,
            skill_name=skill.name,
            input_params=params,
            status=ExecutionStatus.RUNNING,
            started_at=datetime.now(),
        )

        try:
            # 开始MCP追踪
            trace_id = self.mcp_client.start_trace()

            # 通过MCP工具映射调用后端系统
            tool_calls = []
            mcp_tool_ids = self.SKILL_TO_MCP_TOOLS.get(skill_id, [])

            for mcp_tool_id in mcp_tool_ids:
                mcp_result = self.mcp_client.call_tool(mcp_tool_id, params)
                tool_call = self._convert_mcp_result_to_tool_call(mcp_result)
                tool_calls.append(tool_call)

            execution.tool_calls = tool_calls
            execution.trace_id = trace_id  # 关联追踪ID

            # 生成执行结果（合并MCP返回）
            execution.output_result = self._generate_skill_result(skill, params, tool_calls)
            execution.status = ExecutionStatus.SUCCESS

            # 结束MCP追踪
            self.mcp_client.end_trace()

        except Exception as e:
            execution.status = ExecutionStatus.ERROR
            execution.error = str(e)

        execution.completed_at = datetime.now()
        execution.duration_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000

        self.executions[execution_id] = execution
        return execution

    def _convert_mcp_result_to_tool_call(self, mcp_result: MCPToolResult) -> MCPToolCall:
        """将MCPToolResult转换为MCPToolCall格式"""
        return MCPToolCall(
            tool_id=mcp_result.request_id or str(uuid.uuid4())[:8],
            system=mcp_result.server_id,
            operation=mcp_result.tool_name,
            params=mcp_result.input_params or {},
            status=ExecutionStatus.SUCCESS if mcp_result.status.value == "success" else ExecutionStatus.ERROR,
            result=mcp_result.output_data,
            started_at=mcp_result.started_at,
            completed_at=mcp_result.completed_at,
            duration_ms=mcp_result.duration_ms,
        )

    def _generate_skill_result(self, skill: AtomicSkill, params: dict, tool_calls: list[MCPToolCall] = None) -> dict:
        """生成技能执行结果 - 优先使用MCP工具返回，否则使用默认值"""
        # 如果有MCP工具调用结果，合并它们
        if tool_calls:
            merged_result = {}
            for tool_call in tool_calls:
                if tool_call.result:
                    merged_result.update(tool_call.result)
            if merged_result:
                # 添加技能元数据
                merged_result["_skill_id"] = skill.id
                merged_result["_mcp_tools_called"] = [tc.operation for tc in tool_calls]
                return merged_result

        # 后备：使用默认模拟结果
        default_results = {
            "create-sku": {
                "sku_id": f"SKU-{uuid.uuid4().hex[:8].upper()}",
                "status": "created",
                "product_name": params.get("product_name", "未知商品"),
            },
            "config-pos-item": {
                "pos_item_id": f"POS-{uuid.uuid4().hex[:6].upper()}",
                "affected_stores": 2847,
                "button_position": params.get("button_position", "A1"),
            },
            "sync-app-product": {
                "app_product_id": f"APP-{uuid.uuid4().hex[:6].upper()}",
                "status": "synced",
            },
            "update-menu-board": {
                "success_rate": 0.998,
                "failed_stores": ["SH-0234", "BJ-0891"],
            },
            "calculate-price": {
                "suggested_price": params.get("base_price", 25.0) * (1 + params.get("adjustment", 0)),
                "elasticity": -0.42,
                "competitor_range": [21.0, 28.0],
            },
            "update-pos-price": {
                "affected_stores": 1234,
                "effective_time": "明日 06:00",
            },
            "sync-app-price": {
                "cache_cleared": True,
            },
            "create-campaign": {
                "campaign_id": f"CMP-{uuid.uuid4().hex[:8].upper()}",
                "status": "active",
            },
            "config-pos-discount": {
                "rule_id": f"RULE-{uuid.uuid4().hex[:6].upper()}",
                "effective": True,
            },
            "setup-member-points": {
                "config_id": f"PTS-{uuid.uuid4().hex[:6].upper()}",
            },
            "create-training-task": {
                "task_id": f"TRN-{uuid.uuid4().hex[:6].upper()}",
                "estimated_days": 3,
            },
            "send-notification": {
                "sent_count": params.get("recipients", ["all"]).__len__() if isinstance(params.get("recipients"), list) else 100,
                "failed_count": 0,
            },
            "fetch-sales-data": {
                "total_sales": 45200000.0,
                "order_count": 612000,
                "avg_order_value": 73.8,
            },
            "generate-report": {
                "report_id": f"RPT-{uuid.uuid4().hex[:8].upper()}",
                "file_path": f"/reports/report_{datetime.now().strftime('%Y%m%d')}.pdf",
            },
        }

        return default_results.get(skill.id, {"status": "completed"})

    def get_execution(self, execution_id: str) -> Optional[SkillExecution]:
        return self.executions.get(execution_id)
