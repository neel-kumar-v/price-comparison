"""Deterministic Costco.com steps."""

from __future__ import annotations

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, fetch_listing

RETAILER = "Costco"
SEARCH_URL = "https://www.costco.com/CatalogSearch?keyword={query}"

JS_COSTCO_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [automation-id=\"productName\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('[automation-id=\"productPriceOutput\"]')?.textContent?.trim()
    || [...document.querySelectorAll('span')].map(e => e.textContent.trim()).find(t => /^\\$[\\d,]+\\.\\d{2}$/.test(t));
  const sku = text.match(/Model(?: Number)?:?\\s*([A-Z0-9/]+)/i)?.[1]
    || location.pathname.match(/\\.product\\.([\\d]+)/)?.[1];
  const inStock = /Add to Cart/i.test(text);
  return JSON.stringify({ title, price, sku, inStock, url: location.href.split('?')[0] });
})()
"""


def fetch_costco_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(browser, RETAILER, SEARCH_URL, JS_COSTCO_PDP, reference)
