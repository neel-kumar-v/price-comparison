"""Deterministic Apple.com steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Apple"
SEARCH_URL = "https://www.apple.com/us/search/{query}?src=globalnav"

JS_APPLE_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-autom=\"productName\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[data-autom=\"price\"], .rc-prices-currentprice')?.textContent?.trim()
    || [...document.querySelectorAll('span')].map(e => e.textContent.trim()).find(t => /^From \\$|^\\$[\\d,]+/.test(t));
  const sku = text.match(/Model(?: Number)?:?\\s*([A-Z0-9/]+)/i)?.[1]
    || location.pathname.match(/\\/([A-Z0-9]+)\\//)?.[1];
  const inStock = /Add to Bag|Buy|Check Out/i.test(text);
  return JSON.stringify({ title, price, sku, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_apple_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_APPLE_PDP, reference)
