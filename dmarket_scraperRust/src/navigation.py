from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains  # Used in the class
from src.exceptions import NavigationError
import time  # Used in the random_delay method
import random


class DMarketNavigation:
    def __init__(self, browser):
        self.browser = browser
        self.actions = ActionChains(browser)  # ActionChains is used here

    def random_delay(self, min_seconds=2, max_seconds=3):
        """Introduce a random delay between actions."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def navigate_to_marketplace(self):
        try:
            print("Current URL before navigation:", self.browser.current_url)
            marketplace_option = WebDriverWait(self.browser, 20).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//a[contains(@class, 'c-exchangeHeader__titleLink')]")
                )
            )
            self.actions.move_to_element(marketplace_option).pause(
                random.uniform(1.5, 2.5)
            ).click().perform()
            print("Clicked Marketplace navigation icon.")
            self.random_delay()

            print("Waiting for URL to contain '/ingame-items/item-list/csgo-skins'...")
            WebDriverWait(self.browser, 30).until(
                EC.url_contains("/ingame-items/item-list/csgo-skins")
            )
            print("Successfully navigated to Marketplace.")
            print("Current URL after navigation:", self.browser.current_url)
        except Exception as e:
            print("Current URL on error:", self.browser.current_url)
            raise NavigationError(f"Error navigating to Marketplace: {str(e)}")

    def apply_price_filter(self, min_price=10, max_price=20):
        """
        Apply a price filter to the marketplace items.
        :param min_price: Minimum price value (default: 10)
        :param max_price: Maximum price value (default: 20)
        """
        try:
            # Wait for the filter section to load
            filter_section = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (By.TAG_NAME, "expandable-advanced-filter")
                )
            )

            # Check if the input fields are already visible
            try:
                price_from_input = filter_section.find_element(
                    By.CSS_SELECTOR, "input[formcontrolname='priceFrom']"
                )
            except Exception:
                price_from_input = None

            if not price_from_input or not price_from_input.is_displayed():
                # Click on the filter header to expand the section
                filter_header = WebDriverWait(filter_section, 10).until(
                    EC.element_to_be_clickable(
                        (By.CSS_SELECTOR, "mat-expansion-panel-header")
                    )
                )
                filter_header.click()
                print("Clicked filter header to expand price filters.")
                self.random_delay()

            # Wait until the "From" input field is visible
            price_from_input = WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "input[formcontrolname='priceFrom']")
                )
            )
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", price_from_input
            )
            self.actions.move_to_element(price_from_input).click().perform()
            # Clear the field using JavaScript in case clear() doesn't work
            self.browser.execute_script("arguments[0].value = '';", price_from_input)
            price_from_input.send_keys(str(min_price))
            print(f"Set minimum price to {min_price}.")
            self.random_delay()

            # Wait until the "To" input field is visible
            price_to_input = WebDriverWait(self.browser, 10).until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "input[formcontrolname='priceTo']")
                )
            )
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", price_to_input
            )
            self.actions.move_to_element(price_to_input).click().perform()
            self.browser.execute_script("arguments[0].value = '';", price_to_input)
            price_to_input.send_keys(str(max_price))
            print(f"Set maximum price to {max_price}.")
            self.random_delay()

            # Optionally, trigger the filter application (if required)
            try:
                apply_button = self.browser.find_element(
                    By.XPATH, "//button[contains(text(), 'Apply')]"
                )
                self.actions.move_to_element(apply_button).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()
                print("Clicked 'Apply' button to apply filters.")
            except Exception:
                print("No 'Apply' button found. Filters may be applied automatically.")

        except Exception as e:
            raise NavigationError(f"Error applying price filter: {str(e)}")

    def close_filters(self):
        """
        Close the filters section by clicking the close button.
        """
        try:
            # Wait for the close button to be clickable
            close_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.c-filtersArea__headerClose")
                )
            )
            # Scroll the close button into view and click it
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", close_button
            )
            self.actions.move_to_element(close_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the close button to close the filters section.")
            self.random_delay()
        except Exception as e:
            raise NavigationError(f"Error closing filters: {str(e)}")

    def close_hide_button(self):
        """
        Close the hide button by clicking it.
        """
        try:
            # Wait for the hide button within the proposes-hide-button element to be clickable.
            hide_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.CSS_SELECTOR,
                        "proposes-hide-button.c-exchangeSum__hideButton button",
                    )
                )
            )
            # Scroll the hide button into view and click it
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", hide_button
            )
            self.actions.move_to_element(hide_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the hide button to close the hide section.")
            self.random_delay()
        except Exception as e:
            raise NavigationError(f"Error closing hide button: {str(e)}")

    def close_live_feed(self):
        """
        Close the live feed by clicking the live feed toggle button.
        """
        try:
            # Wait for the live feed toggle button to be clickable
            live_feed_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "button.c-liveFeed__toggleBtn")
                )
            )
            # Scroll the live feed button into view and click it
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", live_feed_button
            )
            self.actions.move_to_element(live_feed_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the live feed toggle button to close the live feed.")
            self.random_delay()
        except Exception as e:
            raise NavigationError(f"Error closing live feed: {str(e)}")

    def close_mat_icon(self):
        """
        Close the mat icon by clicking it.
        """
        try:
            # Wait for the mat-icon element to be clickable
            mat_icon = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "mat-icon.c-exchangeTabOnboarding__close")
                )
            )
            # Scroll the mat-icon into view and click it
            self.browser.execute_script("arguments[0].scrollIntoView(true);", mat_icon)
            self.actions.move_to_element(mat_icon).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the mat icon close button.")
            self.random_delay()
        except Exception as e:
            raise NavigationError(f"Error closing mat icon: {str(e)}")

    def close_promo_banner(self):
        """
        Close the promo banner by clicking its close button.
        """
        try:
            # Wait for the promo banner close button to be clickable using its aria-label
            promo_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, 'button[aria-label="close promo banner"]')
                )
            )
            # Scroll the promo button into view and click it
            self.browser.execute_script(
                "arguments[0].scrollIntoView(true);", promo_button
            )
            self.actions.move_to_element(promo_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the promo banner close button.")
            self.random_delay()
        except Exception as e:
            raise NavigationError(f"Error closing promo banner: {str(e)}")
