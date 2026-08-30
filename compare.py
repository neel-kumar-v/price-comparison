#!/usr/bin/env python3
"""CLI entrypoint for agent-browser price comparison.

Examples:
  python compare.py discover "hask argan oil conditioner"
  python compare.py compare --title "..." --size "16 fl oz" --upc 071164341568 --url https://...
"""

from __future__ import annotations

import argparse
import json
import sys

from price_compare.match import ProductReference
from price_compare.workflow import PriceCompareWorkflow


def main() -> int:
    parser = argparse.ArgumentParser(description="Multi-retailer price comparison via agent-browser")
    sub = parser.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("discover", help="Stage 1: discover product on Target")
    d.add_argument("query")

    c = sub.add_parser("compare", help="Stage 2: compare across retailers")
    c.add_argument("--title", required=True)
    c.add_argument("--size", required=True)
    c.add_argument("--upc")
    c.add_argument("--url")

    args = parser.parse_args()
    wf = PriceCompareWorkflow()

    if args.cmd == "discover":
        ref = wf.discover_reference(args.query)
        print(json.dumps({"title": ref.title, "size": ref.size, "upc": ref.upc, "url": ref.url}, indent=2))
        return 0

    ref = ProductReference(title=args.title, size=args.size, upc=args.upc, url=args.url)
    rows = wf.compare_all(ref)
    best, unit = wf.best_deal(rows, ref.size)
    print(json.dumps({"rows": [r.__dict__ for r in rows], "best": best.__dict__ if best else None, "unit_price_per_fl_oz": unit}, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
