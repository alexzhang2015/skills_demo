"""
Layer 2: 子场景 Agent 层 (领域专家)

职责:
- 按业务领域划分的专家Agent
- 理解领域特定的业务逻辑
- 选择和编排该领域的工作流
- 向Master Agent汇报执行结果
"""

import uuid
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from ..models import (
    SubAgent,
    SubAgentCapability,
    SubAgentTask,
    ExecutionStatus,
    WorkflowExecution,
)

if TYPE_CHECKING:
    from .workflow_engine import WorkflowEngine


class SubAgentManager:
    """子场景Agent管理器"""

    def __init__(self, workflow_engine: "WorkflowEngine"):
        self.workflow_engine = workflow_engine
        self.agents: dict[str, SubAgent] = {}
        self.tasks: dict[str, SubAgentTask] = {}
        self._init_sub_agents()

    def _init_sub_agents(self):
        """初始化子场景Agent"""

        # 产品管理Agent
        product_agent = SubAgent(
            id="product-agent",
            name="product-agent",
            display_name="产品管理Agent",
            description="负责产品全生命周期管理，包括新品上市、菜单配置、产品下架等",
            icon="📦",
            color="#3b82f6",
            domain="product",
            capabilities=[
                SubAgentCapability(
                    name="新品上市",
                    description="协调新产品从录入到上线的全流程",
                    keywords=["上市", "新品", "发布", "推出", "首发", "上线"],
                    workflows=["product-launch-workflow"],
                ),
                SubAgentCapability(
                    name="菜单配置",
                    description="管理菜单项的新增、修改和同步",
                    keywords=["菜单", "菜品", "新增", "添加", "配置"],
                    workflows=["product-launch-workflow"],
                ),
                SubAgentCapability(
                    name="产品下架",
                    description="处理产品的停售和下架流程",
                    keywords=["下架", "停售", "删除", "移除"],
                    workflows=[],
                ),
            ],
            available_workflows=["product-launch-workflow"],
            available_skills=["create-sku", "config-pos-item", "sync-app-product", "update-menu-board"],
            can_delegate_to=["pricing-agent", "marketing-agent"],
            system_prompt="""你是产品管理专家Agent，负责:
1. 管理产品从立项到下架的全生命周期
2. 协调POS、App、菜单屏等多系统的产品数据同步
3. 确保新品上市流程的合规性和完整性
4. 与定价Agent、营销Agent协作完成复杂任务""",
        )

        # 定价管理Agent
        pricing_agent = SubAgent(
            id="pricing-agent",
            name="pricing-agent",
            display_name="定价管理Agent",
            description="负责产品定价策略，包括价格计算、区域调价、竞品分析等",
            icon="💰",
            color="#22c55e",
            domain="pricing",
            capabilities=[
                SubAgentCapability(
                    name="价格调整",
                    description="批量调整区域产品价格",
                    keywords=["涨价", "降价", "调价", "价格", "定价"],
                    workflows=["price-adjust-workflow"],
                ),
                SubAgentCapability(
                    name="价格策略",
                    description="制定和优化定价策略",
                    keywords=["策略", "定价模型", "弹性"],
                    workflows=["price-adjust-workflow"],
                ),
            ],
            available_workflows=["price-adjust-workflow"],
            available_skills=["calculate-price", "update-pos-price", "sync-app-price"],
            requires_approval_from=["财务总监", "区域总监"],
            system_prompt="""你是定价管理专家Agent，负责:
1. 基于成本、竞争、需求弹性制定价格策略
2. 执行区域价格调整，确保价格一致性
3. 监控价格变动对销量的影响
4. 价格变更需要财务审批""",
        )

        # 营销活动Agent
        marketing_agent = SubAgent(
            id="marketing-agent",
            name="marketing-agent",
            display_name="营销活动Agent",
            description="负责营销活动的策划和执行，包括促销、会员运营、活动分析等",
            icon="🎯",
            color="#ec4899",
            domain="marketing",
            capabilities=[
                SubAgentCapability(
                    name="活动配置",
                    description="跨渠道配置促销活动",
                    keywords=["活动", "促销", "满减", "优惠", "打折", "折扣"],
                    workflows=["campaign-setup-workflow"],
                ),
                SubAgentCapability(
                    name="会员运营",
                    description="会员积分和权益管理",
                    keywords=["会员", "积分", "权益", "等级"],
                    workflows=["campaign-setup-workflow"],
                ),
            ],
            available_workflows=["campaign-setup-workflow"],
            available_skills=["create-campaign", "config-pos-discount", "setup-member-points"],
            system_prompt="""你是营销活动专家Agent，负责:
1. 策划和执行各类促销活动
2. 配置多渠道活动规则(POS、App、小程序)
3. 管理会员积分和权益体系
4. 分析活动效果并优化""",
        )

        # 供应链Agent
        supply_chain_agent = SubAgent(
            id="supply-chain-agent",
            name="supply-chain-agent",
            display_name="供应链Agent",
            description="负责库存管理、原料采购、物流配送等供应链运营",
            icon="🚚",
            color="#f59e0b",
            domain="supply_chain",
            capabilities=[
                SubAgentCapability(
                    name="库存管理",
                    description="监控和优化库存水平",
                    keywords=["库存", "备货", "盘点"],
                    workflows=[],
                ),
                SubAgentCapability(
                    name="原料采购",
                    description="管理原料采购和供应商",
                    keywords=["采购", "原料", "供应商"],
                    workflows=[],
                ),
            ],
            available_workflows=[],
            available_skills=["create-sku"],
            system_prompt="""你是供应链专家Agent，负责:
1. 监控库存水平，预防缺货和积压
2. 优化采购计划和供应商管理
3. 协调物流配送，确保准时送达
4. 支持新品上市的物料准备""",
        )

        # 数据分析Agent
        analytics_agent = SubAgent(
            id="analytics-agent",
            name="analytics-agent",
            display_name="数据分析Agent",
            description="负责运营数据分析和报告生成",
            icon="📊",
            color="#8b5cf6",
            domain="analytics",
            capabilities=[
                SubAgentCapability(
                    name="报告生成",
                    description="自动生成各类运营报告",
                    keywords=["报告", "报表", "周报", "月报", "分析"],
                    workflows=["report-gen-workflow"],
                ),
                SubAgentCapability(
                    name="数据洞察",
                    description="发现业务趋势和异常",
                    keywords=["洞察", "趋势", "异常", "分析"],
                    workflows=["report-gen-workflow"],
                ),
            ],
            available_workflows=["report-gen-workflow"],
            available_skills=["fetch-sales-data", "generate-report"],
            system_prompt="""你是数据分析专家Agent，负责:
1. 从多个业务系统汇总数据
2. 生成日报、周报、月报等运营报告
3. 发现业务趋势和异常信号
4. 为决策提供数据支持""",
        )

        # 注册所有Agent
        for agent in [product_agent, pricing_agent, marketing_agent, supply_chain_agent, analytics_agent]:
            self.agents[agent.id] = agent

    def get_agent(self, agent_id: str) -> Optional[SubAgent]:
        return self.agents.get(agent_id)

    def get_all_agents(self) -> list[SubAgent]:
        return list(self.agents.values())

    def get_agent_by_domain(self, domain: str) -> Optional[SubAgent]:
        for agent in self.agents.values():
            if agent.domain == domain:
                return agent
        return None

    def match_agent_for_intent(self, intent: str, entities: dict = {}) -> list[SubAgent]:
        """根据意图匹配合适的Agent"""
        matched_agents = []
        intent_lower = intent.lower()

        for agent in self.agents.values():
            for capability in agent.capabilities:
                if any(kw in intent_lower for kw in capability.keywords):
                    if agent not in matched_agents:
                        matched_agents.append(agent)
                    break

        return matched_agents

    def create_task(self, agent_id: str, instruction: str, context: dict = {}) -> SubAgentTask:
        """为子Agent创建任务"""
        agent = self.get_agent(agent_id)
        if not agent:
            return SubAgentTask(
                task_id=str(uuid.uuid4())[:8],
                agent_id=agent_id,
                agent_name="unknown",
                instruction=instruction,
                status=ExecutionStatus.ERROR,
                error=f"Agent '{agent_id}' not found",
            )

        task = SubAgentTask(
            task_id=str(uuid.uuid4())[:8],
            agent_id=agent.id,
            agent_name=agent.display_name,
            instruction=instruction,
            context=context,
            status=ExecutionStatus.PENDING,
            started_at=datetime.now(),
        )

        # 分析指令，确定需要执行的工作流
        task.planned_workflows = self._plan_workflows(agent, instruction, context)

        self.tasks[task.task_id] = task
        return task

    def execute_task(self, task_id: str) -> SubAgentTask:
        """执行子Agent任务"""
        task = self.tasks.get(task_id)
        if not task:
            return SubAgentTask(
                task_id=task_id,
                agent_id="unknown",
                agent_name="unknown",
                instruction="",
                status=ExecutionStatus.ERROR,
                error=f"Task '{task_id}' not found",
            )

        task.status = ExecutionStatus.RUNNING

        try:
            # 执行计划的工作流
            for workflow_id in task.planned_workflows:
                workflow_execution = self.workflow_engine.execute(workflow_id, task.context)
                task.workflow_executions.append(workflow_execution)

                # 如果工作流需要审批，任务暂停
                if workflow_execution.status == ExecutionStatus.AWAITING_APPROVAL:
                    task.status = ExecutionStatus.AWAITING_APPROVAL
                    return task

                # 更新上下文
                if workflow_execution.output_result:
                    task.context.update(workflow_execution.output_result)

            # 所有工作流执行完成
            task.status = ExecutionStatus.SUCCESS
            task.result = {
                "workflows_executed": len(task.workflow_executions),
                "context": task.context,
            }

        except Exception as e:
            task.status = ExecutionStatus.ERROR
            task.error = str(e)

        task.completed_at = datetime.now()
        return task

    def _plan_workflows(self, agent: SubAgent, instruction: str, context: dict) -> list[str]:
        """根据指令规划需要执行的工作流"""
        planned = []
        instruction_lower = instruction.lower()

        for capability in agent.capabilities:
            if any(kw in instruction_lower for kw in capability.keywords):
                planned.extend(capability.workflows)

        # 去重
        return list(dict.fromkeys(planned))

    def approve_task(self, task_id: str, approved: bool, approved_by: str = "运营总监") -> Optional[SubAgentTask]:
        """审批子Agent任务"""
        task = self.tasks.get(task_id)
        if not task or task.status != ExecutionStatus.AWAITING_APPROVAL:
            return None

        # 找到等待审批的工作流并审批
        for workflow_exec in task.workflow_executions:
            if workflow_exec.status == ExecutionStatus.AWAITING_APPROVAL:
                self.workflow_engine.approve_execution(
                    workflow_exec.execution_id,
                    approved,
                    approved_by
                )

        if approved:
            # 继续执行
            return self.execute_task(task_id)
        else:
            task.status = ExecutionStatus.REJECTED
            task.completed_at = datetime.now()
            return task

    def get_task(self, task_id: str) -> Optional[SubAgentTask]:
        return self.tasks.get(task_id)

    def get_all_tasks(self) -> list[SubAgentTask]:
        return list(self.tasks.values())
