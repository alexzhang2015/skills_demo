# Skills Demo 技术文档

## 项目概述

Skills Demo 是一个用于编写、调试和执行 Claude Skills 的 Web 演示应用。

| 项目信息 | 详情 |
|---------|------|
| 技术栈 | FastAPI + Jinja2 + Tailwind CSS + Vanilla JS |
| Python 版本 | >= 3.10 |
| 包管理 | uv |

---

## 架构设计

```
┌─────────────────────────────────────────────────────────────┐
│                        Frontend                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │ Skills List │  │   Editor    │  │ Execution Results   │  │
│  │   Panel     │  │   Panel     │  │      Panel          │  │
│  └─────────────┘  └─────────────┘  └─────────────────────┘  │
│                         │                                    │
│                    Tailwind CSS + app.js                     │
└─────────────────────────┬───────────────────────────────────┘
                          │ HTTP/JSON
┌─────────────────────────┴───────────────────────────────────┐
│                     FastAPI Backend                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │                    API Routes                         │   │
│  │  /api/skills (CRUD)  │  /api/execute  │  /api/executions │
│  └──────────────────────┴────────────────┴──────────────┘   │
│                          │                                   │
│  ┌──────────────────────┴───────────────────────────────┐   │
│  │                   SkillsEngine                        │   │
│  │  - Skill Management    - Step Parser                  │   │
│  │  - Execution Engine    - Result Generator             │   │
│  └───────────────────────────────────────────────────────┘   │
│                          │                                   │
│  ┌───────────────────────┴──────────────────────────────┐   │
│  │              In-Memory Storage                        │   │
│  │  skills: dict[str, Skill]                            │   │
│  │  executions: dict[str, ExecutionResult]              │   │
│  └───────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
skills_demo/
├── app/                      # Python 后端
│   ├── __init__.py
│   ├── main.py              # FastAPI 应用入口和路由
│   ├── models.py            # Pydantic 数据模型
│   └── engine.py            # 核心业务逻辑引擎
├── static/                   # 前端静态资源
│   ├── app.js               # 前端应用逻辑
│   └── style.css            # 自定义样式
├── templates/                # Jinja2 模板
│   └── index.html           # 主页面
├── tests/                    # 测试代码
│   ├── test_api.py          # 基础 API 测试
│   └── test_full.py         # 完整集成测试
├── docs/                     # 文档
│   └── TECHNICAL.md         # 技术文档
├── pyproject.toml           # 项目配置
└── README.md                # 快速入门
```

---

## 数据模型

### SkillStatus (枚举)

```python
class SkillStatus(str, Enum):
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 执行中
    SUCCESS = "success"      # 成功
    ERROR = "error"          # 错误
```

### Skill (技能)

```python
class Skill(BaseModel):
    id: str                  # UUID[:8] 唯一标识
    name: str                # 技能名称
    description: str         # 技能描述
    prompt: str              # 技能提示词
    created_at: datetime     # 创建时间
    updated_at: datetime     # 更新时间
```

### ExecutionStep (执行步骤)

```python
class ExecutionStep(BaseModel):
    step_id: int             # 步骤编号 (1-based)
    action: str              # 操作名称
    detail: str              # 执行详情
    timestamp: datetime      # 时间戳
    status: SkillStatus      # 步骤状态
    result: Optional[Any]    # 执行结果
    duration_ms: Optional[float]  # 耗时(毫秒)
```

### ExecutionResult (执行结果)

```python
class ExecutionResult(BaseModel):
    execution_id: str        # 执行 ID
    skill_id: str            # 技能 ID
    skill_name: str          # 技能名称
    status: SkillStatus      # 执行状态
    input_args: Optional[str]    # 输入参数
    steps: list[ExecutionStep]   # 步骤列表
    final_result: Optional[str]  # 最终结果
    error: Optional[str]         # 错误信息
    started_at: datetime         # 开始时间
    completed_at: Optional[datetime]  # 完成时间
    total_duration_ms: Optional[float]  # 总耗时
```

---

## API 接口

### Skills CRUD

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| GET | `/api/skills` | 获取所有技能 | - | `{"skills": [Skill]}` |
| GET | `/api/skills/{id}` | 获取单个技能 | - | `Skill` / 404 |
| POST | `/api/skills` | 创建技能 | `SkillCreate` | `Skill` |
| PUT | `/api/skills/{id}` | 更新技能 | `SkillUpdate` | `Skill` / 404 |
| DELETE | `/api/skills/{id}` | 删除技能 | - | `{"message": "..."}` / 404 |

### Execution

