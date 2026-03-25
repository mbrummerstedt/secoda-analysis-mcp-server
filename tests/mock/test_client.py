"""Unit tests for core.client functions."""

import json
from unittest.mock import patch

import responses as responses_lib

from secoda_analysis_mcp.core.client import _make_resource_request, _truncate_response, call_tool

TOOL_URL = "https://app.secoda.co/api/v1/ai/mcp/tools/call/"
RESOURCE_URL = "https://app.secoda.co/api/v1/resource/all/res-001"


# ---------------------------------------------------------------------------
# _truncate_response
# ---------------------------------------------------------------------------


class TestTruncateResponse:
    def test_no_truncation_when_max_length_none(self):
        data = {"key": "a" * 500}
        assert _truncate_response(data, None) == data

    def test_truncates_long_string(self):
        result = _truncate_response("a" * 200, 100)
        assert len(result) == 103  # 100 chars + "..."
        assert result.endswith("...")

    def test_does_not_truncate_short_string(self):
        assert _truncate_response("short", 100) == "short"

    def test_truncates_nested_dict(self):
        data = {"desc": "x" * 200, "count": 5}
        result = _truncate_response(data, 50)
        assert result["desc"].endswith("...")
        assert result["count"] == 5

    def test_truncates_nested_list(self):
        data = ["a" * 200, "b" * 10]
        result = _truncate_response(data, 50)
        assert result[0].endswith("...")
        assert result[1] == "b" * 10

    def test_handles_deeply_nested_structure(self):
        data = {"level1": {"level2": {"text": "x" * 200}}}
        result = _truncate_response(data, 50)
        assert result["level1"]["level2"]["text"].endswith("...")

    def test_passes_through_non_string_values(self):
        data = {"num": 42, "flag": True, "nothing": None}
        result = _truncate_response(data, 10)
        assert result == data


# ---------------------------------------------------------------------------
# call_tool
# ---------------------------------------------------------------------------


class TestCallTool:
    @responses_lib.activate
    def test_successful_call_returns_text(self, mcp_tool_response):
        responses_lib.add(
            responses_lib.POST,
            TOOL_URL,
            json=mcp_tool_response,
            status=200,
        )
        result = call_tool("search_data_assets", {"query": "orders"})
        assert "results" in result
        assert "orders" in result

    @responses_lib.activate
    def test_error_response_returns_error_string(self):
        responses_lib.add(
            responses_lib.POST,
            TOOL_URL,
            json={"isError": True, "content": "Something went wrong"},
            status=200,
        )
        result = call_tool("search_data_assets", {"query": "x"})
        assert result.startswith("Error:")

    @responses_lib.activate
    @patch("secoda_analysis.core.client.time.sleep")
    def test_rate_limit_exhausted_returns_error_json(self, mock_sleep):
        for _ in range(3):
            responses_lib.add(responses_lib.POST, TOOL_URL, status=429)
        result = call_tool("search_data_assets", {"query": "x"})
        data = json.loads(result)
        assert "error" in data
        assert "Rate limit" in data["error"]

    @responses_lib.activate
    def test_fallback_json_response(self):
        """When content array is missing, returns full JSON."""
        responses_lib.add(
            responses_lib.POST,
            TOOL_URL,
            json={"unexpected": "structure"},
            status=200,
        )
        result = call_tool("search_data_assets", {"query": "x"})
        data = json.loads(result)
        assert data["unexpected"] == "structure"


# ---------------------------------------------------------------------------
# _make_resource_request
# ---------------------------------------------------------------------------


class TestMakeResourceRequest:
    @responses_lib.activate
    def test_successful_get(self, resource_detail_response):
        responses_lib.add(
            responses_lib.GET,
            RESOURCE_URL,
            json=resource_detail_response,
            status=200,
        )
        result = _make_resource_request("GET", "resource/all/res-001")
        data = json.loads(result)
        assert data["id"] == "res-001"

    @responses_lib.activate
    def test_404_returns_not_found_error(self):
        responses_lib.add(responses_lib.GET, RESOURCE_URL, status=404)
        result = _make_resource_request("GET", "resource/all/res-001")
        data = json.loads(result)
        assert "not found" in data["error"].lower()

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, RESOURCE_URL, status=403)
        result = _make_resource_request("GET", "resource/all/res-001")
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    @patch("secoda_analysis.core.client.time.sleep")
    def test_rate_limit_exhausted_returns_error(self, mock_sleep):
        for _ in range(3):
            responses_lib.add(responses_lib.GET, RESOURCE_URL, status=429)
        result = _make_resource_request("GET", "resource/all/res-001")
        data = json.loads(result)
        assert "Rate limit" in data["error"]

    @responses_lib.activate
    def test_500_returns_generic_error(self):
        responses_lib.add(
            responses_lib.GET,
            RESOURCE_URL,
            json={"detail": "Internal server error"},
            status=500,
        )
        result = _make_resource_request("GET", "resource/all/res-001")
        data = json.loads(result)
        assert "error" in data
