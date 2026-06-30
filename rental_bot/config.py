import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('rental_bot')

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "your_default_token")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "your_default_chat_id")

# Locations to search. Configurable via the LOCATIONS env var (comma separated)
# so the town list can change without code edits. Defaults to Apeldoorn plus the
# Triada region (Epe/Vaassen/Heerde and surrounding villages).
DEFAULT_LOCATIONS = "Apeldoorn,Epe,Vaassen,Heerde,Hattem,Wapenveld,Emst,Oene,Veessen"
LOCATIONS = [loc.strip() for loc in os.environ.get("LOCATIONS", DEFAULT_LOCATIONS).split(",") if loc.strip()]

PRICE_RANGE = os.environ.get("PRICE_RANGE", "0-1500")
# CITY kept as a backward-compatible alias (first location) for older imports.
CITY = os.environ.get("CITY", LOCATIONS[0] if LOCATIONS else "Apeldoorn")


def _parse_max_price(price_range: str):
    try:
        return int(price_range.split("-")[-1])
    except (ValueError, AttributeError):
        return None


PRICE_MAX = _parse_max_price(PRICE_RANGE)
