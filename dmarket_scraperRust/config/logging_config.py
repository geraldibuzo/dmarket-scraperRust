# config/logging_config.py
import logging


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,  # Or DEBUG for development
        format="%(asctime)s [%(levelname)s] %(message)s",
        handlers=[logging.FileHandler("logs/scraping.log"), logging.StreamHandler()],
    )
