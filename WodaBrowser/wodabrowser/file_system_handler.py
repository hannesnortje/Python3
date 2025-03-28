import os
from PyQt6.QtCore import QObject, pyqtSlot, pyqtSignal, QMetaObject, Q_ARG, Qt

class FileSystemHandler(QObject):
    # Define signals with explicit names and signature
    fileRead = pyqtSignal(str, str, name='fileRead')
    fileCreated = pyqtSignal(str, name='fileCreated')
    fileChanged = pyqtSignal(str, name='fileChanged')
    fileDeleted = pyqtSignal(str, name='fileDeleted')
    directoryCreated = pyqtSignal(str, name='directoryCreated')
    directoryDeleted = pyqtSignal(str, name='directoryDeleted')
    errorOccurred = pyqtSignal(str, name='errorOccurred')

    def __init__(self, parent=None):
        super().__init__(parent)
        self.base_path = "/"
        self.setObjectName('fileSystemHandler')
        self._signal_map = {}
        self._register_signals()
        print("FileSystemHandler initialized with name:", self.objectName())
        self._debug_signals()

    def _register_signals(self):
        """Register signals with QMetaObject system."""
        self._signal_map = {
            'fileRead': self.fileRead,
            'fileCreated': self.fileCreated,
            'fileChanged': self.fileChanged,
            'fileDeleted': self.fileDeleted,
            'directoryCreated': self.directoryCreated,
            'directoryDeleted': self.directoryDeleted,
            'errorOccurred': self.errorOccurred
        }
        print("Registered signals:", list(self._signal_map.keys()))

    def _debug_signals(self):
        """Debug helper to list available signals."""
        signals = {}
        for name, signal in self._signal_map.items():
            signals[name] = {
                'type': str(type(signal)),
                'name': getattr(signal, 'signal', name)
            }
        print(f"Available signals: {signals}")

    def _resolve_path(self, path):
        """Resolve path to either absolute or relative to base_path."""
        if path.startswith("/"):
            return path
        return os.path.join(self.base_path, path)

    @pyqtSlot(str)
    def readFile(self, filePath):
        """Read a file and emit its content."""
        full_path = self._resolve_path(filePath)
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            self.fileRead.emit(filePath, content)
        except Exception as e:
            error_msg = f"Error reading file {filePath}: {str(e)}"
            print(error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(str, str)
    def createFile(self, filePath, content):
        """Create a file with the given content."""
        print(f"Creating file: {filePath}")
        full_path = self._resolve_path(filePath)
        try:
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"File created successfully: {filePath}")
            print(f"Emitting fileCreated signal with path: {filePath}")
            self.fileCreated.emit(filePath)
            print(f"Signal emission completed")
        except Exception as e:
            error_msg = f"Error creating file {filePath}: {str(e)}"
            print(error_msg)
            print(f"Emitting errorOccurred signal with message: {error_msg}")
            self.errorOccurred.emit(error_msg)
            print(f"Error signal emission completed")

    @pyqtSlot(str)
    def createDirectory(self, dirPath: str) -> None:
        """Create a directory and emit appropriate signals."""
        print(f"Creating directory: {dirPath}")
        try:
            os.makedirs(dirPath, exist_ok=True)
            print(f"Directory created successfully: {dirPath}")
            # Add more logging for signal emission
            print(f"Emitting directoryCreated signal with path: {dirPath}")
            self.directoryCreated.emit(dirPath)
            print(f"Signal emission completed")
        except Exception as e:
            error_msg = f"Error creating directory {dirPath}: {str(e)}"
            print(error_msg)
            print(f"Emitting errorOccurred signal with message: {error_msg}")
            self.errorOccurred.emit(error_msg)
            print(f"Error signal emission completed")

    @pyqtSlot(str, str)
    def changeFileContent(self, filePath, content):
        """Change the content of a file."""
        full_path = self._resolve_path(filePath)
        try:
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            self.fileChanged.emit(filePath)
        except Exception as e:
            error_msg = f"Error changing file content {filePath}: {str(e)}"
            print(error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(str)
    def deleteFile(self, filePath):
        """Delete a file."""
        full_path = self._resolve_path(filePath)
        try:
            os.remove(full_path)
            self.fileDeleted.emit(filePath)
        except Exception as e:
            error_msg = f"Error deleting file {filePath}: {str(e)}"
            print(error_msg)
            self.errorOccurred.emit(error_msg)

    @pyqtSlot(str)
    def deleteDirectory(self, dirPath):
        """Delete a directory."""
        full_path = self._resolve_path(dirPath)
        try:
            os.rmdir(full_path)  # Only works for empty directories
            self.directoryDeleted.emit(dirPath)
        except Exception as e:
            error_msg = f"Error deleting directory {dirPath}: {str(e)}"
            print(error_msg)
            self.errorOccurred.emit(error_msg)

    def __getattr__(self, name):
        """Intercept signal access for better debugging."""
        print(f"Accessing attribute: {name}")
        # Handle signal access
        if name in self._signal_map:
            print(f"Returning registered signal: {name}")
            return self._signal_map[name]
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")
