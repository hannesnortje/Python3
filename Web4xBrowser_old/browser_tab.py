# browser_tab.py

from PyQt6.QtCore import QUrl
from PyQt6.QtWidgets import QWidget, QVBoxLayout
from PyQt6.QtWebEngineWidgets import QWebEngineView

class BrowserTab(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        
        self.layout = QVBoxLayout(self)
        self.browser = QWebEngineView()
        self.browser.setUrl(url)
        self.layout.addWidget(self.browser)
        self.setLayout(self.layout)
