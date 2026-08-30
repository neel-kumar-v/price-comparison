"""Deterministic Amazon.com steps."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from typing import Any
from urllib.parse import quote_plus

from ..browser import AgentBrowser
from ..match import ProductReference, verify_same_product


@dataclass
class RetailerListing:
    retailer: str
    title: str
    size: str
    price: str | None
    in_stock: bool
    url: str
    upc: str | None
    verification: dict[str, Any]


SEARCH_URL = "https://www.amazon.com/s?k={query}"

JS_AMAZON_SEARCH = """
(() => {
  const results = [...document.querySelectorAll('div[data-asin]')]
    .filter(el => el.getAttribute('data-asin') && el.getAttribute('data-asin') !== '')
    .map(el => {
      const asin = el.getAttribute('data-asin');
      const title = el.querySelector('h2 span, h2 a')?.textContent?.replace(/\\s+/g,' ').trim() || '';
      const price = el.querySelector('.a-price .a-offscreen')?.textContent?.trim() || null;
      return { asin, title, price, href: `https://www.amazon.com/dp/${asin}` };
    })
    .filter(r => r.title);
  return JSON.stringify(results);
})()
"""

JS_AMAZON_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('#productTitle')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = document.querySelector('#corePriceDisplay_desktop_feature_div .a-price .a-offscreen, .priceToPay .a-offscreen, #priceblock_ourprice, .a-price .a-offscreen')?.textContent?.trim();
  const html = document.documentElement.innerHTML;
  const upc = html.match(/071164341568/)?.[0] || text.match(/UPC[\\s:]*([0-9]{10,14})/i)?.[1] || null;
  const inStock = !/Currently unavailable/i.test(text);
  return JSON.stringify({ title, price, upc, inStock, url: location.href.split('?')[0] });
})()
"""


def _score_result(title: str) -> int:
    t = title.lower()
    score = 0
    if "hask" in t:
        score += 3
    if "repair" in t:
        score += 2
    if "argan" in t:
        score += 2
    if "conditioner" in t:
        score += 2
    if re.search(r"16\\s*(fl\\s*)?oz", t):
        score += 3
    if re.search(r"pack|set|duo|shampoo|\\(\\d+\\)|each x|count of", t):
        score -= 5
    return score


def search_amazon(browser: AgentBrowser, reference: ProductReference) -> list[dict[str, Any]]:
    query = f"HASK Repair Argan Oil Conditioner {reference.size}"
    browser.open(SEARCH_URL.format(query=quote_plus(query)))
    time.sleep(4)
    results = json.loads(browser.eval_js(JS_AMAZON_SEARCH))
    scored = [{**r, "score": _score_result(r.get("title", ""))} for r in results]
    return sorted(scored, key=lambda x: x["score"], reverse=True)


def fetch_amazon_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing | None:
    candidates = search_amazon(browser, reference)
    best = next((c for c in candidates if c["score"] >= 8), None)
    if not best:
        return None

    browser.open(best["href"])
    time.sleep(4)
    data = json.loads(browser.eval_js(JS_AMAZON_PDP))
    verification = verify_same_product(reference, data.get("title", ""), observed_upc=data.get("upc"))
    if not verification.same_product:
        return None

    return RetailerListing(
        retailer="Amazon",
        title=data.get("title", ""),
        size=reference.size,
        price=data.get("price"),
        in_stock=bool(data.get("inStock")),
        url=data.get("url", best["href"]),
        upc=data.get("upc"),
        verification={"confidence": verification.confidence, "reasons": verification.reasons, "same_product": verification.same_product},
    )
