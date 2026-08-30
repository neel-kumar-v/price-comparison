"""Deterministic Dick's Sporting Goods steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, discover_listing, fetch_listing

RETAILER = "Dick's"
SEARCH_URL = "https://www.dickssportinggoods.com/search/SearchDisplay?searchTerm={query}"

JS_DICKS_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [data-testid=\"product-title\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[class*=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const styleCode = text.match(/Style[\\s:#]*([A-Z0-9-]+)/i)?.[1] || null;
  const inStock = /Add to Cart|Add to Bag/i.test(text) && !/Out of Stock/i.test(text);
  return JSON.stringify({ title, price, styleCode, sku: styleCode, inStock, url: location.href.split('?')[0] });
})()
"""


def discover_dicks(browser: AgentBrowser, query: str, category: str = "shoes") -> ProductReference:
    return discover_listing(browser, query, category, SEARCH_URL, JS_DICKS_PDP)


def fetch_dicks_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_DICKS_PDP, reference)
