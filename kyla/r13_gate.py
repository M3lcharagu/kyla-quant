"""Deterministic R13 v0.1 output gate; this is not an LLM reviewer."""

import re
from collections.abc import Mapping
from typing import Any, Dict, List


ALLOWED_DOMAINS = [
    "creativecommons.org",
    "docs.python.org",
    "github.com",
    "opensource.org",
    "pypi.org",
    "raw.githubusercontent.com",
]
DISCLAIMER = "R13 v0.1 is a deterministic rules engine, not an LLM reviewer or legal/financial adviser."

_SECRET_PATTERNS = (
    ("sk- API key", re.compile(r"sk-[A-Za-z0-9_-]+", re.IGNORECASE)),
    ("AKIA access key", re.compile(r"\bAKIA[0-9A-Z]*\b", re.IGNORECASE)),
    ("0x hexadecimal key", re.compile(r"\b0x[0-9a-fA-F]{8,}\b")),
    ("password assignment", re.compile(r"\bpassword\s*=\s*[^\s,;]+", re.IGNORECASE)),
)
_FINANCIAL_ADVICE_PATTERNS = (
    re.compile(r"\b(?:tell|advise|recommend|instruct|urge)\b.{0,100}\b(?:client|customer|third[- ]party|others|them)\b", re.IGNORECASE),
    re.compile(r"\b(?:client|customer|third[- ]party|others|them)\b.{0,100}\b(?:buy|sell|invest|trade|long|short)\b", re.IGNORECASE),
)
_URL_PATTERN = re.compile(r"https?://([^/\s)]+)", re.IGNORECASE)


def _text(message: Any) -> str:
    if isinstance(message, Mapping):
        parts = []
        for key in ("message", "content", "output", "domain", "type", "audience"):
            if key in message:
                parts.append(str(message[key]))
        return " ".join(parts) if parts else repr(dict(message))
    return str(message)


def _is_allowed(host: str) -> bool:
    host = host.casefold().split(":", 1)[0].lstrip("www.")
    return any(host == allowed or host.endswith("." + allowed) for allowed in ALLOWED_DOMAINS)


def check(message: Any) -> Dict[str, Any]:
    """Return a repeatable PASS/FAIL report for a proposed message or output."""

    text = _text(message)
    lower = text.casefold()
    secret_matches = [label for label, pattern in _SECRET_PATTERNS if pattern.search(text)]
    urls = _URL_PATTERN.findall(text)
    unknown_domains = sorted({host for host in urls if not _is_allowed(host)})
    financial_advice = any(pattern.search(text) for pattern in _FINANCIAL_ADVICE_PATTERNS)
    trading_output = any(word in lower for word in ("trade", "trading", "forex", "crypto", "stock", "backtest"))
    publishing_output = any(word in lower for word in ("publish", "publishing", "article", "book", "newsletter"))
    evidence_required = trading_output or publishing_output
    evidence_present = any(
        marker in lower
        for marker in ("evidence", "source", "citation", "backtest", "data", "journal", "report", "link")
    )

    checks = {
        "secrets": not secret_matches,
        "legal_license": not unknown_domains,
        "evidence": not evidence_required or evidence_present,
        "third_party_financial_advice": not financial_advice,
    }
    passed = all(checks.values())
    details = {
        "secrets": {"matched_patterns": secret_matches},
        "legal_license": {"unknown_domains": unknown_domains},
        "evidence": {"required": evidence_required, "present": evidence_present},
        "third_party_financial_advice": {"detected": financial_advice},
    }
    return {
        "version": "0.1",
        "status": "PASS" if passed else "FAIL",
        "result": "pass" if passed else "fail",
        "passed": passed,
        "failed": not passed,
        "checks": checks,
        "check_details": details,
        "evidence_required": evidence_required,
        "allowed_domains": list(ALLOWED_DOMAINS),
        "legal_license_note": "Use only content with a compatible license; R13 checks an allow-list, not legal ownership.",
        "disclaimer": DISCLAIMER,
    }
