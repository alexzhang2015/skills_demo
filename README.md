# Skills Demo

A web demo for writing, debugging and executing Claude Skills.

## Features

- **Skills Editor** - Create and edit skills with a web-based editor
- **Execution Engine** - Execute skills with custom arguments
- **Execution Details** - View step-by-step execution with timing
- **Dark Mode** - Automatic dark/light mode based on system preference
- **Hot Reload** - Auto-restart on Python code changes

## Quick Start

```bash
# Install dependencies
uv sync

# Start development server (with hot reload)
uv run uvicorn app.main:app --reload --port 8000

# Open browser
open http://localhost:8000
```

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | FastAPI + Pydantic |
| Frontend | Tailwind CSS + Vanilla JS |
| Template | Jinja2 |
| Package Manager | uv |

## Project Structure

```
skills_demo/
├── app/
│   ├── main.py          # FastAPI routes
│   ├── models.py        # Data models
│   └── engine.py        # Core execution engine
├── static/
│   ├── app.js           # Frontend logic
│   └── style.css        # Custom styles
├── templates/
│   └── index.html       # Main page
├── tests/
│   ├── test_api.py      # API tests
│   └── test_full.py     # Integration tests
└── docs/
    └── TECHNICAL.md     # Technical documentation
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/skills` | List all skills |
| POST | `/api/skills` | Create a skill |
| GET | `/api/skills/{id}` | Get skill by ID |
| PUT | `/api/skills/{id}` | Update a skill |
| DELETE | `/api/skills/{id}` | Delete a skill |
| POST | `/api/execute` | Execute a skill |
| GET | `/api/executions` | List execution history |

## Built-in Demo Skills

| Skill | Description | Example Args |
|-------|-------------|--------------|
| greet | Generate greeting | `World` |
| calculate | Math calculation | `2 + 3 * 4` |
| summarize | Summarize text | `Long text here...` |

## Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ -v --tb=short
```

## Documentation

See [docs/TECHNICAL.md](docs/TECHNICAL.md) for detailed technical documentation.

## License

MIT
