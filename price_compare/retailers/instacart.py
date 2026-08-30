"""Instacart aggregator — delivered price with markup."""

from __future__ import annotations

import time

from ..browser import AgentBrowser
from ..match import ProductReference
from ..profile import WEGMANS_INSTACART_MARKUP, format_price, parse_shelf_price
from ._base import RetailerListing, build_listing, build_search_query, extract_pdp, find_listing_ref

RETAILER = "Instacart"

STORE_SLUGS = {
    "61801": "aldi",
    "19425": "wegmans",
}

JS_INSTACART_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-testid=\"product-name\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[data-testid=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const inStock = !/Out of stock|Unavailable/i.test(text);
  return JSON.stringify({ title, price, inStock, url: location.href.split('?')[0] });
})()
"""


def _open_store(browser: AgentBrowser, zip_code: str) -> None:
    store = STORE_SLUGS.get(zip_code, "aldi")
    browser.tab_new(f"https://www.instacart.com/store/{store}/storefront?zip={zip_code}")
    time.sleep(4)


def _instacart_search(browser: AgentBrowser, reference: ProductReference) -> None:
    query = build_search_query(reference)
    browser.eval_js(f"""
    (() => {{
      const input = document.querySelector('input[type=\"search\"], input[placeholder*=\"Search\"]');
      if (input) {{ input.value = '{query}'; input.dispatchEvent(new Event('input', {{bubbles:true}})); }}
    }})()
    """)
    time.sleep(4)
    snap = browser.snapshot_interactive_json()
    ref_link = find_listing_ref(snap, reference)
    if ref_link:
        browser.click(ref_link)
        time.sleep(3)


def fetch_instacart_listing(browser: AgentBrowser, reference: ProductReference, zip_code: str = "61801") -> RetailerListing:
    zip_code = reference.location_zip or zip_code
    reference = ProductReference(**{**reference.__dict__, "location_zip": zip_code})
    _open_store(browser, zip_code)
    _instacart_search(browser, reference)
    data = extract_pdp(browser, JS_INSTACART_PDP)
    listing = build_listing(RETAILER, reference, data)
    shelf = parse_shelf_price(listing.price)
    if shelf is not None:
        delivered = round(shelf * (1 + WEGMANS_INSTACART_MARKUP), 2)
        listing.delivered_price = format_price(delivered)
    return listing
