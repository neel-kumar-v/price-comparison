"""Product matching helpers.

UPC/SKU is kept internally: a matching barcode or model number is strong proof,
but title + size (+ description) can still verify the same item when retailers
expose different or missing identifiers.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

_STOPWORDS = frozenset({"the", "a", "an", "and", "or", "with", "for", "of", "in", "to"})


@dataclass
class ProductReference:
    title: str
    size: str
    category: str = "general"
    upc: str | None = None
    sku: str | None = None
    colorway: str | None = None
    url: str | None = None
    location_zip: str | None = None


@dataclass
class VerificationResult:
    same_product: bool
    confidence: str
    reasons: list[str]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+ /-]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def title_tokens(title: str) -> list[str]:
    words = _normalize(title).split()
    return [w for w in words if w not in _STOPWORDS and len(w) > 1]


def _size_oz(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\s*)?oz", text, re.I)
    return float(m.group(1)) if m else None


def _size_gal(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*gal", text, re.I)
    return float(m.group(1)) if m else None


def _size_count(text: str) -> float | None:
    m = re.search(r"(\d+)\s*(?:count|ct|dozen|pk|pack)\b", text, re.I)
    if m:
        return float(m.group(1))
    m = re.search(r"(\d+)\s*eggs?", text, re.I)
    return float(m.group(1)) if m else None


def _size_lb(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:lb|lbs|pound)", text, re.I)
    return float(m.group(1)) if m else None


def _us_shoe_size(text: str) -> float | None:
    m = re.search(r"size\s*(\d+(?:\.\d+)?)\b", text, re.I)
    if m:
        val = float(m.group(1))
        if 4 <= val <= 18:
            return val
    m = re.search(r"\b(\d+(?:\.\d+)?)\s*(?:us|m|w)\b", text, re.I)
    if m:
        val = float(m.group(1))
        if 4 <= val <= 18:
            return val
    m = re.search(r"us\s*(\d+(?:\.\d+)?)\b", text, re.I)
    if m:
        val = float(m.group(1))
        if 4 <= val <= 18:
            return val
    return None


def _is_multi_pack(title: str) -> bool:
    return bool(re.search(r"\b(pack|set|duo|bundle|count of|\(\d+\)|2-pack|3-pack)\b", title, re.I))


def _is_refurb(title: str) -> bool:
    return bool(re.search(r"\b(renewed|refurb|open box|open-box|pre-owned|used)\b", title, re.I))


def verify_general(
    reference: ProductReference,
    observed_title: str,
    observed_size: str | None = None,
    observed_upc: str | None = None,
    allow_multi_pack: bool = False,
) -> VerificationResult:
    reasons: list[str] = []
    obs_title = _normalize(observed_title)

    if not allow_multi_pack and _is_multi_pack(observed_title):
        return VerificationResult(False, "low", ["Listing looks like a multi-pack/set, not a single item"])

    tokens = title_tokens(reference.title)
    missing = [t for t in tokens if t not in obs_title]
    if missing:
        reasons.append(f"Title missing expected tokens: {', '.join(missing)}")

    ref_oz = _size_oz(reference.size) or _size_oz(reference.title)
    obs_oz = _size_oz(observed_size or observed_title)
    if ref_oz and obs_oz and abs(ref_oz - obs_oz) > 0.01:
        return VerificationResult(False, "low", [f"Size mismatch: expected {ref_oz} oz, saw {obs_oz} oz"])

    if reference.upc and observed_upc:
        if reference.upc == observed_upc:
            reasons.append("UPC matches")
            return VerificationResult(True, "high", reasons)
        reasons.append(f"UPC differs ({reference.upc} vs {observed_upc}); falling back to title/size")

    if not missing and ref_oz and obs_oz and abs(ref_oz - obs_oz) <= 0.01:
        reasons.append("Title tokens and size match")
        return VerificationResult(True, "medium" if not observed_upc else "high", reasons)

    return VerificationResult(False, "low", reasons or ["Could not confirm same product"])


def verify_shoes(
    reference: ProductReference,
    observed_title: str,
    observed_size: str | None = None,
    observed_sku: str | None = None,
) -> VerificationResult:
    reasons: list[str] = []
    obs_title = _normalize(observed_title)

    if _is_multi_pack(observed_title):
        return VerificationResult(False, "low", ["Listing looks like a pack/set, not a single shoe"])

    tokens = title_tokens(reference.title)
    missing = [t for t in tokens if t not in obs_title]
    if missing:
        reasons.append(f"Title missing expected tokens: {', '.join(missing)}")

    if reference.colorway:
        color_tokens = [t for t in _normalize(reference.colorway).replace("/", " ").split() if len(t) > 2]
        color_hits = sum(1 for t in color_tokens if t in obs_title)
        if color_tokens and color_hits == 0:
            reasons.append(f"Colorway not found: {reference.colorway}")

    ref_size = _us_shoe_size(reference.size)
    obs_size = _us_shoe_size(observed_size or observed_title)
    if ref_size and obs_size and abs(ref_size - obs_size) > 0.01:
        return VerificationResult(False, "low", [f"Size mismatch: expected US {ref_size}, saw US {obs_size}"])

    if reference.sku and observed_sku:
        if _normalize(reference.sku) == _normalize(observed_sku):
            reasons.append("Style code matches")
            return VerificationResult(True, "high", reasons)
        reasons.append(f"Style code differs ({reference.sku} vs {observed_sku}); falling back to title/size")

    if not missing and ref_size and obs_size and abs(ref_size - obs_size) <= 0.01:
        reasons.append("Model and US size match")
        return VerificationResult(True, "medium", reasons)

    return VerificationResult(False, "low", reasons or ["Could not confirm same shoe"])


def verify_tech(
    reference: ProductReference,
    observed_title: str,
    observed_sku: str | None = None,
    allow_refurb: bool = False,
) -> VerificationResult:
    reasons: list[str] = []
    obs_title = _normalize(observed_title)

    if not allow_refurb and _is_refurb(observed_title):
        return VerificationResult(False, "low", ["Listing appears renewed/refurbished/open-box"])

    ref_sku = _normalize(reference.sku or reference.size)
    if ref_sku:
        obs_sku_norm = _normalize(observed_sku or "")
        if ref_sku in obs_title or (obs_sku_norm and ref_sku == obs_sku_norm):
            reasons.append(f"SKU/model {reference.sku or reference.size} matches")
            return VerificationResult(True, "high", reasons)
        if observed_sku and ref_sku in _normalize(observed_sku):
            reasons.append("SKU matches in specs")
            return VerificationResult(True, "high", reasons)

    tokens = title_tokens(reference.title)
    missing = [t for t in tokens if t not in obs_title]
    if missing:
        reasons.append(f"Title missing expected tokens: {', '.join(missing)}")
        return VerificationResult(False, "low", reasons)

    reasons.append("Title tokens match (SKU not confirmed on page)")
    return VerificationResult(True, "medium", reasons)


def verify_grocery(
    reference: ProductReference,
    observed_title: str,
    observed_size: str | None = None,
) -> VerificationResult:
    reasons: list[str] = []
    obs_title = _normalize(observed_title)
    combined = f"{observed_title} {observed_size or ''}"

    tokens = title_tokens(reference.title)
    missing = [t for t in tokens if t not in obs_title]
    if missing:
        reasons.append(f"Title missing expected tokens: {', '.join(missing)}")

    ref_gal = _size_gal(reference.size) or _size_gal(reference.title)
    obs_gal = _size_gal(combined)
    ref_oz = _size_oz(reference.size) or _size_oz(reference.title)
    obs_oz = _size_oz(combined)
    ref_count = _size_count(reference.size) or _size_count(reference.title)
    obs_count = _size_count(combined)
    ref_lb = _size_lb(reference.size) or _size_lb(reference.title)
    obs_lb = _size_lb(combined)

    size_ok = False
    if ref_gal and obs_gal and abs(ref_gal - obs_gal) <= 0.01:
        size_ok = True
        reasons.append(f"Package size {ref_gal} gal matches")
    elif ref_oz and obs_oz and abs(ref_oz - obs_oz) <= 0.01:
        size_ok = True
        reasons.append(f"Package size {ref_oz} oz matches")
    elif ref_count and obs_count and abs(ref_count - obs_count) <= 0.01:
        size_ok = True
        reasons.append(f"Count {ref_count} matches")
    elif ref_lb is not None and obs_lb is not None:
        size_ok = True
        reasons.append("Per-lb item (unit price comparison)")

    if not missing and size_ok:
        return VerificationResult(True, "medium", reasons)

    if not missing and not (ref_gal or ref_oz or ref_count or ref_lb is not None):
        reasons.append("Title matches (size not strictly verified)")
        return VerificationResult(True, "low", reasons)

    return VerificationResult(False, "low", reasons or ["Could not confirm same grocery item"])


def verify_same_product(
    reference: ProductReference,
    observed_title: str,
    observed_size: str | None = None,
    observed_upc: str | None = None,
    observed_sku: str | None = None,
    allow_multi_pack: bool = False,
    allow_refurb: bool = False,
) -> VerificationResult:
    """Dispatch to category-specific verifier."""
    cat = reference.category
    if cat == "shoes":
        return verify_shoes(reference, observed_title, observed_size, observed_sku)
    if cat == "tech":
        return verify_tech(reference, observed_title, observed_sku, allow_refurb)
    if cat == "grocery":
        return verify_grocery(reference, observed_title, observed_size)
    return verify_general(reference, observed_title, observed_size, observed_upc, allow_multi_pack)


def load_fixture(path: str, key: str) -> ProductReference:
    """Load a ProductReference from tests/fixtures/products.json#key."""
    fixture_path = Path(path)
    if "#" in path:
        fixture_path = Path(path.split("#", 1)[0])
    data = json.loads(fixture_path.read_text(encoding="utf-8"))
    if key not in data:
        raise KeyError(f"Fixture key '{key}' not found in {fixture_path}")
    entry = data[key]
    return ProductReference(
        title=entry["title"],
        size=entry["size"],
        category=entry.get("category", key),
        upc=entry.get("upc"),
        sku=entry.get("sku"),
        colorway=entry.get("colorway"),
        url=entry.get("url"),
    )
