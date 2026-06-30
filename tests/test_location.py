import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rental_bot.location import address_matches, address_matches_any
from rental_bot.scrapers import ParariusScraper

TARGETS = ["Apeldoorn", "Epe", "Vaassen", "Heerde"]


def test_address_matches_by_town_name():
    assert address_matches("7311 JC Apeldoorn (Binnenstad)", "Apeldoorn")
    assert not address_matches("8014 VZ Zwolle (Ittersumerlanden)", "Apeldoorn")


def test_address_matches_by_postcode():
    # Ugchelen (7339) falls inside the Apeldoorn postal range.
    assert address_matches("7339 CH Ugchelen", "Apeldoorn")


def test_address_matches_word_boundary():
    # "Epe" must not match as a substring of another word.
    assert not address_matches("Eperweg 12, Heerde", "Epe")


def test_address_matches_any():
    assert address_matches_any("7202 DA Zutphen", TARGETS) is False
    assert address_matches_any("Dorpsstraat 3, Vaassen", TARGETS) is True


def test_location_filter_drops_fallback_results():
    scraper = ParariusScraper("http://example.com", source="Pararius", locations=TARGETS)
    raw = [
        {"address": "7311 JC Apeldoorn", "title": "Appartement"},
        {"address": "8014 VZ Zwolle", "title": "Woning"},
        {"address": "Koperweg", "title": "Vaassen, Koperweg"},  # town in title
    ]
    kept = scraper._filter_by_location(raw)
    assert len(kept) == 2
    addresses = {l["address"] for l in kept}
    assert "8014 VZ Zwolle" not in addresses
