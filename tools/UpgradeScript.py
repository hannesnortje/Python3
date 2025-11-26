"""
Woda Version Upgrade Script

This script provides a graphical user interface (GUI) using PySide6 to upgrade versioned directories
and update version numbers in JavaScript, HTML, TypeScript, and JSON files.

The application allows the user to:
1. Select a base directory to search for versioned subdirectories (formatted as X.X.X).
2. Copy directories that match the old version and update them to the new version.
3. Traverse files within the copied directories to replace version strings
   (in the format `/EAMD.ucp/`) from the old version to the new version, but only when they contain the
   last word of the entry path.
4. Ensure that strings in JavaScript comments are not updated.
5. Specify how deep into the directory structure the script should go using a spin box.
6. Independently, replace occurrences of a specific component's `/EAMD.ucp/` path string in a selected directory,
   automatically converting the component name to PascalCase if necessary.
7. Preview changes before applying them (dry-run mode).
8. Create backups before modifying files.

Key Features:
- GUI with tabbed interface for easy input of paths, old version, and new version.
- Directory traversal to identify and copy versioned folders.
- Spin box to control the depth of directory traversal.
- Update version strings in `.js`, `.html`, `.ts`, `.json`, and `.xml` files.
- Replace specific component `/EAMD.ucp/` path strings in the chosen directory.
- Ignore version replacements within JavaScript comments.
- Dry-run preview mode to see changes before applying.
- Automatic backup creation before modifications.
- Progress feedback with file count display.
- Remembers last used directories and window position.

Usage:
Run the script using Python 3.x:
    $ python3 UpgradeScript.py

Dependencies:
- Python 3.x
- PySide6: GUI components
- typeguard: Runtime type checking
"""

import os
import shutil
import re
import sys
import logging
from datetime import datetime
from typing import List, Tuple, Optional, Set
from typeguard import typechecked
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QFileDialog, QMessageBox, QSpinBox, QTabWidget,
    QTextEdit, QCheckBox, QProgressBar, QGroupBox, QFormLayout
)
from PySide6.QtCore import QSettings, Qt

# ============================================================================
# Constants
# ============================================================================
EAMD_PATH_PREFIX = "/EAMD.ucp/"
COMPONENT_XML_SUFFIX = ".component.xml"
VERSION_PATTERN = r'^\d+\.\d+\.\d+(\.\d+)?$'

# Supported file extensions
FILE_EXTENSIONS: Set[str] = {'.js', '.html', '.ts', '.json', '.xml'}

# Directories to exclude from processing
EXCLUDE_DIRS: Set[str] = {'node_modules', '.git', '__pycache__', '.venv', 'venv', '.idea', '.vscode'}

