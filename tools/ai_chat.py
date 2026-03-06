import json
import time
from typing import Annotated, Optional

import requests
from pydantic import Field

from core.config import API_TOKEN, EAPI_BASE_URL


# --------------------------------
# Internal Helpers
# --------------------------------


def _submit_prompt(
    prompt: str,
    parent: Optional[str] = None,
    persona_id: Optional[str] = None,
) -> dict:
    """
    POST to /ai/embedded_prompt/ and return the response dict.

    Raises:
        RuntimeError: If the request fails or no chat ID is returned.
    """
    url = f"{EAPI_BASE_URL}/ai/embedded_prompt/"
    payload = {
        "prompt": prompt,
        "parent": parent,
        "user_generated": True,
    }
    if persona_id is not None:
        payload["persona_id"] = persona_id

    max_attempts = 3
    backoff_delays = [60, 120]

    for attempt in range(max_attempts):
        try:
            response = requests.post(
                url,
                headers={
                    "Authorization": f"Bearer {API_TOKEN}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=(30, 120),
            )

            if response.status_code == 429:
                if attempt < max_attempts - 1:
                    time.sleep(backoff_delays[attempt])
                    continue
                raise RuntimeError("Rate limit exceeded after retries.")

            if response.status_code == 403:
                raise RuntimeError(
                    "Permission denied. Check that your API token has permission to use the AI chat endpoint."
                )

            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                raise RuntimeError(f"Request failed with status {response.status_code}: {detail}")

            data = response.json()
            if not data.get("id"):
                raise RuntimeError(f"No chat ID returned from Secoda AI: {data}")
            return data

        except requests.Timeout:
            if attempt < max_attempts - 1:
                continue
            raise RuntimeError("Request timed out while submitting AI chat prompt.")
        except requests.RequestException as exc:
            if attempt < max_attempts - 1:
                continue
            raise RuntimeError(f"Request failed: {exc}") from exc

    raise RuntimeError("Failed to submit prompt after all retries.")


def _poll_for_completion(
    chat_id: str,
    poll_interval: float = 10.0,
    timeout: float = 360.0,
) -> dict:
    """
    Poll GET /ai/embedded_prompt/{chat_id}/ until status is 'completed' or 'failed'.

    Returns:
        The completed response dict.

    Raises:
        RuntimeError: On failure status, timeout, or request error.
    """
    url = f"{EAPI_BASE_URL}/ai/embedded_prompt/{chat_id}/"
    headers = {
        "Authorization": f"Bearer {API_TOKEN}",
        "Content-Type": "application/json",
    }

    deadline = time.monotonic() + timeout

    while True:
        if time.monotonic() >= deadline:
            raise RuntimeError(
                f"AI chat timed out after {timeout}s waiting for completion of chat {chat_id}."
            )

        try:
            response = requests.get(url, headers=headers, timeout=(30, 120))

            if response.status_code == 429:
                time.sleep(60)
                continue

            if response.status_code == 404:
                raise RuntimeError(f"Chat ID '{chat_id}' not found.")

            if response.status_code >= 400:
                try:
                    detail = response.json()
                except Exception:
                    detail = response.text
                raise RuntimeError(
                    f"Polling failed with status {response.status_code}: {detail}"
                )

            data = response.json()
            status = data.get("status")

            if status == "completed":
                return data
            if status == "failed":
                raise RuntimeError(f"AI chat task failed for chat {chat_id}.")

        except requests.Timeout:
            pass
        except requests.RequestException as exc:
            raise RuntimeError(f"Polling request failed: {exc}") from exc

        time.sleep(poll_interval)


# --------------------------------
# Public Tool
# --------------------------------


def ai_chat(
    prompt: Annotated[str, Field(description="The message or question to send to the Secoda AI")],
    parent: Annotated[
        Optional[str],
        Field(
            description=(
                "Chat ID of a previous conversation to continue. "
                "Use the chat_id returned from a previous ai_chat call to maintain conversation context."
            )
        ),
    ] = None,
    persona_id: Annotated[
        Optional[str],
        Field(
            description=(
                "Persona ID to use for the AI chat. "
                "Leave blank to use the default persona."
            )
        ),
    ] = None,
    poll_interval_seconds: Annotated[
        float,
        Field(ge=1, description="Seconds between polling attempts while waiting for the AI to respond (default: 10)"),
    ] = 10.0,
    timeout_seconds: Annotated[
        float,
        Field(ge=10, description="Maximum seconds to wait for the AI to complete the response (default: 360)"),
    ] = 360.0,
) -> str:
    """
    Start an AI chat session in Secoda and wait for the response.

    Submits a prompt to the Secoda embedded AI endpoint and polls until the
    response is complete. Returns the AI's response text along with the chat ID,
    which can be passed as `parent` in a follow-up call to continue the conversation.

    Args:
        prompt: The message or question to send to the Secoda AI.
        parent: Chat ID of a previous conversation to continue (optional).
            Pass the chat_id from a previous ai_chat response to maintain context.
        persona_id: Persona ID to use for the AI chat (optional).
            Leave blank to use the default persona.
        poll_interval_seconds: Seconds between polling attempts (default: 10).
        timeout_seconds: Maximum seconds to wait for completion (default: 360).

    Returns:
        JSON with keys:
            - success: true
            - chat_id: The ID of this chat (use as `parent` in follow-up calls)
            - status: "completed"
            - response_content: The AI's response text

    Example:
        # Start a new conversation
        ai_chat(prompt="How do we handle price reductions in GMV calculations?")

        # Continue a previous conversation
        ai_chat(
            prompt="Can you elaborate on the discount logic?",
            parent="0d53d57b-d1ef-4fc2-bc50-fd3fba2fea93"
        )

    Error handling:
        - 403: Permission denied - check API token has AI chat permissions
        - 429: Rate limit exceeded - tool retries automatically
        - Timeout: Increase timeout_seconds if the AI takes longer than expected
    """
    try:
        submitted = _submit_prompt(prompt=prompt, parent=parent, persona_id=persona_id)
    except RuntimeError as exc:
        return json.dumps({"error": str(exc)})

    chat_id = submitted["id"]

    try:
        completed = _poll_for_completion(
            chat_id=chat_id,
            poll_interval=poll_interval_seconds,
            timeout=timeout_seconds,
        )
    except RuntimeError as exc:
        return json.dumps({"error": str(exc), "chat_id": chat_id})

    response_content = None
    resp = completed.get("response")
    if isinstance(resp, dict):
        response_content = resp.get("content")
    if response_content and isinstance(response_content, str):
        response_content = response_content.strip()

    return json.dumps(
        {
            "success": True,
            "chat_id": chat_id,
            "status": "completed",
            "response_content": response_content,
        },
        indent=2,
    )


# --------------------------------
# Registration
# --------------------------------


def register_tools(mcp):
    """Register AI chat tools with the MCP server."""
    mcp.tool(
        annotations={
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        }
    )(ai_chat)
