from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bookworm.agent import Agent
from bookworm.agent_events import TurnCancelledError, TurnEventHandler
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


def _tool_call_delta(index, call_id="", name="", arguments=""):
    function = SimpleNamespace(name=name, arguments=arguments)
    return SimpleNamespace(index=index, id=call_id, function=function)


def _stream_chunk(content=None, tool_calls=None, usage=None):
    delta = SimpleNamespace(
        content=content,
        tool_calls=tool_calls,
        reasoning=None,
        reasoning_content=None,
    )
    return SimpleNamespace(
        choices=[SimpleNamespace(delta=delta)],
        usage=usage,
    )


def test_run_turn_with_events_streams_final_text(tmp_path):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(schema=[], implementations={})
    client = MagicMock()
    client.chat.completions.create.return_value = iter([
        _stream_chunk("Hel"),
        _stream_chunk("lo"),
    ])

    agent = Agent(config, client, registry, "system prompt")
    agent.messages.append({"role": "user", "content": "Hi"})

    deltas: list[str] = []
    completed: list[tuple[str, list]] = []
    handler = TurnEventHandler(
        on_text_delta=deltas.append,
        on_turn_complete=lambda content, tool_calls: completed.append((content, tool_calls)),
    )

    result = agent.run_turn_with_events(handler)

    assert result == "Hello"
    assert deltas == ["Hel", "lo"]
    assert completed == [("Hello", [])]
    assert agent.messages[-1]["content"] == "Hello"


def test_run_turn_with_events_emits_tool_events(tmp_path, monkeypatch):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(
        schema=[{"type": "function", "function": {"name": "bash", "parameters": {}}}],
        implementations={"bash": lambda command: f"ran:{command}"},
    )
    client = MagicMock()

    tool_call_chunks = [
        _stream_chunk(
            tool_calls=[_tool_call_delta(0, call_id="call_1", name="bash", arguments='{"command": "echo hi"}')],
        ),
    ]
    final_chunks = [
        _stream_chunk("Done"),
    ]
    client.chat.completions.create.side_effect = [
        iter(tool_call_chunks),
        iter(final_chunks),
    ]

    monkeypatch.setattr(
        "bookworm.agent.call_tool",
        lambda registry, name, arguments_json: "tool-output",
    )

    agent = Agent(config, client, registry, "system prompt")
    agent.messages.append({"role": "user", "content": "Run it"})

    tool_started: list[tuple[str, str, str]] = []
    tool_results: list[tuple[str, str]] = []
    handler = TurnEventHandler(
        on_tool_call_started=lambda name, args, call_id: tool_started.append((name, args, call_id)),
        on_tool_result=lambda call_id, output: tool_results.append((call_id, output)),
        on_turn_complete=lambda content, tool_calls: None,
    )

    result = agent.run_turn_with_events(handler)

    assert result == "Done"
    assert tool_started == [("bash", '{"command": "echo hi"}', "call_1")]
    assert tool_results == [("call_1", "tool-output")]
    assert len(agent.messages) == 5
    assert agent.messages[2]["tool_calls"][0]["function"]["name"] == "bash"
    assert agent.messages[3]["role"] == "tool"


def test_run_turn_with_events_stops_when_cancelled(tmp_path):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(schema=[], implementations={})
    client = MagicMock()

    def streaming_create(**kwargs):
        chunks = [_stream_chunk("Hel"), _stream_chunk("lo"), _stream_chunk("!")]

        def generate():
            for index, chunk in enumerate(chunks):
                yield chunk
                if index == 1:
                    agent.request_cancel()

        return generate()

    client.chat.completions.create.side_effect = streaming_create

    agent = Agent(config, client, registry, "system prompt")
    agent.messages.append({"role": "user", "content": "Hi"})

    with pytest.raises(TurnCancelledError):
        agent.run_turn_with_events(TurnEventHandler())

    assert agent.messages[-1]["role"] == "assistant"
    assert agent.messages[-1]["content"] == "Hello"


def test_run_turn_without_handler_uses_non_streaming_api(tmp_path):
    config = _fake_config(tmp_path)
    registry = ToolRegistry(schema=[], implementations={})
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="Final", tool_calls=None),
            )
        ],
        usage=None,
    )

    agent = Agent(config, client, registry, "system prompt")
    agent.messages.append({"role": "user", "content": "Hi"})

    result = agent.run_turn()

    assert result == "Final"
    kwargs = client.chat.completions.create.call_args.kwargs
    assert "stream" not in kwargs
