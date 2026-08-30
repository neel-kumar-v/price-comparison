"""Deterministic Finish Line steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Finish Line"
SEARCH_URL = "https://www.finishline.com/search?q={query}"

JS_FINISHLINE_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[class*=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const styleCode = text.match(/Style[\\s:#]*([A-Z0-9-]+)/i)?.[1];
  const inStock = /Add to Bag|Add to Cart/i.test(text);
  return JSON.stringify({ title, price, styleCode, sku: styleCode, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_finishline_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_FINISHLINE_PDP, reference)
