import os
import sys
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import ParariusScraper, HuurwoningenScraper, Wonen123Scraper

PARARIUS_HTML = """
<div class="search-list">
  <section class="search-list__item--listing">
    <div class="listing-search-item__content">
      <h2 class="listing-search-item__title">
        <a href="/listing-1">Nice Apt</a>
      </h2>
      <div class="listing-search-item__price">€1,000</div>
      <div class="listing-search-item__sub-title">Street 1</div>
    </div>
  </section>
</div>
"""

HUURWONINGEN_HTML = """
<div class="listing-search-item__content">
  <h2 class="listing-search-item__title"><a href="/woning-1">Home</a></h2>
  <div class="listing-search-item__price">€1,200</div>
  <div class="listing-search-item__sub-title">Street 2</div>
</div>
"""

WONEN123_HTML = """
<div class="pandlist-container" onclick="location.href='/detail/1';">
  <div class="pand-price">€1,300</div>
  <div class="pand-title">Nice Home <span class="pand-address">Street 3</span></div>
  <div class="pand-specs"><li>80 m2</li></div>
</div>
"""

def test_pararius_parse():
    scraper = ParariusScraper('http://example.com', source='Pararius')
    soup = BeautifulSoup(PARARIUS_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) == 1
    assert listings[0]['url'] == 'https://www.pararius.com/listing-1'

def test_huurwoningen_parse():
    scraper = HuurwoningenScraper('http://example.com', source='Huurwoningen')
    soup = BeautifulSoup(HUURWONINGEN_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) == 1
    assert listings[0]['url'] == 'https://www.huurwoningen.nl/woning-1'

def test_wonen123_parse():
    scraper = Wonen123Scraper('http://example.com', source='123Wonen')
    soup = BeautifulSoup(WONEN123_HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) == 1
    assert listings[0]['url'] == '/detail/1'
