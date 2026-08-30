"""Deterministic Target.com steps.

Known-good as of 2026-08. If a step fails, an agent should re-snapshot and patch these selectors.
"""

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


JS_TARGET_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('span')]
    .map(s => s.textContent.trim())
    .find(t => /^\\$\\d+\\.\\d{2}$/.test(t));
  const upc = text.match(/UPC:\\s*(\\d+)/)?.[1] || null;
  const inStock = !/Out of stock|Unavailable/i.test(text) && /Add to cart|Pickup|Shipping/i.test(text);
  return JSON.stringify({ title, price, upc, inStock, url: location.href });
})()
"""

JS_TARGET_EXPAND_SPECS = """
(() => {
  const btn = [...document.querySelectorAll('button')].find(b => /specifications/i.test(b.textContent));
  if (btn && btn.getAttribute('aria-expanded') !== 'true') btn.click();
  const text = document.body.innerText;
  return JSON.stringify({
    upc: text.match(/UPC:\\s*(\\d+)/)?.[1] || null,
    tcin: text.match(/TCIN:\\s*(\\d+)/)?.[1] || null,
  });
})()
"""


def _find_top_conditioner_ref(snapshot: dict[str, Any]) -> str | None:
    refs = snapshot.get("refs", {})
    for ref_id, meta in refs.items():
        if meta.get("role") != "link":
            continue
        name = meta.get("name", "")
        if re.search(r"repair.*argan.*conditioner", name, re.I) and re.search(r"16\s*oz", name, re.I):
            if re.search(r"deep|leave-in|packet|shampoo", name, re.I):
                continue
            return f"@{ref_id}"
    return None


def discover_target(browser: AgentBrowser, query: str) -> ProductReference:
    browser.tab_new(f"https://www.target.com/s?searchTerm={quote_plus(query)}")
    time.sleep(3)
    snap = browser.snapshot_interactive_json()
    ref = _find_top_conditioner_ref(snap)
    if not ref:
        raise RuntimeError("Target discovery failed: no matching product link in snapshot")

    browser.click(ref)
    time.sleep(3)
    browser.eval_js(JS_TARGET_EXPAND_SPECS)
    time.sleep(1)
    data = json.loads(browser.eval_js(JS_TARGET_PDP))

    size_match = re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\s*)?oz", data.get("title", ""), re.I)
    return ProductReference(
        title=data["title"],
        size=f"{size_match.group(1)} fl oz" if size_match else "unknown",
        upc=data.get("upc"),
        url=data.get("url"),
    )


def fetch_target_listing(browser: AgentBrowser, reference: ProductReference) -> RetailerListing:
    if not reference.url:
        raise ValueError("reference.url required for Target fetch")
    browser.tab_new(reference.url)
    time.sleep(3)
    browser.eval_js(JS_TARGET_EXPAND_SPECS)
    data = json.loads(browser.eval_js(JS_TARGET_PDP))
    verification = verify_same_product(reference, data.get("title", ""), observed_upc=data.get("upc"))
    return RetailerListing(
        retailer="Target",
        title=data.get("title", reference.title),
        size=reference.size,
        price=data.get("price"),
        in_stock=bool(data.get("inStock")),
        url=data.get("url", reference.url),
        upc=data.get("upc") or reference.upc,
        verification={"confidence": verification.confidence, "reasons": verification.reasons, "same_product": verification.same_product},
    )
