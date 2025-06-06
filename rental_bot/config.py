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
CITY = os.environ.get("CITY", "Apeldoorn")
PRICE_RANGE = os.environ.get("PRICE_RANGE", "0-1500")
