"""Integration tests for question tools against the real Secoda API."""

import json

import pytest

from secoda_analysis_mcp.tools.questions import get_question, list_questions

pytestmark = pytest.mark.integration


class TestListQuestionsIntegration:
    def test_returns_string(self):
        result = list_questions()
        assert isinstance(result, str)

    def test_result_is_valid_json(self):
        result = list_questions()
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_pagination(self):
        result = list_questions(page=1)
        assert isinstance(result, str)
        json.loads(result)


class TestGetQuestionIntegration:
    def test_invalid_id_returns_error(self):
        result = get_question(question_id="00000000-0000-0000-0000-000000000000")
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_invalid_id_error_message(self):
        result = get_question(question_id="definitely-not-a-real-id")
        data = json.loads(result)
        assert "error" in data
