"""Personal retailer discounts and subscriptions.

Edit these named constants to match your accounts. Scraped shelf prices are
adjusted here to produce the final price used for comparison.
"""

from __future__ import annotations

import re

# --- Target ---
TARGET_CIRCLE_DEBIT_CARD_DISCOUNT = 0.05  # 5% off everything with Target Circle debit card

# --- Walmart ---
WALMART_PLUS_DISCOUNT = 0.0
WALMART_SUBSCRIPTION_DISCOUNT = 0.0

# --- Amazon ---
AMAZON_PRIME_DISCOUNT = 0.0
AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT = 0.0


def parse_shelf_price(price: str | None) -> float | None:
    if not price:
        return None
    m = re.search(r"(\d+\.\d{2})", price)
    return float(m.group(1)) if m else None


def format_price(amount: float) -> str:
    return f"${amount:.2f}"


def discounts_for_retailer(retailer: str) -> list[tuple[str, float]]:
    """Return ordered (label, rate) pairs applied to shelf price."""
    key = retailer.lower()
    if key == "target":
        if TARGET_CIRCLE_DEBIT_CARD_DISCOUNT:
            return [("Target Circle debit card", TARGET_CIRCLE_DEBIT_CARD_DISCOUNT)]
        return []
    if key == "walmart":
        out: list[tuple[str, float]] = []
        if WALMART_PLUS_DISCOUNT:
            out.append(("Walmart+", WALMART_PLUS_DISCOUNT))
        if WALMART_SUBSCRIPTION_DISCOUNT:
            out.append(("Walmart subscription", WALMART_SUBSCRIPTION_DISCOUNT))
        return out
    if key == "amazon":
        out = []
        if AMAZON_PRIME_DISCOUNT:
            out.append(("Amazon Prime", AMAZON_PRIME_DISCOUNT))
        if AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT:
            out.append(("Subscribe & Save", AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT))
        return out
    return []


def final_price_for_retailer(retailer: str, shelf_price: float) -> tuple[float, str]:
    """Apply stacked profile discounts. Returns (final_price, human-readable note)."""
    amount = shelf_price
    notes: list[str] = []
    for label, rate in discounts_for_retailer(retailer):
        amount *= 1 - rate
        notes.append(f"{label} {rate:.0%} off")
    return round(amount, 2), "; ".join(notes)


def price_with_profile(retailer: str, shelf_price: str | None) -> tuple[str | None, str | None, str]:
    """Parse shelf price and return (shelf, final, discount_notes)."""
    parsed = parse_shelf_price(shelf_price)
    if parsed is None:
        return shelf_price, None, ""
    final, note = final_price_for_retailer(retailer, parsed)
    return format_price(parsed), format_price(final), note
