# code_executor.py

from PyQt6.QtCore import QObject, pyqtSignal, pyqtSlot, QVariant

class CodeExecutor(QObject):
    codeResultReady = pyqtSignal(QVariant)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(QVariant)
    def executeSignal(self, incoming):
        print(f"Received from JavaScript: {incoming}")
        self.codeResultReady.emit(incoming)
