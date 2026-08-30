# price-comparison

Agent-driven, multi-retailer price comparison using [agent-browser](https://github.com/vercel-labs/agent-browser) and Helium (Chrome CDP on port 9222).

Compares prices across **general merchandise**, **shoes**, **tech**, and **grocery** categories. Matches products by title/size/SKU (UPC when available) and applies personal discounts from `price_compare/profile.py`.

## Prerequisites

- [agent-browser](https://www.npmjs.com/package/agent-browser) CLI
- [Helium](https://helium.computer) (or Chrome with `--remote-debugging-port=9222`)
- Python 3.10+

## Quick start

```powershell
# 1. Enable CDP on Helium
pwsh scripts/launch-helium-dev.ps1
$env:AGENT_BROWSER_DEFAULT_TIMEOUT = '60000'

# 2. Stage 1 — discover product
python compare.py discover --category general "hask argan oil conditioner"
python compare.py discover --category tech "airpods pro MTJV3LL/A"
python compare.py discover --category shoes "nike pegasus 41"
python compare.py discover --category grocery --zip 61801 "organic whole milk 1 gal"

# 3. Stage 2 — compare using fixture
python compare.py compare --category tech --fixture tests/fixtures/products.json#tech
python compare.py compare --category grocery --zip 19425 --fixture tests/fixtures/products.json#grocery
```

PowerShell wrapper: `./upc-price-compare.ps1 discover "query"`

## Test fixtures

Canonical products in [`tests/fixtures/products.json`](tests/fixtures/products.json):

- **general:** HASK Repair + Argan Oil Conditioner 16 fl oz
- **shoes:** Nike Pegasus 41 Black/White US 10.5
- **tech:** Apple AirPods Pro 2 MTJV3LL/A
- **grocery:** Organic Whole Milk 1 gal (ZIPs 61801, 19425)

## Personal discounts

Edit named constants in `price_compare/profile.py`:

```python
TARGET_CIRCLE_DEBIT_CARD_DISCOUNT = 0.05  # 5% Target Circle debit card
BEST_BUY_TOTALTECH_DISCOUNT = 0.0
COSTCO_EXECUTIVE_REWARDS = 0.0
WEGMANS_INSTACART_MARKUP = 0.15  # delivered vs shelf
```

Comparisons use **final_price** (shelf price minus profile discounts).

## Project layout

```
compare.py              CLI entrypoint
tests/fixtures/         canonical test products per category
price_compare/
  browser.py            agent-browser + CDP wrapper
  profile.py            your retailer discounts
  match.py              category-aware same-product verification
  workflow.py           category workflows (discover + compare)
  retailers/            deterministic per-site steps
scripts/
  launch-helium-dev.ps1 CDP launcher for Helium
WORKFLOW.md             agent playbook + fallback protocol
RETAILERS.md            per-retailer status and selectors
```

## Agent workflow

See [WORKFLOW.md](./WORKFLOW.md) for deterministic steps per retailer and how to patch selectors when pages change.

**Tabs:** close scraper tabs with `agent-browser tab close` when data is captured; never `agent-browser close`. See [`.cursor/skills/price-compare-tabs/SKILL.md`](.cursor/skills/price-compare-tabs/SKILL.md).
