"""Unit tests for tools.collections functions."""

import json

import responses as responses_lib

from secoda_analysis_mcp.tools.collections import get_collection, list_collections

LIST_URL = "https://app.secoda.co/api/v1/collection/collections"
GET_URL = "https://app.secoda.co/api/v1/collection/collections/col-001"


class TestListCollections:
    @responses_lib.activate
    def test_basic_list(self, collection_list_response):
        responses_lib.add(responses_lib.GET, LIST_URL, json=collection_list_response, status=200)
        result = list_collections()
        data = json.loads(result)
        assert data["count"] == 1

    @responses_lib.activate
    def test_title_filter_passed_as_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_collections(title="Finance")
        assert "title=Finance" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_no_title_filter_when_none(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_collections()
        assert "title" not in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_page_passed_as_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_collections(page=2)
        assert "page=2" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, LIST_URL, status=403)
        result = list_collections()
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    def test_truncation_applied(self, collection_list_response):
        collection_list_response["results"][0]["description"] = "d" * 500
        responses_lib.add(responses_lib.GET, LIST_URL, json=collection_list_response, status=200)
        result = list_collections(truncate_length=50)
        data = json.loads(result)
        assert data["results"][0]["description"].endswith("...")


class TestGetCollection:
    @responses_lib.activate
    def test_basic_get(self, collection_list_response):
        detail = collection_list_response["results"][0]
        responses_lib.add(responses_lib.GET, GET_URL, json=detail, status=200)
        result = get_collection(collection_id="col-001")
        data = json.loads(result)
        assert data["id"] == "col-001"

    @responses_lib.activate
    def test_404_returns_not_found_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=404)
        result = get_collection(collection_id="col-001")
        data = json.loads(result)
        assert "not found" in data["error"].lower()
        assert "col-001" in data["error"]

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=403)
        result = get_collection(collection_id="col-001")
        data = json.loads(result)
        assert "Permission denied" in data["error"]
