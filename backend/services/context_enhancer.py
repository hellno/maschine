import logging
import pathlib
from typing import Optional, TypedDict
from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex


class ContextPiece(TypedDict):
    filepath: str
    parentDocFilepath: Optional[str]


PARENT_UPDATE_DOC = "shared.md"
DOCS_ROOT_PATH = "llm_context/docs"


class CodeContextEnhancer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._prepare_query_engine()

    def _prepare_query_engine(self) -> list[ContextPiece]:
        """Dynamically load context pieces from docs directory structure."""

        # Load documents from directory (including subdirectories)
        self.documents = SimpleDirectoryReader(
            input_dir=DOCS_ROOT_PATH, recursive=True
        ).load_data()

        print("self.documents", self.documents)
        # Build a vector index
        index = GPTVectorStoreIndex.from_documents(self.documents)

        # Create a query engine to fetch top 3 documents
        self.query_engine = index.as_query_engine(query_kwargs={"top_k": 3})

    def get_relevant_context(self, query: str) -> Optional[str]:
        """Retrieve raw context without formatting assumptions."""

        try:
            content_pieces = self.get_content_pieces(query)
            if not content_pieces:
                return None
            return "\n".join(content_pieces)
        except Exception as e:
            self.logger.error(f"Failed to query context: {e}")
            return None

    def get_content_pieces(self, query: str) -> list[str]:
        """Retrieve context pieces for a given query."""
        matching_pieces = [
            piece
            for piece in self.context_pieces
            if any(kw in query for kw in piece["keywords"])
        ]

        if not matching_pieces:
            return []
        print("matching_pieces", matching_pieces)
        contents = []

        parent_docs = set(
            piece.get("parentDocFilepath")
            for piece in matching_pieces
            if piece.get("parentDocFilepath")
        )
        for parent_doc in parent_docs:
            try:
                with open(parent_doc) as f:
                    contents.append(f.read())
            except Exception as e:
                self.logger.error(f"Failed to read parent doc {parent_doc}: {e}")

        for piece in matching_pieces:
            try:
                with open(piece["filepath"]) as f:
                    contents.append(f.read())
            except Exception as e:
                self.logger.error(f"Failed to read doc {piece['filepath']}: {e}")
        print("contents", contents)
        return contents
