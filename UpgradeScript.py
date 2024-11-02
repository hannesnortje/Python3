"""
Woda Version Upgrade Script

This script provides a graphical user interface (GUI) using PySide6 to upgrade versioned directories
and update version numbers in JavaScript and HTML files.

The application allows the user to:
1. Select a base directory to search for versioned subdirectories (formatted as X.X.X).
2. Copy directories that match the old version and update them to the new version.
3. Traverse JavaScript and HTML files within the copied directories to replace version strings
   (in the format `/EAMD.ucp/`) from the old version to the new version, but only when they contain the
   last word of the entry path.
4. Ensure that strings in JavaScript comments are not updated.
5. Specify how deep into the directory structure the script should go using a spin box.
6. Independently, replace occurrences of a specific component’s `/EAMD.ucp/` path string in a selected directory,
   automatically converting the component name to PascalCase if necessary.

Key Features:
- GUI for easy input of paths, old version, and new version.
- Directory traversal to identify and copy versioned folders.
- Spin box to control the depth of directory traversal.
- Update version strings in both `.js` and `.html` files.
- Replace specific component `/EAMD.ucp/` path strings in the chosen directory.
- Ignore version replacements within JavaScript comments.

Usage:
Run the script using Python 3.x:
    $ python3 upgrade_script.py

Dependencies:
- **Python 3.x**: Make sure Python 3.x is installed on your system.
- **PySide6**: Required for the GUI components. Install using:
    $ pip install PySide6
- **os**: Standard Python library for filesystem operations.
- **shutil**: Standard Python library for high-level file operations (e.g., copying directories).
- **re**: Standard Python library for working with regular expressions.
- **typeguard**: Used for runtime type checking.

"""

import os
import shutil
import re
import sys
from typing import List
from typeguard import typechecked
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QSpinBox)


