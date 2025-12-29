"""
MCP Server 定义

定义所有核心业务系统的MCP服务器配置
"""

from typing import Optional
from pydantic import BaseModel
from enum import Enum


class MCPServerStatus(str, Enum):
    """MCP服务器状态"""
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    CONNECTING = "connecting"


class MCPServer(BaseModel):
    """MCP服务器定义"""
    id: str
    name: str
    description: str
    endpoint: str
    version: str = "1.0.0"
    status: MCPServerStatus = MCPServerStatus.DISCONNECTED
    capabilities: list[str] = []
    auth_type: str = "bearer"  # bearer, api_key, oauth2
    rate_limit: int = 1000  # requests per minute
    timeout_ms: int = 30000
    retry_count: int = 3

    # 元数据
    icon: str = ""
    color: str = "#6b7280"
    category: str = "general"


class MCPServerRegistry:
    """MCP服务器注册表"""

    # 核心业务系统定义
    SERVERS = {
        "pos": MCPServer(
            id="pos",
            name="POS系统",
            description="门店收银系统 - 管理商品、价格、订单",
            endpoint="mcp://pos.internal.example.com",
            version="3.2.1",
            capabilities=[
                "product.create", "product.update", "product.delete",
                "price.set", "price.batch_update",
                "order.query", "order.refund",
                "store.sync", "store.status",
                "menu.config", "menu.layout",
            ],
            icon="🏪",
            color="#ef4444",
            category="operations",
        ),

        "app": MCPServer(
            id="app",
            name="App后台",
            description="移动应用后台 - 用户端App和骑手端App",
            endpoint="mcp://app.internal.example.com",
            version="5.1.0",
            capabilities=[
                "product.sync", "product.visibility",
                "price.sync", "price.cache_clear",
                "notification.send", "notification.batch",
                "user.query", "user.segment",
                "order.status", "order.track",
                "content.update", "content.publish",
            ],
            icon="📱",
            color="#3b82f6",
            category="digital",
        ),

        "inventory": MCPServer(
            id="inventory",
            name="库存系统",
            description="原料和成品库存管理",
            endpoint="mcp://inventory.internal.example.com",
            version="2.5.0",
            capabilities=[
                "sku.create", "sku.update", "sku.archive",
                "bom.create", "bom.update",  # Bill of Materials
                "stock.query", "stock.adjust",
                "purchase.request", "purchase.approve",
                "supplier.manage",
                "batch.track", "expiry.alert",
            ],
            icon="📦",
            color="#f59e0b",
            category="supply_chain",
        ),

        "pricing": MCPServer(
            id="pricing",
            name="定价引擎",
            description="智能定价策略引擎",
            endpoint="mcp://pricing.internal.example.com",
            version="2.0.0",
            capabilities=[
                "price.calculate", "price.optimize",
                "elasticity.analyze", "elasticity.predict",
                "competitor.monitor", "competitor.compare",
                "margin.calculate", "margin.simulate",
                "promotion.price", "promotion.bundle",
                "region.adjust", "region.strategy",
            ],
            icon="💰",
            color="#8b5cf6",
            category="analytics",
        ),

        "crm": MCPServer(
            id="crm",
            name="会员系统",
            description="客户关系管理和会员运营",
            endpoint="mcp://crm.internal.example.com",
            version="4.0.0",
            capabilities=[
                "member.query", "member.segment",
                "points.add", "points.deduct", "points.rules",
                "coupon.create", "coupon.issue", "coupon.validate",
                "tier.upgrade", "tier.benefits",
                "campaign.target", "campaign.track",
                "loyalty.analyze",
            ],
            icon="👥",
            color="#ec4899",
            category="marketing",
        ),

        "marketing": MCPServer(
            id="marketing",
            name="营销平台",
            description="活动和促销管理平台",
            endpoint="mcp://marketing.internal.example.com",
            version="3.5.0",
            capabilities=[
                "campaign.create", "campaign.update", "campaign.pause",
                "discount.config", "discount.rules",
                "banner.create", "banner.schedule",
                "push.send", "push.segment",
                "analytics.campaign", "analytics.roi",
                "ab_test.create", "ab_test.analyze",
            ],
            icon="📢",
            color="#06b6d4",
            category="marketing",
        ),

        "menu_board": MCPServer(
            id="menu_board",
            name="菜单屏CMS",
            description="店内数字菜单屏内容管理",
            endpoint="mcp://menuboard.internal.example.com",
            version="1.8.0",
            capabilities=[
                "content.update", "content.schedule",
                "layout.set", "layout.template",
                "media.upload", "media.manage",
                "device.status", "device.reboot",
                "sync.trigger", "sync.status",
            ],
            icon="🖥️",
            color="#22c55e",
            category="operations",
        ),

        "training": MCPServer(
            id="training",
            name="培训系统",
            description="员工培训和认证平台",
            endpoint="mcp://training.internal.example.com",
            version="2.2.0",
            capabilities=[
                "course.create", "course.assign",
                "task.create", "task.track",
                "quiz.create", "quiz.grade",
                "cert.issue", "cert.verify",
                "progress.query", "progress.report",
            ],
            icon="📚",
            color="#84cc16",
            category="hr",
        ),

        "analytics": MCPServer(
            id="analytics",
            name="数据分析平台",
            description="BI和数据分析服务",
            endpoint="mcp://analytics.internal.example.com",
            version="4.1.0",
            capabilities=[
                "query.execute", "query.schedule",
                "report.generate", "report.export",
                "dashboard.create", "dashboard.share",
                "metric.calculate", "metric.alert",
                "forecast.run", "forecast.accuracy",
                "insight.generate",
            ],
            icon="📊",
            color="#6366f1",
            category="analytics",
        ),

        "scm": MCPServer(
            id="scm",
            name="供应链管理",
            description="供应链协同和物流管理",
            endpoint="mcp://scm.internal.example.com",
            version="2.8.0",
            capabilities=[
                "order.create", "order.track",
                "shipment.schedule", "shipment.status",
                "warehouse.query", "warehouse.transfer",
                "supplier.order", "supplier.payment",
                "forecast.demand", "forecast.supply",
            ],
            icon="🚛",
            color="#14b8a6",
            category="supply_chain",
        ),
    }

    def __init__(self):
        self.servers = {k: v.model_copy() for k, v in self.SERVERS.items()}
        self._connection_status = {}

    def get_server(self, server_id: str) -> Optional[MCPServer]:
        """获取服务器配置"""
        return self.servers.get(server_id)

    def get_all_servers(self) -> list[MCPServer]:
        """获取所有服务器"""
        return list(self.servers.values())

    def get_servers_by_category(self, category: str) -> list[MCPServer]:
        """按分类获取服务器"""
        return [s for s in self.servers.values() if s.category == category]

    def get_server_capabilities(self, server_id: str) -> list[str]:
        """获取服务器能力列表"""
        server = self.get_server(server_id)
        return server.capabilities if server else []

    def connect(self, server_id: str) -> bool:
        """连接服务器（模拟）"""
        server = self.get_server(server_id)
        if server:
            server.status = MCPServerStatus.CONNECTED
            return True
        return False

    def disconnect(self, server_id: str) -> bool:
        """断开服务器（模拟）"""
        server = self.get_server(server_id)
        if server:
            server.status = MCPServerStatus.DISCONNECTED
            return True
        return False

    def get_status(self) -> dict:
        """获取所有服务器状态"""
        return {
            server_id: {
                "name": server.name,
                "status": server.status.value,
                "capabilities_count": len(server.capabilities),
            }
            for server_id, server in self.servers.items()
        }
