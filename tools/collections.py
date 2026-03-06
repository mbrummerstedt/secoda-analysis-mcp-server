import json
from typing import Annotated, Optional

from pydantic import Field

from core.client import _make_request_with_retry, _truncate_response
from core.config import API_TOKEN, API_URL


# --------------------------------
# Collection Read Tools
# --------------------------------


def list_collections(
    title: Annotated[Optional[str], Field(description="Filter collections by title (optional)")] = None,
    page: Annotated[float, Field(ge=1, description="Page number for pagination")] = 1,
    truncate_length: Annotated[
        Optional[float], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """List all collections in the workspace.

    Collections are organized groups of related resources (tables, dashboards, documents).
    Use this to browse what topic areas and resource groups exist.

    Args:
        title: Filter collections by title (optional)
        page: Page number for pagination (default: 1)
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        List of collections with text fields truncated to specified length

    Example:
        list_collections(title="Customer")
        list_collections(page=2)
    """
    page = int(page)
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"
    query_params = {"page": page}
    if title is not None:
        query_params["title"] = title

    response = _make_request_with_retry(
        f"{api_url}collection/collections",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
        params=query_params,
    )

    if response.status_code == 429:
        return json.dumps(
            {"error": "Rate limit exceeded after 2 retries. Please wait before trying again."}
        )
    elif response.status_code == 403:
        return json.dumps(
            {"error": "Permission denied. Check that your API token has permission to list collections."}
        )
    elif response.status_code >= 400:
        try:
            error_detail = response.json()
            return json.dumps({"error": f"Request failed: {error_detail}"})
        except Exception:
            return json.dumps(
                {"error": f"Request failed with status {response.status_code}: {response.text}"}
            )

    try:
        collections_data = response.json()
        truncated_data = _truncate_response(collections_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


def get_collection(
    collection_id: Annotated[str, Field(description="The unique identifier of the collection")],
    truncate_length: Annotated[
        Optional[float], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Retrieve a specific collection by its ID.

    Use this to get full details about a collection after finding it via list_collections.

    Args:
        collection_id: The unique identifier of the collection
        truncate_length: Maximum characters for text fields in results (default: 150).
            Set to None for full descriptions.

    Returns:
        Collection details with text fields truncated to specified length

    Example:
        get_collection(collection_id="collection-123")
    """
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"

    response = _make_request_with_retry(
        f"{api_url}collection/collections/{collection_id}",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
    )

    if response.status_code == 429:
        return json.dumps(
            {"error": "Rate limit exceeded after 2 retries. Please wait before trying again."}
        )
    elif response.status_code == 404:
        return json.dumps(
            {"error": f"Collection not found. The collection ID '{collection_id}' does not exist."}
        )
    elif response.status_code == 403:
        return json.dumps(
            {"error": "Permission denied. Check that your API token has permission to access collections."}
        )
    elif response.status_code >= 400:
        try:
            error_detail = response.json()
            return json.dumps({"error": f"Request failed: {error_detail}"})
        except Exception:
            return json.dumps(
                {"error": f"Request failed with status {response.status_code}: {response.text}"}
            )

    try:
        collection_data = response.json()
        truncated_data = _truncate_response(collection_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp):
    """Register read-only collection tools with the MCP server."""
    mcp.tool()(list_collections)
    mcp.tool()(get_collection)
