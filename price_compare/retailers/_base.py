"""Shared retailer helpers and dataclasses."""

from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass, field
from typing import Any, Callable
from urllib.parse import quote_plus

from ..browser import AgentBrowser
from ..match import ProductReference, title_tokens, verify_same_product

LISTING_EXCLUSIONS = re.compile(
    r"\b(pack|set|bundle|duo|refurb|renewed|open.?box|pre-owned|restored)\b",
    re.I,
)

# URL path segments that indicate a product detail page (retailer-specific paths allowed)
PDP_PATH_MARKERS = ("/p/", "/ip/", "/dp/", "/product", "/shop/buy-")


@dataclass
class RetailerListing:
    retailer: str
    title: str
    size: str
    price: str | None
    in_stock: bool
    url: str
    upc: str | None = None
    sku: str | None = None
    verification: dict[str, Any] = field(default_factory=dict)
    delivered_price: str | None = None


def build_search_query(reference: ProductReference) -> str:
    """Build search query from reference fields (category-agnostic)."""
    parts = [reference.title]
    if reference.colorway:
        parts.append(reference.colorway)
    if reference.sku:
        parts.append(reference.sku)
    if reference.size:
        parts.append(reference.size)
    return " ".join(p for p in parts if p)


def _size_token(reference: ProductReference) -> str | None:
    m = re.search(r"(\d+(?:\.\d+)?)", reference.size or "")
    return m.group(1) if m else None


def _name_matches_reference(name: str, reference: ProductReference) -> bool:
    name_lower = name.lower()
    if LISTING_EXCLUSIONS.search(name):
        return False
    tokens = title_tokens(reference.title)
    if tokens and not all(t in name_lower for t in tokens[: min(3, len(tokens))]):
        return False
    size_tok = _size_token(reference)
    if size_tok and size_tok not in name.replace(" ", ""):
        # allow "16oz" without space
        if size_tok not in name_lower:
            return False
    if reference.sku and reference.category == "tech":
        sku_norm = reference.sku.lower().split("/")[0]
        if len(sku_norm) > 4 and sku_norm not in name_lower:
            return False
    if reference.colorway:
        for part in reference.colorway.lower().replace("/", " ").split():
            if len(part) > 2 and part not in name_lower:
                return False
    return True


def find_listing_ref(snap: dict[str, Any], reference: ProductReference) -> str | None:
    """Find first search-result link ref matching the product reference."""
    refs = snap.get("refs", {})
    for ref_id, meta in refs.items():
        if meta.get("role") != "link":
            continue
        name = meta.get("name", "")
        if not name or not _name_matches_reference(name, reference):
            continue
        return f"@{ref_id}"
    # fallback: first title token as loose pattern
    tokens = title_tokens(reference.title)
    if tokens:
        return find_link_by_pattern(snap, re.escape(tokens[0]), reference)
    return None


def find_link_by_pattern(snap: dict[str, Any], pattern: str, reference: ProductReference) -> str | None:
    """Find first interactive link ref whose name matches regex pattern."""
    refs = snap.get("refs", {})
    for ref_id, meta in refs.items():
        if meta.get("role") != "link":
            continue
        name = meta.get("name", "")
        if not re.search(pattern, name, re.I):
            continue
        if not _name_matches_reference(name, reference):
            continue
        return f"@{ref_id}"
    return None


def _is_pdp_url(url: str) -> bool:
    return any(marker in url for marker in PDP_PATH_MARKERS)


def _js_open_best_link(reference: ProductReference) -> str:
    tokens = json.dumps([t.lower() for t in title_tokens(reference.title)[:4]])
    size = json.dumps(_size_token(reference) or "")
    return f"""
(() => {{
  const tokens = {tokens};
  const size = {size};
  const link = [...document.querySelectorAll('a')].find(a => {{
    const t = a.textContent.replace(/\\s+/g,' ').trim().toLowerCase();
    if (!tokens.length || !tokens.every(tok => t.includes(tok))) return false;
    if (size && !t.includes(size)) return false;
    if (/pack|set|bundle|refurb|renewed|restored/.test(t)) return false;
    return true;
  }});
  if (link) {{ link.click(); return link.href; }}
  return null;
}})()
"""


def select_variant(browser: AgentBrowser, reference: ProductReference) -> None:
    """Select size/color variant on PDP when required (e.g. shoes)."""
    if reference.category != "shoes":
        return
    size = _size_token(reference)
    if not size:
        return
    js = f"""
    (() => {{
      const size = '{size}';
      const els = [...document.querySelectorAll('button, label, [role=\"button\"], [data-test*=\"size\"]')];
      const hit = els.find(el => el.textContent.trim() === size || el.getAttribute('aria-label') === size);
      if (hit) hit.click();
    }})()
    """
    browser.eval_js(js)
    time.sleep(2)


