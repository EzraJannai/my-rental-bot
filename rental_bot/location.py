"""Helpers to decide whether a listing actually belongs to a target town.

Some sites (notably Pararius) fall back to a wider regional search when a small
village isn't a recognised location, returning listings from other towns. We
filter parsed listings against the target locations so users don't get e.g.
Deventer results under a "Vaassen" search.
"""
import re
from typing import Iterable

# 4-digit postal-code ranges per town (inclusive). Used as a backup signal when
# the town name itself isn't spelled out in the address string.
TOWN_POSTCODES = {
    "apeldoorn": [(7300, 7349)],
    "epe": [(8160, 8166)],
    "emst": [(8166, 8166)],
    "oene": [(8167, 8167)],
    "vaassen": [(8170, 8172)],
    "heerde": [(8180, 8186)],
    "veessen": [(8194, 8194)],
    "wapenveld": [(8190, 8196)],
    "hattem": [(8050, 8056)],
}

_POSTCODE_RE = re.compile(r"\b(\d{4})\s?[A-Za-z]{2}\b|\b(\d{4})\b")


def _postcodes_in(address: str):
    for m in _POSTCODE_RE.finditer(address):
        code = m.group(1) or m.group(2)
        if code:
            yield int(code)


def address_matches(address: str, town: str) -> bool:
    """True if `address` plausibly lies in `town` (by name or postal code)."""
    if not address or not town:
        return False
    town_l = town.strip().lower()
    address_l = address.lower()
    # Word-boundary name match avoids false hits (e.g. "Epe" inside another word).
    if re.search(rf"\b{re.escape(town_l)}\b", address_l):
        return True
    ranges = TOWN_POSTCODES.get(town_l)
    if ranges:
        for code in _postcodes_in(address):
            if any(low <= code <= high for low, high in ranges):
                return True
    return False


def address_matches_any(address: str, towns: Iterable[str]) -> bool:
    """True if `address` matches any of the target `towns`."""
    return any(address_matches(address, town) for town in towns)
