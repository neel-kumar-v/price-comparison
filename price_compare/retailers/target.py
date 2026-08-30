"""Deterministic Target.com steps."""

from __future__ import annotations

import re

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, discover_listing, fetch_listing

RETAILER = "Target"
SEARCH_URL = "https://www.target.com/s?searchTerm={query}"

JS_TARGET_PDP = """
(() => {
  const text = document.body.innerText || '';
  const h1 = document.querySelector('h1');
  const title = h1 ? h1.textContent.replace(/\\s+/g,' ').trim() : '';
  let price = null;
  for (const s of document.querySelectorAll('span')) {
    const t = (s.textContent || '').trim();
    if (/^\\$\\d+\\.\\d{2}$/.test(t)) { price = t; break; }
  }
  const upc = (text.match(/UPC:\\s*(\\d+)/) || [])[1] || null;
  const inStock = !/Out of stock|Unavailable/i.test(text) && /Add to cart|Pickup|Shipping/i.test(text);
  return JSON.stringify({ title, price, upc, inStock, url: location.href });
})()
"""

JS_TARGET_EXPAND_SPECS = """
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => /specifications/i.test(b.textContent));
  if (btn && btn.getAttribute('aria-expanded') !== 'true') btn.click();
  return '{}';
})()
"""


def discover_target(browser: AgentBrowser, query: str, category: str = "general") -> ProductReference:
    return discover_listing(
        browser,
        query,
        category,
        SEARCH_URL,
        JS_TARGET_PDP,
        expand_js=JS_TARGET_EXPAND_SPECS,
    )


def fetch_target_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    return fetch_listing(
        browser,
        RETAILER,
        SEARCH_URL,
        JS_TARGET_PDP,
        reference,
        expand_js=JS_TARGET_EXPAND_SPECS,
    )
