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
from PyQt6.QtCore import QUrl, Qt, QThread, pyqtSlot, pyqtSignal, QObject, QVariant, QDateTime, QSettings, QEvent, QRunnable, QThreadPool, QStandardPaths
from PyQt6.QtGui import QAction, QCursor, QTextDocument
from PyQt6.QtWidgets import QApplication, QMainWindow, QToolBar, QLineEdit, QMenu, QTabWidget, QWidget, QVBoxLayout, QFileDialog, QDialog, QLabel, QScrollArea, QStyle
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage
from PyQt6.QtWebEngineWidgets import QWebEngineView
from PyQt6.QtWebChannel import QWebChannel
from PyQt6.QtPrintSupport import QPrinter, QPrintDialog
from collections import defaultdict

class DraggableTabWidget(QTabWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)  # Ensure the widget can accept drag events

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
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.dev_tools_view = QWebEngineView()
        self.setCentralWidget(self.dev_tools_view)
        
        self.setWindowTitle("Developer Tools")
        self.resize(800, 600)
        
        self.zoom_level = 1.0  # Default zoom level

        toolbar = QToolBar("DevTools Toolbar")
        self.addToolBar(toolbar)
        
        close_action = QAction("Close", self)
        close_action.triggered.connect(self.close)
        toolbar.addAction(close_action)
        
        reload_action = QAction("Reload DevTools", self)
        reload_action.triggered.connect(self.dev_tools_view.reload)
        toolbar.addAction(reload_action)
        
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

        self.dev_tools_view.installEventFilter(self)  # Event filter for keyboard shortcuts

    def eventFilter(self, source, event):
        if event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Plus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_in()
                return True
            elif event.key() == Qt.Key.Key_Minus and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
                self.zoom_out()
                return True
        return super().eventFilter(source, event)

    def zoom_in(self):
        self.zoom_level += 0.1
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def zoom_out(self):
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.dev_tools_view.setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

