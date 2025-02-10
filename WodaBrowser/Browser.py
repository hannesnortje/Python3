"""
/*
 * SPDX-License-Identifier: AGPL-3.0-or-later AND LicenseRef-Qt-Commercial OR LGPL-3.0-only OR GPL-2.0-only OR GPL-3.0-only
 *
 * This file is part of the Web 4.0 ™ platform, developed and supported by Cerulean Circle GmbH.
 * The Web 4.0 ™ platform is licensed under a subscription model for enterprise customers.
 * 
 * This software includes portions adapted from code originally authored by:
 *    The Qt Company Ltd and Klarälvdalens Datakonsult AB, a KDAB Group company, and author Milian Wolff <milian.wolff@kdab.com>
 *
 * This adaptation and additional modifications are authored by Hannes Nortjé.
 *
 * License:
 *   This program is distributed as free software under the GNU Affero General Public License (AGPL-3.0-or-later),
 *   as published by the Free Software Foundation. You may redistribute and/or modify it under the terms of the AGPL
 *   Version 3 or, at your discretion, any later version. 
 *
 * Warranty:
 *   This program is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied 
 *   warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Affero General Public License for more details.
 *
 * Licensing Documentation:
 *   You should have received a copy of the GNU Affero General Public License along with this program.
 *   If not, see <https://www.gnu.org/licenses/>.
 *
 * Qt Licensing:
 *   The original code from Qt is licensed under multiple options, including the Qt Commercial License, LGPL-3.0-only, 
 *   GPL-2.0-only, and GPL-3.0-only.
 *
 * License Metadata:
 * {
 *   "license": "AGPL-3.0",
 *   "href": "https://www.gnu.org/licenses/agpl-3.0.html",
 *   "coAuthors": ["Hannes Nortjé"]
 * }
 */
"""

import sys
from PyQt6.QtCore import (
    QUrl,
    Qt,
    QThread,
    pyqtSlot,
    pyqtSignal,
    QObject,
    QVariant,
    QDateTime,
    QSettings,
    QEvent,
    QRunnable,
    QThreadPool,
    QTimer,
    QMutex,
    QWaitCondition
)
from PyQt6.QtGui import QAction, QCursor, QTextDocument, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QToolBar,
    QLineEdit,
    QMenu,
    QTabWidget,
    QWidget,
    QVBoxLayout,
    QFileDialog,
    QDialog,
    QLabel,
    QScrollArea,
    QStyle,
)
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from collections import defaultdict
import typing
import os
from file_system_handler import FileSystemHandler
from functools import partial

# Constants
MAX_HISTORY_LENGTH = 100
DEFAULT_URL = "https://google.com"
BROWSER_TITLE = "Web4x Browser"
SETTINGS_ORG = "CeruleanCircle"
SETTINGS_APP = "Web4xBrowser"


class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # Ensure the widget can accept drag events
        self.setMovable(True) # Enable moving of tabs

    def dragEnterEvent(self, event):
        event.accept()  # Accept the drag event to indicate we can handle it

    def dragMoveEvent(self, event):
        pos = event.position().toPoint()  # Get the position as a QPoint
        index = self.tabBar().tabAt(pos)
        if index != -1 and index != self.currentIndex():
            self.setCurrentIndex(index)  # Switch to the hovered tab
        event.accept()

    def dropEvent(self, event):
        event.accept()  # Accept the drop event

class AsyncTabTask(QRunnable):
    def __init__(self, function, *args):
        super().__init__()
        self.function = function
        self.args = args

    @pyqtSlot()
    def run(self):
        self.function(*self.args)

class CodeExecutor(QObject):
    codeResultReady = pyqtSignal(QVariant)

    def __init__(self, parent=None):
        super().__init__(parent)

    @pyqtSlot(QVariant)
    def executeSignal(self, incoming):
        print(f"Received from JavaScript: {incoming}")
        self.codeResultReady.emit(incoming)

