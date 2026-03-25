from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ..core.client import call_tool

# --------------------------------
# Search Tools
# --------------------------------


def search_data_assets(
    query: Annotated[
        str, Field(description="Search query for finding tables, columns, charts, dashboards")
    ],
    page: Annotated[int, Field(ge=1, description="Page number for pagination")] = 1,
    truncate_length: Annotated[
        Optional[int], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Search for data assets in the catalog.

    Args:
        query: Search query for finding tables, columns, charts, dashboards
        page: Page number for pagination (default: 1)
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        Search results with text fields truncated to specified length

    """
    return call_tool(
        "search_data_assets", {"query": query, "page": page, "truncate_length": truncate_length}
    )


def search_documentation(
    query: Annotated[
        str, Field(description="Search query for finding documents, questions, glossary terms")
    ],
    page: Annotated[int, Field(ge=1, description="Page number for pagination")] = 1,
    truncate_length: Annotated[
        Optional[int], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Search for documentation in the catalog.

    Args:
        query: Search query for finding documents, questions, glossary terms
        page: Page number for pagination (default: 1)
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        Search results with text fields truncated to specified length

    """
    return call_tool(
        "search_documentation", {"query": query, "page": page, "truncate_length": truncate_length}
    )


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all search tools with the MCP server."""
    mcp.tool()(search_data_assets)
    mcp.tool()(search_documentation)
