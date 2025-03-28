import os
import sys
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QVariant, QThread

class FileSystemHandler(QObject):
    fileCreated = pyqtSignal(str)
    directoryCreated = pyqtSignal(str)
    fileChanged = pyqtSignal(str)
    fileDeleted = pyqtSignal(str)
    directoryDeleted = pyqtSignal(str)
    errorOccurred = pyqtSignal(str)
    fileRead = pyqtSignal(str, str)  # Signal for file read completion

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_path = os.path.expanduser("~")  # Default to home directory
        if sys.platform == "win32":
            self.base_path = os.path.join(self.base_path, "Documents") # Example of OS specific change

    @pyqtSlot(str, str)
    def createFile(self, filePath, content):
        full_path = os.path.join(self.base_path, filePath)
        try:
            with open(full_path, 'w') as f:
                f.write(content)
            self.fileCreated.emit(filePath)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @pyqtSlot(str)
    def createDirectory(self, dirPath):
        full_path = os.path.join(self.base_path, dirPath)
        try:
            os.makedirs(full_path, exist_ok=True)
            self.directoryCreated.emit(dirPath)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @pyqtSlot(str, str)
    def changeFileContent(self, filePath, content):
        full_path = os.path.join(self.base_path, filePath)
        try:
            with open(full_path, 'w') as f:
                f.write(content)
            self.fileChanged.emit(filePath)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @pyqtSlot(str)
    def deleteFile(self, filePath):
        full_path = os.path.join(self.base_path, filePath)
        try:
            os.remove(full_path)
            self.fileDeleted.emit(filePath)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @pyqtSlot(str)
    def deleteDirectory(self, dirPath):
        full_path = os.path.join(self.base_path, dirPath)
        try:
            os.rmdir(full_path)  # Only works for empty directories
            self.directoryDeleted.emit(dirPath)
        except Exception as e:
            self.errorOccurred.emit(str(e))

    @pyqtSlot(str)
    def readFile(self, filePath):
        full_path = os.path.join(self.base_path, filePath)
        try:
            with open(full_path, 'r') as f:
                content = f.read()
            self.fileRead.emit(filePath, content)
        except Exception as e:
            self.errorOccurred.emit(str(e))
