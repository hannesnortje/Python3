import sys
import os
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QComboBox,
    QTextEdit,
    QWidget,
    QMessageBox,
)
from PySide6.QtCore import Qt, QProcess

# Folder containing test scripts
TESTS_FOLDER = "tests"


# Function to dynamically load test scripts
def load_tests(folder):
    tests = {}
    for filename in os.listdir(folder):
        if filename.endswith(".py"):
            test_name = filename[:-3]  # Remove .py extension
            tests[test_name] = os.path.join(folder, filename)
    return tests


# PySide6 MainWindow Class
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Enhanced Test Runner")
        self.setGeometry(100, 100, 600, 400)

        self.process = None

        # Main Layout
        main_layout = QVBoxLayout()

        # Browser Selection
        browser_layout = QHBoxLayout()
        browser_label = QLabel("Select Browser:")
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Chrome", "Firefox", "Edge", "Safari"])
        browser_layout.addWidget(browser_label)
        browser_layout.addWidget(self.browser_combo)

        # Mode Selection
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Select Mode:")
        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Desktop", "Mobile"])
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.mode_combo)

        # Test Selection
        test_layout = QHBoxLayout()
        test_label = QLabel("Select Test:")
        self.test_combo = QComboBox()
        self.tests = load_tests(TESTS_FOLDER)  # Load tests dynamically
        self.test_combo.addItems(self.tests.keys())
        test_layout.addWidget(test_label)
        test_layout.addWidget(self.test_combo)

        # Action Buttons
        button_layout = QHBoxLayout()
        self.run_button = QPushButton("Run Test")
        self.run_button.clicked.connect(self.run_selected_test)

        self.stop_button = QPushButton("Stop Test")
        self.stop_button.clicked.connect(self.stop_test)
        self.stop_button.setEnabled(False)

        self.quit_button = QPushButton("Quit")
        self.quit_button.clicked.connect(self.close)

        button_layout.addWidget(self.run_button)
        button_layout.addWidget(self.stop_button)
        button_layout.addWidget(self.quit_button)

        # Console Output
        self.console_output = QTextEdit()
        self.console_output.setReadOnly(True)

        # Add Widgets to Main Layout
        main_layout.addLayout(browser_layout)
        main_layout.addLayout(mode_layout)
        main_layout.addLayout(test_layout)
        main_layout.addLayout(button_layout)
        main_layout.addWidget(QLabel("Console Output:"))
        main_layout.addWidget(self.console_output)

        # Set Main Layout
        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

    def append_log(self, message):
        self.console_output.append(message)
        self.console_output.ensureCursorVisible()

    def run_selected_test(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            QMessageBox.warning(self, "Warning", "A test is already running.")
            return

        # Get selected browser, mode, and test
        browser = self.browser_combo.currentText()
        mode = self.mode_combo.currentText()
        selected_test = self.test_combo.currentText()

        if selected_test not in self.tests:
            QMessageBox.critical(self, "Error", "Selected test not found.")
            return

        test_path = self.tests[selected_test]

        # Initialize QProcess
        self.process = QProcess(self)
        self.process.setProgram(sys.executable)
        self.process.setArguments([test_path, browser, mode])

        # Connect signals
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.test_finished)

        # Enable/Disable Buttons
        self.run_button.setEnabled(False)
        self.stop_button.setEnabled(True)

        # Start the process
        self.append_log(f"Starting test '{test_path}' on {browser} in {mode} mode...")
        self.process.start()

    def read_stdout(self):
        output = self.process.readAllStandardOutput().data().decode()
        self.append_log(output.strip())

    def read_stderr(self):
        error = self.process.readAllStandardError().data().decode()
        self.append_log(f"Error: {error.strip()}")

    def test_finished(self):
        self.append_log("Test completed.")
        self.run_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def stop_test(self):
        if self.process and self.process.state() != QProcess.NotRunning:
            self.process.kill()
            self.append_log("Test stopped.")
            self.run_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    def closeEvent(self, event):
        """Ensure cleanup of running test on UI close."""
        self.stop_test()
        event.accept()


# Main Function to Run the Application
def main():
    # Ensure the tests folder exists
    if not os.path.exists(TESTS_FOLDER):
        os.makedirs(TESTS_FOLDER)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
