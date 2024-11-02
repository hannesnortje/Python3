import os
import re
import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QVBoxLayout, QWidget, 
                               QPushButton, QLabel, QFileDialog, QTableWidget, 
                               QTableWidgetItem, QHeaderView, QMessageBox, QLineEdit)
from PySide6.QtCore import Qt, QSettings

# Function to remove comments from JavaScript content
def remove_js_comments(content):
    comment_pattern = re.compile(r"(//.*?$)|(/\*.*?\*/)", re.DOTALL | re.MULTILINE)
    return re.sub(comment_pattern, "", content)

def is_pascal_case(text):
    """Check if the input is already in PascalCase or fully uppercase."""
    return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', text)) or text.isupper()

def to_pascal_case(text):
    """Convert a string to PascalCase, preserving all-uppercase words."""
    words = text.split()
    pascal_case_words = []
    for word in words:
        if word.isupper():
            pascal_case_words.append(word)
        else:
            pascal_case_words.append(word.capitalize())  # Convert to PascalCase
    return ''.join(pascal_case_words)

def normalize_component_name(input_name):
    """Normalize the component name: return as is if fully uppercase or PascalCase."""
    if is_pascal_case(input_name):
        return input_name
    else:
        return to_pascal_case(input_name)

# Function to search for dependencies in each .js file
def search_dependencies_in_files(directory):
    dependencies_info = {}  
    
    # Regex for JavaScript dependencies
    dependency_pattern_js = re.compile(r'static\s+get\s+dependencies\s*\(\)\s*{\s*return\s*\[([^\]]*)\]', re.IGNORECASE | re.DOTALL)
    
    # Regex for HTML dependencies: <link href="...component.xml" .../>
    dependency_pattern_html = re.compile(r'<link\s+[^>]*href\s*=\s*["\']([^"\']+.component.xml)["\']', re.IGNORECASE)

    for root, dirs, files in os.walk(directory):
        for file in files:
            file_path = os.path.join(root, file)
            
            # Process both .js and .html files
            if file.endswith('.js') or file.endswith('.html'):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        if file.endswith('.js'):
                            cleaned_content = remove_js_comments(content)
                            match = dependency_pattern_js.search(cleaned_content)
                            if match:
                                dependencies_str = match.group(1)
                                dependencies = [dep.strip().strip('\'"') for dep in dependencies_str.split(',') if dep.strip()]
                                process_dependencies(dependencies, file_path, dependencies_info)
                        
                        elif file.endswith('.html'):
                            match = dependency_pattern_html.findall(content)
                            if match:
                                process_dependencies(match, file_path, dependencies_info)

                except UnicodeDecodeError:
                    print(f"Skipping file due to encoding issues: {file_path}")
                    continue

    return dependencies_info

# Process dependencies function
def process_dependencies(dependencies, file_path, dependencies_info):
    for dep in dependencies:
        dep_parts = dep.split('/')
        if len(dep_parts) >= 2:
            version = dep_parts[-2].strip() 
            component_name = dep_parts[-1].replace('.component.xml', '').strip()  
            file_name = os.path.basename(file_path)
            print(f"Found version: {version} in file: {file_name}")
            if (dep, version, component_name) in dependencies_info:
                dependencies_info[(dep, version, component_name)].add(file_name)
            else:
                dependencies_info[(dep, version, component_name)] = {file_name}

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.settings = QSettings("MyApp", "DependencySearch")
        self.setWindowTitle("Dependency Search")
        layout = QVBoxLayout()

        # Button to select directory
        self.directory_button = QPushButton("Select Directory")
        self.directory_button.clicked.connect(self.select_directory)
        layout.addWidget(self.directory_button)

        # Label to display selected directory
        self.directory_label = QLabel("")
        layout.addWidget(self.directory_label)

        # Input for version filter
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("Enter version to filter (e.g., 1.0.0)")
        layout.addWidget(self.version_input)

        # Input for component name filter
        self.component_input = QLineEdit()
        self.component_input.setPlaceholderText("Enter component name (in 1-3 words)")
        layout.addWidget(self.component_input)

        # Button to start search
        self.search_button = QPushButton("Start Search")
        self.search_button.clicked.connect(self.start_search)
        layout.addWidget(self.search_button)

        # Table to display results
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(4)
        self.result_table.setHorizontalHeaderLabels(["Dependency", "Version", "Component Name", "Files Found In"])
        self.result_table.setColumnWidth(1, 80)  # Version column fixed to 80px
        self.result_table.setColumnWidth(2, 150)  
        self.result_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch) 
        self.result_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch) 
        self.result_table.setSortingEnabled(True)
        layout.addWidget(self.result_table)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)
        layout.addWidget(self.close_button)

        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

        self.directory = ""
        self.load_last_directory()
        self.showMaximized()

    def load_last_directory(self):
        last_directory = self.settings.value("lastDirectory", "")
        if last_directory:
            self.directory = last_directory
            self.directory_label.setText(f"Selected Directory: {self.directory}")
    
    def save_last_directory(self):
        self.settings.setValue("lastDirectory", self.directory)

    def select_directory(self):
        self.directory = QFileDialog.getExistingDirectory(self, "Select Directory", self.directory or os.path.expanduser("~"))
        if not self.directory:
            QMessageBox.warning(self, "Error", "Directory selection is required.")
        else:
            self.directory_label.setText(f"Selected Directory: {self.directory}")
            self.save_last_directory()
    
    def start_search(self):
        if not self.directory:
            QMessageBox.warning(self, "Error", "Directory selection is required.")
            return

        self.result_table.setRowCount(0)

        # Get the version and component name to filter by
        version_filter = self.version_input.text().strip()
        component_filter = self.component_input.text().strip()

        # Normalize the component filter input
        component_filter_normalized = normalize_component_name(component_filter)

        print(f"Normalized Component Name for Search: {component_filter_normalized}")  # Debugging log

        dependencies_info = search_dependencies_in_files(self.directory)

        if dependencies_info:
            row = 0
            for (dependency, version, component_name), file_names in sorted(dependencies_info.items(), key=lambda x: x[0][0]):
                # Perform case-insensitive comparison for component name
                if (not version_filter or version.lower() == version_filter.lower()) and \
                (not component_filter or component_name.lower() == component_filter_normalized.lower()):  # Case-insensitive comparison
                    self.result_table.insertRow(row)
                    self.result_table.setItem(row, 0, QTableWidgetItem(dependency))        
                    self.result_table.setItem(row, 1, QTableWidgetItem(version))           
                    self.result_table.setItem(row, 2, QTableWidgetItem(component_name))    
                    self.result_table.setItem(row, 3, QTableWidgetItem(', '.join(sorted(file_names))))
                    row += 1  
        else:
            QMessageBox.information(self, "Search Results", "No dependencies found.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
y