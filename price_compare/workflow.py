"""Orchestration for staged price comparison by category."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .browser import AgentBrowser, ensure_cdp
from .match import ProductReference, load_fixture
from .profile import parse_shelf_price, price_with_profile
from .retailers import amazon, target, walmart
from .retailers._base import RetailerListing


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
    delivered_price: str | None = None
    verified_sku: str | None = None


def _unit_price(price: str | None, size: str, category: str) -> float | None:
    parsed = parse_shelf_price(price)
    if parsed is None:
        return None
    if category == "grocery":
        gal = re.search(r"(\d+(?:\.\d+)?)\s*gal", size, re.I)
        if gal:
            return round(parsed / float(gal.group(1)), 3)
        oz = re.search(r"(\d+(?:\.\d+)?)", size)
        if oz:
            return round(parsed / float(oz.group(1)), 3)
    if category == "general":
        oz = re.search(r"(\d+(?:\.\d+)?)", size)
        if oz:
            return round(parsed / float(oz.group(1)), 3)
    return parsed


def _row_from_listing(listing: RetailerListing, reference: ProductReference) -> ComparisonRow:
    shelf, final, discount_notes = price_with_profile(listing.retailer, listing.price)
    product_notes = "; ".join(listing.verification.get("reasons", []))
    if not listing.verification.get("same_product"):
        product_notes = f"VERIFY FAILED: {product_notes}"
    return ComparisonRow(
        retailer=listing.retailer,
        title=listing.title,
        size=reference.size,
        verified_upc=listing.upc,
        verified_sku=listing.sku,
        shelf_price=shelf,
        final_price=final,
        delivered_price=listing.delivered_price,
        in_stock=listing.in_stock,
        url=listing.url,
        notes=product_notes,
        discount_notes=discount_notes,
    )


def _safe_fetch(name: str, fetcher: Callable[[], RetailerListing | None], reference: ProductReference) -> ComparisonRow:
    try:
        listing = fetcher()
        if listing is None:
            return ComparisonRow(
                retailer=name,
                title=f"No verified listing found",
                size=reference.size,
                verified_upc=None,
                verified_sku=None,
                shelf_price=None,
                final_price=None,
                in_stock=None,
                url=None,
                notes="Search returned no matching product; agent may need to patch selectors",
            )
        return _row_from_listing(listing, reference)
    except Exception as exc:
        return ComparisonRow(
            retailer=name,
            title=f"Error fetching {name}",
            size=reference.size,
            verified_upc=None,
            verified_sku=None,
            shelf_price=None,
            final_price=None,
            in_stock=None,
            url=None,
            notes=str(exc),
        )


class GeneralMerchWorkflow:
    category = "general"

    def __init__(self, cdp_port: int = 9222, launch_script: str | None = None):
        self.launch_script = launch_script or str(Path(__file__).resolve().parents[1] / "scripts" / "launch-helium-dev.ps1")
        self.browser = AgentBrowser(cdp_port=cdp_port)

    def preflight(self) -> None:
        ensure_cdp(self.browser.cdp_port, self.launch_script)

    def discover_reference(self, query: str) -> ProductReference:
        self.preflight()
        return target.discover_target(self.browser, query, category=self.category)

    def compare_all(self, reference: ProductReference) -> list[ComparisonRow]:
        self.preflight()
        reference = ProductReference(**{**reference.__dict__, "category": self.category})
        rows = [
            _safe_fetch("Target", lambda: target.fetch_target_listing(self.browser, reference), reference),
            _safe_fetch("Walmart", lambda: walmart.fetch_walmart_listing(self.browser, reference), reference),
            _safe_fetch("Amazon", lambda: amazon.fetch_amazon_listing(self.browser, reference), reference),
        ]
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
        return best_row, _unit_price(best_row.final_price, size, "general")


class ShoesWorkflow(GeneralMerchWorkflow):
    category = "shoes"

    def discover_reference(self, query: str) -> ProductReference:
        self.preflight()
        from .retailers import dicks

        try:
            return dicks.discover_dicks(self.browser, query)
        except Exception:
            from .retailers import footlocker

            return footlocker.discover_footlocker(self.browser, query)

    def compare_all(self, reference: ProductReference) -> list[ComparisonRow]:
        self.preflight()
        reference = ProductReference(**{**reference.__dict__, "category": self.category})
        rows: list[ComparisonRow] = []
        for mod_name in ("dicks", "footlocker", "finishline", "nike", "adidas"):
            try:
                mod = __import__(f"price_compare.retailers.{mod_name}", fromlist=[mod_name])
                name = getattr(mod, "RETAILER")
                fetcher = getattr(mod, f"fetch_{mod_name}_listing")
                rows.append(_safe_fetch(name, lambda f=fetcher: f(self.browser, reference), reference))
            except ImportError:
                pass
        rows.append(_safe_fetch("Amazon", lambda: amazon.fetch_amazon_listing(self.browser, reference), reference))
        rows.append(_safe_fetch("Walmart", lambda: walmart.fetch_walmart_listing(self.browser, reference), reference))
        return rows


class TechWorkflow(GeneralMerchWorkflow):
    category = "tech"

    def discover_reference(self, query: str) -> ProductReference:
        self.preflight()
        from .retailers import bestbuy

        try:
            return bestbuy.discover_bestbuy(self.browser, query)
        except Exception:
            return target.discover_target(self.browser, query, category=self.category)

    def compare_all(self, reference: ProductReference) -> list[ComparisonRow]:
        self.preflight()
        reference = ProductReference(**{**reference.__dict__, "category": self.category})
        rows: list[ComparisonRow] = []
        for mod_name in ("bestbuy", "bhphoto", "apple", "costco"):
            try:
                mod = __import__(f"price_compare.retailers.{mod_name}", fromlist=[mod_name])
                name = getattr(mod, "RETAILER")
                fetcher = getattr(mod, f"fetch_{mod_name}_listing")
                rows.append(_safe_fetch(name, lambda f=fetcher: f(self.browser, reference), reference))
            except (ImportError, AttributeError):
                pass
        rows.append(_safe_fetch("Amazon", lambda: amazon.fetch_amazon_listing(self.browser, reference), reference))
        rows.append(_safe_fetch("Walmart", lambda: walmart.fetch_walmart_listing(self.browser, reference), reference))
        rows.append(_safe_fetch("Target", lambda: target.fetch_target_listing(self.browser, reference), reference))
        return rows


class GroceryWorkflow(GeneralMerchWorkflow):
    category = "grocery"

    def discover_reference(self, query: str, zip_code: str = "61801") -> ProductReference:
        self.preflight()
        from .retailers import aldi

        ref = aldi.discover_aldi(self.browser, query, zip_code)
        ref.location_zip = zip_code
        return ref

    def compare_all(self, reference: ProductReference) -> list[ComparisonRow]:
        self.preflight()
        zip_code = reference.location_zip or "61801"
        reference = ProductReference(**{**reference.__dict__, "category": self.category, "location_zip": zip_code})

        champaign = {"aldi", "meijer", "schnucks", "target", "instacart"}
        chester = {"aldi", "wegmans", "acme", "shoprite", "target", "instacart"}
        allowed = champaign if zip_code.startswith("618") else chester

        rows: list[ComparisonRow] = []
        for mod_name in ("aldi", "meijer", "schnucks", "wegmans", "acme", "shoprite", "instacart"):
            if mod_name not in allowed:
                continue
            try:
                mod = __import__(f"price_compare.retailers.{mod_name}", fromlist=[mod_name])
                name = getattr(mod, "RETAILER")
                fetcher = getattr(mod, f"fetch_{mod_name}_listing")
                rows.append(_safe_fetch(name, lambda f=fetcher, z=zip_code: f(self.browser, reference, z), reference))
            except (ImportError, AttributeError):
                pass
        if "target" in allowed:
            rows.append(_safe_fetch("Target", lambda: target.fetch_target_listing(self.browser, reference), reference))
        return rows

    @staticmethod
    def best_deal(rows: list[ComparisonRow], size: str) -> tuple[ComparisonRow | None, float | None]:
        priced: list[tuple[ComparisonRow, float]] = []
        for row in rows:
            parsed = parse_shelf_price(row.final_price or row.shelf_price)
            if parsed is not None:
                priced.append((row, parsed))
        if not priced:
            return None, None
        best_row, _ = min(priced, key=lambda item: item[1])
        return best_row, _unit_price(best_row.final_price or best_row.shelf_price, size, "grocery")


WORKFLOWS = {
    "general": GeneralMerchWorkflow,
    "shoes": ShoesWorkflow,
    "tech": TechWorkflow,
    "grocery": GroceryWorkflow,
}


def get_workflow(category: str = "general", **kwargs) -> GeneralMerchWorkflow:
    cls = WORKFLOWS.get(category, GeneralMerchWorkflow)
    return cls(**kwargs)


# Backward compatibility
PriceCompareWorkflow = GeneralMerchWorkflow
