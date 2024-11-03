# browser.py

import sys
from PyQt6.QtCore import QUrl, QSettings, QDateTime, Qt
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QMenu, QTabWidget, QFileDialog, QDialog, QLabel, QScrollArea, QVBoxLayout, QWidget, QStyle
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from collections import defaultdict

from code_executor import CodeExecutor
from dev_tools_window import DevToolsWindow
from browser_tab import BrowserTab


class Browser(QMainWindow):
    def __init__(self):
        super().__init__()

        # Persistent settings storage
        self.settings = QSettings("CeruleanCircle", "Web4xBrowser")

        # Core components
        self.url_bar = QLineEdit()
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)  # Connect the tab close event
        self.setCentralWidget(self.tabs)

        # JavaScript-Python bridge
        self.code_executor = CodeExecutor()
        self.channel = QWebChannel()
        self.channel.registerObject("codeExecutor", self.code_executor)

        # Initialize Developer Tools window
        self.dev_tools_window = DevToolsWindow(self)
        self.dev_tools_window.hide()

        # History tracking
        self.history = []
        self.recently_closed = []

        # Default zoom level
        self.zoom_level = 1.0
        self.setup_navigation()

        # Load saved tabs on startup
        self.load_saved_tabs()

        # Add default tab if no saved tabs exist
        if self.tabs.count() == 0:
            self.add_new_tab(QUrl("https://www.example.com"), "Home")

        # Connect tab change to URL bar update
        self.tabs.currentChanged.connect(self.update_url_bar)
        
        # Show browser maximized
        self.showMaximized()

    def setup_navigation(self):
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        # Back button
        self.back_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self)
        self.back_action.setToolTip("Go back to the previous page")
        self.back_action.triggered.connect(self.go_back)
        nav_bar.addAction(self.back_action)

        # Forward button
        self.forward_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Forward", self)
        self.forward_action.setToolTip("Go forward to the next page")
        self.forward_action.triggered.connect(self.go_forward)
        nav_bar.addAction(self.forward_action)

        # Reload button
        self.reload_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Reload", self)
        self.reload_action.setToolTip("Reload the current page")
        self.reload_action.triggered.connect(self.reload_page)
        nav_bar.addAction(self.reload_action)

        # New Tab button
        new_tab_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Tab", self)
        new_tab_action.setToolTip("Open a new tab")
        new_tab_action.triggered.connect(lambda: self.add_new_tab(QUrl("https://www.example.com"), "New Tab"))
        nav_bar.addAction(new_tab_action)

        # URL Bar
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # Three-dot menu with History and Zoom options
        three_dot_menu = QMenu("More", self)

        # History menu
        history_menu = three_dot_menu.addMenu("History")
        view_all_action = QAction("View All History", self)
        view_all_action.triggered.connect(self.open_all_history_tab)
        history_menu.addAction(view_all_action)

        recent_tabs_menu = history_menu.addMenu("Recently Closed")
        self.update_recent_tabs_menu(recent_tabs_menu)

        recent_history_menu = history_menu.addMenu("Recent History")
        self.update_recent_history_menu(recent_history_menu)

        # Zoom controls
        zoom_menu = three_dot_menu.addMenu("Zoom")
        zoom_in_action = QAction("Zoom In (+)", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out (-)", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_menu.addAction(zoom_out_action)

        # Display current zoom level
        self.zoom_label_action = QAction(f"Zoom: {self.zoom_level * 100:.0f}%", self)
        self.zoom_label_action.setEnabled(False)
        zoom_menu.addAction(self.zoom_label_action)

        # Add the three-dot menu to the navigation bar
        three_dot_button = QAction("⋮", self)
        three_dot_button.setMenu(three_dot_menu)
        nav_bar.addAction(three_dot_button)

        # Connect the tab change and URL change events to update navigation actions
        self.tabs.currentChanged.connect(self.update_navigation_actions)

    def current_browser(self):
        """Return the current QWebEngineView instance."""
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, BrowserTab):
            return current_widget.browser
        return None

    def update_navigation_actions(self):
        """Update the navigation action states based on the current browser's history."""
        browser = self.current_browser()
        if browser:
            self.back_action.setEnabled(browser.history().canGoBack())
            self.forward_action.setEnabled(browser.history().canGoForward())
            browser.urlChanged.connect(lambda: self.update_navigation_actions())
        else:
            self.back_action.setEnabled(False)
            self.forward_action.setEnabled(False)

    def go_back(self):
        """Navigate back in the current browser's history."""
        browser = self.current_browser()
        if browser:
            browser.back()

    def go_forward(self):
        """Navigate forward in the current browser's history."""
        browser = self.current_browser()
        if browser:
            browser.forward()

    def reload_page(self):
        """Reload the current page in the active browser."""
        browser = self.current_browser()
        if browser:
            print("Reloading page...")  # Debugging print statement to ensure this method is called
            # Attempt to force reload by stopping the page first
            browser.stop()
            browser.reload()
        else:
            print("No active browser to reload.")

    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar."""
        url_text = self.url_bar.text()
        url = QUrl(url_text)
        if url.scheme() == "":
            url.setScheme("http")
        self.current_browser().setUrl(url)

    def update_url_bar(self):
        """Update the URL bar with the URL of the current tab's page."""
        current_browser = self.current_browser()
        if current_browser:
            self.url_bar.setText(current_browser.url().toString())
        else:
            self.url_bar.clear()

    def add_new_tab(self, url=None, title="New Tab"):
        """Add a new tab with the specified URL and title."""
        new_tab = BrowserTab(url, self)
        
        new_tab.browser.page().setWebChannel(self.channel)
        new_tab.browser.titleChanged.connect(lambda title, tab=new_tab: self.update_tab_title(tab, title))
        new_tab.browser.urlChanged.connect(self.update_url_bar)  # Connect URL change to update URL bar
        new_tab.browser.urlChanged.connect(lambda url: self.record_history(url))
        
        index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)
        
        new_tab.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        new_tab.browser.customContextMenuRequested.connect(self.open_context_menu)

    def close_tab(self, index):
        """Close a tab and optionally save it to recently closed tabs."""
        closed_tab = self.tabs.widget(index)
        if isinstance(closed_tab, BrowserTab):
            self.recently_closed.append(closed_tab.browser.url().toString())
        self.tabs.removeTab(index)

    def update_tab_title(self, tab, title):
        """Update the title of a tab in the tab bar."""
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def open_context_menu(self, position):
        """Open the context menu with actions for Copy, Paste, Cut, Save As, Print, and Developer Tools."""
        menu = QMenu()
        browser = self.current_browser()  # Get the current QWebEngineView instance

        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: browser.page().runJavaScript("document.execCommand('copy');"))
        menu.addAction(copy_action)

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: browser.page().runJavaScript("document.execCommand('cut');"))
        menu.addAction(cut_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: browser.page().runJavaScript("document.execCommand('paste');"))
        menu.addAction(paste_action)

        save_action = QAction("Save As...", self)
        save_action.triggered.connect(self.save_as)
        menu.addAction(save_action)

        print_action = QAction("Print...", self)
        print_action.triggered.connect(self.print_page)
        menu.addAction(print_action)

        inspect_action = QAction("Developer Tools", self)
        inspect_action.triggered.connect(self.open_dev_tools)
        menu.addAction(inspect_action)

        menu.exec(QCursor.pos())

    def save_as(self):
        """Save the current page as an HTML file."""
        page = self.current_browser().page()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "Webpage (*.html);;All Files (*)")
        if file_name:
            page.toHtml(lambda html: self.save_file(html, file_name))

    def save_file(self, html, file_name):
        """Write the HTML content to a file."""
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(html)
        print(f"Page saved as {file_name}")

    def print_page(self):
        """Open a print dialog for the current page."""
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:  # 'Accepted' is uppercase here
            self.current_browser().page().print(printer, lambda success: print("Printed" if success else "Print failed"))

    def open_dev_tools(self):
        """Open the Developer Tools window for the current tab."""
        if not self.dev_tools_window.isVisible():
            self.dev_tools_window.show()
            self.current_browser().page().setDevToolsPage(self.dev_tools_window.dev_tools_view.page())

    def record_history(self, url):
        """Record the history of visited URLs."""
        timestamp = QDateTime.currentDateTime()
        self.history.append((timestamp, url.toString()))
        if len(self.history) > 100:
            self.history.pop(0)

    def open_all_history_tab(self):
        """Open a new tab displaying all history."""
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
                entry_label.linkActivated.connect(lambda link=url: self.add_new_tab(QUrl(link), "History"))
                content_layout.addWidget(entry_label)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        history_tab.setLayout(layout)

        index = self.tabs.addTab(history_tab, "History")
        self.tabs.setCurrentIndex(index)

    def update_recent_tabs_menu(self, recent_tabs_menu):
        """Update the 'Recently Closed' submenu in the history menu."""
        recent_tabs_menu.clear()
        for url in self.recently_closed[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "Reopened Tab"))
            recent_tabs_menu.addAction(action)

    def update_recent_history_menu(self, recent_history_menu):
        """Update the 'Recent History' submenu in the history menu."""
        recent_history_menu.clear()
        for _, url in self.history[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "History Tab"))
            recent_history_menu.addAction(action)

    def zoom_in(self):
        """Zoom in the current browser's view."""
        self.zoom_level += 0.1
        self.current_browser().setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def zoom_out(self):
        """Zoom out the current browser's view."""
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.current_browser().setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def load_saved_tabs(self):
        """Load tabs from the previous session."""
        saved_urls = self.settings.value("openTabs", [])
        for url in saved_urls:
            self.add_new_tab(QUrl(url), "Restored Tab")

    def closeEvent(self, event):
        """Handle the window close event and save the current open tabs."""
        open_tabs = [self.tabs.widget(i).browser.url().toString() for i in range(self.tabs.count())]
        self.settings.setValue("openTabs", open_tabs)
        event.accept()
