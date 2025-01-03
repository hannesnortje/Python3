from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time

def get_driver(browser):
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
        service = EdgeService(executable_path='/home/hannesn/Downloads/edgedriver_linux64/msedgedriver')
        return webdriver.Edge(service=service)
    elif browser.lower() == "safari":
        return webdriver.Safari()  # SafariDriver must be enabled on macOS
    else:
        raise ValueError(f"Unsupported browser: {browser}")

# Initialize driver for the desired browser
browser = "firefox"
driver = get_driver(browser)

# Open the URL
driver.get("https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html")

try:
    # First reload
    driver.refresh()
    print("Page reloaded the first time.")
    time.sleep(10)  # Wait for 10 seconds to allow local storage and iframes to sync

    # Second reload
    driver.refresh()
    print("Page reloaded the second time.")
    time.sleep(10)  # Wait for 10 seconds to allow local storage and iframes to sync

    local_storage_data = driver.execute_script("return window.localStorage;")
    print("Local Storage Data:", local_storage_data)

    # Wait for iframes to load
    WebDriverWait(driver, 90).until(lambda d: len(d.find_elements(By.TAG_NAME, "iframe")) > 0)

    # Switch to the iframe containing the draggable element
    draggable_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/customer']"))
    )
    driver.switch_to.frame(draggable_iframe)

    # Locate the draggable element
    draggable = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_11"))
    )

    # Trigger onDragStart and capture the drag data
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
    drag_data = driver.execute_script(on_drag_start_script, draggable)
    print("Extracted Drag Data:", drag_data)

    # Switch back to the main document
    driver.switch_to.default_content()

    # Switch to the iframe containing the droppable element
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
    print("Clicked the specific <aside> element successfully.")

    # Ensure the directory exists
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    # Save the screenshot
    screenshot_path = os.path.join(screenshot_dir, "expand_verification.png")
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved at: {screenshot_path}")

    # Pause for observation
    input("Press Enter to close the browser after observing the drag-and-drop...")

except Exception as e:
    print(f"An error occurred: {e}")
    driver.save_screenshot("error_screenshot.png")  # Take a screenshot for debugging

finally:
    # Close the browser
    driver.quit()
