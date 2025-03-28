import os
import time
import logging
import argparse
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Configuration
CHROME_DRIVER_PATH = "/home/hannesn/Downloads/chromedriver-linux64/chromedriver"
SOURCE_URL = "https://localhost:8443/EAMD.ucp/Components/com/canvas-gauges/CanvasGauges/2.1.7"
TARGET_URL = "https://localhost:8443/EAMD.ucp/Components/com/ceruleanCircle/EAM/5_ux/WODA/2.4.4/test/html/Woda.2.4.4.html"
TARGET_XPATH = '//*[@id="Panel_DefaultView_3"]/div/div[2]/div'
SOURCE_ITEMVIEW_XPATH = '//*[@id="JavaScriptObject_DefaultItemView_11-icon"]'
TARGET_ITEMVIEW_XPATH = '//*[@id="Panel_DefaultView_5"]/div/div[1]'

# Screenshot directory configuration
SCREENSHOT_DIR = "woda_gauge_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def create_chrome_driver(window_name, window_position, headless=False):
    """Create Chrome driver with appropriate settings"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    
    if headless:
        options.add_argument("--headless")
        options.add_argument("--window-size=1920,1080")
    else:
        options.add_argument(f"--window-position={window_position[0]},{window_position[1]}")
        if window_name == "SOURCE":
            options.add_argument("--window-size=800,900")
        else:  # TARGET window
            options.add_argument("--start-maximized")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

def simulate_drag_and_drop(source_driver, target_driver, source_element, target_element):
    """Simulate drag and drop using JavaScript events"""
    logging.info("Setting up drag and drop simulation...")
    
    drag_start_script = """
    const element = arguments[0];
    const dragStartEvent = new DragEvent('dragstart', {
        bubbles: true,
        cancelable: true,
        dataTransfer: new DataTransfer()
    });
    element.dispatchEvent(dragStartEvent);
    return {
        'text/plain': element.textContent,
        'text/uri-list': element.href,
        'text/html': element.outerHTML
    };
    """
    
    try:
        drag_data = source_driver.execute_script(drag_start_script, source_element)
        logging.info(f"Drag data captured: {drag_data}")
        
        drop_script = """
        const element = arguments[0];
        const dragData = arguments[1];
        const dropEvent = new DragEvent('drop', {
            bubbles: true,
            cancelable: true,
            dataTransfer: new DataTransfer()
        });
        
        Object.keys(dragData).forEach(type => {
            dropEvent.dataTransfer.setData(type, dragData[type]);
        });
        
        element.dispatchEvent(dropEvent);
        return true;
        """
        
        success = target_driver.execute_script(drop_script, target_element, drag_data)
        logging.info(f"Drop event completed: {success}")
        return success
        
    except Exception as e:
        logging.error(f"Error during drag and drop simulation: {e}")
        return False

def perform_itemview_move(target_driver):
    """Move the Canvas Gauge item view to the overview panel"""
    logging.info("Starting item view move operation...")
    
    try:
        # Wait for source element (item view) to be present
        source_element = WebDriverWait(target_driver, 10).until(
            EC.presence_of_element_located((By.XPATH, SOURCE_ITEMVIEW_XPATH))
        )
        logging.info("Found item view source element")
        
        # Wait for target drop zone
        target_element = WebDriverWait(target_driver, 10).until(
            EC.presence_of_element_located((By.XPATH, TARGET_ITEMVIEW_XPATH))
        )
        logging.info("Found target drop zone")
        
        # Take screenshot before move
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "4_before_itemview_move.png"))
        
        # Perform drag and drop within the same window
        drag_start_script = """
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
        
        drag_data = target_driver.execute_script(drag_start_script, source_element)
        logging.info("Item view drag started")
        
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
        return true;
        """
        
        success = target_driver.execute_script(drop_script, target_element, drag_data)
        
        if not success:
            raise Exception("Item view move failed")
        
        # Wait for move to complete and take screenshot
        time.sleep(5)
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "5_after_itemview_move.png"))
        logging.info("Item view moved successfully")
        
    except Exception as e:
        logging.error(f"Item view move failed: {e}")
        raise

def wait_and_click(driver, xpath, timeout=10, retries=3):
    """Helper function to wait for element and click with retries"""
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.element_to_be_clickable((By.XPATH, xpath))
            )
            element.click()
            return True
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)
    return False

def wait_and_send_keys(driver, xpath, keys, timeout=10, retries=3):
    """Helper function to wait for element and send keys with retries"""
    for attempt in range(retries):
        try:
            element = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
            element.clear()
            element.send_keys(keys)
            return True
        except Exception as e:
            if attempt == retries - 1:
                raise
            time.sleep(1)
    return False

def perform_gauge_interactions(target_driver):
    """Perform click operations and value changes on the gauge"""
    logging.info("Starting gauge interactions...")
    try:
        # Click on the gauge settings with retry
        settings_xpath = '//*[@id="JavaScriptObject_DefaultItemView_11"]/div/div[2]'
        wait_and_click(target_driver, settings_xpath)
        logging.info("Clicked gauge settings")
        time.sleep(2)
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "6_after_settings_click.png"))
        
        # Click show details with retry
        details_xpath = '//*[@id="ActionsPanel_DefaultView_9_showDetails"]'
        wait_and_click(target_driver, details_xpath)
        logging.info("Clicked show details")
        time.sleep(2)
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "7_after_show_details.png"))
        
        # Change input value with retry
        input_xpath = '//*[@id="DefaultPropertyEditor_DefaultView_57_inputBox"]'
        wait_and_send_keys(target_driver, input_xpath, "37")
        logging.info("Changed value to 37")
        
        # Change focus to trigger update
        next_field_xpath = '//*[@id="DefaultPropertyEditor_DefaultView_58_inputBox"]'
        wait_and_click(target_driver, next_field_xpath)
        logging.info("Changed focus to trigger update")
        
        # Add delay to allow gauge to update
        time.sleep(1.1)
        
        # Take final screenshot after all changes
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "8_after_value_change.png"))
        logging.info("Gauge interactions completed")
        
    except Exception as e:
        logging.error(f"Gauge interactions failed: {e}")
        raise

def perform_gauge_test(headless=False):
    """Perform the Canvas Gauges drag and drop test"""
    source_driver = None
    target_driver = None
    
    try:
        # Setup windows
        source_driver = create_chrome_driver("SOURCE", (0, 0), headless)
        target_driver = create_chrome_driver("TARGET", (820, 0), headless)
        
        # Load source and target
        source_driver.get(SOURCE_URL)
        logging.info("Loading target window...")
        target_driver.get(TARGET_URL)
        
        # Increased initial wait time for target window
        logging.info("Waiting for target window to initialize...")
        time.sleep(10)  # Increased from 2 to 10 seconds
        logging.info("Target window initialization period completed")
        
        # Take initial screenshots
        source_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "1_source_initial.png"))
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "2_target_initial.png"))
        
        # Find source element (component XML)
        source_element = WebDriverWait(source_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='component.xml']"))
        )
        
        # Find target drop zone using XPath
        target_element = WebDriverWait(target_driver, 10).until(
            EC.presence_of_element_located((By.XPATH, TARGET_XPATH))
        )
        
        # Perform drag and drop
        if not simulate_drag_and_drop(source_driver, target_driver, source_element, target_element):
            raise Exception("Drag and drop simulation failed")
        
        # Wait for component to load and take final screenshot
        time.sleep(5)
        target_driver.save_screenshot(os.path.join(SCREENSHOT_DIR, "3_after_drop.png"))
        logging.info("Canvas Gauge component added successfully")
        
        # Add item view move after initial component drop
        logging.info("\n" + "="*80 + "\nMoving item view to overview panel\n" + "="*80)
        perform_itemview_move(target_driver)
        
        # Add gauge interactions after item view move
        logging.info("\n" + "="*80 + "\nPerforming gauge interactions\n" + "="*80)
        perform_gauge_interactions(target_driver)
        
    except Exception as e:
        logging.error(f"Test failed: {e}")
        raise
        
    finally:
        # Cleanup
        for driver in [source_driver, target_driver]:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.warning(f"Error closing window: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run Canvas Gauges drag and drop test')
    parser.add_argument('--headless', action='store_true', help='Run in headless mode')
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    perform_gauge_test(args.headless)
