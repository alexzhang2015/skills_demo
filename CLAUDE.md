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

This is a Skills editing and execution demo built with FastAPI + Tailwind CSS.

### Backend (app/)

- **main.py** - FastAPI app with REST API routes for skills CRUD and execution
- **models.py** - Pydantic models: `Skill`, `SkillCreate`, `SkillUpdate`, `ExecutionStep`, `ExecutionResult`, `ExecuteRequest`
- **engine.py** - `SkillsEngine` class handles all business logic:
  - In-memory storage (`self.skills`, `self.executions` dicts)
  - Step parsing from prompts (regex for "1. step" format)
  - Skill execution with step-by-step results and timing
  - Three demo skills initialized on startup: greet, calculate, summarize

### Frontend

- **templates/index.html** - Jinja2 template with Tailwind CSS (CDN), 3-panel layout
- **static/app.js** - `SkillsApp` class handles UI interactions, API calls, result rendering
- Dark mode auto-detects system preference via `prefers-color-scheme`

### Data Flow

```
Frontend (app.js) → POST /api/execute → SkillsEngine.execute_skill()
                                              ↓
                                    Parse steps from prompt
                                              ↓
                                    Execute each step (with 0.1s delay)
                                              ↓
                                    Generate final result
                                              ↓
                                    Return ExecutionResult with steps
```

### Adding New Skill Types

1. Add step handling in `engine.py:_execute_step()` for skill-specific logic
2. Add result generation in `engine.py:_generate_final_result()`
3. Optionally register as demo skill in `engine.py:_init_demo_skills()`
