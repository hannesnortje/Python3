import sys
import os
import time
from PySide6.QtWidgets import QApplication, QDialog, QVBoxLayout, QLabel, QComboBox, QPushButton
from PySide6.QtCore import Signal, QObject
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading


class BrowserSelectionDialog(QDialog):
    selection_made = Signal(str, str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle(os.path.basename(sys.argv[0]))
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

        # Run Test button
        self.run_button = QPushButton("Run Test")
        self.run_button.clicked.connect(self.make_selection)
        layout.addWidget(self.run_button)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.close_application)
        layout.addWidget(self.close_button)

        self.setLayout(layout)

    def make_selection(self):
        browser = self.browser_dropdown.currentText()
        server = self.server_dropdown.currentText()
        self.selection_made.emit(browser, server)

    def close_application(self):
        QApplication.instance().quit()


class SeleniumWorker(QObject):
    def __init__(self, browser, server, test_function):
        super().__init__()
        self.browser = browser
        self.server = server
        self.test_function = test_function

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

            # Run the provided test function
            self.test_function(driver)

            driver.quit()

        except Exception as e:
            print(f"An error occurred: {e}")

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


def run_test(driver):
    """
    Test Logic:
    """
    # Relative path to the file
    relative_path = "tests/download.jpeg"

    # Convert relative path to absolute path
    image_path = os.path.abspath(relative_path)

    # Verify the file exists
    if not os.path.exists(image_path):
        raise FileNotFoundError(f"File not found: {image_path}")
    print(f"Using image path: {image_path}")

    # Wait for iframes to load
    WebDriverWait(driver, 90).until(lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0)

    # Define iframe conditions
    iframe_conditions = {
        "iframe[src*='/customer']": [
            "DefaultTableRow_TableRowDefaultView_10",
            "DefaultTableRow_TableRowDefaultView_11",
            "DefaultTableRow_TableRowDefaultView_12",
        ],
        "iframe[src*='/tablet-customer']": [
            "DefaultTableRow_TableRowDefaultView_10",
        ],
        "iframe[src*='/laptop-customer']": [
            "DefaultTableRow_TableRowDefaultView_10",
            "DefaultTableRow_TableRowDefaultView_11",
            "DefaultTableRow_TableRowDefaultView_12",
        ],
    }

    # Add an initial delay before starting the reload loop
    print("Initial wait before checking conditions...")
    time.sleep(20)

    # Function to check elements in an iframe
    def are_elements_present(driver, iframe_selector, element_ids):
        try:
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, iframe_selector))
            )
            driver.switch_to.frame(iframe)
            for element_id in element_ids:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.ID, element_id))
                )
            driver.switch_to.default_content()
            return True
        except:
            driver.switch_to.default_content()
            return False

    # Function to perform a factory reset
    def factory_reset(driver):
        try:
            print("Attempting factory reset...")
            iframe = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/customer']"))
            )
            driver.switch_to.frame(iframe)

            # Locate and click the menu toggle element
            toggle_menu_element = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.user-details.profile[onclick*='toggleMenu()']"))
            )
            toggle_menu_element.click()
            print("Menu toggled successfully.")

            # Locate and click the Factory Reset link
            factory_reset_link = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, "//a[contains(@onclick, 'factoryReset()')]"))
            )
            factory_reset_link.click()
            print("Factory reset executed successfully.")

            driver.switch_to.default_content()
        except Exception as e:
            driver.switch_to.default_content()
            print(f"Factory reset failed: {e}")

    # Reload loop until conditions are met
    reload_count = 0
    consecutive_failures = 0
    while True:
        all_conditions_met = True
        for iframe_selector, element_ids in iframe_conditions.items():
            if not are_elements_present(driver, iframe_selector, element_ids):
                all_conditions_met = False
                break

        if all_conditions_met:
            print("All conditions met. Proceeding with the test.")
            break

        reload_count += 1
        consecutive_failures += 1
        print(f"Conditions not met. Reloading the page (Attempt #{reload_count}).")

        # Perform factory reset if conditions fail three times consecutively
        if consecutive_failures >= 3:
            factory_reset(driver)
            consecutive_failures = 0  # Reset the failure count after factory reset

        driver.get(driver.current_url)
        time.sleep(20)

    print(f"Page reloads completed: {reload_count} time(s)")

    # Local storage data
    #local_storage_data = driver.execute_script("return window.localStorage;")
    #print("Local Storage Data:", local_storage_data)

    # Wait for iframes to load
    WebDriverWait(driver, 90).until(lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0)

    # Switch to the iframe containing the iphone element
    iphone_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/customer']"))
    )
    driver.switch_to.frame(iphone_iframe)

    # Locate the file input element and upload the image
    file_input = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "myfile"))
    )
    file_input.send_keys(image_path)
    print(f"Uploaded image: {image_path}")

    # Wait for the uploaded image to appear in the draggable list
    uploaded_image = WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_13"))
    )
    print("Uploaded image is now draggable.")

    # Trigger dragstart on the uploaded image
    on_drag_start_script = """
    const element = arguments[0];
    const dragStartEvent = new DragEvent('dragstart', {
        bubbles: true,
        cancelable: true,
        dataTransfer: new DataTransfer()
    });
    element.dispatchEvent(dragStartEvent);
    return dragStartEvent.dataTransfer.types.reduce((data, type) => {
        data[type] = dragStartEvent.dataTransfer.getData(type);
        return data;
    }, {});
    """
    drag_data = driver.execute_script(on_drag_start_script, uploaded_image)
    print("Drag data extracted for the uploaded image.")

    # Switch to the tablet iframe
    driver.switch_to.default_content()
    droppable_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/tablet-customer']"))
    )
    driver.switch_to.frame(droppable_iframe)

    # Locate the droppable element
    droppable = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH, "//*[@webean-role='DefaultTableRow_TableRowDefaultView_10:container']"))
    )

    # Perform the drop operation in the target iframe
    drop_script = """
    const droppableElement = arguments[0];
    const dragData = arguments[1];
    const dropEvent = new DragEvent('drop', {
        bubbles: true,
        cancelable: true,
        dataTransfer: new DataTransfer()
    });

    Object.keys(dragData).forEach(type => {
        dropEvent.dataTransfer.setData(type, dragData[type]);
    });

    droppableElement.dispatchEvent(dropEvent);
    """
    driver.execute_script(drop_script, droppable, drag_data)
    print("Drop event executed with payload.")

    # Locate the <article> element by its ID
    article_element = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located(
            (By.ID, "DefaultTableRow_TableRowDefaultView_11")
        )
    )

    # Locate the <aside> element inside the <article> element
    aside_element = article_element.find_element(By.CSS_SELECTOR, "aside.item-settings-aside")

    # Click the <aside> element
    aside_element.click()
    print("Clicked the tablet specific <aside> element successfully.")

    # Switch back to the main document
    driver.switch_to.default_content()

    # Switch to the iframe containing the draggable element
    iphone_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/customer']"))
    )
    driver.switch_to.frame(iphone_iframe)

    # Locate the draggable element
    iphone_photo = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_13"))
    )

    # Locate the <aside> element inside the <article> element
    iphone_aside_element = iphone_photo.find_element(By.CSS_SELECTOR, "aside.item-settings-aside")

    # Click the <aside> element
    iphone_aside_element.click()
    print("Clicked the iphone specific <aside> element successfully.")

    # Switch back to the main document
    driver.switch_to.default_content()

    # Switch to the iframe containing the draggable element
    laptop_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/laptop-customer']"))
    )
    driver.switch_to.frame(laptop_iframe)

    # Locate the draggable element
    laptop_photo = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_13"))
    )

    # Locate the <aside> element inside the <article> element
    laptop_aside_element = laptop_photo.find_element(By.CSS_SELECTOR, "aside.item-settings-aside")

    # Click the <aside> element
    laptop_aside_element.click()
    print("Clicked the laptop specific <aside> element successfully.")

    # Ensure the directory exists
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    # Save the screenshot
    screenshot_path = os.path.join(screenshot_dir, "expand_verification.png")
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved at: {screenshot_path}")

    # Pause for observation
    input("Press Enter to close the browser after observing the drag-and-drop...")

    driver.quit()

def start_selenium(browser, server):
    selenium_worker = SeleniumWorker(browser, server, run_test)
    selenium_thread = threading.Thread(target=selenium_worker.run)
    selenium_thread.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    dialog = BrowserSelectionDialog()
    dialog.selection_made.connect(start_selenium)
    dialog.show()

    sys.exit(app.exec())
