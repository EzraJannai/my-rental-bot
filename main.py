# main.py
import os
import requests
from bs4 import BeautifulSoup
import json
import time
import hashlib
import logging
from datetime import datetime
from typing import Dict, List, Set
from urllib.parse import quote_plus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger('rental_bot')

# Telegram Bot credentials (set these in GitHub Actions secrets)
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN", "your_default_token")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "your_default_chat_id")

# Define city and price range variables.
CITY = "Apeldoorn"
PRICE_RANGE = "0-1500"

##############################################
# Base Scraper Class
##############################################
class BaseScraper:
    def __init__(self, search_url: str, user_agent: str = None, source: str = "Unknown"):
        self.search_url = search_url
        self.source = source
        self.headers = {
            'User-Agent': user_agent or 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                                         'AppleWebKit/537.36 (KHTML, like Gecko) '
                                         'Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def fetch_page(self) -> str:
        logger.info(f"[{self.source}] Fetching page: {self.search_url}")
        response = requests.get(self.search_url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def fetch_listings(self) -> List[Dict]:
        try:
            page_content = self.fetch_page()
            soup = BeautifulSoup(page_content, 'html.parser')
            listings = self.parse_listings(soup)
            logger.info(f"[{self.source}] Parsed {len(listings)} listings")
            return listings
        except Exception as e:
            logger.error(f"[{self.source}] Error fetching listings: {e}")
            return []

    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        raise NotImplementedError("parse_listings must be implemented by the subclass")

    def generate_listing_id(self, url: str) -> str:
        return hashlib.md5((self.source + url).encode('utf-8')).hexdigest()

##############################################
# Pararius Scraper
##############################################
class ParariusScraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        seen_urls = set()
        search_list = soup.select('.search-list')
        if search_list:
            listing_elements = search_list[0].select('.search-list__item--listing')
        else:
            listing_elements = soup.select('.listing-search-item__content')
        
        for element in listing_elements:
            try:
                content = element.select_one('.listing-search-item__content') or element
                title_element = content.select_one('.listing-search-item__title a')
                if not title_element:
                    continue
                title = title_element.text.strip()
                relative_url = title_element.get('href', '')
                url = f"https://www.pararius.com{relative_url}" if relative_url else ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                price_element = content.select_one('.listing-search-item__price')
                address_element = content.select_one('.listing-search-item__sub-title')
                price = price_element.text.strip() if price_element else "Price not specified"
                address = address_element.text.strip() if address_element else "Address not specified"
                listing_id = self.generate_listing_id(url)
                listings.append({
                    'id': listing_id,
                    'title': title,
                    'url': url,
                    'price': price,
                    'address': address,
                    'source': self.source,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"[{self.source}] Error parsing a listing: {e}")
                continue
        
        return listings

##############################################
# Woonkeus Scraper (Using JSON API)
##############################################
class WoonkeusScraper(BaseScraper):
    def __init__(self, user_agent: str = None, source: str = "Woonkeus"):
        json_api_url = ("https://woonkeusstedendriehoekapi.hexia.io/api/v1/actueel-aanbod?"
                        "limit=60&locale=nl_NL&page=0&sort=-publicationDate")
        super().__init__(json_api_url, user_agent, source)

    def fetch_listings(self) -> List[Dict]:
        try:
            logger.info(f"[{self.source}] Fetching listings from JSON API: {self.search_url}")
            response = requests.get(self.search_url, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            items = data.get("data", [])
            listings = []
            for item in items:
                if item.get("gemeenteGeoLocatieNaam", "") != CITY:
                    continue
                street = item.get("street", "Unknown Street")
                house_number = item.get("houseNumber", "")
                house_number_addition = item.get("houseNumberAddition", "")
                full_street = f"{street} {house_number}{house_number_addition}".strip()
                city = item.get("gemeenteGeoLocatieNaam", "Unknown City")
                total_rent = item.get("totalRent", "Price not specified")
                url_key = item.get("urlKey", "")
                url = (f"https://www.woonkeus-stedendriehoek.nl/aanbod/nu-te-huur/huurwoningen/details/{url_key}"
                       if url_key else "")
                title = full_street
                address = f"{full_street}, {city}"
                listing_id = self.generate_listing_id(url)
                listings.append({
                    "id": listing_id,
                    "title": title,
                    "url": url,
                    "price": f"€ {total_rent}",
                    "address": address,
                    "source": self.source,
                    "timestamp": datetime.now().isoformat()
                })
            logger.info(f"[{self.source}] Parsed {len(listings)} listings from JSON")
            return listings
        except Exception as e:
            logger.error(f"[{self.source}] Error fetching listings from JSON API: {e}")
            return []

##############################################
# Nederwoon Scraper
##############################################
class NederwoonScraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        locations_container = soup.find(id="locations")
        if not locations_container:
            logger.warning(f"[{self.source}] No locations container found.")
            return listings

        location_elements = locations_container.find_all("div", class_="location")
        for loc in location_elements:
            try:
                second_col = loc.find("div", class_="col-lg-4 col-md-3 click-see-page-button")
                if not second_col:
                    continue
                title_elem = second_col.find("h2", class_="heading-sm")
                if not title_elem:
                    continue
                a_elem = title_elem.find("a", class_="see-page-button")
                if not a_elem:
                    continue
                title = a_elem.get_text(strip=True)
                relative_url = a_elem.get("href", "")
                url = relative_url if relative_url.startswith("http") else "https://www.nederwoon.nl" + relative_url
                address_elem = second_col.find("p", class_="color-medium fixed-lh")
                address = address_elem.get_text(strip=True) if address_elem else "Address not specified"
                third_col = loc.find("div", class_="col-lg-4 col-md-3 vertical-items start-items click-see-page-button")
                price_elem = third_col.find("p", class_="heading-md text-regular color-primary") if third_col else None
                price = price_elem.get_text(strip=True) if price_elem else "Price not specified"
                details_list = second_col.find("ul")
                details = ""
                if details_list:
                    detail_items = [li.get_text(strip=True) for li in details_list.find_all("li")]
                    details = " | ".join(detail_items)
                listing_id = self.generate_listing_id(url)
                listings.append({
                    "id": listing_id,
                    "title": title,
                    "url": url,
                    "price": price,
                    "address": address,
                    "details": details,
                    "source": self.source,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"[{self.source}] Error parsing a location: {e}")
                continue

        logger.info(f"[{self.source}] Parsed {len(listings)} listings")
        return listings

##############################################
# Huurwoningen Scraper
##############################################
class HuurwoningenScraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        listing_elements = soup.select('.listing-search-item__content')
        for element in listing_elements:
            try:
                title_element = element.select_one('h2.listing-search-item__title a')
                if not title_element:
                    continue
                title = title_element.get_text(strip=True)
                relative_url = title_element.get('href', '')
                url = relative_url if relative_url.startswith("http") else "https://www.huurwoningen.nl" + relative_url
                address_element = element.select_one('.listing-search-item__sub-title')
                address = address_element.get_text(strip=True) if address_element else "Address not specified"
                price_element = element.select_one('.listing-search-item__price')
                price = price_element.get_text(strip=True) if price_element else "Price not specified"
                listing_id = self.generate_listing_id(url)
                listings.append({
                    'id': listing_id,
                    'title': title,
                    'url': url,
                    'price': price,
                    'address': address,
                    'source': self.source,
                    'timestamp': datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"[{self.source}] Error parsing a listing: {e}")
                continue
        return listings

##############################################
# 123Wonen Scraper
##############################################
class Wonen123Scraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        listing_elements = soup.select("div.pandlist-container")
        for element in listing_elements:
            try:
                onclick_attr = element.get("onclick", "")
                if "location.href" not in onclick_attr:
                    continue
                url = onclick_attr.split("location.href=")[1].split(";")[0].strip().strip("'").strip('"')
                price_elem = element.find("div", class_="pand-price")
                price = price_elem.get_text(strip=True) if price_elem else "Price not specified"
                title_elem = element.find("div", class_="pand-title")
                if title_elem:
                    title = title_elem.get_text(" ", strip=True)
                else:
                    title = "Title not specified"
                address_elem = title_elem.find("span", class_="pand-address") if title_elem else None
                address = address_elem.get_text(strip=True) if address_elem else ""
                specs_elem = element.find("div", class_="pand-specs")
                details = ""
                if specs_elem:
                    li_items = specs_elem.find_all("li")
                    details = " | ".join([li.get_text(" ", strip=True) for li in li_items])
                listing_id = self.generate_listing_id(url)
                listings.append({
                    "id": listing_id,
                    "title": title,
                    "url": url,
                    "price": price,
                    "address": address,
                    "details": details,
                    "source": self.source,
                    "timestamp": datetime.now().isoformat()
                })
            except Exception as e:
                logger.error(f"[{self.source}] Error parsing a listing: {e}")
                continue
        
        logger.info(f"[{self.source}] Parsed {len(listings)} listings")
        return listings

##############################################
# Listing Storage
##############################################
class ListingStorage:
    def __init__(self, storage_file: str = 'seen_listings.json'):
        self.storage_file = storage_file
        self.seen_listings: Set[str] = set()
        self.load_seen_listings()
    
    def load_seen_listings(self) -> None:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, 'r') as f:
                    self.seen_listings = set(json.load(f))
                logger.info(f"Loaded {len(self.seen_listings)} previously seen listings")
            except Exception as e:
                logger.error(f"Error loading seen listings: {e}")
        else:
            logger.info("No existing storage file found, starting fresh")
    
    def save_seen_listings(self) -> None:
        try:
            with open(self.storage_file, 'w') as f:
                json.dump(list(self.seen_listings), f)
            logger.info(f"Saved {len(self.seen_listings)} listings to storage")
        except Exception as e:
            logger.error(f"Error saving seen listings: {e}")
    
    def is_new_listing(self, listing_id: str) -> bool:
        return listing_id not in self.seen_listings
    
    def mark_as_seen(self, listing_id: str) -> None:
        self.seen_listings.add(listing_id)
    
    def update_with_listings(self, listings: List[Dict]) -> None:
        for listing in listings:
            self.mark_as_seen(listing['id'])
        self.save_seen_listings()

##############################################
# Notification System with Telegram
##############################################
class NotificationSystem:
    def __init__(self, telegram_token: str, telegram_chat_id: str):
        self.telegram_token = telegram_token
        self.telegram_chat_id = telegram_chat_id
        self.notified_ids = set()
    
    def send_telegram_message(self, message: str) -> None:
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        payload = {"chat_id": self.telegram_chat_id, "text": message}
        try:
            response = requests.post(url, json=payload)
            response.raise_for_status()
            logger.info("Telegram notification sent successfully.")
        except Exception as e:
            logger.error(f"Error sending telegram message: {e}")
    
    def notify_new_listing(self, listing: Dict) -> None:
        if listing['id'] in self.notified_ids:
            return
        self.notified_ids.add(listing['id'])
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

##############################################
# Multi-Source Rental Bot
##############################################
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
        
        new_listings = [listing for listing in all_listings if self.storage.is_new_listing(listing['id'])]
        if new_listings:
            logger.info(f"Found {len(new_listings)} new listings across all sources")
            for listing in new_listings:
                self.notifier.notify_new_listing(listing)
        else:
            logger.info("No new listings found")
        
        self.storage.update_with_listings(all_listings)

def run_bot():
    """
    Standard Python entry point: build scrapers, run the bot, check for new listings.
    """
    pararius_url = f"https://www.pararius.com/apartments/{CITY.lower()}/{PRICE_RANGE}"
    huurwoningen_url = f"https://www.huurwoningen.nl/in/{CITY.lower()}/?price={PRICE_RANGE}"
    nederwoon_url = f"https://www.nederwoon.nl/search?search_type=1&city={quote_plus(CITY)}"
    wonen123_url = f"https://www.123wonen.nl/huurwoningen/in/{CITY.lower()}"

    pararius_scraper = ParariusScraper(pararius_url, source="Pararius")
    woonkeus_scraper = WoonkeusScraper(source="Woonkeus")
    huurwoningen_scraper = HuurwoningenScraper(huurwoningen_url, source="Huurwoningen")
    nederwoon_scraper = NederwoonScraper(nederwoon_url, source="Nederwoon")
    wonen123_scraper = Wonen123Scraper(wonen123_url, source="123Wonen")

    scrapers = [pararius_scraper, woonkeus_scraper, huurwoningen_scraper, nederwoon_scraper, wonen123_scraper]

    bot = MultiRentalBot(scrapers)
    bot.check_for_new_listings()

if __name__ == "__main__":
    run_bot()
