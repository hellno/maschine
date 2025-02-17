import pytest
from unittest import mock
from backend.services.context_enhancer import CodeContextEnhancer


@pytest.fixture
def mock_docs(tmp_path):
    docs_dir = tmp_path / "llm_context/docs/dune"
    docs_dir.mkdir(parents=True)

    dune_doc = docs_dir / "dune_api.md"
    dune_doc.write_text("Dune API documentation content")

    return tmp_path


def test_query_processing(mock_docs):
    # Mock the query generation and engine responses
    with mock.patch.object(
        CodeContextEnhancer,
        "_generate_queries",
        return_value=["Dune API authentication", "Dune query execution methods"]
    ), mock.patch.object(
        CodeContextEnhancer,
        "query_engine"
    ) as mock_engine:
        # Setup mock response with document nodes
        mock_response = mock.Mock()
        mock_response.source_nodes = [
            mock.Mock(text="Dune API documentation content"),
            mock.Mock(text="Common Dune authentication methods")
        ]
        mock_engine.query.return_value = mock_response
        
        enhancer = CodeContextEnhancer()
        result = enhancer.get_relevant_context("How to query Dune API?")
        
        assert "Dune API documentation content" in result
        assert "Common Dune authentication methods" in result


def test_empty_query():
    enhancer = CodeContextEnhancer()
    result = enhancer.get_relevant_context("")
    assert result is None
