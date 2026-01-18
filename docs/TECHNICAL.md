# Skills Demo 技术文档

## 项目概述

Skills Demo 是一个企业级 AI 运营自动化平台，实现"运营即代码"（Operations as Code）理念。

| 项目信息 | 详情 |
|---------|------|
| 技术栈 | FastAPI + SQLAlchemy + Multi-LLM Providers |
| Python 版本 | >= 3.10 |
| 包管理 | uv |
| 版本 | 2.1.0 |

---

## 架构设计

### 整体架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户层 (User Layer)                             │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────────┐   │
│  │  Web UI      │  │  CLI         │  │  API Client                  │   │
│  └──────────────┘  └──────────────┘  └──────────────────────────────┘   │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │ HTTP/JSON
┌─────────────────────────────────────┴───────────────────────────────────┐
│                         API 层 (FastAPI Routes)                          │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  /api/v2/skills/*    统一 Skills API                             │    │
│  │  /api/governance/*   治理监控 API                                │    │
│  │  /api/capture/*      录制生成 API                                │    │
│  │  /api/skills/*       原有四层架构 API                            │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────┬───────────────────────────────────┘
                                      │
┌─────────────────────────────────────┴───────────────────────────────────┐
│                        统一引擎层 (Unified Engine)                        │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │                    UnifiedSkillsEngine                           │    │
│  │  • Skill 加载与执行    • 多 LLM Provider 支持                     │    │
│  │  • 工具路由与权限      • 监控与审计                               │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└──────────┬──────────────┬──────────────┬──────────────┬─────────────────┘
           │              │              │              │
    ┌──────┴──────┐ ┌─────┴─────┐ ┌──────┴──────┐ ┌─────┴─────┐
    │ LLM Provider│ │Tool Router│ │ Governance  │ │  Capture  │
    │    Layer    │ │   Layer   │ │   Layer     │ │   Layer   │
    └──────┬──────┘ └─────┬─────┘ └──────┬──────┘ └─────┬─────┘
           │              │              │              │
┌──────────┴──────────────┴──────────────┴──────────────┴─────────────────┐
│                          存储层 (Storage Layer)                           │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  SQLite/PostgreSQL    Vector Store    File System (.claude/)    │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 六层模块架构

```
┌─────────────────────────────────────────────────────────────────────────┐
│                      Layer 1: LLM Provider 抽象层                         │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │   Claude   │ │   OpenAI   │ │   Gemini   │ │   Ollama   │           │
│  │  Provider  │ │  Provider  │ │  Provider  │ │  Provider  │           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │
│                         ↓ 统一接口 BaseLLMProvider                        │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                      Layer 2: Tool Router 工具路由层                       │
│  ┌─────────────────────────────────────────────────────────────────┐    │
│  │  工具注册    权限检查    格式适配    执行路由                      │    │
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                │    │
│  │  │ BUILTIN │ │   MCP   │ │PLAYWRIGHT│ │ CUSTOM  │                │    │
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                │    │
│  └─────────────────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                      Layer 3: Governance 治理层                           │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │  Metrics   │ │   Audit    │ │   Safety   │ │   Alerts   │           │
│  │  Collector │ │   Logger   │ │   Guard    │ │  Manager   │           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │
│    成功率监控      审计日志       安全隔离       告警管理                   │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                      Layer 4: Capture 知识捕获层                          │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │  Recorder  │ │ Generator  │ │  Refiner   │ │ Repository │           │
│  │  操作录制   │ │ Skill生成  │ │ 参数优化   │ │  知识库    │           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                      Layer 5: Storage 存储层                              │
│  ┌────────────────────────┐ ┌────────────────────────┐                  │
│  │    SQLite/PostgreSQL   │ │     Vector Store       │                  │
│  │  执行记录  会话  审计   │ │  Embeddings  RAG搜索   │                  │
│  └────────────────────────┘ └────────────────────────┘                  │
└─────────────────────────────────────────────────────────────────────────┘
                                  │
┌─────────────────────────────────┴───────────────────────────────────────┐
│                      Layer 6: 四层 Agent 架构 (原有)                       │
│  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────┐           │
│  │   Master   │ │ Sub-Agent  │ │  Workflow  │ │   Skills   │           │
│  │   Agent    │ │  Manager   │ │   Engine   │ │  Executor  │           │
│  └────────────┘ └────────────┘ └────────────┘ └────────────┘           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
skills_demo/
├── app/                          # Python 后端
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口和路由
│   ├── models.py                 # Pydantic 数据模型
│   ├── skills_engine.py          # 统一 Skills 执行引擎 (NEW)
│   ├── tool_router.py            # 工具路由系统 (NEW)
│   │
│   ├── providers/                # LLM Provider 抽象层 (NEW)
│   │   ├── __init__.py
│   │   ├── base.py               # 基础抽象类
│   │   ├── factory.py            # Provider 工厂
│   │   ├── claude_provider.py    # Claude 实现
│   │   ├── openai_provider.py    # OpenAI 实现
│   │   ├── gemini_provider.py    # Google Gemini 实现
│   │   └── ollama_provider.py    # Ollama 本地模型实现
│   │
│   ├── storage/                  # 存储层 (NEW)
│   │   ├── __init__.py
│   │   ├── database.py           # 数据库连接管理
│   │   ├── models.py             # ORM 模型
│   │   └── repository.py         # 数据访问层
│   │
│   ├── governance/               # 治理系统 (NEW)
│   │   ├── __init__.py
│   │   ├── metrics.py            # 监控指标收集
│   │   ├── audit.py              # 审计日志
│   │   ├── safety.py             # 安全隔离
│   │   └── alerts.py             # 告警管理
│   │
│   ├── capture/                  # 知识捕获 (NEW)
│   │   ├── __init__.py
│   │   ├── recorder.py           # Chrome 操作录制
│   │   ├── generator.py          # SKILL.md 生成器
│   │   ├── refiner.py            # 参数化/泛化工具
│   │   ├── repository.py         # 知识库管理
│   │   └── vector_store.py       # 向量存储 (RAG)
│   │
│   ├── layers.py                 # 四层 Agent 架构
│   └── mcp.py                    # MCP 客户端
│
├── static/                       # 前端静态资源
│   ├── app.js
│   └── style.css
│
├── templates/                    # Jinja2 模板
│   └── index.html
│
├── .claude/skills/               # Skills 存储
│   ├── product-launch/
│   │   └── SKILL.md
│   └── menu-management/
│       └── SKILL.md
│
├── data/                         # 数据存储
│   ├── skills.db                 # SQLite 数据库
│   └── vectors/                  # 向量索引
│
├── tests/                        # 测试代码
├── docs/                         # 文档
├── pyproject.toml                # 项目配置
└── README.md
```

---

## 核心模块详解

### 1. LLM Provider 抽象层

提供统一的多 LLM 接口，支持动态切换。

```python
# app/providers/base.py

class BaseLLMProvider(ABC):
    """LLM Provider 基类"""

    @abstractmethod
    def chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs
    ) -> LLMResponse:
        """同步对话"""
        pass

    @abstractmethod
    def stream_chat(
        self,
        messages: list[Message],
        tools: Optional[list[ToolDefinition]] = None,
        **kwargs
    ) -> Generator[str, None, LLMResponse]:
        """流式对话"""
        pass
```

**支持的 Provider:**

| Provider | 模型 | 环境变量 |
|----------|------|---------|
| Claude | claude-sonnet-4-20250514 等 | ANTHROPIC_API_KEY |
| OpenAI | gpt-4o, gpt-4o-mini 等 | OPENAI_API_KEY |
| Gemini | gemini-2.0-flash 等 | GOOGLE_API_KEY |
| Ollama | llama3.3, qwen2.5 等 | OLLAMA_HOST |

**使用示例:**

```python
from app.providers import get_provider

# 使用 Claude
provider = get_provider("claude", model="claude-sonnet-4-20250514")

# 切换到 OpenAI
provider = get_provider("openai", model="gpt-4o")

# 使用本地 Ollama
provider = get_provider("ollama", model="llama3.3")
```

### 2. Tool Router 工具路由

统一管理和路由所有工具调用。

```python
# app/tool_router.py

class ToolRouter:
    """工具路由器"""

    def register_tool(
        self,
        metadata: ToolMetadata,
        handler: Callable
    ):
        """注册工具"""
        pass

    def get_tool_definitions(
        self,
        allowed_tools: List[str] = None,
        access_levels: List[AccessLevel] = None
    ) -> List[ToolDefinition]:
        """获取可用工具定义"""
        pass

    def execute(self, tool_call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass
```

**工具类别:**

| 类别 | 说明 | 示例 |
|------|------|------|
| BUILTIN | 内置工具 | Read, Write, Glob |
| MCP | MCP 协议工具 | mcp__database__query |
| PLAYWRIGHT | 浏览器自动化 | mcp__playwright__browser_* |
| CUSTOM | 自定义工具 | 业务特定工具 |

**访问级别:**

| 级别 | 说明 |
|------|------|
| READ | 只读操作 |
| WRITE | 写入操作 |
| EXECUTE | 执行操作 |
| ADMIN | 管理操作 |

### 3. Governance 治理系统

提供完整的监控、审计、安全能力。

#### 3.1 Metrics 监控指标

```python
# app/governance/metrics.py

class MetricsCollector:
    """监控指标收集器"""

    def record(
        self,
        execution_id: str,
        scope: MetricScope,      # SKILL / TOOL / GLOBAL
        target_id: str,
        success: bool,
        duration_ms: float,
        **metadata
    ):
        """记录指标"""
        pass

    def get_success_rate(
        self,
        scope: MetricScope,
        target_id: str,
        hours: int = 24
    ) -> float:
        """获取成功率"""
        pass

    def get_dashboard(self) -> MetricsDashboard:
        """获取仪表盘数据"""
        pass
```

#### 3.2 Audit 审计日志

```python
# app/governance/audit.py

class AuditLogger:
    """审计日志记录器"""

    # 事件类型
    EXECUTION_START = "execution_start"
    EXECUTION_END = "execution_end"
    TOOL_CALL = "tool_call"
    APPROVAL_REQUESTED = "approval_requested"
    APPROVAL_GRANTED = "approval_granted"
    SKILL_CREATED = "skill_created"

    def log_execution_start(self, execution_id, skill_id, user_id, parameters):
        """记录执行开始"""
        pass

    def log_tool_call(self, execution_id, tool_name, arguments, success, result):
        """记录工具调用"""
        pass
```

#### 3.3 Safety 安全隔离

```python
# app/governance/safety.py

class SafetyGuard:
    """安全守卫"""

    def classify_operation(
        self,
        tool_name: str,
        params: Dict[str, Any]
    ) -> OperationType:
        """分类操作类型: READ / WRITE / EXECUTE / DANGEROUS"""
        pass

    def check_permission(
        self,
        context: SecurityContext,
        tool_name: str,
        params: Dict[str, Any]
    ) -> SecurityCheckResult:
        """检查权限"""
        pass

    def validate_bash_command(self, command: str) -> SecurityCheckResult:
        """验证 Bash 命令安全性"""
        pass
```

#### 3.4 Alerts 告警管理

```python
# app/governance/alerts.py

class AlertManager:
    """告警管理器"""

    # 内置规则
    RULES = {
        "success_rate_low": AlertRule(
            threshold=0.9,
            severity=AlertSeverity.WARNING,
            message="成功率低于 90%"
        ),
        "success_rate_critical": AlertRule(
            threshold=0.7,
            severity=AlertSeverity.CRITICAL,
            message="成功率低于 70%"
        ),
    }

    def check_and_trigger(self):
        """检查并触发告警"""
        pass

    def acknowledge(self, alert_id: str, by: str) -> Alert:
        """确认告警"""
        pass

    def resolve(self, alert_id: str) -> Alert:
        """解决告警"""
        pass
```

### 4. Capture 知识捕获

实现从人工操作到自动化 Skill 的转化。

#### 4.1 Recorder 操作录制

```python
# app/capture/recorder.py

class ActionRecorder:
    """操作录制器"""

    def start_session(
        self,
        name: str = None,
        start_url: str = None,
        recorded_by: str = None
    ) -> RecordingSession:
        """开始录制会话"""
        pass

    def record_action(
        self,
        action_type: ActionType,    # CLICK, FILL, NAVIGATE, etc.
        selector: ElementSelector,
        value: str = None,
        **options
    ) -> RecordedAction:
        """记录操作"""
        pass

    def end_session(self, session_id: str) -> RecordingSession:
        """结束录制"""
        pass
```

**操作类型:**

| 类型 | 说明 |
|------|------|
| NAVIGATE | 页面导航 |
| CLICK | 点击操作 |
| FILL | 填充输入框 |
| SELECT | 下拉选择 |
| WAIT_FOR_ELEMENT | 等待元素 |
| ASSERT_TEXT | 断言文本 |

#### 4.2 Generator SKILL.md 生成

```python
# app/capture/generator.py

class SkillGenerator:
    """SKILL.md 生成器"""

    def generate(
        self,
        recording: RecordingSession,
        skill_name: str = None,
        category: str = None
    ) -> GeneratedSkill:
        """从录制生成 Skill"""
        pass

    def _extract_parameters(self, actions) -> List[ExtractedParameter]:
        """提取参数"""
        pass

    def _generate_steps(self, actions) -> List[GeneratedStep]:
        """生成步骤"""
        pass
```

#### 4.3 Refiner 参数化优化

```python
# app/capture/refiner.py

class SkillRefiner:
    """Skill 优化器"""

    def refine(
        self,
        skill: GeneratedSkill,
        options: RefineOptions = None
    ) -> RefineResult:
        """优化 Skill"""
        pass

    # 优化能力
    # - 参数化：替换硬编码值为 ${param}
    # - 泛化：使用更稳定的选择器
    # - 增强：添加错误处理、重试逻辑
    # - 文档：添加使用示例、FAQ
```

#### 4.4 Vector Store 向量存储

```python
# app/capture/vector_store.py

class SkillVectorStore(VectorStore):
    """Skill 向量存储"""

    def add_skill(
        self,
        skill_id: str,
        name: str,
        description: str,
        content: str,
        category: str = None,
        tags: List[str] = None
    ) -> str:
        """添加 Skill 到向量库"""
        pass

    def search_skills(
        self,
        query: str,
        top_k: int = 5,
        category: str = None
    ) -> List[SearchMatch]:
        """语义搜索 Skills"""
        pass
```

**Embedding 后端:**

| 后端 | 说明 | 环境变量 |
|------|------|---------|
| Voyage AI | 高质量 Embedding | VOYAGE_API_KEY |
| OpenAI | text-embedding-3-small | OPENAI_API_KEY |
| Local | 本地简单 Embedding | 无需配置 |

---

## API 接口

### V2 API (新版统一接口)

#### Skills 执行

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/v2/skills/{id}/execute` | 执行 Skill |
| GET | `/api/v2/skills` | 列出 Skills |
| GET | `/api/v2/skills/search?q=xxx` | 语义搜索 Skills |
| GET | `/api/v2/skills/{id}` | 获取 Skill 详情 |
| GET | `/api/v2/skills/{id}/stats` | 获取 Skill 统计 |

#### Provider 管理

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/v2/provider` | 获取当前 Provider |
| POST | `/api/v2/provider` | 切换 Provider |

### Governance API (治理监控)

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | `/api/governance/metrics` | 获取监控指标 |
| GET | `/api/governance/metrics/dashboard` | 获取仪表盘 |
| GET | `/api/governance/alerts` | 获取告警列表 |
| POST | `/api/governance/alerts/{id}/acknowledge` | 确认告警 |
| POST | `/api/governance/alerts/{id}/resolve` | 解决告警 |
| GET | `/api/governance/audit` | 获取审计日志 |

### Capture API (录制生成)

| 方法 | 端点 | 描述 |
|------|------|------|
| POST | `/api/capture/recording/start` | 开始录制 |
| POST | `/api/capture/recording/{id}/action` | 记录操作 |
| POST | `/api/capture/recording/{id}/stop` | 停止录制 |
| GET | `/api/capture/recording/{id}` | 获取录制详情 |
| GET | `/api/capture/recordings` | 列出所有录制 |
| POST | `/api/capture/generate` | 从录制生成 Skill |
| POST | `/api/capture/refine` | 优化 Skill |

### V1 API (原有四层架构)

保持兼容，详见原文档。

---

## 执行流程

### Skill 执行完整流程

```
用户请求: POST /api/v2/skills/product-launch/execute
    │
    ├─ 1. 加载 Skill
    │      └─ KnowledgeRepository.get_skill("product-launch")
    │
    ├─ 2. 创建执行上下文
    │      └─ SkillExecutionContext(skill_id, parameters, access_levels)
    │
    ├─ 3. 审计日志
    │      └─ AuditLogger.log_execution_start()
    │
    ├─ 4. 安全检查
    │      └─ SafetyGuard.check_permission()
    │
    ├─ 5. 获取可用工具
    │      └─ ToolRouter.get_tool_definitions(allowed_tools)
    │
    ├─ 6. LLM 执行循环
    │      ├─ LLMProvider.chat(messages, tools)
    │      ├─ 处理工具调用
    │      │    ├─ SafetyGuard.check_permission()
    │      │    ├─ ToolRouter.execute(tool_call)
    │      │    └─ AuditLogger.log_tool_call()
    │      └─ 重复直到完成或达到 max_turns
    │
    ├─ 7. 记录指标
    │      └─ MetricsCollector.record(success, duration_ms)
    │
    ├─ 8. 更新统计
    │      └─ KnowledgeRepository.update_stats()
    │
    ├─ 9. 检查告警
    │      └─ AlertManager.check_and_trigger()
    │
    └─ 10. 审计日志
           └─ AuditLogger.log_execution_end()
```

### 知识捕获流程

```
┌────────────────────────────────────────────────────────────────────────┐
│  Step 1: 操作录制                                                       │
│  POST /api/capture/recording/start                                     │
│       ↓                                                                │
│  用户在浏览器中操作，前端调用 /action 记录每个操作                         │
│       ↓                                                                │
│  POST /api/capture/recording/{id}/stop                                 │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│  Step 2: Skill 生成                                                     │
│  POST /api/capture/generate                                            │
│       ↓                                                                │
│  SkillGenerator 分析操作序列:                                            │
│  • 提取可变参数 (价格、日期、名称等)                                       │
│  • 生成步骤说明                                                          │
│  • 推断前置条件                                                          │
│  • 生成 SKILL.md 内容                                                   │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│  Step 3: 优化精炼                                                        │
│  POST /api/capture/refine                                              │
│       ↓                                                                │
│  SkillRefiner 优化:                                                     │
│  • 参数化硬编码值                                                        │
│  • 泛化不稳定选择器                                                       │
│  • 添加错误处理                                                          │
│  • 补充文档示例                                                          │
└────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ↓
┌────────────────────────────────────────────────────────────────────────┐
│  Step 4: 存储索引                                                        │
│  KnowledgeRepository.save_skill()                                      │
│  SkillVectorStore.add_skill()                                          │
│       ↓                                                                │
│  Skill 可通过语义搜索发现和执行                                            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 配置说明

### 环境变量

```bash
# LLM Providers
ANTHROPIC_API_KEY=sk-ant-xxx       # Claude API Key
OPENAI_API_KEY=sk-xxx              # OpenAI API Key
GOOGLE_API_KEY=xxx                 # Google Gemini API Key
OLLAMA_HOST=http://localhost:11434 # Ollama 服务地址

# 默认 Provider
LLM_PROVIDER=claude                # claude / openai / gemini / ollama
LLM_MODEL=claude-sonnet-4-20250514 # 默认模型

# 数据库
DATABASE_URL=sqlite:///data/skills.db  # 或 PostgreSQL 连接串

# Embeddings
VOYAGE_API_KEY=xxx                 # Voyage AI (优先)
# 如果没有 Voyage，会使用 OpenAI 或本地 Embedding
```

### pyproject.toml 依赖

```toml
dependencies = [
    # Web Framework
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.32.0",
    "jinja2>=3.1.0",
    "python-multipart>=0.0.9",
    "pydantic>=2.0.0",
    "pyyaml>=6.0.0",
    "python-dotenv>=1.0.0",

    # LLM Providers
    "anthropic>=0.40.0",
    "openai>=1.0.0",
    "google-generativeai>=0.8.0",
    "ollama>=0.3.0",

    # Storage
    "sqlalchemy>=2.0.0",
    "aiosqlite>=0.19.0",

    # Embeddings
    "numpy>=1.24.0",
    "voyageai>=0.3.0",
]
```

---

## 监控指标

### 核心指标

| 指标 | 说明 | 目标值 |
|------|------|--------|
| global_success_rate | 全局成功率 | > 90% |
| skill_success_rate | 单 Skill 成功率 | > 85% |
| avg_duration_ms | 平均执行时间 | < 30000ms |
| tool_call_count | 工具调用次数 | - |

### 告警规则

| 规则 | 阈值 | 级别 |
|------|------|------|
| success_rate_low | < 90% | WARNING |
| success_rate_critical | < 70% | CRITICAL |
| high_latency | > 2x 预期时间 | WARNING |

---

## 开发指南

### 添加新 LLM Provider

1. 继承 `BaseLLMProvider`:

```python
# app/providers/new_provider.py

class NewProvider(BaseLLMProvider):
    def __init__(self, model: str = None, **kwargs):
        self.model = model or "default-model"
        self._client = NewClient()

    def chat(self, messages, tools=None, **kwargs):
        # 实现对话逻辑
        pass

    def stream_chat(self, messages, tools=None, **kwargs):
        # 实现流式对话
        pass

    def convert_tools(self, tools):
        # 转换工具格式
        pass
```

2. 注册到工厂:

```python
# app/providers/factory.py

PROVIDER_CLASSES["new"] = "app.providers.new_provider:NewProvider"
```

### 添加新工具

```python
from app.tool_router import get_router, ToolMetadata, ToolCategory, AccessLevel

router = get_router()

# 定义工具元数据
metadata = ToolMetadata(
    name="my_custom_tool",
    description="自定义工具描述",
    category=ToolCategory.CUSTOM,
    access_level=AccessLevel.WRITE,
    parameters={
        "param1": {"type": "string", "required": True},
    }
)

# 定义处理函数
def handle_my_tool(params):
    return {"result": "success"}

# 注册工具
router.register_tool(metadata, handle_my_tool)
```

### 添加新告警规则

```python
from app.governance.alerts import get_alert_manager, AlertRule, AlertSeverity

alert_manager = get_alert_manager()

# 添加自定义规则
alert_manager.add_rule(
    "custom_rule",
    AlertRule(
        condition=lambda m: m.get("custom_metric") > 100,
        severity=AlertSeverity.WARNING,
        message="自定义指标超过阈值",
        cooldown_minutes=30,
    )
)
```

---

## 版本历史

| 版本 | 日期 | 变更 |
|------|------|------|
| 2.1.0 | 2025-01 | P0-P3 完整实施：LLM Provider、Tool Router、Governance、Capture、Vector Store |
| 2.0.0 | 2024-12 | 四层 Agent 架构 |
| 0.1.0 | 2024-12 | 初始版本 |

---

*文档持续更新中。如有问题请联系开发团队。*
