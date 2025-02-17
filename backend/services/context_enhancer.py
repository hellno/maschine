import logging
import pathlib
from typing import Optional, TypedDict
from llama_index.core import SimpleDirectoryReader, GPTVectorStoreIndex, PromptTemplate
from llama_index.llms.openai import OpenAI


class ContextPiece(TypedDict):
    filepath: str
    parentDocFilepath: Optional[str]


PARENT_UPDATE_DOC = "shared.md"
DOCS_ROOT_PATH = "llm_context/docs"


class CodeContextEnhancer:
    QUERY_GEN_STR = """\
    You are a technical assistant that generates search queries to find relevant API documentation.
    Generate {num_queries} technical search queries, one per line, focused on identifying:
    - Specific API endpoints or SDK methods
    - Service integration patterns
    - Authentication requirements
    - Rate limiting or quota information
    
    Original query: {query}
    Queries:
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.llm = OpenAI(model="gpt-3.5-turbo")
        self.query_gen_prompt = PromptTemplate(self.QUERY_GEN_STR)
        self._prepare_query_engine()

    def _generate_queries(self, query: str, num_queries: int = 4) -> list[str]:
        """Generate expanded technical queries for documentation search."""
        response = self.llm.predict(
            self.query_gen_prompt, 
            num_queries=num_queries,
            query=query
        )
        return [q.strip() for q in response.split("\n") if q.strip()]

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
        """Retrieve context using generated technical queries."""
        try:
            # Generate focused technical queries
            queries = self._generate_queries(query)
            self.logger.info(f"Generated search queries: {queries}")
            
            # Collect unique content from all queries
            content_pieces = set()
            for q in queries:
                response = self.query_engine.query(q)
                content_pieces.update(
                    node.text for node in response.source_nodes
                )
            
            return "\n\n".join(content_pieces) if content_pieces else None
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
