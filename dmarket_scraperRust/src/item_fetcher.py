import time
import random
import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.exceptions import DataFetchError
from selenium.common.exceptions import TimeoutException

# Global set to track processed items based on (name, wear)
processed_items = set()

# Get a logger for this module
logger = logging.getLogger(__name__)


# Custom exception for duplicate items
class DuplicateItemError(Exception):
    pass


def parse_item_name_and_wear(full_name):
    """
    Parses the full name to extract the item name and wear.
    Expects the wear to be in parentheses at the end, e.g.,
    "Sawed-Off | Mosaico (Well-Worn)".
    Returns a tuple (item_name, item_wear).
    """
    if "(" in full_name and full_name.endswith(")"):
        name_part, wear_part = full_name.rsplit("(", 1)
        item_name = name_part.strip()
        item_wear = wear_part[:-1].strip()  # remove the closing parenthesis
        return item_name, item_wear
    else:
        return full_name, None


class ItemFetcher:
    def __init__(self, browser):
        self.browser = browser
        self.actions = ActionChains(browser)

    def random_delay(self, min_seconds=2, max_seconds=3):
        """Introduce a random delay between actions."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def click_info_icon(self, item_element):
        """Click the info icon for a specific item by scoping the search to its container."""
        info_icon_button = None  # Predefine the variable
        try:
            info_icon_button = WebDriverWait(item_element, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.c-asset__action--info--purge-ignore")
                )
            )
            self.browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center'});", info_icon_button
            )
            time.sleep(1)
            self.actions.move_to_element(info_icon_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            logger.info("Clicked the info icon for the specific item.")
            self.random_delay()
        except Exception:
            logger.warning("First attempt to click info icon failed. Retrying...")
            try:
                if info_icon_button is None:
                    info_icon_button = WebDriverWait(item_element, 10).until(
                        EC.element_to_be_clickable(
                            (
                                By.CSS_SELECTOR,
                                "button.c-asset__action--info--purge-ignore",
                            )
                        )
                    )
                self.browser.execute_script("arguments[0].click();", info_icon_button)
                logger.info("Clicked the info icon using JavaScript fallback.")
                self.random_delay()
            except Exception as e:
                raise DataFetchError(f"Error clicking info icon: {e}")

    def fetch_item_name(self):
        """Fetch the name of the item from the preview modal."""
        try:
            item_name = (
                WebDriverWait(self.browser, 10)
                .until(
                    EC.presence_of_element_located(
                        (By.CSS_SELECTOR, "h3.c-assetPreview__title")
                    )
                )
                .text
            )
            logger.info(f"Fetched item name: {item_name}")
            return item_name
        except Exception as e:
            raise DataFetchError(f"Error fetching item name: {e}")

    def fetch_sales_history(self):
        """Fetch the sales history for the last month from the preview modal."""
        sales_history = []
        try:
            sales_table = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "table.c-assetPreview__table")
                )
            )
        except TimeoutException:
            logger.info("No sales history table found (Timeout); returning empty list.")
            return sales_history

        try:
            sales_rows = sales_table.find_elements(
                By.CSS_SELECTOR, "tr.c-assetPreview__row"
            )
            for row in sales_rows:
                cells = row.find_elements(By.CSS_SELECTOR, "td.c-assetPreview__cell")
                if len(cells) >= 3:
                    sale = {
                        "price": cells[0].text.strip(),
                        "operation": cells[1].text.strip(),
                        "date_time": cells[2].text.strip(),
                    }
                    sales_history.append(sale)
                    logger.info(
                        f"Sale: Price={sale['price']}, Operation={sale['operation']}, Date/Time={sale['date_time']}"
                    )
            logger.info(f"Total sales in the last month: {len(sales_history)}")
            return sales_history
        except Exception as e:
            raise DataFetchError(f"Error fetching sales history: {e}")

    def click_trading_statistics(self, item_element):
        """Click the Trading statistics button in the preview modal using JavaScript."""
        try:
            WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "div.c-assetSalesTabs")
                )
            )
            trading_stats_button = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located(
                    (
                        By.CSS_SELECTOR,
                        "div.c-assetSalesTabs > button.c-assetSalesTab.ng-star-inserted:not(.c-assetSalesTab--active)",
                    )
                )
            )
            self.browser.execute_script(
                "arguments[0].scrollIntoView({block: 'center', behavior: 'smooth'});",
                trading_stats_button,
            )
            time.sleep(0.5)
            self.browser.execute_script("arguments[0].click();", trading_stats_button)
            logger.info("Clicked Trading statistics tab using JavaScript")
            self.random_delay()
            WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.c-listContainer"))
            )
        except Exception as e:
            raise DataFetchError(f"Failed to click Trading Statistics: {str(e)}")

    def fetch_target_prices(self):
        """Fetch the Target Price data from the list container using bulk fetching."""
        try:
            list_container = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.c-listContainer"))
            )
            target_table = list_container.find_element(
                By.CSS_SELECTOR, "offer-order-table:nth-of-type(1) .c-tableBody"
            )
            target_price_rows = target_table.find_elements(
                By.CSS_SELECTOR, "div.c-tableRow"
            )
            target_prices = []
            for row in target_price_rows:
                try:
                    price_element = row.find_element(
                        By.CSS_SELECTOR,
                        "div.price__target offer-details-popup div.c-assetPreview_icon > div:nth-child(2)",
                    )
                    price = price_element.text.strip()
                    quantity_element = row.find_element(
                        By.CSS_SELECTOR, "div.c-tableCell:nth-of-type(2)"
                    )
                    quantity = quantity_element.text.strip()
                    logger.info(f"Target Price: {price}, Quantity: {quantity}")
                    target_prices.append({"price": price, "quantity": quantity})
                except Exception as e:
                    logger.warning(
                        f"Warning: Could not fetch target price for a row. Error: {e}"
                    )
                    continue
            logger.info(f"Fetched {len(target_prices)} Target Price records.")
            return target_prices
        except Exception as e:
            raise DataFetchError(f"Error fetching Target Price data: {e}")

    def fetch_offer_prices(self):
        """Fetch the Offer Price data from the list container using bulk fetching."""
        try:
            list_container = WebDriverWait(self.browser, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.c-listContainer"))
            )
            offer_table = list_container.find_element(
                By.CSS_SELECTOR, "offer-order-table:nth-of-type(2) .c-tableBody"
            )
            offer_price_rows = offer_table.find_elements(
                By.CSS_SELECTOR, "div.c-tableRow"
            )
            offer_prices = []
            for row in offer_price_rows:
                try:
                    price_element = row.find_element(
                        By.CSS_SELECTOR,
                        "div.price__offer offer-details-popup div.c-assetPreview_icon > div:nth-child(2)",
                    )
                    price = price_element.text.strip()
                    quantity_element = row.find_element(
                        By.CSS_SELECTOR, "div.c-tableCell:nth-of-type(2)"
                    )
                    quantity = quantity_element.text.strip()
                    logger.info(f"Offer Price: {price}, Quantity: {quantity}")
                    offer_prices.append({"price": price, "quantity": quantity})
                except Exception as e:
                    logger.warning(
                        f"Warning: Could not fetch offer price for a row. Error: {e}"
                    )
                    continue
            logger.info(f"Fetched {len(offer_prices)} Offer Price records.")
            return offer_prices
        except Exception as e:
            raise DataFetchError(f"Error fetching Offer Price data: {e}")

    def click_close_button(self):
        """Click the Close button in the preview modal."""
        try:
            close_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.c-dialogHeader__close")
                )
            )
            self.actions.move_to_element(close_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            logger.info("Clicked Close button.")
            self.random_delay()
        except Exception as e:
            raise DataFetchError(f"Error clicking Close button: {e}")

    def fetch_item_data(self, item_element):
        """
        Fetch data for a specific item.
        The method attempts to click the info icon to open the modal,
        then retrieves details such as item name, sales history, and pricing.
        """
        start_time = time.time()  # Start timer for this item
        try:
            self.click_info_icon(item_element)
            time.sleep(1)
            full_name = self.fetch_item_name()
            item_name, item_wear = parse_item_name_and_wear(full_name)
            item_key = (item_name, item_wear)
            if item_key in processed_items:
                logger.info(f"Duplicate item found ({item_key}). Skipping processing.")
                self.click_close_button()
                raise DuplicateItemError(
                    "Duplicate item encountered, skipping processing."
                )
            processed_items.add(item_key)
            item_data = {
                "name": item_name,
                "wear": item_wear,
                "sales_history": self.fetch_sales_history(),
            }
            self.click_trading_statistics(item_element)
            time.sleep(1)
            item_data["target_prices"] = self.fetch_target_prices()
            item_data["offer_prices"] = self.fetch_offer_prices()
            self.click_close_button()
            time.sleep(10)
            return item_data
        except DuplicateItemError:
            raise
        except Exception as e:
            raise DataFetchError(f"Error fetching item data: {e}")
        finally:
            elapsed = time.time() - start_time
            logger.info(
                "Time taken to process one item in fetch_item_data: %.2f seconds",
                elapsed,
            )

    def scroll_down_segment(self):
        """Scroll down one segment (80% of container height) in the marketplace inventory."""
        try:
            scroller = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "virtual-scroller.c-assets__container")
                )
            )
            self.browser.execute_script(
                "arguments[0].scrollBy(0, arguments[0].clientHeight * 0.8);", scroller
            )
            logger.info("Scrolled down one segment (80% of container height).")
            self.random_delay(1, 2)
        except Exception as e:
            logger.warning(f"Failed to scroll down segment: {e}")
