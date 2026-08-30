#!/usr/bin/env python3
"""CLI entrypoint for agent-browser price comparison.

Examples:
  python compare.py discover --category general "hask argan oil conditioner"
  python compare.py compare --category shoes --fixture tests/fixtures/products.json#shoes
  python compare.py compare --category grocery --zip 61801 --fixture tests/fixtures/products.json#grocery
"""

from __future__ import annotations

import argparse
import json
import sys

from price_compare.match import ProductReference, load_fixture
from price_compare.workflow import get_workflow


def _parse_fixture_arg(fixture: str) -> tuple[str, str]:
    if "#" in fixture:
        path, key = fixture.rsplit("#", 1)
        return path, key
    return fixture, "general"


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-retailer price comparison via agent-browser")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Stage 1: discover product on anchor retailer")
    d.add_argument("query")
    d.add_argument("--category", default="general", choices=["general", "shoes", "tech", "grocery"])
    d.add_argument("--zip", help="ZIP code for grocery discovery")

    c = sub.add_parser("compare", help="Stage 2: compare across retailers")
    c.add_argument("--category", default="general", choices=["general", "shoes", "tech", "grocery"])
    c.add_argument("--fixture", help="Path to fixture JSON, optionally with #key suffix")
    c.add_argument("--title")
    c.add_argument("--size")
    c.add_argument("--upc")
    c.add_argument("--sku")
    c.add_argument("--colorway")
    c.add_argument("--url")
    c.add_argument("--zip", help="ZIP code for grocery comparison")

    args = parser.parse_args()
    wf = get_workflow(args.category)

    if args.cmd == "discover":
        if args.category == "grocery" and args.zip:
            ref = wf.discover_reference(args.query, zip_code=args.zip)
        else:
            ref = wf.discover_reference(args.query)
        print(
            json.dumps(
                {
                    "title": ref.title,
                    "size": ref.size,
                    "category": ref.category,
                    "upc": ref.upc,
                    "sku": ref.sku,
                    "colorway": ref.colorway,
                    "url": ref.url,
                    "location_zip": ref.location_zip,
                },
                indent=2,
            )
        )
        return 0

    if args.fixture:
        path, key = _parse_fixture_arg(args.fixture)
        ref = load_fixture(path, key)
        if args.category != "general":
            ref = ProductReference(**{**ref.__dict__, "category": args.category})
    else:
        if not args.title or not args.size:
            print("Error: --title and --size required unless --fixture is provided", file=sys.stderr)
            return 1
        ref = ProductReference(
            title=args.title,
            size=args.size,
            category=args.category,
            upc=args.upc,
            sku=args.sku,
            colorway=args.colorway,
            url=args.url,
            location_zip=args.zip,
        )

    if args.zip:
        ref = ProductReference(**{**ref.__dict__, "location_zip": args.zip})

    rows = wf.compare_all(ref)
    best, unit = wf.best_deal(rows, ref.size)
    print(
        json.dumps(
            {
                "category": args.category,
                "reference": ref.__dict__,
                "rows": [r.__dict__ for r in rows],
                "best": best.__dict__ if best else None,
                "unit_price": unit,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
