"""
测试4层架构API
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ==================== Layer 4: Skills API ====================

def test_list_skills(client):
    """测试获取所有原子技能"""
    response = client.get("/api/skills")
    assert response.status_code == 200
    data = response.json()
    assert "skills" in data
    assert len(data["skills"]) >= 10  # 原子技能数量


def test_get_skill(client):
    """测试获取单个技能"""
    response = client.get("/api/skills")
    skills = response.json()["skills"]
    skill_id = skills[0]["id"]

    response = client.get(f"/api/skills/{skill_id}")
    assert response.status_code == 200
    assert response.json()["id"] == skill_id


def test_get_nonexistent_skill(client):
    """测试获取不存在的技能"""
    response = client.get("/api/skills/nonexistent-skill")
    assert response.status_code == 404


def test_execute_skill(client):
    """测试执行原子技能"""
    response = client.get("/api/skills")
    skills = response.json()["skills"]
    skill = skills[0]

    response = client.post(f"/api/skills/{skill['id']}/execute", json={
        "params": {"product_name": "测试商品"}
    })
    assert response.status_code == 200
    data = response.json()
    assert "execution_id" in data
    assert "status" in data


def test_list_skill_executions(client):
    """测试获取技能执行历史"""
    # 先执行一个技能
    response = client.get("/api/skills")
    skill_id = response.json()["skills"][0]["id"]
    client.post(f"/api/skills/{skill_id}/execute", json={"params": {}})

    # 获取执行历史
    response = client.get("/api/skill-executions")
    assert response.status_code == 200
    assert "executions" in response.json()


def test_get_skill_execution(client):
    """测试获取单个执行记录"""
    # 先执行一个技能
    response = client.get("/api/skills")
    skill_id = response.json()["skills"][0]["id"]
    exec_response = client.post(f"/api/skills/{skill_id}/execute", json={"params": {}})
    exec_id = exec_response.json()["execution_id"]

    # 获取执行记录
    response = client.get(f"/api/skill-executions/{exec_id}")
    assert response.status_code == 200
    assert response.json()["execution_id"] == exec_id


# ==================== Layer 3: Workflows API ====================

def test_list_workflows(client):
    """测试获取所有工作流"""
    response = client.get("/api/workflows")
    assert response.status_code == 200
    data = response.json()
    assert "workflows" in data
    assert len(data["workflows"]) >= 1


def test_get_workflow(client):
    """测试获取单个工作流"""
    response = client.get("/api/workflows")
    workflows = response.json()["workflows"]
    if workflows:
        workflow_id = workflows[0]["id"]
        response = client.get(f"/api/workflows/{workflow_id}")
        assert response.status_code == 200
        assert response.json()["id"] == workflow_id


def test_execute_workflow(client):
    """测试执行工作流"""
    response = client.get("/api/workflows")
    workflows = response.json()["workflows"]
    if workflows:
        workflow_id = workflows[0]["id"]
        response = client.post(f"/api/workflows/{workflow_id}/execute", json={
            "params": {"product_name": "测试商品", "price": 25.0}
        })
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data


def test_list_workflow_executions(client):
    """测试获取工作流执行历史"""
    response = client.get("/api/workflow-executions")
    assert response.status_code == 200
    assert "executions" in response.json()


# ==================== Layer 2: Agents API ====================

def test_list_agents(client):
    """测试获取所有子场景Agent"""
    response = client.get("/api/agents")
    assert response.status_code == 200
    data = response.json()
    assert "agents" in data
    assert len(data["agents"]) >= 1


def test_get_agent(client):
    """测试获取单个Agent"""
    response = client.get("/api/agents")
    agents = response.json()["agents"]
    if agents:
        agent_id = agents[0]["id"]
        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["id"] == agent_id


def test_get_agent_tasks(client):
    """测试获取Agent任务"""
    response = client.get("/api/agents")
    agents = response.json()["agents"]
    if agents:
        agent_id = agents[0]["id"]
        response = client.get(f"/api/agents/{agent_id}/tasks")
        assert response.status_code == 200
        assert "tasks" in response.json()


# ==================== Layer 1: Master Agent API ====================

def test_process_natural_language(client):
    """测试自然语言处理"""
    response = client.post("/api/process", json={
        "input": "上市新品麦辣鸡腿堡，定价25元"
    })
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "status" in data


def test_list_sessions(client):
    """测试获取所有会话"""
    # 先创建一个会话
    client.post("/api/process", json={"input": "生成周报"})

    response = client.get("/api/sessions")
    assert response.status_code == 200
    assert "sessions" in response.json()


def test_get_session(client):
    """测试获取单个会话"""
    # 先创建一个会话
    proc_response = client.post("/api/process", json={"input": "配置满减活动"})
    session_id = proc_response.json()["session_id"]

    response = client.get(f"/api/sessions/{session_id}")
    assert response.status_code == 200
    assert response.json()["session_id"] == session_id


# ==================== 预览和模板 API ====================

def test_preview_execution(client):
    """测试执行预览"""
    response = client.post("/api/preview", json={
        "input": "下周一川香系列产品全国上市，定价比竞品低2元"
    })
    assert response.status_code == 200
    preview = response.json()

    # 验证预览结构
    assert "intent" in preview
    assert "estimated_impact" in preview
    assert "execution_steps" in preview

    # 验证影响估算
    impact = preview["estimated_impact"]
    assert "affected_stores" in impact
    assert "affected_skus" in impact
    assert "affected_systems" in impact
    assert "estimated_duration" in impact


def test_preview_with_relative_date(client):
    """测试带相对日期的预览"""
    response = client.post("/api/preview", json={
        "input": "下下周一华东区汉堡类产品涨价5%"
    })
    assert response.status_code == 200
    preview = response.json()

    # 验证实体提取
    entities = preview.get("entities", {})
    # 应该识别出日期
    assert "date" in entities or "percentage" in entities


def test_preview_with_competitor_reference(client):
    """测试带竞品参照的预览"""
    response = client.post("/api/preview", json={
        "input": "新品定价比竞品低10%"
    })
    assert response.status_code == 200
    preview = response.json()

    entities = preview.get("entities", {})
    assert "competitor_reference" in entities
    assert entities["competitor_reference"]["percentage"] == 10.0


def test_enrich_input(client):
    """测试输入丰富化"""
    response = client.post("/api/enrich", json={
        "input": "季节性新品发布，芒果系列"
    })
    assert response.status_code == 200
    enriched = response.json()

    assert "original_input" in enriched
    assert "entities" in enriched
    assert "complexity_level" in enriched


def test_list_templates(client):
    """测试获取模板列表"""
    response = client.get("/api/templates")
    assert response.status_code == 200
    data = response.json()

    assert "templates" in data
    assert len(data["templates"]) >= 5  # 至少5个模板


def test_get_template(client):
    """测试获取单个模板"""
    response = client.get("/api/templates/seasonal_new_product")
    assert response.status_code == 200
    template = response.json()

    assert template["id"] == "seasonal_new_product"
    assert "name" in template
    assert "template" in template
    assert "estimated_impact" in template


def test_match_template(client):
    """测试模板匹配"""
    response = client.post("/api/templates/match", json={
        "input": "季节限定产品上市"
    })
    assert response.status_code == 200
    result = response.json()

    assert "matched" in result
    if result["matched"]:
        assert "template" in result
        assert result["template"] is not None


# ==================== 系统状态 API ====================

def test_homepage(client):
    """测试首页"""
    response = client.get("/")
    assert response.status_code == 200
    assert "运营" in response.text or "Agent" in response.text


def test_status_endpoint(client):
    """测试系统状态"""
    response = client.get("/api/status")
    assert response.status_code == 200
    status = response.json()
    assert "version" in status
    assert "architecture" in status
    assert "layers" in status
    assert "mcp" in status  # MCP集成状态


def test_architecture_endpoint(client):
    """测试架构详情"""
    response = client.get("/api/architecture")
    assert response.status_code == 200
    data = response.json()
    assert "layers" in data
    assert len(data["layers"]) == 4
    assert "mcp_integration" in data  # MCP集成信息


# ==================== MCP API 测试 ====================

def test_list_mcp_servers(client):
    """测试获取MCP服务器列表"""
    response = client.get("/api/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert "servers" in data
    assert len(data["servers"]) == 10  # 10个核心系统
    # 验证服务器结构
    server = data["servers"][0]
    assert "id" in server
    assert "name" in server
    assert "capabilities" in server


def test_get_mcp_server(client):
    """测试获取单个MCP服务器"""
    response = client.get("/api/mcp/servers/pos")
    assert response.status_code == 200
    server = response.json()
    assert server["id"] == "pos"
    assert server["name"] == "POS系统"
    assert "capabilities" in server


def test_get_nonexistent_mcp_server(client):
    """测试获取不存在的MCP服务器"""
    response = client.get("/api/mcp/servers/nonexistent")
    assert response.status_code == 404


def test_list_mcp_tools(client):
    """测试获取MCP工具列表"""
    response = client.get("/api/mcp/tools")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    assert len(data["tools"]) > 20  # 超过20个工具
    # 验证工具结构
    tool = data["tools"][0]
    assert "id" in tool
    assert "name" in tool
    assert "server_id" in tool


def test_list_mcp_tools_filtered_by_server(client):
    """测试按服务器过滤MCP工具"""
    response = client.get("/api/mcp/tools?server_id=pos")
    assert response.status_code == 200
    data = response.json()
    assert "tools" in data
    # 所有工具都应该属于POS服务器
    for tool in data["tools"]:
        assert tool["server_id"] == "pos"


def test_get_mcp_tool(client):
    """测试获取单个MCP工具"""
    response = client.get("/api/mcp/tools/pos.product.create")
    assert response.status_code == 200
    tool = response.json()
    assert tool["id"] == "pos.product.create"
    assert tool["server_id"] == "pos"


def test_get_nonexistent_mcp_tool(client):
    """测试获取不存在的MCP工具"""
    response = client.get("/api/mcp/tools/nonexistent.tool")
    assert response.status_code == 404


def test_call_mcp_tool(client):
    """测试调用MCP工具"""
    response = client.post("/api/mcp/tools/pos.product.create/call", json={
        "params": {"product_name": "测试商品", "price": 28.0}
    })
    assert response.status_code == 200
    result = response.json()
    assert result["tool_id"] == "pos.product.create"
    assert result["status"] == "success"
    assert "output_data" in result


def test_mcp_status(client):
    """测试MCP状态"""
    response = client.get("/api/mcp/status")
    assert response.status_code == 200
    status = response.json()
    assert "servers" in status
    assert "total_tools" in status
    assert status["total_tools"] > 0


def test_mcp_history(client):
    """测试MCP执行历史"""
    # 先执行一个工具调用
    client.post("/api/mcp/tools/pos.product.create/call", json={
        "params": {"product_name": "历史测试", "price": 25.0}
    })
    # 获取历史
    response = client.get("/api/mcp/history")
    assert response.status_code == 200
    data = response.json()
    assert "history" in data
    assert len(data["history"]) > 0
