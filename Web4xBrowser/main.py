# main.py
import sys
from cefpython3 import cefpython as cef
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtCore import QTimer

class CEFWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.browser = None
        self.init_cef(url)

    def init_cef(self, url):
        # Set up the layout for the CEF widget
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create the CEF browser instance within this widget
        window_info = cef.WindowInfo()
        window_info.SetAsChild(int(self.winId()))
        self.browser = cef.CreateBrowserSync(window_info, url=url)

        # Timer to keep the CEF message loop running
        self.timer = QTimer(self)
        self.timer.timeout.connect(cef.MessageLoopWork)
        self.timer.start(10)

    def navigate(self, url):
        if self.browser:
            self.browser.LoadUrl(url)

    def closeEvent(self, event):
        # Cleanly shut down the CEF browser instance
        self.timer.stop()
        if self.browser:
            self.browser.CloseBrowser(True)
        cef.Shutdown()
        event.accept()

class BrowserApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CEF Browser Example")
        self.setGeometry(300, 100, 1024, 768)

        # Initialize the browser with a default URL
        self.browser_widget = CEFWidget("https://www.example.com", self)
        self.setCentralWidget(self.browser_widget)

def main():
    # Initialize CEF
    cef.Initialize()

    # Set up the Qt application
    app = QApplication(sys.argv)
    window = BrowserApp()
    window.show()

    # Run the Qt application
    app.exec()

    # Shutdown CEF after app closes
    cef.Shutdown()

if __name__ == "__main__":
    main()

