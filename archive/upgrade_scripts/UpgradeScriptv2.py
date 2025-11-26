"""
Woda Version Upgrade Script

This script provides a graphical user interface (GUI) using PySide6 to upgrade versioned directories 
and update version numbers in JavaScript and HTML files.

The application allows the user to:
1. Select a base directory to search for versioned subdirectories (formatted as X.X.X).
2. Copy directories that match the old version and update them to the new version.
3. Traverse JavaScript and HTML files within the copied directories to replace version strings 
   (in the format `/EAMD.ucp/`) from the old version to the new version.
4. Ensure that strings in JavaScript comments are not updated.
5. Specify how deep into the directory structure the script should go using a spin box. By default, 
   it traverses all subdirectories. The user can set the depth to limit the traversal.

Key Features:
- GUI for easy input of paths, old version, and new version.
- Directory traversal to identify and copy versioned folders.
- Spin box to control the depth of directory traversal.
- Update version strings in both `.js` and `.html` files.
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

PySide6 Copyright:
- PySide6 is developed and maintained by The Qt Company and is available under the LGPL license.
- It is a set of Python bindings for the Qt application framework, allowing for the creation of 
  cross-platform graphical applications.
- For further licensing and copyright information, visit The Qt Company’s website: 
  https://doc.qt.io/qtforpython/
"""

import os
import shutil
import re
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QSpinBox)


class VersionUpgradeApp(QWidget):
    """
    A PySide6-based GUI application for upgrading versioned directories and updating version numbers
    in both JavaScript (.js) and HTML (.html) files.

    This script allows users to select a base directory, specify an old version (in X.X.X format),
    and specify a new version. It traverses subdirectories named with version numbers (e.g., 0.0.0),
    duplicates them with the updated version, and updates occurrences of version numbers inside 
    JavaScript and HTML files.

    The script:
    - Ignores version numbers within JavaScript comments.
    - Replaces version numbers in both JavaScript and HTML files.
    - Allows users to set a depth limit for the directory traversal using a spin box.

    Dependencies:
    - Python 3.x
    - PySide6 for creating the GUI.
    - `os` and `shutil` for filesystem operations.
    - `re` for regular expressions.

    Example:
    ```
    python3 upgrade_script.py
    ```
    """

    def __init__(self):
        """
        Initialize the main GUI window and its components (widgets).
        """
        super().__init__()
        self.init_ui()

    def init_ui(self):
        """
        Set up the GUI layout and connect signals to slots (functions).
        """
        # Window setup
        self.setWindowTitle('Woda Version Upgrade')
        self.setGeometry(100, 100, 400, 250)

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

        # Submit button
        self.submit_button = QPushButton('Start Upgrade')
        self.submit_button.clicked.connect(self.start_upgrade)
        layout.addWidget(self.submit_button)

        # Close button
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close_app)
        layout.addWidget(self.close_button)

        # Set layout to window
        self.setLayout(layout)

    def browse_path(self):
        """
        Opens a file dialog to browse and select a directory path for the base folder to be processed.
        """
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.path_edit.setText(path)

    def start_upgrade(self):
        """
        Validates the input fields (entry path, current version, new version) and starts the upgrade process.
        If the inputs are invalid, it displays a warning message.
        """
        entry_path = self.path_edit.text().strip()
        old_version = self.curr_version_edit.text().strip()
        new_version = self.new_version_edit.text().strip()
        depth = self.depth_spinbox.value()

        # Check for empty fields
        if not entry_path or not old_version or not new_version:
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return

        # Validate version format (X.X.X)
        if not re.match(r'^\d+\.\d+\.\d+$', old_version) or not re.match(r'^\d+\.\d+\.\d+$', new_version):
            QMessageBox.warning(self, "Version Error", "Version must be in the format X.X.X")
            return

        # Start folder upgrade process
        self.upgrade_folders(entry_path, old_version, new_version, depth)

    def upgrade_folders(self, path, old_version, new_version, max_depth):
        """
        Traverses directories to locate versioned folders (e.g., 0.0.0) and copies them to the new version.
        For each copied folder, it updates JavaScript and HTML files with the new version number.

        Parameters:
        - path (str): The root path where the traversal begins.
        - old_version (str): The current version to be replaced.
        - new_version (str): The new version to be set.
        - max_depth (int): The maximum directory depth to traverse. If 0, traverses all directories.
        """
        for root, dirs, _ in os.walk(path):
            current_depth = root[len(path):].count(os.sep)

            if max_depth != 0 and current_depth >= max_depth:
                continue

            for folder in dirs:
                if re.match(r'^\d+\.\d+\.\d+$', folder):
                    folder_path = os.path.join(root, folder)

                    if folder == old_version:
                        new_folder_path = os.path.join(root, new_version)

                        # Skip if the new folder already exists
                        if os.path.exists(new_folder_path):
                            print(f"Skipping directory {new_folder_path} as it already exists.")
                            continue

                        # Copy the folder if it doesn't exist
                        shutil.copytree(folder_path, new_folder_path)

                        # Target all relevant subdirectories in the new copied folder
                        self.upgrade_specific_subdirectories(new_folder_path, old_version, new_version)

        QMessageBox.information(self, "Success", "Upgrade process completed successfully!")

    def upgrade_specific_subdirectories(self, folder_path, old_version, new_version):
        """
        This function targets specific subdirectories after copying the new version folder.
        Specifically:
        - Looks for 'js' and 'html' folders inside both 'src' and 'test' directories.

        Parameters:
        - folder_path (str): Path of the newly copied version directory.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        """
        # Define the subdirectory targets
        subdirs_to_process = [
            os.path.join(folder_path, 'src', 'js'),
            os.path.join(folder_path, 'src', 'html'),
            os.path.join(folder_path, 'test', 'js'),
            os.path.join(folder_path, 'test', 'html')
        ]

        # Process each subdirectory if it exists
        for subdir in subdirs_to_process:
            if os.path.exists(subdir):
                file_extension = '.js' if 'js' in subdir else '.html'
                self.update_dir_files(subdir, old_version, new_version, file_extension)

    def update_dir_files(self, dir_path, old_version, new_version, file_extension):
        """
        Traverses a directory to find files of a specified type and updates the version number.

        Parameters:
        - dir_path (str): Path of the directory to traverse.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        - file_extension (str): File extension to target (.js or .html).
        """
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    self.update_file(file_path, old_version, new_version)

    def update_file(self, file_path, old_version, new_version):
        """
        Reads a file and replaces the old version number with the new one.
        For JavaScript (.js) files, it avoids replacing version numbers inside comments.

        Parameters:
        - file_path (str): Path of the file to update.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.endswith('.js'):
            updated_content = self.replace_js_version(content, old_version, new_version)
        else:
            updated_content = content.replace(old_version, new_version)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    def replace_js_version(self, content, old_version, new_version):
        """
        Replaces occurrences of `/EAMD.ucp` followed by the old version number in JavaScript files,
        ignoring comments.

        Parameters:
        - content (str): The content of the JavaScript file.
        - old_version (str): Old version to replace.
        - new_version (str): New version to replace with.

        Returns:
        - str: The updated content with replaced version numbers.
        """
        def replacer(match):
            return match.group(0) if old_version not in match.group(0) else match.group(0).replace(old_version, new_version)

        pattern = re.compile(rf'(//.*?$|/\*.*?\*/|(/EAMD\.ucp[^\s]*{old_version}))', re.DOTALL | re.MULTILINE)
        updated_content = pattern.sub(replacer, content)
        return updated_content

    def close_app(self):
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
