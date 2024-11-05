import sys
from PySide6.QtCore import QDateTime, QTimer, QSettings
from PySide6.QtGui import QAction, QTextDocument, QCursor
from PySide6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QMenu, QTabWidget, QWidget, QVBoxLayout, QFileDialog, QDialog, QLabel, QScrollArea, QStyle
from cefpython3 import cefpython as cef
from collections import defaultdict

class CEFWidget(QWidget):
    def __init__(self, url, parent=None):
        super().__init__(parent)
        self.browser = None
        self.init_cef(url)

    def init_cef(self, url):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create a CEF browser window in this QWidget
        window_info = cef.WindowInfo()
        window_info.SetAsChild(int(self.winId()))
        self.browser = cef.CreateBrowserSync(window_info, url=url)

        # Start a timer to keep updating CEF
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.on_timer)
        self.timer.start(10)  # Update CEF every 10 ms

    def on_timer(self):
        cef.MessageLoopWork()

    def navigate(self, url):
        if self.browser:
            self.browser.LoadUrl(url)

    def closeEvent(self, event):
        self.timer.stop()
        if self.browser:
            self.browser.CloseBrowser(True)
        cef.Shutdown()
        event.accept()


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Initialize CEF settings
        self.settings = QSettings("CeruleanCircle", "Web4xBrowser")
        cef.Initialize()

        self.url_bar = QLineEdit()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.setCentralWidget(self.tabs)

        self.history = []
        self.recently_closed = []
        self.zoom_level = 1.0

        self.setup_navigation()
        self.load_saved_tabs()

        # Open a default tab if none are restored
        if self.tabs.count() == 0:
            self.add_new_tab("https://www.example.com", "Home")

        self.tabs.currentChanged.connect(self.update_url_bar)
        self.showMaximized()

    def setup_navigation(self):
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        # Back button
        self.back_action = QAction(self.style().standardIcon(QStyle.SP_ArrowBack), "Back", self)
        self.back_action.triggered.connect(lambda: self.current_browser().browser.GoBack())
        nav_bar.addAction(self.back_action)

        # Forward button
        self.forward_action = QAction(self.style().standardIcon(QStyle.SP_ArrowForward), "Forward", self)
        self.forward_action.triggered.connect(lambda: self.current_browser().browser.GoForward())
        nav_bar.addAction(self.forward_action)

        # Reload button
        reload_action = QAction(self.style().standardIcon(QStyle.SP_BrowserReload), "Reload", self)
        reload_action.triggered.connect(lambda: self.current_browser().browser.Reload())
        nav_bar.addAction(reload_action)

        # New Tab button
        new_tab_action = QAction(self.style().standardIcon(QStyle.SP_FileDialogNewFolder), "New Tab", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab("https://www.example.com", "New Tab"))
        nav_bar.addAction(new_tab_action)

        # URL bar
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # Menu with history and zoom options
        three_dot_menu = QMenu("More", self)
        history_menu = three_dot_menu.addMenu("History")

        view_all_action = QAction("View All History", self)
        view_all_action.triggered.connect(self.open_all_history_tab)
        history_menu.addAction(view_all_action)

        recent_tabs_menu = history_menu.addMenu("Recently Closed")
        self.update_recent_tabs_menu(recent_tabs_menu)

        recent_history_menu = history_menu.addMenu("Recent History")
        self.update_recent_history_menu(recent_history_menu)

        zoom_menu = three_dot_menu.addMenu("Zoom")
        zoom_in_action = QAction("Zoom In (+)", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out (-)", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_menu.addAction(zoom_out_action)

        self.zoom_label_action = QAction(f"Zoom: {self.zoom_level * 100:.0f}%", self)
        self.zoom_label_action.setEnabled(False)
        zoom_menu.addAction(self.zoom_label_action)

        three_dot_button = QAction("⋮", self)
        three_dot_button.setMenu(three_dot_menu)
        nav_bar.addAction(three_dot_button)

    def current_browser(self):
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, CEFWidget):
            return current_widget
        return None

    def navigate_to_url(self):
        url = self.url_bar.text()
        if self.current_browser():
            self.current_browser().navigate(url)

    def update_url_bar(self):
        if self.current_browser():
            self.url_bar.setText(self.current_browser().browser.GetUrl())

    def add_new_tab(self, url, title="New Tab"):
        new_tab = CEFWidget(url, self)
        index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)

    def close_tab(self, index):
        closed_tab = self.tabs.widget(index)
        if isinstance(closed_tab, CEFWidget):
            self.recently_closed.append(closed_tab.browser.GetUrl())
        self.tabs.removeTab(index)

    def open_all_history_tab(self):
        history_data = defaultdict(list)
        for timestamp, url in self.history:
            date = timestamp.date().toString("dddd, MMMM d, yyyy")
            time = timestamp.time().toString("hh:mm AP")
            history_data[date].append((time, url))

        history_tab = QWidget()
        scroll_area = QScrollArea()
        layout = QVBoxLayout()
        scroll_area.setWidgetResizable(True)
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        for date, entries in history_data.items():
            date_label = QLabel(f"<b>{date}</b>")
            content_layout.addWidget(date_label)
            
            for time, url in entries:
                entry_label = QLabel(f"<span style='color: grey;'>{time}</span> - <a href='{url}'>{url}</a>")
                entry_label.setOpenExternalLinks(False)
                entry_label.linkActivated.connect(lambda link=url: self.add_new_tab(link, "History"))
                content_layout.addWidget(entry_label)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        history_tab.setLayout(layout)

        index = self.tabs.addTab(history_tab, "History")
        self.tabs.setCurrentIndex(index)

    def zoom_in(self):
        self.zoom_level += 0.1
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def zoom_out(self):
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def load_saved_tabs(self):
        saved_urls = self.settings.value("openTabs", [])
        for url in saved_urls:
            self.add_new_tab(url, "Restored Tab")

    def closeEvent(self, event):
        open_tabs = [self.tabs.widget(i).browser.GetUrl() for i in range(self.tabs.count())]
        self.settings.setValue("openTabs", open_tabs)
        event.accept()
        cef.Shutdown()


def main():
    # Initialize the application and CEF
    cef_settings = {}
    cef.Initialize(cef_settings)

    app = QApplication(sys.argv)
    window = Browser()
    window.show()
    
    app.exec()
    cef.Shutdown()


if __name__ == "__main__":
    main()
