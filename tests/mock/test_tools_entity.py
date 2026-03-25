"""Unit tests for tools.entity functions."""

import json

import responses as responses_lib

from secoda_analysis_mcp.tools.entity import entity_lineage, glossary, retrieve_entity

TOOL_URL = "https://app.secoda.co/api/v1/ai/mcp/tools/call/"


def _tool_response(text: str) -> dict:
    return {"isError": False, "content": [{"type": "text", "text": text}]}


class TestRetrieveEntity:
    @responses_lib.activate
    def test_basic_retrieve(self):
        responses_lib.add(
            responses_lib.POST, TOOL_URL, json=_tool_response('{"id": "e1"}'), status=200
        )
        result = retrieve_entity(entity_id="e1")
        assert "e1" in result

    @responses_lib.activate
    def test_passes_entity_id(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        retrieve_entity(entity_id="entity-xyz")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["entity_id"] == "entity-xyz"

    @responses_lib.activate
    def test_calls_correct_tool_name(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        retrieve_entity(entity_id="e1")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["name"] == "retrieve_entity"

    @responses_lib.activate
    def test_default_truncate_length(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        retrieve_entity(entity_id="e1")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] == 150

    @responses_lib.activate
    def test_truncate_none_passes_through(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        retrieve_entity(entity_id="e1", truncate_length=None)
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] is None


class TestEntityLineage:
    @responses_lib.activate
    def test_basic_lineage(self):
        responses_lib.add(
            responses_lib.POST, TOOL_URL, json=_tool_response('{"upstream": []}'), status=200
        )
        result = entity_lineage(entity_id="e1")
        assert "upstream" in result

    @responses_lib.activate
    def test_calls_correct_tool_name(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        entity_lineage(entity_id="e1")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["name"] == "entity_lineage"

    @responses_lib.activate
    def test_passes_entity_id(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        entity_lineage(entity_id="lineage-e1")
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["entity_id"] == "lineage-e1"


class TestGlossary:
    @responses_lib.activate
    def test_basic_glossary(self):
        responses_lib.add(
            responses_lib.POST,
            TOOL_URL,
            json=_tool_response('{"terms": [{"title": "GMV"}]}'),
            status=200,
        )
        result = glossary()
        assert "GMV" in result

    @responses_lib.activate
    def test_calls_correct_tool_name(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        glossary()
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["name"] == "glossary"

    @responses_lib.activate
    def test_default_truncate_length(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        glossary()
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] == 150

    @responses_lib.activate
    def test_custom_truncate_length(self):
        responses_lib.add(responses_lib.POST, TOOL_URL, json=_tool_response("{}"), status=200)
        glossary(truncate_length=500)
        body = json.loads(responses_lib.calls[0].request.body)
        assert body["arguments"]["truncate_length"] == 500
