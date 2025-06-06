import os
import sys
from pathlib import Path
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from rental_bot.scrapers import ParariusScraper, HuurwoningenScraper, Wonen123Scraper

DATA_DIR = Path(__file__).resolve().parent / "data"

PARARIUS_HTML = (DATA_DIR / "pararius_sample.html").read_text()
HUURWONINGEN_HTML = (DATA_DIR / "huurwoningen_sample.html").read_text()
WONEN123_HTML = (DATA_DIR / "123wonen_sample.html").read_text()

def test_pararius_parse():
    scraper = ParariusScraper('http://example.com', source='Pararius')
    soup = BeautifulSoup(PARARIUS_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) > 0
    assert listings[0]['url'].startswith('https://www.pararius.com')

def test_huurwoningen_parse():
    scraper = HuurwoningenScraper('http://example.com', source='Huurwoningen')
    soup = BeautifulSoup(HUURWONINGEN_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) > 0
    assert listings[0]['url'].startswith('https://www.huurwoningen.nl')

def test_wonen123_parse():
    scraper = Wonen123Scraper('http://example.com', source='123Wonen')
    soup = BeautifulSoup(WONEN123_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) > 0
    assert listings[0]['url'].startswith('https://www.123wonen.nl')
