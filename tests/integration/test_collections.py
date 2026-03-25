"""Integration tests for collection tools against the real Secoda API."""

import json

import pytest

from secoda_analysis_mcp.tools.collections import get_collection, list_collections

pytestmark = pytest.mark.integration


class TestListCollectionsIntegration:
    def test_returns_string(self):
        result = list_collections()
        assert isinstance(result, str)

    def test_result_is_valid_json(self):
        result = list_collections()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_pagination(self):
        result = list_collections(page=1)
        assert isinstance(result, str)
        json.loads(result)

    def test_title_filter(self):
        result = list_collections(title="a")
        assert isinstance(result, str)
        json.loads(result)


class TestGetCollectionIntegration:
    def test_invalid_id_returns_error(self):
        result = get_collection(collection_id="00000000-0000-0000-0000-000000000000")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_invalid_id_error_message(self):
        result = get_collection(collection_id="definitely-not-a-real-id")
        data = json.loads(result)
        assert "error" in data
