# Skills Demo

企业级 AI 运营自动化平台 - 实现"运营即代码"（Operations as Code）

## 核心特性

| 特性 | 说明 |
|------|------|
| **多 LLM 支持** | Claude、OpenAI、Gemini、Ollama 动态切换 |
| **工具路由** | 统一工具管理，支持 MCP / Playwright / 自定义工具 |
| **治理监控** | 成功率追踪、审计日志、告警管理 |
| **知识捕获** | Chrome 录制 → SKILL.md 自动生成 |
| **语义搜索** | 向量化存储，RAG 增强的 Skill 发现 |
| **安全隔离** | Read/Write 分离，权限分级控制 |

## 快速开始

```bash
# 安装依赖
uv sync

# 配置环境变量
cp .env.example .env
# 编辑 .env 设置 API Keys

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000

# 打开浏览器
open http://localhost:8000
```

## 技术栈

| 层级 | 技术 |
|------|------|
| Web Framework | FastAPI + Pydantic |
| Frontend | Tailwind CSS + Vanilla JS |
| LLM Providers | Claude / OpenAI / Gemini / Ollama |
| Storage | SQLAlchemy + SQLite/PostgreSQL |
| Vector Store | Voyage AI / OpenAI Embeddings |
| Template | Jinja2 |

## 项目结构

```
skills_demo/
├── app/
│   ├── main.py               # FastAPI 入口
│   ├── skills_engine.py      # 统一执行引擎
│   ├── tool_router.py        # 工具路由
│   │
│   ├── providers/            # LLM Provider 抽象层
│   │   ├── base.py           # 基础接口
│   │   ├── claude_provider.py
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   └── ollama_provider.py
│   │
│   ├── governance/           # 治理系统
│   │   ├── metrics.py        # 监控指标
│   │   ├── audit.py          # 审计日志
│   │   ├── safety.py         # 安全隔离
│   │   └── alerts.py         # 告警管理
│   │
│   ├── capture/              # 知识捕获
│   │   ├── recorder.py       # 操作录制
│   │   ├── generator.py      # Skill 生成
│   │   ├── refiner.py        # 参数优化
│   │   ├── repository.py     # 知识库
│   │   └── vector_store.py   # 向量存储
│   │
│   ├── storage/              # 存储层
│   │   ├── database.py
│   │   ├── models.py
│   │   └── repository.py
│   │
│   ├── layers.py             # 四层 Agent 架构
│   └── mcp.py                # MCP 客户端
│
├── .claude/skills/           # Skills 存储
├── static/                   # 前端资源
├── templates/                # 页面模板
├── tests/                    # 测试
└── docs/                     # 文档
```

## API 概览

### V2 API (统一接口)

| 端点 | 说明 |
|------|------|
| `POST /api/v2/skills/{id}/execute` | 执行 Skill |
| `GET /api/v2/skills/search?q=xxx` | 语义搜索 |
| `POST /api/v2/provider` | 切换 LLM Provider |

### Governance API

| 端点 | 说明 |
|------|------|
| `GET /api/governance/metrics` | 监控指标 |
| `GET /api/governance/alerts` | 告警列表 |
| `GET /api/governance/audit` | 审计日志 |

### Capture API

| 端点 | 说明 |
|------|------|
| `POST /api/capture/recording/start` | 开始录制 |
| `POST /api/capture/generate` | 生成 Skill |
| `POST /api/capture/refine` | 优化 Skill |

## 环境变量

```bash
# LLM Providers (至少配置一个)
ANTHROPIC_API_KEY=sk-ant-xxx
OPENAI_API_KEY=sk-xxx
GOOGLE_API_KEY=xxx
OLLAMA_HOST=http://localhost:11434

# 默认配置
LLM_PROVIDER=claude
LLM_MODEL=claude-sonnet-4-20250514

# 数据库
DATABASE_URL=sqlite:///data/skills.db

# Embeddings (可选)
VOYAGE_API_KEY=xxx
```

## 监控目标

| 指标 | 目标 |
|------|------|
| 全局成功率 | > 90% |
| 单 Skill 成功率 | > 85% |
| 平均执行时间 | < 30s |

## 开发命令

```bash
# 安装依赖
uv sync

# 启动开发服务器
uv run uvicorn app.main:app --reload --port 8000

# 运行测试
uv run pytest tests/ -v

# 运行特定测试
uv run pytest tests/test_full.py -v
```

## 文档

- [技术文档](docs/TECHNICAL.md) - 详细架构和 API 说明
- [设计文档](docs/AGENTIC_OPERATIONS_DESIGN.md) - 运营自动化设计理念

## 版本

| 版本 | 说明 |
|------|------|
| 2.1.0 | 多 LLM 支持、治理系统、知识捕获 |
| 2.0.0 | 四层 Agent 架构 |
| 0.1.0 | 初始版本 |

## License

MIT
