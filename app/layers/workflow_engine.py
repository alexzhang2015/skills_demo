"""
Layer 3: Workflow 编排层 (流程引擎)

职责:
- 定义和管理工作流
- 编排多个 Skills 的执行顺序
- 处理并行执行、条件分支、循环重试
- 管理人工审批节点
"""

import uuid
import time
from datetime import datetime
from typing import Optional, TYPE_CHECKING

from ..models import (
    Workflow,
    WorkflowNode,
    WorkflowNodeType,
    WorkflowExecution,
    WorkflowNodeExecution,
    ExecutionStatus,
)

if TYPE_CHECKING:
    from .skill_executor import SkillExecutor


class WorkflowEngine:
    """工作流编排引擎"""

    def __init__(self, skill_executor: "SkillExecutor"):
        self.skill_executor = skill_executor
        self.workflows: dict[str, Workflow] = {}
        self.executions: dict[str, WorkflowExecution] = {}
        self._init_workflows()

    def _init_workflows(self):
        """初始化预定义工作流"""

        # 新品上市工作流
        product_launch_workflow = Workflow(
            id="product-launch-workflow",
            name="product-launch-workflow",
            display_name="新品上市流程",
            description="协调新产品从录入到上线的全流程",
            category="product",
            start_node="node-1",
            input_schema={
                "product_name": "str",
                "price": "float",
                "launch_date": "str",
                "region": "str",
            },
            nodes=[
                WorkflowNode(
                    node_id="node-1",
                    name="创建SKU",
                    node_type=WorkflowNodeType.SKILL,
                    description="在库存系统创建商品SKU",
                    skill_id="create-sku",
                    next_node="node-2",
                ),
                WorkflowNode(
                    node_id="node-2",
                    name="配置POS",
                    node_type=WorkflowNodeType.SKILL,
                    description="配置POS系统菜单项",
                    skill_id="config-pos-item",
                    next_node="node-3",
                ),
                WorkflowNode(
                    node_id="node-3",
                    name="同步App",
                    node_type=WorkflowNodeType.SKILL,
                    description="同步商品到App",
                    skill_id="sync-app-product",
                    next_node="node-4",
                ),
                WorkflowNode(
                    node_id="node-4",
                    name="更新菜单屏",
                    node_type=WorkflowNodeType.SKILL,
                    description="推送到门店菜单屏",
                    skill_id="update-menu-board",
                    next_node="node-5",
                ),
                WorkflowNode(
                    node_id="node-5",
                    name="创建培训任务",
                    node_type=WorkflowNodeType.SKILL,
                    description="为门店员工创建培训任务",
                    skill_id="create-training-task",
                    next_node="node-6",
                ),
                WorkflowNode(
                    node_id="node-6",
                    name="上市审批",
                    node_type=WorkflowNodeType.APPROVAL,
                    description="运营总监审批新品上市",
                    approval_roles=["运营总监"],
                    next_node="node-7",
                ),
                WorkflowNode(
                    node_id="node-7",
                    name="发送通知",
                    node_type=WorkflowNodeType.SKILL,
                    description="通知相关人员新品已上线",
                    skill_id="send-notification",
                    next_node=None,
                ),
            ],
        )

        # 价格调整工作流
        price_adjust_workflow = Workflow(
            id="price-adjust-workflow",
            name="price-adjust-workflow",
            display_name="价格调整流程",
            description="批量调整区域产品价格",
            category="pricing",
            start_node="node-1",
            input_schema={
                "product_id": "str",
                "region": "str",
                "adjustment_percent": "float",
            },
            nodes=[
                WorkflowNode(
                    node_id="node-1",
                    name="计算价格",
                    node_type=WorkflowNodeType.SKILL,
                    description="调用定价引擎计算最优价格",
                    skill_id="calculate-price",
                    next_node="node-2",
                ),
                WorkflowNode(
                    node_id="node-2",
                    name="价格审批",
                    node_type=WorkflowNodeType.APPROVAL,
                    description="财务总监审批价格变更",
                    approval_roles=["财务总监", "区域总监"],
                    next_node="node-3",
                ),
                WorkflowNode(
                    node_id="node-3",
                    name="更新POS价格",
                    node_type=WorkflowNodeType.SKILL,
                    description="批量更新POS系统价格表",
                    skill_id="update-pos-price",
                    next_node="node-4",
                ),
                WorkflowNode(
                    node_id="node-4",
                    name="同步App价格",
                    node_type=WorkflowNodeType.SKILL,
                    description="同步价格到App端",
                    skill_id="sync-app-price",
                    next_node="node-5",
                ),
                WorkflowNode(
                    node_id="node-5",
                    name="更新菜单屏",
                    node_type=WorkflowNodeType.SKILL,
                    description="更新菜单屏价格显示",
                    skill_id="update-menu-board",
                    next_node="node-6",
                ),
                WorkflowNode(
                    node_id="node-6",
                    name="发送通知",
                    node_type=WorkflowNodeType.SKILL,
                    description="通知区域经理价格已调整",
                    skill_id="send-notification",
                    next_node=None,
                ),
            ],
        )

        # 营销活动工作流
        campaign_workflow = Workflow(
            id="campaign-setup-workflow",
            name="campaign-setup-workflow",
            display_name="营销活动配置流程",
            description="跨渠道配置促销活动",
            category="marketing",
            start_node="node-1",
            input_schema={
                "campaign_type": "str",
                "discount_rules": "dict",
                "start_date": "str",
                "end_date": "str",
            },
            nodes=[
                WorkflowNode(
                    node_id="node-1",
                    name="创建活动",
                    node_type=WorkflowNodeType.SKILL,
                    description="在营销平台创建活动",
                    skill_id="create-campaign",
                    next_node="node-2",
                ),
                WorkflowNode(
                    node_id="node-2",
                    name="配置POS折扣",
                    node_type=WorkflowNodeType.SKILL,
                    description="配置POS折扣规则",
                    skill_id="config-pos-discount",
                    next_node="node-3",
                ),
                WorkflowNode(
                    node_id="node-3",
                    name="同步App活动",
                    node_type=WorkflowNodeType.SKILL,
                    description="同步活动到App",
                    skill_id="sync-app-product",
                    next_node="node-4",
                ),
                WorkflowNode(
                    node_id="node-4",
                    name="配置会员积分",
                    node_type=WorkflowNodeType.SKILL,
                    description="设置会员积分规则",
                    skill_id="setup-member-points",
                    next_node="node-5",
                ),
                WorkflowNode(
                    node_id="node-5",
                    name="发送通知",
                    node_type=WorkflowNodeType.SKILL,
                    description="通知门店活动即将开始",
                    skill_id="send-notification",
                    next_node=None,
                ),
            ],
        )

        # 运营报告工作流
        report_workflow = Workflow(
            id="report-gen-workflow",
            name="report-gen-workflow",
            display_name="运营报告生成流程",
            description="汇总多源数据生成分析报告",
            category="report",
            start_node="node-1",
            input_schema={
                "report_type": "str",
                "date_range": "dict",
                "region": "str",
            },
            nodes=[
                WorkflowNode(
                    node_id="node-1",
                    name="获取销售数据",
                    node_type=WorkflowNodeType.SKILL,
                    description="从POS系统提取销售数据",
                    skill_id="fetch-sales-data",
                    next_node="node-2",
                ),
                WorkflowNode(
                    node_id="node-2",
                    name="生成报告",
                    node_type=WorkflowNodeType.SKILL,
                    description="生成分析报告",
                    skill_id="generate-report",
                    next_node="node-3",
                ),
                WorkflowNode(
                    node_id="node-3",
                    name="发送报告",
                    node_type=WorkflowNodeType.SKILL,
                    description="发送报告给相关人员",
                    skill_id="send-notification",
                    next_node=None,
                ),
            ],
        )

        # 注册工作流
        for wf in [product_launch_workflow, price_adjust_workflow, campaign_workflow, report_workflow]:
            self.workflows[wf.id] = wf

    def get_workflow(self, workflow_id: str) -> Optional[Workflow]:
        return self.workflows.get(workflow_id)

    def get_all_workflows(self) -> list[Workflow]:
        return list(self.workflows.values())

    def get_workflows_by_category(self, category: str) -> list[Workflow]:
        return [w for w in self.workflows.values() if w.category == category]

    def execute(self, workflow_id: str, params: dict = {}) -> WorkflowExecution:
        """执行工作流"""
        workflow = self.get_workflow(workflow_id)
        if not workflow:
            return WorkflowExecution(
                execution_id=str(uuid.uuid4())[:8],
                workflow_id=workflow_id,
                workflow_name="unknown",
                status=ExecutionStatus.ERROR,
                error=f"Workflow '{workflow_id}' not found",
            )

        execution_id = str(uuid.uuid4())[:8]
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=workflow.id,
            workflow_name=workflow.display_name,
            status=ExecutionStatus.RUNNING,
            input_params=params,
            context=params.copy(),
            started_at=datetime.now(),
        )

        try:
            # 从起始节点开始执行
            current_node_id = workflow.start_node

            while current_node_id:
                node = self._get_node(workflow, current_node_id)
                if not node:
                    break

                execution.current_node = current_node_id

                # 执行节点
                node_execution = self._execute_node(node, execution.context)
                execution.node_executions.append(node_execution)

                # 检查是否需要等待审批
                if node.node_type == WorkflowNodeType.APPROVAL and node_execution.status == ExecutionStatus.AWAITING_APPROVAL:
                    execution.status = ExecutionStatus.AWAITING_APPROVAL
                    execution.pending_approval = current_node_id
                    self.executions[execution_id] = execution
                    return execution

                # 检查执行结果
                if node_execution.status == ExecutionStatus.ERROR:
                    if node.on_error:
                        current_node_id = node.on_error
                    else:
                        raise Exception(node_execution.error or "Node execution failed")
                else:
                    # 更新上下文
                    execution.context.update(node_execution.output_data)
                    current_node_id = node.next_node

            # 执行完成
            execution.status = ExecutionStatus.SUCCESS
            execution.output_result = execution.context

        except Exception as e:
            execution.status = ExecutionStatus.ERROR
            execution.error = str(e)

        execution.completed_at = datetime.now()
        execution.total_duration_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000

        self.executions[execution_id] = execution
        return execution

    def _get_node(self, workflow: Workflow, node_id: str) -> Optional[WorkflowNode]:
        for node in workflow.nodes:
            if node.node_id == node_id:
                return node
        return None

    def _execute_node(self, node: WorkflowNode, context: dict) -> WorkflowNodeExecution:
        """执行单个工作流节点"""
        node_execution = WorkflowNodeExecution(
            node_id=node.node_id,
            node_name=node.name,
            node_type=node.node_type,
            status=ExecutionStatus.RUNNING,
            input_data=context.copy(),
            started_at=datetime.now(),
        )

        try:
            if node.node_type == WorkflowNodeType.SKILL:
                # 执行技能
                skill_execution = self.skill_executor.execute(
                    node.skill_id,
                    {**context, **node.skill_params}
                )
                node_execution.skill_execution = skill_execution
                node_execution.output_data = skill_execution.output_result or {}
                node_execution.status = skill_execution.status

            elif node.node_type == WorkflowNodeType.APPROVAL:
                # 审批节点 - 返回等待状态
                node_execution.status = ExecutionStatus.AWAITING_APPROVAL
                node_execution.output_data = {
                    "approval_required": True,
                    "approval_roles": node.approval_roles,
                }

            elif node.node_type == WorkflowNodeType.PARALLEL:
                # TODO: 实现并行执行
                node_execution.status = ExecutionStatus.SUCCESS

            elif node.node_type == WorkflowNodeType.CONDITION:
                # TODO: 实现条件分支
                node_execution.status = ExecutionStatus.SUCCESS

            elif node.node_type == WorkflowNodeType.WAIT:
                # TODO: 实现等待
                time.sleep(0.1)
                node_execution.status = ExecutionStatus.SUCCESS

        except Exception as e:
            node_execution.status = ExecutionStatus.ERROR
            node_execution.error = str(e)

        node_execution.completed_at = datetime.now()
        node_execution.duration_ms = (node_execution.completed_at - node_execution.started_at).total_seconds() * 1000

        return node_execution

    def approve_execution(self, execution_id: str, approved: bool, approved_by: str = "运营总监") -> Optional[WorkflowExecution]:
        """审批工作流"""
        execution = self.executions.get(execution_id)
        if not execution or execution.status != ExecutionStatus.AWAITING_APPROVAL:
            return None

        execution.approved_by = approved_by

        if approved:
            # 继续执行后续节点
            workflow = self.get_workflow(execution.workflow_id)
            if workflow and execution.pending_approval:
                # 找到审批节点的下一个节点
                approval_node = self._get_node(workflow, execution.pending_approval)
                if approval_node:
                    # 更新审批节点状态
                    for node_exec in execution.node_executions:
                        if node_exec.node_id == execution.pending_approval:
                            node_exec.status = ExecutionStatus.APPROVED
                            node_exec.output_data["approved_by"] = approved_by
                            break

                    # 继续执行
                    current_node_id = approval_node.next_node
                    execution.pending_approval = None

                    while current_node_id:
                        node = self._get_node(workflow, current_node_id)
                        if not node:
                            break

                        execution.current_node = current_node_id
                        node_execution = self._execute_node(node, execution.context)
                        execution.node_executions.append(node_execution)

                        if node_execution.status == ExecutionStatus.AWAITING_APPROVAL:
                            execution.status = ExecutionStatus.AWAITING_APPROVAL
                            execution.pending_approval = current_node_id
                            return execution

                        execution.context.update(node_execution.output_data)
                        current_node_id = node.next_node

            execution.status = ExecutionStatus.SUCCESS
            execution.output_result = execution.context
        else:
            execution.status = ExecutionStatus.REJECTED

        execution.completed_at = datetime.now()
        execution.total_duration_ms = (execution.completed_at - execution.started_at).total_seconds() * 1000

        return execution

    def get_execution(self, execution_id: str) -> Optional[WorkflowExecution]:
        return self.executions.get(execution_id)

    def get_all_executions(self) -> list[WorkflowExecution]:
        return list(self.executions.values())
