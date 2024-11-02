from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
import time

# Path to your ChromeDriver
chrome_driver_path = '/home/hannesn/Downloads/chromedriver-linux64/chromedriver'

# Set up the ChromeDriver using Service
service = Service(executable_path=chrome_driver_path)

# Initialize the driver
driver = webdriver.Chrome(service=service)

# Navigate to the CUADDS login page
driver.get('https://www.cuadds.com/signin')

# Pause for manual login
print("Please log in manually within the next 30 seconds...")
time.sleep(30)  # Adjust the time as necessary

# After login, navigate to the grid page (your Dev Sprint or similar page)
driver.get('https://www.cuadds.com/item/HsYnX3vdPxzHEqMZ7')

# Wait for the page to load fully
time.sleep(30)

# Initialize the list for cuadds
cuadd_text_list = []

# Find all column containers (for example, these could be divs that contain cuadds for "To Do", "In Progress", etc.)
columns = driver.find_elements(By.CSS_SELECTOR, '.column-class')  # Replace with the actual class or ID for the columns

# Loop through each column and capture cuadds
for column in columns:
    # Find all cuadds in the current column
    cuadds = column.find_elements(By.CSS_SELECTOR, '.gridItemMainWrapper')  # Replace with actual cuadd class

    # Loop through each cuadd and get all visible text inside each cuadd
    for cuadd in cuadds:
        cuadd_text = cuadd.text.strip()  # This gets all visible text within the cuadd

        # Avoid duplicates and empty entries
        if cuadd_text and cuadd_text not in cuadd_text_list:
            cuadd_text_list.append(cuadd_text)

# Print out the list of cuadds
for index, text in enumerate(cuadd_text_list, start=1):
    print(f"Cuadd {index}: {text}")

# Close the browser when done
driver.quit()
