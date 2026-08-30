"""Deterministic Schnucks steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Schnucks"
SEARCH_URL = "https://schnucks.com/shop/search?q={query}"

JS_SCHNUCKS_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[class*=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const inStock = /Add to Cart/i.test(text);
  return JSON.stringify({ title, price, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_schnucks_listing(browser: AgentBrowser, reference: ProductReference, zip_code: str = "61801") -> RetailerListing:
    reference = ProductReference(**{**reference.__dict__, "location_zip": zip_code})
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_SCHNUCKS_PDP, reference)
