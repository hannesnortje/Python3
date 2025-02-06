import sys
import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import threading
from selenium.common.exceptions import TimeoutException  # <-- new import

class SeleniumWorker(object):
    def __init__(self, browser, test_function):
        self.browser = browser
        self.test_function = test_function

    def run(self):
        try:
            driver = self.get_driver()

            # Always use localhost URL
            url = "https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html"
            driver.get(url)
            print(f"Browser: {self.browser}, URL: {url}")

            # Run the provided test function
            self.test_function(driver)

            driver.quit()

        except Exception as e:
            print(f"An error occurred: {e}")

    def get_driver(self):
        # Always return Chrome driver
        chrome_options = webdriver.ChromeOptions()
        chrome_options.add_argument("--ignore-certificate-errors")
        chrome_options.add_argument("--allow-insecure-localhost")
        service = ChromeService(executable_path='/home/hannesn/Downloads/chromedriver-linux64/chromedriver')
        return webdriver.Chrome(service=service, options=chrome_options)

def run_test(driver):
    """
    Chat Client Test Logic:
    """
    # Navigate to chat client test URL
    client_url = "http://localhost:8080/EAMD.ucp/Components/me/hannesnortje/MLConnect/1.0.0/test/html/MLConnectTest.html"
    driver.get(client_url)
    print(f"Navigated to chat client URL: {client_url}")

    # Handle API key alert: try up to 2 times for reliability
    for attempt in range(2):
        try:
            alert = WebDriverWait(driver, 5).until(EC.alert_is_present())
            print(f"Alert found: {alert.text}. Sending API key. Attempt {attempt+1}.")
            alert.send_keys("AIzaSyDxxxxxxxx")
            alert.accept()
            # Optional: wait a bit to allow the app to process the key
            time.sleep(2)
        except TimeoutException:
            break

    # Wait for the chat interface to load (assume the textarea with id 'ml-connect' is present)
    WebDriverWait(driver, 30).until(
        EC.presence_of_element_located((By.ID, "ml-connect"))
    )
    print("Chat interface loaded.")

    def send_message_and_check(message):
        # Re-fetch the prompt element to avoid stale element reference
        prompt_textarea = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.ID, "ml-connect"))
        )
        prompt_textarea.clear()
        # Simulate human-like typing: send one character at a time with delay
        for char in message:
            prompt_textarea.send_keys(char)
            time.sleep(0.15)  # adjust delay as needed
        # Debug: show what has been typed in the prompt box
        typed_text = prompt_textarea.get_attribute("value")
        print(f"Typed text in prompt box: {typed_text}")
        send_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'onPromptSubmit')]")
        send_button.click()
        print(f"Sent message: {message}")
        time.sleep(5)  # wait for the chat reply to update
        response_container = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "[webean-role$=':response']"))
        )
        response_text = response_container.text
        if message in response_text:
            print(f"Message '{message}' found in response.")
        else:
            print(f"Message '{message}' NOT found in response.")
        return response_text

    first_response = send_message_and_check("Hello Gemini")
    second_response = send_message_and_check("Second message")
    if "Hello Gemini" in second_response and "Second message" in second_response:
        print("Both messages found in chat response.")
    else:
        print("Messages missing in chat response.")

    new_chat_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'onNewChat')]")
    new_chat_button.click()
    print("Clicked New Chat button.")
    time.sleep(3)

    new_chat_response = send_message_and_check("New chat message")

    download_pdf_button = driver.find_element(By.XPATH, "//button[contains(@onclick, 'onDownloadChat')]")
    download_pdf_button.click()
    print("Clicked Save as PDF button. Chat should be saved to the default folder.")

    input("Press Enter to close the browser after reviewing the chat...")
    driver.quit()

def start_selenium(browser):
    selenium_worker = SeleniumWorker(browser, run_test)
    selenium_thread = threading.Thread(target=selenium_worker.run)
    selenium_thread.start()

if __name__ == "__main__":
    # Directly use Chrome and localhost -- no UI is needed
    start_selenium("chrome")
