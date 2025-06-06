"""Telegram notification helpers."""
import requests
from typing import Dict

from .config import logger


class NotificationSystem:
    def __init__(self, telegram_token: str, telegram_chat_id: str):
        self.telegram_token = telegram_token
        if isinstance(telegram_chat_id, str):
            self.telegram_chat_ids = [cid.strip() for cid in telegram_chat_id.split(",") if cid.strip()]
        else:
            self.telegram_chat_ids = telegram_chat_id
        self.notified_ids = set()

    def send_telegram_message(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        for chat_id in self.telegram_chat_ids:
            payload = {"chat_id": chat_id, "text": message}
            try:
                response = requests.post(url, json=payload)
                response.raise_for_status()
                logger.info(f"Telegram notification sent successfully to chat id: {chat_id}.")
            except Exception as exc:  # pragma: no cover - network errors
                logger.error(f"Error sending telegram message to chat id {chat_id}: {exc}")

    def notify_new_listing(self, listing: Dict) -> None:
        if listing["id"] in self.notified_ids:
            return
        self.notified_ids.add(listing["id"])
        message = (
            f"NEW LISTING FOUND [{listing['source']}]:\n"
            f"Title: {listing['title']}\n"
            f"Price: {listing['price']}\n"
            f"Address: {listing['address']}\n"
            f"URL: {listing['url']}"
        )
        self.send_telegram_message(message)
        print("\n" + "=" * 50)
        print(message)
        print("=" * 50 + "\n")
