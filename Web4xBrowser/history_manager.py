# history_manager.py

from PyQt6.QtCore import QDateTime, QUrl
from PyQt6.QtGui import QAction  # Corrected import for QAction
from PyQt6.QtWidgets import QScrollArea, QWidget, QVBoxLayout, QLabel, QMenu
from collections import defaultdict


class HistoryManager:
    def __init__(self, browser):
        self.browser = browser
        self.history = []
        self.recently_closed = []

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
                entry_label.linkActivated.connect(lambda link=url: self.browser.tab_manager.add_new_tab(QUrl(link), "History"))
                content_layout.addWidget(entry_label)

        content_widget.setLayout(content_layout)
        scroll_area.setWidget(content_widget)
        layout.addWidget(scroll_area)
        history_tab.setLayout(layout)

        index = self.browser.tabs.addTab(history_tab, "History")
        self.browser.tabs.setCurrentIndex(index)
