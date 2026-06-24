"""
Background runner for Agent turns in the GUI.

Runs ``Agent.run_turn_with_events()`` off the UI thread and emits Qt signals
mirroring the agent event protocol.
"""

from typing import Any

from PySide6.QtCore import QObject, QThread, Signal

from bookworm.agent import Agent
from bookworm.agent_events import TurnEventHandler


class _TurnWorker(QObject):
    turn_complete = Signal(str, list)
    text_delta = Signal(str)
    tool_call_started = Signal(str, str, str)
    tool_result = Signal(str, str)
    reasoning_delta = Signal(str)
    failed = Signal(str)

    def __init__(self, agent: Agent):
        super().__init__()
        self._agent = agent

    def run_turn(self) -> None:
        handler = TurnEventHandler(
            on_text_delta=self.text_delta.emit,
            on_tool_call_started=self.tool_call_started.emit,
            on_tool_result=self.tool_result.emit,
            on_reasoning_delta=self.reasoning_delta.emit,
            on_turn_complete=self._on_turn_complete,
        )
        try:
            self._agent.run_turn_with_events(handler)
        except Exception as exc:
            self.failed.emit(str(exc))

    def _on_turn_complete(self, content: str, tool_calls: list[dict[str, Any]]) -> None:
        self.turn_complete.emit(content, tool_calls)


class AgentRunner(QObject):
    """Execute agent turns on a worker thread."""

    text_delta = Signal(str)
    tool_call_started = Signal(str, str, str)
    tool_result = Signal(str, str)
    reasoning_delta = Signal(str)
    turn_complete = Signal(str, list)
    error = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._thread: QThread | None = None
        self._worker: _TurnWorker | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.isRunning()

    def start_turn(self, agent: Agent) -> None:
        if self.is_running():
            return

        thread = QThread()
        worker = _TurnWorker(agent)
        worker.moveToThread(thread)

        thread.started.connect(worker.run_turn)
        worker.text_delta.connect(self.text_delta.emit)
        worker.tool_call_started.connect(self.tool_call_started.emit)
        worker.tool_result.connect(self.tool_result.emit)
        worker.reasoning_delta.connect(self.reasoning_delta.emit)
        worker.turn_complete.connect(self.turn_complete.emit)
        worker.failed.connect(self.error.emit)
        worker.turn_complete.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.turn_complete.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_worker)

        self._thread = thread
        self._worker = worker
        thread.start()

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None
