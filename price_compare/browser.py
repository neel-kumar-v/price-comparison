"""Thin wrapper around the chrome-use CLI (formerly agent-browser)."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_CDP_PORT = 9222
DEFAULT_TIMEOUT_MS = 60_000


def _agent_browser_cmd() -> list[str]:
    # chrome-use replaced agent-browser; abs is its short alias.
    for name in ("chrome-use", "abs"):
        exe = shutil.which(name)
        if exe:
            return [exe]
    # Windows shims installed next to npm globals
    for candidate in (
        os.path.expandvars(r"%APPDATA%\npm\chrome-use.exe"),
        os.path.expandvars(r"%APPDATA%\npm\abs.exe"),
    ):
        if os.path.isfile(candidate):
            return [candidate]
    # Legacy fallback (agent-browser removed; kept for old checkouts)
    exe = shutil.which("agent-browser")
    if exe:
        return [exe]
    for candidate in (
        os.path.expandvars(r"%APPDATA%\npm\agent-browser.cmd"),
        "agent-browser.cmd",
    ):
        if os.path.isfile(candidate):
            return [candidate]
    return ["chrome-use"]


@dataclass
class TabInfo:
    tab_id: str
    title: str
    url: str
    active: bool


class AgentBrowser:
    def __init__(self, cdp_port: int = DEFAULT_CDP_PORT, timeout_ms: int = DEFAULT_TIMEOUT_MS):
        self.cdp_port = cdp_port
        self.timeout_ms = timeout_ms
        os.environ["AGENT_BROWSER_DEFAULT_TIMEOUT"] = str(timeout_ms)

    def run(self, *args: str) -> str:
        cmd = [*_agent_browser_cmd(), "--cdp", str(self.cdp_port), *args]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            raise RuntimeError(f"chrome-use failed ({' '.join(args)}): {output.strip()}")
        return output.strip()

    def tab_new(self, url: str, *, label: str | None = None) -> str:
        args = ["tab", "new"]
        if label:
            args.extend(["--label", label])
        args.append(url)
        return self.run(*args)

    def tab_list(self) -> list[dict[str, Any]]:
        raw = self.run("tab", "list", "--json")
        payload = json.loads(raw)
        data = payload.get("data", payload)
        if isinstance(data, list):
            return data
        return data.get("tabs", [])

    def tab_close(self, tab_ref: str | None = None) -> str:
        if tab_ref:
            return self.run("tab", "close", tab_ref)
        return self.run("tab", "close")

    def tab_select(self, tab_ref: str) -> str:
        return self.run("tab", tab_ref)

    def reuse_tab(self, tab_ref: str, url: str) -> str:
        """Switch to tab (by id or label) and navigate — avoids opening another tab."""
        self.tab_select(tab_ref)
        return self.open(url)

    def open(self, url: str) -> str:
        return self.run("open", url)

    def reload(self) -> str:
        return self.run("reload")

    def click(self, ref: str) -> str:
        return self.run("click", ref)

    def find_text_click(self, text: str) -> str:
        return self.run("find", "text", text, "click")

    def wait(self, ms: int) -> str:
        return self.run("wait", str(ms))

    def get_url(self) -> str:
        return self.run("get", "url")

    def read(self) -> str:
        return self.run("read")

    def snapshot_interactive_json(self) -> dict[str, Any]:
        raw = self.run("snapshot", "-i", "--json")
        payload = json.loads(raw)
        return payload.get("data", payload)

    def eval_js(self, js: str, *, retries: int = 3) -> Any:
        # Windows chrome-use chokes on multiline eval scripts
        js_oneline = " ".join(js.split())
        last_err = ""
        for attempt in range(retries):
            raw = self.run("eval", js_oneline)
            if raw and raw.strip() not in ("null", ""):
                try:
                    return json.loads(raw)
                except json.JSONDecodeError:
                    return raw
            last_err = raw or "empty"
            self.wait(2000)
        return None


def ensure_cdp(cdp_port: int = DEFAULT_CDP_PORT, launch_script: str | None = None) -> None:
    """Preflight: CDP must respond before any retailer steps run."""
    url = f"http://localhost:{cdp_port}/json/version"
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            if resp.status == 200:
                return
    except (urllib.error.URLError, TimeoutError):
        pass

    if launch_script:
        subprocess.run(["pwsh", "-File", launch_script], check=True)
    else:
        raise RuntimeError(
            f"CDP not available on port {cdp_port}. "
            "Quit Helium and run launch-helium-dev.ps1, then retry."
        )

    with urllib.request.urlopen(url, timeout=10) as resp:
        if resp.status != 200:
            raise RuntimeError(f"CDP still unavailable on port {cdp_port}")
