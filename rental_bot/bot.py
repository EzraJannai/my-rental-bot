"""Main bot orchestration."""
from typing import List
from urllib.parse import quote_plus

from .config import CITY, PRICE_RANGE, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN, logger
from .notification import NotificationSystem
from .scrapers import (
    BaseScraper,
    ParariusScraper,
    WoonkeusScraper,
    HuurwoningenScraper,
    NederwoonScraper,
    Wonen123Scraper,
)
from .storage import ListingStorage


class MultiRentalBot:
    def __init__(self, scrapers: List[BaseScraper]):
        self.scrapers = scrapers
        self.storage = ListingStorage()
        self.notifier = NotificationSystem(TELEGRAM_TOKEN, TELEGRAM_CHAT_ID)

    def check_for_new_listings(self) -> None:
        all_listings = []
        for scraper in self.scrapers:
            listings = scraper.fetch_listings()
            all_listings.extend(listings)

        new_listings = [listing for listing in all_listings if self.storage.is_new_listing(listing["id"])]
        if new_listings:
            logger.info(f"Found {len(new_listings)} new listings across all sources")
            for listing in new_listings:
                self.notifier.notify_new_listing(listing)
        else:
            logger.info("No new listings found")

        self.storage.update_with_listings(all_listings)


def run_bot() -> None:
    """Create scrapers and run the bot once."""
    pararius_url = f"https://www.pararius.com/apartments/{CITY.lower()}/{PRICE_RANGE}"
    huurwoningen_url = f"https://www.huurwoningen.nl/in/{CITY.lower()}/?price={PRICE_RANGE}"
    nederwoon_url = f"https://www.nederwoon.nl/search?search_type=1&city={quote_plus(CITY)}"
    wonen123_url = f"https://www.123wonen.nl/huurwoningen/in/{CITY.lower()}"

    scrapers = [
        ParariusScraper(pararius_url, source="Pararius"),
        WoonkeusScraper(source="Woonkeus"),
        HuurwoningenScraper(huurwoningen_url, source="Huurwoningen"),
        NederwoonScraper(nederwoon_url, source="Nederwoon"),
        Wonen123Scraper(wonen123_url, source="123Wonen"),
    ]

    bot = MultiRentalBot(scrapers)
    bot.check_for_new_listings()
