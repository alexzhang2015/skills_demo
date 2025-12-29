"""
MCP Tool 定义

定义MCP服务器提供的具体工具和调用接口
"""

import uuid
from datetime import datetime
from typing import Optional, Any
from pydantic import BaseModel
from enum import Enum


class MCPToolStatus(str, Enum):
    """工具执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    TIMEOUT = "timeout"


class MCPToolResult(BaseModel):
    """MCP工具执行结果"""
    tool_id: str
    server_id: str
    tool_name: str
    status: MCPToolStatus = MCPToolStatus.PENDING
    input_params: dict = {}
    output_data: Optional[dict] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0
    retry_count: int = 0

    # 追踪信息
    request_id: str = ""
    trace_id: str = ""


class MCPTool(BaseModel):
    """MCP工具定义"""
    id: str
    name: str
    description: str
    server_id: str
    category: str = "general"

    # 输入输出schema
    input_schema: dict = {}
    output_schema: dict = {}

    # 执行配置
    requires_approval: bool = False
    is_dangerous: bool = False  # 危险操作需要确认
    timeout_ms: int = 30000
    retry_enabled: bool = True


class MCPToolRegistry:
    """MCP工具注册表"""

    # 所有MCP工具定义
    TOOLS = {
        # ==================== POS系统工具 ====================
        "pos.product.create": MCPTool(
            id="pos.product.create",
            name="创建POS商品",
            description="在POS系统中创建新商品条目",
            server_id="pos",
            category="product",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "name": {"type": "string", "required": True},
                "price": {"type": "number", "required": True},
                "category": {"type": "string", "required": True},
                "button_position": {"type": "string", "required": False},
                "modifier_groups": {"type": "array", "required": False},
            },
            output_schema={
                "pos_item_id": "string",
                "created_at": "datetime",
                "sync_status": "string",
            },
        ),
        "pos.product.batch_update": MCPTool(
            id="pos.product.batch_update",
            name="批量更新POS商品",
            description="批量更新多个商品信息",
            server_id="pos",
            category="product",
            input_schema={
                "items": {"type": "array", "required": True},
                "store_scope": {"type": "string", "required": False},
            },
            output_schema={
                "updated_count": "integer",
                "failed_items": "array",
            },
        ),
        "pos.price.update": MCPTool(
            id="pos.price.update",
            name="更新POS价格",
            description="更新商品在POS系统中的价格",
            server_id="pos",
            category="pricing",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "new_price": {"type": "number", "required": True},
                "effective_time": {"type": "datetime", "required": False},
                "store_scope": {"type": "string", "required": False},
            },
            output_schema={
                "affected_stores": "integer",
                "effective_time": "datetime",
            },
            requires_approval=True,
        ),
        "pos.discount.config": MCPTool(
            id="pos.discount.config",
            name="配置POS折扣",
            description="配置POS系统的折扣规则",
            server_id="pos",
            category="marketing",
            input_schema={
                "campaign_id": {"type": "string", "required": True},
                "discount_type": {"type": "string", "required": True},
                "rules": {"type": "object", "required": True},
            },
            output_schema={
                "rule_id": "string",
                "store_count": "integer",
            },
        ),
        "pos.store.sync": MCPTool(
            id="pos.store.sync",
            name="同步门店数据",
            description="触发门店数据同步",
            server_id="pos",
            category="operations",
            input_schema={
                "store_ids": {"type": "array", "required": False},
                "sync_type": {"type": "string", "required": True},
            },
            output_schema={
                "synced_count": "integer",
                "pending_count": "integer",
            },
        ),

        # ==================== App后台工具 ====================
        "app.product.sync": MCPTool(
            id="app.product.sync",
            name="同步App商品",
            description="将商品信息同步到App",
            server_id="app",
            category="product",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "product_info": {"type": "object", "required": True},
                "images": {"type": "array", "required": False},
            },
            output_schema={
                "app_product_id": "string",
                "cache_cleared": "boolean",
            },
        ),
        "app.notification.send": MCPTool(
            id="app.notification.send",
            name="发送App通知",
            description="向用户发送App推送通知",
            server_id="app",
            category="notification",
            input_schema={
                "title": {"type": "string", "required": True},
                "body": {"type": "string", "required": True},
                "target_type": {"type": "string", "required": True},
                "target_ids": {"type": "array", "required": False},
            },
            output_schema={
                "sent_count": "integer",
                "failed_count": "integer",
                "notification_id": "string",
            },
        ),
        "app.price.sync": MCPTool(
            id="app.price.sync",
            name="同步App价格",
            description="同步商品价格到App并清除缓存",
            server_id="app",
            category="pricing",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "new_price": {"type": "number", "required": True},
            },
            output_schema={
                "cache_cleared": "boolean",
                "effective_at": "datetime",
            },
        ),
        "app.content.publish": MCPTool(
            id="app.content.publish",
            name="发布App内容",
            description="发布App首页或详情页内容",
            server_id="app",
            category="content",
            input_schema={
                "content_type": {"type": "string", "required": True},
                "content_data": {"type": "object", "required": True},
                "schedule_time": {"type": "datetime", "required": False},
            },
            output_schema={
                "content_id": "string",
                "publish_status": "string",
            },
        ),

        # ==================== 库存系统工具 ====================
        "inventory.sku.create": MCPTool(
            id="inventory.sku.create",
            name="创建SKU",
            description="在库存系统中创建商品SKU",
            server_id="inventory",
            category="product",
            input_schema={
                "product_name": {"type": "string", "required": True},
                "category": {"type": "string", "required": True},
                "unit": {"type": "string", "required": True},
                "cost": {"type": "number", "required": False},
            },
            output_schema={
                "sku_id": "string",
                "barcode": "string",
                "created_at": "datetime",
            },
        ),
        "inventory.bom.create": MCPTool(
            id="inventory.bom.create",
            name="创建BOM",
            description="创建商品物料清单(Bill of Materials)",
            server_id="inventory",
            category="product",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "materials": {"type": "array", "required": True},
            },
            output_schema={
                "bom_id": "string",
                "material_count": "integer",
            },
        ),
        "inventory.stock.query": MCPTool(
            id="inventory.stock.query",
            name="查询库存",
            description="查询指定SKU的库存情况",
            server_id="inventory",
            category="query",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "store_scope": {"type": "string", "required": False},
            },
            output_schema={
                "total_stock": "number",
                "available_stock": "number",
                "store_breakdown": "array",
            },
        ),
        "inventory.stock.reserve": MCPTool(
            id="inventory.stock.reserve",
            name="预留库存",
            description="为新品上市预留库存",
            server_id="inventory",
            category="operations",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "quantity": {"type": "number", "required": True},
                "stores": {"type": "array", "required": True},
            },
            output_schema={
                "reservation_id": "string",
                "reserved_quantity": "number",
            },
        ),

        # ==================== 定价引擎工具 ====================
        "pricing.calculate": MCPTool(
            id="pricing.calculate",
            name="计算建议价格",
            description="基于成本、竞品、需求弹性计算建议价格",
            server_id="pricing",
            category="pricing",
            input_schema={
                "sku_id": {"type": "string", "required": True},
                "cost": {"type": "number", "required": True},
                "target_margin": {"type": "number", "required": False},
                "region": {"type": "string", "required": False},
            },
            output_schema={
                "suggested_price": "number",
                "margin": "number",
                "elasticity": "number",
                "competitor_range": "array",
            },
        ),
        "pricing.competitor.analyze": MCPTool(
            id="pricing.competitor.analyze",
            name="竞品价格分析",
            description="分析竞品定价策略",
            server_id="pricing",
            category="analytics",
            input_schema={
                "product_category": {"type": "string", "required": True},
                "region": {"type": "string", "required": False},
            },
            output_schema={
                "competitor_prices": "array",
                "avg_price": "number",
                "price_position": "string",
            },
        ),

        # ==================== CRM系统工具 ====================
        "crm.member.segment": MCPTool(
            id="crm.member.segment",
            name="会员分群",
            description="根据条件筛选会员分群",
            server_id="crm",
            category="marketing",
            input_schema={
                "criteria": {"type": "object", "required": True},
                "limit": {"type": "integer", "required": False},
            },
            output_schema={
                "segment_id": "string",
                "member_count": "integer",
            },
        ),
        "crm.points.config": MCPTool(
            id="crm.points.config",
            name="配置积分规则",
            description="配置活动积分奖励规则",
            server_id="crm",
            category="marketing",
            input_schema={
                "campaign_id": {"type": "string", "required": True},
                "points_multiplier": {"type": "number", "required": True},
                "conditions": {"type": "object", "required": False},
            },
            output_schema={
                "rule_id": "string",
                "effective_from": "datetime",
            },
        ),
        "crm.coupon.batch_issue": MCPTool(
            id="crm.coupon.batch_issue",
            name="批量发券",
            description="向指定会员批量发放优惠券",
            server_id="crm",
            category="marketing",
            input_schema={
                "coupon_template_id": {"type": "string", "required": True},
                "member_segment_id": {"type": "string", "required": True},
            },
            output_schema={
                "issued_count": "integer",
                "coupon_batch_id": "string",
            },
        ),

        # ==================== 营销平台工具 ====================
        "marketing.campaign.create": MCPTool(
            id="marketing.campaign.create",
            name="创建营销活动",
            description="创建新的营销活动",
            server_id="marketing",
            category="marketing",
            input_schema={
                "name": {"type": "string", "required": True},
                "type": {"type": "string", "required": True},
                "start_time": {"type": "datetime", "required": True},
                "end_time": {"type": "datetime", "required": True},
                "rules": {"type": "object", "required": True},
            },
            output_schema={
                "campaign_id": "string",
                "status": "string",
            },
        ),
        "marketing.banner.schedule": MCPTool(
            id="marketing.banner.schedule",
            name="排期Banner",
            description="为活动排期App/门店Banner",
            server_id="marketing",
            category="content",
            input_schema={
                "campaign_id": {"type": "string", "required": True},
                "banner_images": {"type": "array", "required": True},
                "positions": {"type": "array", "required": True},
            },
            output_schema={
                "banner_ids": "array",
                "schedule_status": "string",
            },
        ),

        # ==================== 菜单屏CMS工具 ====================
        "menuboard.content.update": MCPTool(
            id="menuboard.content.update",
            name="更新菜单屏内容",
            description="更新店内菜单屏显示内容",
            server_id="menu_board",
            category="content",
            input_schema={
                "product_id": {"type": "string", "required": True},
                "display_config": {"type": "object", "required": True},
                "store_scope": {"type": "string", "required": False},
            },
            output_schema={
                "updated_stores": "integer",
                "failed_stores": "array",
            },
        ),
        "menuboard.sync.trigger": MCPTool(
            id="menuboard.sync.trigger",
            name="触发菜单屏同步",
            description="触发指定门店的菜单屏数据同步",
            server_id="menu_board",
            category="operations",
            input_schema={
                "store_ids": {"type": "array", "required": False},
                "force": {"type": "boolean", "required": False},
            },
            output_schema={
                "sync_job_id": "string",
                "estimated_minutes": "integer",
            },
        ),

        # ==================== 培训系统工具 ====================
        "training.task.create": MCPTool(
            id="training.task.create",
            name="创建培训任务",
            description="为新品创建员工培训任务",
            server_id="training",
            category="training",
            input_schema={
                "product_id": {"type": "string", "required": True},
                "training_type": {"type": "string", "required": True},
                "target_roles": {"type": "array", "required": True},
                "deadline_days": {"type": "integer", "required": False},
            },
            output_schema={
                "task_id": "string",
                "target_count": "integer",
                "deadline": "datetime",
            },
        ),
        "training.progress.query": MCPTool(
            id="training.progress.query",
            name="查询培训进度",
            description="查询培训任务完成进度",
            server_id="training",
            category="query",
            input_schema={
                "task_id": {"type": "string", "required": True},
            },
            output_schema={
                "completed_count": "integer",
                "total_count": "integer",
                "completion_rate": "number",
            },
        ),

        # ==================== 数据分析工具 ====================
        "analytics.sales.query": MCPTool(
            id="analytics.sales.query",
            name="查询销售数据",
            description="查询指定时间范围的销售数据",
            server_id="analytics",
            category="query",
            input_schema={
                "start_date": {"type": "date", "required": True},
                "end_date": {"type": "date", "required": True},
                "dimensions": {"type": "array", "required": False},
            },
            output_schema={
                "total_sales": "number",
                "order_count": "integer",
                "data": "array",
            },
        ),
        "analytics.report.generate": MCPTool(
            id="analytics.report.generate",
            name="生成分析报告",
            description="生成指定类型的分析报告",
            server_id="analytics",
            category="report",
            input_schema={
                "report_type": {"type": "string", "required": True},
                "parameters": {"type": "object", "required": True},
            },
            output_schema={
                "report_id": "string",
                "file_url": "string",
            },
        ),

        # ==================== 供应链管理工具 ====================
        "scm.order.create": MCPTool(
            id="scm.order.create",
            name="创建采购订单",
            description="向供应商创建采购订单",
            server_id="scm",
            category="supply_chain",
            input_schema={
                "supplier_id": {"type": "string", "required": True},
                "items": {"type": "array", "required": True},
                "delivery_date": {"type": "date", "required": True},
            },
            output_schema={
                "order_id": "string",
                "estimated_delivery": "date",
            },
        ),
        "scm.demand.forecast": MCPTool(
            id="scm.demand.forecast",
            name="需求预测",
            description="预测新品上市后的需求量",
            server_id="scm",
            category="analytics",
            input_schema={
                "product_category": {"type": "string", "required": True},
                "forecast_days": {"type": "integer", "required": True},
            },
            output_schema={
                "daily_forecast": "array",
                "total_forecast": "number",
                "confidence": "number",
            },
        ),
    }

    def __init__(self):
        self.tools = {k: v.model_copy() for k, v in self.TOOLS.items()}

    def get_tool(self, tool_id: str) -> Optional[MCPTool]:
        """获取工具定义"""
        return self.tools.get(tool_id)

    def get_all_tools(self) -> list[MCPTool]:
        """获取所有工具"""
        return list(self.tools.values())

    def get_tools_by_server(self, server_id: str) -> list[MCPTool]:
        """获取指定服务器的工具"""
        return [t for t in self.tools.values() if t.server_id == server_id]

    def get_tools_by_category(self, category: str) -> list[MCPTool]:
        """获取指定分类的工具"""
        return [t for t in self.tools.values() if t.category == category]

    def search_tools(self, keyword: str) -> list[MCPTool]:
        """搜索工具"""
        keyword = keyword.lower()
        return [
            t for t in self.tools.values()
            if keyword in t.name.lower() or keyword in t.description.lower()
        ]
