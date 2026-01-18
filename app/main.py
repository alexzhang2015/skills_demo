from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional, List
from pydantic import BaseModel

from .layers import SkillExecutor, WorkflowEngine, SubAgentManager, MasterAgent
from .mcp import MCPClient

# 新增模块导入
from .skills_engine import get_skills_engine, UnifiedSkillsEngine
from .tool_router import ToolAccessLevel as AccessLevel
from .governance.metrics import get_metrics_collector
from .governance.audit import get_audit_logger
from .governance.alerts import get_alert_manager
from .capture.recorder import get_recorder, ActionType, ElementSelector
from .capture.generator import get_generator
from .capture.refiner import get_refiner, RefineOptions

app = FastAPI(
    title="总部运营Agent",
    description="AI驱动的餐饮连锁运营自动化演示 - 四层架构Agent系统",
    version="2.0.0",
)

# Setup templates and static files
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")
app.mount("/slides", StaticFiles(directory=BASE_DIR / "workspace" / "slides"), name="slides")
templates = Jinja2Templates(directory=BASE_DIR / "templates")

# ==================== 四层架构初始化 ====================
# Layer 4 → Layer 3 → Layer 2 → Layer 1

skill_executor = SkillExecutor()
workflow_engine = WorkflowEngine(skill_executor)
sub_agent_manager = SubAgentManager(workflow_engine)
master_agent = MasterAgent(sub_agent_manager)


# ==================== 页面路由 ====================

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request, "index.html")


# ==================== Layer 1: Master Agent API ====================

class NaturalLanguageRequest(BaseModel):
    """自然语言输入请求"""
    input: str


class ApprovalRequest(BaseModel):
    """审批请求"""
    approved: bool
    approved_by: str = "运营总监"


@app.post("/api/process")
async def process_natural_language(request: NaturalLanguageRequest):
    """处理自然语言输入，由Master Agent进行意图路由"""
    session = master_agent.process(request.input)
    return session.model_dump()


@app.post("/api/preview")
async def preview_execution(request: NaturalLanguageRequest):
    """预览执行影响，不实际执行"""
    preview = master_agent.preview(request.input)
    return preview


@app.post("/api/enrich")
async def enrich_input(request: NaturalLanguageRequest):
    """丰富化自然语言输入"""
    enriched = master_agent.enrich_input(request.input)
    return enriched


# ==================== 模板库 API ====================

@app.get("/api/templates")
async def list_templates():
    """获取所有运营场景模板"""
    templates = master_agent.get_templates()
    return {"templates": templates}


