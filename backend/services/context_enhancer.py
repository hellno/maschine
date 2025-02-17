import logging
import pathlib
from typing import Optional, TypedDict


class ContextPiece(TypedDict):
    filepath: str
    parentDocFilepath: Optional[str]
    keywords: list[str]


class CodeContextEnhancer:
    def __init__(self):
        self.context_pieces = self._load_context_pieces()
        self.logger = logging.getLogger(__name__)
        for piece in self.context_pieces:
            if not pathlib.Path(piece["filepath"]).exists():
                self.logger.error(f"Missing context file: {piece['filepath']}")
                raise FileNotFoundError(f"Context file missing: {piece['filepath']}")

    def _load_context_pieces(self) -> list[ContextPiece]:
        """Dynamically load context pieces from docs directory structure."""
        context_pieces = []
        docs_root = pathlib.Path("llm_context/docs")
        
        # Find all markdown files except shared.md
        for md_path in docs_root.glob("**/*.md"):
            if md_path.name == "shared.md":
                continue
            
            # Create parent doc path in same directory
            parent_doc = md_path.parent / "shared.md"
            
            context_pieces.append(ContextPiece(
                filepath=str(md_path),
                keywords=[],  # Empty array as specified
                parentDocFilepath=str(parent_doc) if parent_doc.exists() else None
            ))
        
        return context_pieces
    
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
