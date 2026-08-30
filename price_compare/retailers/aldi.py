"""Deterministic ALDI steps (native + Instacart)."""

from __future__ import annotations

import re
import time

from ..browser import AgentBrowser
from ..match import ProductReference
from ._base import RetailerListing, build_listing, build_search_query, extract_pdp, find_listing_ref

RETAILER = "ALDI"
STORE_URL = "https://www.aldi.us/en/grocery/"

JS_ALDI_SEARCH = """
(() => {
  const input = document.querySelector('input[type=\"search\"], input[placeholder*=\"Search\"]');
  if (input) { input.focus(); input.value = '%QUERY%'; input.dispatchEvent(new Event('input', {bubbles:true})); input.form?.submit(); }
  return 'submitted';
})()
"""

JS_ALDI_PDP = """
(() => {
  const text = document.body.innerText;
  const title = document.querySelector('h1, [class*=\"product-title\"]')?.textContent?.replace(/\\s+/g,' ').trim();
  const price = [...document.querySelectorAll('[class*=\"price\"], span')]
    .map(e => e.textContent.trim())
    .find(t => /^\\$\\d+[\\d,]*\\.\\d{2}$/.test(t));
  const inStock = !/Out of Stock|Unavailable/i.test(text);
  return JSON.stringify({ title, price, inStock, url: location.href });
})()
"""


def _set_zip(browser: AgentBrowser, zip_code: str) -> None:
    browser.tab_new(f"{STORE_URL}?zip={zip_code}")
    time.sleep(3)


def _aldi_search(browser: AgentBrowser, reference: ProductReference) -> None:
    query = build_search_query(reference)
    browser.eval_js(JS_ALDI_SEARCH.replace("%QUERY%", query))
    time.sleep(4)
    snap = browser.snapshot_interactive_json()
    ref_link = find_listing_ref(snap, reference)
    if ref_link:
        browser.click(ref_link)
        time.sleep(3)


def _infer_size(title: str, default: str = "") -> str:
    oz = re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\s*)?oz", title, re.I)
    if oz:
        return f"{oz.group(1)} fl oz"
    gal = re.search(r"(\d+(?:\.\d+)?)\s*gal", title, re.I)
    if gal:
        return f"{gal.group(1)} gal"
    return default


def discover_aldi(browser: AgentBrowser, query: str, zip_code: str = "61801") -> ProductReference:
    ref = ProductReference(title=query, category="grocery", location_zip=zip_code)
    _set_zip(browser, zip_code)
    _aldi_search(browser, ref)
    data = extract_pdp(browser, JS_ALDI_PDP)
    size = _infer_size(data.get("title", query), "1 gal")
    return ProductReference(
        title=data.get("title", query),
        size=size,
        category="grocery",
        location_zip=zip_code,
        url=data.get("url"),
    )


def fetch_aldi_listing(browser: AgentBrowser, reference: ProductReference, zip_code: str = "61801") -> RetailerListing:
    zip_code = reference.location_zip or zip_code
    reference = ProductReference(**{**reference.__dict__, "location_zip": zip_code})
    _set_zip(browser, zip_code)
    _aldi_search(browser, reference)
    data = extract_pdp(browser, JS_ALDI_PDP)
    return build_listing(RETAILER, reference, data)