def open_pdp(
    browser: AgentBrowser,
    reference: ProductReference,
    search_url: str,
    *,
    wait_s: float = 5,
    click_text: str | None = None,
) -> None:
    """Open product detail page via reference URL or search."""
    if reference.url:
        try:
            browser.reuse_tab("scratch", reference.url)
        except RuntimeError:
            browser.tab_new(reference.url, label="scratch")
        time.sleep(wait_s)
        select_variant(browser, reference)
        return

    search_and_open(
        browser,
        search_url,
        reference,
        click_text=click_text,
        ref_finder=find_listing_ref,
        wait_s=wait_s,
    )
    if not _is_pdp_url(browser.get_url()):
        href = browser.eval_js(_js_open_best_link(reference))
        if href:
            browser.open(href)
            time.sleep(wait_s)
    select_variant(browser, reference)


def search_and_open(
    browser: AgentBrowser,
    search_url: str,
    reference: ProductReference,
    *,
    click_text: str | None = None,
    ref_finder: Callable[[dict[str, Any], ProductReference], str | None] | None = None,
    wait_s: float = 3,
    reuse_label: str = "scratch",
) -> None:
    query = build_search_query(reference)
    url = search_url.format(query=quote_plus(query))
    try:
        browser.reuse_tab(reuse_label, url)
    except RuntimeError:
        browser.tab_new(url, label=reuse_label)
    time.sleep(max(wait_s, 5))

    if click_text:
        try:
            browser.find_text_click(click_text)
            time.sleep(max(wait_s, 4))
            return
        except RuntimeError:
            pass

    finder = ref_finder or find_listing_ref
    for _ in range(3):
        snap = browser.snapshot_interactive_json()
        ref = finder(snap, reference)
        if ref:
            browser.click(ref)
            time.sleep(max(wait_s, 4))
            return
        time.sleep(3)

    raise RuntimeError(f"Could not open product listing for {reference.title}")


def extract_pdp(browser: AgentBrowser, js_pdp: str, *, expand_js: str | None = None) -> dict[str, Any]:
    if expand_js:
        browser.eval_js(expand_js)
        time.sleep(1)
    raw = browser.eval_js(js_pdp)
    if raw is None:
        raise RuntimeError("PDP eval returned null")
    if isinstance(raw, str):
        return json.loads(raw)
    return raw


def build_listing(
    retailer: str,
    reference: ProductReference,
    data: dict[str, Any],
    *,
    default_url: str | None = None,
) -> RetailerListing:
    verification = verify_same_product(
        reference,
        data.get("title", ""),
        observed_size=data.get("size"),
        observed_upc=data.get("upc"),
        observed_sku=data.get("sku") or data.get("styleCode"),
    )
    return RetailerListing(
        retailer=retailer,
        title=data.get("title", reference.title),
        size=reference.size,
        price=data.get("price"),
        in_stock=bool(data.get("inStock", data.get("in_stock", True))),
        url=data.get("url", default_url or ""),
        upc=data.get("upc") or reference.upc,
        sku=data.get("sku") or data.get("styleCode") or reference.sku,
        delivered_price=data.get("deliveredPrice"),
        verification={
            "confidence": verification.confidence,
            "reasons": verification.reasons,
            "same_product": verification.same_product,
        },
    )


def fetch_listing(
    browser: AgentBrowser,
    retailer: str,
    search_url: str,
    js_pdp: str,
    reference: ProductReference,
    *,
    expand_js: str | None = None,
    before_search: Callable[[AgentBrowser], None] | None = None,
    click_text: str | None = None,
) -> RetailerListing:
    """Standard fetch: optional store setup → open PDP → extract → build listing."""
    if before_search:
        before_search(browser)
    open_pdp(browser, reference, search_url, click_text=click_text)
    data = extract_pdp(browser, js_pdp, expand_js=expand_js)
    return build_listing(retailer, reference, data, default_url=reference.url or browser.get_url())


def discover_listing(
    browser: AgentBrowser,
    query: str,
    category: str,
    search_url: str,
    js_pdp: str,
    *,
    expand_js: str | None = None,
    before_search: Callable[[AgentBrowser], None] | None = None,
    default_size: str = "",
) -> ProductReference:
    """Discover anchor product: search → PDP → infer ProductReference fields."""
    ref = ProductReference(title=query, size=default_size, category=category)
    listing = fetch_listing(
        browser,
        "",
        search_url,
        js_pdp,
        ref,
        expand_js=expand_js,
        before_search=before_search,
    )
    size = default_size
    oz = re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\s*)?oz", listing.title, re.I)
    if oz:
        size = f"{oz.group(1)} fl oz"
    elif listing.sku and category == "tech":
        size = listing.sku
    return ProductReference(
        title=listing.title,
        size=size or default_size or "unknown",
        category=category,
        upc=listing.upc,
        sku=listing.sku,
        url=listing.url,
    )
