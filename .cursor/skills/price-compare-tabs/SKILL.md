---
name: price-compare-tabs
description: >-
  Manage Helium/agent-browser tabs during price-comparison scrapes. Use when
  opening retailer sites, running compare across many stores, seeing CDP timeouts
  (os error 10060), or deciding whether to keep or close browser tabs.
---

# Price comparison tab management

Helium CDP (port 9222) degrades when too many tabs accumulate. During a full
`compare` run (10+ retailers), **close intermediate tabs** as you go. This is
different from killing the browser session.

## Rules

| Command | OK? | When |
|---------|-----|------|
| `agent-browser tab close` | **Yes** | Search pages, store-locator modals, failed attempts, duplicate PDPs after data captured |
| `agent-browser tab close t3` | **Yes** | Close a specific tab by id from `tab list` |
| `agent-browser tab close bestbuy` | **Yes** | Close by label (if you used `--label`) |
| `agent-browser close` | **No** | Kills the entire browser session — never use during scrapes |
| `agent-browser close --all` | **No** | Same — never use |

**Keep at most one PDP tab per retailer** (the verified listing with price).
Discard everything else once title, price, URL, and stock are recorded.

## Preflight tab audit

Before a multi-retailer run:

```powershell
curl http://localhost:9222/json/version
$env:AGENT_BROWSER_DEFAULT_TIMEOUT = '60000'
agent-browser --cdp 9222 tab list
```

If more than ~5 tabs are open from a prior session, close stale ones:

```powershell
agent-browser --cdp 9222 tab close t1
agent-browser --cdp 9222 tab close t2
# …or close by URL you recognize as abandoned search pages
agent-browser --cdp 9222 tab list
```

## Per-retailer lifecycle

Use labels so tabs are easy to close by name:

```powershell
# 1. Open scratch tab for this retailer
agent-browser --cdp 9222 tab new --label scratch-bestbuy "https://www.bestbuy.com/site/searchpage.jsp?st=airpods+pro"

Start-Sleep -Seconds 3
agent-browser --cdp 9222 snapshot -i --json

# 2. Navigate to PDP (click or open)
agent-browser --cdp 9222 find text "AirPods Pro 2" click
Start-Sleep -Seconds 3

# 3. Extract price/title/SKU via eval (see retailer module JS_*_PDP)

# 4. Relabel the PDP tab, or open PDP in a labeled tab
agent-browser --cdp 9222 tab new --label bestbuy-pdp "https://www.bestbuy.com/site/.../6447382.p"

# 5. DISCARD the search/scratch tab — data is already captured
agent-browser --cdp 9222 tab close scratch-bestbuy
```

### What to discard

- Search result pages (after PDP is open or data extracted)
- Store-locator / ZIP entry pages (grocery)
- Tabs where verification failed (`same_product=False`)
- Duplicate attempts (wrong size, bundle, renewed listing)
- Intermediate `about:blank` or error pages

### What to keep (optional)

- One verified PDP per retailer for manual checkout review
- The single best-deal PDP if the user wants to buy immediately

After the full compare JSON is written, close remaining retailer PDPs unless
the user asked to keep them open.

## Compare run pattern (agent)

For `python compare.py compare --category tech --fixture ...`:

1. `tab list` — baseline count
2. For each retailer: scrape → record row → **close that retailer's tab**
3. `tab list` — should be ≤ baseline + 1 at end
4. If CDP times out mid-run: `tab list`, close half the tabs, retry once

Do **not** leave every `tab new` from Python open — the CLI opens one tab per
retailer module call. An agent supervising a compare run should close tabs
after each row succeeds, or patch retailer code to reuse a scratch tab (see
`price_compare/browser.py` helpers).

## Scratch-tab reuse (preferred)

Instead of unbounded `tab new`:

```powershell
agent-browser --cdp 9222 tab new --label scratch
agent-browser --cdp 9222 tab scratch
agent-browser --cdp 9222 open "https://www.walmart.com/search?q=..."
# …scrape…
agent-browser --cdp 9222 open "https://www.amazon.com/s?k=..."
# …scrape…
# One tab, many navigations — no cleanup needed until the run ends
```

Use `tab new` only when you need two pages at once (e.g. native store vs
Instacart side-by-side).

## Recovery from CDP timeout

Symptom: `os error 10060`, snapshot hangs, `Failed to read`.

```powershell
agent-browser --cdp 9222 tab list
# Close everything except one working tab
agent-browser --cdp 9222 tab close t2
agent-browser --cdp 9222 tab close t3
# If still broken: quit Helium, relaunch
pwsh scripts/launch-helium-dev.ps1
```

## Python helpers

```python
from price_compare.browser import AgentBrowser

browser = AgentBrowser()
tabs = browser.tab_list()          # list[{id, title, url, ...}]
browser.tab_close("t3")            # close specific tab
browser.tab_close()                # close current tab
browser.tab_new("https://...", label="scratch-target")
browser.reuse_tab("scratch")     # select labeled tab then open next URL
```

## Quick reference

```powershell
agent-browser --cdp 9222 tab list
agent-browser --cdp 9222 tab list --json
agent-browser --cdp 9222 tab new --label docs https://example.com
agent-browser --cdp 9222 tab docs              # switch
agent-browser --cdp 9222 tab close             # close current
agent-browser --cdp 9222 tab close t2          # close by id
agent-browser --cdp 9222 tab close docs        # close by label
```

See also [WORKFLOW.md](../../WORKFLOW.md) and [RETAILERS.md](../../RETAILERS.md).
