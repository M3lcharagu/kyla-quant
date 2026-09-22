#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: ./setup.sh [--help]

Check the local tools required by Kyla Quant without installing packages,
creating secrets, or contacting external services.

Checks:
  - Python 3
  - Node.js 18 or newer
  - npm 9 or newer
  - macOS Catalina (10.15): node and npm are present and versioned
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi
if [[ "$#" -gt 0 ]]; then
  echo "Unknown argument: $1" >&2
  usage >&2
  exit 2
fi

failures=0
require_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "missing: $name" >&2
    failures=$((failures + 1))
    return
  fi
  echo "found: $name ($($name --version 2>&1 | head -n 1))"
}

require_command python3
require_command node
require_command npm

version_at_least() {
  local actual="$1" minimum="$2"
  [[ "$(printf '%s\n%s\n' "$minimum" "$actual" | sort -V | head -n 1)" == "$minimum" ]]
}

if command -v node >/dev/null 2>&1; then
  node_version="$(node -p 'process.versions.node')"
  if ! version_at_least "$node_version" "18.0.0"; then
    echo "node: requires >= 18.0.0 (found $node_version)" >&2
    failures=$((failures + 1))
  else
    echo "node: compatible ($node_version)"
  fi
fi

if command -v npm >/dev/null 2>&1; then
  npm_version="$(npm --version)"
  if ! version_at_least "$npm_version" "9.0.0"; then
    echo "npm: requires >= 9.0.0 (found $npm_version)" >&2
    failures=$((failures + 1))
  else
    echo "npm: compatible ($npm_version)"
  fi
fi

if [[ "$(uname -s 2>/dev/null || true)" == "Darwin" ]] && command -v sw_vers >/dev/null 2>&1; then
  mac_version="$(sw_vers -productVersion)"
  if [[ "$mac_version" == 10.15.* ]]; then
    echo "macOS Catalina detected ($mac_version): checking Node.js/npm compatibility"
    if ! command -v node >/dev/null 2>&1 || ! command -v npm >/dev/null 2>&1; then
      echo "Catalina requires an installed Node.js/npm toolchain; nothing was installed." >&2
      failures=$((failures + 1))
    fi
  fi
fi

if (( failures > 0 )); then
  echo "setup checks failed: $failures" >&2
  exit 1
fi

echo "setup checks passed; no packages or credentials were changed"
