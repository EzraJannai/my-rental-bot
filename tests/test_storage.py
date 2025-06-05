import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from main import ListingStorage


def test_is_new_and_mark(tmp_path):
    storage_file = tmp_path / "storage.json"
    storage_file.write_text("")
    storage = ListingStorage(str(storage_file))
    test_id = "abc123"
    assert storage.is_new_listing(test_id) is True
    storage.mark_as_seen(test_id)
    assert storage.is_new_listing(test_id) is False