@typechecked
class VersionUpgradeApp(QWidget):
    """
    A PySide6-based GUI application for upgrading versioned directories and updating version numbers
    in both JavaScript (.js) and HTML (.html) files.

    The application also allows for the replacement of specific component `/EAMD.ucp/` path strings in a selected directory.
    The component name is converted to PascalCase if necessary, and the new path string is applied wherever the component appears.
    """

    def __init__(self) -> None:
        """
        Initialize the main GUI window and its components (widgets).
        """
        super().__init__()
        self.init_ui()

    def init_ui(self) -> None:
        """
        Set up the GUI layout and connect signals to slots (functions).
        """
        # Window setup
        self.setWindowTitle('Woda Version Upgrade')
        self.setGeometry(100, 100, 400, 400)

        # Layout setup
        layout = QVBoxLayout()

        # Path entry
        self.path_label = QLabel('Entry Path:')
        self.path_edit = QLineEdit()
        self.path_button = QPushButton('Browse')
        self.path_button.clicked.connect(self.browse_path)

        layout.addWidget(self.path_label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.path_button)

        # Current version entry
        self.curr_version_label = QLabel('Current Version:')
        self.curr_version_edit = QLineEdit()
        layout.addWidget(self.curr_version_label)
        layout.addWidget(self.curr_version_edit)

        # New version entry
        self.new_version_label = QLabel('New Version:')
        self.new_version_edit = QLineEdit()
        layout.addWidget(self.new_version_label)
        layout.addWidget(self.new_version_edit)

        # Traversal depth entry
        self.depth_label = QLabel('Traversal Depth (empty = all):')
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setMinimum(0)
        self.depth_spinbox.setSpecialValueText("All")
        self.depth_spinbox.setValue(0)  # Default to unlimited traversal
        layout.addWidget(self.depth_label)
        layout.addWidget(self.depth_spinbox)

        # Submit button for version upgrade
        self.submit_button = QPushButton('Start Upgrade')
        self.submit_button.clicked.connect(self.start_upgrade)
        layout.addWidget(self.submit_button)

        # New Section for Component Replacement
        self.component_label = QLabel('Component Name:')
        self.component_edit = QLineEdit()
        layout.addWidget(self.component_label)
        layout.addWidget(self.component_edit)

        self.new_path_label = QLabel('Replacement Path (/EAMD.ucp):')
        self.new_path_edit = QLineEdit()
        layout.addWidget(self.new_path_label)
        layout.addWidget(self.new_path_edit)

        # Directory selection for component replacement
        self.component_dir_label = QLabel('Component Directory:')
        self.component_dir_edit = QLineEdit()
        self.component_dir_button = QPushButton('Browse')
        self.component_dir_button.clicked.connect(self.browse_component_directory)

        layout.addWidget(self.component_dir_label)
        layout.addWidget(self.component_dir_edit)
        layout.addWidget(self.component_dir_button)

        # Submit button for component replacement
        self.component_submit_button = QPushButton('Replace Component Paths')
        self.component_submit_button.clicked.connect(self.replace_component_paths)
        layout.addWidget(self.component_submit_button)

        # Close button at the bottom
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close_app)
        layout.addWidget(self.close_button)

        # Set layout to window
        self.setLayout(layout)

    @typechecked
    def browse_path(self) -> None:
        """
        Opens a file dialog to browse and select a directory path for the base folder to be processed.
        """
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.path_edit.setText(path)

    @typechecked
    def browse_component_directory(self) -> None:
        """
        Opens a file dialog to select the directory for the component path replacement.
        """
        path = QFileDialog.getExistingDirectory(self, "Select Component Folder")
        if path:
            self.component_dir_edit.setText(path)

    @typechecked
    def start_upgrade(self) -> None:
        """
        Validates the input fields (entry path, current version, new version) and starts the upgrade process.
        If the inputs are invalid, it displays a warning message.
        """
        entry_path: str = self.path_edit.text().strip()
        old_version: str = self.curr_version_edit.text().strip()
        new_version: str = self.new_version_edit.text().strip()
        depth: int = self.depth_spinbox.value()

        # Check for empty fields
        if not entry_path or not old_version or not new_version:
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return

        # Validate version format (X.X.X and X.X.X.X)
        if not re.match(r'^\d+\.\d+\.\d+(\.\d+)?$', old_version) or not re.match(r'^\d+\.\d+\.\d+(\.\d+)?$', new_version):
            QMessageBox.warning(self, "Version Error", "Version must be in the format X.X.X or X.X.X.X")
            return

        # Extract the last word from the entry path (after the last '/')
        last_word = os.path.basename(os.path.normpath(entry_path))

        # Start folder upgrade process
        self.upgrade_folders(entry_path, old_version, new_version, depth, last_word)

    @typechecked
    def upgrade_folders(self, path: str, old_version: str, new_version: str, max_depth: int, last_word: str) -> None:
        """
        Traverses directories to locate versioned folders (e.g., 0.0.0) and copies them to the new version.
        For each copied folder, it updates JavaScript and HTML files with the new version number.

        The version number is updated only in strings that contain the last word of the entry path.

        Parameters:
        - path (str): The root path where the traversal begins.
        - old_version (str): The current version to be replaced.
        - new_version (str): The new version to be set.
        - max_depth (int): The maximum directory depth to traverse. If 0, traverses all directories.
        - last_word (str): The last word from the entry path. Only update version numbers in strings containing this word.
        """
        for root, dirs, _ in os.walk(path):
            current_depth = root[len(path):].count(os.sep)

            if max_depth != 0 and current_depth >= max_depth:
                continue

            for folder in dirs:
                # Match both X.X.X and X.X.X.X formats
                if re.match(r'^\d+\.\d+\.\d+(\.\d+)?$', folder):
                    folder_path = os.path.join(root, folder)

                    if folder == old_version:
                        new_folder_path = os.path.join(root, new_version)

                        # Skip if the new folder already exists
                        if os.path.exists(new_folder_path):
                            print(f"Skipping directory {new_folder_path} as it already exists.")
                            continue

                        # Copy the folder manually using os.walk and shutil.copy2
                        self.copy_directory(folder_path, new_folder_path)

                        # Target all relevant subdirectories in the new copied folder
                        self.upgrade_specific_subdirectories(new_folder_path, old_version, new_version, last_word)


        QMessageBox.information(self, "Success", "Upgrade process completed successfully!")

    @typechecked
    def copy_directory(self, src: str, dst: str) -> None:
        """
        Manually copies a directory structure from src to dst, using os.walk and shutil.copy2 to ensure
        it works across platforms like macOS and Windows.

        Parameters:
        - src (str): The source directory to copy.
        - dst (str): The destination directory where the content will be copied.
        """
        # Create destination directory if it does not exist
        if not os.path.exists(dst):
            os.makedirs(dst)
        for root, dirs, files in os.walk(src):
            relative_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, relative_path)

            # Ensure destination directory exists
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            # Copy files
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dest_file)  # copy2 preserves metadata

    @typechecked
    def upgrade_specific_subdirectories(self, folder_path: str, old_version: str, new_version: str, last_word: str) -> None:
        """
        This function targets specific subdirectories after copying the new version folder.
        Specifically:
        - Looks for 'js' and 'html' folders inside both 'src' and 'test' directories.

        Only updates version numbers in strings that contain the last word of the entry path.

        Parameters:
        - folder_path (str): Path of the newly copied version directory.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - last_word (str): The last word from the entry path.
        """
        # Define the subdirectory targets
        subdirs_to_process: List[str] = [
            os.path.join(folder_path, 'src', 'js'),
            os.path.join(folder_path, 'src', 'html'),
            os.path.join(folder_path, 'test', 'js'),
            os.path.join(folder_path, 'test', 'html')
        ]

        # Process each subdirectory if it exists
        for subdir in subdirs_to_process:
            if os.path.exists(subdir):
                file_extension = '.js' if 'js' in subdir else '.html'
                self.update_dir_files(subdir, old_version, new_version, file_extension, last_word)

    @typechecked
    def update_dir_files(self, dir_path: str, old_version: str, new_version: str, file_extension: str, last_word: str) -> None:
        """
        Traverses a directory to find files of a specified type and updates the version number.

        The version number is updated only in strings that contain the last word of the entry path.

        Parameters:
        - dir_path (str): Path of the directory to traverse.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - file_extension (str): File extension to target (.js or .html).
        - last_word (str): The last word from the entry path.
        """
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    self.update_file(file_path, old_version, new_version, last_word)

    @typechecked
    def update_file(self, file_path: str, old_version: str, new_version: str, last_word: str) -> None:
        """
        Reads a file and replaces the old version number with the new one.
        For JavaScript (.js) and HTML (.html) files, it only updates version numbers in strings that contain
        the last word of the entry path.

        Parameters:
        - file_path (str): Path of the file to update.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - last_word (str): The last word from the entry path.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Update version number only in strings that contain the last word from the entry path
        if file_path.endswith('.js'):
            updated_content = self.replace_js_version(content, old_version, new_version, last_word)
        else:
            updated_content = self.replace_html_version(content, old_version, new_version, last_word)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    @typechecked
    def replace_js_version(self, content: str, old_version: str, new_version: str, last_word: str) -> str:
        """
        Replaces occurrences of `/EAMD.ucp` followed by the old version number in JavaScript files,
        but only if the string contains the last word from the entry path.

        Parameters:
        - content (str): The content of the JavaScript file.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - last_word (str): The last word from the entry path.

        Returns:
        - str: The updated content with replaced version numbers.
        """
        # Debugging: Print the last_word and the old version to ensure we're targeting the right strings
        # print(f"Replacing in JS: Looking for version '{old_version}' in paths containing '{last_word}'")

        # Match the "/EAMD.ucp" string containing the last word and replace the version number
        # Adjust regex to ensure that it captures the last word correctly.
        pattern = re.compile(rf'(/EAMD\.ucp/.*?/{last_word}/.*?)({old_version})')

        # Check if there are matches before replacing (for debugging)
        # matches = pattern.findall(content)
        # if matches:
        #     print(f"Found {len(matches)} matches for replacement: {matches}")
        # else:
        #     print("No matches found for replacement.")

        # Perform the replacement if any matches are found
        updated_content = pattern.sub(rf'\g<1>{new_version}', content)
        return updated_content

    @typechecked
    def replace_html_version(self, content: str, old_version: str, new_version: str, last_word: str) -> str:
        """
        Replaces occurrences of `/EAMD.ucp` followed by the old version number in HTML files,
        but only if the string contains the last word from the entry path.

        Parameters:
        - content (str): The content of the HTML file.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - last_word (str): The last word from the entry path.

        Returns:
        - str: The updated content with replaced version numbers.
        """
        # Debugging: Print the last_word and the old version to ensure we're targeting the right strings
        # print(f"Replacing in HTML: Looking for version '{old_version}' in paths containing '{last_word}'")

        # Match the "/EAMD.ucp" string containing the last word and replace the version number
        pattern = re.compile(rf'(/EAMD\.ucp/.*?/{last_word}/.*?)({old_version})')

        # Check if there are matches before replacing (for debugging)
        # matches = pattern.findall(content)
        # if matches:
        #     print(f"Found {len(matches)} matches for replacement: {matches}")
        # else:
        #     print("No matches found for replacement.")

        # Perform the replacement if any matches are found
        updated_content = pattern.sub(rf'\g<1>{new_version}', content)
        return updated_content

    @typechecked
    def replace_component_paths(self) -> None:
        """
        Replaces all occurrences of the component's `/EAMD.ucp/` path string in the selected directory and subdirectories.
        The component name is converted to PascalCase if necessary, and the replacement path string is provided by the user.
        """
        component_dir: str = self.component_dir_edit.text().strip()
        component_name: str = self.component_edit.text().strip()
        new_path: str = self.new_path_edit.text().strip()

        if not component_dir or not component_name or not new_path:
            QMessageBox.warning(self, "Input Error", "All fields must be filled for component replacement!")
            return

        # Convert component name to PascalCase
        component_name = ''.join(word.capitalize() for word in re.split(r'[\s_-]', component_name))

        # Perform the replacement in the directory
        self.replace_paths_in_dir(component_dir, component_name, new_path)

    @typechecked
    def replace_paths_in_dir(self, dir_path: str, component_name: str, new_path: str) -> None:
        """
        Replaces the entire old component path strings with the new ones in the specified directory.

        Parameters:
        - dir_path (str): The directory where replacements will occur.
        - component_name (str): The PascalCase component name to search for in paths.
        - new_path (str): The new path to replace the old paths with.
        """
        # Pattern to match the entire old component path for replacement
        old_path_pattern = re.compile(rf'/EAMD\.ucp/.*?/{component_name}/.*?\.component\.xml')

        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith('.js') or file.endswith('.html'):
                    file_path = os.path.join(root, file)
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Replace occurrences of the old component path with the new path
                    updated_content = old_path_pattern.sub(new_path, content)

                    # Write back the updated content
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)

        QMessageBox.information(self, "Success", "Component paths replaced successfully!")

    @typechecked
    def close_app(self) -> None:
        """
        Closes the application when the close button is clicked.
        """
        self.close()


if __name__ == "__main__":
    """
    Entry point of the application. It creates and runs the PySide6 application.
    """
    app = QApplication(sys.argv)
    window = VersionUpgradeApp()
    window.show()
    sys.exit(app.exec())
