from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

from .layers import SkillExecutor, WorkflowEngine, SubAgentManager, MasterAgent
from .mcp import MCPClient

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