| 方法 | 端点 | 描述 | 请求体 | 响应 |
|------|------|------|--------|------|
| POST | `/api/execute` | 执行技能 | `ExecuteRequest` | `ExecutionResult` |
| GET | `/api/executions` | 执行历史 | - | `{"executions": [...]}` |
| GET | `/api/executions/{id}` | 单个执行记录 | - | `ExecutionResult` / 404 |

### 请求/响应示例

**创建技能:**
```bash
curl -X POST http://localhost:8000/api/skills \
  -H "Content-Type: application/json" \
  -d '{
    "name": "hello",
    "description": "Say hello",
    "prompt": "Greet the user.\n\nSteps:\n1. Parse input\n2. Generate greeting"
  }'
```

**执行技能:**
```bash
curl -X POST http://localhost:8000/api/execute \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "abc12345",
    "args": "World"
  }'
```

---

## 核心引擎

### SkillsEngine 类

```python
class SkillsEngine:
    skills: dict[str, Skill]              # 技能存储
    executions: dict[str, ExecutionResult] # 执行历史
```

### 主要方法

| 方法 | 功能 |
|------|------|
| `create_skill(data)` | 创建新技能，生成 UUID |
| `get_skill(id)` | 按 ID 获取技能 |
| `get_all_skills()` | 获取所有技能列表 |
| `update_skill(id, data)` | 部分更新技能 |
| `delete_skill(id)` | 删除技能 |
| `execute_skill(id, args)` | 执行技能，返回详细结果 |

### 执行流程

```
execute_skill(skill_id, args)
    │
    ├─ 1. 验证技能存在
    │
    ├─ 2. 创建 ExecutionResult (status=RUNNING)
    │
    ├─ 3. _parse_steps_from_prompt(prompt)
    │      └─ 正则提取 "1. xxx" 格式的步骤
    │
    ├─ 4. 遍历执行每个步骤
    │      ├─ 创建 ExecutionStep
    │      ├─ sleep(0.1s) 模拟执行
    │      ├─ _execute_step() 获取结果
    │      └─ 记录耗时
    │
    ├─ 5. _generate_final_result() 生成最终输出
    │
    └─ 6. 更新状态，记录到 executions
```

### 步骤解析规则

从 prompt 中提取编号步骤：

```
输入 prompt:
"""
Perform a calculation.

Steps:
1. Parse the expression
2. Validate safety
3. Calculate result
"""

输出 steps:
["Parse the expression", "Validate safety", "Calculate result"]
```

---

## 前端架构

### SkillsApp 类

```javascript
class SkillsApp {
    currentSkillId    // 当前选中技能 ID
    skills            // 技能列表

    // DOM 引用
    skillsList, skillForm, skillName, skillDesc,
    skillPrompt, executeArgs, executionResults
}
```

### 核心方法

| 方法 | 功能 |
|------|------|
| `loadSkills()` | 从 API 加载技能列表 |
| `renderSkillsList()` | 渲染左侧技能列表 |
| `selectSkill(id)` | 选中技能，填充表单 |
| `newSkill()` | 清空表单，准备新建 |
| `saveSkill()` | 保存技能 (POST/PUT) |
| `deleteSkill()` | 删除当前技能 |
| `executeSkill()` | 执行技能，显示结果 |
| `renderExecutionResult(result)` | 渲染执行结果卡片 |
| `clearResults()` | 清空结果面板 |

### UI 交互流程

```
用户选择技能 → selectSkill() → 填充编辑表单
     │
用户修改内容 → saveSkill() → API 调用 → 刷新列表
     │
用户点击 Run → executeSkill() → 显示 Loading
     │                              │
     └──────────────────────────────┴→ renderExecutionResult()
                                          └→ 显示步骤和结果
```

---

## 深色模式

### 实现方式

```javascript
// 检测系统偏好
if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    document.documentElement.classList.add('dark');
}

// 监听系统变化
window.matchMedia('(prefers-color-scheme: dark)')
    .addEventListener('change', e => {
        document.documentElement.classList.toggle('dark', e.matches);
    });
```

### Tailwind 配置

```javascript
tailwind.config = {
    darkMode: 'class',
    theme: {
        extend: {
            colors: {
                dark: {
                    bg: '#0d1117',
                    card: '#161b22',
                    border: '#30363d',
                    hover: '#21262d'
                }
            }
        }
    }
}
```

---

## 预置技能

### greet - 问候生成

```
输入: 用户名 (可选)
输出: "Hello, {name}! Welcome to the Skills Demo. Have a great day!"

步骤:
1. Parse the input arguments
2. Generate personalized greeting
3. Return the formatted message
```

