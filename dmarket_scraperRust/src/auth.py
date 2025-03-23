import pyotp
import time
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from src.exceptions import AuthenticationError
from config.settings import GOOGLE_AUTH_SECRET, STEAM_USERNAME, STEAM_PASSWORD


class DMarketAuth:
    def __init__(self, browser):
        self.browser = browser
        self.actions = ActionChains(browser)

    def random_delay(self, min_seconds=1, max_seconds=3):
        """Introduce a random delay between actions."""
        time.sleep(random.uniform(min_seconds, max_seconds))

    def human_type(self, element, text, min_delay=0.1, max_delay=0.3):
        """Simulate human typing with random delays between keystrokes."""
        for char in text:
            element.send_keys(char)
            time.sleep(random.uniform(min_delay, max_delay))

    def accept_cookies(self):
        """Accept cookie consent if prompted."""
        try:
            cookie_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Accept all')]")
                )
            )
            self.actions.move_to_element(cookie_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Cookie consent accepted.")
            self.random_delay()
        except Exception as e:
            print(f"Could not handle the cookie consent dialog: {e}")

    def login_via_steam(self):
        """Click the 'Sign up via Steam' button to initiate login."""
        try:
            steam_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (
                        By.XPATH,
                        "//button[@data-test-id='signUp_actionVendor_steam_userSide']",
                    )
                )
            )
            self.actions.move_to_element(steam_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked 'Sign up via Steam' button.")
            self.random_delay()
        except Exception as e:
            raise AuthenticationError(f"Error clicking 'Sign up via Steam' button: {e}")

    def enter_steam_credentials(self):
        """Enter Steam username and password and submit."""
        try:
            username_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@type='text' and contains(@class, '_2GBWeup5cttgbTw8FM3tfx')]",
                    )
                )
            )
            password_input = WebDriverWait(self.browser, 10).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//input[@type='password' and contains(@class, '_2GBWeup5cttgbTw8FM3tfx')]",
                    )
                )
            )
            self.actions.move_to_element(username_input).click().perform()
            self.human_type(username_input, STEAM_USERNAME)
            self.random_delay()

            self.actions.move_to_element(password_input).click().perform()
            self.human_type(password_input, STEAM_PASSWORD)
            self.random_delay()

            sign_in_button = WebDriverWait(self.browser, 10).until(
                EC.element_to_be_clickable(
                    (By.XPATH, "//button[contains(text(), 'Sign in')]")
                )
            )
            self.actions.move_to_element(sign_in_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked 'Sign in' button.")
            self.random_delay()
        except Exception as e:
            raise AuthenticationError(f"Error entering Steam credentials: {e}")

    def confirm_steam_mobile_login(self):
        """Click the 'Sign In' button after Steam Mobile Confirmation."""
        try:
            wait = WebDriverWait(self.browser, 20)
            possible_locators = [
                (By.ID, "imageLogin"),
                (By.XPATH, "//button[contains(text(), 'Sign In')]"),
            ]
            steam_sign_in_button = None
            for locator in possible_locators:
                try:
                    steam_sign_in_button = wait.until(
                        EC.element_to_be_clickable(locator)
                    )
                    break
                except Exception:
                    continue

            if not steam_sign_in_button:
                raise AuthenticationError("Steam 'Sign In' button not found!")

            self.actions.move_to_element(steam_sign_in_button).pause(
                random.uniform(0.5, 1.5)
            ).click().perform()
            print("Clicked the Steam 'Sign In' button after confirmation.")
            self.random_delay()
        except Exception as e:
            raise AuthenticationError(f"Error clicking Steam 'Sign In' button: {e}")

    def handle_google_auth(self):
        """Enter the Google Authenticator code to complete login."""
        for attempt in range(3):
            try:
                google_auth_input = WebDriverWait(self.browser, 20).until(
                    EC.visibility_of_element_located(
                        (
                            By.XPATH,
                            "//input[contains(@class, 'c-dialogTfa__copyCode--input')]",
                        )
                    )
                )
                current_code = pyotp.TOTP(GOOGLE_AUTH_SECRET).now()
                self.actions.move_to_element(google_auth_input).click().perform()
                self.human_type(google_auth_input, current_code)
                self.random_delay()

                submit_button = WebDriverWait(self.browser, 10).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, "//button[@data-test-id='logIn_logInWithTfa']")
                    )
                )
                self.actions.move_to_element(submit_button).pause(
                    random.uniform(0.5, 1.5)
                ).click().perform()
                print("Submitted Google Authenticator code.")
                break
            except Exception as e:
                print(
                    f"Error with Google Authenticator (attempt {attempt + 1}): {str(e)}"
                )
                if attempt == 2:
                    raise AuthenticationError(
                        "Failed to authenticate after 3 attempts."
                    )