class DevToolsWindow(QMainWindow):
    def __init__(self, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)

        self.dev_tools_view = QWebEngineView()
        self.setCentralWidget(self.dev_tools_view)

        self.setWindowTitle("Developer Tools")
        self.resize(800, 600)

        self.zoom_level = 1.0  # Default zoom level

        toolbar = QToolBar("DevTools Toolbar")
        self.addToolBar(toolbar)

        self.add_action(toolbar, "Close", self.close)
        self.add_action(toolbar, "Reload DevTools", self.dev_tools_view.reload)
        self.add_zoom_actions(toolbar)

        self.dev_tools_view.installEventFilter(
            self
        )  # Event filter for keyboard shortcuts

    def add_action(self, toolbar: QToolBar, label: str, callback: typing.Callable) -> None:
        action = QAction(label, self)
        action.triggered.connect(callback)
        toolbar.addAction(action)

    def add_zoom_actions(self, toolbar: QToolBar) -> None:
        zoom_in_action = QAction("Zoom In", self)
        zoom_in_action.setShortcut("Ctrl++")
        zoom_in_action.triggered.connect(self.zoom_in)
        toolbar.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out", self)
        zoom_out_action.setShortcut("Ctrl+-")
        zoom_out_action.triggered.connect(self.zoom_out)
        toolbar.addAction(zoom_out_action)

        self.zoom_label_action = QAction(f"Zoom: {self.zoom_level * 100:.0f}%", self)
        self.zoom_label_action.setEnabled(False)
        toolbar.addAction(self.zoom_label_action)

    def eventFilter(self, source: QObject, event: QEvent) -> bool:
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Plus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_in()
                return True
            elif event.key() == Qt.Key.Key_Minus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_out()
                return True
        return super().eventFilter(source, event)

    def zoom_in(self) -> None:
        self.zoom_level += 0.1
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.update_zoom_label()

    def zoom_out(self) -> None:
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.update_zoom_label()

    def update_zoom_label(self) -> None:
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")


class BrowserTab(QWidget):
    content_loaded = pyqtSignal(str)  # Signal for content load completion

    def __init__(self, url: str, parent: typing.Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)  # Remove default margins

        # Create a QWebEngineView and set up its own thread
        self.browser = QWebEngineView()
        #self.browser_thread = QThread()  # New thread for asynchronous loading
        #self.browser.moveToThread(self.browser_thread)
        #self.browser_thread.start()  # Start the thread

        self.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.NoContextMenu)
        self.browser.page().loadFinished.connect(self.on_load_finished)
        self.browser.page().loadFinished.connect(self.inject_scripts)

        self.layout.addWidget(self.browser)
        self.setLayout(self.layout)

        #self.load_async_content = partial(self.browser.setUrl, QUrl(url))
        #QTimer.singleShot(0, self.load_async_content)
        self.browser.setUrl(QUrl(url))

    @pyqtSlot(bool)
    def on_load_finished(self, ok: bool) -> None:
        if (ok):
            self.content_loaded.emit(self.browser.url().toString())
        else:
            print(f"Failed to load {self.browser.url().toString()}")

    def inject_scripts(self, ok: bool) -> None:
        if not ok:
            return

        # Load qwebchannel.js from file
        qwebchannel_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "qwebchannel.js")
        with open(qwebchannel_js_path, 'r') as file:
            qwebchannel_js = file.read()

        # Load browser functions JavaScript code from file
        browser_functions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "browser_functions.js")
        with open(browser_functions_path, 'r') as file:
            browser_functions_js = file.read()

        # Inject both scripts
        script = f"""
            // Inject QWebChannel.js
            {qwebchannel_js}
            
            // Inject browser functions
            {browser_functions_js}
        """
        self.browser.page().runJavaScript(script)


