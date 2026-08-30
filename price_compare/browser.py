"""Thin wrapper around the agent-browser CLI."""

from __future__ import annotations

import json
import os
import subprocess
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_CDP_PORT = 9222
DEFAULT_TIMEOUT_MS = 60_000


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
        cmd = ["agent-browser", "--cdp", str(self.cdp_port), *args]
        result = subprocess.run(cmd, capture_output=True, text=True, check=False)
        output = (result.stdout or "") + (result.stderr or "")
        if result.returncode != 0:
            raise RuntimeError(f"agent-browser failed ({' '.join(args)}): {output.strip()}")
        return output.strip()

    def tab_new(self, url: str) -> str:
        return self.run("tab", "new", url)

    def tab_select(self, tab_id: str) -> str:
        return self.run("tab", tab_id)

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

    def eval_js(self, js: str) -> Any:
        raw = self.run("eval", js)
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw


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
