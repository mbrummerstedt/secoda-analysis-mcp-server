"""Unit tests for tools.ai_chat functions."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import responses as responses_lib

from secoda_analysis.tools.ai_chat import (
    _RateLimited,
    _poll_for_completion,
    _single_poll,
    _submit_prompt,
    ai_chat,
)

SUBMIT_URL = "https://app.secoda.co/ai/embedded_prompt/"
POLL_URL = "https://app.secoda.co/ai/embedded_prompt/chat-abc123/"


@pytest.fixture
def mock_ctx():
    ctx = MagicMock()
    ctx.report_progress = AsyncMock()
    return ctx


class TestSubmitPrompt:
    @responses_lib.activate
    def test_successful_submit_returns_dict_with_id(self, ai_chat_submit_response):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        result = _submit_prompt(prompt="What is GMV?")
        assert result["id"] == "chat-abc123"

    @responses_lib.activate
    def test_persona_id_included_when_set(self, ai_chat_submit_response):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        _submit_prompt(prompt="Hello", persona_id="persona-xyz")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["persona_id"] == "persona-xyz"

    @responses_lib.activate
    def test_persona_id_omitted_when_none(self, ai_chat_submit_response):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        _submit_prompt(prompt="Hello", persona_id=None)
        body = json.loads(responses_lib.calls[0].request.body)
        assert "persona_id" not in body

    @responses_lib.activate
    def test_parent_included_when_set(self, ai_chat_submit_response):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        _submit_prompt(prompt="Follow up", parent="prev-chat-id")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["parent"] == "prev-chat-id"

    @responses_lib.activate
    def test_403_raises_runtime_error(self):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, status=403)
        with pytest.raises(RuntimeError, match="Permission denied"):
            _submit_prompt(prompt="Hello")

    @responses_lib.activate
    def test_no_id_in_response_raises_runtime_error(self):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json={"status": "pending"}, status=200)
        with pytest.raises(RuntimeError, match="No chat ID"):
            _submit_prompt(prompt="Hello")

    @responses_lib.activate
    @patch("secoda_analysis.tools.ai_chat.time.sleep")
    def test_rate_limit_exhausted_raises_runtime_error(self, mock_sleep):
        for _ in range(3):
            responses_lib.add(responses_lib.POST, SUBMIT_URL, status=429)
        with pytest.raises(RuntimeError, match="Rate limit"):
            _submit_prompt(prompt="Hello")


class TestPollForCompletion:
    @responses_lib.activate
    def test_returns_completed_response(self, ai_chat_completed_response):
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        result = _poll_for_completion("chat-abc123", poll_interval=0.01, timeout=5.0)
        assert result["status"] == "completed"

    @responses_lib.activate
    def test_polls_until_completed(self, ai_chat_completed_response):
        responses_lib.add(
            responses_lib.GET, POLL_URL, json={"id": "chat-abc123", "status": "pending"}, status=200
        )
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        result = _poll_for_completion("chat-abc123", poll_interval=0.01, timeout=5.0)
        assert result["status"] == "completed"
        assert len(responses_lib.calls) == 2

    @responses_lib.activate
    def test_failed_status_raises_runtime_error(self):
        responses_lib.add(
            responses_lib.GET, POLL_URL, json={"id": "chat-abc123", "status": "failed"}, status=200
        )
        with pytest.raises(RuntimeError, match="failed"):
            _poll_for_completion("chat-abc123", poll_interval=0.01, timeout=5.0)

    @responses_lib.activate
    def test_404_raises_runtime_error(self):
        responses_lib.add(responses_lib.GET, POLL_URL, status=404)
        with pytest.raises(RuntimeError, match="not found"):
            _poll_for_completion("chat-abc123", poll_interval=0.01, timeout=5.0)

    @responses_lib.activate
    def test_timeout_raises_runtime_error(self):
        responses_lib.add(
            responses_lib.GET,
            POLL_URL,
            json={"id": "chat-abc123", "status": "pending"},
            status=200,
        )
        with pytest.raises(RuntimeError, match="timed out"):
            _poll_for_completion("chat-abc123", poll_interval=0.01, timeout=0.05)


class TestSinglePoll:
    @responses_lib.activate
    def test_returns_dict_on_success(self, ai_chat_completed_response):
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        result = _single_poll("chat-abc123")
        assert result is not None
        assert result["status"] == "completed"

    @responses_lib.activate
    def test_returns_pending_dict(self):
        responses_lib.add(
            responses_lib.GET,
            POLL_URL,
            json={"id": "chat-abc123", "status": "pending"},
            status=200,
        )
        result = _single_poll("chat-abc123")
        assert result is not None
        assert result["status"] == "pending"

    @responses_lib.activate
    def test_raises_rate_limited_on_429(self):
        responses_lib.add(responses_lib.GET, POLL_URL, status=429)
        with pytest.raises(_RateLimited):
            _single_poll("chat-abc123")

    @responses_lib.activate
    def test_raises_runtime_error_on_404(self):
        responses_lib.add(responses_lib.GET, POLL_URL, status=404)
        with pytest.raises(RuntimeError, match="not found"):
            _single_poll("chat-abc123")

    @responses_lib.activate
    def test_raises_runtime_error_on_5xx(self):
        responses_lib.add(responses_lib.GET, POLL_URL, status=500, body="server error")
        with pytest.raises(RuntimeError, match="Polling failed"):
            _single_poll("chat-abc123")

    def test_returns_none_on_timeout(self):
        import requests

        with patch("requests.get", side_effect=requests.Timeout):
            result = _single_poll("chat-abc123")
        assert result is None


class TestAiChat:
    @responses_lib.activate
    async def test_successful_chat_returns_json(
        self, mock_ctx, ai_chat_submit_response, ai_chat_completed_response
    ):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        result = await ai_chat(
            prompt="What is GMV?", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
        )
        data = json.loads(result)
        assert data["success"] is True
        assert data["chat_id"] == "chat-abc123"
        assert data["status"] == "completed"
        assert "GMV" in data["response_content"]

    @responses_lib.activate
    async def test_submit_error_returns_error_json(self, mock_ctx):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, status=403)
        result = await ai_chat(
            prompt="Hello", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
        )
        data = json.loads(result)
        assert "error" in data

    @responses_lib.activate
    async def test_poll_error_returns_error_json_with_chat_id(
        self, mock_ctx, ai_chat_submit_response
    ):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        responses_lib.add(
            responses_lib.GET,
            POLL_URL,
            json={"id": "chat-abc123", "status": "failed"},
            status=200,
        )
        result = await ai_chat(
            prompt="Hello", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
        )
        data = json.loads(result)
        assert "error" in data
        assert data["chat_id"] == "chat-abc123"

    @responses_lib.activate
    async def test_progress_reported_on_each_poll(
        self, mock_ctx, ai_chat_submit_response, ai_chat_completed_response
    ):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        responses_lib.add(
            responses_lib.GET, POLL_URL, json={"id": "chat-abc123", "status": "pending"}, status=200
        )
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        await ai_chat(
            prompt="Hello", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
        )
        assert mock_ctx.report_progress.call_count >= 2
        call_kwargs = mock_ctx.report_progress.call_args_list[0].kwargs
        assert "progress" in call_kwargs
        assert "total" in call_kwargs
        assert "message" in call_kwargs

    @responses_lib.activate
    async def test_rate_limit_on_poll_backs_off_then_completes(
        self, mock_ctx, ai_chat_submit_response, ai_chat_completed_response
    ):
        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        responses_lib.add(responses_lib.GET, POLL_URL, status=429)
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        with patch("secoda_analysis.tools.ai_chat.asyncio.sleep") as mock_sleep:
            mock_sleep.return_value = None
            result = await ai_chat(
                prompt="Hello", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
            )
        data = json.loads(result)
        assert data["success"] is True
        mock_sleep.assert_any_call(60)

    @responses_lib.activate
    async def test_default_persona_id_from_env(
        self, monkeypatch, mock_ctx, ai_chat_submit_response, ai_chat_completed_response
    ):
        monkeypatch.setenv("AI_PERSONA_ID", "env-persona-123")
        import importlib

        import secoda_analysis.core.config as cfg
        import secoda_analysis.tools.ai_chat as ai_chat_mod

        importlib.reload(cfg)
        importlib.reload(ai_chat_mod)

        responses_lib.add(responses_lib.POST, SUBMIT_URL, json=ai_chat_submit_response, status=200)
        responses_lib.add(responses_lib.GET, POLL_URL, json=ai_chat_completed_response, status=200)
        await ai_chat_mod.ai_chat(
            prompt="Hello", ctx=mock_ctx, poll_interval_seconds=0.01, timeout_seconds=5.0
        )
        body = json.loads(responses_lib.calls[0].request.body)
        assert body.get("persona_id") == "env-persona-123"
