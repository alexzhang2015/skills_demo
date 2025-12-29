from pydantic import BaseModel, Field
from typing import Optional, Any, Literal
from datetime import datetime
from enum import Enum


class ExecutionStatus(str, Enum):
    """统一的执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# ============================================================
# Layer 4: MCP Tools & Atomic Skills (最底层)
# ============================================================

class MCPToolCall(BaseModel):
    """MCP工具调用记录"""
    tool_id: str
    system: str                          # 目标系统: POS, APP, INVENTORY等
    operation: str                       # 操作名称
    params: dict = {}                    # 调用参数
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[Any] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None


class AtomicSkill(BaseModel):
    """原子技能 - 单一职责的最小执行单元"""
    id: str
    name: str                            # 如: create-sku, sync-pos, send-notify
    description: str
    category: str                        # 所属领域
    input_schema: dict = {}              # 输入参数定义
    output_schema: dict = {}             # 输出参数定义
    target_systems: list[str] = []       # 调用的目标系统
    estimated_duration_ms: int = 1000    # 预估执行时间
    retry_config: dict = Field(default_factory=lambda: {"max_retries": 3, "backoff_ms": 1000})


class SkillExecution(BaseModel):
    """原子技能执行记录"""
    execution_id: str
    skill_id: str
    skill_name: str
    input_params: dict = {}
    output_result: Optional[Any] = None
    tool_calls: list[MCPToolCall] = []
    status: ExecutionStatus = ExecutionStatus.PENDING
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None
    trace_id: Optional[str] = None  # MCP调用追踪ID


# ============================================================
# Layer 3: Workflow 编排层
# ============================================================

class WorkflowNodeType(str, Enum):
    """工作流节点类型"""
    SKILL = "skill"              # 执行单个Skill
    PARALLEL = "parallel"        # 并行执行多个分支
    CONDITION = "condition"      # 条件分支
    APPROVAL = "approval"        # 人工审批节点
    WAIT = "wait"               # 等待/延迟节点
    SUB_WORKFLOW = "sub_workflow"  # 子工作流


class WorkflowNode(BaseModel):
    """工作流节点定义"""
    node_id: str
    name: str
    node_type: WorkflowNodeType
    description: str = ""

    # 技能执行配置 (node_type == SKILL)
    skill_id: Optional[str] = None
    skill_params: dict = {}

    # 并行执行配置 (node_type == PARALLEL)
    parallel_branches: list[list[str]] = []  # 并行分支的节点ID列表

    # 条件分支配置 (node_type == CONDITION)
    condition_expr: Optional[str] = None     # 条件表达式
    true_branch: Optional[str] = None        # 条件为真时的下一节点
    false_branch: Optional[str] = None       # 条件为假时的下一节点

    # 审批配置 (node_type == APPROVAL)
    approval_roles: list[str] = []           # 审批角色
    approval_timeout_hours: int = 24

    # 流转配置
    next_node: Optional[str] = None          # 下一个节点ID
    on_error: Optional[str] = None           # 错误时跳转的节点


class Workflow(BaseModel):
    """工作流定义"""
    id: str
    name: str                                # 如: product-launch-workflow
    display_name: str                        # 如: 新品上市流程
    description: str
    category: str                            # 所属子场景Agent
    version: str = "1.0.0"

    # 节点定义
    nodes: list[WorkflowNode] = []
    start_node: str                          # 起始节点ID

    # 输入输出
    input_schema: dict = {}
    output_schema: dict = {}

    # 元数据
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)
    created_by: str = "system"


class WorkflowNodeExecution(BaseModel):
    """工作流节点执行记录"""
    node_id: str
    node_name: str
    node_type: WorkflowNodeType
    status: ExecutionStatus = ExecutionStatus.PENDING
    input_data: dict = {}
    output_data: dict = {}
    skill_execution: Optional[SkillExecution] = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: Optional[float] = None


class WorkflowExecution(BaseModel):
    """工作流执行实例"""
    execution_id: str
    workflow_id: str
    workflow_name: str
    status: ExecutionStatus = ExecutionStatus.PENDING

    # 执行上下文
    input_params: dict = {}
    context: dict = {}                       # 执行过程中的变量
    output_result: Optional[dict] = None

    # 节点执行记录
    current_node: Optional[str] = None
    node_executions: list[WorkflowNodeExecution] = []

    # 审批信息
    pending_approval: Optional[str] = None   # 等待审批的节点ID
    approved_by: Optional[str] = None

    # 时间信息
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[float] = None

    # 错误处理
    error: Optional[str] = None
    retry_count: int = 0


# ============================================================
# Layer 2: 子场景 Agent 层
# ============================================================

class SubAgentCapability(BaseModel):
    """子Agent能力定义"""
    name: str
    description: str
    keywords: list[str] = []                 # 触发关键词
    workflows: list[str] = []                # 可执行的工作流ID列表


class SubAgent(BaseModel):
    """子场景Agent定义"""
    id: str
    name: str                                # 如: product-agent
    display_name: str                        # 如: 产品管理Agent
    description: str
    icon: str = "📦"
    color: str = "#3b82f6"

    # 能力定义
    domain: str                              # 领域: product, pricing, marketing, supply_chain
    capabilities: list[SubAgentCapability] = []

    # 可调用的资源
    available_workflows: list[str] = []
    available_skills: list[str] = []

    # 协作配置
    can_delegate_to: list[str] = []          # 可委托的其他Agent
    requires_approval_from: list[str] = []   # 需要哪些角色审批

    # 系统提示词
    system_prompt: str = ""

    created_at: datetime = Field(default_factory=datetime.now)


class SubAgentTask(BaseModel):
    """子Agent任务"""
    task_id: str
    agent_id: str
    agent_name: str

    # 任务内容
    instruction: str                         # 来自Master Agent的指令
    context: dict = {}                       # 上下文信息

    # 执行计划
    planned_workflows: list[str] = []
    workflow_executions: list[WorkflowExecution] = []

    # 状态
    status: ExecutionStatus = ExecutionStatus.PENDING
    result: Optional[dict] = None
    error: Optional[str] = None

    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None


# ============================================================
# Layer 1: Master Agent 层 (最顶层)
# ============================================================

class IntentAnalysis(BaseModel):
    """意图分析结果"""
    original_input: str
    intent_type: str                         # 如: product_launch, price_adjust
    confidence: float = 0.0
    entities: dict = {}                      # 提取的实体: {product: "川香麻辣鸡腿堡", date: "1月15日"}
    required_agents: list[str] = []          # 需要的子Agent
    suggested_workflows: list[str] = []      # 建议的工作流


class ExecutionPlan(BaseModel):
    """执行计划"""
    plan_id: str
    intent: IntentAnalysis

    # 任务分解
    agent_tasks: list[dict] = []             # [{agent_id, instruction, priority, dependencies}]

    # 执行顺序
    execution_order: list[list[str]] = []    # [[并行任务], [并行任务], ...]

    # 协调点
    sync_points: list[str] = []              # 需要同步的点
    approval_points: list[str] = []          # 需要审批的点

    created_at: datetime = Field(default_factory=datetime.now)


class MasterAgentSession(BaseModel):
    """Master Agent 会话"""
    session_id: str
    user_input: str

    # 处理过程
    intent_analysis: Optional[IntentAnalysis] = None
    execution_plan: Optional[ExecutionPlan] = None

    # 子Agent任务
    agent_tasks: list[SubAgentTask] = []

    # 汇总结果
    status: ExecutionStatus = ExecutionStatus.PENDING
    final_result: Optional[str] = None
    summary: Optional[str] = None

    # 审批状态
    pending_approvals: list[str] = []

    # 时间
    started_at: datetime = Field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    total_duration_ms: Optional[float] = None


# ============================================================
# API Request/Response Models
# ============================================================

class ExecuteRequest(BaseModel):
    """执行请求 - 支持多种粒度"""
    # 可选: 直接执行Skill
    skill_id: Optional[str] = None

    # 可选: 执行Workflow
    workflow_id: Optional[str] = None

    # 可选: 自然语言 (走Master Agent)
    natural_language: Optional[str] = None

    # 执行参数
    params: dict = {}

    # 执行选项
    async_execution: bool = False
    skip_approval: bool = False


class ExecuteResponse(BaseModel):
    """执行响应"""
    execution_id: str
    execution_type: Literal["skill", "workflow", "master_agent"]
    status: ExecutionStatus

    # 执行详情 (根据类型返回不同内容)
    skill_execution: Optional[SkillExecution] = None
    workflow_execution: Optional[WorkflowExecution] = None
    master_session: Optional[MasterAgentSession] = None

    # 通用字段
    message: Optional[str] = None
    error: Optional[str] = None


# ============================================================
# Legacy compatibility (兼容旧API)
# ============================================================

class Skill(BaseModel):
    """兼容旧版Skill模型"""
    id: str
    name: str
    description: str
    prompt: str
    category: str = "general"
    requires_approval: bool = False
    affected_systems: list[str] = []
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class SkillCreate(BaseModel):
    name: str
    description: str
    prompt: str
    category: str = "general"
    requires_approval: bool = False
    affected_systems: list[str] = []


class SkillUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    prompt: Optional[str] = None
    category: Optional[str] = None
    requires_approval: Optional[bool] = None
    affected_systems: Optional[list[str]] = None
