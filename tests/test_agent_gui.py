from types import SimpleNamespace
from unittest.mock import MagicMock

from bookworm.agent import Agent
from bookworm.tools import ToolRegistry


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


def test_load_conversation_from_gui_messages(tmp_path):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(schema=[], implementations={})
    agent = Agent(config, MagicMock(), registry, "system prompt")

    agent.load_conversation([
        {
            "role": "user",
            "content": "Hello",
            "timestamp": "2026-06-23T10:00:00",
            "tool_calls": [],
        },
        {
            "role": "assistant",
            "content": "Hi there",
            "timestamp": "2026-06-23T10:00:01",
            "tool_calls": [],
        },
    ])

    assert len(agent.messages) == 3
    assert agent.messages[0]["role"] == "system"
    assert agent.messages[1] == {"role": "user", "content": "Hello"}
    assert agent.messages[2] == {"role": "assistant", "content": "Hi there"}


def test_load_conversation_skips_non_chat_roles(tmp_path):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(schema=[], implementations={})
    agent = Agent(config, MagicMock(), registry, "system prompt")

    agent.load_conversation([
        {"role": "tool", "content": "ignored", "timestamp": "2026-06-23T10:00:00"},
        {"role": "user", "content": "Keep me", "timestamp": "2026-06-23T10:00:01", "tool_calls": []},
    ])

    assert len(agent.messages) == 2
    assert agent.messages[1]["content"] == "Keep me"
