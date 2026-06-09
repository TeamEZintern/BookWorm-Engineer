from types import SimpleNamespace

from bookworm.rag import embeddings


class FakeHuggingFaceEmbeddings:
    def __init__(self, *, model_name: str):
        self.model_name = model_name


def test_create_embeddings_uses_default_model(monkeypatch):
    monkeypatch.setattr(embeddings, "HuggingFaceEmbeddings", FakeHuggingFaceEmbeddings)

    result = embeddings.create_embeddings(SimpleNamespace())

    assert isinstance(result, FakeHuggingFaceEmbeddings)
    assert result.model_name == "sentence-transformers/all-MiniLM-L6-v2"


def test_create_embeddings_uses_configured_model(monkeypatch):
    monkeypatch.setattr(embeddings, "HuggingFaceEmbeddings", FakeHuggingFaceEmbeddings)
    config = SimpleNamespace(rag_embedding_model="sentence-transformers/custom-model")

    result = embeddings.create_embeddings(config)

    assert isinstance(result, FakeHuggingFaceEmbeddings)
    assert result.model_name == "sentence-transformers/custom-model"
