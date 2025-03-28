import os
import time
import logging
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

# Reuse configuration from WindowDragMonitor.py
CHROME_DRIVER_PATH = "/home/hannesn/Downloads/chromedriver-linux64/chromedriver"

# Update configuration to handle multiple tests
TEST_CONFIGS = [
    {
        "name": "WhatPanel",
        "source_url": "https://localhost:8443/EAMD.ucp/Components/com/ceruleanCircle/EAM/5_ux/WODA/WhatPanel/2.4.4",
        "component": "WhatPanel.component.xml"
    },
    {
        "name": "OverviewPanel",
        "source_url": "https://localhost:8443/EAMD.ucp/Components/com/ceruleanCircle/EAM/5_ux/WODA/OverviewPanel/2.4.4",
        "component": "OverviewPanel.component.xml"
    },
    {
        "name": "DetailsPanel",
        "source_url": "https://localhost:8443/EAMD.ucp/Components/com/ceruleanCircle/EAM/5_ux/WODA/DetailsPanel/2.4.4",
        "component": "DetailsPanel.component.xml"
    },
    {
        "name": "ActionsPanel",
        "source_url": "https://localhost:8443/EAMD.ucp/Components/com/ceruleanCircle/EAM/5_ux/WODA/ActionsPanel/2.4.4",
        "component": "ActionsPanel.component.xml"
    }
]

TARGET_URL = "https://localhost:8443/EAMD.ucp/Components/tla/EAM/layer1/Thinglish/Once/2.4.4/src/html/Once.html"

# Add screenshot directory configuration after existing config
SCREENSHOT_DIR = "test_screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

def create_chrome_driver(window_name, window_position):
    """Reuse driver creation from WindowDragMonitor.py"""
    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--ignore-certificate-errors")
    options.add_argument("--allow-insecure-localhost")
    options.add_argument(f"--window-position={window_position[0]},{window_position[1]}")
    
    # Set window size based on window type
    if window_name == "SOURCE":
        options.add_argument("--window-size=800,900")
    else:  # TARGET window
        options.add_argument("--start-maximized")
    
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    
    return webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)

def wait_for_kernel_load(driver):
    """Wait briefly for the kernel to load in the target window"""
    try:
        # Simple check with short timeout
        time.sleep(2)  # Brief wait for page load
        status = driver.execute_script("return window.Once ? true : false")
        logging.info(f"Once object detected: {status}")
        return True
    except Exception as e:
        logging.error(f"Kernel check failed: {str(e)}")
        return False

def take_screenshot(driver, name):
    """Take a screenshot and save it with timestamp"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(SCREENSHOT_DIR, f"{name}_{timestamp}.png")
    driver.save_screenshot(filename)
    logging.info(f"Screenshot saved: {filename}")

def simulate_drag_and_drop(source_driver, target_driver, source_element, target_element):
    """Simulate drag and drop using JavaScript events"""
    logging.info("Setting up drag and drop simulation...")
    
    # Trigger dragstart and capture data
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
        
        # Perform drop in target window
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

def perform_single_test(config):
    """Perform drag and drop test for a single panel configuration"""
    source_driver = None
    target_driver = None
    
    try:
        # Setup source window
        source_driver = create_chrome_driver("SOURCE", (0, 0))
        source_driver.get(config["source_url"])
        
        time.sleep(2)
        take_screenshot(source_driver, f"1_{config['name']}_source_initial")
        
        # Setup target window
        target_driver = create_chrome_driver("TARGET", (820, 0))
        target_driver.get(TARGET_URL)
        
        if not wait_for_kernel_load(target_driver):
            raise Exception("Target window kernel failed to load")
        take_screenshot(target_driver, f"2_{config['name']}_target_initial")
        
        # Find source element
        source_element = WebDriverWait(source_driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, f"a[href*='{config['component']}']"))
        )
        
        # Get target drop zone
        target_element = WebDriverWait(target_driver, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        
        take_screenshot(source_driver, f"3_{config['name']}_before_drag")
        
        if not simulate_drag_and_drop(source_driver, target_driver, source_element, target_element):
            raise Exception("Drag and drop simulation failed")
            
        logging.info(f"Waiting for {config['name']} component to load...")
        time.sleep(5)
        take_screenshot(target_driver, f"4_{config['name']}_after_drop")
        logging.info(f"{config['name']} drag and drop completed successfully")
        
    finally:
        for driver in [source_driver, target_driver]:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.warning(f"Error closing window: {e}")

def perform_drag_and_drop_test():
    """Run all configured tests sequentially in the same browser windows"""
    source_driver = None
    target_driver = None
    
    try:
        # Setup initial windows once
        source_driver = create_chrome_driver("SOURCE", (0, 0))
        target_driver = create_chrome_driver("TARGET", (820, 0))
        
        # Load target window once
        target_driver.get(TARGET_URL)
        if not wait_for_kernel_load(target_driver):
            raise Exception("Target window kernel failed to load")
        take_screenshot(target_driver, "1_target_initial")
        
        # Process each panel sequentially
        for i, config in enumerate(TEST_CONFIGS, 1):
            logging.info(f"\n{'='*80}\nAdding {config['name']}\n{'='*80}")
            
            # Load source for current panel
            source_driver.get(config["source_url"])
            time.sleep(2)
            take_screenshot(source_driver, f"{i}_source_{config['name']}")
            
            # Find source element
            source_element = WebDriverWait(source_driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, f"a[href*='{config['component']}']"))
            )
            
            # Get target drop zone
            target_element = WebDriverWait(target_driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            # Perform drag and drop
            if not simulate_drag_and_drop(source_driver, target_driver, source_element, target_element):
                raise Exception(f"Drag and drop simulation failed for {config['name']}")
                
            logging.info(f"Waiting for {config['name']} component to load...")
            time.sleep(5)
            take_screenshot(target_driver, f"{i}_target_after_{config['name']}")
            logging.info(f"{config['name']} added successfully")
    
    except Exception as e:
        logging.error(f"Test failed: {e}")
        raise
    
    finally:
        # Cleanup only at the end
        for driver in [source_driver, target_driver]:
            if driver:
                try:
                    driver.quit()
                except Exception as e:
                    logging.warning(f"Error closing window: {e}")

if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    perform_drag_and_drop_test()
