"""Deterministic Nike.com DTC steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Nike"
SEARCH_URL = "https://www.nike.com/w?q={query}"

JS_NIKE_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('#pdp_product_title, h1[id*=\"title\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[data-test=\"product-price\"], #price-container')?.textContent?.trim()
    || [...document.querySelectorAll('div, span')].map(e => e.textContent.trim()).find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const styleCode = text.match(/Style[\\s:#]*([A-Z0-9-]+)/i)?.[1]
    || location.pathname.match(/\\/t\\/([\\w-]+)/)?.[1];
  const inStock = /Add to Bag|Add to Cart/i.test(text);
  return JSON.stringify({ title, price, styleCode, sku: styleCode, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_nike_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_NIKE_PDP, reference)
