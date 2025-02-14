import logging
import pathlib
from typing import Optional, TypedDict


class ContextPiece(TypedDict):
    filepath: str
    keywords: list[str]


class CodeContextEnhancer:
    # Path is now relative to backend directory
    BACKEND_ROOT = pathlib.Path(__file__).parent.parent
    
    context_pieces = [
        ContextPiece(
            filepath=str(BACKEND_ROOT / "llm_context/docs/neynar/cast_search.md"),
            keywords=["neynar", "cast", "search"],
        ),
        ContextPiece(
            filepath=str(BACKEND_ROOT / "llm_context/docs/dune/dune_api.md"),
            keywords=["dune"]
        ),
    ]

    def __init__(self):
        self.logger = logging.getLogger(__name__)
        for piece in self.context_pieces:
            if not pathlib.Path(piece["filepath"]).exists():
                self.logger.error(f"Missing context file: {piece['filepath']}")
                raise FileNotFoundError(f"Context file missing: {piece['filepath']}")

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
        for piece in matching_pieces:
            try:
                with open(piece["filepath"]) as f:
                    contents.append(f.read())
            except Exception as e:
                self.logger.error(f"Failed to read {piece['filepath']}: {e}")
        print("contents", contents)
        return contents
