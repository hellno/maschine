import logging
from typing import Optional, TypedDict
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    PromptTemplate,
    Settings,
    StorageContext,
    load_index_from_storage,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI

Settings.embed_model = OpenAIEmbedding(model="text-embedding-3-small")
Settings.model = OpenAI(model="gpt-4o-mini")


class ContextPiece(TypedDict):
    filepath: str
    parentDocFilepath: Optional[str]


PARENT_UPDATE_DOC = "shared.md"
CONTEXT_DOCS_PATH = "backend/llm_context/docs"
INDEX_STORAGE_PATH = "backend/llm_context/index"

QUERY_GEN_STR = """\
You are a technical query refinement assistant. Transform the following user project description into up to {num_queries} concise, highly technical search queries—one per line—that will help retrieve relevant API documentation. Your queries should:
• Identify specific API endpoints, function or method names, or SDK operations implied by the description.
• Use precise, domain-specific terminology.

If no clear API-related details are present, do not generate any queries.
 
Original prompt: {query}
Refined queries:
"""


class CodeContextEnhancer:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._prepare_query_engine()

    def get_relevant_context(self, query: str) -> Optional[str]:
        """Retrieve context using generated technical queries."""
        try:
            if not query or not query.strip():
                return None
            queries = self._generate_queries(query)
            content_pieces = set()
            for q in queries:
                response = self.query_engine.query(q)
                print(f"Query: {q}, Response: {response}")
                content_pieces.update(node.text for node in response.source_nodes)

            return "\n\n".join(content_pieces) if content_pieces else None
        except Exception as e:
            self.logger.error(f"Failed to query context: {e}")
            return None

    def _generate_queries(self, prompt: str, num_queries: int = 3) -> list[str]:
        """Generate expanded technical queries for documentation search."""
        print(f"Generating queries from prompt: {prompt}")
        response = Settings.model.predict(
            PromptTemplate(QUERY_GEN_STR), query=prompt, num_queries=num_queries
        )
        queries = [q.strip() for q in response.split("\n") if q.strip()]
        print(f"Generated queries from prompt:\nqueries: {queries}")
        return queries

    def _prepare_query_engine(self) -> list[ContextPiece]:
        """Dynamically load context pieces from docs directory structure."""

        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=INDEX_STORAGE_PATH
            )
            index = load_index_from_storage(storage_context)
        except Exception as e:
            print(f"Error loading index: {e}")
            documents = SimpleDirectoryReader(
                input_dir=CONTEXT_DOCS_PATH, recursive=True
            ).load_data()

            # Build a vector index
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=INDEX_STORAGE_PATH)
            print(f"Index created and stored at {INDEX_STORAGE_PATH}")

        self.query_engine = index.as_query_engine(query_kwargs={"top_k": 3})
