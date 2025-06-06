import os
import sys
from pathlib import Path
import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rental_bot.scrapers import NederwoonScraper

DATA_DIR = Path(__file__).resolve().parent / "data"
HTML = (DATA_DIR / "nederwoon_sample.html").read_text()

def test_skip_listing_without_href():
    scraper = NederwoonScraper('http://example.com', source='Nederwoon')
    soup = BeautifulSoup(HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) > 0
    assert listings[0]['url'].startswith('https://www.nederwoon.nl')