class BrowserTab(QWidget):
    content_loaded = pyqtSignal(str)  # Signal for content load completion

    def __init__(self, url, profile, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout(self)

        # Create a QWebEngineView and set up its own thread
        self.browser = QWebEngineView()

        # Set up its profile
        self.browser.setPage(QWebEnginePage(profile))

        self.browser_thread = QThread()  # New thread for asynchronous loading
        self.browser.moveToThread(self.browser_thread)
        self.browser_thread.start()  # Start the thread

        # Load the initial URL asynchronously
        if url:
            self.load_async_content(url)

        self.layout.addWidget(self.browser)
        self.setLayout(self.layout)


    def load_async_content(self, url):
        # Function to load URL in a separate thread
        @pyqtSlot()
        def load_url():
            self.browser.setUrl(QUrl(url))

        self.browser_thread.started.connect(load_url)
        self.browser_thread.start()

class Browser(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.settings = QSettings("CeruleanCircle", "Web4xBrowser")

        self.url_bar = QLineEdit()
        self.tabs = DraggableTabWidget()  # Use custom DraggableTabWidget to handle drag events
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tabs.customContextMenuRequested.connect(self.tab_context_menu)
        
        self.setCentralWidget(self.tabs)
        
        self.code_executor = CodeExecutor()
        self.channel = QWebChannel()
        self.channel.registerObject("codeExecutor", self.code_executor)
        
        self.dev_tools_window = DevToolsWindow(self)
        self.dev_tools_window.hide()

        self.history = []
        self.recently_closed = []
        
        self.zoom_level = 1.0

        self.setup_navigation()
        
        self.load_saved_tabs()
        self.update_url_bar()

         # Set up a persistent profile
        storage_path = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.AppDataLocation)
        profile = QWebEngineProfile.defaultProfile()
        profile.setPersistentStoragePath(storage_path)
        profile.setPersistentCookiesPolicy(QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies)

        # Pass this profile when creating new tabs
        self.tabs = DraggableTabWidget()
        self.setCentralWidget(self.tabs)

        if self.tabs.count() == 0:
            self.add_new_tab(QUrl("https://test.wo-da.de/ide"), "Home")
        
        self.tabs.currentChanged.connect(self.update_url_bar)
        self.showMaximized()

        self.code_executor.codeResultReady.connect(self.open_new_tab)


    @pyqtSlot(QVariant)
    def open_new_tab(self, url):
        """Opens a new tab with the given URL."""
        self.add_new_tab(QUrl(url), "New Tab")

    def setup_navigation(self):
        nav_bar = QToolBar()
        self.addToolBar(nav_bar)
        
        self.back_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowBack), "Back", self)
        self.back_action.triggered.connect(lambda: self.current_browser().back())
        nav_bar.addAction(self.back_action)
        
        self.forward_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_ArrowForward), "Forward", self)
        self.forward_action.triggered.connect(lambda: self.current_browser().forward())
        nav_bar.addAction(self.forward_action)
        
        reload_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload), "Reload", self)
        reload_action.triggered.connect(lambda: self.current_browser().reload())
        nav_bar.addAction(reload_action)
        
        new_tab_action = QAction(self.style().standardIcon(QStyle.StandardPixmap.SP_FileDialogNewFolder), "New Tab", self)
        new_tab_action.triggered.connect(lambda: self.add_new_tab(QUrl("https://test.wo-da.de/ide"), "New Tab"))
        nav_bar.addAction(new_tab_action)
        
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        nav_bar.addWidget(self.url_bar)

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
        
        self.tabs.currentChanged.connect(self.update_navigation_actions)

    def current_browser(self):
        current_widget = self.tabs.currentWidget()
        if isinstance(current_widget, BrowserTab):
            return current_widget.browser
        return None

    def update_navigation_actions(self):
        browser = self.current_browser()
        if browser:
            self.back_action.setEnabled(browser.history().canGoBack())
            self.forward_action.setEnabled(browser.history().canGoForward())
            browser.urlChanged.connect(lambda: self.update_navigation_actions())
        else:
            self.back_action.setEnabled(False)
            self.forward_action.setEnabled(False)

    def navigate_to_url(self):
        url_text = self.url_bar.text()
        url = QUrl(url_text)
        if url.scheme() == "":
            url.setScheme("http")
        self.current_browser().setUrl(url)

    def update_url_bar(self):
        current_browser = self.current_browser()
        if current_browser:
            self.url_bar.setText(current_browser.url().toString())
        else:
            self.url_bar.clear()

    def add_new_tab(self, url=None, title="New Tab", profile=None):
        new_tab = BrowserTab(url, profile, self)
        
        new_tab.browser.page().setWebChannel(self.channel)
        new_tab.browser.titleChanged.connect(lambda title, tab=new_tab: self.update_tab_title(tab, title))
        new_tab.browser.urlChanged.connect(self.update_url_bar)
        new_tab.browser.urlChanged.connect(lambda url: self.record_history(url))
        
        index = self.tabs.addTab(new_tab, title)
        self.tabs.setCurrentIndex(index)
        
        new_tab.browser.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        new_tab.browser.customContextMenuRequested.connect(self.open_context_menu)

    def close_tab(self, index):
        closed_tab = self.tabs.widget(index)
        if isinstance(closed_tab, BrowserTab):
            self.recently_closed.append(closed_tab.browser.url().toString())
        self.tabs.removeTab(index)

    def update_tab_title(self, tab, title):
        index = self.tabs.indexOf(tab)
        if index != -1:
            self.tabs.setTabText(index, title)

    def open_context_menu(self, position):
        menu = QMenu()

        # Existing context menu options
        copy_action = QAction("Copy", self)
        copy_action.triggered.connect(lambda: self.execute_javascript("document.execCommand('copy');"))
        menu.addAction(copy_action)

        cut_action = QAction("Cut", self)
        cut_action.triggered.connect(lambda: self.execute_javascript("document.execCommand('cut');"))
        menu.addAction(cut_action)

        paste_action = QAction("Paste", self)
        paste_action.triggered.connect(lambda: self.execute_javascript("document.execCommand('paste');"))
        menu.addAction(paste_action)

        save_action = QAction("Save As...", self)
        save_action.triggered.connect(self.save_as)
        menu.addAction(save_action)

        print_action = QAction("Print...", self)
        print_action.triggered.connect(self.print_page)
        menu.addAction(print_action)

        # New "Open in New Tab" action
        open_in_new_tab_action = QAction("Open Link in New Tab", self)
        open_in_new_tab_action.triggered.connect(lambda: self.open_link_in_new_tab())
        menu.addAction(open_in_new_tab_action)

        inspect_action = QAction("Inspect Element", self)
        inspect_action.triggered.connect(self.open_dev_tools)
        menu.addAction(inspect_action)

        menu.exec(QCursor.pos())

    def open_link_in_new_tab(self):
        # This JavaScript will capture the link under the context menu
        script = """
            var element = document.activeElement;
            if (element && element.href) {
                element.href;
            } else {
                null;
            }
        """
        self.current_browser().page().runJavaScript(script, self.open_new_tab)

    def execute_javascript(self, script):
        browser = self.current_browser()
        if browser:
            browser.page().runJavaScript(script)

    def save_as(self):
        page = self.current_browser().page()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Page As", "", "Webpage (*.html);;All Files (*)")
        if file_name:
            page.toHtml(lambda html: self.save_file(html, file_name))

    def save_file(self, html, file_name):
        with open(file_name, 'w', encoding='utf-8') as file:
            file.write(html)
        print(f"Page saved as {file_name}")

    def print_page(self):
        printer = QPrinter()
        dialog = QPrintDialog(printer, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            current_page = self.current_browser().page()
            current_page.toHtml(lambda html: self.handle_print(html, printer))

    def handle_print(self, html, printer):
        document = QTextDocument()
        document.setHtml(html)
        document.print(printer)
        print("Printing job completed.")

    def tab_context_menu(self, position):
        tab_index = self.tabs.tabBar().tabAt(position)
        if tab_index == -1:
            return
        
        menu = QMenu()
        
        clone_action = QAction("Clone Tab", self)
        clone_action.triggered.connect(lambda: self.clone_tab(tab_index))
        menu.addAction(clone_action)
        
        menu.exec(QCursor.pos())

    def clone_tab(self, index):
        original_tab = self.tabs.widget(index)
        url = original_tab.browser.url()
        title = self.tabs.tabText(index)
        self.add_new_tab(url, title)

    def open_dev_tools(self):
        if not self.dev_tools_window.isVisible():
            self.dev_tools_window.show()
            self.current_browser().page().setDevToolsPage(self.dev_tools_window.dev_tools_view.page())

    def record_history(self, url):
        timestamp = QDateTime.currentDateTime()
        self.history.append((timestamp, url.toString()))
        if len(self.history) > 100:
            self.history.pop(0)

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
                entry_label.linkActivated.connect(lambda link=url: self.add_new_tab(QUrl(link), "History"))
                content_layout.addWidget(entry_label)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        history_tab.setLayout(layout)

        index = self.tabs.addTab(history_tab, "History")
        self.tabs.setCurrentIndex(index)

    def update_recent_tabs_menu(self, recent_tabs_menu):
        recent_tabs_menu.clear()
        for url in self.recently_closed[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "Reopened Tab"))
            recent_tabs_menu.addAction(action)

    def update_recent_history_menu(self, recent_history_menu):
        recent_history_menu.clear()
        for _, url in self.history[-5:]:
            action = QAction(url, self)
            action.triggered.connect(lambda checked, url=url: self.add_new_tab(QUrl(url), "History Tab"))
            recent_history_menu.addAction(action)

    def zoom_in(self):
        self.zoom_level += 0.1
        self.current_browser().setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def zoom_out(self):
        self.zoom_level = max(0.1, self.zoom_level - 0.1)
        self.current_browser().setZoomFactor(self.zoom_level)
        self.zoom_label_action.setText(f"Zoom: {self.zoom_level * 100:.0f}%")

    def inject_javascript(self):
        script = """
            debugger;
            document.addEventListener("DOMContentLoaded", function() {
                // Existing drag-and-drop functionality
                document.body.addEventListener("dragover", function(e) {
                    e.preventDefault();
                });

                document.body.addEventListener("drop", function(e) {
                    e.preventDefault();
                    const files = e.dataTransfer.files;
                    const textData = e.dataTransfer.getData("text/plain");

                    if (files.length > 0) {
                        console.log("File(s) dropped:", files);
                        if (typeof add === "function") {
                            add(files[0]);
                        }
                    } else if (textData) {
                        console.log("Text dropped:", textData);
                        if (typeof this.add === "function") {
                            debugger;
                            this.add(textData);
                        }
                    } else {
                        console.log("No recognizable data in drop.");
                    }
                });

                // New link-click handling to open in a new tab only for target="_blank" links
                document.body.addEventListener("click", function(e) {
                    const link = e.target.closest("a[target='_blank']");
                    if (link) {
                        e.preventDefault();
                        e.stopPropagation();
                        window.codeExecutor.executeSignal(link.href);  // Send the link URL to PyQt
                    }
                });
            });
        """
        self.current_browser().page().runJavaScript(script)

    def load_saved_tabs(self):
        saved_urls = self.settings.value("openTabs", [])
        for url in saved_urls:
            self.add_new_tab(QUrl(url), "Restored Tab")

    def closeEvent(self, event):
        open_tabs = [self.tabs.widget(i).browser.url().toString() for i in range(self.tabs.count())]
        self.settings.setValue("openTabs", open_tabs)
        event.accept()

def main():
    """Main function to run the Web4x Browser."""
    app = QApplication(sys.argv)
    QApplication.setApplicationName("Web4x Browser")
    window = Browser()
    window.inject_javascript()  # Initialize any JavaScript injection
    window.show()
    sys.exit(app.exec())

# Ensures the application only runs when executed directly or as a script entry point
if __name__ == "__main__":
    main()
