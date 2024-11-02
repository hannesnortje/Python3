import os
import re
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                               QPushButton, QLabel, QFileDialog, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QSettings

# Function to remove comments from JavaScript content
def remove_js_comments(content):
    # Pattern to match both single-line and multi-line comments
    comment_pattern = re.compile(r"(//.*?$)|(/\*.*?\*/)", re.DOTALL | re.MULTILINE)
    return re.sub(comment_pattern, "", content)

# Function to search for dependencies in each .js file
def search_dependencies_in_files(directory):
    dependencies_info = {}  # Use a dict to store dependencies with their respective file names
    dependency_pattern = re.compile(r'static\s+get\s+dependencies\s*\(\)\s*{\s*return\s*\[([^\]]*)\]', re.IGNORECASE | re.DOTALL)

    # Walk through the directory to find .js files
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith('.js'):
                file_path = os.path.join(root, file)
                try:
                    # Try opening the file with utf-8 encoding
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        # Remove comments from the content
                        cleaned_content = remove_js_comments(content)
                        # Search for the static get dependencies() method
                        match = dependency_pattern.search(cleaned_content)
                        if match:
                            # Extract the dependencies list (inside the brackets)
                            dependencies_str = match.group(1)
                            # Split by commas, clean up the strings
                            dependencies = [dep.strip().strip('\'"') for dep in dependencies_str.split(',') if dep.strip()]
                            for dep in dependencies:
                                # Extract version number and component name
                                dep_parts = dep.split('/')
                                if len(dep_parts) >= 2:
                                    version = dep_parts[-2]  # Second last directory (version number)
                                    component_name = dep_parts[-1].replace('.component.xml', '')  # Last part without .component.xml
                                    # Extract the file name (not the full path)
                                    file_name = os.path.basename(file_path)
                                    # If dependency exists, add file name to list of files, otherwise create new entry
                                    if (dep, version, component_name) in dependencies_info:
                                        dependencies_info[(dep, version, component_name)].add(file_name)
                                    else:
                                        dependencies_info[(dep, version, component_name)] = {file_name}
                except UnicodeDecodeError:
                    print(f"Skipping file due to encoding issues: {file_path}")
                    continue

    return dependencies_info

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        # Set up settings to save/load the last directory
        self.settings = QSettings("MyApp", "DependencySearch")

        # Main layout
        self.setWindowTitle("Dependency Search")
        layout = QVBoxLayout()

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
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Dependency", "Version", "Component Name", "Files Found In"])
        
        # Set fixed width for Version and Component Name columns
        self.result_table.setColumnWidth(1, 80)  # Version column fixed to 80px
        self.result_table.setColumnWidth(2, 150)  # Component Name column fixed to 150px

        # Set Dependency and Files columns to stretch
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)  # Dependency column stretches
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)  # Files Found In column stretches
        
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
        if not self.directory:
            QMessageBox.warning(self, "Error", "Directory selection is required.")
            return

        # Clear previous results
        self.result_table.setRowCount(0)

        # Search for dependencies in .js files and extract version, component name, and file names found in
        dependencies_info = search_dependencies_in_files(self.directory)

        # Populate table with unique dependencies, version, component name, and file names found in
        if dependencies_info:
            for i, ((dependency, version, component_name), file_names) in enumerate(sorted(dependencies_info.items(), key=lambda x: x[0][0])):  # Sort dependencies alphabetically
                self.result_table.insertRow(i)
                self.result_table.setItem(i, 0, QTableWidgetItem(dependency))        # Dependency
                self.result_table.setItem(i, 1, QTableWidgetItem(version))           # Version
                self.result_table.setItem(i, 2, QTableWidgetItem(component_name))    # Component Name
                self.result_table.setItem(i, 3, QTableWidgetItem(', '.join(sorted(file_names))))  # Files Found In (only file names)
        else:
            QMessageBox.information(self, "Search Results", "No dependencies found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()  # Show the window
    sys.exit(app.exec())
