import json
import time
from typing import Any, Dict, Optional

import requests

from .config import API_TOKEN, API_URL

# --------------------------------
# Helper Functions
# --------------------------------


def _make_request_with_retry(
    url: str, headers: dict, params: Optional[dict] = None
) -> requests.Response:
    """Make a GET request with automatic retry on rate limit.

    Args:
        url: The full URL to request
        headers: Request headers
        params: Optional query parameters

    Returns:
        requests.Response object

    """
    max_attempts = 3
    backoff_delays = [60, 120]

    for attempt in range(max_attempts):
        try:
            response = requests.get(url, headers=headers, params=params, timeout=(30, 120))

            if response.status_code == 429:
                if attempt < max_attempts - 1:
                    time.sleep(backoff_delays[attempt])
                    continue

            return response
        except requests.Timeout:
            if attempt < max_attempts - 1:
                continue
            raise
        except requests.RequestException:
            if attempt < max_attempts - 1:
                continue
            raise

    return response  # type: ignore[return-value]  # unreachable but satisfies type checker


def _truncate_response(data: Any, max_length: Optional[int]) -> Any:
    """Recursively truncate string values in a data structure.

    Args:
        data: The data structure (dict, list, or primitive)
        max_length: Maximum length for string values (None = no truncation)

    Returns:
        Data structure with truncated strings

    """
    if max_length is None:
        return data

    if isinstance(data, dict):
        return {key: _truncate_response(value, max_length) for key, value in data.items()}
    if isinstance(data, list):
        return [_truncate_response(item, max_length) for item in data]
    if isinstance(data, str) and len(data) > max_length:
        return data[:max_length] + "..."
    return data


# --------------------------------
# API Client Functions
# --------------------------------


def call_tool(tool_name: str, args: dict) -> str:
    """Call a tool via the Secoda AI MCP endpoint with automatic retry on rate limit."""
    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"

    max_attempts = 3
    backoff_delays = [60, 120]

    for attempt in range(max_attempts):
        try:
            response = requests.post(
                f"{api_url}ai/mcp/tools/call/",
                headers={
                    "Authorization": f"Bearer {API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": tool_name,
                    "arguments": args,
                },
                timeout=(30, 120),
            )

            if response.status_code == 429:
                if attempt < max_attempts - 1:
                    time.sleep(backoff_delays[attempt])
                    continue
                else:
                    return json.dumps(
                        {
                            "error": "Rate limit exceeded after 2 retries. Please wait before trying again."
                        }
                    )

            response.raise_for_status()

            result = response.json()

            if result.get("isError"):
                return f"Error: {result.get('content', 'Unknown error')}"

            if "content" in result and isinstance(result["content"], list):
                for item in result["content"]:
                    if item.get("type") == "text" and "text" in item:
                        return str(item["text"])

            return json.dumps(result, indent=2)

        except requests.Timeout:
            if attempt < max_attempts - 1:
                continue
            return json.dumps(
                {
                    "error": (
                        f"Request timed out after {max_attempts} attempts. "
                        "The Secoda API may be slow or unavailable. Try a more specific search query."
                    )
                }
            )
        except requests.HTTPError as e:
            if e.response.status_code != 429:
                raise
        except requests.RequestException as e:
            if attempt < max_attempts - 1:
                continue
            return json.dumps({"error": f"Request failed: {str(e)}"})

    return json.dumps(
        {"error": "Rate limit exceeded after 2 retries. Please wait before trying again."}
    )


def _make_resource_request(
    method: str, endpoint: str, data: Optional[Dict[str, Any]] = None
) -> str:
    """Make a direct request to the Secoda resource API with automatic retry on rate limit.

    Args:
        method: HTTP method (GET, POST, PATCH, DELETE)
        endpoint: API endpoint path (e.g., 'resource/all/bulk_update/')
        data: Optional request body data

    Returns:
        Response JSON as string

    Raises:
        requests.HTTPError: If the request fails

    """
    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"
    url = f"{api_url}{endpoint}"

    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    max_attempts = 3
    backoff_delays = [60, 120]

    for attempt in range(max_attempts):
        try:
            response = requests.request(
                method=method, url=url, headers=headers, json=data, timeout=(30, 120)
            )

            if response.status_code == 429:
                if attempt < max_attempts - 1:
                    time.sleep(backoff_delays[attempt])
                    continue
                else:
                    return json.dumps(
                        {
                            "error": "Rate limit exceeded after 2 retries. Please wait before trying again."
                        }
                    )

            if response.status_code == 403:
                return json.dumps(
                    {
                        "error": (
                            "Permission denied. You do not have permission to perform this operation. "
                            "Check that your API token has the necessary permissions in Secoda."
                        )
                    }
                )
            if response.status_code == 404:
                return json.dumps(
                    {
                        "error": "Resource not found. The specified resource ID does not exist in Secoda."
                    }
                )
            if response.status_code >= 400:
                try:
                    error_detail = response.json()
                    return json.dumps({"error": f"Request failed: {error_detail}"})
                except Exception:
                    return json.dumps(
                        {
                            "error": f"Request failed with status {response.status_code}: {response.text}"
                        }
                    )

            try:
                return json.dumps(response.json())
            except Exception:
                return json.dumps({"success": True, "message": response.text})

        except requests.Timeout:
            if attempt < max_attempts - 1:
                continue
            return json.dumps(
                {
                    "error": (
                        f"Request timed out after {max_attempts} attempts. "
                        "The Secoda API may be slow or unavailable."
                    )
                }
            )
        except requests.RequestException as e:
            if attempt < max_attempts - 1:
                continue
            return json.dumps({"error": f"Request failed: {str(e)}"})

    return json.dumps(
        {"error": "Rate limit exceeded after 2 retries. Please wait before trying again."}
    )
