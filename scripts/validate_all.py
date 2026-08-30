#!/usr/bin/env python3
"""Run validations sequentially; append results to validation_results.json."""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "validation_results.json"

# (module, category, zip or None)
QUEUE = [
    ("target", "general", None),
    ("walmart", "general", None),
    ("amazon", "general", None),
    ("dicks", "shoes", None),
    ("footlocker", "shoes", None),
    ("finishline", "shoes", None),
    ("nike", "shoes", None),
    ("adidas", "shoes", None),
    ("amazon", "shoes", None),
    ("walmart", "shoes", None),
    ("bestbuy", "tech", None),
    ("bhphoto", "tech", None),
    ("apple", "tech", None),
    ("costco", "tech", None),
    ("amazon", "tech", None),
    ("walmart", "tech", None),
    ("target", "tech", None),
    ("aldi", "grocery", "61801"),
    ("meijer", "grocery", "61801"),
    ("schnucks", "grocery", "61801"),
    ("instacart", "grocery", "61801"),
    ("target", "grocery", "61801"),
    ("aldi", "grocery", "19425"),
    ("wegmans", "grocery", "19425"),
    ("acme", "grocery", "19425"),
    ("shoprite", "grocery", "19425"),
    ("instacart", "grocery", "19425"),
]


def run_one(mod: str, category: str, zip_code: str | None) -> dict:
    cmd = [sys.executable, str(ROOT / "scripts" / "validate_retailer.py"), mod, category]
    if zip_code:
        cmd.extend(["--zip", zip_code])
    env = {**dict(**subprocess.os.environ), "AGENT_BROWSER_DEFAULT_TIMEOUT": "60000", "PYTHONPATH": str(ROOT)}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=180, env=env)
        out = (proc.stdout or "").strip()
        if not out and proc.stderr:
            out = proc.stderr.strip()
        try:
            return json.loads(out)
        except json.JSONDecodeError:
            return {"ok": False, "retailer": mod, "error": out[:500]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "retailer": mod, "error": "timeout 180s"}
    except Exception as exc:
        return {"ok": False, "retailer": mod, "error": str(exc)}


def main() -> int:
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else len(QUEUE)
    results = json.loads(RESULTS.read_text()) if RESULTS.exists() else {"date": str(date.today()), "runs": []}
    for mod, cat, z in QUEUE[start:end]:
        key = f"{mod}:{cat}:{z or ''}"
        print(f"=== {key} ===", flush=True)
        row = run_one(mod, cat, z)
        row["key"] = key
        results["runs"] = [r for r in results.get("runs", []) if r.get("key") != key] + [row]
        RESULTS.write_text(json.dumps(results, indent=2))
        print(json.dumps(row), flush=True)
    passed = sum(1 for r in results["runs"] if r.get("ok"))
    print(f"Done: {passed}/{len(results['runs'])} passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())
