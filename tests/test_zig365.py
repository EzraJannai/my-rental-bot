import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rental_bot.scrapers import Zig365Scraper

DATA_DIR = Path(__file__).resolve().parent / "data"
SAMPLE = json.loads((DATA_DIR / "zig365_sample.json").read_text())["data"]

LOCATIONS = ["Apeldoorn", "Heerde", "Veessen", "Vaassen"]


def _scraper():
    return Zig365Scraper(
        api_host="natuurlijkhuren-aanbodapi.zig365.nl",
        site_base_url="https://www.natuurlijkhuren.nl",
        source="Triada",
        locations=LOCATIONS,
        max_price=1500,
    )


def test_zig365_keeps_only_residential_rentals_in_target_towns():
    listings = _scraper().parse_items(SAMPLE)
    # Only the Veessen rental survives: Koop, garage, Zwolle and the €2000
    # Vaassen home are all filtered out.
    assert len(listings) == 1
    listing = listings[0]
    assert listing["title"] == "Kerkstraat 23C"
    assert "Veessen" in listing["address"]
    assert listing["price"] == "€ 514.65"


def test_zig365_builds_detail_url():
    listing = _scraper().parse_items(SAMPLE)[0]
    assert listing["url"] == (
        "https://www.natuurlijkhuren.nl/aanbod/te-huur/details/770-kerkstraat-23-c-veessen"
    )


def test_zig365_without_location_filter_keeps_all_residential_rentals():
    scraper = Zig365Scraper(
        api_host="x",
        site_base_url="https://example.com",
        source="X",
        locations=None,
        max_price=None,
    )
    listings = scraper.parse_items(SAMPLE)
    # Koop and garage are still dropped; Veessen, Zwolle and Vaassen rentals stay.
    assert len(listings) == 3