### calculate - 数学计算

```
输入: 数学表达式 (如 "2 + 3 * 4")
输出: "Result: 2 + 3 * 4 = 14"

步骤:
1. Parse the math expression
2. Validate the expression is safe
3. Calculate the result
4. Return formatted result

安全过滤: 只允许 0-9 + - * / ( ) . 和空格
```

### summarize - 文本总结

```
输入: 待总结文本
输出: 文本摘要

步骤:
1. Receive input text
2. Analyze content structure
3. Extract key points
4. Generate concise summary
```

---

## 测试覆盖

### 测试统计

| 测试文件 | 测试数 | 覆盖范围 |
|---------|--------|---------|
| test_api.py | 9 | 基础 API 功能 |
| test_full.py | 24 | 完整集成测试 |
| **总计** | **33** | - |

### 测试分类

```
TestHomepage (3)
├── test_homepage_loads
├── test_static_css
└── test_static_js

TestSkillsCRUD (8)
├── test_list_skills_has_demos
├── test_get_skill_by_id
├── test_get_nonexistent_skill (404)
├── test_create_skill_full
├── test_update_skill_partial
├── test_update_nonexistent_skill (404)
├── test_delete_skill_success
└── test_delete_nonexistent_skill (404)

TestSkillExecution (8)
├── test_execute_greet_skill
├── test_execute_greet_without_args
├── test_execute_calculate_skill
├── test_execute_calculate_complex
├── test_execute_summarize_skill
├── test_execute_nonexistent_skill
└── test_execute_custom_skill

TestExecutionHistory (3)
├── test_list_executions
├── test_get_execution_by_id
└── test_get_nonexistent_execution (404)

TestEdgeCases (3)
├── test_skill_with_no_steps_in_prompt
├── test_skill_with_empty_args
└── test_calculate_with_invalid_expression
```

### 运行测试

```bash
# 运行所有测试
uv run pytest tests/ -v

# 运行特定测试文件
uv run pytest tests/test_full.py -v

# 运行特定测试类
uv run pytest tests/test_full.py::TestSkillExecution -v
```

---

## 开发指南

### 环境搭建

```bash
# 克隆项目
cd skills_demo

# 安装依赖
uv sync

# 启动开发服务器 (热重载)
uv run uvicorn app.main:app --reload --port 8000
```

### 添加新技能类型

1. **在 engine.py 中添加处理逻辑:**

```python
def _execute_step(self, skill_name, step_idx, step_desc, args):
    # ... 现有代码 ...
    elif skill_name == "new_skill":
        if step_idx == 0:
            return "Step 1 result"
        # ...
    return f"Step {step_idx + 1} completed"

def _generate_final_result(self, skill_name, args):
    # ... 现有代码 ...
    elif skill_name == "new_skill":
        return f"New skill result for: {args}"
    return "Skill executed successfully"
```

2. **在 _init_demo_skills 中注册:**

```python
def _init_demo_skills(self):
    demo_skills = [
        # ... 现有技能 ...
        SkillCreate(
            name="new_skill",
            description="Description here",
            prompt="""Prompt here.

Steps:
1. First step
2. Second step"""
        ),
    ]
```

### 扩展存储

当前使用内存存储，可扩展为持久化：

```python
# 替换 engine.py 中的存储
class SkillsEngine:
    def __init__(self, db_session):
        self.db = db_session

    def create_skill(self, skill_data):
        skill = SkillModel(**skill_data.dict())
        self.db.add(skill)
        self.db.commit()
        return skill
```

---

## 部署

### 生产环境

```bash
# 使用 gunicorn + uvicorn workers
pip install gunicorn

gunicorn app.main:app \
    -w 4 \
    -k uvicorn.workers.UvicornWorker \
    -b 0.0.0.0:8000
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv && uv sync

EXPOSE 8000
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0"]
```

---

## 依赖清单

### 运行时依赖

| 包 | 版本 | 用途 |
|----|------|------|
| fastapi | >= 0.115.0 | Web 框架 |
| uvicorn[standard] | >= 0.32.0 | ASGI 服务器 |
| jinja2 | >= 3.1.0 | 模板引擎 |
| python-multipart | >= 0.0.9 | 表单处理 |
| pydantic | >= 2.0.0 | 数据验证 |

### 开发依赖

| 包 | 版本 | 用途 |
|----|------|------|
| pytest | >= 8.0.0 | 测试框架 |
| httpx | >= 0.27.0 | HTTP 测试客户端 |

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 0.1.0 | 2025-12-28 | 初始版本，基础功能完成 |
