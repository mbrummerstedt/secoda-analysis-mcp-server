import json
from typing import Annotated, Optional

from pydantic import Field

from core.client import _make_request_with_retry, _truncate_response
from core.config import API_TOKEN, API_URL


# --------------------------------
# Question Read Tools
# --------------------------------


def list_questions(
    page: Annotated[float, Field(ge=1, description="Page number for pagination")] = 1,
    truncate_length: Annotated[
        Optional[float], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """List all questions in the workspace.

    Questions in Secoda represent data consumer inquiries that have been asked and
    answered by the data team. Use this to find existing answers before asking
    a new question.

    Args:
        page: Page number for pagination (default: 1)
        truncate_length: Maximum characters for text fields in results (default: 150)

    Returns:
        List of questions with text fields truncated to specified length
    """
    page = int(page)
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"

    response = _make_request_with_retry(
        f"{api_url}question/questions",
        headers={
            "Authorization": f"Bearer {API_TOKEN}",
            "Content-Type": "application/json",
        },
        params={"page": page},
    )

    if response.status_code == 429:
        return json.dumps(
            {"error": "Rate limit exceeded after 2 retries. Please wait before trying again."}
        )
    elif response.status_code == 403:
        return json.dumps(
            {"error": "Permission denied. Check that your API token has permission to list questions."}
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
        questions_data = response.json()
        truncated_data = _truncate_response(questions_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


def get_question(
    question_id: Annotated[str, Field(description="The unique identifier of the question")],
    truncate_length: Annotated[
        Optional[float], Field(ge=1, description="Maximum characters for text fields in results")
    ] = 150,
) -> str:
    """Retrieve a specific question and its answer by ID.

    Use this to read the full content of a question and any accepted answers after
    finding it via list_questions or search_documentation.

    Args:
        question_id: The unique identifier of the question
        truncate_length: Maximum characters for text fields in results (default: 150).
            Set to None to read the full question and answer text.

    Returns:
        Question details including title, description, and answers
    """
    if truncate_length is not None:
        truncate_length = int(truncate_length)

    api_url = API_URL if API_URL.endswith("/") else f"{API_URL}/"

    response = _make_request_with_retry(
        f"{api_url}question/questions/{question_id}",
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
            {"error": f"Question not found. The question ID '{question_id}' does not exist."}
        )
    elif response.status_code == 403:
        return json.dumps(
            {"error": "Permission denied. Check that your API token has permission to access questions."}
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
        question_data = response.json()
        truncated_data = _truncate_response(question_data, truncate_length)
        return json.dumps(truncated_data, indent=2)
    except Exception as e:
        return json.dumps({"error": f"Failed to parse response: {str(e)}"})


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp):
    """Register read-only question tools with the MCP server."""
    mcp.tool()(list_questions)
    mcp.tool()(get_question)
