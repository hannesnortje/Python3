# main.py

import sys
import os
from PyQt6.QtWidgets import QApplication
from browser import Browser

if __name__ == "__main__":
    # Set the QT_QPA_PLATFORM environment variable based on display server
    if "WAYLAND_DISPLAY" in os.environ:
        os.environ["QT_QPA_PLATFORM"] = "wayland"
        os.environ["QT_QUICK_BACKEND"] = "software"  # Use software rendering for Wayland
        os.environ["QT_WAYLAND_DISABLE_WINDOWDECORATION"] = "1"  # Disable window decorations if on Wayland
    else:
        os.environ["QT_QPA_PLATFORM"] = "xcb"  # Fallback to X11 if Wayland is not available

    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web4x Browser")
    window = Browser()

    # Launch the application
    app.exec()
