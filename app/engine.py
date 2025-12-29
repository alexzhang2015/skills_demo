import uuid
from typing import Optional

from .models import (
    Skill,
    SkillCreate,
    SkillUpdate,
    ExecutionResult,
    SkillStatus,
)
from .registry import SkillRegistry
from .executor import SkillExecutor


class SkillsEngine:
    """
    总部运营Agent引擎

    技术架构:
    ┌─────────────────────────────────────────┐
    │     人类监督层 (Human Oversight)         │
    │  战略决策 | 异常干预 | 质量审计 | 创新探索  │
    └─────────────────────────────────────────┘
                        ↓
    ┌─────────────────────────────────────────┐
    │        Skill编排引擎 (本类)              │
    │  菜单配置 | 价格调整 | 上市协调 | 活动管理  │
    └─────────────────────────────────────────┘
                        ↓
    ┌─────────────────────────────────────────┐
    │       工具调用层 (MCP Tools)            │
    │  POS API | App CMS | 数据库 | 通知系统   │
    └─────────────────────────────────────────┘

    组件架构:
    - SkillRegistry: 技能注册与管理
    - SkillExecutor: 技能执行引擎
    - StepParser: 步骤解析器
    - SystemSimulator: 系统模拟器
    """

    def __init__(self):
        self.registry = SkillRegistry()
        self.executor = SkillExecutor()
        self._init_demo_skills()

    def _init_demo_skills(self):
        """初始化QSR运营场景的演示Skills"""
        demo_skills = [
            SkillCreate(
                name="menu-config",
                description="菜单配置同步 - 跨系统批量更新菜单项（POS、App、菜单屏）",
                category="menu",
                requires_approval=True,
                affected_systems=["POS", "APP", "MENU_BOARD", "INVENTORY"],
                prompt="""# 菜单配置同步 Skill

## 触发场景
当需要新增、修改或下架菜品时，自动同步到所有相关系统。

## 执行步骤
1. 解析菜单变更请求（新增/修改/下架）
2. 验证菜品信息完整性（名称、价格、图片、描述、原料）
3. 检查库存系统原料可用性
4. 更新POS系统菜单数据库
5. 同步App后台商品信息
6. 推送菜单屏CMS内容更新
7. 触发库存系统SKU关联
8. 生成变更报告并通知相关人员

## 输入参数
- action: add/update/remove
- item_name: 菜品名称
- price: 价格
- category: 分类
- regions: 适用区域

## 人工介入点
- 价格变动超过20%需要审批
- 新品上线需要营销确认""",
            ),
            SkillCreate(
                name="price-adjust",
                description="区域价格调整 - 批量更新指定区域的产品定价",
                category="pricing",
                requires_approval=True,
                affected_systems=["PRICING", "POS", "APP", "MENU_BOARD"],
                prompt="""# 区域价格调整 Skill

## 触发场景
根据成本变化、竞争分析或促销策略，批量调整特定区域的产品价格。

## 执行步骤
1. 解析价格调整请求（产品、区域、新价格）
2. 获取当前价格基线数据
3. 计算价格变动幅度和影响门店数
4. 调用定价引擎计算最优价格
5. 生成价格变更预览报告
6. 等待人工审批（如变动>10%）
7. 批量更新POS系统价格表
8. 同步App端价格显示
9. 更新菜单屏价格标签
10. 记录价格变更日志

## 输入参数
- product_ids: 产品ID列表
- regions: 区域代码
- adjustment_type: percentage/absolute
- adjustment_value: 调整值

## 风控规则
- 单次调整不超过30%
- 需要财务审批链确认""",
            ),
            SkillCreate(
                name="product-launch",
                description="新品上市协调 - 跨部门协调新产品发布流程",
                category="launch",
                requires_approval=True,
                affected_systems=["POS", "APP", "MENU_BOARD", "INVENTORY", "MARKETING", "TRAINING"],
                prompt="""# 新品上市协调 Skill

## 触发场景
R&D完成新品开发后，协调运营、营销、培训等多部门的上市准备工作。

## 执行步骤
1. 接收新品上市请求（产品信息、上市日期、目标区域）
2. 检查产品资料完整性（配方、成本、图片、营销文案）
3. 创建库存系统新SKU和BOM表
4. 配置POS系统新品按钮和价格
5. 上传App端商品详情页
6. 准备菜单屏宣传素材
7. 触发培训系统制作SOP视频
8. 协调营销平台推广计划
9. 设置会员系统新品优惠券
10. 生成上市检查清单并追踪完成度
11. 发送上市就绪通知

## 关键协调点
- R&D → 运营：配方和成本确认
- 运营 → 营销：定价和卖点确认
- 营销 → 培训：话术和促销规则

## 审批节点
- 成本审批（财务）
- 定价审批（销售总监）
- 上市日期确认（运营总监）""",
            ),
            SkillCreate(
                name="campaign-setup",
                description="营销活动配置 - 跨渠道设置促销活动规则",
                category="campaign",
                requires_approval=False,
                affected_systems=["MARKETING", "APP", "POS", "CRM"],
                prompt="""# 营销活动配置 Skill

## 触发场景
市场部门发起促销活动时，自动配置所有渠道的活动规则。

## 执行步骤
1. 解析活动配置请求（类型、时间、规则、预算）
2. 验证活动规则合法性（折扣上限、时间冲突）
3. 配置营销平台活动模板
4. 设置App端活动入口和页面
5. 更新POS系统折扣规则
6. 配置会员系统积分规则
7. 生成活动效果预测报告
8. 设置活动监控告警

## 支持的活动类型
- 满减活动
- 折扣活动
- 买赠活动
- 会员专享
- 新客优惠

## 自动化规则
- 活动冲突自动检测
- 预算超支自动暂停
- 效果不达标自动预警""",
            ),
            SkillCreate(
                name="store-audit",
                description="门店合规巡检 - AI驱动的门店标准检查",
                category="audit",
                requires_approval=False,
                affected_systems=["APP", "TRAINING"],
                prompt="""# 门店合规巡检 Skill

## 触发场景
定期或随机触发门店合规性检查，结合计算机视觉和数据分析。

## 执行步骤
1. 获取门店最新运营数据
2. 分析POS交易异常模式
3. 检查库存盘点差异
4. 审核员工培训完成度
5. 分析顾客评价关键词
6. 生成合规评分报告
7. 创建整改任务清单
8. 推送至门店经理App

## 检查维度
- 食品安全合规
- 服务标准执行
- 设备维护状态
- 员工培训达标
- 财务合规性

## 输出报告
- 综合评分
- 问题清单
- 整改建议
- 跟踪截止日期""",
            ),
            SkillCreate(
                name="report-gen",
                description="运营报告生成 - 自动汇总多源数据生成分析报告",
                category="report",
                requires_approval=False,
                affected_systems=["POS", "APP", "CRM", "INVENTORY"],
                prompt="""# 运营报告生成 Skill

## 触发场景
定期或按需生成各类运营分析报告。

## 执行步骤
1. 确定报告类型和时间范围
2. 从POS系统提取销售数据
3. 从App后台获取线上订单
4. 汇总会员系统消费行为
5. 分析库存周转率
6. 计算关键KPI指标
7. 生成数据可视化图表
8. 编写分析洞察摘要
9. 输出PDF/Excel报告

## 报告类型
- 日报/周报/月报
- 区域对比分析
- 品类销售分析
- 会员价值分析
- 异常预警报告

## 自动化特性
- 定时自动生成
- 异常自动高亮
- 同比环比自动计算""",
            ),
        ]
        for skill in demo_skills:
            self.create_skill(skill)

    # ==================== Skill CRUD (委托给 Registry) ====================

    def create_skill(self, skill_data: SkillCreate) -> Skill:
        """创建技能"""
        return self.registry.create(skill_data)

    def get_skill(self, skill_id: str) -> Optional[Skill]:
        """获取技能"""
        return self.registry.get(skill_id)

    def get_all_skills(self) -> list[Skill]:
        """获取所有技能"""
        return self.registry.get_all()

    def update_skill(self, skill_id: str, update_data: SkillUpdate) -> Optional[Skill]:
        """更新技能"""
        return self.registry.update(skill_id, update_data)

    def delete_skill(self, skill_id: str) -> bool:
        """删除技能"""
        return self.registry.delete(skill_id)

    # ==================== Skill Execution (委托给 Executor) ====================

    def execute_skill(self, skill_id: str, args: Optional[str] = None) -> ExecutionResult:
        """执行技能"""
        skill = self.get_skill(skill_id)
        if not skill:
            return ExecutionResult(
                execution_id=str(uuid.uuid4())[:8],
                skill_id=skill_id,
                skill_name="Unknown",
                status=SkillStatus.ERROR,
                error=f"Skill '{skill_id}' not found",
            )
        return self.executor.execute(skill, args)

    def approve_execution(
        self, execution_id: str, approved: bool, approved_by: str = "运营总监"
    ) -> Optional[ExecutionResult]:
        """审批执行结果"""
        return self.executor.approve(execution_id, approved, approved_by)

    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """获取执行结果"""
        return self.executor.get(execution_id)

    def get_all_executions(self) -> list[ExecutionResult]:
        """获取所有执行结果"""
        return self.executor.get_all()

    # ==================== 兼容性属性 ====================

    @property
    def skills(self) -> dict[str, Skill]:
        """兼容旧API: 直接访问skills字典"""
        return self.registry.skills

    @property
    def executions(self) -> dict[str, ExecutionResult]:
        """兼容旧API: 直接访问executions字典"""
        return self.executor.executions


# Global engine instance
engine = SkillsEngine()
