"""Integration tests for entity tools against the real Secoda API."""

import json

import pytest

from secoda_analysis_mcp.tools.entity import entity_lineage, glossary, retrieve_entity

pytestmark = pytest.mark.integration


class TestGlossaryIntegration:
    def test_returns_string(self):
        result = glossary()
        assert isinstance(result, str)

    def test_result_is_valid_json_or_text(self):
        result = glossary()
        try:
            data = json.loads(result)
            assert isinstance(data, (dict, list, str))
        except json.JSONDecodeError:
            assert len(result) > 0

    def test_custom_truncate_length(self):
        result = glossary(truncate_length=50)
        assert isinstance(result, str)

    def test_no_truncation(self):
        result = glossary(truncate_length=None)
        assert isinstance(result, str)


class TestRetrieveEntityIntegration:
    def test_invalid_id_returns_error(self):
        result = retrieve_entity(entity_id="00000000-0000-0000-0000-000000000000")
        assert isinstance(result, str)
        # Should either return an error dict or an empty/not-found response
        try:
            data = json.loads(result)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pass  # Plain text error is also acceptable


class TestEntityLineageIntegration:
    def test_invalid_id_returns_error(self):
        result = entity_lineage(entity_id="00000000-0000-0000-0000-000000000000")
        assert isinstance(result, str)
        try:
            data = json.loads(result)
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pass
