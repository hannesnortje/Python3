import sys
from PyQt6.QtWidgets import QApplication
from .browser import Browser  # assuming your Browser class is in this file

def main():
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web4x Browser")
    window = Browser()
    window.inject_javascript()
    window.show()
    sys.exit(app.exec())
