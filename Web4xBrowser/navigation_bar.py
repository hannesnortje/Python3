# navigation_bar.py

from PyQt6.QtCore import QUrl
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QToolBar, QMenu, QStyle


class NavigationBar:
    def __init__(self, browser):
        self.browser = browser
        self.setup_navigation()

    def setup_navigation(self):
        nav_bar = QToolBar()
        self.browser.addToolBar(nav_bar)

        # Back button
        self.browser.back_action = QAction(self.browser.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self.browser)
        self.browser.back_action.triggered.connect(lambda: self.browser.tab_manager.current_browser().back())
        nav_bar.addAction(self.browser.back_action)

        # Forward button
        self.browser.forward_action = QAction(self.browser.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Forward", self.browser)
        self.browser.forward_action.triggered.connect(lambda: self.browser.tab_manager.current_browser().forward())
        nav_bar.addAction(self.browser.forward_action)

        # Reload button
        reload_action = QAction(self.browser.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Reload", self.browser)
        reload_action.triggered.connect(lambda: self.browser.tab_manager.current_browser().reload())
        nav_bar.addAction(reload_action)

        # New Tab button
        new_tab_action = QAction(self.browser.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Tab", self.browser)
        new_tab_action.triggered.connect(lambda: self.browser.tab_manager.add_new_tab(QUrl("https://www.example.com"), "New Tab"))
        nav_bar.addAction(new_tab_action)

        # URL Bar
        self.browser.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.browser.url_bar)

    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar."""
        url_text = self.browser.url_bar.text()
        url = QUrl(url_text)
        if url.scheme() == "":
            url.setScheme("http")
        self.browser.tab_manager.current_browser().setUrl(url)

    def update_url_bar(self):
        """Update the URL bar with the current tab's URL."""
        current_browser = self.browser.tab_manager.current_browser()
        if current_browser:
            self.browser.url_bar.setText(current_browser.url().toString())
        else:
            self.browser.url_bar.clear()
