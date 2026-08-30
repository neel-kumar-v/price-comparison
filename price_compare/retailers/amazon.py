"""Deterministic Amazon.com steps."""

from __future__ import annotations

import json
import re
import time
from typing import Any
from urllib.parse import quote_plus

from ..browser import AgentBrowser
from ..match import ProductReference, title_tokens
from ._base import LISTING_EXCLUSIONS, RetailerListing, build_listing, build_search_query, extract_pdp

RETAILER = "Amazon"
SEARCH_URL = "https://www.amazon.com/s?k={query}"

JS_AMAZON_SEARCH = """
(() => {
  const results = [...document.querySelectorAll('div[data-asin]')]
    .filter(el => el.getAttribute('data-asin') && el.getAttribute('data-asin') !== '')
    .map(el => {
      const asin = el.getAttribute('data-asin');
      const title = (el.innerText || '').replace(/\\s+/g,' ').trim().slice(0, 200);
      const price = el.querySelector('.a-price .a-offscreen')?.textContent?.trim() || null;
      return { asin, title, price, href: `https://www.amazon.com/dp/${asin}` };
    })
    .filter(r => r.title && r.title.length > 20);
  return JSON.stringify(results);
})()
"""

JS_AMAZON_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('#productTitle')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('#corePriceDisplay_desktop_feature_div .a-price .a-offscreen, .priceToPay .a-offscreen, #priceblock_ourprice, .a-price .a-offscreen')?.textContent?.trim();
  const html = document.documentElement.innerHTML;
  const upc = text.match(/UPC[\\s:]*([0-9]{10,14})/i)?.[1] || null;
  const sku = text.match(/(?:Model|Part) Number[\\s:]*([A-Z0-9/-]+)/i)?.[1] || null;
  const inStock = !/Currently unavailable/i.test(text);
  return JSON.stringify({ title, price, upc, sku, inStock, url: location.href.split('?')[0] });
})()
"""


def _score_listing(title: str, reference: ProductReference) -> int:
    t = title.lower()
    if LISTING_EXCLUSIONS.search(title):
        return -10
    score = sum(2 for token in title_tokens(reference.title) if token in t)
    if reference.sku and reference.sku.lower() in t:
        score += 5
    size_tok = re.search(r"(\d+(?:\.\d+)?)", reference.size or "")
    if size_tok and size_tok.group(1) in t:
        score += 3
    return score


def search_amazon(browser: AgentBrowser, reference: ProductReference) -> list[dict[str, Any]]:
    query = build_search_query(reference)
    browser.open(SEARCH_URL.format(query=quote_plus(query)))
    time.sleep(5)
    results = json.loads(browser.eval_js(JS_AMAZON_SEARCH))
    return sorted(
        [{**r, "score": _score_listing(r.get("title", ""), reference)} for r in results],
        key=lambda x: x["score"],
        reverse=True,
    )


def fetch_amazon_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing | None:
    candidates = search_amazon(browser, reference)
    min_score = max(4, len(title_tokens(reference.title)) * 2 - 2)
    best = next((c for c in candidates if c["score"] >= min_score), None)
    if not best:
        return None

    browser.open(best["href"])
    time.sleep(4)
    data = extract_pdp(browser, JS_AMAZON_PDP)
    listing = build_listing(RETAILER, reference, data, default_url=best["href"])
    if not listing.verification.get("same_product"):
        return None
    return listing
