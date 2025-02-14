import pytest
from unittest import mock
from backend.services.context_enhancer import CodeContextEnhancer


@pytest.fixture
def mock_docs(tmp_path):
    # Create structure under backend/llm_context
    docs_dir = tmp_path / "backend/llm_context/docs/dune"
    docs_dir.mkdir(parents=True)
    
    dune_doc = docs_dir / "dune_api.md"
    dune_doc.write_text("Dune API documentation content")

    return tmp_path


def test_query_processing(mock_docs):
    # Patch the context pieces to use temporary paths
    with mock.patch.object(
        CodeContextEnhancer,
        "context_pieces",
        [
            {
                "filepath": str(mock_docs / "backend/llm_context/docs/dune/dune_api.md"),
                "keywords": ["dune"],
            }
        ],
    ):
        enhancer = CodeContextEnhancer()
        result = enhancer.get_relevant_context("make something nice with dune api")

        assert "Dune API documentation content" in result


def test_empty_query():
    enhancer = CodeContextEnhancer()
    result = enhancer.get_relevant_context("")
    assert result is None
