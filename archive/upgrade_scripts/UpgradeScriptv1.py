import os
import shutil
import re
import sys
from PySide6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, QMessageBox, QSpinBox)


class VersionUpgradeApp(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('Metatrom Version Upgrade')
        self.setGeometry(100, 100, 400, 250)

        layout = QVBoxLayout()

        self.path_label = QLabel('Entry Path:')
        self.path_edit = QLineEdit()
        self.path_button = QPushButton('Browse')
        self.path_button.clicked.connect(self.browse_path)

        layout.addWidget(self.path_label)
        layout.addWidget(self.path_edit)
        layout.addWidget(self.path_button)

        self.curr_version_label = QLabel('Current Version:')
        self.curr_version_edit = QLineEdit()
        layout.addWidget(self.curr_version_label)
        layout.addWidget(self.curr_version_edit)

        self.new_version_label = QLabel('New Version:')
        self.new_version_edit = QLineEdit()
        layout.addWidget(self.new_version_label)
        layout.addWidget(self.new_version_edit)

        self.depth_label = QLabel('Traversal Depth (empty = all):')
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setMinimum(0)
        self.depth_spinbox.setSpecialValueText("All")
        self.depth_spinbox.setValue(0)  # Default to unlimited traversal
        layout.addWidget(self.depth_label)
        layout.addWidget(self.depth_spinbox)

        self.submit_button = QPushButton('Start Upgrade')
        self.submit_button.clicked.connect(self.start_upgrade)
        layout.addWidget(self.submit_button)

        self.setLayout(layout)

    def browse_path(self):
        path = QFileDialog.getExistingDirectory(self, "Select Folder")
        if path:
            self.path_edit.setText(path)

    def start_upgrade(self):
        entry_path = self.path_edit.text().strip()
        old_version = self.curr_version_edit.text().strip()
        new_version = self.new_version_edit.text().strip()
        depth = self.depth_spinbox.value()

        if not entry_path or not old_version or not new_version:
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return

        if not re.match(r'^\d+\.\d+\.\d+$', old_version) or not re.match(r'^\d+\.\d+\.\d+$', new_version):
            QMessageBox.warning(self, "Version Error", "Version must be in the format X.X.X")
            return

        self.upgrade_folders(entry_path, old_version, new_version, depth)

    def upgrade_folders(self, path, old_version, new_version, max_depth):
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
        for root, _, files in os.walk(dir_path):
            for file in files:
                if file.endswith(file_extension):
                    file_path = os.path.join(root, file)
                    self.update_file(file_path, old_version, new_version)

    def update_file(self, file_path, old_version, new_version):
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if file_path.endswith('.js'):
            updated_content = self.replace_js_version(content, old_version, new_version)
        else:
            updated_content = content.replace(old_version, new_version)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(updated_content)

    def replace_js_version(self, content, old_version, new_version):
        def replacer(match):
            return match.group(0) if old_version not in match.group(0) else match.group(0).replace(old_version, new_version)

        pattern = re.compile(rf'(//.*?$|/\*.*?\*/|(/EAMD\.ucp[^\s]*{old_version}))', re.DOTALL | re.MULTILINE)
        updated_content = pattern.sub(replacer, content)
        return updated_content


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VersionUpgradeApp()
    window.show()
    sys.exit(app.exec())
