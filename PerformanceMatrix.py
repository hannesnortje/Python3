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
driver.get("https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html")

# Start measuring time for the DemoTable load
start_time = time.time()

# Expected DOM node count for comparison
EXPECTED_NODE_COUNT = 1500  # Set this to your baseline value

# Wait until the iframe is present and switch to it
try:
    iframe = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "iframe[src*='/EAMD.ucp/Components/com/metatrom/EAM/layer5/DeviceSimulation/3.1.0/src/html/DeviceSimulation.2.4.2.html#!/customer']"))
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

    # Measure Total DOM Nodes
    total_nodes = driver.execute_script("return document.getElementsByTagName('*').length;")
    print(f"Total DOM Nodes: {total_nodes}")

    # Validate against expected node count
    if total_nodes > EXPECTED_NODE_COUNT:
        print(f"Warning: Node count ({total_nodes}) exceeds expected baseline ({EXPECTED_NODE_COUNT})!")
    else:
        print(f"Node count ({total_nodes}) is within the expected range.")

    # Log DOM structure with tag names and child counts
    dom_structure = driver.execute_script("""
        const structure = [];
        document.querySelectorAll('*').forEach(node => {
            structure.push({
                tag: node.tagName,
                children: node.children.length
            });
        });
        return structure;
    """)
    
    print("DOM Structure (Sample):")
    for entry in dom_structure[:10]:  # Show only the first 10 entries
        print(f"Tag: {entry['tag']}, Children: {entry['children']}")

    # Measure memory usage without triggering garbage collection
    try:
        memory_info = driver.execute_script("return window.performance.memory;")
        print("Memory Usage:")
        print(f"Total JS Heap Size: {memory_info['totalJSHeapSize']} bytes")
        print(f"Used JS Heap Size: {memory_info['usedJSHeapSize']} bytes")
        print(f"JS Heap Size Limit: {memory_info['jsHeapSizeLimit']} bytes")
    except Exception as e:
        print(f"Error while measuring memory: {e}")


except Exception as e:
    print(f"Error: {e}")

# Close the browser after testing
driver.quit()
