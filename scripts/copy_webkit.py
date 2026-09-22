#!/usr/bin/env python3
"""Copy the static webkit starter into a local client directory."""
from __future__ import annotations
import argparse
import re
import shutil
from pathlib import Path

CLIENT_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def main() -> int:
    parser = argparse.ArgumentParser(description="Copy webkit/ into clients/<client> without deploying it.")
    parser.add_argument("--client", required=True, help="Safe client folder name, for example demo")
    parser.add_argument("--output-dir", default="clients", help="Destination parent (default: clients)")
    parser.add_argument("--force", action="store_true", help="Replace an existing destination")
    args = parser.parse_args()
    if not CLIENT_RE.fullmatch(args.client): raise SystemExit("--client may contain only letters, numbers, dot, underscore, and hyphen")
    root = Path(__file__).resolve().parents[1]
    source = root / "webkit"
    destination = (root / args.output_dir / args.client).resolve()
    if not source.is_dir(): raise SystemExit(f"Missing starter directory: {source}")
    if destination == root or root not in destination.parents: raise SystemExit("Destination must remain inside the repository")
    if destination.exists() and not args.force: raise SystemExit(f"Destination exists: {destination}; pass --force to replace it")
    if destination.exists(): shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".DS_Store"))
    print(f"Copied {source.relative_to(root)}/ to {destination.relative_to(root)}/")
    print("Review placeholders, links, prices, hours, consent, and contact details before publishing.")
    return 0


if __name__ == "__main__": raise SystemExit(main())
