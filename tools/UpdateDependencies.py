import sys
import os
import re
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton, QLabel, QFileDialog,
    QLineEdit, QTableWidget, QTableWidgetItem, QHBoxLayout, QHeaderView, QCheckBox
)
from PySide6.QtCore import QSettings, Qt

class DependencySearcher(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Set initial window size
        self.resize(1000, 600)

        # Load saved settings for default directory
        self.settings = QSettings('MyApp', 'DependencySearcher')
        self.default_dir = self.settings.value('default_directory', os.path.expanduser("~"))

        # Directory selection
        self.dir_label = QLabel(f"Selected Directory: {self.default_dir}")
        self.select_dir_button = QPushButton("Select Directory")
        self.select_dir_button.clicked.connect(self.select_directory)

        # Second directory selection (initially hidden)
        self.second_dir_label = QLabel("Select Secondary Directory (for dependency search):")
        self.second_dir_button = QPushButton("Select Secondary Directory")
        self.second_dir_button.clicked.connect(self.select_second_directory)
        self.second_dir_label.setVisible(False)  # Initially hidden
        self.second_dir_button.setVisible(False)  # Initially hidden

        # Checkbox to search all versions
        self.search_all_versions_checkbox = QCheckBox("Search all versions")
        self.search_all_versions_checkbox.stateChanged.connect(self.toggle_second_directory_selection)

        # Version input
        self.version_input = QLineEdit()
        self.version_input.setPlaceholderText("Enter version (e.g., x.x.x or x.x.x.x)")

        # Search button
        self.search_button = QPushButton("Search for Dependencies")
        self.search_button.clicked.connect(self.search_for_dependencies)

        # Output windows for showing results as tables
        self.left_table = QTableWidget()
        self.left_table.setColumnCount(2)  # Two columns: JS File and Path
        self.left_table.setHorizontalHeaderLabels(["Processed Files", "Path"])
        self.left_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.left_table.setSortingEnabled(True)

        self.right_table = QTableWidget()
        self.right_table.setColumnCount(6)
        self.right_table.setHorizontalHeaderLabels(["Dependency Path", "Component", "Parent", "Version Comparison", "Component/Version Status", "Action"])
        self.right_table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.right_table.setSortingEnabled(True)

        # Bottom close button and "Update All" button
        self.update_all_button = QPushButton("Update All")
        self.update_all_button.clicked.connect(self.update_all_dependencies)

        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close)

        # Layout organization
        layout.addWidget(self.dir_label)
        layout.addWidget(self.select_dir_button)
        layout.addWidget(self.version_input)
        layout.addWidget(self.search_all_versions_checkbox)
        layout.addWidget(self.second_dir_label)  # Second directory UI
        layout.addWidget(self.second_dir_button)  # Second directory UI
        layout.addWidget(self.search_button)

        # Split output layout with two tables
        output_layout = QHBoxLayout()
        output_layout.addWidget(self.left_table, 1)
        output_layout.addWidget(self.right_table, 2)
        layout.addLayout(output_layout)

        # Add the "Update All" and close buttons
        layout.addWidget(self.update_all_button)
        layout.addWidget(self.close_button)
        self.setLayout(layout)
        self.setWindowTitle("Dependency Searcher")

    def toggle_second_directory_selection(self, state):
        """Toggle the visibility of the second directory selection based on checkbox state."""
        if state == 2:  # Checked
            self.second_dir_label.setVisible(True)  # Show second directory label when checked
            self.second_dir_button.setVisible(True)  # Show second directory button when checked
        else:  # Unchecked
            self.second_dir_label.setVisible(False)  # Hide second directory label when unchecked
            self.second_dir_button.setVisible(False)  # Hide second directory button when unchecked

    def select_directory(self):
        dir_name = QFileDialog.getExistingDirectory(self, "Select Directory", self.default_dir)
        if dir_name:
            self.default_dir = dir_name
            self.dir_label.setText(f"Selected Directory: {self.default_dir}")
            self.settings.setValue('default_directory', self.default_dir)

    def select_second_directory(self):
        """Select the second directory for dependency search."""
        second_dir_name = QFileDialog.getExistingDirectory(self, "Select Second Directory", self.default_dir)
        if second_dir_name:
            self.second_dir = second_dir_name
            self.second_dir_label.setText(f"Selected Secondary Directory: {self.second_dir}")

    def search_for_dependencies(self):
        version = self.version_input.text()
        search_all_versions = self.search_all_versions_checkbox.isChecked()
        
        if not version and not search_all_versions:
            self.add_left_row("Please enter a version number or select 'Search all versions'.")
            return

        version_regex = re.compile(r"\d+\.\d+\.\d+(\.\d+)?")
        if not search_all_versions and not version_regex.match(version):
            self.add_left_row("Invalid version format. Please use x.x.x or x.x.x.x.")
            return

        # Clear previous table entries
        self.left_table.setRowCount(0)
        self.right_table.setRowCount(0)

        # Left window processing: Depending on the checkbox state
        if search_all_versions:
            # Search all directories (ignore version filtering)
            for root, dirs, files in os.walk(self.default_dir):
                for dir_name in dirs:
                    if version_regex.match(dir_name):  # Process directories that match any version
                        version_folder = os.path.join(root, dir_name)
                        self.process_version_folder(version_folder, version)
        else:
            # Search for the exact version directory
            for root, dirs, files in os.walk(self.default_dir):
                if version in dirs:
                    version_folder = os.path.join(root, version)
                    self.process_version_folder(version_folder, version)

        # Right window processing: Search for dependencies
        if search_all_versions and hasattr(self, 'second_dir'):
            # Use the second directory to search for dependencies
            self.search_dependencies_in_second_directory()
        else:
            # Use the first selected directory to search for dependencies
            self.search_dependencies_in_first_directory()

    def process_version_folder(self, folder_path, user_version):
        """Process both .js and .html files in the folder for dependencies."""
        for root, dirs, files in os.walk(folder_path):
            for file_name in files:
                if file_name.endswith('.js') or file_name.endswith('.html'):
                    file_path = os.path.join(root, file_name)
                    # Add both the file name and its path to the left table
                    self.add_left_row(file_name, root)

    def search_dependencies_in_first_directory(self):
        """Search dependencies in the first selected directory."""
        for row in range(self.left_table.rowCount()):
            file_name = self.left_table.item(row, 0).text()
            file_path = os.path.join(self.left_table.item(row, 1).text(), file_name)
            self.process_file(file_path, self.version_input.text())

    def search_dependencies_in_second_directory(self):
        """Search dependencies in the second directory."""
        for row in range(self.left_table.rowCount()):
            file_name = self.left_table.item(row, 0).text()
            file_path = os.path.join(self.left_table.item(row, 1).text(), file_name)
            self.process_file_in_second_directory(file_path, self.version_input.text())

    def process_file(self, file_path, user_version):
        """Process files to check for dependencies."""
        with open(file_path, 'r') as file:
            content = file.read()

        # Regex to find dependencies in the static dependencies block for JS or HTML
        dependencies_regex = re.compile(r'static\s+get\s+dependencies\s*\(\)\s*\{\s*return\s*\[(.*?)\]', re.DOTALL)
        html_dependencies_regex = re.compile(r'\"(\/EAMD\.ucp\/.*?)\"')

        # Find dependencies in JavaScript files
        match = dependencies_regex.search(content)
        if match:
            dependencies_block = match.group(1)
            dependencies = re.findall(r'\"(.*?)\"', dependencies_block)
        else:
            # Check for dependencies in HTML files
            dependencies = html_dependencies_regex.findall(content)

        parent_file_name = os.path.basename(file_path)  # Get the file name

        for dep in dependencies:
            if '/EAMD.ucp/' in dep:
                component_name, dep_version = self.extract_component_info(dep)
                if component_name and dep_version:
                    if self.is_valid_version(dep_version):
                        if self.is_version_smaller(dep_version, user_version):
                            # Check component and version existence
                            status = self.check_component_and_version(component_name, user_version)
                            self.add_right_row(dep, component_name, parent_file_name, f"{dep_version} < {user_version}", status, file_path, dep)

    def process_file_in_second_directory(self, file_path, user_version):
        """Process dependencies in files located in the second directory."""
        self.process_file(file_path, user_version)  # Reuse the same logic for file processing

    def extract_component_info(self, dep_string):
        parts = dep_string.split('/')
        if len(parts) >= 5:
            version = parts[-2]        # 2nd last element is the version number
            component_name = parts[-3]  # 3rd last element is the component name
            return component_name, version
        return None, None

    def is_valid_version(self, version):
        return bool(re.match(r'^\d+(\.\d+)*$', version))

    def is_version_smaller(self, dep_version, user_version):
        dep_version_tuple = tuple(map(int, dep_version.split('.')))
        user_version_tuple = tuple(map(int, user_version.split('.')))
        return dep_version_tuple < user_version_tuple

    def check_component_and_version(self, component_name, user_version):
        """Check if the component with the user version exists in either first or second directory."""
        component_exists = False
        version_exists = False

        # Check the directory based on whether "Search all versions" is checked
        search_dir = self.second_dir if self.search_all_versions_checkbox.isChecked() else self.default_dir

        # Walk through the selected directory to check for the component and its version
        for root, dirs, files in os.walk(search_dir):
            if component_name in root:  # Search for the component name in the directory
                component_exists = True
                # Now check if the given version exists in the component path
                if user_version in dirs:
                    version_exists = True
                    break

        if not component_exists:
            return "Component does not exist"
        elif not version_exists:
            return "Version does not exist"
        else:
            return "Version exists"

    def add_left_row(self, file_name, file_path):
        row_position = self.left_table.rowCount()
        self.left_table.insertRow(row_position)
        self.left_table.setItem(row_position, 0, QTableWidgetItem(file_name))  # File name column
        self.left_table.setItem(row_position, 1, QTableWidgetItem(file_path))  # Path column

    def add_right_row(self, dependency, component, parent, version_comparison, status, file_path, original_dep):
        row_position = self.right_table.rowCount()
        self.right_table.insertRow(row_position)
        self.right_table.setItem(row_position, 0, QTableWidgetItem(dependency))
        self.right_table.setItem(row_position, 1, QTableWidgetItem(component))
        self.right_table.setItem(row_position, 2, QTableWidgetItem(parent))  # Parent column (file name)
        self.right_table.setItem(row_position, 3, QTableWidgetItem(version_comparison))
        self.right_table.setItem(row_position, 4, QTableWidgetItem(status))

        # Add a button to update the dependency
        update_button = QPushButton("Update")
        update_button.setEnabled(status == "Version exists")
        update_button.clicked.connect(lambda: self.update_dependency(file_path, original_dep))
        self.right_table.setCellWidget(row_position, 5, update_button)

    def update_dependency(self, file_path, original_dep):
        user_version = self.version_input.text()

        # Read the file content
        with open(file_path, 'r') as file:
            content = file.read()

        # Update the dependency string to use the user version
        updated_content = content.replace(original_dep, original_dep.replace(original_dep.split('/')[-2], user_version))

        # Write the updated content back to the file
        with open(file_path, 'w') as file:
            file.write(updated_content)

        # Re-run the search to refresh the results after updating the file
        self.search_for_dependencies()

    def update_all_dependencies(self):
        # Loop through all rows in the right table
        for row in range(self.right_table.rowCount()):
            status_item = self.right_table.item(row, 4)
            if status_item and status_item.text() == "Version exists":
                # Get the dependency and file path from the current row
                dependency = self.right_table.item(row, 0).text()
                parent = self.right_table.item(row, 2).text()

                # Find the corresponding file path for the parent (file name)
                for left_row in range(self.left_table.rowCount()):
                    if self.left_table.item(left_row, 0).text() == parent:
                        file_path = os.path.join(self.left_table.item(left_row, 1).text(), parent)
                        self.update_dependency(file_path, dependency)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DependencySearcher()
    window.show()
    sys.exit(app.exec())
