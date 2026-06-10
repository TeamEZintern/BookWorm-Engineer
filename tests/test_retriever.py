from pathlib import Path
from types import SimpleNamespace

from langchain_core.documents import Document

from bookworm.rag import retriever


class FakeChroma:
    def __init__(self, **kwargs):
        self._docs = []

    def similarity_search(self, query, k=5):
        return self._docs


def test_retrieve_context_returns_empty_when_no_index(tmp_path):
    config = SimpleNamespace(
        rag_index_dir=tmp_path / "nonexistent",
        rag_collection_name="test",
        rag_top_k=5,
    )

    result = retriever.retrieve_context(config, "anything")

    assert result == ""


def test_retrieve_context_returns_empty_when_no_matches(monkeypatch, tmp_path):
    index_dir = tmp_path / "index"
    index_dir.mkdir()

    monkeypatch.setattr(retriever, "Chroma", FakeChroma)
    monkeypatch.setattr(retriever, "create_embeddings", lambda _: object())

    config = SimpleNamespace(
        rag_index_dir=index_dir,
        rag_collection_name="test",
        rag_top_k=5,
    )

    result = retriever.retrieve_context(config, "anything")

    assert result == ""


def test_retrieve_context_formats_matches(monkeypatch, tmp_path):
    index_dir = tmp_path / "index"
    index_dir.mkdir()

    fake = FakeChroma()
    fake._docs = [
        Document(
            page_content="Python is a programming language.",
            metadata={"file_name": "guide.md", "file_path": "/fake/guide.md", "file_type": ".md"},
        ),
        Document(
            page_content="It supports multiple paradigms.",
            metadata={"file_name": "notes.txt", "file_path": "/fake/notes.txt", "file_type": ".txt"},
        ),
    ]

    monkeypatch.setattr(retriever, "Chroma", lambda **kwargs: fake)
    monkeypatch.setattr(retriever, "create_embeddings", lambda _: object())

    config = SimpleNamespace(
        rag_index_dir=index_dir,
        rag_collection_name="test",
        rag_top_k=5,
    )

    result = retriever.retrieve_context(config, "Python")

    assert "[Source: guide.md]" in result
    assert "Python is a programming language." in result
    assert "[Source: notes.txt]" in result
    assert "It supports multiple paradigms." in result
