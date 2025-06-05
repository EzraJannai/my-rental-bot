import os
import sys
import pytest
from bs4 import BeautifulSoup

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from main import NederwoonScraper

# HTML snippet with one listing missing href and one valid listing
HTML = '''
<div id="locations">
  <div class="location">
    <div class="col-lg-4 col-md-3 click-see-page-button">
      <h2 class="heading-sm"><a class="see-page-button" href="">No URL</a></h2>
      <p class="color-medium fixed-lh">Bad Address</p>
    </div>
    <div class="col-lg-4 col-md-3 vertical-items start-items click-see-page-button">
      <p class="heading-md text-regular color-primary">€1,000</p>
    </div>
  </div>
  <div class="location">
    <div class="col-lg-4 col-md-3 click-see-page-button">
      <h2 class="heading-sm"><a class="see-page-button" href="/valid-path">Valid Listing</a></h2>
      <p class="color-medium fixed-lh">Valid Address</p>
    </div>
    <div class="col-lg-4 col-md-3 vertical-items start-items click-see-page-button">
      <p class="heading-md text-regular color-primary">€1,500</p>
    </div>
  </div>
</div>
'''

def test_skip_listing_without_href():
    scraper = NederwoonScraper('http://example.com', source='Nederwoon')
    soup = BeautifulSoup(HTML, 'html.parser')
    listings = scraper.parse_listings(soup)
    assert len(listings) == 1
    assert listings[0]['url'] == 'https://www.nederwoon.nl/valid-path'

