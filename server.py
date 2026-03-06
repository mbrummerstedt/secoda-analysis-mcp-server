from fastmcp import FastMCP

from prompt import MCP_PROMPT
from tools.search import register_tools as register_search_tools
from tools.entity import register_tools as register_entity_tools
from tools.resources import register_tools as register_resource_tools
from tools.collections import register_tools as register_collection_tools
from tools.questions import register_tools as register_question_tools
from tools.ai_chat import register_tools as register_ai_chat_tools


# --------------------------------
# Initialize MCP Server
# --------------------------------

mcp = FastMCP(
    name="Secoda Analysis",
    instructions=MCP_PROMPT,
)


# --------------------------------
# Register Read-Only Tools
# --------------------------------

# Search tools (semantic search across data assets and documentation)
register_search_tools(mcp)

# Entity and utility tools (retrieve, lineage, glossary, SQL)
register_entity_tools(mcp)

# Resource browsing tools (list + get, read-only)
register_resource_tools(mcp)

# Collection browsing tools (list + get, read-only)
register_collection_tools(mcp)

# Question browsing tools (list + get, read-only)
register_question_tools(mcp)

# AI chat tool (analysis conversations with Secoda AI)
register_ai_chat_tools(mcp)


# --------------------------------
# Run Server
# --------------------------------

if __name__ == "__main__":
    mcp.run()