# Application settings keys
SETTINGS_ORG = 'Woda'
SETTINGS_APP = 'VersionUpgrade'
SETTINGS_LAST_PATH = 'last_path'
SETTINGS_LAST_COMPONENT_PATH = 'last_component_path'
SETTINGS_WINDOW_GEOMETRY = 'window_geometry'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@typechecked
class VersionUpgradeApp(QWidget):
    """
    A PySide6-based GUI application for upgrading versioned directories and updating version numbers
    in JavaScript, HTML, TypeScript, JSON, and XML files.

    The application also allows for the replacement of specific component `/EAMD.ucp/` path strings 
    in a selected directory.
    """

    def __init__(self) -> None:
        """Initialize the main GUI window and its components."""
        super().__init__()
        self.settings = QSettings(SETTINGS_ORG, SETTINGS_APP)
        self.files_modified: int = 0
        self.files_scanned: int = 0
        self.preview_changes: List[Tuple[str, str, str]] = []  # (file, old, new)
        self.init_ui()
        self.restore_window_state()

    def init_ui(self) -> None:
        """Set up the GUI layout with tabbed interface."""
        self.setWindowTitle('Woda Version Upgrade')
        self.setMinimumSize(600, 500)

        main_layout = QVBoxLayout()

        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Tab 1: Version Upgrade
        self.version_tab = self.create_version_upgrade_tab()
        self.tab_widget.addTab(self.version_tab, "Version Upgrade")
        
        # Tab 2: Component Replacement
        self.component_tab = self.create_component_replacement_tab()
        self.tab_widget.addTab(self.component_tab, "Component Replacement")

        main_layout.addWidget(self.tab_widget)

        # Progress bar (shared)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Log/Preview area (shared)
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setMaximumHeight(150)
        self.log_area.setPlaceholderText("Activity log will appear here...")
        main_layout.addWidget(self.log_area)

        # Close button
        self.close_button = QPushButton('Close')
        self.close_button.clicked.connect(self.close_app)
        main_layout.addWidget(self.close_button)

        self.setLayout(main_layout)

    def create_version_upgrade_tab(self) -> QWidget:
        """Create the version upgrade tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Path selection group
        path_group = QGroupBox("Directory Selection")
        path_layout = QFormLayout()
        
        path_row = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select the base directory to process...")
        self.path_button = QPushButton('Browse')
        self.path_button.clicked.connect(self.browse_path)
        path_row.addWidget(self.path_edit)
        path_row.addWidget(self.path_button)
        path_layout.addRow("Entry Path:", path_row)
        
        path_group.setLayout(path_layout)
        layout.addWidget(path_group)

        # Version settings group
        version_group = QGroupBox("Version Settings")
        version_layout = QFormLayout()
        
        self.curr_version_edit = QLineEdit()
        self.curr_version_edit.setPlaceholderText("e.g., 3.1.0 or 3.1.0.1")
        version_layout.addRow("Current Version:", self.curr_version_edit)
        
        self.new_version_edit = QLineEdit()
        self.new_version_edit.setPlaceholderText("e.g., 3.2.0 or 3.2.0.1")
        version_layout.addRow("New Version:", self.new_version_edit)
        
        self.depth_spinbox = QSpinBox()
        self.depth_spinbox.setMinimum(0)
        self.depth_spinbox.setMaximum(100)
        self.depth_spinbox.setSpecialValueText("Unlimited")
        self.depth_spinbox.setValue(0)
        version_layout.addRow("Traversal Depth:", self.depth_spinbox)
        
        version_group.setLayout(version_layout)
        layout.addWidget(version_group)

        # Options group
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.backup_checkbox = QCheckBox("Create backup before modifying files")
        self.backup_checkbox.setChecked(True)
        options_layout.addWidget(self.backup_checkbox)
        
        self.dry_run_checkbox = QCheckBox("Dry run (preview changes without applying)")
        options_layout.addWidget(self.dry_run_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Auto-detect button
        self.auto_detect_button = QPushButton('Auto-detect Current Version')
        self.auto_detect_button.clicked.connect(self.auto_detect_version)
        layout.addWidget(self.auto_detect_button)

        # Action buttons
        button_layout = QHBoxLayout()
        
        self.preview_button = QPushButton('Preview Changes')
        self.preview_button.clicked.connect(self.preview_upgrade)
        button_layout.addWidget(self.preview_button)
        
        self.submit_button = QPushButton('Start Upgrade')
        self.submit_button.clicked.connect(self.start_upgrade)
        button_layout.addWidget(self.submit_button)
        
        layout.addLayout(button_layout)
        layout.addStretch()

        tab.setLayout(layout)
        return tab

    def create_component_replacement_tab(self) -> QWidget:
        """Create the component replacement tab."""
        tab = QWidget()
        layout = QVBoxLayout()

        # Directory selection group
        dir_group = QGroupBox("Directory Selection")
        dir_layout = QFormLayout()
        
        dir_row = QHBoxLayout()
        self.component_dir_edit = QLineEdit()
        self.component_dir_edit.setPlaceholderText("Select directory for component replacement...")
        self.component_dir_button = QPushButton('Browse')
        self.component_dir_button.clicked.connect(self.browse_component_directory)
        dir_row.addWidget(self.component_dir_edit)
        dir_row.addWidget(self.component_dir_button)
        dir_layout.addRow("Directory:", dir_row)
        
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Component settings group
        component_group = QGroupBox("Component Settings")
        component_layout = QFormLayout()
        
        self.component_edit = QLineEdit()
        self.component_edit.setPlaceholderText("e.g., MyComponent or my-component")
        component_layout.addRow("Component Name:", self.component_edit)
        
        self.new_path_edit = QLineEdit()
        self.new_path_edit.setPlaceholderText("/EAMD.ucp/.../ComponentName.component.xml")
        component_layout.addRow("Replacement Path:", self.new_path_edit)
        
        component_group.setLayout(component_layout)
        layout.addWidget(component_group)

        # Options
        options_group = QGroupBox("Options")
        options_layout = QVBoxLayout()
        
        self.component_backup_checkbox = QCheckBox("Create backup before modifying files")
        self.component_backup_checkbox.setChecked(True)
        options_layout.addWidget(self.component_backup_checkbox)
        
        self.component_dry_run_checkbox = QCheckBox("Dry run (preview changes without applying)")
        options_layout.addWidget(self.component_dry_run_checkbox)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Action button
        self.component_submit_button = QPushButton('Replace Component Paths')
        self.component_submit_button.clicked.connect(self.replace_component_paths)
        layout.addWidget(self.component_submit_button)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def restore_window_state(self) -> None:
        """Restore window geometry from settings."""
        geometry = self.settings.value(SETTINGS_WINDOW_GEOMETRY)
        if geometry:
            self.restoreGeometry(geometry)
        
        last_path = self.settings.value(SETTINGS_LAST_PATH, "")
        if last_path:
            self.path_edit.setText(last_path)
        
        last_component_path = self.settings.value(SETTINGS_LAST_COMPONENT_PATH, "")
        if last_component_path:
            self.component_dir_edit.setText(last_component_path)

    def save_window_state(self) -> None:
        """Save window geometry to settings."""
        self.settings.setValue(SETTINGS_WINDOW_GEOMETRY, self.saveGeometry())
        self.settings.setValue(SETTINGS_LAST_PATH, self.path_edit.text())
        self.settings.setValue(SETTINGS_LAST_COMPONENT_PATH, self.component_dir_edit.text())

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_window_state()
        super().closeEvent(event)

    def is_directory_empty(self, path: str) -> bool:
        """
        Check if a directory is empty (contains no files, only empty subdirectories allowed).
        
        Parameters:
        - path (str): The directory path to check.
        
        Returns:
        - bool: True if the directory contains no files, False otherwise.
        """
        for root, dirs, files in os.walk(path):
            if files:
                return False
        return True

    def log(self, message: str, level: str = "info") -> None:
        """Log a message to the log area and logger."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        formatted_msg = f"[{timestamp}] {message}"
        self.log_area.append(formatted_msg)
        
        if level == "error":
            logger.error(message)
        elif level == "warning":
            logger.warning(message)
        else:
            logger.info(message)
        
        # Process events to update UI
        QApplication.processEvents()

    def browse_path(self) -> None:
        """Open a file dialog to browse and select a directory path."""
        start_dir = self.path_edit.text() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Folder", start_dir)
        if path:
            self.path_edit.setText(path)
            self.settings.setValue(SETTINGS_LAST_PATH, path)

    def browse_component_directory(self) -> None:
        """Open a file dialog to select the directory for component path replacement."""
        start_dir = self.component_dir_edit.text() or os.path.expanduser("~")
        path = QFileDialog.getExistingDirectory(self, "Select Component Folder", start_dir)
        if path:
            self.component_dir_edit.setText(path)
            self.settings.setValue(SETTINGS_LAST_COMPONENT_PATH, path)

    def auto_detect_version(self) -> None:
        """Auto-detect the current version from existing directories."""
        entry_path = self.path_edit.text().strip()
        if not entry_path or not os.path.isdir(entry_path):
            QMessageBox.warning(self, "Input Error", "Please select a valid entry path first.")
            return

        versions: List[str] = []
        for root, dirs, _ in os.walk(entry_path):
            for folder in dirs:
                if re.match(VERSION_PATTERN, folder):
                    versions.append(folder)
            break  # Only check first level

        if versions:
            # Sort versions and get the latest
            versions.sort(key=lambda v: [int(x) for x in v.split('.')])
            latest_version = versions[-1]
            self.curr_version_edit.setText(latest_version)
            self.log(f"Auto-detected version: {latest_version} (found {len(versions)} version(s))")
        else:
            QMessageBox.information(self, "No Versions Found", "No version directories found in the selected path.")

    def validate_version_inputs(self) -> Optional[Tuple[str, str, str, int]]:
        """Validate and return version upgrade inputs."""
        entry_path = self.path_edit.text().strip()
        old_version = self.curr_version_edit.text().strip()
        new_version = self.new_version_edit.text().strip()
        depth = self.depth_spinbox.value()

        if not entry_path or not old_version or not new_version:
            QMessageBox.warning(self, "Input Error", "All fields must be filled!")
            return None

        if not os.path.isdir(entry_path):
            QMessageBox.warning(self, "Path Error", "The entry path does not exist or is not a directory.")
            return None

        if not re.match(VERSION_PATTERN, old_version):
            QMessageBox.warning(self, "Version Error", f"Current version '{old_version}' must be in format X.X.X or X.X.X.X")
            return None

        if not re.match(VERSION_PATTERN, new_version):
            QMessageBox.warning(self, "Version Error", f"New version '{new_version}' must be in format X.X.X or X.X.X.X")
            return None

        if old_version == new_version:
            QMessageBox.warning(self, "Version Error", "Current and new versions must be different.")
            return None

        return entry_path, old_version, new_version, depth

    def preview_upgrade(self) -> None:
        """Preview changes without applying them."""
        self.dry_run_checkbox.setChecked(True)
        self.start_upgrade()

    def start_upgrade(self) -> None:
        """Validate inputs and start the upgrade process."""
        result = self.validate_version_inputs()
        if not result:
            return

        entry_path, old_version, new_version, depth = result
        is_dry_run = self.dry_run_checkbox.isChecked()
        create_backup = self.backup_checkbox.isChecked()

        # Reset counters
        self.files_modified = 0
        self.files_scanned = 0
        self.preview_changes = []
        self.log_area.clear()

        # Extract the last word from the entry path
        last_word = os.path.basename(os.path.normpath(entry_path))

        mode = "DRY RUN" if is_dry_run else "UPGRADE"
        self.log(f"Starting {mode}: {old_version} -> {new_version}")
        self.log(f"Entry path: {entry_path}")
        self.log(f"Filter keyword: {last_word}")

        # Start folder upgrade process
        self.upgrade_folders(entry_path, old_version, new_version, depth, last_word, is_dry_run, create_backup)

    def upgrade_folders(self, path: str, old_version: str, new_version: str, max_depth: int, 
                       last_word: str, is_dry_run: bool, create_backup: bool) -> None:
        """
        Traverse directories to locate versioned folders and copy them to the new version.
        """
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress

        folders_processed = 0
        
        for root, dirs, _ in os.walk(path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            current_depth = root[len(path):].count(os.sep)

            if max_depth != 0 and current_depth >= max_depth:
                continue

            for folder in dirs:
                if re.match(VERSION_PATTERN, folder) and folder == old_version:
                    folder_path = os.path.join(root, folder)
                    new_folder_path = os.path.join(root, new_version)

                    target_exists_empty = False
                    if os.path.exists(new_folder_path):
                        if self.is_directory_empty(new_folder_path):
                            target_exists_empty = True
                            # Proceed with copying into the empty directory
                        else:
                            self.log(f"Skipping: {new_folder_path} (already exists and not empty)", "warning")
                            continue

                    if not is_dry_run:
                        if target_exists_empty:
                            self.log(f"Copying into existing empty folder: {folder_path} -> {new_folder_path}")
                        else:
                            self.log(f"Copying: {folder_path} -> {new_folder_path}")
                        self.copy_directory(folder_path, new_folder_path)
                        self.upgrade_specific_subdirectories(new_folder_path, old_version, new_version, 
                                                            last_word, is_dry_run, create_backup)
                    else:
                        if target_exists_empty:
                            self.log(f"[DRY RUN] Would copy into existing empty folder: {folder_path} -> {new_folder_path}")
                        else:
                            self.log(f"[DRY RUN] Would copy: {folder_path} -> {new_folder_path}")
                        # Scan for what would be changed
                        self.scan_for_changes(folder_path, old_version, new_version, last_word)
                    
                    folders_processed += 1

        self.progress_bar.setVisible(False)

        # Summary
        if is_dry_run:
            self.log(f"\n=== DRY RUN COMPLETE ===")
            self.log(f"Folders that would be copied: {folders_processed}")
            self.log(f"Files that would be modified: {self.files_modified}")
            if self.preview_changes:
                self.log(f"\nPreview of changes (first 10):")
                for file_path, old, new in self.preview_changes[:10]:
                    self.log(f"  {os.path.basename(file_path)}: '{old}' -> '{new}'")
        else:
            self.log(f"\n=== UPGRADE COMPLETE ===")
            self.log(f"Folders processed: {folders_processed}")
            self.log(f"Files modified: {self.files_modified}")
            self.log(f"Files scanned: {self.files_scanned}")
            QMessageBox.information(self, "Success", 
                f"Upgrade completed!\n\nFolders processed: {folders_processed}\nFiles modified: {self.files_modified}")

    def scan_for_changes(self, folder_path: str, old_version: str, new_version: str, last_word: str) -> None:
        """Scan for changes without applying them (for dry run preview)."""
        subdirs_to_process = [
            os.path.join(folder_path, 'src'),
            os.path.join(folder_path, 'test')
        ]

        for subdir in subdirs_to_process:
            if os.path.exists(subdir):
                for root, dirs, files in os.walk(subdir):
                    dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
                    for file in files:
                        if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                            file_path = os.path.join(root, file)
                            self.check_file_for_changes(file_path, old_version, new_version, last_word)

    def check_file_for_changes(self, file_path: str, old_version: str, new_version: str, last_word: str) -> None:
        """Check a file for potential changes."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
            except Exception as e:
                self.log(f"Cannot read file {file_path}: {e}", "warning")
                return

        escaped_version = re.escape(old_version)
        pattern = re.compile(rf'({re.escape(EAMD_PATH_PREFIX)}[^"\']*?/{re.escape(last_word)}/[^"\']*?)({escaped_version})')
        
        matches = pattern.findall(content)
        if matches:
            self.files_modified += 1
            for match in matches[:3]:  # Store first 3 matches per file
                self.preview_changes.append((file_path, match[1], new_version))

    def copy_directory(self, src: str, dst: str) -> None:
        """Copy a directory structure from src to dst."""
        if not os.path.exists(dst):
            os.makedirs(dst)
        
        for root, dirs, files in os.walk(src):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            relative_path = os.path.relpath(root, src)
            dest_dir = os.path.join(dst, relative_path)

            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)

            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                shutil.copy2(src_file, dest_file)

    def upgrade_specific_subdirectories(self, folder_path: str, old_version: str, new_version: str, 
                                        last_word: str, is_dry_run: bool, create_backup: bool) -> None:
        """Process specific subdirectories after copying the new version folder."""
        subdirs_to_process = [
            os.path.join(folder_path, 'src'),
            os.path.join(folder_path, 'test')
        ]

        for subdir in subdirs_to_process:
            if os.path.exists(subdir):
                self.update_dir_files(subdir, old_version, new_version, last_word, is_dry_run, create_backup)

    def update_dir_files(self, dir_path: str, old_version: str, new_version: str, 
                        last_word: str, is_dry_run: bool, create_backup: bool) -> None:
        """Traverse a directory to find and update files."""
        for root, dirs, files in os.walk(dir_path):
            # Filter out excluded directories
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    self.files_scanned += 1
                    self.update_file(file_path, old_version, new_version, last_word, is_dry_run, create_backup)

    def create_file_backup(self, file_path: str) -> Optional[str]:
        """Create a backup of a file before modification."""
        backup_path = f"{file_path}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            self.log(f"Failed to create backup for {file_path}: {e}", "error")
            return None

    def update_file(self, file_path: str, old_version: str, new_version: str, 
                   last_word: str, is_dry_run: bool, create_backup: bool) -> None:
        """Read a file and replace version numbers."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()
                self.log(f"Using latin-1 encoding for: {file_path}", "warning")
            except Exception as e:
                self.log(f"Cannot read file {file_path}: {e}", "error")
                return

        updated_content = self.replace_version_in_content(content, old_version, new_version, last_word)

        if updated_content != content:
            self.files_modified += 1
            if not is_dry_run:
                if create_backup:
                    self.create_file_backup(file_path)
                
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(updated_content)
                self.log(f"Updated: {os.path.basename(file_path)}")

    def replace_version_in_content(self, content: str, old_version: str, new_version: str, last_word: str) -> str:
        """
        Replace occurrences of `/EAMD.ucp` followed by the old version number,
        but only if the string contains the last word from the entry path.

        Uses proper regex escaping for version numbers.
        """
        # Escape special regex characters in version (especially dots)
        escaped_old_version = re.escape(old_version)
        escaped_last_word = re.escape(last_word)
        escaped_prefix = re.escape(EAMD_PATH_PREFIX)
        
        # Pattern matches EAMD.ucp paths containing the last_word and the old version
        # Uses [^"'\s]* instead of .*? to avoid matching across quotes/lines
        pattern = re.compile(
            rf'({escaped_prefix}[^"\'<>\s]*?/{escaped_last_word}/[^"\'<>\s]*?)({escaped_old_version})'
        )
        
        updated_content = pattern.sub(rf'\g<1>{new_version}', content)
        return updated_content

    def validate_component_inputs(self) -> Optional[Tuple[str, str, str]]:
        """Validate and return component replacement inputs."""
        component_dir = self.component_dir_edit.text().strip()
        component_name = self.component_edit.text().strip()
        new_path = self.new_path_edit.text().strip()

        if not component_dir or not component_name or not new_path:
            QMessageBox.warning(self, "Input Error", "All fields must be filled for component replacement!")
            return None

        if not os.path.isdir(component_dir):
            QMessageBox.warning(self, "Path Error", "The component directory does not exist.")
            return None

        # Validate new_path format
        if not new_path.startswith(EAMD_PATH_PREFIX):
            QMessageBox.warning(self, "Path Error", f"Replacement path should start with '{EAMD_PATH_PREFIX}'")
            return None

        if not new_path.endswith(COMPONENT_XML_SUFFIX):
            QMessageBox.warning(self, "Path Error", f"Replacement path should end with '{COMPONENT_XML_SUFFIX}'")
            return None

        return component_dir, component_name, new_path

    def replace_component_paths(self) -> None:
        """Replace all occurrences of the component's `/EAMD.ucp/` path string."""
        result = self.validate_component_inputs()
        if not result:
            return

        component_dir, component_name, new_path = result
        is_dry_run = self.component_dry_run_checkbox.isChecked()
        create_backup = self.component_backup_checkbox.isChecked()

        # Reset counters
        self.files_modified = 0
        self.files_scanned = 0
        self.log_area.clear()

        # Convert component name to PascalCase
        component_name = ''.join(word.capitalize() for word in re.split(r'[\s_-]', component_name))

        mode = "DRY RUN" if is_dry_run else "REPLACE"
        self.log(f"Starting {mode} for component: {component_name}")
        self.log(f"Directory: {component_dir}")
        self.log(f"New path: {new_path}")

        self.replace_paths_in_dir(component_dir, component_name, new_path, is_dry_run, create_backup)

    def replace_paths_in_dir(self, dir_path: str, component_name: str, new_path: str, 
                            is_dry_run: bool, create_backup: bool) -> None:
        """Replace component path strings in the specified directory."""
        # Escape special regex characters
        escaped_component = re.escape(component_name)
        escaped_prefix = re.escape(EAMD_PATH_PREFIX)
        escaped_suffix = re.escape(COMPONENT_XML_SUFFIX)
        
        old_path_pattern = re.compile(
            rf'{escaped_prefix}[^"\'<>\s]*?/{escaped_component}{escaped_suffix}'
        )

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)

        for root, dirs, files in os.walk(dir_path):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                if any(file.endswith(ext) for ext in FILE_EXTENSIONS):
                    file_path = os.path.join(root, file)
                    self.files_scanned += 1
                    
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    except UnicodeDecodeError:
                        try:
                            with open(file_path, 'r', encoding='latin-1') as f:
                                content = f.read()
                        except Exception as e:
                            self.log(f"Cannot read file {file_path}: {e}", "error")
                            continue

                    if old_path_pattern.search(content):
                        self.files_modified += 1
                        
                        if not is_dry_run:
                            if create_backup:
                                self.create_file_backup(file_path)
                            
                            updated_content = old_path_pattern.sub(new_path, content)
                            with open(file_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)
                            self.log(f"Updated: {os.path.basename(file_path)}")
                        else:
                            self.log(f"[DRY RUN] Would update: {os.path.basename(file_path)}")

        self.progress_bar.setVisible(False)

        # Summary
        if is_dry_run:
            self.log(f"\n=== DRY RUN COMPLETE ===")
            self.log(f"Files that would be modified: {self.files_modified}")
        else:
            self.log(f"\n=== REPLACEMENT COMPLETE ===")
            self.log(f"Files modified: {self.files_modified}")
            self.log(f"Files scanned: {self.files_scanned}")
            QMessageBox.information(self, "Success", 
                f"Component paths replaced!\n\nFiles modified: {self.files_modified}")

    def close_app(self) -> None:
        """Close the application."""
        self.save_window_state()
        self.close()


if __name__ == "__main__":
    """Entry point of the application."""
    app = QApplication(sys.argv)
    window = VersionUpgradeApp()
    window.show()
    sys.exit(app.exec())
