# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
uv sync

# Start dev server (hot reload)
uv run uvicorn app.main:app --reload --port 8000

# Run all tests
uv run pytest tests/ -v

# Run specific test file
uv run pytest tests/test_full.py -v

# Run specific test class
uv run pytest tests/test_full.py::TestSkillExecution -v

# Run single test
uv run pytest tests/test_full.py::TestSkillExecution::test_execute_greet_skill -v
```

## Architecture

Enterprise AI operations automation platform ("Operations as Code") built with FastAPI.

### Core Execution Pipeline

```
User Request → UnifiedSkillsEngine → LLM Provider → Tool Router → Result
                      │                    │              │
                      ├── Governance ──────┤              │
                      │   (metrics, audit, safety)        │
                      │                                   │
                      └── Capture ────────────────────────┘
                          (recording → SKILL.md generation)
```

### Key Modules

**`app/skills_engine.py`** - Unified execution engine that orchestrates all components:
- `UnifiedSkillsEngine.execute()` - Main entry point for Skill execution
- Integrates LLM providers, tool routing, governance, and knowledge repository
- Manages execution context with security levels and audit logging

**`app/providers/`** - Multi-LLM abstraction layer:
- `base.py` - `BaseLLMProvider` ABC with `Message`, `ToolDefinition`, `ToolCall`, `LLMResponse` dataclasses
- `claude_provider.py`, `openai_provider.py`, `gemini_provider.py`, `ollama_provider.py` - Concrete implementations
- `factory.py` - `get_provider(name)` factory function

**`app/tool_router.py`** - Unified tool management:
- `ToolRouter` manages builtin tools (bash, read, write, glob, grep), MCP tools, and custom tools
- `ToolAccessLevel` enum: READ, WRITE, EXECUTE, ADMIN for permission control
- `execute(ToolCall)` → `ToolResult` with safety checks

**`app/governance/`** - Monitoring and safety:
- `metrics.py` - `MetricsCollector` tracks success rates, durations, aggregates by scope
- `audit.py` - `AuditLogger` records all executions and tool calls
- `safety.py` - `SafetyGuard` with permission checks and dangerous pattern detection
- `alerts.py` - `AlertManager` with rule-based triggering (success rate thresholds)

**`app/capture/`** - Knowledge capture pipeline:
- `recorder.py` - Records browser actions (click, input, navigate) during Chrome sessions
- `generator.py` - Converts `RecordingSession` → `GeneratedSkill` (SKILL.md format)
- `refiner.py` - Parameterizes values, optimizes selectors
- `vector_store.py` - `SkillVectorStore` for semantic search with Voyage/OpenAI embeddings

**`app/layers/`** - Four-layer agent architecture:
- `master_agent.py` - Intent routing with keyword patterns and scenario templates
- `sub_agents.py` - Domain-specific agents (product, pricing, marketing, etc.)
- `workflow_engine.py` - DAG-based workflow execution
- `skill_executor.py` - Step-by-step Skill execution

### API Structure

- `/api/v2/skills/*` - Unified Skills API (execute, list, search)
- `/api/v2/provider` - LLM provider switching
- `/api/governance/*` - Metrics, alerts, audit logs
- `/api/capture/*` - Recording, SKILL.md generation

### Adding New Components

**New LLM Provider:**
1. Create `app/providers/{name}_provider.py` extending `BaseLLMProvider`
2. Implement `chat()`, `stream_chat()`, and tool format converters
3. Register in `app/providers/__init__.py`

**New Tool:**
1. Add to `ToolRouter._register_builtin_tools()` or call `register_tool()`
2. Provide `ToolMetadata` and handler function `(params) -> ToolResult`

**New Alert Rule:**
1. Add to `AlertManager._init_default_rules()` or call `add_rule()`
2. Specify scope, condition function, severity, and action
