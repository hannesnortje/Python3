# tab_manager.py

from PyQt6.QtCore import QUrl, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QMenu

from browser_tab import BrowserTab


class TabManager:
    def __init__(self, browser):
        self.browser = browser
        self.tabs = browser.tabs
        self.browser.tabs.tabCloseRequested.connect(self.close_tab)

    def add_new_tab(self, url=None, title="New Tab"):
        """Add a new tab with the specified URL and title."""
        new_tab = BrowserTab(url, self.browser)
        new_tab.browser.page().setWebChannel(self.browser.channel)
        new_tab.browser.setUrl(url)
        new_tab.browser.titleChanged.connect(lambda title, tab=new_tab: self.update_tab_title(tab, title))
        new_tab.browser.urlChanged.connect(self.browser.navigation_bar.update_url_bar)
        new_tab.browser.urlChanged.connect(lambda url: self.browser.history_manager.record_history(url))

        # Set up the context menu with Developer Tools option
        new_tab.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        new_tab.browser.customContextMenuRequested.connect(self.open_context_menu)

        index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)

    def open_context_menu(self, position):
        """Open the context menu with Developer Tools option."""
        menu = QMenu()

        # Option for Developer Tools
        inspect_action = QAction("Developer Tools", self.browser)
        inspect_action.triggered.connect(self.browser.open_dev_tools)
        menu.addAction(inspect_action)

        # Additional context menu options (e.g., Copy, Paste) can be added here if needed
        menu.exec(position)

    def close_tab(self, index):
        """Close a tab and optionally save it to recently closed tabs."""
        closed_tab = self.tabs.widget(index)
        if isinstance(closed_tab, BrowserTab):
            self.browser.history_manager.recently_closed.append(closed_tab.browser.url().toString())
        self.tabs.removeTab(index)

    def update_tab_title(self, tab, title):
        """Update the title of a tab in the tab bar."""
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def load_saved_tabs(self):
        """Load tabs from saved session."""
        saved_urls = self.browser.settings.value("openTabs", [])
        for url in saved_urls:
            self.add_new_tab(QUrl(url), "Restored Tab")

    def save_open_tabs(self):
        """Save the current open tabs for session restoration."""
        open_tabs = [self.tabs.widget(i).browser.url().toString() for i in range(self.tabs.count())]
        self.browser.settings.setValue("openTabs", open_tabs)

    def current_browser(self):
        """Return the currently active QWebEngineView."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, BrowserTab):
            return current_widget.browser
        return None
