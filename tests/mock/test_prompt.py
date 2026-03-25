"""Unit tests for the MCP system prompt."""

from secoda_analysis_mcp.prompt import MCP_PROMPT


class TestMcpPrompt:
    def test_prompt_is_non_empty_string(self):
        assert isinstance(MCP_PROMPT, str)
        assert len(MCP_PROMPT) > 100

    def test_prompt_mentions_ai_chat(self):
        assert "ai_chat" in MCP_PROMPT

    def test_prompt_mentions_search_tools(self):
        assert "search_data_assets" in MCP_PROMPT
        assert "search_documentation" in MCP_PROMPT

    def test_prompt_mentions_entity_tools(self):
        assert "retrieve_entity" in MCP_PROMPT
        assert "entity_lineage" in MCP_PROMPT
        assert "glossary" in MCP_PROMPT

    def test_prompt_mentions_resource_tools(self):
        assert "list_resources" in MCP_PROMPT
        assert "get_resource" in MCP_PROMPT

    def test_prompt_mentions_collection_tools(self):
        assert "list_collections" in MCP_PROMPT
        assert "get_collection" in MCP_PROMPT

    def test_prompt_mentions_question_tools(self):
        assert "list_questions" in MCP_PROMPT
        assert "get_question" in MCP_PROMPT

    def test_prompt_does_not_mention_run_sql(self):
        assert "run_sql" not in MCP_PROMPT

    def test_prompt_does_not_mention_integration_id(self):
        assert "integration_id" not in MCP_PROMPT.lower()

    def test_prompt_mentions_filter_syntax(self):
        assert "list_resources FILTER SYNTAX" in MCP_PROMPT

    def test_prompt_mentions_truncation_rules(self):
        assert "TRUNCATION RULES" in MCP_PROMPT
