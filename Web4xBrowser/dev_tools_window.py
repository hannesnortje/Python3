# dev_tools_window.py

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMainWindow, QToolBar
from PyQt6.QtWebEngineWidgets import QWebEngineView


class DevToolsWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.dev_tools_view = QWebEngineView()
        self.setCentralWidget(self.dev_tools_view)
        
        self.setWindowTitle("Developer Tools")
        self.resize(800, 600)

        # Default zoom level
        self.zoom_level = 1.0

        # Toolbar with actions
        toolbar = QToolBar("DevTools Toolbar")
        self.addToolBar(toolbar)

        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)

        reload_action = QAction("Reload DevTools", self)
        reload_action.triggered.connect(self.dev_tools_view.reload)
        toolbar.addAction(reload_action)

        # Zoom controls
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        # Display current zoom level
        self.zoom_label_action = QAction(f"Zoom: {self.zoom_level * 100:.0f}%", self)
        self.zoom_label_action.setEnabled(False)
        toolbar.addAction(self.zoom_label_action)

        # Enable keyboard shortcuts for zoom in/out
        self.dev_tools_view.installEventFilter(self)

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Plus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_in()
                return True
            elif event.key() == Qt.Key.Key_Minus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_out()
                return True
        return super().eventFilter(source, event)

    def zoom_in(self):
        self.zoom_level += 0.1
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def zoom_out(self):
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")
