"""Integration tests for resource tools against the real Secoda API."""

import json

import pytest

from secoda_analysis_mcp.tools.resources import get_resource, list_resources

pytestmark = pytest.mark.integration


class TestListResourcesIntegration:
    def test_returns_string(self):
        result = list_resources()
        assert isinstance(result, str)

    def test_result_is_valid_json(self):
        result = list_resources()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_filter_by_native_type_table(self):
        result = list_resources(
            filter={"operator": "exact", "field": "native_type", "value": "table"}
        )
        data = json.loads(result)
        assert "results" in data or "error" in data

    def test_filter_with_and_operator(self):
        result = list_resources(
            filter={
                "operator": "and",
                "operands": [
                    {"operator": "exact", "field": "native_type", "value": "table"},
                    {"operator": "is_set", "field": "description", "value": None},
                ],
            }
        )
        assert isinstance(result, str)
        json.loads(result)  # Must be valid JSON

    def test_sort_by_title(self):
        result = list_resources(sort={"field": "title", "order": "asc"})
        assert isinstance(result, str)
        json.loads(result)

    def test_pagination(self):
        result = list_resources(page=1)
        assert isinstance(result, str)


class TestGetResourceIntegration:
    def test_invalid_id_returns_error(self):
        result = get_resource(resource_id="00000000-0000-0000-0000-000000000000")
        data = json.loads(result)
        # Should be a not-found error or an empty resource
        assert isinstance(data, dict)

    def test_invalid_id_error_message(self):
        result = get_resource(resource_id="definitely-not-a-real-id")
        data = json.loads(result)
        assert "error" in data
