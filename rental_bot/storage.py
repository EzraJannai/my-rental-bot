"""Persistence for seen listings."""
import json
import os
from typing import Dict, List, Set

from .config import logger


class ListingStorage:
    def __init__(self, storage_file: str = "seen_listings.json"):
        self.storage_file = storage_file
        self.seen_listings: Set[str] = set()
        self.load_seen_listings()

    def load_seen_listings(self) -> None:
        if os.path.exists(self.storage_file):
            try:
                with open(self.storage_file, "r") as f:
                    self.seen_listings = set(json.load(f))
                logger.info(f"Loaded {len(self.seen_listings)} previously seen listings")
            except Exception as exc:  # pragma: no cover - file errors
                logger.error(f"Error loading seen listings: {exc}")
        else:
            logger.info("No existing storage file found, starting fresh")

    def save_seen_listings(self) -> None:
        try:
            with open(self.storage_file, "w") as f:
                json.dump(list(self.seen_listings), f)
            logger.info(f"Saved {len(self.seen_listings)} listings to storage")
        except Exception as exc:  # pragma: no cover - file errors
            logger.error(f"Error saving seen listings: {exc}")

    def is_new_listing(self, listing_id: str) -> bool:
        return listing_id not in self.seen_listings

    def mark_as_seen(self, listing_id: str) -> None:
        self.seen_listings.add(listing_id)

    def update_with_listings(self, listings: List[Dict]) -> None:
        for listing in listings:
            self.mark_as_seen(listing["id"])
        self.save_seen_listings()
