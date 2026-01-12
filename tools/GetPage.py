from selenium import webdriver
import time

# Initialize the driver (Selenium will auto-manage ChromeDriver)
driver = webdriver.Chrome()

# Navigate to the CUADDS page and log in
driver.get('https://www.cuadds.com/signin')
print("Please log in manually within the next 30 seconds...")
time.sleep(30)  # Give time for manual login

# Navigate to the target page
driver.get('https://www.cuadds.com/item/HsYnX3vdPxzHEqMZ7')

# Wait for the page to load fully
time.sleep(30)

# Get the full page source after JavaScript has loaded
page_source = driver.page_source

# Save the page source to a text file in /home/hannesn/Documents/
file_path = '/home/hannesn/Documents/cuadds_page_source.txt'
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(page_source)

print(f"Page source saved to {file_path}")

driver.quit()
