import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.edge.options import Options as EdgeOptions
import argparse
import json
import time

# Fixed URL
URL = "https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html"

# Configure Selenium WebDriver for multiple browsers
def get_driver(browser, headless=False):
    if browser.lower() == "chrome":
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        if headless:
            chrome_options.add_argument("--headless")
        service = ChromeService(executable_path='/home/hannesn/Downloads/chromedriver-linux64/chromedriver')
        return webdriver.Chrome(service=service, options=chrome_options)

    elif browser.lower() == "firefox":
        firefox_options = webdriver.FirefoxOptions()
        firefox_options.add_argument("--ignore-certificate-errors")
        firefox_options.add_argument("--no-remote")
        firefox_options.add_argument("--new-instance")
        if headless:
            firefox_options.add_argument("--headless")
        service = FirefoxService(executable_path="/usr/local/bin/geckodriver")
        return webdriver.Firefox(service=service, options=firefox_options)

    elif browser.lower() == "edge":
        edge_options = EdgeOptions()
        edge_options.add_argument("--ignore-certificate-errors")
        edge_options.add_argument("--allow-insecure-localhost")
        if headless:
            edge_options.add_argument("--headless")
        service = EdgeService(executable_path='/home/hannesn/Downloads/edgedriver_linux64/msedgedriver')
        return webdriver.Edge(service=service, options=edge_options)

    elif browser.lower() == "safari":
        if headless:
            raise ValueError("Safari does not support headless mode.")
        return webdriver.Safari()

    else:
        raise ValueError(f"Unsupported browser: {browser}")

# JavaScript code for PerformanceObserver
performance_observer_js = """
window.performanceMetrics = {
    paint: [],
    longtasks: [],
    resources: [],
    layoutShifts: [],
    navigation: null
};

const observer = new PerformanceObserver((list) => {
    const entries = list.getEntries();
    entries.forEach((entry) => {
        switch (entry.entryType) {
            case 'paint':
                window.performanceMetrics.paint.push({
                    name: entry.name,
                    startTime: entry.startTime
                });
                break;
            case 'longtask':
                window.performanceMetrics.longtasks.push({
                    start: entry.startTime,
                    duration: entry.duration
                });
                break;
            case 'resource':
                window.performanceMetrics.resources.push({
                    name: entry.name,
                    startTime: entry.startTime,
                    duration: entry.duration,
                    transferSize: entry.transferSize || 0
                });
                break;
            case 'layout-shift':
                window.performanceMetrics.layoutShifts.push({
                    value: entry.value,
                    hadRecentInput: entry.hadRecentInput,
                    startTime: entry.startTime
                });
                break;
        }
    });
});

observer.observe({
    entryTypes: ['paint', 'longtask', 'resource', 'layout-shift']
});

setTimeout(() => {
    observer.disconnect();
    console.log('PerformanceObserver disconnected.');
}, 10000);
"""

# Run PerformanceObserver on the fixed URL
def run_performance_observer(browser, duration):
    driver = get_driver(browser, args.headless)
    metrics = None
    try:
        print(f"Loading: {URL}")
        driver.get(URL)
        print("Page loaded.")

        # Inject PerformanceObserver JS
        driver.execute_script(performance_observer_js)
        print("PerformanceObserver script injected.")

        # Simulate interaction
        time.sleep(3)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print("Page scrolled.")

        # Wait for metrics collection
        time.sleep(duration)

        # Retrieve collected metrics
        metrics = driver.execute_script("return window.performanceMetrics;")
        print("Collected metrics.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    return metrics

# Save metrics to a JSON file
def save_metrics_to_file(metrics, filename="performance_metrics.json"):
    with open(filename, 'w') as file:
        json.dump(metrics, file, indent=4)
    print(f"Metrics saved to {filename}")

# Visualize performance metrics
def visualize_metrics(metrics):
    if not metrics:
        print("No metrics to display.")
        return

    # Layout Shifts (CLS)
    if 'layoutShifts' in metrics and metrics['layoutShifts']:
        shift_times = [shift['startTime'] for shift in metrics['layoutShifts']]
        shift_values = [shift['value'] for shift in metrics['layoutShifts']]

        plt.figure(figsize=(12, 6))
        plt.scatter(shift_times, shift_values, color='orange')
        plt.title("Layout Shifts (CLS)")
        plt.xlabel("Time (ms)")
        plt.ylabel("Shift Value")
        plt.tight_layout()
        plt.show()

    # Long Tasks
    if 'longtasks' in metrics and metrics['longtasks']:
        starts = [task['start'] for task in metrics['longtasks']]
        durations = [task['duration'] for task in metrics['longtasks']]

        plt.figure(figsize=(12, 6))
        plt.bar(range(len(starts)), durations, color='red', label="Long Task Duration")
        plt.axhline(y=50, color='green', linestyle='--', label="Expected Max Duration: 50 ms")
        plt.title("Long Tasks Analysis")
        plt.xlabel("Task Index")
        plt.ylabel("Duration (ms)")
        plt.xticks(range(len(starts)), [f"{int(start)} ms" for start in starts], rotation=45)
        plt.legend()
        plt.tight_layout()
        plt.show()

    # Paint Metrics
    if 'paint' in metrics and metrics['paint']:
        names = [metric['name'] for metric in metrics['paint']]
        times = [metric['startTime'] for metric in metrics['paint']]

        plt.figure(figsize=(8, 6))
        plt.bar(names, times, color='blue')
        plt.title("Paint Metrics")
        plt.ylabel("Time (ms)")
        plt.xlabel("Metric")
        plt.tight_layout()
        plt.show()

    # Resource Load Times and Sizes
    if 'resources' in metrics and metrics['resources']:
        resource_names = [resource['name'] for resource in metrics['resources'][:10]]
        resource_durations = [resource['duration'] for resource in metrics['resources'][:10]]
        resource_sizes = [resource.get('transferSize', 0) for resource in metrics['resources'][:10]]

        # Resource Durations
        plt.figure(figsize=(12, 6))
        plt.barh(resource_names, resource_durations, color='purple')
        plt.title("Top 10 Resource Load Times")
        plt.xlabel("Load Time (ms)")
        plt.ylabel("Resource Name")
        plt.tight_layout()
        plt.show()

        # Resource Sizes
        plt.figure(figsize=(12, 6))
        plt.barh(resource_names, resource_sizes, color='cyan')
        plt.title("Top 10 Resource Sizes")
        plt.xlabel("Size (bytes)")
        plt.ylabel("Resource Name")
        plt.tight_layout()
        plt.show()

# Main Execution
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Performance Metrics Analysis")
    parser.add_argument("--browser", type=str, default="chrome", help="Browser to use: chrome, firefox, edge, safari")
    parser.add_argument("--duration", type=int, default=30, help="Observation duration in seconds")
    parser.add_argument("--headless", action="store_true", help="Run in headless mode")
    args = parser.parse_args()

    metrics = run_performance_observer(args.browser, args.duration)
    if metrics:
        save_metrics_to_file(metrics, f"metrics_{args.browser}.json")
        visualize_metrics(metrics)
    else:
        print("No metrics collected.")
