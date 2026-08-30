"""Orchestration for staged price comparison."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .browser import AgentBrowser, ensure_cdp
from .match import ProductReference
from .profile import parse_shelf_price, price_with_profile
from .retailers import amazon, target, walmart


@dataclass
class ComparisonRow:
    retailer: str
    title: str
    size: str
    verified_upc: str | None
    shelf_price: str | None
    final_price: str | None
    in_stock: bool | None
    url: str | None
    notes: str = ""
    discount_notes: str = ""


def _unit_price(price: str | None, size: str) -> float | None:
    parsed = parse_shelf_price(price)
    oz = re.search(r"(\d+(?:\.\d+)?)", size)
    if parsed is None or not oz:
        return None
    return round(parsed / float(oz.group(1)), 3)


def _row_from_listing(listing, reference_size: str) -> ComparisonRow:
    shelf, final, discount_notes = price_with_profile(listing.retailer, listing.price)
    product_notes = "; ".join(listing.verification.get("reasons", []))
    return ComparisonRow(
        retailer=listing.retailer,
        title=listing.title,
        size=reference_size,
        verified_upc=listing.upc,
        shelf_price=shelf,
        final_price=final,
        in_stock=listing.in_stock,
        url=listing.url,
        notes=product_notes,
        discount_notes=discount_notes,
    )


class PriceCompareWorkflow:
    """Agent calls these stages explicitly.

    Stage 1: discover_reference() -> halt for human confirmation
    Stage 2: compare_all() after confirmation
    """

    def __init__(self, cdp_port: int = 9222, launch_script: str | None = None):
        self.launch_script = launch_script or str(Path(__file__).resolve().parents[1] / "scripts" / "launch-helium-dev.ps1")
        self.browser = AgentBrowser(cdp_port=cdp_port)

    def preflight(self) -> None:
        ensure_cdp(self.browser.cdp_port, self.launch_script)

    def discover_reference(self, query: str) -> ProductReference:
        self.preflight()
        return target.discover_target(self.browser, query)

    def compare_all(self, reference: ProductReference) -> list[ComparisonRow]:
        self.preflight()
        rows: list[ComparisonRow] = []

        rows.append(_row_from_listing(target.fetch_target_listing(self.browser, reference), reference.size))
        rows.append(_row_from_listing(walmart.fetch_walmart_listing(self.browser, reference), reference.size))

        a = amazon.fetch_amazon_listing(self.browser, reference)
        if a:
            rows.append(_row_from_listing(a, reference.size))
        else:
            rows.append(
                ComparisonRow(
                    retailer="Amazon",
                    title="No verified single-bottle listing found",
                    size=reference.size,
                    verified_upc=None,
                    shelf_price=None,
                    final_price=None,
                    in_stock=None,
                    url=None,
                    notes="Search returned sets/12oz variants only; agent may need to patch amazon.py selectors",
                )
            )

        return rows

    @staticmethod
    def best_deal(rows: list[ComparisonRow], size: str) -> tuple[ComparisonRow | None, float | None]:
        priced: list[tuple[ComparisonRow, float]] = []
        for row in rows:
            parsed = parse_shelf_price(row.final_price)
            if parsed is not None:
                priced.append((row, parsed))
        if not priced:
            return None, None
        best_row, _ = min(priced, key=lambda item: item[1])
        return best_row, _unit_price(best_row.final_price, size)
