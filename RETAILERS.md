# Retailers

Per-retailer scrape status and known drift. Validated against [`tests/fixtures/products.json`](tests/fixtures/products.json).

Run single-retailer check: `python scripts/validate_retailer.py <module> <category> [--zip ZIP]`

## Fixtures

| Category | Product | Match fields |
|----------|---------|--------------|
| general | HASK Repair + Argan Oil Conditioner 16 fl oz | title tokens + 16 oz + UPC |
| sheamoisture | SheaMoisture Manuka Honey & Mafura Leave-In 11.5 fl oz | title tokens + oz |
| shoes | Nike Pegasus 41 Black/White US 10.5 | brand + model + US size + colorway |
| tech | Apple AirPods Pro 2 MTJV3LL/A | manufacturer SKU |
| grocery | Organic Whole Milk 1 gal | name + package size; ZIP 61801 / 19425 |

## General merchandise

| Retailer | Status | Last validated | Notes |
|----------|--------|----------------|-------|
| Target | **validated** | 2026-08-30 | $8.69; UPC match; direct PDP URL in fixture |
| Walmart | **validated** | 2026-08-30 | $7.97; find-text + ref finder |
| Amazon | pending | — | Search scoring needs work; sets dominate results |

## Shoes

| Retailer | Status | Last validated | Notes |
|----------|--------|----------------|-------|
| Dick's | partial | 2026-08-30 | Finds Pegasus 41 but often women's colorway; needs men's 10.5 filter |
| Foot Locker | pending | — | Search click fails |
| Finish Line | pending | — | Search click fails |
| Nike | pending | — | Card click covered by hero image |
| Adidas | pending | — | Search click fails |

## Tech

| Retailer | Status | Last validated | Notes |
|----------|--------|----------------|-------|
| Best Buy | explored | 2026-08-30 | Direct SKU URL works manually; `[data-testid="customer-price"]`; MTJV3LL/A |
| B&H | pending | — | Timeout on search |
| Apple | pending | — | Buy URL needs update for Pro 2 USB-C |
| Costco | pending | — | Returns Pro 3; need query filter |

## Grocery

| Retailer | ZIP 61801 | ZIP 19425 | Status |
|----------|-----------|-----------|--------|
| ALDI | yes | yes | pending |
| Meijer | yes | no | pending |
| Schnucks | yes | no | pending |
| Wegmans | no | yes | pending |
| ACME | no | yes | pending |
| ShopRite | no | yes | pending |
| Instacart | yes | yes | pending |

## Known drift

- **Windows eval:** multiline JS snippets return null — `browser.eval_js` collapses to single line (fixed in `browser.py`).
- **Tab overload:** close with `agent-browser tab close` after each retailer; see tab-management skill.
- **Best Buy:** use direct PDP URL `6447382.p?skuId=6447382`, reject Pro 3 / renewed / bundle.
- **Dick's:** eval link fallback when snapshot empty; prefer men's Pegasus 41 in search query.

## Agent-browser protocol

See [WORKFLOW.md](WORKFLOW.md). Skill: [`.cursor/skills/price-compare-tabs/SKILL.md`](.cursor/skills/price-compare-tabs/SKILL.md).
