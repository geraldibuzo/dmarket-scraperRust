# config/settings.py
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Google Authenticator secret
GOOGLE_AUTH_SECRET = os.getenv("GOOGLE_AUTH_SECRET")

# Steam credentials (load from environment variables or hardcode for testing)
STEAM_USERNAME = os.getenv(
    "STEAM_USERNAME", "eurythmic123"
)  # Replace with your Steam username
STEAM_PASSWORD = os.getenv(
    "STEAM_PASSWORD", "Goltsteinstrasse92.123$"
)  # Replace with your Steam password

# DMarket URLs
DMARKET_SIGN_IN_URL = "https://dmarket.com/sign-in"
DMARKET_MARKETPLACE_URL = "https://dmarket.com/ingame-items/item-list/csgo-skins"

# settings.py
ITEM_URLS = [
    "https://dmarket.com/item1",
    "https://dmarket.com/item2",
    # Add more item URLs here
]
