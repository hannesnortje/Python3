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
browser = "chrome"
driver = get_driver(browser)

# # Path to your ChromeDriver
# chrome_driver_path = '/home/hannesn/Downloads/chromedriver-linux64/chromedriver'

# # Set up Chrome options to ignore certificate errors
# chrome_options = webdriver.ChromeOptions()
# chrome_options.add_argument("--ignore-certificate-errors")
# chrome_options.add_argument("--allow-insecure-localhost")

# # Set up the ChromeDriver using Service
# service = Service(executable_path=chrome_driver_path)

# # Initialize the driver with options
# driver = webdriver.Chrome(service=service, options=chrome_options)

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
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_10"))
    )

    # Locate and extract the plays count before playing
    plays_element = draggable.find_element(By.CSS_SELECTOR, "div.item-info")
    initial_plays_text = plays_element.text
    initial_plays_count = int(initial_plays_text.split()[0])  # Extract the numeric part
    print(f"Initial plays count: {initial_plays_count}")

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
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/media-player']"))
    )
    driver.switch_to.frame(droppable_iframe)

    # Locate the droppable element
    droppable = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH, "//*[@view-id='DefaultMediaPlayer_MediaPlayerDefaultView_10_drag-drop-box']"))
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

    # Wait for the "Sign" button to be present
    sign_button = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "button.btn-sign[aria-label='Sign Terms and Conditions']"))
    )

    # Click the "Sign" button
    sign_button.click()
    print("Sign button clicked.")

     # Ensure the directory exists
    screenshot_dir = "screenshots"
    os.makedirs(screenshot_dir, exist_ok=True)

    # Save the screenshot
    screenshot_path = os.path.join(screenshot_dir, "song_drop_verification.png")
    driver.save_screenshot(screenshot_path)
    print(f"Screenshot saved at: {screenshot_path}")

    play_button = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "button.btn[view-id='DefaultMediaPlayer_MediaPlayerDefaultView_10_playPauseBtn']")
        )
    )
    play_button.click()
    print("Play button clicked.")

    # Confirm the song is playing by checking timestamp progression
    current_time_element = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "span[view-id='DefaultMediaPlayer_MediaPlayerDefaultView_10_currentTime']")
        )
    )

    # Record the initial timestamp
    initial_time = current_time_element.text
    print(f"Initial timestamp: {initial_time}")

    # Wait for the timestamp to update
    WebDriverWait(driver, 90).until(
        lambda d: current_time_element.text != initial_time
    )
    updated_time = current_time_element.text
    print(f"Timestamp updated: {updated_time}")

    # Alternatively, confirm the progress bar changes
    progress_bar_inner = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located(
            (By.CSS_SELECTOR, "div.progress-bar-inner")
        )
    )

    # Record the initial width of the progress bar
    initial_width = driver.execute_script("return arguments[0].style.width;", progress_bar_inner)
    print(f"Initial progress bar width: {initial_width}")

    # Wait for the progress bar width to change
    WebDriverWait(driver, 90).until(
        lambda d: driver.execute_script("return arguments[0].style.width;", progress_bar_inner) != initial_width
    )
    updated_width = driver.execute_script("return arguments[0].style.width;", progress_bar_inner)
    print(f"Progress bar width updated: {updated_width}")

    play_button.click()
    print("Play button clicked again.")

    # Switch back to the main document
    driver.switch_to.default_content()

    # Switch to the iphone iframe
    draggable_iframe = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/customer']"))
    )
    driver.switch_to.frame(draggable_iframe)

    # Locate the draggable element
    draggable = WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.ID, "DefaultTableRow_TableRowDefaultView_10"))
    )

   # Locate and extract the plays count after playing
    plays_element = draggable.find_element(By.CSS_SELECTOR, "div.item-info")
    new_plays_text = plays_element.text
    new_plays_count = int(new_plays_text.split()[0])  # Extract the numeric part

    # Assert that the plays count has increased
    if new_plays_count <= initial_plays_count:
        raise AssertionError(
            f"Plays count did not increment as expected. Initial: {initial_plays_count}, Current: {new_plays_count}"
        )
    
    print("Plays count incremented successfully.")

    print(f"Plays count updated from {initial_plays_count} to {new_plays_count}")

    # Pause for observation
    input("Press Enter to close the browser after observing the drag-and-drop...")

except Exception as e:
    print(f"An error occurred: {e}")
    driver.save_screenshot("error_screenshot.png")  # Take a screenshot for debugging

finally:
    # Close the browser
    driver.quit()
