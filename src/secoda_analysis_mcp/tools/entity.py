from typing import Annotated, Optional

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from ..core.client import call_tool

# --------------------------------
# Entity and Utility Tools
# --------------------------------


def retrieve_entity(
    entity_id: Annotated[str, Field(description="The ID of the entity to retrieve")],
    truncate_length: Annotated[
        Optional[int],
        Field(
            ge=1,
            description="Maximum characters for text fields in results. Often useful to set to None when you need full descriptions/definitions",
        ),
    ] = 150,
) -> str:
    """Retrieve an entity from the catalog by ID.

    Args:
        entity_id: The ID of the entity to retrieve
        truncate_length: Maximum characters for text fields in results (default: 150).
            Often useful to set to None when you need full descriptions/definitions.

    Returns:
        Entity details with text fields truncated to specified length

    """
    return call_tool(
        "retrieve_entity", {"entity_id": entity_id, "truncate_length": truncate_length}
    )


def entity_lineage(
    entity_id: Annotated[str, Field(description="The ID of the entity to get lineage for")],
    truncate_length: Annotated[
        Optional[int], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Retrieve the upstream and downstream lineage of an entity.

    Args:
        entity_id: The ID of the entity to get lineage for
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        Entity lineage with text fields truncated to specified length

    """
    return call_tool("entity_lineage", {"entity_id": entity_id, "truncate_length": truncate_length})


def glossary(
    truncate_length: Annotated[
        Optional[int], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Retrieve all business term definitions from the workspace glossary.

    Args:
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        Glossary with text fields truncated to specified length

    """
    return call_tool("glossary", {"truncate_length": truncate_length})


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp: FastMCP) -> None:
    """Register all entity and utility tools with the MCP server."""
    mcp.tool()(retrieve_entity)
    mcp.tool()(entity_lineage)
    mcp.tool()(glossary)
