# Secoda Analysis MCP Server

A **read-only** [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for exploring and analysing your [Secoda](https://www.secoda.co) data catalog. Designed for business users who need to discover data, look up metric definitions, run SQL queries, and understand data lineage — without any risk of modifying the catalog.

Built to work alongside the [Power BI MCP server](https://github.com/microsoft/power-bi-mcp) for end-to-end data discovery across your warehouse and reports.

## Features

- **Zero write access** — completely safe to use; nothing in Secoda can be changed
- **AI chat** — ask Secoda's AI natural language questions about your data
- **Semantic search** — find tables, columns, dashboards, and documentation by keyword
- **Glossary & definitions** — browse business term definitions
- **Data lineage** — trace where data comes from and where it flows downstream
- **SQL execution** — run ad-hoc queries against your data warehouse via Secoda
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
| `run_sql` | Execute a SQL query against the data warehouse via Secoda |
| `list_collections` | Browse organised groups of resources |
| `get_collection` | Get details of a specific collection |
| `list_questions` | Browse previously asked and answered Q&A threads |
| `get_question` | Read a specific question and its answer |

## Requirements

- Python 3.8+
- A Secoda account with API access
- A Secoda API token (read permissions are sufficient)

## Installation

```bash
git clone https://github.com/martinbrummerstedt/secoda-analysis-mcp-server.git
cd secoda-analysis-mcp-server
pip install -r requirements.txt
```

## Configuration

The server is configured via environment variables:

| Variable | Description | Default |
|----------|-------------|---------|
| `API_TOKEN` | Your Secoda API token (required) | — |
| `API_URL` | Secoda API base URL | `https://app.secoda.co/api/v1/` |

Copy `.env.example` to `.env` and fill in your values:

```bash
cp .env.example .env
```

## Usage

### Run directly

```bash
API_TOKEN=your-token python server.py
```

### Cursor integration

Add to your `.cursor/mcp.json`:

```json
{
  "mcpServers": {
    "secoda-analysis": {
      "command": "python",
      "args": ["/absolute/path/to/secoda-analysis-mcp-server/server.py"],
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
      "args": ["/absolute/path/to/secoda-analysis-mcp-server/server.py"],
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

### Find a table and query it
```
# 1. Find the table
search_data_assets(query="order lines")

# 2. Get full details
get_resource(resource_id="<id-from-search>", truncate_length=None)

# 3. Run a query (integration_id found in Secoda → Settings → Integrations)
run_sql(
    query="SELECT date, COUNT(*) AS orders FROM your_schema.order_lines WHERE date >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY) GROUP BY 1 ORDER BY 1 DESC LIMIT 7",
    integration_id="your-integration-id",
    truncate_length=None
)
```

### Understand data lineage
```
# Find the entity first
search_data_assets(query="my_important_table")

# Then trace its lineage
entity_lineage(entity_id="<id-from-search>")
```

### Combine with Power BI MCP
```
# 1. Get the metric definition from Secoda
ai_chat(prompt="How is Average Order Value calculated?")

# 2. Find the underlying table
search_data_assets(query="fct_order_lines")

# 3. Switch to Power BI MCP to find where it's used in reports
#    list_workspaces → list_datasets → list_measures → execute_dax
```

## Finding your integration_id for run_sql

The `run_sql` tool requires a Secoda `integration_id` to know which warehouse to query. To find it:

1. Go to your Secoda workspace
2. Navigate to **Settings → Integrations**
3. Click on your data warehouse integration (e.g. BigQuery, Snowflake)
4. Copy the UUID from the URL or the integration details page

## License

Apache License 2.0 — see [LICENSE](LICENSE) for details.
