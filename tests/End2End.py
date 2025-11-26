from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import time

# Browser Automation to Inject Changes and Trigger View Re-Renders
class ViewReloader:
    def __init__(self, url, chrome_driver_path):
        self.url = url
        # Configure the Selenium ChromeDriver
        chrome_service = Service(chrome_driver_path)
        self.driver = webdriver.Chrome(service=chrome_service)
        self.driver.get(self.url)
        print(f"Opened browser at {self.url}")

    def inject_and_rerender(self, file_path):
        try:
            file_extension = file_path.split('.')[-1]

            # Read the updated file content
            with open(file_path, 'r') as file:
                updated_content = file.read()

            if file_extension == 'html':
                # Replace the content in the corresponding component in the browser
                self.driver.execute_script(f"""
                    const element = document.querySelector('[data-component="{file_path.split("/")[-1].split(".")[0]}"]');
                    if (element) {{
                        element.innerHTML = `{updated_content}`;
                        console.log("HTML content replaced and rerendered!");
                    }} else {{
                        console.log("Element for the updated HTML not found.");
                    }}
                """)
            elif file_extension == 'css':
                # Inject updated CSS into the browser
                self.driver.execute_script(f"""
                    const styleElement = document.createElement('style');
                    styleElement.innerHTML = `{updated_content}`;
                    document.head.appendChild(styleElement);
                    console.log("CSS updated and applied!");
                """)
            elif file_extension == 'js':
                # Inject updated JavaScript into the browser
                self.driver.execute_script(f"""
                    const scriptElement = document.createElement('script');
                    scriptElement.innerHTML = `{updated_content}`;
                    document.body.appendChild(scriptElement);
                    console.log("JavaScript updated and executed!");
                """)
            else:
                print(f"Unsupported file type for: {file_path}")
        except Exception as e:
            print(f"Error during injection and rerendering: {e}")

    def quit(self):
        self.driver.quit()


# File Watcher to Monitor Changes
class ChangeHandler(FileSystemEventHandler):
    def __init__(self, reloader):
        self.reloader = reloader

    def on_modified(self, event):
        # Watch for specific file types
        valid_extensions = ('.html', '.css', '.js')
        if event.src_path.endswith(valid_extensions):
            print(f"File changed: {event.src_path}")
            self.reloader.inject_and_rerender(event.src_path)


def start_file_watcher(path, reloader):
    event_handler = ChangeHandler(reloader)
    observer = Observer()
    observer.schedule(event_handler, path=path, recursive=True)
    observer.start()
    print(f"Watching for changes in {path}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("Stopped watching files.")
    observer.join()


if __name__ == "__main__":
    # Paths and URL setup
    chrome_driver_path = '/home/hannesn/Downloads/chromedriver-linux64/chromedriver'  # Path to ChromeDriver
    demo_url = 'https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html'
    watch_directory = '/media/hannesn/Hannes/WODA.2023/_var_dev/EAMD.ucp/Components/com/metatrom/EAM/layer5'  # Update to your project directory

    # Initialize and run the watcher with the browser refresher
    reloader = ViewReloader(demo_url, chrome_driver_path)
    try:
        start_file_watcher(watch_directory, reloader)
    finally:
        reloader.quit()
