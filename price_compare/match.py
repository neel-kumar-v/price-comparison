"""Product matching helpers.

UPC is kept internally: a matching UPC is strong proof, but title + size (+ image/description)
can still verify the same item when retailers expose different or missing barcodes.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass
class ProductReference:
    title: str
    size: str
    upc: str | None = None
    url: str | None = None


@dataclass
class VerificationResult:
    same_product: bool
    confidence: str
    reasons: list[str]


def _normalize(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9+ ]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def _size_oz(text: str) -> float | None:
    m = re.search(r"(\d+(?:\.\d+)?)\s*(?:fl\s*)?oz", text, re.I)
    return float(m.group(1)) if m else None


def verify_same_product(reference: ProductReference, observed_title: str, observed_size: str | None = None, observed_upc: str | None = None, allow_multi_pack: bool = False) -> VerificationResult:
    reasons: list[str] = []
    ref_title = _normalize(reference.title)
    obs_title = _normalize(observed_title)

    if not allow_multi_pack and re.search(r"\b(pack|set|duo|bundle|count of|\(\d+\))\b", observed_title, re.I):
        return VerificationResult(False, "low", ["Listing looks like a multi-pack/set, not a single bottle"])

    title_tokens = ["hask", "repair", "argan", "conditioner"]
    missing = [t for t in title_tokens if t not in obs_title]
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
