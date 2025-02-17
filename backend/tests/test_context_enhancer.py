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
    # Create test context pieces using temporary paths
    test_pieces = [
        {
            "filepath": str(mock_docs / "llm_context/docs/dune/dune_api.md"),
            "parentDocFilepath": str(mock_docs / "llm_context/docs/dune/shared.md")
        }
    ]
    
    # Create shared.md file that the test expects
    shared_doc = mock_docs / "llm_context/docs/dune/shared.md"
    shared_doc.write_text("Common Dune documentation")
    
    # Patch the loader method to return our test pieces
    with mock.patch.object(
        CodeContextEnhancer,
        "_load_context_pieces",
        return_value=test_pieces
    ):
        enhancer = CodeContextEnhancer()
        result = enhancer.get_relevant_context("make something nice with dune api")
        
        # Verify both parent doc and specific doc content are returned
        assert "Common Dune documentation" in result
        assert "Dune API documentation content" in result


def test_empty_query():
    enhancer = CodeContextEnhancer()
    result = enhancer.get_relevant_context("")
    assert result is None
