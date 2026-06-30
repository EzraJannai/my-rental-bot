"""Main bot orchestration."""
from typing import List
from urllib.parse import quote_plus

from .config import (
    LOCATIONS,
    PRICE_MAX,
    PRICE_RANGE,
    TELEGRAM_CHAT_ID,
    TELEGRAM_TOKEN,
    logger,
)
from .notification import NotificationSystem
from .scrapers import (
    BaseScraper,
    ParariusScraper,
    HuurwoningenScraper,
    NederwoonScraper,
    Wonen123Scraper,
    Zig365Scraper,
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


def _location_scrapers(location: str) -> List[BaseScraper]:
    """Build the URL-based scrapers for a single town.

    Pararius and Huurwoningen fall back to a wider region for small villages, so
    every scraper is given `locations=LOCATIONS` to filter the parsed results
    back down to the towns we actually want.
    """
    slug = location.lower()
    return [
        ParariusScraper(
            f"https://www.pararius.com/apartments/{slug}/{PRICE_RANGE}",
            source="Pararius",
            locations=LOCATIONS,
        ),
        HuurwoningenScraper(
            f"https://www.huurwoningen.nl/in/{slug}/?price={PRICE_RANGE}",
            source="Huurwoningen",
            locations=LOCATIONS,
        ),
        NederwoonScraper(
            f"https://www.nederwoon.nl/search?search_type=1&city={quote_plus(location)}",
            source="Nederwoon",
            locations=LOCATIONS,
        ),
        Wonen123Scraper(
            f"https://www.123wonen.nl/huurwoningen/in/{slug}",
            source="123Wonen",
            locations=LOCATIONS,
        ),
    ]


def run_bot() -> None:
    """Create scrapers for every configured location and run the bot once."""
    scrapers: List[BaseScraper] = []
    for location in LOCATIONS:
        scrapers.extend(_location_scrapers(location))

    # Social-housing platforms on zig365/hexia. One JSON call per tenant covers
    # its whole region; results are filtered to LOCATIONS by city/municipality.
    scrapers.extend(
        [
            Zig365Scraper(
                api_host="natuurlijkhuren-aanbodapi.zig365.nl",
                site_base_url="https://www.natuurlijkhuren.nl",
                source="Triada (NatuurlijkHuren)",
                locations=LOCATIONS,
                max_price=PRICE_MAX,
            ),
            Zig365Scraper(
                api_host="woonkeusstedendriehoek-aanbodapi.zig365.nl",
                site_base_url="https://www.woonkeus-stedendriehoek.nl",
                source="Woonkeus",
                locations=LOCATIONS,
                max_price=PRICE_MAX,
                detail_path="/aanbod/nu-te-huur/huurwoningen/details/",
            ),
        ]
    )

    bot = MultiRentalBot(scrapers)
    bot.check_for_new_listings()
