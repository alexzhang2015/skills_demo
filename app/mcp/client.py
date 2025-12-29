"""
MCP Client

MCP工具调用客户端，提供统一的工具执行接口
"""

import uuid
import time
import random
from datetime import datetime
from typing import Optional, Any

from .servers import MCPServerRegistry, MCPServerStatus
from .tools import MCPToolRegistry, MCPTool, MCPToolResult, MCPToolStatus


class MCPClient:
    """MCP客户端 - 统一的MCP工具调用接口"""

    def __init__(self):
        self.server_registry = MCPServerRegistry()
        self.tool_registry = MCPToolRegistry()
        self.execution_history: list[MCPToolResult] = []
        self._trace_id = None

    def start_trace(self) -> str:
        """开始追踪（用于关联一系列调用）"""
        self._trace_id = str(uuid.uuid4())[:12]
        return self._trace_id

    def end_trace(self):
        """结束追踪"""
        self._trace_id = None

    def call_tool(
        self,
        tool_id: str,
        params: dict = {},
        timeout_ms: Optional[int] = None,
    ) -> MCPToolResult:
        """
        调用MCP工具

        Args:
            tool_id: 工具ID (如 "pos.product.create")
            params: 输入参数
            timeout_ms: 超时时间（毫秒）

        Returns:
            MCPToolResult: 执行结果
        """
        tool = self.tool_registry.get_tool(tool_id)
        if not tool:
            return MCPToolResult(
                tool_id=tool_id,
                server_id="unknown",
                tool_name="unknown",
                status=MCPToolStatus.ERROR,
                error_message=f"Tool '{tool_id}' not found",
            )

        # 检查服务器状态
        server = self.server_registry.get_server(tool.server_id)
        if not server:
            return MCPToolResult(
                tool_id=tool_id,
                server_id=tool.server_id,
                tool_name=tool.name,
                status=MCPToolStatus.ERROR,
                error_message=f"Server '{tool.server_id}' not found",
            )

        # 模拟连接服务器
        if server.status != MCPServerStatus.CONNECTED:
            self.server_registry.connect(tool.server_id)

        # 创建执行记录
        result = MCPToolResult(
            tool_id=tool_id,
            server_id=tool.server_id,
            tool_name=tool.name,
            status=MCPToolStatus.RUNNING,
            input_params=params,
            started_at=datetime.now(),
            request_id=str(uuid.uuid4())[:8],
            trace_id=self._trace_id or "",
        )

        try:
            # 模拟网络延迟
            delay = random.uniform(0.01, 0.05)
            time.sleep(delay)

            # 模拟执行结果
            result.output_data = self._simulate_tool_execution(tool, params)
            result.status = MCPToolStatus.SUCCESS

        except Exception as e:
            result.status = MCPToolStatus.ERROR
            result.error_message = str(e)

        result.completed_at = datetime.now()
        result.duration_ms = (result.completed_at - result.started_at).total_seconds() * 1000

        # 记录执行历史
        self.execution_history.append(result)

        return result

    def _simulate_tool_execution(self, tool: MCPTool, params: dict) -> dict:
        """模拟工具执行返回结果"""
        tool_results = {
            # POS系统
            "pos.product.create": {
                "pos_item_id": f"POS-{uuid.uuid4().hex[:6].upper()}",
                "created_at": datetime.now().isoformat(),
                "sync_status": "synced",
                "affected_stores": 2847,
            },
            "pos.product.batch_update": {
                "updated_count": params.get("items", []) and len(params.get("items", [])) or 100,
                "failed_items": [],
            },
            "pos.price.update": {
                "affected_stores": 2847,
                "effective_time": "明日 06:00",
                "price_change": {
                    "old": params.get("old_price", 25.0),
                    "new": params.get("new_price", 28.0),
                },
            },
            "pos.discount.config": {
                "rule_id": f"RULE-{uuid.uuid4().hex[:6].upper()}",
                "store_count": 2847,
                "effective": True,
            },
            "pos.store.sync": {
                "synced_count": 2847,
                "pending_count": 0,
                "sync_time": datetime.now().isoformat(),
            },

            # App后台
            "app.product.sync": {
                "app_product_id": f"APP-{uuid.uuid4().hex[:6].upper()}",
                "cache_cleared": True,
                "cdn_refreshed": True,
            },
            "app.notification.send": {
                "sent_count": params.get("target_ids", []) and len(params.get("target_ids", [])) or 50000,
                "failed_count": 12,
                "notification_id": f"NOTIF-{uuid.uuid4().hex[:8].upper()}",
            },
            "app.price.sync": {
                "cache_cleared": True,
                "effective_at": datetime.now().isoformat(),
            },
            "app.content.publish": {
                "content_id": f"CONTENT-{uuid.uuid4().hex[:6].upper()}",
                "publish_status": "published",
            },

            # 库存系统
            "inventory.sku.create": {
                "sku_id": f"SKU-{uuid.uuid4().hex[:8].upper()}",
                "barcode": f"69{random.randint(10000000000, 99999999999)}",
                "created_at": datetime.now().isoformat(),
            },
            "inventory.bom.create": {
                "bom_id": f"BOM-{uuid.uuid4().hex[:6].upper()}",
                "material_count": len(params.get("materials", [])) or 5,
            },
            "inventory.stock.query": {
                "total_stock": random.randint(10000, 50000),
                "available_stock": random.randint(8000, 45000),
                "store_breakdown": [
                    {"region": "华东", "stock": random.randint(3000, 15000)},
                    {"region": "华南", "stock": random.randint(2000, 10000)},
                    {"region": "华北", "stock": random.randint(2000, 10000)},
                ],
            },
            "inventory.stock.reserve": {
                "reservation_id": f"RES-{uuid.uuid4().hex[:6].upper()}",
                "reserved_quantity": params.get("quantity", 10000),
            },

            # 定价引擎
            "pricing.calculate": {
                "suggested_price": round(params.get("cost", 10) * 2.5 * (1 + random.uniform(-0.1, 0.1)), 2),
                "margin": round(random.uniform(0.55, 0.65), 2),
                "elasticity": round(random.uniform(-0.5, -0.3), 2),
                "competitor_range": [21.0, 32.0],
            },
            "pricing.competitor.analyze": {
                "competitor_prices": [
                    {"brand": "品牌A", "price": 26.0},
                    {"brand": "品牌B", "price": 28.0},
                    {"brand": "品牌C", "price": 24.0},
                ],
                "avg_price": 26.0,
                "price_position": "中等偏上",
            },

            # CRM系统
            "crm.member.segment": {
                "segment_id": f"SEG-{uuid.uuid4().hex[:6].upper()}",
                "member_count": random.randint(100000, 500000),
            },
            "crm.points.config": {
                "rule_id": f"PTS-{uuid.uuid4().hex[:6].upper()}",
                "effective_from": datetime.now().isoformat(),
            },
            "crm.coupon.batch_issue": {
                "issued_count": random.randint(50000, 200000),
                "coupon_batch_id": f"COUPON-{uuid.uuid4().hex[:6].upper()}",
            },

            # 营销平台
            "marketing.campaign.create": {
                "campaign_id": f"CMP-{uuid.uuid4().hex[:8].upper()}",
                "status": "active",
                "estimated_reach": random.randint(100000, 500000),
            },
            "marketing.banner.schedule": {
                "banner_ids": [f"BNR-{uuid.uuid4().hex[:4].upper()}" for _ in range(3)],
                "schedule_status": "scheduled",
            },

            # 菜单屏CMS
            "menuboard.content.update": {
                "updated_stores": 2845,
                "failed_stores": ["SH-0234", "BJ-0891"],
            },
            "menuboard.sync.trigger": {
                "sync_job_id": f"SYNC-{uuid.uuid4().hex[:6].upper()}",
                "estimated_minutes": 15,
            },

            # 培训系统
            "training.task.create": {
                "task_id": f"TRAIN-{uuid.uuid4().hex[:6].upper()}",
                "target_count": random.randint(5000, 15000),
                "deadline": "7天后",
            },
            "training.progress.query": {
                "completed_count": random.randint(3000, 10000),
                "total_count": 12000,
                "completion_rate": round(random.uniform(0.6, 0.95), 2),
            },

            # 数据分析
            "analytics.sales.query": {
                "total_sales": round(random.uniform(1000000, 5000000), 2),
                "order_count": random.randint(50000, 200000),
                "data": [
                    {"date": "2025-01-01", "sales": 150000, "orders": 5000},
                    {"date": "2025-01-02", "sales": 160000, "orders": 5500},
                ],
            },
            "analytics.report.generate": {
                "report_id": f"RPT-{uuid.uuid4().hex[:6].upper()}",
                "file_url": f"/reports/report_{uuid.uuid4().hex[:8]}.pdf",
            },

            # 供应链管理
            "scm.order.create": {
                "order_id": f"PO-{uuid.uuid4().hex[:8].upper()}",
                "estimated_delivery": "3-5个工作日",
            },
            "scm.demand.forecast": {
                "daily_forecast": [1000, 1200, 1500, 1800, 2000, 1900, 1700],
                "total_forecast": 11100,
                "confidence": 0.85,
            },
        }

        # 返回对应工具的结果，或通用结果
        return tool_results.get(tool.id, {
            "success": True,
            "message": f"{tool.name} 执行成功",
            "timestamp": datetime.now().isoformat(),
        })

    def batch_call(self, calls: list[tuple[str, dict]]) -> list[MCPToolResult]:
        """批量调用工具"""
        results = []
        for tool_id, params in calls:
            result = self.call_tool(tool_id, params)
            results.append(result)
        return results

    def get_execution_history(
        self,
        trace_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[MCPToolResult]:
        """获取执行历史"""
        history = self.execution_history
        if trace_id:
            history = [r for r in history if r.trace_id == trace_id]
        return history[-limit:]

    def get_server_status(self) -> dict:
        """获取所有服务器状态"""
        return self.server_registry.get_status()

    def get_available_tools(self, server_id: Optional[str] = None) -> list[MCPTool]:
        """获取可用工具列表"""
        if server_id:
            return self.tool_registry.get_tools_by_server(server_id)
        return self.tool_registry.get_all_tools()


# 全局MCP客户端实例
mcp_client = MCPClient()
