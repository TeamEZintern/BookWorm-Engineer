from bookworm.config import load_config


def test_rag_config_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_API_KEY", "test-key")

    config = load_config(working_dir=tmp_path)

    assert config.rag_sources_dir == (tmp_path / ".bookworm/sources").resolve()
    assert config.rag_index_dir == (tmp_path / ".bookworm/index").resolve()
    assert config.rag_chunk_size == 800
    assert config.rag_chunk_overlap == 120
    assert config.rag_top_k == 5
    assert config.rag_collection_name == "bookworm_sources"
    assert config.rag_embedding_model == "sentence-transformers/all-MiniLM-L6-v2"


def test_rag_config_env_override(monkeypatch, tmp_path):
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("RAG_CHUNK_SIZE", "400")
    monkeypatch.setenv("RAG_TOP_K", "3")
    monkeypatch.setenv("RAG_COLLECTION_NAME", "my_collection")

    config = load_config(working_dir=tmp_path)

    assert config.rag_chunk_size == 400
    assert config.rag_top_k == 3
    assert config.rag_collection_name == "my_collection"
