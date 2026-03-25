"""Unit tests for tools.resources functions."""

import json

import responses as responses_lib

from secoda_analysis_mcp.tools.resources import get_resource, list_resources

LIST_URL = "https://app.secoda.co/api/v1/resource/catalog"
GET_URL = "https://app.secoda.co/api/v1/resource/all/res-001"


class TestListResources:
    @responses_lib.activate
    def test_basic_list(self, resource_list_response):
        responses_lib.add(responses_lib.GET, LIST_URL, json=resource_list_response, status=200)
        result = list_resources()
        data = json.loads(result)
        assert data["count"] == 1

    @responses_lib.activate
    def test_filter_is_serialized_to_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_resources(filter={"operator": "exact", "field": "native_type", "value": "table"})
        assert "filter" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_sort_is_serialized_to_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_resources(sort={"field": "title", "order": "asc"})
        assert "sort" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_page_is_passed_as_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_resources(page=3)
        assert "page=3" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, LIST_URL, status=403)
        result = list_resources()
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    def test_400_returns_bad_request_error(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"detail": "invalid filter"},
            status=400,
        )
        result = list_resources()
        data = json.loads(result)
        assert "Bad request" in data["error"]

    @responses_lib.activate
    def test_truncation_applied_to_results(self):
        long_desc = "x" * 500
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 1, "results": [{"id": "r1", "description": long_desc}]},
            status=200,
        )
        result = list_resources(truncate_length=50)
        data = json.loads(result)
        assert data["results"][0]["description"].endswith("...")

    @responses_lib.activate
    def test_invalid_filter_falls_back_gracefully(self):
        """Invalid filter dict should still pass (raw JSON fallback)."""
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        result = list_resources(filter={"operator": "bogus", "field": "x", "value": "y"})
        assert result is not None


class TestGetResource:
    @responses_lib.activate
    def test_basic_get(self, resource_detail_response):
        responses_lib.add(responses_lib.GET, GET_URL, json=resource_detail_response, status=200)
        result = get_resource(resource_id="res-001")
        data = json.loads(result)
        assert data["id"] == "res-001"

    @responses_lib.activate
    def test_404_returns_not_found_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=404)
        result = get_resource(resource_id="res-001")
        data = json.loads(result)
        assert "not found" in data["error"].lower()
        assert "res-001" in data["error"]

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=403)
        result = get_resource(resource_id="res-001")
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    def test_truncation_applied(self, resource_detail_response):
        resource_detail_response["description"] = "y" * 500
        responses_lib.add(responses_lib.GET, GET_URL, json=resource_detail_response, status=200)
        result = get_resource(resource_id="res-001", truncate_length=50)
        data = json.loads(result)
        assert data["description"].endswith("...")

    @responses_lib.activate
    def test_no_truncation_when_none(self, resource_detail_response):
        long_desc = "z" * 500
        resource_detail_response["description"] = long_desc
        responses_lib.add(responses_lib.GET, GET_URL, json=resource_detail_response, status=200)
        result = get_resource(resource_id="res-001", truncate_length=None)
        data = json.loads(result)
        assert data["description"] == long_desc
