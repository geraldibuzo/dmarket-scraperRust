import logging
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# from selenium.common.exceptions import TimeoutException

from src.utils import setup_browser
from src.auth import DMarketAuth
from src.navigation import DMarketNavigation
from src.item_fetcher import ItemFetcher, DuplicateItemError
from src.storage import save_item_data
from config.settings import DMARKET_SIGN_IN_URL

# Set up logging configuration.
logging.basicConfig(
    level=logging.INFO,  # Change to DEBUG during development if needed.
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.FileHandler("logs/scraping.log"), logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def take_screenshot(browser, name="screenshot"):
    """Helper function to take a screenshot and save it with a timestamp."""
    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"screenshots/{name}_{timestamp}.png"
    browser.save_screenshot(filename)
    logger.info(f"Screenshot saved as {filename}")


def main():
    logger.info("Starting main()")
    browser = None
    try:
        # Setup browser and navigate to sign-in URL.
        browser = setup_browser()
        browser.get(DMARKET_SIGN_IN_URL)
        browser.maximize_window()
        logger.info("Browser opened and navigated to sign-in URL.")

        # Authenticate on DMarket.
        auth = DMarketAuth(browser)
        auth.accept_cookies()
        auth.login_via_steam()
        auth.enter_steam_credentials()
        auth.confirm_steam_mobile_login()  # Wait for Steam Mobile Confirmation and click the second "Sign In" button.
        auth.handle_google_auth()
        logger.info("Authentication complete.")

        # Navigate to the marketplace page.
        navigation = DMarketNavigation(browser)
        navigation.navigate_to_marketplace()
        logger.info("Navigated to marketplace.")

        # --- New Rust Navigation Flow ---
        # Close unnecessary elements.
        navigation.close_hide_button()
        navigation.close_live_feed()
        navigation.close_mat_icon()
        navigation.close_promo_banner()
        logger.info("Closed unnecessary elements.")

        # Click the Game Banner Selector.
        gamebanner_selector = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "div.c-gameBannerSelector"))
        )
        navigation.actions.move_to_element(gamebanner_selector).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        logger.info("Clicked the Game Banner Selector.")
        time.sleep(1)

        # Click the Rust button.
        rust_button = WebDriverWait(browser, 10).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//a[@href='/ingame-items/item-list/rust-skins']")
            )
        )
        navigation.actions.move_to_element(rust_button).pause(
            random.uniform(0.5, 1.5)
        ).click().perform()
        logger.info("Clicked the Rust button.")
        time.sleep(1)

        # Confirm navigation to the Rust marketplace page.
        expected_url = "https://dmarket.com/ingame-items/item-list/rust-skins"
        WebDriverWait(browser, 30).until(EC.url_to_be(expected_url))
        logger.info(
            "Successfully navigated to Rust marketplace: %s", browser.current_url
        )

        # Apply price filter and close filters.
        navigation.apply_price_filter(min_price=10.1, max_price=15)
        navigation.close_filters()
        logger.info("Applied price filter and closed filters.")

        # Wait for the marketplace items to load.
        initial_items = WebDriverWait(browser, 20).until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "div.c-asset__headerRight")
            )
        )
        # Build a master list that never resets.
        master_items = list(initial_items)
        logger.info("Found %d initial marketplace items.", len(master_items))

        item_fetcher = ItemFetcher(browser)
        processed_count = 0
        total_index = 0

        while processed_count < 90:
            # If we've run out of items in the master list, scroll and append new ones.
            if total_index >= len(master_items):
                logger.info(
                    "Reached end of master items list. Scrolling down to load more items."
                )
                item_fetcher.scroll_down_segment()
                time.sleep(2)
                new_items = WebDriverWait(browser, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.c-asset__headerRight")
                    )
                )
                for item in new_items:
                    if item not in master_items:
                        master_items.append(item)
                if total_index >= len(master_items):
                    logger.info("No new items loaded; waiting a bit longer.")
                    time.sleep(2)
                    continue

            # Process the item at the current index.
            item = master_items[total_index]
            total_index += 1

            start_time = time.time()  # Start timing for this item.
            try:
                logger.info("Processing valid item at overall index %d", total_index)
                item_data = item_fetcher.fetch_item_data(item)
                if item_data:
                    save_item_data(item_data, item_data["name"])
                    processed_count += 1
                else:
                    logger.info("fetch_item_data returned None, skipping.")
            except DuplicateItemError as e:
                logger.info(
                    "Duplicate item encountered at overall index %d: %s", total_index, e
                )
                continue
            except Exception as e:
                logger.error(
                    "Error processing item at overall index %d: %s", total_index, e
                )
                take_screenshot(browser, f"item_{total_index}_error")
                continue
            elapsed = time.time() - start_time
            logger.info(
                "Time taken to scrape, process, and save item at overall index %d: %.2f seconds",
                total_index,
                elapsed,
            )

            # Optionally, after processing 8 valid items, scroll down to load more items.
            if processed_count > 0 and processed_count % 8 == 0:
                logger.info(
                    "Processed 8 valid items; scrolling down 80%% of the container."
                )
                item_fetcher.scroll_down_segment()
                time.sleep(2)
                new_items = WebDriverWait(browser, 20).until(
                    EC.presence_of_all_elements_located(
                        (By.CSS_SELECTOR, "div.c-asset__headerRight")
                    )
                )
                for item in new_items:
                    if item not in master_items:
                        master_items.append(item)

        logger.info("Script completed successfully.")
    except Exception as e:
        logger.error("An error occurred in the main script: %s", e)
        if browser is not None:
            take_screenshot(browser, "main_script_error")
        raise
    finally:
        if browser is not None:
            browser.quit()
            logger.info("Browser closed.")


if __name__ == "__main__":
    main()
