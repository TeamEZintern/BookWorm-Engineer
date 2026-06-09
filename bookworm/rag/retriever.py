from pathlib import Path

from langchain_chroma import Chroma

from bookworm.config import Config
from bookworm.rag.embeddings import create_embeddings


def _get_index_dir(config: Config) -> Path:
    return getattr(config, "rag_index_dir", Path(".bookworm/index"))


def _get_collection_name(config: Config) -> str:
    return getattr(config, "rag_collection_name", "bookworm_sources")


def _get_top_k(config: Config) -> int:
    return getattr(config, "rag_top_k", 5)


def retrieve_context(config: Config, query: str) -> str:
    index_dir = _get_index_dir(config)

    if not index_dir.exists():
        return ""

    vector_store = Chroma(
        persist_directory=str(index_dir),
        collection_name=_get_collection_name(config),
        embedding_function=create_embeddings(config),
    )

    docs = vector_store.similarity_search(query, k=_get_top_k(config))

    if not docs:
        return ""

    return "\n\n".join(
        f"[Source: {doc.metadata.get('file_name', 'unknown')}]\n{doc.page_content}"
        for doc in docs
    )