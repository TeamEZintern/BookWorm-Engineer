import json
from datetime import datetime

import pytest

from bookworm.gui.models import (
    Chat,
    ChatStore,
    Message,
    default_chat_name,
    validate_chat_data,
)


def test_default_chat_name_uses_timestamp():
    when = datetime(2026, 6, 22, 11, 30, 0)
    assert default_chat_name(when) == "New Chat 11:30 AM 22/6/2026"


def test_chat_round_trip_dict():
    chat = Chat(
        chat_id="abc-123",
        name="Design GUI",
        created_at=datetime(2026, 6, 17, 10, 30, 0),
        updated_at=datetime(2026, 6, 17, 11, 15, 0),
        messages=[Message(role="user", content="Hello").to_dict()],
        draft="unfinished prompt",
    )

    restored = Chat.from_dict(chat.to_dict())
    assert restored.id == chat.id
    assert restored.name == chat.name
    assert restored.messages == chat.messages
    assert restored.draft == "unfinished prompt"


def test_chat_draft_defaults_to_empty_string():
    chat = Chat.from_dict({
        "id": "abc-123",
        "name": "Design GUI",
        "created_at": "2026-06-17T10:30:00",
        "updated_at": "2026-06-17T11:15:00",
        "messages": [],
    })

    assert chat.draft == ""
    assert chat.to_dict()["draft"] == ""


def test_validate_chat_data_rejects_missing_keys():
    with pytest.raises(ValueError, match="missing required keys"):
        validate_chat_data({"id": "x", "name": "n"})


def test_validate_chat_data_rejects_non_string_draft():
    with pytest.raises(ValueError, match="draft must be a string"):
        validate_chat_data({
            "id": "x",
            "name": "n",
            "created_at": "2026-06-17T10:30:00",
            "updated_at": "2026-06-17T11:15:00",
            "messages": [],
            "draft": ["not", "text"],
        })


def test_chat_store_save_load_and_delete(tmp_path):
    store = ChatStore(tmp_path / "chats")
    chat = Chat(
        chat_id="chat-1",
        name="New Chat 11:30 AM 22/6/2026",
        created_at=datetime(2026, 6, 22, 12, 0, 0),
        updated_at=datetime(2026, 6, 22, 12, 5, 0),
        messages=[Message(role="user", content="asdf").to_dict()],
        draft="draft text",
    )

    store.add(chat)
    json_path = tmp_path / "chats" / "chat-1.json"
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["name"] == "New Chat 11:30 AM 22/6/2026"
    assert len(data["messages"]) == 1
    assert data["draft"] == "draft text"

    reloaded = ChatStore(tmp_path / "chats")
    reloaded.load()
    assert len(reloaded.all()) == 1
    assert reloaded.get("chat-1").name == "New Chat 11:30 AM 22/6/2026"
    assert reloaded.get("chat-1").draft == "draft text"

    store.remove(chat)
    assert not json_path.exists()
    assert store.is_empty()