@app.get("/api/templates/{template_id}")
async def get_template(template_id: str):
    """获取指定模板"""
    template = master_agent.get_template(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@app.post("/api/templates/match")
async def match_template(request: NaturalLanguageRequest):
    """根据输入匹配最佳模板"""
    matched = master_agent.match_template(request.input)
    if matched:
        return {"matched": True, "template": matched}
    return {"matched": False, "template": None}


@app.get("/api/sessions")
async def list_sessions():
    """获取所有会话"""
    sessions = master_agent.get_all_sessions()
    return {"sessions": [s.model_dump() for s in sessions]}


@app.get("/api/sessions/{session_id}")
async def get_session(session_id: str):
    """获取指定会话"""
    session = master_agent.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session.model_dump()


@app.post("/api/sessions/{session_id}/approve")
async def approve_session(session_id: str, request: ApprovalRequest):
    """审批会话"""
    session = master_agent.approve_session(
        session_id,
        request.approved,
        request.approved_by
    )
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or not awaiting approval")
    return session.model_dump()


# ==================== Layer 2: Sub Agents API ====================

@app.get("/api/agents")
async def list_agents():
    """获取所有子场景Agent"""
    agents = sub_agent_manager.get_all_agents()
    return {"agents": [a.model_dump() for a in agents]}


@app.get("/api/agents/{agent_id}")
async def get_agent(agent_id: str):
    """获取指定子场景Agent"""
    agent = sub_agent_manager.get_agent(agent_id)
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return agent.model_dump()


@app.get("/api/agents/{agent_id}/tasks")
async def get_agent_tasks(agent_id: str):
    """获取Agent的所有任务"""
    tasks = [t for t in sub_agent_manager.get_all_tasks() if t.agent_id == agent_id]
    return {"tasks": [t.model_dump() for t in tasks]}


# ==================== Layer 3: Workflow API ====================

@app.get("/api/workflows")
async def list_workflows():
    """获取所有工作流"""
    workflows = workflow_engine.get_all_workflows()
    return {"workflows": [w.model_dump() for w in workflows]}


@app.get("/api/workflows/{workflow_id}")
async def get_workflow(workflow_id: str):
    """获取指定工作流"""
    workflow = workflow_engine.get_workflow(workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow.model_dump()


class WorkflowExecuteRequest(BaseModel):
    """工作流执行请求"""
    params: dict = {}


@app.post("/api/workflows/{workflow_id}/execute")
async def execute_workflow(workflow_id: str, request: WorkflowExecuteRequest):
    """执行工作流"""
    execution = workflow_engine.execute(workflow_id, request.params)
    return execution.model_dump()


@app.get("/api/workflow-executions")
async def list_workflow_executions():
    """获取所有工作流执行记录"""
    executions = workflow_engine.get_all_executions()
    return {"executions": [e.model_dump() for e in executions]}


@app.get("/api/workflow-executions/{execution_id}")
async def get_workflow_execution(execution_id: str):
    """获取指定工作流执行记录"""
    execution = workflow_engine.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.model_dump()


@app.post("/api/workflow-executions/{execution_id}/approve")
async def approve_workflow_execution(execution_id: str, request: ApprovalRequest):
    """审批工作流执行"""
    execution = workflow_engine.approve_execution(
        execution_id,
        request.approved,
        request.approved_by
    )
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found or not awaiting approval")
    return execution.model_dump()


# ==================== Layer 4: Skills API ====================

@app.get("/api/skills")
async def list_skills():
    """获取所有原子技能"""
    skills = skill_executor.get_all_skills()
    return {"skills": [s.model_dump() for s in skills]}


@app.get("/api/skills/{skill_id}")
async def get_skill(skill_id: str):
    """获取指定原子技能"""
    skill = skill_executor.get_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.model_dump()


class SkillExecuteRequest(BaseModel):
    """技能执行请求"""
    params: dict = {}


@app.post("/api/skills/{skill_id}/execute")
async def execute_skill(skill_id: str, request: SkillExecuteRequest):
    """执行原子技能"""
    execution = skill_executor.execute(skill_id, request.params)
    return execution.model_dump()


@app.get("/api/skill-executions")
async def list_skill_executions():
    """获取所有技能执行记录"""
    executions = list(skill_executor.executions.values())
    return {"executions": [e.model_dump() for e in executions]}


@app.get("/api/skill-executions/{execution_id}")
async def get_skill_execution(execution_id: str):
    """获取指定技能执行记录"""
    execution = skill_executor.get_execution(execution_id)
    if not execution:
        raise HTTPException(status_code=404, detail="Execution not found")
    return execution.model_dump()


# ==================== MCP 系统集成 API ====================

# 全局MCP客户端（与SkillExecutor共享）
mcp_client = skill_executor.mcp_client


@app.get("/api/mcp/servers")
async def list_mcp_servers():
    """获取所有MCP服务器"""
    servers = mcp_client.server_registry.get_all_servers()
    return {"servers": [s.model_dump() for s in servers]}


@app.get("/api/mcp/servers/{server_id}")
async def get_mcp_server(server_id: str):
    """获取指定MCP服务器"""
    server = mcp_client.server_registry.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="MCP Server not found")
    return server.model_dump()


@app.get("/api/mcp/tools")
async def list_mcp_tools(server_id: Optional[str] = None):
    """获取所有MCP工具，可按服务器过滤"""
    tools = mcp_client.get_available_tools(server_id)
    return {"tools": [t.model_dump() for t in tools]}


@app.get("/api/mcp/tools/{tool_id}")
async def get_mcp_tool(tool_id: str):
    """获取指定MCP工具"""
    tool = mcp_client.tool_registry.get_tool(tool_id)
    if not tool:
        raise HTTPException(status_code=404, detail="MCP Tool not found")
    return tool.model_dump()


class MCPToolCallRequest(BaseModel):
    """MCP工具调用请求"""
    params: dict = {}


@app.post("/api/mcp/tools/{tool_id}/call")
async def call_mcp_tool(tool_id: str, request: MCPToolCallRequest):
    """直接调用MCP工具"""
    result = mcp_client.call_tool(tool_id, request.params)
    return result.model_dump()


@app.get("/api/mcp/status")
async def get_mcp_status():
    """获取MCP服务器状态"""
    return {
        "servers": mcp_client.get_server_status(),
        "total_tools": len(mcp_client.get_available_tools()),
        "execution_history_count": len(mcp_client.execution_history),
    }


@app.get("/api/mcp/history")
async def get_mcp_history(trace_id: Optional[str] = None, limit: int = 100):
    """获取MCP执行历史"""
    history = mcp_client.get_execution_history(trace_id, limit)
    return {"history": [h.model_dump() for h in history]}


# ==================== 系统状态 API ====================

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "version": "2.0.0",
        "architecture": "4-layer-agent",
        "demo_mode": "总部运营Agent",
        "layers": {
            "layer1_master_agent": {
                "sessions_count": len(master_agent.get_all_sessions()),
            },
            "layer2_sub_agents": {
                "agents_count": len(sub_agent_manager.get_all_agents()),
                "tasks_count": len(sub_agent_manager.get_all_tasks()),
            },
            "layer3_workflows": {
                "workflows_count": len(workflow_engine.get_all_workflows()),
                "executions_count": len(workflow_engine.get_all_executions()),
            },
            "layer4_skills": {
                "skills_count": len(skill_executor.get_all_skills()),
                "executions_count": len(skill_executor.executions),
            },
        },
        "mcp": {
            "servers_count": len(mcp_client.server_registry.get_all_servers()),
            "tools_count": len(mcp_client.get_available_tools()),
        },
    }


