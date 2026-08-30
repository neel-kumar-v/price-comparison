"""Deterministic B&H Photo steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "B&H"
SEARCH_URL = "https://www.bhphotovideo.com/c/search?q={query}&sts=ma"

JS_BH_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-selenium=\"productTitle\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[data-selenium=\"pricingPrice\"]')?.textContent?.trim()
    || [...document.querySelectorAll('span')].map(e => e.textContent.trim()).find(t => /^\\$[\\d,]+\\.\\d{2}$/.test(t));
  const sku = text.match(/Mfr(?:\\s#)?:?\\s*([A-Z0-9/]+)/i)?.[1];
  const inStock = /Add to Cart/i.test(text) && !/Out of Stock/i.test(text);
  return JSON.stringify({ title, price, sku, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_bhphoto_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_BH_PDP, reference)
