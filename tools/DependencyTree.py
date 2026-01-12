from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QPushButton, QLineEdit, QTreeWidget, QTreeWidgetItem, QWidget
from selenium import webdriver
from selenium.webdriver.chrome.service import Service  # Corrected import
import json
import sys
import time
from urllib.parse import urlparse

class DependencyLoggerApp(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up the main window
        self.setWindowTitle("Dependency Logger with Tree View")
        self.setGeometry(300, 200, 800, 600)

        # Create a central widget
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        # Create a vertical layout
        layout = QVBoxLayout(central_widget)

        # URL Input Textbox
        self.url_input = QLineEdit(self)
        self.url_input.setPlaceholderText("Enter website URL here...")
        layout.addWidget(self.url_input)

        # Button to trigger the dependency retrieval
        self.retrieve_button = QPushButton("Retrieve Dependencies", self)
        layout.addWidget(self.retrieve_button)

        # Tree widget to display the dependency tree
        self.dependency_tree = QTreeWidget(self)
        self.dependency_tree.setHeaderLabels(["Dependencies"])
        layout.addWidget(self.dependency_tree)

        # Close Button
        self.close_button = QPushButton("Close", self)
        layout.addWidget(self.close_button)

        # Connect the buttons to their actions
        self.retrieve_button.clicked.connect(self.retrieve_dependencies)
        self.close_button.clicked.connect(self.close)

    def retrieve_dependencies(self):
        url = self.url_input.text()

        if not url:
            self.dependency_tree.clear()
            root_item = QTreeWidgetItem(["Please enter a valid URL."])
            self.dependency_tree.addTopLevelItem(root_item)
            return

        # Configure Chrome options
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        chrome_options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        # Initialize the Chrome WebDriver (Selenium will auto-manage the driver)
        driver = webdriver.Chrome(options=chrome_options)
        driver.get(url)

        # Wait for 5 seconds to allow the site to load fully
        time.sleep(15)

        # Extract performance logs after waiting
        logs = driver.get_log("performance")
        driver.quit()

        # Process logs and extract URLs
        urls = []
        for log in logs:
            log_entry = json.loads(log["message"])  # Parse the log entry
            message = log_entry.get("message", {})
            method = message.get("method", "")

            # Check for network request/response events
            if method.startswith("Network."):
                request = message.get("params", {}).get("request", {})
                url = request.get("url")

                # Only add URLs that are found in the logs
                if url and url not in urls:  # Avoid duplicate URLs
                    urls.append(url)

        # Build and display the dependency tree
        self.build_dependency_tree(urls)

    def build_dependency_tree(self, urls):
        self.dependency_tree.clear()  # Clear any existing tree

        # Dictionary to store the tree structure
        tree = {}

        # Build tree structure from the URLs
        for url in urls:
            parsed_url = urlparse(url)
            parts = [parsed_url.scheme + "://", parsed_url.netloc] + parsed_url.path.strip("/").split("/")

            current_level = tree
            for part in parts:
                if part not in current_level:
                    current_level[part] = {"_full_url": url}
                current_level = current_level[part]

        # Function to format text with dots and spacing
        def format_item_text(name, full_url):
            dots = '.' * 30  # Create a series of dots to represent spacing
            # Adjust the number of dots based on the length of the name to fit a consistent width
            padding = 30 - len(name) if len(name) < 30 else 0
            return f"{name}{dots[:padding]}... {full_url}"

        # Function to recursively add items to the tree widget
        def add_items(parent, subtree):
            for key, value in subtree.items():
                if key == "_full_url":
                    continue  # Skip the special key for the full URL

                # Create a tree item with both the part and the full URL concatenated
                full_url = value.get("_full_url", "")
                item_text = format_item_text(key, full_url)  # Format with dots and spacing
                item = QTreeWidgetItem([item_text])
                parent.addChild(item)

                # Recurse if the node has children
                if isinstance(value, dict):
                    add_items(item, value)

        # Create the top-level tree item and populate the tree
        root_item = QTreeWidgetItem(["Dependencies"])
        self.dependency_tree.addTopLevelItem(root_item)
        add_items(root_item, tree)
        self.dependency_tree.expandAll()  # Expand all items in the tree for better visibility

# Initialize the application
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DependencyLoggerApp()
    window.show()
    sys.exit(app.exec())
