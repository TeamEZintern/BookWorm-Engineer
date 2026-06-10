import sys
from types import SimpleNamespace

from bookworm.cli import main


def _fake_config(tmp_path):
    return SimpleNamespace(
        llm_api_key="test-key",
        llm_base_url="https://openrouter.ai/api/v1",
        llm_model="openai/gpt-4o-mini",
        context_window=128000,
        git_user_name="Test",
        git_user_email="test@example.com",
        working_dir=tmp_path,
        rag_sources_dir=tmp_path / ".bookworm" / "sources",
        rag_index_dir=tmp_path / ".bookworm" / "index",
        rag_chunk_size=800,
        rag_chunk_overlap=120,
        rag_top_k=5,
        rag_collection_name="bookworm_sources",
        rag_embedding_model="sentence-transformers/all-MiniLM-L6-v2",
    )


def test_index_subcommand_empty_sources(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, "argv", ["bookworm", "index"])
    monkeypatch.setattr("bookworm.cli.load_dotenv", lambda *_: None)
    monkeypatch.setattr("bookworm.cli.load_config", lambda **_: _fake_config(tmp_path))

    result = main()

    assert result == 0
    captured = capsys.readouterr()
    assert "No supported" in captured.out


def test_unknown_subcommand_returns_error(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(sys, "argv", ["bookworm", "foobar"])
    monkeypatch.setattr("bookworm.cli.load_dotenv", lambda *_: None)
    monkeypatch.setattr("bookworm.cli.load_config", lambda **_: _fake_config(tmp_path))

    result = main()

    assert result == 1
    captured = capsys.readouterr()
    assert "Unknown command" in captured.err
