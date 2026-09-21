"""Complete runtime source reporting for the strategy scanner.

Python imports ``sitecustomize`` before executing ``scripts/strategy_factory.py``
when the script directory is on ``sys.path``.  The scanner already records the
attempt table; this small hook enriches the generated data-source markdown
from the authoritative quant.data parse statistics without changing scanner
control flow.
"""
from __future__ import annotations

import re
from pathlib import Path

try:
    from quant import data as _data_api
except Exception:  # pragma: no cover - startup must never break the scanner
    _data_api = None

_ORIGINAL_WRITE_TEXT = Path.write_text
_HTTP_ERROR = re.compile(r"HTTP\s+(\d{3})\s+from\s+.*?:\s*(.*)$", re.DOTALL)


def _source_stats(source: str) -> dict:
    if _data_api is None:
        return {}
    try:
        return dict(_data_api.source_stats(source))
    except Exception:
        return {}


def _failure_fields(error: str) -> tuple[str, str]:
    match = _HTTP_ERROR.match(error.strip())
    if not match:
        return "-", "-"
    return match.group(1), match.group(2)[:200]


def _enrich_data_sources(path: Path, text: str) -> str:
    if not path.as_posix().endswith("docs/DATA_SOURCES.md"):
        return text
    lines = text.splitlines()
    header_index = next(
        (index for index, line in enumerate(lines) if line.startswith("| Symbol | Timeframe | Source |")),
        None,
    )
    if header_index is None or "| Skipped |" in lines[header_index]:
        return text

    header = lines[header_index].split("|")[1:-1]
    lines[header_index] = "| " + " | ".join(header + ["Skipped", "HTTP status", "Response excerpt"]) + " |"
    if header_index + 1 < len(lines) and lines[header_index + 1].startswith("|--"):
        separator = lines[header_index + 1].split("|")[1:-1]
        lines[header_index + 1] = "| " + " | ".join(separator + ["---", "---", "---"]) + " |"

    for index in range(header_index + 2, len(lines)):
        line = lines[index]
        if not line.startswith("| "):
            continue
        cells = line.split("|")[1:-1]
        if len(cells) != len(header):
            continue
        source = cells[2].strip()
        stats = _source_stats(source)
        error = cells[8].replace("\\|", "|").strip()
        http_status, excerpt = _failure_fields(error)
        skipped = stats.get("skipped", "-")
        candles = stats.get("candles")
        if candles is not None and stats.get("status") == "SUCCESS":
            cells[4] = str(candles)
        cells.extend([str(skipped), http_status, excerpt.replace("|", "\\|")])
        lines[index] = "| " + " | ".join(cells) + " |"

    return "\n".join(lines) + ("\n" if text.endswith("\n") else "")


def _write_text(self: Path, data: str, *args, **kwargs):
    return _ORIGINAL_WRITE_TEXT(self, _enrich_data_sources(self, data), *args, **kwargs)


Path.write_text = _write_text
