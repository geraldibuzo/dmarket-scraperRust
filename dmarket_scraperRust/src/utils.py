# utils.py
from selenium import webdriver
from selenium.webdriver.chrome.options import Options


def setup_browser():
    chrome_options = Options()
    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    chrome_options.add_argument(f"user-agent={user_agent}")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--headless")  # Uncomment for headless mode
    return webdriver.Chrome(options=chrome_options)
