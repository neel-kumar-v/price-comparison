"""Deterministic Foot Locker steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, discover_listing, fetch_listing

RETAILER = "Foot Locker"
SEARCH_URL = "https://www.footlocker.com/search?query={query}"

JS_FOOTLOCKER_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-testid=\"product-name\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[data-testid=\"product-price\"], .ProductPrice, span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const styleCode = text.match(/Style[\\s:#]*([A-Z0-9-]+)/i)?.[1] || location.pathname.match(/product\\/([\\w-]+)/)?.[1];
  const inStock = /Add To Bag|Add to Cart/i.test(text);
  return JSON.stringify({ title, price, styleCode, sku: styleCode, inStock, url: location.href.split('?')[0] });
})()
"""


def discover_footlocker(browser: AgentBrowser, query: str, category: str = "shoes") -> ProductReference:
    return discover_listing(browser, query, category, SEARCH_URL, JS_FOOTLOCKER_PDP)


def fetch_footlocker_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_FOOTLOCKER_PDP, reference)