@app.get("/api/architecture")
async def get_architecture():
    """获取四层架构详情"""
    return {
        "layers": [
            {
                "layer": 1,
                "name": "Master Agent",
                "chinese_name": "总部运营 Master Agent",
                "description": "理解用户自然语言输入，分析意图，规划执行方案，协调多个子Agent",
                "components": ["意图识别", "实体提取", "执行规划", "结果汇总"],
            },
            {
                "layer": 2,
                "name": "Sub-scenario Agents",
                "chinese_name": "子场景 Agent 层",
                "description": "按业务领域划分的专家Agent，理解领域特定的业务逻辑",
                "components": [a.model_dump() for a in sub_agent_manager.get_all_agents()],
            },
            {
                "layer": 3,
                "name": "Workflow Engine",
                "chinese_name": "Workflow 编排层",
                "description": "定义和管理工作流，编排多个Skills的执行顺序",
                "components": [w.model_dump() for w in workflow_engine.get_all_workflows()],
            },
            {
                "layer": 4,
                "name": "Skills Executor",
                "chinese_name": "Skills 执行层",
                "description": "执行单一职责的原子技能，调用MCP Tools与后端系统交互",
                "components": [s.model_dump() for s in skill_executor.get_all_skills()],
            },
        ],
        "mcp_integration": {
            "servers": [s.model_dump() for s in mcp_client.server_registry.get_all_servers()],
            "tool_count": len(mcp_client.get_available_tools()),
            "skill_to_mcp_mapping": skill_executor.SKILL_TO_MCP_TOOLS,
        },
    }


# ==================== 新增: 统一 Skills 引擎 API ====================

# 初始化统一引擎
unified_engine = get_skills_engine()


class UnifiedSkillExecuteRequest(BaseModel):
    """统一 Skill 执行请求"""
    parameters: dict = {}
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    access_levels: List[str] = ["read"]


class ProviderSwitchRequest(BaseModel):
    """切换 LLM Provider 请求"""
    provider: str
    model: Optional[str] = None


@app.post("/api/v2/skills/{skill_id}/execute")
async def execute_skill_v2(skill_id: str, request: UnifiedSkillExecuteRequest):
    """使用统一引擎执行 Skill"""
    access_levels = [AccessLevel(level) for level in request.access_levels]

    result = unified_engine.execute(
        skill_id=skill_id,
        parameters=request.parameters,
        user_id=request.user_id,
        session_id=request.session_id,
        access_levels=access_levels,
    )
    return result.to_dict()


