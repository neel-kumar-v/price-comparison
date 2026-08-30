"""Deterministic Meijer steps."""

from __future__ import annotations

import time

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Meijer"
SEARCH_URL = "https://www.meijer.com/shopping/search.html?query={query}"

JS_MEIJER_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-testid=\"product-title\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[class*=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const inStock = /Add to Cart/i.test(text);
  return JSON.stringify({ title, price, inStock, url: location.href.split('?')[0] });
})()
"""


def _set_zip(browser: AgentBrowser, zip_code: str) -> None:
    browser.tab_new(f"https://www.meijer.com/shopping/store-locator.html?zip={zip_code}")
    time.sleep(2)


def fetch_meijer_listing(browser: AgentBrowser, reference: ProductReference, zip_code: str = "61801") -> RetailerListing:
    zip_code = reference.location_zip or zip_code
    reference = ProductReference(**{**reference.__dict__, "location_zip": zip_code})
    return fetch_listing(
        browser,
        RETAILER,
        SEARCH_URL,
        JS_MEIJER_PDP,
        reference,
        before_search=lambda b: _set_zip(b, zip_code),
    )
