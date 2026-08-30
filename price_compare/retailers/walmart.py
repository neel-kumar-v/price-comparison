"""Deterministic Walmart.com steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Walmart"
SEARCH_URL = "https://www.walmart.com/search?q={query}"

JS_WALMART_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const html = document.documentElement.innerHTML;
  const priceJson = html.match(/"price"\\s*:\\s*([0-9]+\\.[0-9]{2})/)?.[1];
  const oneTime = text.match(/One-time purchase\\s*\\$(\\d+\\.\\d{2})/i)?.[1]
    || text.match(/current price \\$(\\d+\\.\\d{2})/i)?.[1];
  const upc = text.match(/UPC[\\s:]*([0-9]{10,14})/i)?.[1] || null;
  const sku = text.match(/Model[\\s:#]*([A-Z0-9/-]+)/i)?.[1] || null;
  const inStock = /Add to cart/i.test(text) && !/Out of stock/i.test(text);
  return JSON.stringify({
    title,
    price: oneTime ? `$${oneTime}` : (priceJson ? `$${priceJson}` : null),
    upc,
    sku,
    inStock,
    url: location.href.split('?')[0],
  });
})()
"""


def fetch_walmart_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_WALMART_PDP, reference)
