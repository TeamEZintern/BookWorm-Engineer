"""
Ask-user bridge for GUI agent runs.

Tools may call ``ask_user`` from a background thread. Qt widgets must be used
on the GUI thread, so this bridge marshals prompts with a blocking queued call.
"""

from PySide6.QtCore import QObject, Qt, Slot
from PySide6.QtWidgets import QInputDialog, QWidget


class AskUserBridge(QObject):
    """Show ask_user prompts on the GUI thread."""

    def __init__(self, parent: QWidget):
        super().__init__(parent)
        self._parent = parent

    @Slot(str, result=str)
    def _prompt(self, question: str) -> str:
        text, ok = QInputDialog.getText(self._parent, "BookWorm", question)
        return text if ok else ""

    def ask(self, question: str) -> str:
        from PySide6.QtCore import QMetaObject, Q_ARG

        result = QMetaObject.invokeMethod(
            self,
            "_prompt",
            Qt.ConnectionType.BlockingQueuedConnection,
            Q_ARG(str, question),
        )
        return result or ""
