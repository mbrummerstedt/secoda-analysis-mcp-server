# Secoda Analysis MCP Server

A **read-only** [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for exploring and analysing your [Secoda](https://www.secoda.co) data catalog. Designed for business users who need to discover data, look up metric definitions, and understand data lineage — without any risk of modifying the catalog.

## Features

- **Zero write access** — completely safe to use; nothing in Secoda can be changed
- **AI chat** — ask Secoda's AI natural language questions about your data
- **Semantic search** — find tables, columns, dashboards, and documentation by keyword
- **Glossary & definitions** — browse business term definitions
- **Data lineage** — trace where data comes from and where it flows downstream
- **Browse collections & Q&A** — explore organised resource groups and previously answered questions

## Tools

| Tool | Purpose |
|------|---------|
| `ai_chat` | Ask Secoda AI a natural language question (supports multi-turn conversations) |
| `search_data_assets` | Find tables, columns, charts, and dashboards by keyword |
| `search_documentation` | Find docs, glossary terms, and Q&A by keyword |
| `retrieve_entity` | Get full details of any entity by its Secoda ID |
| `get_resource` | Get full details of a catalog resource (table, column, view) by ID |
| `list_resources` | Browse and filter resources using structured criteria |
| `entity_lineage` | Trace upstream/downstream data flow for any entity |
| `glossary` | Browse all business term definitions in the workspace |
| `list_collections` | Browse organised groups of resources |
| `get_collection` | Get details of a specific collection |
| `list_questions` | Browse previously asked and answered Q&A threads |
| `get_question` | Read a specific question and its answer |

## Requirements

- Python 3.10+
- A Secoda account with API access
- A Secoda API token (read permissions are sufficient)

## Installation

```bash
pip install secoda-analysis-mcp
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uvx secoda-analysis-mcp
```

From source:

```bash
git clone https://github.com/mbrummerstedt/secoda-analysis-mcp.git
cd secoda-analysis-mcp
pip install .
```

## Configuration

The server is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_TOKEN` | Your Secoda API token (required) | — |
| `API_URL` | Secoda API base URL | `https://app.secoda.co/api/v1/` |
| `AI_PERSONA_ID` | Secoda AI persona ID — pins a specific persona for all `ai_chat` calls. Find it in Secoda → Settings → AI → Personas. | workspace default |

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Usage

### Run directly

```bash
API_TOKEN=your-token python -m secoda_analysis
```

### Cursor integration

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "secoda-analysis": {
      "command": "python",
      "args": ["-m", "secoda_analysis"],
      "cwd": "/absolute/path/to/secoda-analysis-mcp",
      "env": {
        "API_TOKEN": "your-secoda-api-token",
        "API_URL": "https://app.secoda.co/api/v1/"
      }
    }
  }
}
```

### Claude Desktop integration

Add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "secoda-analysis": {
      "command": "python",
      "args": ["-m", "secoda_analysis"],
      "cwd": "/absolute/path/to/secoda-analysis-mcp",
      "env": {
        "API_TOKEN": "your-secoda-api-token"
      }
    }
  }
}
```

## Example workflows

### Ask a business question
```
ai_chat(prompt="How is Gross Margin calculated and what tables does it use?")
```

### Find a table and explore its schema
```
# 1. Find the table
search_data_assets(query="order lines")

# 2. Get full details (columns, description, tags)
get_resource(resource_id="<id-from-search>", truncate_length=None)
```

### Understand data lineage
```
# Find the entity first
search_data_assets(query="my_important_table")

# Then trace its lineage
entity_lineage(entity_id="<id-from-search>")
```

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.

---

## Development

### Setup

Clone the repo and install all dependencies (including dev tools) with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/mbrummerstedt/secoda-analysis-mcp.git
cd secoda-analysis-mcp
uv sync --extra dev
```

Copy `.env.example` to `.env` and fill in your credentials:

```bash
cp .env.example .env
```

### Project structure

```
secoda-analysis-mcp/
├── src/
│   └── secoda_analysis/        # Main package
│       ├── __init__.py
│       ├── __main__.py         # python -m secoda_analysis entrypoint
│       ├── server.py           # FastMCP server setup and tool registration
│       ├── prompt.py           # MCP system prompt (tool guidance for the LLM)
│       ├── core/
│       │   ├── client.py       # HTTP client with retry logic
│       │   ├── config.py       # Environment variable configuration
│       │   └── models.py       # Pydantic models (filter/sort validation)
│       └── tools/
│           ├── ai_chat.py      # AI chat tool (submit + poll)
│           ├── collections.py  # list_collections, get_collection
│           ├── entity.py       # retrieve_entity, entity_lineage, glossary
│           ├── questions.py    # list_questions, get_question
│           ├── resources.py    # list_resources, get_resource
│           └── search.py       # search_data_assets, search_documentation
├── tests/
│   ├── conftest.py             # Root fixtures (env var defaults)
│   ├── mock/                   # Unit tests — all HTTP calls mocked
│   │   ├── conftest.py         # Shared mock fixtures and response payloads
│   │   ├── test_client.py
│   │   ├── test_models.py
│   │   ├── test_prompt.py
│   │   ├── test_tools_ai_chat.py
│   │   ├── test_tools_collections.py
│   │   ├── test_tools_entity.py
│   │   ├── test_tools_questions.py
│   │   ├── test_tools_resources.py
│   │   └── test_tools_search.py
│   └── integration/            # Integration tests — hit the real Secoda API
│       ├── conftest.py         # Auto-skip when API_TOKEN is not set
│       ├── test_ai_chat.py
│       ├── test_collections.py
│       ├── test_entity.py
│       ├── test_questions.py
│       ├── test_resources.py
│       └── test_search.py
├── pyproject.toml
├── .env.example
└── .python-version
```

### Architecture

```
LLM / MCP client
      │  MCP protocol (stdio)
      ▼
  server.py  ──── registers tools from tools/*.py
      │
      ├── tools calling Secoda AI MCP endpoint
      │     tools/search.py, entity.py
      │           │
      │           └── core/client.py  call_tool()
      │                     │
      │                     └── POST {API_URL}/ai/mcp/tools/call/
      │
      ├── tools making direct REST calls
      │     tools/resources.py, collections.py, questions.py
      │           │
      │           └── core/client.py  _make_request_with_retry()
      │                     │
      │                     └── GET {API_URL}/resource/... etc.
      │
      └── ai_chat tool (submit + poll)
            tools/ai_chat.py
                  │
                  └── POST/GET {base_url}/ai/embedded_prompt/
```

All tools are **read-only** — there are no write, update, or delete operations.

### Running tests

**Mock tests** (no credentials required, fast):

```bash
uv run pytest tests/mock/ -v
```

**Integration tests** (requires a valid `API_TOKEN` in your `.env`):

```bash
uv run pytest tests/integration/ -v
```

> Integration tests hit the live Secoda API. The `ai_chat` tests are slow (30–120s each) as they wait for the AI to respond.

**All tests:**

```bash
uv run pytest -v
```

Integration tests are automatically skipped when `API_TOKEN` is not set.

### Code style

This project uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting, and [mypy](https://mypy.readthedocs.io/) for type checking.

```bash
# Lint
uv run ruff check src/ tests/

# Format
uv run ruff format src/ tests/

# Type check
uv run mypy src/
```
