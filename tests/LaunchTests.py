import sys
import os
import threading
import importlib.util
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Signal, QObject
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions

class BrowserSelectionDialog(QDialog):
    selection_made = Signal(str, str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Test Runner")
        self.setFixedWidth(500)

        layout = QVBoxLayout()

        # Browser selection dropdown
        layout.addWidget(QLabel("Choose Browser:"))
        self.browser_dropdown = QComboBox()
        self.browser_dropdown.addItems(["Chrome", "Firefox", "Edge", "Safari"])
        layout.addWidget(self.browser_dropdown)

        # Server selection dropdown
        layout.addWidget(QLabel("Choose Server:"))
        self.server_dropdown = QComboBox()
        self.server_dropdown.addItems(["Online", "Localhost"])
        layout.addWidget(self.server_dropdown)

        # Test selection dropdown
        layout.addWidget(QLabel("Choose Test:"))
        self.test_dropdown = QComboBox()
        self.load_tests()
        layout.addWidget(self.test_dropdown)

        # Run Test button
        self.run_button = QPushButton("Run Test")
        self.run_button.clicked.connect(self.make_selection)
        layout.addWidget(self.run_button)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_application)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def load_tests(self):
        """Load test scripts from the `tests` folder."""
        tests_folder = "tests"
        if not os.path.exists(tests_folder):
            os.makedirs(tests_folder)  # Create the folder if it doesn't exist

        test_files = [f for f in os.listdir(tests_folder) if f.endswith(".py")]
        self.test_dropdown.addItems(test_files)

    def make_selection(self):
        browser = self.browser_dropdown.currentText()
        server = self.server_dropdown.currentText()
        test_file = self.test_dropdown.currentText()
        self.selection_made.emit(browser, server, test_file)

    def close_application(self):
        QApplication.instance().quit()

class SeleniumWorker(QObject):
    def __init__(self, browser, server, test_file):
        super().__init__()
        self.browser = browser
        self.server = server
        self.test_file = test_file

    def run(self):
        try:
            driver = self.get_driver(self.browser)

            # Determine the URL based on the server selection
            url = (
                "https://demo.metatrom.net/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html"
                if self.server.lower() == "online"
                else "https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html"
            )
            driver.get(url)
            print(f"Browser: {self.browser}, Server: {self.server}, URL: {url}")

            # Dynamically import and run the selected test
            self.run_test_script(driver)

            driver.quit()

        except Exception as e:
            print(f"An error occurred: {e}")

    def run_test_script(self, driver):
        """Run the selected test script."""
        test_path = os.path.join("tests", self.test_file)
        spec = importlib.util.spec_from_file_location("test_module", test_path)
        test_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_module)

        if hasattr(test_module, "run_test"):
            print(f"Running test: {self.test_file}")
            test_module.run_test(driver)
        else:
            print(f"The selected test file {self.test_file} does not have a 'run_test(driver)' function.")

    def get_driver(self, browser):
        if browser.lower() == "chrome":
            chrome_options = webdriver.ChromeOptions()
            chrome_options.add_argument("--ignore-certificate-errors")
            chrome_options.add_argument("--allow-insecure-localhost")
            service = ChromeService(executable_path='/home/hannesn/Downloads/chromedriver-linux64/chromedriver')
            return webdriver.Chrome(service=service, options=chrome_options)
        elif browser.lower() == "firefox":
            firefox_options = webdriver.FirefoxOptions()
            firefox_options.add_argument("--ignore-certificate-errors")
            firefox_options.add_argument("--no-remote")
            firefox_options.add_argument("--new-instance")
            service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
            return webdriver.Firefox(service=service, options=firefox_options)
        elif browser.lower() == "edge":
            edge_options = EdgeOptions()
            edge_options.add_argument("--ignore-certificate-errors")
            edge_options.add_argument("--allow-insecure-localhost")
            service = EdgeService(executable_path='/home/hannesn/Downloads/edgedriver_linux64/msedgedriver')
            return webdriver.Edge(service=service, options=edge_options)
        elif browser.lower() == "safari":
            return webdriver.Safari()
        else:
            raise ValueError(f"Unsupported browser: {browser}")

def start_selenium(browser, server, test_file):
    selenium_worker = SeleniumWorker(browser, server, test_file)
    selenium_thread = threading.Thread(target=selenium_worker.run)
    selenium_thread.start()

if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = BrowserSelectionDialog()
    dialog.selection_made.connect(start_selenium)
    dialog.show()

    sys.exit(app.exec())
