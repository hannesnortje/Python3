import sys
import os
from PyQt6.QtWidgets import QApplication

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Determine if the script is run directly or imported as a module
if __name__ == "__main__":
    from web4x_browser.browser import Browser, run_browser
else:
    from .browser import Browser, run_browser

def main():
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web4x Browser")
    run_browser()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
