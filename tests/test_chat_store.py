import json
from datetime import datetime

import pytest

from bookworm.gui.models import (
    Message,
    Thread,
    ThreadStore,
    default_thread_name,
    validate_thread_data,
)


def test_default_thread_name_uses_timestamp():
    when = datetime(2026, 6, 22, 11, 30, 0)
    assert default_thread_name(when) == "New Thread 11:30 AM 22/6/2026"


def test_thread_round_trip_dict():
    thread = Thread(
        thread_id="abc-123",
        name="Design GUI",
        created_at=datetime(2026, 6, 17, 10, 30, 0),
        updated_at=datetime(2026, 6, 17, 11, 15, 0),
        messages=[Message(role="user", content="Hello").to_dict()],
    )

    restored = Thread.from_dict(thread.to_dict())
    assert restored.id == thread.id
    assert restored.name == thread.name
    assert restored.messages == thread.messages


def test_validate_thread_data_rejects_missing_keys():
    with pytest.raises(ValueError, match="missing required keys"):
        validate_thread_data({"id": "x", "name": "n"})


def test_thread_store_save_load_and_delete(tmp_path):
    store = ThreadStore(tmp_path / "threads")
    thread = Thread(
        thread_id="thread-1",
        name="New Thread 11:30 AM 22/6/2026",
        created_at=datetime(2026, 6, 22, 12, 0, 0),
        updated_at=datetime(2026, 6, 22, 12, 5, 0),
        messages=[Message(role="user", content="asdf").to_dict()],
    )

    store.add(thread)
    json_path = tmp_path / "threads" / "thread-1.json"
    assert json_path.is_file()

    data = json.loads(json_path.read_text(encoding="utf-8"))
    assert data["name"] == "New Thread 11:30 AM 22/6/2026"
    assert len(data["messages"]) == 1

    reloaded = ThreadStore(tmp_path / "threads")
    reloaded.load()
    assert len(reloaded.all()) == 1
    assert reloaded.get("thread-1").name == "New Thread 11:30 AM 22/6/2026"

    store.remove(thread)
    assert not json_path.exists()
    assert store.is_empty()
