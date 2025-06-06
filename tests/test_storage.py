import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rental_bot.storage import ListingStorage


def test_is_new_and_mark(tmp_path):
    storage_file = tmp_path / "storage.json"
    storage_file.write_text("")
    storage = ListingStorage(str(storage_file))
    test_id = "abc123"
    assert storage.is_new_listing(test_id) is True
    storage.mark_as_seen(test_id)
    assert storage.is_new_listing(test_id) is False




def test_update_with_listings_persist(tmp_path):
    storage_file = tmp_path / "listings.json"
    storage_file.write_text("[]")
    storage = ListingStorage(str(storage_file))
    listing = {"id": "xyz123"}
    storage.update_with_listings([listing])
    storage2 = ListingStorage(str(storage_file))
    assert storage2.is_new_listing(listing["id"]) is False
    assert listing["id"] in storage_file.read_text()
