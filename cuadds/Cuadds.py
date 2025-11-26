from selenium import webdriver
from selenium.webdriver.chrome.service import Service
import couchdb
import time

# CouchDB Setup
def connect_to_couchdb():
    couch = couchdb.Server("http://admin:123456@127.0.0.1:5984/")  # CouchDB server URL
    db_name = "cuadds"

    # Create database if it doesn't exist
    if db_name not in couch:
        db = couch.create(db_name)
    else:
        db = couch[db_name]

    return db

# Path to your ChromeDriver
chrome_driver_path = '/home/hannesn/Downloads/chromedriver-linux64/chromedriver'

# Set up the ChromeDriver using Service
service = Service(executable_path=chrome_driver_path)

# Initialize the driver
driver = webdriver.Chrome(service=service)

try:
    # Navigate to the CUADDS login page
    driver.get('https://www.cuadds.com/signin')

    # Pause for manual login
    print("Please log in manually within the next 30 seconds...")
    time.sleep(30)  # Adjust the time as necessary

    # Navigate to the specific page you want to save
    target_url = 'https://www.cuadds.com/item/mBcyjgrTfdbGY4xsr'
    driver.get(target_url)

    # Wait for the page to load fully
    time.sleep(30)

    # Get the entire HTML content of the page
    page_html = driver.page_source

    # Save the HTML content to CouchDB
    try:
        # Connect to CouchDB
        db = connect_to_couchdb()

        # Document to save
        document = {
            "_id": "mBcyjgrTfdbGY4xsr",  # Use the URL segment as the unique ID
            "url": target_url,
            "html": page_html
        }

        # Save the document
        db.save(document)
        print("Page HTML successfully saved to CouchDB!")

    except Exception as e:
        print(f"Error saving to CouchDB: {e}")

finally:
    # Close the browser when done
    driver.quit()
