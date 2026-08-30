"""Deterministic Adidas.com steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Adidas"
SEARCH_URL = "https://www.adidas.com/us/search?q={query}"

JS_ADIDAS_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-testid=\"product-title\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[data-testid=\"product-price\"]')?.textContent?.trim()
    || [...document.querySelectorAll('span')].map(e => e.textContent.trim()).find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const styleCode = text.match(/Model number[\\s:#]*([A-Z0-9]+)/i)?.[1];
  const inStock = /Add to Bag|Add to Cart/i.test(text);
  return JSON.stringify({ title, price, styleCode, sku: styleCode, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_adidas_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_ADIDAS_PDP, reference)
