"""Unit tests for tools.search functions."""

import json
from unittest.mock import patch

import responses as responses_lib

from secoda_analysis_mcp.tools.search import search_data_assets, search_documentation

TOOL_URL = "https://app.secoda.co/api/v1/ai/mcp/tools/call/"


def _tool_response(text: str) -> dict:
    return {"isError": False, "content": [{"type": "text", "text": text}]}


class TestSearchDataAssets:
    @responses_lib.activate
    def test_basic_search(self):
        responses_lib.add(
            responses_lib.POST, TOOL_URL, json=_tool_response('{"results": []}'), status=200
        )
        result = search_data_assets(query="orders")
        assert "results" in result

    @responses_lib.activate
    def test_passes_query_to_api(self):
        responses_lib.add(
            responses_lib.POST, TOOL_URL, json=_tool_response('{"results": []}'), status=200
        )
        search_data_assets(query="revenue")
        request_body = json.loads(responses_lib.calls[0].request.body)
        assert request_body["arguments"]["query"] == "revenue"

    @responses_lib.activate
    def test_passes_page_to_api(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_data_assets(query="orders", page=2)
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["page"] == 2

    @responses_lib.activate
    def test_default_truncate_length_is_150(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_data_assets(query="orders")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] == 150

    @responses_lib.activate
    def test_truncate_length_none_passes_through(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_data_assets(query="orders", truncate_length=None)
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] is None

    @responses_lib.activate
    def test_calls_correct_tool_name(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_data_assets(query="orders")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["name"] == "search_data_assets"

    @responses_lib.activate
    @patch("secoda_analysis.core.client.time.sleep")
    def test_rate_limit_returns_error(self, mock_sleep):
        for _ in range(3):
            responses_lib.add(responses_lib.POST, TOOL_URL, status=429)
        result = search_data_assets(query="orders")
        data = json.loads(result)
        assert "error" in data


class TestSearchDocumentation:
    @responses_lib.activate
    def test_basic_search(self):
        responses_lib.add(
            responses_lib.POST, TOOL_URL, json=_tool_response('{"results": []}'), status=200
        )
        result = search_documentation(query="GMV")
        assert result is not None

    @responses_lib.activate
    def test_calls_correct_tool_name(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_documentation(query="GMV")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["name"] == "search_documentation"

    @responses_lib.activate
    def test_passes_all_params(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        search_documentation(query="margin", page=3, truncate_length=200)
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["query"] == "margin"
        assert body["arguments"]["page"] == 3
        assert body["arguments"]["truncate_length"] == 200
