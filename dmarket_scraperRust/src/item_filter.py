# src/item_filter.py

import os
import json
import logging
import statistics
from datetime import datetime, timedelta
from collections import defaultdict
import unicodedata

# Updated thresholds per the new requirements
MIN_SALES_NORMAL = 15  # At least 15 sales for normal (high-volume) activity
MIN_SALES_EXCEPTION = 7  # Items with fewer than 7 sales in a month are immediately bad
PRICE_CONSISTENCY_THRESHOLD_STRICT = 1.20  # For higher-priced items (average >= $5)
PRICE_CONSISTENCY_THRESHOLD_LOW_PRICE = 4.2  # For low-priced items (average < $5)
MIN_TARGET_RATIO = (
    0.35  # At least 35% of sale history operations should be target operations
)
MIN_OFFER_RATIO = (
    0.45  # At least 45% of sale history operations should be offer operations
)

# Profit margin factors (for override checks)
PROFIT_MARGIN_NORMAL = (
    1.15  # 15% profit margin for items with at least 15 sales in 30 days
)
PROFIT_MARGIN_EXCEPTION = (
    1.30  # 30% profit margin for items with at least 7 sales in 30 days
)

logging.basicConfig(level=logging.DEBUG)


def clean_name(name):
    """
    Cleans the item name by attempting to fix mis-encoded text and removing unwanted symbols.
    For example, if a name appears as "StatTrakâ¢ M249 | Magma", this function will:
      - Detect the mis-encoding (e.g., presence of "â")
      - Attempt to re-encode from Latin-1 to UTF-8
      - Remove the trademark symbol (™)
    The final output will be "StatTrak M249 | Magma".
    """
    if not name:
        return ""
    try:
        # If mis-encoded artifact exists, try re-encoding from Latin-1 to UTF-8.
        if "â" in name:
            try:
                name_fixed = name.encode("latin1").decode("utf-8")
            except Exception:
                name_fixed = name
        else:
            name_fixed = name

        # Remove trademark symbols and unwanted characters.
        name_fixed = name_fixed.replace("™", "")
        # Normalize and remove extra whitespace.
        name_fixed = unicodedata.normalize("NFKC", name_fixed)
        name_fixed = " ".join(name_fixed.split())
        return name_fixed
    except Exception as e:
        logging.error("Error cleaning name '%s': %s", name, e)
        return name


def base_name(name):
    """
    Returns the base name of an item by removing a trailing " MINE" if present.
    For example, "Sticker | Twistzz (Glitter) | Shanghai 2024 MINE" returns
    "Sticker | Twistzz (Glitter) | Shanghai 2024".
    """
    if name.endswith(" MINE"):
        return name[: -len(" MINE")].strip()
    return name


def parse_date(date_str):
    """
    Attempts to parse a date string using several common formats.
    Returns a datetime object if parsing succeeds, or None otherwise.
    """
    date_formats = [
        "%Y-%m-%d %H:%M:%S",  # e.g. "2025-02-03 14:30:00"
        "%Y-%m-%d",  # e.g. "2025-02-03"
        "%b %d, %Y, %I:%M %p",  # e.g. "Feb 03, 2025, 06:46 PM"
        "%b %d, %Y at %I:%M %p",  # e.g. "Mar 09, 2025 at 04:02 PM"
    ]
    for fmt in date_formats:
        try:
            return datetime.strptime(date_str, fmt)
        except Exception:
            continue
    logging.error(
        "Error parsing date: time data '%s' does not match any expected format",
        date_str,
    )
    return None


