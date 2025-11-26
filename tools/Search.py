import os
import re
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                               QLineEdit, QPushButton, QLabel, QFileDialog, 
                               QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QHBoxLayout)
from PySide6.QtCore import Qt, QSettings

def to_pascal_case(s):
    # If the string is all caps, return it as is
    if s.isupper():
        return s
    # Otherwise, convert it to PascalCase
    return ''.join(word.capitalize() for word in s.split())

def search_component_in_files(directory, component_name, version_number=None):
    # Prepare the regex pattern
    component_file_pattern = re.compile(rf"/EAMD\.ucp.*/{component_name}\.component\.xml", re.IGNORECASE)
    found_files = []

    # Walk through the directory to find .js and .html files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.js', '.html')):
                file_path = os.path.join(root, file)
                try:
                    # Try opening the file with utf-8 encoding
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        matches = component_file_pattern.findall(content)
                        if matches:
                            for match in matches:
                                # If a version number is provided, check if it's in the match string
                                if version_number:
                                    if version_number in match:
                                        relative_path = os.path.relpath(file_path, start=directory)
                                        found_files.append((file, relative_path, match))
                                else:
                                    # No version filter, include all matches
                                    relative_path = os.path.relpath(file_path, start=directory)
                                    found_files.append((file, relative_path, match))
                except UnicodeDecodeError:
                    print(f"Skipping file due to encoding issues: {file_path}")
                    continue

    return found_files

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up settings to save/load the last directory
        self.settings = QSettings("MyApp", "ComponentSearch")

        # Main layout
        self.setWindowTitle("Component Search")
        layout = QVBoxLayout()

        # Input for component name
        input_layout = QHBoxLayout()
        self.component_label = QLabel("Component Name:")
        self.component_input = QLineEdit()
        input_layout.addWidget(self.component_label)
        input_layout.addWidget(self.component_input)
        layout.addLayout(input_layout)

        # Input for version number
        version_layout = QHBoxLayout()
        self.version_label = QLabel("Version (optional):")
        self.version_input = QLineEdit()
        version_layout.addWidget(self.version_label)
        version_layout.addWidget(self.version_input)
        layout.addLayout(version_layout)

        # Button to select directory
        self.directory_button = QPushButton("Select Directory")
        self.directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.directory_button)

        # Label to display selected directory
        self.directory_label = QLabel("")
        layout.addWidget(self.directory_label)

        # Button to start search
        self.search_button = QPushButton("Start Search")
        self.search_button.clicked.connect(self.start_search)
        layout.addWidget(self.search_button)

        # Table to display results
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(3)
        self.result_table.setHorizontalHeaderLabels(["File Name", "Relative Path", "Match (Full String)"])
        
        # Set File Name column to a fixed width of 150px
        self.result_table.setColumnWidth(0, 150)
        
        # Set Relative Path and Match columns to stretch equally
        self.result_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.result_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.result_table.setSortingEnabled(True)  # Enable sorting by clicking headers
        layout.addWidget(self.result_table)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        # Set layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        # Placeholder for directory
        self.directory = ""

        # Load the last used directory if available
        self.load_last_directory()

        # Maximize the window to fill the screen
        self.showMaximized()

    def load_last_directory(self):
        # Load the last directory from settings, if it exists
        last_directory = self.settings.value("lastDirectory", "")
        if last_directory:
            self.directory = last_directory
            self.directory_label.setText(f"Selected Directory: {self.directory}")
    
    def save_last_directory(self):
        # Save the currently selected directory to settings
        self.settings.setValue("lastDirectory", self.directory)

    def select_directory(self):
        # Select directory
        self.directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.directory or os.path.expanduser("~"))
        if not self.directory:
            QMessageBox.warning(self, "Error", "Directory selection is required.")
        else:
            # Display selected directory
            self.directory_label.setText(f"Selected Directory: {self.directory}")
            # Save the selected directory for next session
            self.save_last_directory()
    
    def start_search(self):
        # Get component name from input
        component_name = self.component_input.text().strip()
        if not component_name:
            QMessageBox.warning(self, "Error", "Component name is required.")
            return

        # Get version number from input (optional)
        version_number = self.version_input.text().strip() if self.version_input.text().strip() else None

        # Convert component name to PascalCase, unless it's in all caps
        pascal_case_component = to_pascal_case(component_name)

        if not self.directory:
            QMessageBox.warning(self, "Error", "Directory selection is required.")
            return

        # Clear previous results
        self.result_table.setRowCount(0)

        # Search for the component in .js and .html files, with optional version filtering
        results = search_component_in_files(self.directory, pascal_case_component, version_number)

        # Populate table with results
        if results:
            for i, (file_name, file_path, match) in enumerate(results):
                self.result_table.insertRow(i)
                self.result_table.setItem(i, 0, QTableWidgetItem(file_name))   # File Name
                self.result_table.setItem(i, 1, QTableWidgetItem(file_path))   # Relative Path
                self.result_table.setItem(i, 2, QTableWidgetItem(match))       # Match (Full String)
        else:
            QMessageBox.information(self, "Search Results", "No matches found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # Show the window
    sys.exit(app.exec())
