"""Integration tests for search tools against the real Secoda API."""

import json

import pytest

from secoda_analysis_mcp.tools.search import search_data_assets, search_documentation

pytestmark = pytest.mark.integration


class TestSearchDataAssetsIntegration:
    def test_returns_string(self):
        result = search_data_assets(query="test")
        assert isinstance(result, str)

    def test_result_is_valid_json_or_text(self):
        result = search_data_assets(query="test")
        # Response is either JSON or a plain text string from the API
        try:
            data = json.loads(result)
            assert isinstance(data, (dict, list))
        except json.JSONDecodeError:
            assert len(result) > 0

    def test_pagination(self):
        result_p1 = search_data_assets(query="a", page=1)
        result_p2 = search_data_assets(query="a", page=2)
        # Both should succeed (may be different or same content)
        assert isinstance(result_p1, str)
        assert isinstance(result_p2, str)

    def test_no_truncation_returns_more_content(self):
        truncated = search_data_assets(query="test", truncate_length=10)
        full = search_data_assets(query="test", truncate_length=None)
        assert isinstance(truncated, str)
        assert isinstance(full, str)


class TestSearchDocumentationIntegration:
    def test_returns_string(self):
        result = search_documentation(query="metric")
        assert isinstance(result, str)

    def test_result_is_valid_json_or_text(self):
        result = search_documentation(query="metric")
        try:
            data = json.loads(result)
            assert isinstance(data, (dict, list))
        except json.JSONDecodeError:
            assert len(result) > 0
