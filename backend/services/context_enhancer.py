import os
from typing import Optional
from backend.integrations.llm import (
    generate_search_queries_from_user_input,
)
from llama_index.embeddings.openai import OpenAIEmbedding
from llama_index.llms.openai import OpenAI
from llama_index.llms.openai.utils import DEFAULT_OPENAI_API_BASE
from llama_index.core import (
    SimpleDirectoryReader,
    VectorStoreIndex,
    Settings,
    StorageContext,
    load_index_from_storage,
)

from backend.config import CODE_CONTEXT

embed_model = OpenAIEmbedding(
    model="text-embedding-3-small",
    api_base=DEFAULT_OPENAI_API_BASE,
    api_key=os.environ.get("REAL_OPENAI_API_KEY"),
)
model = OpenAI(
    model="gpt-4o-mini",
    api_base=DEFAULT_OPENAI_API_BASE,
    api_key=os.environ.get("REAL_OPENAI_API_KEY"),
)

Settings.embed_model = embed_model
Settings.model = model

PARENT_UPDATE_DOC = "shared.md"
CONTEXT_DOCS_PATH = "backend/llm_context/docs"
INDEX_STORAGE_PATH = "backend/llm_context/index"


class CodeContextEnhancer:
    def __init__(self):
        self._prepare_query_engine()

    def get_relevant_context(self, user_input: str) -> Optional[str]:
        """Retrieve context using generated technical queries."""
        if not CODE_CONTEXT["ENABLED"]:
            print("Context enhancement disabled.")
            return None

        try:
            if not user_input or not user_input.strip():
                return None
            queries = generate_search_queries_from_user_input(user_input=user_input)
            content_pieces = set()
            for q in queries:
                response = self.query_engine.query(q)
                print(f"Search query: {q}, Response: {response}, Nodes: {response.source_nodes}")
                content_pieces.update(node.text for node in response.source_nodes)

            return "\n\n".join(content_pieces) if content_pieces else None
        except Exception as e:
            print(f"Failed to query context: {e}")
            return None

    def _prepare_query_engine(self):
        """Dynamically load context pieces from docs directory structure."""

        try:
            storage_context = StorageContext.from_defaults(
                persist_dir=INDEX_STORAGE_PATH
            )
            index = load_index_from_storage(storage_context)
            print(f"Index loaded from {INDEX_STORAGE_PATH}")
        except Exception as e:
            print(f"Error loading index: {e}")
            documents = SimpleDirectoryReader(
                input_dir=CONTEXT_DOCS_PATH, recursive=True
            ).load_data()

            # Build a vector index
            index = VectorStoreIndex.from_documents(documents)
            index.storage_context.persist(persist_dir=INDEX_STORAGE_PATH)
            print(f"Index created and stored at {INDEX_STORAGE_PATH}")

        self.query_engine = index.as_query_engine(llm=model, query_kwargs={"top_k": 3})

    def refresh_persisted_index(self):
        """Rebuild and persist the context index."""
        documents = SimpleDirectoryReader(
            input_dir=CONTEXT_DOCS_PATH, recursive=True
        ).load_data()

        # Build a vector index
        index = VectorStoreIndex.from_documents(documents)
        index.storage_context.persist(persist_dir=INDEX_STORAGE_PATH)
        print(f"Index refreshed and stored at {INDEX_STORAGE_PATH}")