def transform_item(raw_item):
    """
    Transforms a raw item into the expected format and calculates metrics.
      - The 'name' and 'wear' keys are added.
      - Only sales from the last 30 days (starting from today) are counted.
      - 'offer_prices_list' is reduced to the lowest 3 offers and its quantity.
      - 'target_price_list' is reduced to the highest 3 target prices and its quantity.
      - Calculates profit margins for:
            Pair 1: (first lowest offer / first highest target)
            Pair 2: (second lowest offer / second highest target)
          When there is no first/second offer or target, a default value of 0.01 is used.
    """
    transformed = {}
    # Clean the name.
    raw_name = raw_item.get("name", "")
    transformed["name"] = clean_name(raw_name)
    transformed["wear"] = raw_item.get("wear", "")  # Add wear attribute

    try:
        # Process recent sales from the last 30 days.
        sales_history = raw_item.get("sales_history", [])
        thirty_days_ago = datetime.now() - timedelta(days=30)
        recent_sales_data = []
        monthly_sales = 0
        for sh in sales_history:
            if sh.get("price"):
                try:
                    price = float(sh.get("price", "0").replace("$", "").strip())
                except Exception as e:
                    logging.error(
                        "Error parsing price for sale in item %s: %s",
                        transformed["name"],
                        e,
                    )
                    continue

                date_time = sh.get("date_time")
                if not date_time:
                    date_value = sh.get("date")
                    time_value = sh.get("time")
                    if date_value and time_value:
                        date_time = f"{date_value} {time_value}"
                    else:
                        date_time = sh.get("date")

                sale_date = parse_date(date_time)
                if not sale_date:
                    continue

                if sale_date >= thirty_days_ago:
                    monthly_sales += 1
                    sale_info = {
                        "price": price,
                        "date_time": date_time,
                        "operation": sh.get("operation"),
                    }
                    recent_sales_data.append(sale_info)
        transformed["sales"] = monthly_sales
        transformed["recent_sales_prices"] = recent_sales_data

        recent_prices = [sale["price"] for sale in recent_sales_data]

        # Process offer prices.
        offer_prices = raw_item.get("offer_prices", [])
        full_offer_list = [
            float(op.get("price", "0").replace("$", "").strip())
            for op in offer_prices
            if op.get("price")
        ]
        sorted_offers = sorted(full_offer_list)
        lowest_offers = sorted_offers[:3]
        transformed["offer_prices_list"] = lowest_offers
        transformed["offer_prices_quantity"] = len(lowest_offers)

        # Process target prices.
        target_prices = raw_item.get("target_prices", [])
        full_target_list = [
            float(tp.get("price", "0").replace("$", "").strip())
            for tp in target_prices
            if tp.get("price")
        ]
        sorted_targets = sorted(full_target_list, reverse=True)
        highest_targets = sorted_targets[:3]
        transformed["target_price_list"] = highest_targets
        transformed["target_price_list_quantity"] = len(highest_targets)

        # Calculate profit margins.
        offer1 = lowest_offers[0] if len(lowest_offers) >= 1 else 0.01
        target1 = highest_targets[0] if len(highest_targets) >= 1 else 0.01
        margin_pair1 = offer1 / target1
        transformed["profit_margin_pair1"] = margin_pair1
        logging.debug(
            "Item %s: Profit margin pair1 = %.4f", transformed["name"], margin_pair1
        )

        offer2 = lowest_offers[1] if len(lowest_offers) >= 2 else 0.01
        target2 = highest_targets[1] if len(highest_targets) >= 2 else 0.01
        margin_pair2 = offer2 / target2
        transformed["profit_margin_pair2"] = margin_pair2
        logging.debug(
            "Item %s: Profit margin pair2 = %.4f", transformed["name"], margin_pair2
        )

        if recent_prices:
            transformed["average_recent_sale_price"] = statistics.mean(recent_prices)
            transformed["price_variance"] = (
                statistics.variance(recent_prices) if len(recent_prices) > 1 else 0.0
            )
        else:
            transformed["average_recent_sale_price"] = 0.0
            transformed["price_variance"] = 0.0

    except Exception as e:
        logging.error(
            "Error transforming item %s: %s", transformed.get("name", "unknown"), e
        )
    return transformed


def is_price_consistent(prices):
    """
    Checks if recent sale prices are consistent.
    For items with a low average price (< $5), a higher threshold is allowed.
    """
    if not prices or min(prices) == 0:
        return False
    ratio = max(prices) / min(prices)
    avg_price = statistics.mean(prices)
    threshold = (
        PRICE_CONSISTENCY_THRESHOLD_LOW_PRICE
        if avg_price < 5.0
        else PRICE_CONSISTENCY_THRESHOLD_STRICT
    )
    return ratio <= threshold


