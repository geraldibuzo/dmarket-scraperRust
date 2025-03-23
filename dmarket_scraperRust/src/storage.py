import json
import os
from datetime import datetime

# Constants for aggregated data file
AGGREGATED_DIR = "data/aggregated"
AGGREGATED_FILE = os.path.join(AGGREGATED_DIR, "items_all.json")


def save_item_data(item_data, item_name):
    """Save item data to an individual JSON file and update aggregated data."""
    try:
        # Create the data/items directory if it doesn't exist
        os.makedirs("data/items", exist_ok=True)

        # Add a timestamp to the filename for individual item storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"data/items/{item_name}_{timestamp}.json"

        # Save the item data to an individual JSON file
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(item_data, file, indent=4)
        print(f"Saved item data to {filename}")

        # --- New code: Update aggregated file ---

        # Ensure the aggregated directory exists
        os.makedirs(AGGREGATED_DIR, exist_ok=True)

        # Load existing aggregated data if available; otherwise, start with an empty list
        aggregated_items = []
        if os.path.exists(AGGREGATED_FILE):
            try:
                with open(AGGREGATED_FILE, "r", encoding="utf-8") as agg_file:
                    aggregated_items = json.load(agg_file)
            except json.JSONDecodeError:
                # If the file is empty or invalid, start fresh
                aggregated_items = []

        # Append the new item data
        aggregated_items.append(item_data)

        # Write the updated aggregated data back to file
        with open(AGGREGATED_FILE, "w", encoding="utf-8") as agg_file:
            json.dump(aggregated_items, agg_file, indent=4)
        print(f"Updated aggregated file: {AGGREGATED_FILE}")

    except Exception as e:
        print(f"Error saving item data: {e}")
