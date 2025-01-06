import matplotlib.pyplot as plt
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
import time

# Configure the Selenium WebDriver
def get_driver():
    chrome_options = webdriver.ChromeOptions()
    chrome_options.add_argument("--ignore-certificate-errors")
    chrome_options.add_argument("--allow-insecure-localhost")
    chrome_options.add_argument("--headless")  # Enable headless mode
    service = ChromeService(executable_path='/home/hannesn/Downloads/chromedriver-linux64/chromedriver')
    return webdriver.Chrome(service=service, options=chrome_options)

# JavaScript code for PerformanceObserver
performance_observer_js = """
window.performanceMetrics = {
    paint: [],
    longtasks: [],
    resources: [],
    marks: [],
    measures: [],
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
                    duration: entry.duration
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

# Run the PerformanceObserver and collect metrics
def run_performance_observer():
    driver = get_driver()
    metrics = None
    try:
        driver.get("https://demo.metatrom.net/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html")
        print("Demo application loaded.")

        driver.execute_script(performance_observer_js)
        print("PerformanceObserver script injected.")

        time.sleep(30)

        metrics = driver.execute_script("return window.performanceMetrics;")
        print("Collected Performance Metrics:", metrics)

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

    return metrics

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

    # Resource Load Times
    if 'resources' in metrics and metrics['resources']:
        resource_names = [resource['name'] for resource in metrics['resources'][:10]]  # Limit to 10 for readability
        resource_durations = [resource['duration'] for resource in metrics['resources'][:10]]

        plt.figure(figsize=(12, 6))
        plt.barh(resource_names, resource_durations, color='purple')
        plt.title("Top 10 Resource Load Times")
        plt.xlabel("Load Time (ms)")
        plt.ylabel("Resource Name")
        plt.tight_layout()
        plt.show()

# Main Execution
metrics = run_performance_observer()
if metrics:
    visualize_metrics(metrics)
else:
    print("No metrics collected.")
