# Price Compare Workflow (agent-browser + Helium CDP)

Deterministic retailer steps live in `price_compare/retailers/*.py`. Agents orchestrate; Python executes the brittle parts.

## Philosophy

1. **Search by title + size**, not UPC. Retailers do not reliably expose UPC search.
2. **UPC is internal verification** on the product page. Matching UPC = same item. Different/missing UPC can still match if title + size (+ description) align.
3. **When a deterministic step fails**, the agent re-snapshots, finds the new selector/path, updates the retailer module, and retries.

## Preflight (always)

```bash
curl http://localhost:9222/json/version
# if fail: quit Helium, run scripts/launch-helium-dev.ps1
$env:AGENT_BROWSER_DEFAULT_TIMEOUT = '60000'
```

PowerShell must quote refs: `agent-browser --cdp 9222 click '@e99'`

## Stage 1 — Discovery (Target)

| Step | Command / function |
|------|-------------------|
| Open search | `tab new "https://www.target.com/s?searchTerm=..."` |
| Wait | 3s |
| Find link | `snapshot -i --json` → ref where name ~ `/repair.*argan.*conditioner/i` and `16oz`, exclude deep/leave-in |
| Open PDP | `click '@eNNN'` |
| Expand specs | click button named `Specifications`, or JS in `target.py` |
| Price | JS: first `span` matching `/^\$\d+\.\d{2}$/` |
| UPC | JS: `text.match(/UPC:\s*(\d+)/)` |
| **HALT** | Ask user to confirm title + size |

## Stage 2 — Walmart

| Step | Deterministic action |
|------|---------------------|
| Search | `open https://www.walmart.com/search?q=Hask+Repair+Argan+Oil+Conditioner+16oz` (NOT UPC) |
| Click result | `find text "HASK Repair + Argan Oil Conditioner, 16 fl oz" click` |
| Price | JS: `One-time purchase $X.XX` or `"price":7.97` in HTML |
| Verify | `h1` title tokens + 16 fl oz; UPC often absent |
| Stock | `Add to cart` present |

## Stage 2 — Amazon

| Step | Deterministic action |
|------|---------------------|
| Search | `open https://www.amazon.com/s?k=HASK+Repair+Argan+Oil+Conditioner+16+fl+oz` |
| Parse cards | JS: `div[data-asin]` → `h2` title + `.a-price .a-offscreen` |
| Score | +HASK +repair +argan +conditioner +16oz; -pack/-set/-shampoo |
| Open best | `open https://www.amazon.com/dp/{asin}` if score ≥ 8 |
| Price | `#corePriceDisplay_desktop_feature_div .a-price .a-offscreen` |
| Verify | Reject multi-packs; require title/size match |

## Stage 2 — Target (price refresh)

Re-open confirmed URL, rerun Target PDP JS.

## Fallback protocol (agent)

When `RuntimeError` or empty parse:

1. `snapshot -i --json` or `read` on the live tab
2. Identify the new interactive ref / text label / CSS hook
3. Patch the retailer module constant (`CLICK_TEXT`, JS snippet, or ref finder)
4. Retry once; leave browser tabs open (never `agent-browser close`)

## Python API

```python
from price_compare import PriceCompareWorkflow

wf = PriceCompareWorkflow()
ref = wf.discover_reference("hask argan oil conditioner")  # stage 1
rows = wf.compare_all(ref)  # stage 2 after user confirms
```

CLI:

```bash
python compare.py discover "hask argan oil conditioner"
python compare.py compare --title "..." --size "16 fl oz" --upc 071164341568 --url "https://..."
```

## Personal discounts (`price_compare/profile.py`)

Shelf prices scraped from each site are adjusted using named constants before comparison:

| Constant | Default | Retailer |
|---|---|---|
| `TARGET_CIRCLE_DEBIT_CARD_DISCOUNT` | `0.05` | Target — 5% off with Circle debit card |
| `WALMART_PLUS_DISCOUNT` | `0.0` | Walmart |
| `WALMART_SUBSCRIPTION_DISCOUNT` | `0.0` | Walmart |
| `AMAZON_PRIME_DISCOUNT` | `0.0` | Amazon |
| `AMAZON_SUBSCRIBE_AND_SAVE_DISCOUNT` | `0.0` | Amazon |

Each comparison row exposes `shelf_price` (scraped), `final_price` (after profile discounts), and `discount_notes`. `best_deal()` ranks on `final_price`.

Never run `agent-browser close`. Leave product tabs in Helium for manual checkout.