@app.get("/api/v2/skills")
async def list_skills_v2(category: Optional[str] = None):
    """列出所有 Skills (v2)"""
    skills = unified_engine.list_skills(category=category)
    return {"skills": [s.to_dict() for s in skills]}


@app.get("/api/v2/skills/search")
async def search_skills_v2(q: str, top_k: int = 5, use_vector: bool = True):
    """搜索 Skills (支持语义搜索)"""
    skills = unified_engine.search_skills(query=q, top_k=top_k, use_vector=use_vector)
    return {"skills": [s.to_dict() for s in skills if s]}


@app.get("/api/v2/skills/{skill_id}")
async def get_skill_v2(skill_id: str):
    """获取 Skill 详情 (v2)"""
    skill = unified_engine.load_skill(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill.to_dict()


@app.get("/api/v2/skills/{skill_id}/stats")
async def get_skill_stats(skill_id: str):
    """获取 Skill 统计信息"""
    stats = unified_engine.get_skill_stats(skill_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Skill not found")
    return stats


@app.post("/api/v2/provider")
async def switch_provider(request: ProviderSwitchRequest):
    """切换 LLM Provider"""
    unified_engine.set_provider(request.provider, request.model)
    return unified_engine.get_provider_info()


@app.get("/api/v2/provider")
async def get_provider_info():
    """获取当前 LLM Provider 信息"""
    return unified_engine.get_provider_info()


# ==================== 新增: 治理监控 API ====================

@app.get("/api/governance/metrics")
async def get_governance_metrics():
    """获取治理监控指标"""
    return unified_engine.get_metrics()


@app.get("/api/governance/metrics/dashboard")
async def get_metrics_dashboard():
    """获取监控仪表盘"""
    metrics = get_metrics_collector()
    dashboard = metrics.get_dashboard()
    return {
        "global_success_rate": dashboard.global_success_rate,
        "total_executions": dashboard.total_executions,
        "avg_duration_ms": dashboard.avg_duration_ms,
        "skills": dashboard.skills,
        "updated_at": dashboard.updated_at.isoformat() if dashboard.updated_at else None,
    }


@app.get("/api/governance/alerts")
async def get_alerts(active_only: bool = True):
    """获取告警"""
    alert_manager = get_alert_manager()
    if active_only:
        alerts = alert_manager.get_active_alerts()
    else:
        alerts = list(alert_manager._alerts.values())
    return {"alerts": [a.to_dict() for a in alerts]}


class AlertAcknowledgeRequest(BaseModel):
    """告警确认请求"""
    acknowledged_by: str


@app.post("/api/governance/alerts/{alert_id}/acknowledge")
async def acknowledge_alert(alert_id: str, request: AlertAcknowledgeRequest):
    """确认告警"""
    alert_manager = get_alert_manager()
    alert = alert_manager.acknowledge(alert_id, request.acknowledged_by)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


@app.post("/api/governance/alerts/{alert_id}/resolve")
async def resolve_alert(alert_id: str):
    """解决告警"""
    alert_manager = get_alert_manager()
    alert = alert_manager.resolve(alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
    return alert.to_dict()


@app.get("/api/governance/audit")
async def get_audit_logs(
    execution_id: Optional[str] = None,
    event_type: Optional[str] = None,
    limit: int = 100
):
    """获取审计日志"""
    audit = get_audit_logger()
    logs = audit.get_logs(
        execution_id=execution_id,
        event_type=event_type,
        limit=limit,
    )
    return {"logs": [log.to_dict() for log in logs]}


# ==================== 新增: 录制和生成 API ====================

class StartRecordingRequest(BaseModel):
    """开始录制请求"""
    name: Optional[str] = None
    start_url: Optional[str] = None
    recorded_by: Optional[str] = None


class RecordActionRequest(BaseModel):
    """记录操作请求"""
    action_type: str
    selector: Optional[dict] = None
    url: Optional[str] = None
    value: Optional[str] = None
    key: Optional[str] = None
    page_url: Optional[str] = None
    page_title: Optional[str] = None


class GenerateSkillRequest(BaseModel):
    """生成 Skill 请求"""
    session_id: str
    skill_name: Optional[str] = None
    category: Optional[str] = None


class RefineSkillRequest(BaseModel):
    """优化 Skill 请求"""
    parameterize: bool = True
    add_error_handling: bool = True
    add_examples: bool = True


@app.post("/api/capture/recording/start")
async def start_recording(request: StartRecordingRequest):
    """开始录制"""
    recorder = get_recorder()
    session = recorder.start_session(
        name=request.name,
        start_url=request.start_url,
        recorded_by=request.recorded_by,
    )
    return session.to_dict()


@app.post("/api/capture/recording/{session_id}/action")
async def record_action(session_id: str, request: RecordActionRequest):
    """记录操作"""
    recorder = get_recorder()

    # 转换选择器
    selector = None
    if request.selector:
        selector = ElementSelector(
            selector=request.selector.get("selector", ""),
            selector_type=request.selector.get("selector_type", "css"),
            tag_name=request.selector.get("tag_name"),
            text_content=request.selector.get("text_content"),
            attributes=request.selector.get("attributes", {}),
        )

    action = recorder.record_action(
        action_type=ActionType(request.action_type),
        selector=selector,
        url=request.url,
        value=request.value,
        key=request.key,
        page_url=request.page_url,
        page_title=request.page_title,
        session_id=session_id,
    )
    return action.to_dict()


@app.post("/api/capture/recording/{session_id}/stop")
async def stop_recording(session_id: str):
    """停止录制"""
    recorder = get_recorder()
    session = recorder.end_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Recording session not found")
    return session.to_dict()


@app.get("/api/capture/recording/{session_id}")
async def get_recording(session_id: str):
    """获取录制详情"""
    recorder = get_recorder()
    session = recorder.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Recording session not found")
    return session.to_dict()


@app.get("/api/capture/recordings")
async def list_recordings():
    """列出所有录制"""
    recorder = get_recorder()
    sessions = recorder.list_sessions()
    return {"recordings": [s.to_dict() for s in sessions]}


@app.post("/api/capture/generate")
async def generate_skill_from_recording(request: GenerateSkillRequest):
    """从录制生成 Skill"""
    recorder = get_recorder()
    generator = get_generator()

    session = recorder.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Recording session not found")

    skill = generator.generate(
        recording=session,
        skill_name=request.skill_name,
        category=request.category,
    )

    return {
        "name": skill.name,
        "description": skill.description,
        "parameters": [{"name": p.name, "type": p.param_type, "description": p.description} for p in skill.parameters],
        "steps": [{"number": s.step_number, "title": s.title, "actions": s.actions} for s in skill.steps],
        "content": skill.to_skill_md(),
    }


@app.post("/api/capture/refine")
async def refine_skill(request: RefineSkillRequest, skill_content: str):
    """优化 Skill"""
    refiner = get_refiner()
    # 注意：这里需要先解析 skill_content 为 GeneratedSkill 对象
    # 简化实现，返回优化建议
    return {
        "suggestions": [
            "考虑添加更多参数化",
            "建议使用更稳定的选择器",
            "添加错误处理逻辑",
        ]
    }


# ==================== 系统状态扩展 ====================

@app.get("/api/v2/status")
async def get_status_v2():
    """获取系统状态 (v2 - 包含新模块)"""
    metrics = unified_engine.get_metrics()
    provider_info = unified_engine.get_provider_info()

    return {
        "version": "2.1.0",
        "architecture": "4-layer-agent + unified-engine",
        "provider": provider_info,
        "governance": {
            "global_success_rate": metrics.get("global_success_rate", 0),
            "total_executions": metrics.get("total_executions", 0),
            "active_alerts": metrics.get("active_alerts", 0),
        },
        "layers": {
            "layer1_master_agent": {
                "sessions_count": len(master_agent.get_all_sessions()),
            },
            "layer2_sub_agents": {
                "agents_count": len(sub_agent_manager.get_all_agents()),
            },
            "layer3_workflows": {
                "workflows_count": len(workflow_engine.get_all_workflows()),
            },
            "layer4_skills": {
                "skills_count": len(skill_executor.get_all_skills()),
            },
        },
        "mcp": {
            "servers_count": len(mcp_client.server_registry.get_all_servers()),
            "tools_count": len(mcp_client.get_available_tools()),
        },
    }
