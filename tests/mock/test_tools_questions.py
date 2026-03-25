"""Unit tests for tools.questions functions."""

import json

import responses as responses_lib

from secoda_analysis_mcp.tools.questions import get_question, list_questions

LIST_URL = "https://app.secoda.co/api/v1/question/questions"
GET_URL = "https://app.secoda.co/api/v1/question/questions/q-001"


class TestListQuestions:
    @responses_lib.activate
    def test_basic_list(self, question_list_response):
        responses_lib.add(responses_lib.GET, LIST_URL, json=question_list_response, status=200)
        result = list_questions()
        data = json.loads(result)
        assert data["count"] == 1

    @responses_lib.activate
    def test_page_passed_as_query_param(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_questions(page=2)
        assert "page=2" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_default_page_is_1(self):
        responses_lib.add(
            responses_lib.GET,
            LIST_URL,
            json={"count": 0, "results": []},
            status=200,
        )
        list_questions()
        assert "page=1" in responses_lib.calls[0].request.url

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, LIST_URL, status=403)
        result = list_questions()
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    def test_truncation_applied(self, question_list_response):
        question_list_response["results"][0]["description"] = "q" * 500
        responses_lib.add(responses_lib.GET, LIST_URL, json=question_list_response, status=200)
        result = list_questions(truncate_length=50)
        data = json.loads(result)
        assert data["results"][0]["description"].endswith("...")


class TestGetQuestion:
    @responses_lib.activate
    def test_basic_get(self, question_list_response):
        detail = question_list_response["results"][0]
        responses_lib.add(responses_lib.GET, GET_URL, json=detail, status=200)
        result = get_question(question_id="q-001")
        data = json.loads(result)
        assert data["id"] == "q-001"

    @responses_lib.activate
    def test_404_returns_not_found_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=404)
        result = get_question(question_id="q-001")
        data = json.loads(result)
        assert "not found" in data["error"].lower()
        assert "q-001" in data["error"]

    @responses_lib.activate
    def test_403_returns_permission_error(self):
        responses_lib.add(responses_lib.GET, GET_URL, status=403)
        result = get_question(question_id="q-001")
        data = json.loads(result)
        assert "Permission denied" in data["error"]

    @responses_lib.activate
    def test_no_truncation_when_none(self, question_list_response):
        long_desc = "a" * 500
        detail = {"id": "q-001", "title": "How?", "description": long_desc}
        responses_lib.add(responses_lib.GET, GET_URL, json=detail, status=200)
        result = get_question(question_id="q-001", truncate_length=None)
        data = json.loads(result)
        assert data["description"] == long_desc
