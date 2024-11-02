from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

# Path to your ChromeDriver
chrome_driver_path = '/home/hannesn/Downloads/chromedriver-linux64/chromedriver'

# Set up the ChromeDriver using Service
service = Service(executable_path=chrome_driver_path)

# Initialize the driver
driver = webdriver.Chrome(service=service)

# Open the new local URL
driver.get("http://localhost:8080/EAMD.ucp/Components/com/metatrom/EAM/layer5/OnceIframeDeviceEmulator/3.1.0/test/html/index.html")

# Start measuring time for the DemoTable load
start_time = time.time()

# Wait until the iframe is present and switch to it
try:
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/EAMD.ucp/Components/com/metatrom/EAM/layer5/OnceIframeDeviceEmulator/3.1.0/src/html/OnceIframeDeviceEmulator.2.4.2.html#!/customer']"))
    )
    driver.switch_to.frame(iframe)

    # Now search for the DemoTable inside the iframe
    demo_table = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "demo-table"))
    )
    
    # End measuring time after the DemoTable is found
    end_time = time.time()
    load_time = end_time - start_time
    print(f"DemoTable Load Time: {load_time} seconds")

    # Measure the load time for each "web4-item" element
    web4_items = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located((By.CLASS_NAME, "web4-item"))
    )

    for idx, item in enumerate(web4_items):
        # Start the time for each web4-item element
        item_start_time = time.time()
        WebDriverWait(driver, 10).until(
            EC.visibility_of(item)  # Wait until the element is visible
        )
        item_end_time = time.time()
        item_load_time = item_end_time - item_start_time
        print(f"Web4-item {idx+1} Load Time: {item_load_time} seconds")

except Exception as e:
    print(f"Error: {e}")

# Close the browser after testing
driver.quit()
