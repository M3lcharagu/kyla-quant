#!/usr/bin/env python3
"""Scan tracked and present worktree files for common secret material."""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

PATTERNS = {
    "private key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b"),
    "generic secret assignment": re.compile(r"(?i)\b(?:api[_-]?key|api[_-]?secret|password|passwd|private[_-]?key|access[_-]?token)\s*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}"),
    "JWT": re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b"),
}
EXCLUDED_DIRS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules"}
EXCLUDED_NAMES = {"scrub_check.py"}


def tracked(root: Path) -> set[Path]:
    try:
        result = subprocess.run(["git", "ls-files", "-co", "--exclude-standard"], cwd=root, text=True, capture_output=True, check=True)
    except (OSError, subprocess.CalledProcessError):
        return set()
    return {root / line for line in result.stdout.splitlines() if line}


def worktree(root: Path) -> set[Path]:
    paths: set[Path] = set()
    for directory, dirs, files in os.walk(root):
        dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
        for name in files:
            path = Path(directory) / name
            if name not in EXCLUDED_NAMES:
                paths.add(path)
    return paths


def scan(path: Path) -> list[tuple[str, str, int]]:
    try:
        data = path.read_bytes()
        if b"\0" in data or len(data) > 5_000_000:
            return []
        text = data.decode("utf-8", errors="ignore")
    except OSError:
        return []
    findings: list[tuple[str, str, int]] = []
    for number, line in enumerate(text.splitlines(), 1):
        for name, pattern in PATTERNS.items():
            if pattern.search(line):
                findings.append((str(path), name, number))
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", default=".")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    paths = tracked(root) | worktree(root)
    findings = [finding for path in sorted(paths) if path.is_file() for finding in scan(path)]
    if findings:
        for path, kind, line in findings:
            print(f"SECRET PATTERN: {kind} at {path}:{line}", file=sys.stderr)
        return 1
    print(f"scrub_check: scanned {len(paths)} files; no common secret patterns found")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
