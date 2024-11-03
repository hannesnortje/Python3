# main.py

import sys
from PyQt6.QtWidgets import QApplication
from browser import Browser

if __name__ == "__main__":
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web4x Browser")
    window = Browser()

    app.exec()
