#!/usr/bin/env python3
"""Fail-closed kill switch and pre-trade guard helpers.

The guard is deliberately dependency-free so strategy and execution entrypoints
can call it as their first check.  Set KYLA_KILL_SWITCH_FILE and/or
KYLA_KILL_SWITCH_URL in the runtime environment; a local flag is armed when
its file exists and contains a non-empty value other than 0/false/off/no.
The remote endpoint may return JSON (``{"armed": true}``) or plain text.
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import urllib.request
from pathlib import Path
from typing import Any, Mapping

LOG = logging.getLogger("kyla.kill_switch")
_FALSE = {"", "0", "false", "off", "no", "disabled", "disarmed"}
DEFAULT_LOCAL_FILE = ".kill_switch"
DEFAULT_NEWS_FILE = "NEWS_GUARD"


class KillSwitchArmed(RuntimeError):
    """Raised when a trading/deployment action must be refused."""


def _truthy(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() not in _FALSE


def _local_path() -> Path:
    return Path(os.getenv("KYLA_KILL_SWITCH_FILE", DEFAULT_LOCAL_FILE))


def _read_local(path: Path) -> tuple[bool, str]:
    if not path.exists():
        return False, f"local flag absent: {path}"
    try:
        value = path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        return True, f"local flag unreadable ({exc}); failing closed"
    return _truthy(value), f"local flag {path}={value!r}"


def _read_remote(url: str, timeout: float = 3.0) -> tuple[bool, str]:
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "kyla-kill-switch/1"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace").strip()
        try:
            payload = json.loads(raw)
        except json.JSONDecodeError:
            payload = raw
        if isinstance(payload, Mapping):
            value = payload.get("armed", payload.get("kill_switch", payload.get("enabled", False)))
        else:
            value = payload
        return _truthy(value), f"remote flag {url}={value!r}"
    except Exception as exc:  # network errors must not permit an unsafe action
        return True, f"remote flag unavailable ({exc}); failing closed"


def status(*, local_file: str | None = None, remote_url: str | None = None) -> tuple[bool, list[str]]:
    """Return ``(armed, reasons)`` using local and optional remote controls."""
    reasons: list[str] = []
    local_armed, local_reason = _read_local(Path(local_file) if local_file else _local_path())
    reasons.append(local_reason)
    armed = local_armed
    url = remote_url if remote_url is not None else os.getenv("KYLA_KILL_SWITCH_URL", "")
    if url:
        remote_armed, remote_reason = _read_remote(url)
        reasons.append(remote_reason)
        armed = armed or remote_armed
    return armed, reasons


def require_clear(action: str = "trading", *, local_file: str | None = None, remote_url: str | None = None) -> None:
    """Refuse an action when either kill-switch source is armed."""
    armed, reasons = status(local_file=local_file, remote_url=remote_url)
    if armed:
        message = f"KILL SWITCH ARMED: refusing {action}; " + "; ".join(reasons)
        LOG.error(message)
        raise KillSwitchArmed(message)
    LOG.info("kill switch clear for %s; %s", action, "; ".join(reasons))


def trade_allowed(*, spread: float | None = None, max_spread: float | None = None, news_file: str | None = None) -> tuple[bool, str]:
    """Apply kill switch, NEWS_GUARD, and an optional spread ceiling."""
    try:
        require_clear("trade")
    except KillSwitchArmed as exc:
        return False, str(exc)
    flag = Path(news_file or os.getenv("KYLA_NEWS_GUARD_FILE", DEFAULT_NEWS_FILE))
    if flag.exists():
        return False, f"NEWS_GUARD present: {flag}"
    if spread is not None and max_spread is not None and spread > max_spread:
        return False, f"spread {spread} exceeds max_spread {max_spread}"
    return True, "guards clear"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", default="trading", help="action being guarded")
    parser.add_argument("--status", action="store_true", help="print status without raising")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    armed, reasons = status()
    print(json.dumps({"armed": armed, "reasons": reasons}, indent=2))
    if armed and not args.status:
        try:
            require_clear(args.action)
        except KillSwitchArmed:
            return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
