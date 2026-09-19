#!/bin/sh
# Thin, dependency-free convenience wrapper for the Python preflight.
# It intentionally forwards argv; it does not evaluate a command string.
set -eu
SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
exec python3 "$SCRIPT_DIR/kyla_boot.py" --root "$SCRIPT_DIR/.." "$@"
