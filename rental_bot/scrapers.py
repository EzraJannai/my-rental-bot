"""Scraper classes for various rental websites."""
from datetime import datetime
from typing import Dict, List
import hashlib

import requests
from bs4 import BeautifulSoup

from .config import CITY, logger


class BaseScraper:
    """Base class for all scrapers."""

    def __init__(self, search_url: str, user_agent: str = None, source: str = "Unknown"):
        self.search_url = search_url
        self.source = source
        self.headers = {
            "User-Agent": user_agent
            or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/91.0.4472.124 Safari/537.36"
        }

    def fetch_page(self) -> str:
        logger.info(f"[{self.source}] Fetching page: {self.search_url}")
        response = requests.get(self.search_url, headers=self.headers)
        response.raise_for_status()
        return response.text

    def fetch_listings(self) -> List[Dict]:
        try:
            page_content = self.fetch_page()
            soup = BeautifulSoup(page_content, "html.parser")
            listings = self.parse_listings(soup)
            logger.info(f"[{self.source}] Parsed {len(listings)} listings")
            return listings
        except Exception as exc:  # pragma: no cover - network errors
            logger.error(f"[{self.source}] Error fetching listings: {exc}")
            return []

    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        raise NotImplementedError

    def generate_listing_id(self, url: str) -> str:
        return hashlib.md5((self.source + url).encode("utf-8")).hexdigest()


class ParariusScraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        seen_urls = set()
        search_list = soup.select(".search-list")
        if search_list:
            listing_elements = search_list[0].select(".search-list__item--listing")
        else:
            listing_elements = soup.select(".listing-search-item__content")

        for element in listing_elements:
            try:
                content = element.select_one(".listing-search-item__content") or element
                title_element = content.select_one(".listing-search-item__title a")
                if not title_element:
                    continue
                title = title_element.text.strip()
                relative_url = title_element.get("href", "")
                url = f"https://www.pararius.com{relative_url}" if relative_url else ""
                if not url or url in seen_urls:
                    continue
                seen_urls.add(url)
                price_element = content.select_one(".listing-search-item__price")
                address_element = content.select_one(".listing-search-item__sub-title")
                price = price_element.text.strip() if price_element else "Price not specified"
                address = address_element.text.strip() if address_element else "Address not specified"
                listing_id = self.generate_listing_id(url)
                listings.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "url": url,
                        "price": price,
                        "address": address,
                        "source": self.source,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as exc:  # pragma: no cover - parsing errors
                logger.error(f"[{self.source}] Error parsing a listing: {exc}")
                continue
        return listings


class WoonkeusScraper(BaseScraper):
    def __init__(self, user_agent: str = None, source: str = "Woonkeus"):
        json_api_url = (
            "https://woonkeusstedendriehoekapi.hexia.io/api/v1/actueel-aanbod?"
            "limit=60&locale=nl_NL&page=0&sort=-publicationDate"
        )
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
                url = (
                    f"https://www.woonkeus-stedendriehoek.nl/aanbod/nu-te-huur/huurwoningen/details/{url_key}"
                    if url_key
                    else ""
                )
                title = full_street
                address = f"{full_street}, {city}"
                listing_id = self.generate_listing_id(url)
                listings.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "url": url,
                        "price": f"€ {total_rent}",
                        "address": address,
                        "source": self.source,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            logger.info(f"[{self.source}] Parsed {len(listings)} listings from JSON")
            return listings
        except Exception as exc:  # pragma: no cover - network errors
            logger.error(f"[{self.source}] Error fetching listings from JSON API: {exc}")
            return []


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
                if not relative_url:
                    continue
                url = relative_url if relative_url.startswith("http") else "https://www.nederwoon.nl" + relative_url
                address_elem = second_col.find("p", class_="color-medium fixed-lh")
                address = address_elem.get_text(strip=True) if address_elem else "Address not specified"
                third_col = loc.find("div", class_="col-lg-4 col-md-3 vertical-items start-items click-see-page-button")
                price_elem = (
                    third_col.find("p", class_="heading-md text-regular color-primary") if third_col else None
                )
                price = price_elem.get_text(strip=True) if price_elem else "Price not specified"
                details_list = second_col.find("ul")
                details = ""
                if details_list:
                    detail_items = [li.get_text(strip=True) for li in details_list.find_all("li")]
                    details = " | ".join(detail_items)
                listing_id = self.generate_listing_id(url)
                listings.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "url": url,
                        "price": price,
                        "address": address,
                        "details": details,
                        "source": self.source,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as exc:  # pragma: no cover - parsing errors
                logger.error(f"[{self.source}] Error parsing a location: {exc}")
                continue
        logger.info(f"[{self.source}] Parsed {len(listings)} listings")
        return listings


class HuurwoningenScraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        listing_elements = soup.select(".listing-search-item__content")
        for element in listing_elements:
            try:
                title_element = element.select_one("h2.listing-search-item__title a")
                if not title_element:
                    continue
                title = title_element.get_text(strip=True)
                relative_url = title_element.get("href", "")
                url = (
                    relative_url
                    if relative_url.startswith("http")
                    else "https://www.huurwoningen.nl" + relative_url
                )
                address_element = element.select_one(".listing-search-item__sub-title")
                address = address_element.get_text(strip=True) if address_element else "Address not specified"
                price_element = element.select_one(".listing-search-item__price")
                price = price_element.get_text(strip=True) if price_element else "Price not specified"
                listing_id = self.generate_listing_id(url)
                listings.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "url": url,
                        "price": price,
                        "address": address,
                        "source": self.source,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as exc:  # pragma: no cover - parsing errors
                logger.error(f"[{self.source}] Error parsing a listing: {exc}")
                continue
        return listings


class Wonen123Scraper(BaseScraper):
    def parse_listings(self, soup: BeautifulSoup) -> List[Dict]:
        listings = []
        listing_elements = soup.select("div.pandlist-container")
        for element in listing_elements:
            try:
                onclick_attr = element.get("onclick", "")
                if "location.href" not in onclick_attr:
                    continue
                url = (
                    onclick_attr.split("location.href=")[1]
                    .split(";")[0]
                    .strip()
                    .strip("'")
                    .strip('"')
                )
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
                listings.append(
                    {
                        "id": listing_id,
                        "title": title,
                        "url": url,
                        "price": price,
                        "address": address,
                        "details": details,
                        "source": self.source,
                        "timestamp": datetime.now().isoformat(),
                    }
                )
            except Exception as exc:  # pragma: no cover - parsing errors
                logger.error(f"[{self.source}] Error parsing a listing: {exc}")
                continue
        logger.info(f"[{self.source}] Parsed {len(listings)} listings")
        return listings
