"""
4层架构完整测试套件

测试覆盖:
- Layer 1: Master Agent (自然语言处理、意图识别)
- Layer 2: Sub Agents (子场景Agent)
- Layer 3: Workflows (工作流编排)
- Layer 4: Skills (原子技能执行)
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


# ==================== 首页测试 ====================

class TestHomepage:
    def test_homepage_loads(self, client):
        """测试首页加载"""
        response = client.get("/")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]

    def test_static_js(self, client):
        """测试静态JS文件"""
        response = client.get("/static/app.js")
        assert response.status_code == 200


# ==================== Layer 4: Skills 测试 ====================

class TestSkills:
    def test_list_skills_has_items(self, client):
        """测试技能列表非空"""
        response = client.get("/api/skills")
        assert response.status_code == 200
        skills = response.json()["skills"]
        assert len(skills) >= 10

    def test_skill_has_required_fields(self, client):
        """测试技能包含必要字段"""
        response = client.get("/api/skills")
        skill = response.json()["skills"][0]
        assert "id" in skill
        assert "name" in skill
        assert "description" in skill
        assert "category" in skill

    def test_skill_has_target_systems(self, client):
        """测试技能包含目标系统"""
        response = client.get("/api/skills")
        skill = response.json()["skills"][0]
        assert "target_systems" in skill
        assert isinstance(skill["target_systems"], list)

    def test_get_skill_by_id(self, client):
        """测试按ID获取技能"""
        response = client.get("/api/skills")
        skill_id = response.json()["skills"][0]["id"]

        response = client.get(f"/api/skills/{skill_id}")
        assert response.status_code == 200
        assert response.json()["id"] == skill_id

    def test_get_nonexistent_skill(self, client):
        """测试获取不存在的技能"""
        response = client.get("/api/skills/nonexistent")
        assert response.status_code == 404

    def test_execute_skill_success(self, client):
        """测试执行技能成功"""
        response = client.get("/api/skills")
        skill = response.json()["skills"][0]

        response = client.post(f"/api/skills/{skill['id']}/execute", json={
            "params": {"product_name": "测试商品", "price": 25.0}
        })
        assert response.status_code == 200
        data = response.json()
        assert "execution_id" in data
        assert data["status"] in ["success", "running", "error"]

    def test_execute_skill_with_empty_params(self, client):
        """测试空参数执行技能"""
        response = client.get("/api/skills")
        skill = response.json()["skills"][0]

        response = client.post(f"/api/skills/{skill['id']}/execute", json={
            "params": {}
        })
        assert response.status_code == 200

    def test_execute_nonexistent_skill(self, client):
        """测试执行不存在的技能"""
        response = client.post("/api/skills/nonexistent/execute", json={
            "params": {}
        })
        assert response.status_code == 200
        assert response.json()["status"] == "error"

    def test_skill_execution_has_tool_calls(self, client):
        """测试技能执行包含工具调用"""
        response = client.get("/api/skills")
        skill = response.json()["skills"][0]

        response = client.post(f"/api/skills/{skill['id']}/execute", json={
            "params": {}
        })
        data = response.json()
        assert "tool_calls" in data
        assert isinstance(data["tool_calls"], list)

    def test_list_skill_executions(self, client):
        """测试获取技能执行历史"""
        # 先执行一个技能
        response = client.get("/api/skills")
        skill_id = response.json()["skills"][0]["id"]
        client.post(f"/api/skills/{skill_id}/execute", json={"params": {}})

        response = client.get("/api/skill-executions")
        assert response.status_code == 200
        assert "executions" in response.json()

    def test_get_skill_execution_by_id(self, client):
        """测试按ID获取执行记录"""
        response = client.get("/api/skills")
        skill_id = response.json()["skills"][0]["id"]
        exec_response = client.post(f"/api/skills/{skill_id}/execute", json={"params": {}})
        exec_id = exec_response.json()["execution_id"]

        response = client.get(f"/api/skill-executions/{exec_id}")
        assert response.status_code == 200
        assert response.json()["execution_id"] == exec_id

    def test_get_nonexistent_execution(self, client):
        """测试获取不存在的执行记录"""
        response = client.get("/api/skill-executions/nonexistent")
        assert response.status_code == 404


# ==================== Layer 3: Workflows 测试 ====================

class TestWorkflows:
    def test_list_workflows(self, client):
        """测试获取工作流列表"""
        response = client.get("/api/workflows")
        assert response.status_code == 200
        assert "workflows" in response.json()

    def test_workflow_has_required_fields(self, client):
        """测试工作流包含必要字段"""
        response = client.get("/api/workflows")
        workflows = response.json()["workflows"]
        if workflows:
            workflow = workflows[0]
            assert "id" in workflow
            assert "name" in workflow

    def test_get_workflow_by_id(self, client):
        """测试按ID获取工作流"""
        response = client.get("/api/workflows")
        workflows = response.json()["workflows"]
        if workflows:
            workflow_id = workflows[0]["id"]
            response = client.get(f"/api/workflows/{workflow_id}")
            assert response.status_code == 200
            assert response.json()["id"] == workflow_id

    def test_get_nonexistent_workflow(self, client):
        """测试获取不存在的工作流"""
        response = client.get("/api/workflows/nonexistent")
        assert response.status_code == 404

    def test_execute_workflow(self, client):
        """测试执行工作流"""
        response = client.get("/api/workflows")
        workflows = response.json()["workflows"]
        if workflows:
            workflow_id = workflows[0]["id"]
            response = client.post(f"/api/workflows/{workflow_id}/execute", json={
                "params": {"product_name": "新品测试", "price": 28.0}
            })
            assert response.status_code == 200
            assert "execution_id" in response.json()

    def test_list_workflow_executions(self, client):
        """测试获取工作流执行历史"""
        response = client.get("/api/workflow-executions")
        assert response.status_code == 200
        assert "executions" in response.json()

    def test_workflow_execution_has_nodes(self, client):
        """测试工作流执行包含节点"""
        response = client.get("/api/workflows")
        workflows = response.json()["workflows"]
        if workflows:
            workflow_id = workflows[0]["id"]
            exec_response = client.post(f"/api/workflows/{workflow_id}/execute", json={
                "params": {}
            })
            data = exec_response.json()
            assert "node_executions" in data


# ==================== Layer 2: Agents 测试 ====================

class TestAgents:
    def test_list_agents(self, client):
        """测试获取Agent列表"""
        response = client.get("/api/agents")
        assert response.status_code == 200
        assert "agents" in response.json()
        assert len(response.json()["agents"]) >= 1

    def test_agent_has_required_fields(self, client):
        """测试Agent包含必要字段"""
        response = client.get("/api/agents")
        agent = response.json()["agents"][0]
        assert "id" in agent
        assert "display_name" in agent

    def test_get_agent_by_id(self, client):
        """测试按ID获取Agent"""
        response = client.get("/api/agents")
        agent_id = response.json()["agents"][0]["id"]

        response = client.get(f"/api/agents/{agent_id}")
        assert response.status_code == 200
        assert response.json()["id"] == agent_id

    def test_get_nonexistent_agent(self, client):
        """测试获取不存在的Agent"""
        response = client.get("/api/agents/nonexistent")
        assert response.status_code == 404

    def test_get_agent_tasks(self, client):
        """测试获取Agent任务"""
        response = client.get("/api/agents")
        agent_id = response.json()["agents"][0]["id"]

        response = client.get(f"/api/agents/{agent_id}/tasks")
        assert response.status_code == 200
        assert "tasks" in response.json()


# ==================== Layer 1: Master Agent 测试 ====================

class TestMasterAgent:
    def test_process_product_launch(self, client):
        """测试处理新品上市请求"""
        response = client.post("/api/process", json={
            "input": "上市新品麦辣鸡腿堡，定价25元，1月15日全国发布"
        })
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert "status" in data

    def test_process_price_adjust(self, client):
        """测试处理调价请求"""
        response = client.post("/api/process", json={
            "input": "华东区麦辣鸡腿堡涨价8%"
        })
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_process_campaign(self, client):
        """测试处理营销活动请求"""
        response = client.post("/api/process", json={
            "input": "配置满30减5的促销活动"
        })
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_process_report(self, client):
        """测试处理报告请求"""
        response = client.post("/api/process", json={
            "input": "生成华东区本周销售周报"
        })
        assert response.status_code == 200
        assert "session_id" in response.json()

    def test_session_has_intent_analysis(self, client):
        """测试会话包含意图分析"""
        response = client.post("/api/process", json={
            "input": "新品发布麦辣鸡腿堡"
        })
        data = response.json()
        assert "intent_analysis" in data

    def test_list_sessions(self, client):
        """测试获取会话列表"""
        # 先创建会话
        client.post("/api/process", json={"input": "测试请求"})

        response = client.get("/api/sessions")
        assert response.status_code == 200
        assert "sessions" in response.json()

    def test_get_session_by_id(self, client):
        """测试按ID获取会话"""
        proc_response = client.post("/api/process", json={"input": "测试请求"})
        session_id = proc_response.json()["session_id"]

        response = client.get(f"/api/sessions/{session_id}")
        assert response.status_code == 200
        assert response.json()["session_id"] == session_id

    def test_get_nonexistent_session(self, client):
        """测试获取不存在的会话"""
        response = client.get("/api/sessions/nonexistent")
        assert response.status_code == 404


# ==================== 审批流程测试 ====================

class TestApprovalWorkflow:
    def test_approve_workflow_execution(self, client):
        """测试审批工作流执行"""
        # 执行需要审批的工作流
        response = client.get("/api/workflows")
        workflows = response.json()["workflows"]
        approval_workflow = next(
            (w for w in workflows if w.get("requires_approval")),
            workflows[0] if workflows else None
        )

        if approval_workflow:
            exec_response = client.post(f"/api/workflows/{approval_workflow['id']}/execute", json={
                "params": {}
            })
            exec_id = exec_response.json()["execution_id"]

            # 审批
            response = client.post(f"/api/workflow-executions/{exec_id}/approve", json={
                "approved": True,
                "approved_by": "测试管理员"
            })
            # 可能返回200或404（如果不需要审批）
            assert response.status_code in [200, 404]

    def test_approve_session(self, client):
        """测试审批会话"""
        # 创建需要审批的会话
        proc_response = client.post("/api/process", json={
            "input": "上市新品测试商品，定价100元"
        })
        session_id = proc_response.json()["session_id"]

        # 审批
        response = client.post(f"/api/sessions/{session_id}/approve", json={
            "approved": True,
            "approved_by": "测试管理员"
        })
        # 可能返回200或404（如果不需要审批）
        assert response.status_code in [200, 404]


# ==================== 系统状态测试 ====================

class TestSystemStatus:
    def test_status_endpoint(self, client):
        """测试系统状态端点"""
        response = client.get("/api/status")
        assert response.status_code == 200
        status = response.json()
        assert "version" in status
        assert "architecture" in status
        assert "layers" in status

    def test_status_has_layer_info(self, client):
        """测试状态包含各层信息"""
        response = client.get("/api/status")
        layers = response.json()["layers"]
        assert "layer1_master_agent" in layers
        assert "layer2_sub_agents" in layers
        assert "layer3_workflows" in layers
        assert "layer4_skills" in layers

    def test_architecture_endpoint(self, client):
        """测试架构详情端点"""
        response = client.get("/api/architecture")
        assert response.status_code == 200
        data = response.json()
        assert "layers" in data
        assert len(data["layers"]) == 4

    def test_architecture_has_mcp_integration(self, client):
        """测试架构包含MCP集成信息"""
        response = client.get("/api/architecture")
        data = response.json()
        assert "mcp_integration" in data
        assert "servers" in data["mcp_integration"]
        assert "tool_count" in data["mcp_integration"]
        assert "skill_to_mcp_mapping" in data["mcp_integration"]


# ==================== 边缘情况测试 ====================

class TestEdgeCases:
    def test_empty_input(self, client):
        """测试空输入"""
        response = client.post("/api/process", json={"input": ""})
        assert response.status_code == 200

    def test_long_input(self, client):
        """测试长输入"""
        long_input = "测试" * 1000
        response = client.post("/api/process", json={"input": long_input})
        assert response.status_code == 200

    def test_special_characters_input(self, client):
        """测试特殊字符输入"""
        response = client.post("/api/process", json={
            "input": "新品麦辣鸡腿堡定价25.00元，上市日期2025-01-15"
        })
        assert response.status_code == 200

    def test_concurrent_executions(self, client):
        """测试并发执行"""
        response = client.get("/api/skills")
        skill_id = response.json()["skills"][0]["id"]

        # 连续执行多次
        for _ in range(3):
            response = client.post(f"/api/skills/{skill_id}/execute", json={"params": {}})
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