def is_good_candidate(item):
    """
    Determines if the item is a good candidate.
    - If the item has fewer than 7 sales in the last 30 days, it is immediately bad.
    - Otherwise, if the item has valid offer and target price lists, it is considered good.
    """
    sales = item.get("sales", 0)
    if sales < MIN_SALES_EXCEPTION:
        logging.debug(
            "Item %s has only %d sales (< %d). Marking as bad candidate.",
            item.get("name"),
            sales,
            MIN_SALES_EXCEPTION,
        )
        return False

    if not item.get("offer_prices_list") or not item.get("target_price_list"):
        logging.debug(
            "Item %s missing offer or target price list (offer_qty: %d, target_qty: %d)",
            item.get("name"),
            len(item.get("offer_prices_list", [])),
            len(item.get("target_price_list", [])),
        )
        return False

    logging.debug(
        "Item %s qualifies as a good candidate with %d sales.", item.get("name"), sales
    )
    return True


def passes_profit_margin(item):
    """
    Checks if at least one of the profit margin pairs meets the required threshold.
    This override is only considered if the item has at least 7 sales.
    """
    sales = item.get("sales", 0)
    if sales < MIN_SALES_EXCEPTION:
        return False
    factor = (
        PROFIT_MARGIN_NORMAL if sales >= MIN_SALES_NORMAL else PROFIT_MARGIN_EXCEPTION
    )
    pm1 = item.get("profit_margin_pair1")
    pm2 = item.get("profit_margin_pair2")
    if (pm1 is not None and pm1 >= factor) or (pm2 is not None and pm2 >= factor):
        logging.debug(
            "Item %s passes profit margin check (pm1: %s, pm2: %s, required factor: %.2f)",
            item.get("name"),
            pm1,
            pm2,
            factor,
        )
        return True
    return False


def load_items(data_dir):
    aggregated_file = os.path.join(data_dir, "aggregated", "items_all.json")
    try:
        with open(aggregated_file, "r", encoding="utf-8") as f:
            raw_items = json.load(f)
        items = [transform_item(item) for item in raw_items]
        return items
    except Exception as e:
        logging.error("Error reading aggregated file %s: %s", aggregated_file, e)
        return []


def save_items(items, filepath, ndjson=False):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            if ndjson:
                for item in items:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            else:
                json.dump(items, f, indent=4, ensure_ascii=False)
        logging.info("Successfully saved items to %s", filepath)
    except Exception as e:
        logging.error("Error saving items to %s: %s", filepath, e)


def main():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_directory = os.path.join(base_dir, "data")
    items = load_items(data_directory)

    # Group items by base name (remove trailing " MINE" for grouping)
    groups = defaultdict(list)
    for item in items:
        name_clean = clean_name(item.get("name", ""))
        base = base_name(name_clean)
        groups[base].append(item)

    good_items = []
    bad_items = []

    for base, group in groups.items():
        # Separate items that have " MINE" at the end from those that don't.
        mine_items = [item for item in group if item.get("name", "").endswith(" MINE")]
        non_mine_items = [
            item for item in group if not item.get("name", "").endswith(" MINE")
        ]

        # Prefer non-MINE items as candidates for good_items.
        candidate = None
        for item in non_mine_items:
            if is_good_candidate(item) or passes_profit_margin(item):
                candidate = {"name": item.get("name"), "wear": item.get("wear")}
                break
        if candidate:
            good_items.append(candidate)
        else:
            # If no non-MINE candidate qualifies, treat all items in the group as bad.
            for item in group:
                bad_items.append({"name": item.get("name"), "wear": item.get("wear")})
            continue

        # Regardless, if there are items with " MINE" in the name, add them to bad_items.
        for item in mine_items:
            bad_items.append({"name": item.get("name"), "wear": item.get("wear")})

    aggregated_dir = os.path.join(data_directory, "aggregated")
    os.makedirs(aggregated_dir, exist_ok=True)
    good_filepath = os.path.join(aggregated_dir, "good_items.json")
    bad_filepath = os.path.join(aggregated_dir, "bad_items.json")
    save_items(good_items, good_filepath, ndjson=False)
    save_items(bad_items, bad_filepath, ndjson=False)

    logging.info(
        "Filtering complete: %d good items, %d bad items saved.",
        len(good_items),
        len(bad_items),
    )


if __name__ == "__main__":
    main()
