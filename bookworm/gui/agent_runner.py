"""
Background runner for Agent turns in the GUI.

Runs ``Agent.run_turn()`` off the UI thread and emits Qt signals with the
result or error.
"""

from PySide6.QtCore import QObject, QThread, Signal

from bookworm.agent import Agent


class _TurnWorker(QObject):
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, agent: Agent):
        super().__init__()
        self._agent = agent

    def run_turn(self) -> None:
        try:
            self.finished.emit(self._agent.run_turn())
        except Exception as exc:
            self.failed.emit(str(exc))


class AgentRunner(QObject):
    """Execute agent turns on a worker thread."""

    response_ready = Signal(str)
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
        worker.finished.connect(self.response_ready.emit)
        worker.failed.connect(self.error.emit)
        worker.finished.connect(thread.quit)
        worker.failed.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        worker.failed.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_worker)

        self._thread = thread
        self._worker = worker
        thread.start()

    def _clear_worker(self) -> None:
        self._thread = None
        self._worker = None
