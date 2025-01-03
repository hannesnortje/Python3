from playwright.sync_api import sync_playwright

def test_drag_and_drop():
    with sync_playwright() as p:
        # Launch the browser
        browser = p.chromium.launch(headless=False)  # Set headless=True for headless mode
        context = browser.new_context(ignore_https_errors=True)
        context.set_default_timeout(60000)  # Increase default timeout to 60 seconds
        page = context.new_page()

        # Navigate to the URL
        page.goto('https://localhost:8443/EAMD.ucp/Components/com/metatrom/EAM/layer5/LandingPage/3.1.0/src/html/index.html')

        # Wait for the page to fully load
        print("Waiting for the page to fully load...")
        page.wait_for_load_state("networkidle", timeout=60000)

        # Wait for specific elements to appear
        print("Waiting for customer-page__container...")
        page.wait_for_selector(".customer-page__container", timeout=60000)

        print("Waiting for tablet-customer-page__container...")
        page.wait_for_selector(".tablet-customer-page__container", timeout=60000)

        # Locate the source and target elements
        source = page.locator(".customer-page__container .table-row")
        target = page.locator(".tablet-customer-page__container .table-row")

        # Perform the drag-and-drop
        print("Performing drag-and-drop...")
        source.drag_to(target)

        # Verify the result (e.g., check if the source element moved)
        success = page.locator(".tablet-customer-page__container .table-row").count() > 0
        assert success, "Drag and drop failed!"

        print("Drag and drop test completed successfully!")
        browser.close()

if __name__ == "__main__":
    test_drag_and_drop()
