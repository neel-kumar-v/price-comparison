"""Deterministic Walmart.com steps."""

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


# UPC search on Walmart returned no results in testing — always search by title + size.
SEARCH_URL = "https://www.walmart.com/search?q={query}"

# Exact visible card title from search results (stable enough to click by text).
CLICK_TEXT = "HASK Repair + Argan Oil Conditioner, 16 fl oz"

JS_WALMART_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const html = document.documentElement.innerHTML;
  const priceJson = html.match(/"price"\\s*:\\s*([0-9]+\\.[0-9]{2})/)?.[1];
  const oneTime = text.match(/One-time purchase\\s*\\$(\\d+\\.\\d{2})/i)?.[1]
    || text.match(/current price \\$(\\d+\\.\\d{2})/i)?.[1];
  const upc = html.match(/071164341568/)?.[0]
    || text.match(/UPC[\\s:]*([0-9]{10,14})/i)?.[1]
    || null;
  const inStock = /Add to cart/i.test(text) && !/Out of stock/i.test(text);
  return JSON.stringify({
    title,
    price: oneTime ? `$${oneTime}` : (priceJson ? `$${priceJson}` : null),
    upc,
    inStock,
    url: location.href.split('?')[0],
  });
})()
"""


def search_and_open(browser: AgentBrowser, reference: ProductReference) -> None:
    query = f"Hask Repair Argan Oil Conditioner {reference.size}"
    browser.open(SEARCH_URL.format(query=quote_plus(query)))
    time.sleep(4)
    browser.find_text_click(CLICK_TEXT)
    time.sleep(4)


def fetch_walmart_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    search_and_open(browser, reference)
    data = json.loads(browser.eval_js(JS_WALMART_PDP))
    verification = verify_same_product(reference, data.get("title", ""), observed_upc=data.get("upc"))
    return RetailerListing(
        retailer="Walmart",
        title=data.get("title", ""),
        size=reference.size,
        price=data.get("price"),
        in_stock=bool(data.get("inStock")),
        url=data.get("url", browser.get_url()),
        upc=data.get("upc"),
        verification={"confidence": verification.confidence, "reasons": verification.reasons, "same_product": verification.same_product},
    )
