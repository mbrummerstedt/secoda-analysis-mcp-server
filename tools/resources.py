import json
from typing import Annotated, Optional

from pydantic import Field

from core.client import _make_request_with_retry, _truncate_response
from core.config import API_TOKEN, API_URL


# --------------------------------
# Resource Read Tools
# --------------------------------


def list_resources(
    filter: Annotated[
        Optional[dict],
        Field(
            description="""Filter dictionary for filtering resources. Can be either a field filter or logical filter.

Field filter example: {"operator": "exact", "field": "title", "value": "my_table"}
Logical filter example: {"operator": "and", "operands": [{"operator": "exact", "field": "native_type", "value": "table"}, {"operator": "contains", "field": "title", "value": "order"}]}

PARENT/CHILD RELATIONSHIPS (COMMON PATTERN):
- Filter by parent_id to find ALL columns of a table: {"operator": "exact", "field": "parent_id", "value": "table-id-123"}

Available field operators: "exact", "contains", "in", "is_set"
Available logical operators: "and", "or", "not"
"""
        ),
    ] = None,
    sort: Annotated[
        Optional[dict],
        Field(
            description="""Sort configuration dictionary for ordering results.

Example: {"field": "title", "order": "asc"}
With tie breaker: {"field": "updated_at", "order": "desc", "tie_breaker": {"field": "created_at", "order": "desc"}}
"""
        ),
    ] = None,
    page: Annotated[float, Field(ge=1, description="Page number for pagination")] = 1,
    truncate_length: Annotated[
        Optional[float], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """List catalog resources with advanced filtering capabilities.

    This endpoint provides precise control over resource queries using structured filters.
    Use this when you need exact matching, specific field filtering, or complex queries.

    Args:
        filter: FilterOperand (field or logical) for filtering resources
        sort: SortConfig for ordering results
        page: Page number for pagination (default: 1)
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        Paginated list of resources matching the filter criteria

    Filter Examples:

        # Single condition - title contains
        filter = {"operator": "contains", "field": "title", "value": "order_lines"}

        # Single condition - entity type
        filter = {"operator": "exact", "field": "native_type", "value": "table"}

        # Find all columns of a specific table
        filter = {"operator": "exact", "field": "parent_id", "value": "table-id-123"}

        # Multiple conditions with AND
        filter = {
            "operator": "and",
            "operands": [
                {"operator": "exact", "field": "native_type", "value": "table"},
                {"operator": "contains", "field": "title", "value": "customer"}
            ]
        }

    Sort Examples:

        # Sort by title ascending
        sort = {"field": "title", "order": "asc"}

        # Sort by external_usage descending (most popular first)
        sort = {"field": "external_usage", "order": "desc"}

    """
    page = int(page)
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"
    query_params = {"page": page}

    if filter:
        try:
            from core.models import FilterOperand

            validated_filter = FilterOperand.model_validate(filter)
            query_params["filter"] = json.dumps(validated_filter.model_dump())
        except Exception:
            query_params["filter"] = json.dumps(filter)

    if sort:
        try:
            from core.models import SortConfig

            validated_sort = SortConfig.model_validate(sort)
            query_params["sort"] = json.dumps(validated_sort.model_dump(exclude_none=True))
        except Exception:
            query_params["sort"] = json.dumps(sort)

    response = _make_request_with_retry(
        f"{api_url}resource/catalog",
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
            {"error": "Permission denied. Check that your API token has permission to list resources."}
        )
    elif response.status_code == 400:
        try:
            error_detail = response.json()
            return json.dumps({"error": f"Bad request. Check filter/sort format: {error_detail}"})
        except Exception:
            return json.dumps(
                {"error": f"Bad request with status {response.status_code}: {response.text}"}
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
        resources_data = response.json()
        truncated_data = _truncate_response(resources_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


def get_resource(
    resource_id: Annotated[
        str, Field(description="The unique identifier of the resource to retrieve")
    ],
    truncate_length: Annotated[
        Optional[float],
        Field(
            ge=1,
            description="Maximum characters for text fields in results. Set to None for full descriptions/definitions",
        ),
    ] = 150,
) -> str:
    """Retrieve a specific resource by its ID.

    Use this to get full details of a catalog resource (table, column, view, etc.)
    after finding it through list_resources or search_data_assets.

    Args:
        resource_id: The unique identifier of the resource to retrieve
        truncate_length: Maximum characters for text fields in results (default: 150).
            Set to None when you need full descriptions/definitions.

    Returns:
        Resource details with text fields truncated to specified length

    """
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"

    response = _make_request_with_retry(
        f"{api_url}resource/all/{resource_id}",
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
            {"error": f"Resource not found. The resource ID '{resource_id}' does not exist."}
        )
    elif response.status_code == 403:
        return json.dumps(
            {"error": "Permission denied. Check that your API token has permission to access resources."}
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
        resource_data = response.json()
        truncated_data = _truncate_response(resource_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp):
    """Register read-only resource tools with the MCP server."""
    mcp.tool()(list_resources)
    mcp.tool()(get_resource)
