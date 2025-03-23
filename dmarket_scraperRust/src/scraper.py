import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from src.auth import authenticate
from src.navigation import navigate_to_marketplace
from src.item_fetcher import ItemFetcher
from src.storage import save_item_data
from src.utils import setup_browser
from src.exceptions import DataFetchError


def scrape_items():
    """Main function to scrape item data from the marketplace."""
    # Initialize the browser using setup_browser() from utils.py
    browser = setup_browser()

    try:
        # Authenticate the user if needed
        authenticate(browser)

        # Navigate to the marketplace page
        navigate_to_marketplace(browser)

        # Initialize item fetcher
        item_fetcher = ItemFetcher(browser)

        # Wait for items to load using the updated container selector
        WebDriverWait(browser, 15).until(
            EC.presence_of_all_elements_located(
                (
                    By.CSS_SELECTOR,
                    "div.c-asset-wrapper.inline-block.overflow-hidden.ng-star-inserted",
                )
            )
        )

        items = browser.find_elements(
            By.CSS_SELECTOR,
            "div.c-asset-wrapper.inline-block.overflow-hidden.ng-star-inserted",
        )
        print(f"Found {len(items)} items to scrape.")

        for index, item in enumerate(items, start=1):
            print(f"\nProcessing item {index}/{len(items)}...")
            try:
                item_data = item_fetcher.fetch_item_data(item)
                # Use the fetched item name or a default name if unavailable
                item_name = item_data.get("name", f"item_{index}")
                save_item_data(item_data, item_name)
                # Delay between items to avoid detection
                time.sleep(random.uniform(5, 10))
            except DataFetchError as e:
                print(f"Skipping item due to error: {e}")

        print("\nScraping completed successfully.")

    except Exception as e:
        print(f"Scraper encountered an error: {e}")

    finally:
        browser.quit()


if __name__ == "__main__":
    scrape_items()