class Browser(QMainWindow):
    def __init__(self) -> None:
        super().__init__()

        # Load QWebChannel JavaScript code from file
        qwebchannel_js_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "qwebchannel.js")
        with open(qwebchannel_js_path, 'r') as file:
            self.qwebchannel_js = file.read()

        # Continue with the rest of initialization
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.setWindowTitle(BROWSER_TITLE)

        self.url_bar = QLineEdit()
        self.tabs = DraggableTabWidget()  # Use custom DraggableTabWidget to handle drag events
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.tab_context_menu)

        self.setCentralWidget(self.tabs)

        self.channel = QWebChannel()
        self.code_executor = CodeExecutor()
        self.file_system_handler = FileSystemHandler()
        self.channel.registerObject("codeExecutor", self.code_executor)
        self.channel.registerObject("fileSystemHandler", self.file_system_handler)
        self.file_system_handler.fileRead.connect(self.handle_file_read)

        self.dev_tools_window = DevToolsWindow(self)
        self.dev_tools_window.hide()

        self.history: typing.List[typing.Tuple[QDateTime, str]] = []
        self.recently_closed: typing.List[str] = []

        self.zoom_level = 1.0

        self.setup_navigation()

        self.load_saved_tabs()
        self.update_url_bar()

        if self.tabs.count() == 0:
            self.add_new_tab(QUrl(DEFAULT_URL), "Home")

        self.tabs.currentChanged.connect(self.update_url_bar)
        self.showMaximized()

        self.code_executor.codeResultReady.connect(self.open_new_tab)

    @pyqtSlot(QVariant)
    def open_new_tab(self, url: QVariant) -> None:
        """Opens a new tab with the given URL."""
        if isinstance(url, str):
            self.add_new_tab(QUrl(url), "New Tab")
        else:
            print(f"Invalid URL received: {url}")

    def setup_navigation(self) -> None:
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)

        self.back_action = self.create_action(
            QStyle.StandardPixmap.SP_ArrowBack, "Back", self.go_back
        )
        self.forward_action = self.create_action(
            QStyle.StandardPixmap.SP_ArrowForward, "Forward", self.go_forward
        )
        reload_action = self.create_action(
            QStyle.StandardPixmap.SP_BrowserReload, "Reload", self.reload_page
        )
        new_tab_action = self.create_action(
            QStyle.StandardPixmap.SP_FileDialogNewFolder, "New Tab", self.new_tab
        )

        nav_bar.addAction(self.back_action)
        nav_bar.addAction(self.forward_action)
        nav_bar.addAction(reload_action)
        nav_bar.addAction(new_tab_action)

        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

        # Add GitHub icon
        github_action = QAction(QIcon(os.path.join(os.path.dirname(os.path.abspath(__file__)), "github-mark.svg")), "GitHub", self)
        github_action.triggered.connect(lambda: self.open_github_page("https://github.com/HannesNortje/Web4xBrowser"))  # Replace with your repo URL
        nav_bar.addAction(github_action)

        three_dot_menu = QMenu("More", self)
        self.setup_history_menu(three_dot_menu)
        self.setup_zoom_menu(three_dot_menu)

        three_dot_button = QAction("⋮", self)
        three_dot_button.triggered.connect(lambda: three_dot_menu.exec(QCursor.pos()))
        nav_bar.addAction(three_dot_button)

        self.tabs.currentChanged.connect(self.update_navigation_actions)

    def open_github_page(self, url: str) -> None:
        """Opens the GitHub page in a new tab."""
        self.add_new_tab(QUrl(url), "GitHub");

    def create_action(self, icon: QStyle.StandardPixmap, tip: str, callback: typing.Callable) -> QAction:
        action = QAction(self.style().standardIcon(icon), tip, self)
        action.triggered.connect(callback)
        return action

    def setup_history_menu(self, parent_menu: QMenu) -> None:
        history_menu = parent_menu.addMenu("History")

        view_all_action = QAction("View All History", self)
        view_all_action.triggered.connect(self.open_all_history_tab)
        history_menu.addAction(view_all_action)

        recent_tabs_menu = history_menu.addMenu("Recently Closed")
        self.update_recent_tabs_menu(recent_tabs_menu)

        recent_history_menu = history_menu.addMenu("Recent History")
        self.update_recent_history_menu(recent_history_menu)

    def setup_zoom_menu(self, parent_menu: QMenu) -> None:
        zoom_menu = parent_menu.addMenu("Zoom")

        zoom_in_action = QAction("Zoom In (+)", self)
        zoom_in_action.triggered.connect(self.zoom_in)
        zoom_menu.addAction(zoom_in_action)

        zoom_out_action = QAction("Zoom Out (-)", self)
        zoom_out_action.triggered.connect(self.zoom_out)
        zoom_menu.addAction(zoom_out_action)

        self.zoom_label_action = QAction(f"Zoom: {self.zoom_level * 100:.0f}%", self)
        self.zoom_label_action.setEnabled(False)
        zoom_menu.addAction(self.zoom_label_action)

    def go_back(self) -> None:
        if self.current_browser():
            self.current_browser().back()

    def go_forward(self) -> None:
        if self.current_browser():
            self.current_browser().forward()

    def reload_page(self) -> None:
        if self.current_browser():
            self.current_browser().reload()

    def new_tab(self) -> None:
        self.add_new_tab(QUrl(DEFAULT_URL), "New Tab")

    def current_browser(self) -> typing.Optional[QWebEngineView]:
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, BrowserTab):
            return current_widget.browser
        return None

    def update_navigation_actions(self) -> None:
        browser = self.current_browser()
        if browser:
            self.back_action.setEnabled(browser.history().canGoBack())
            self.forward_action.setEnabled(browser.history().canGoForward())
        else:
            self.back_action.setEnabled(False)
            self.forward_action.setEnabled(False)

    def navigate_to_url(self) -> None:
        url_text = self.url_bar.text()
        url = QUrl(url_text)
        if url.scheme() == "":
            url.setScheme("http")
        if self.current_browser():
            self.current_browser().setUrl(url)

    def update_url_bar(self) -> None:
        current_browser = self.current_browser()
        if current_browser:
            self.url_bar.setText(current_browser.url().toString())
        else:
            self.url_bar.clear()

    def add_new_tab(self, url: QUrl, title: str = "New Tab") -> None:
        new_tab = BrowserTab(url.toString(), self)

        # Connect signals
        page = new_tab.browser.page()
        # Set the web channel before anything else
        page.setWebChannel(self.channel)

        # Connect other signals
        new_tab.browser.titleChanged.connect(lambda title, tab=new_tab: self.update_tab_title(tab, title))
        new_tab.browser.urlChanged.connect(self.update_url_bar)
        new_tab.content_loaded.connect(self.record_history)
        new_tab.browser.urlChanged.connect(self.update_navigation_actions)

        # Setup context menu
        new_tab.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        new_tab.browser.customContextMenuRequested.connect(self.open_context_menu)

        # Add tab
        index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)

        # Inject JavaScript after the content is loaded
        page.loadFinished.connect(lambda ok, tab=new_tab: self.inject_javascript(tab) if ok else None)

    def close_tab(self, index: int) -> None:
        closed_tab = self.tabs.widget(index)
        if isinstance(closed_tab, BrowserTab):
            self.recently_closed.append(closed_tab.browser.url().toString())
        self.tabs.removeTab(index)
        closed_tab.deleteLater()  # Clean up the tab

    def update_tab_title(self, tab: BrowserTab, title: str) -> None:
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def open_context_menu(self, position: typing.Any) -> None:
        menu = QMenu()

        self.add_context_action(menu, "Copy", "document.execCommand('copy');")
        self.add_context_action(menu, "Cut", "document.execCommand('cut');")
        self.add_context_action(menu, "Paste", "document.execCommand('paste');")

        self.add_action_to_menu(menu, "Save As...", self.save_as)
        self.add_action_to_menu(menu, "Print...", self.print_page)
        self.add_action_to_menu(menu, "Open Link in New Tab", self.open_link_in_new_tab)
        self.add_action_to_menu(menu, "Inspect Element", self.open_dev_tools)

        menu.exec(QCursor.pos())

    def add_context_action(self, menu: QMenu, label: str, js_command: str) -> None:
        action = QAction(label, self)
        action.triggered.connect(lambda: self.execute_javascript(js_command))
        menu.addAction(action)

    def add_action_to_menu(self, menu: QMenu, label: str, callback: typing.Callable) -> None:
        action = QAction(label, self)
        action.triggered.connect(callback)
        menu.addAction(action)

    def open_link_in_new_tab(self) -> None:
        script = """
            var element = document.activeElement;
            if (element && element.href) {
                element.href;
            } else {
                null;
            }
        """
        self.current_browser().page().runJavaScript(script, self.open_new_tab)

    def execute_javascript(self, script: str) -> None:
        browser = self.current_browser()
        if browser:
            browser.page().runJavaScript(script)

    def save_as(self) -> None:
        page = self.current_browser().page()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Page As", "", "Webpage (*.html);;All Files (*)"
        )
        if file_name:
            page.toHtml(lambda html: self.save_file(html, file_name))

    def save_file(self, html: str, file_name: str) -> None:
        with open(file_name, "w", encoding="utf-8") as file:
            file.write(html)
        print(f"Page saved as {file_name}")

    def print_page(self) -> None:
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_page = self.current_browser().page()
            current_page.toHtml(lambda html: self.handle_print(html, printer))

    def handle_print(self, html: str, printer: QPrinter) -> None:
        document = QTextDocument()
        document.setHtml(html)
        document.print(printer)
        print("Printing job completed.")

    def tab_context_menu(self, position: typing.Any) -> None:
        tab_index = self.tabs.tabBar().tabAt(position)
        if tab_index == -1:
            return

        menu = QMenu()

        clone_action = QAction("Clone Tab", self)
        clone_action.triggered.connect(lambda: self.clone_tab(tab_index))
        menu.addAction(clone_action)

        menu.exec(QCursor.pos())

    def clone_tab(self, index: int) -> None:
        original_tab = self.tabs.widget(index)
        if isinstance(original_tab, BrowserTab):
            url = original_tab.browser.url()
            title = self.tabs.tabText(index)
            self.add_new_tab(url, title)

    def open_dev_tools(self) -> None:
        if not self.dev_tools_window.isVisible():
            self.dev_tools_window.show()
            self.current_browser().page().setDevToolsPage(self.dev_tools_window.dev_tools_view.page())

    def record_history(self, url: str) -> None:
        timestamp = QDateTime.currentDateTime()
        self.history.append((timestamp, url))
        if len(self.history) > MAX_HISTORY_LENGTH:
            self.history.pop(0)

    def open_all_history_tab(self) -> None:
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

    def update_recent_tabs_menu(self, recent_tabs_menu: QMenu) -> None:
        recent_tabs_menu.clear()
        for url in self.recently_closed[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "Reopened Tab"))
            recent_tabs_menu.addAction(action)

    def update_recent_history_menu(self, recent_history_menu: QMenu) -> None:
        recent_history_menu.clear()
        for _, url in self.history[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "History Tab"))
            recent_history_menu.addAction(action)

    def zoom_in(self) -> None:
        self.zoom_level += 0.1
        if self.current_browser():
            self.current_browser().setZoomFactor(self.zoom_level)
        self.update_zoom_label()

    def zoom_out(self) -> None:
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        if self.current_browser():
            self.current_browser().setZoomFactor(self.zoom_level)
        self.update_zoom_label()

    def update_zoom_label(self) -> None:
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def inject_javascript(self, tab: BrowserTab) -> None:
        # Load browser functions JavaScript code from file
        browser_functions_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "js", "browser_functions.js")
        with open(browser_functions_path, 'r') as file:
            browser_functions_js = file.read()

        # Inject both scripts
        script = f"""
            // Inject QWebChannel.js
            {self.qwebchannel_js}
            
            // Inject browser functions
            {browser_functions_js}
        """
        
        def check_initialization(result):
            print("JavaScript injection result:", result)
            
        tab.browser.page().runJavaScript(script, check_initialization)

    @pyqtSlot(str, str)
    def handle_file_read(self, filePath: str, content: str) -> None:
        print(f"File {filePath} read successfully. Content: {content}")
        # You can add logic here to pass the content back to the web page, e.g., using runJavaScript
        script = f"""
            (function(filePath, content) {{
                if (window.readFileCallback) {{
                    window.readFileCallback(content);
                    window.readFileCallback = null; // Clear the callback after execution
                }}
            }})('{filePath}', '{content}');
        """
        self.current_browser().page().runJavaScript(script)

    def load_saved_tabs(self) -> None:
        saved_urls = self.settings.value("openTabs", [])
        if isinstance(saved_urls, list):
            for url in saved_urls:
                if isinstance(url, str):
                    self.add_new_tab(QUrl(url), "Restored Tab")

    def closeEvent(self, event: QEvent) -> None:
        open_tabs = []
        for i in range(self.tabs.count()):
            widget = self.tabs.widget(i)
            if isinstance(widget, BrowserTab):
                open_tabs.append(widget.browser.url().toString())
        self.settings.setValue("openTabs", open_tabs)
        event.accept()


def main() -> None:
    """Main function to run the Web4x Browser."""
    app = QApplication(sys.argv)
    QApplication.setApplicationName(BROWSER_TITLE)
    window = Browser()
    window.show()
    sys.exit(app.exec())


# Ensures the application only runs when executed directly or as a script entry point
if __name__ == "__main__":
    main()