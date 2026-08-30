#!/usr/bin/env python3
"""Validate a single retailer module against a fixture. Usage:
  python scripts/validate_retailer.py target general
  python scripts/validate_retailer.py bestbuy tech
  python scripts/validate_retailer.py aldi grocery --zip 61801
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from price_compare.browser import AgentBrowser
from price_compare.match import ProductReference, load_fixture

FETCHERS: dict[str, tuple[str, bool]] = {
    # mod_name -> (fixture_key, needs_zip)
    "target": ("general", False),
    "walmart": ("general", False),
    "amazon": ("general", False),
    "dicks": ("shoes", False),
    "footlocker": ("shoes", False),
    "finishline": ("shoes", False),
    "nike": ("shoes", False),
    "adidas": ("shoes", False),
    "bestbuy": ("tech", False),
    "bhphoto": ("tech", False),
    "apple": ("tech", False),
    "costco": ("tech", False),
    "aldi": ("grocery", True),
    "meijer": ("grocery", True),
    "schnucks": ("grocery", True),
    "wegmans": ("grocery", True),
    "acme": ("grocery", True),
    "shoprite": ("grocery", True),
    "instacart": ("grocery", True),
}

# Override fixture key per mod when category differs
FIXTURE_OVERRIDE: dict[str, str] = {
    "target_shoes": "shoes",
    "target_tech": "tech",
    "amazon_shoes": "shoes",
    "amazon_tech": "tech",
    "walmart_shoes": "shoes",
    "walmart_tech": "tech",
}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("retailer")
    parser.add_argument("category", nargs="?", default=None)
    parser.add_argument("--zip", default="61801")
    parser.add_argument("--fixture-key", default=None)
    args = parser.parse_args()

    mod_name = args.retailer.lower().replace("'", "").replace("&", "").replace(" ", "")
    if mod_name == "bh":
        mod_name = "bhphoto"
    if mod_name == "dicks":
        mod_name = "dicks"

    category = args.category
    if not category:
        for key in (mod_name, f"{mod_name}_{args.fixture_key}"):
            if key in FIXTURE_OVERRIDE:
                category = FIXTURE_OVERRIDE[key].split("_")[0] if "_" in key else None
        if mod_name in FETCHERS:
            fk, _ = FETCHERS[mod_name]
            category = fk

    fixture_key = args.fixture_key or category or "general"
    ref = load_fixture(str(ROOT / "tests/fixtures/products.json"), fixture_key)
    ref = ProductReference(**{**ref.__dict__, "category": category or ref.category})
    if FETCHERS.get(mod_name, (None, False))[1] or category == "grocery":
        ref = ProductReference(**{**ref.__dict__, "location_zip": args.zip})

    browser = AgentBrowser()
    browser.tab_list()  # warm connection

    import importlib

    mod = importlib.import_module(f"price_compare.retailers.{mod_name}")
    fetcher_name = f"fetch_{mod_name}_listing"
    if not hasattr(mod, fetcher_name):
        print(json.dumps({"ok": False, "error": f"No {fetcher_name} in {mod_name}"}))
        return 1

    fetcher = getattr(mod, fetcher_name)
    try:
        if FETCHERS.get(mod_name, (None, False))[1] or category == "grocery":
            listing = fetcher(browser, ref, args.zip)
        else:
            listing = fetcher(browser, ref)
        if listing is None:
            print(json.dumps({"ok": False, "error": "fetcher returned None"}))
            return 1
        ok = bool(listing.price) and listing.verification.get("same_product", False)
        out = {
            "ok": ok,
            "retailer": listing.retailer,
            "title": listing.title,
            "price": listing.price,
            "url": listing.url,
            "in_stock": listing.in_stock,
            "verification": listing.verification,
            "delivered_price": listing.delivered_price,
        }
        print(json.dumps(out, indent=2))
        # Close current tab after scrape
        try:
            browser.tab_close()
        except Exception:
            pass
        return 0 if ok else 1
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}))
        try:
            browser.tab_close()
        except Exception:
            pass
        return 1


if __name__ == "__main__":
    sys.exit(main())
