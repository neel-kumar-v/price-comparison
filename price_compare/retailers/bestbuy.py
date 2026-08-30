"""Deterministic Best Buy steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, discover_listing, fetch_listing

RETAILER = "Best Buy"
SEARCH_URL = "https://www.bestbuy.com/site/searchpage.jsp?st={query}"

JS_BESTBUY_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[data-testid=\"customer-price\"]')?.textContent?.trim()
    || [...document.querySelectorAll('.priceView-customer-price span, .pricing-price__regular-price, span')]
      .map(e => e.textContent.trim())
      .find(t => /^\\$[\\d,]+\\.\\d{2}$/.test(t));
  const sku = text.match(/Model(?: Number)?:?\\s*([A-Z0-9/]+)/i)?.[1]
    || new URLSearchParams(location.search).get('skuId');
  const inStock = /Add to cart/i.test(text) && !/Sold Out/i.test(text);
  return JSON.stringify({ title, price, sku, inStock, url: location.href.split('?')[0] });
})()
"""


def discover_bestbuy(browser: AgentBrowser, query: str, category: str = "tech") -> ProductReference:
    return discover_listing(browser, query, category, SEARCH_URL, JS_BESTBUY_PDP)


def fetch_bestbuy_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_BESTBUY_PDP, reference)
