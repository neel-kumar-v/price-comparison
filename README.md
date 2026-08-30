# price-comparison

Agent-driven, multi-retailer price comparison using [agent-browser](https://github.com/vercel-labs/agent-browser) and Helium (Chrome CDP on port 9222).

Scrapes **Target**, **Walmart**, and **Amazon**, matches the same product by title/size (UPC when available), and applies personal discounts from `price_compare/profile.py`.

## Prerequisites

- [agent-browser](https://www.npmjs.com/package/agent-browser) CLI
- [Helium](https://helium.computer) (or Chrome with `--remote-debugging-port=9222`)
- Python 3.10+

## Quick start

```powershell
# 1. Enable CDP on Helium
pwsh scripts/launch-helium-dev.ps1

# 2. Stage 1 — discover product on Target
python compare.py discover "hask argan oil conditioner"

# 3. Stage 2 — compare after confirming title/size
python compare.py compare --title "..." --size "16 fl oz" --upc 071164341568 --url "https://..."
```

PowerShell wrapper: `./upc-price-compare.ps1 discover "query"`

## Personal discounts

Edit named constants in `price_compare/profile.py`:

```python
TARGET_CIRCLE_DEBIT_CARD_DISCOUNT = 0.05  # 5% Target Circle debit card
WALMART_PLUS_DISCOUNT = 0.0
AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT = 0.0
```

Comparisons use **final_price** (shelf price minus profile discounts).

## Project layout

```
compare.py              CLI entrypoint
price_compare/
  browser.py            agent-browser + CDP wrapper
  profile.py            your retailer discounts
  match.py              same-product verification
  workflow.py           discover + compare orchestration
  retailers/            deterministic per-site steps
scripts/
  launch-helium-dev.ps1 CDP launcher for Helium
WORKFLOW.md             agent playbook + fallback protocol
```

## Agent workflow

See [WORKFLOW.md](./WORKFLOW.md) for deterministic steps per retailer and how to patch selectors when pages change.

**Rule:** never run `agent-browser close` — leave product tabs open for checkout.
