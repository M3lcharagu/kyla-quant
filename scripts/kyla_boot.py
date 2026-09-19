#!/usr/bin/env python3
"""Dependency-free KYLA Quant launch preflight and controlled command runner.

This module uses only Python's standard library. It never installs packages,
contacts a network service, or prints environment values. Run it from the
repository root, or pass --root to identify the checkout explicitly.
"""

from __future__ import annotations

import argparse
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Iterable, Sequence

REQUIRED_FILES = ("Dockerfile", "config.example.yaml", "requirements.txt")
REQUIRED_DIRS = ("src", "docs")
OPTIONAL_COMMANDS = ("brew", "node", "npm", "git", "code", "docker")


def emit(level: str, message: str) -> None:
    print(f"[{level}] {message}")


def command_version(command: str) -> str | None:
    """Return a short version line without exposing command arguments or secrets."""
    executable = shutil.which(command)
    if not executable:
        return None
    try:
        result = subprocess.run(
            [executable, "--version"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    output = (result.stdout or result.stderr).strip().splitlines()
    return output[0][:160] if output else "available"


def check_command(command: str, *, required: bool) -> bool:
    version = command_version(command)
    if version is None:
        emit("FAIL" if required else "WARN", f"{command}: not found")
        return not required
    emit("PASS", f"{command}: {version}")
    return True


def check_project(root: Path) -> bool:
    ok = True
    for relative in REQUIRED_FILES:
        path = root / relative
        if path.is_file():
            emit("PASS", f"file present: {relative}")
        else:
            emit("FAIL", f"required file missing: {relative}")
            ok = False
    for relative in REQUIRED_DIRS:
        path = root / relative
        if path.is_dir():
            emit("PASS", f"directory present: {relative}")
        else:
            emit("FAIL", f"required directory missing: {relative}")
            ok = False
    return ok


def check_git(root: Path) -> bool:
    git = shutil.which("git")
    if not git:
        return False
    try:
        result = subprocess.run(
            [git, "-C", str(root), "rev-parse", "--show-toplevel"],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is None or result.returncode != 0:
        emit("FAIL", "repository is not a readable Git checkout")
        return False
    emit("PASS", "repository is a readable Git checkout")
    return True


def check_docker() -> bool:
    docker = shutil.which("docker")
    if not docker:
        emit("WARN", "docker: not found (required only for a Docker launch)")
        return True
    try:
        result = subprocess.run(
            [docker, "info", "--format", "{{.ServerVersion}}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=12,
        )
    except (OSError, subprocess.SubprocessError):
        result = None
    if result is None or result.returncode != 0:
        emit("FAIL", "docker: installed but the Docker daemon is not ready")
        return False
    version = (result.stdout or "").strip() or "ready"
    emit("PASS", f"docker daemon: {version[:80]}")
    return True


def preflight(root: Path) -> int:
    emit("INFO", f"root: {root}")
    if platform.system() != "Darwin":
        emit("WARN", f"host OS is {platform.system()}, not macOS/Catalina")
    elif platform.mac_ver()[0]:
        emit("PASS", f"host OS: macOS {platform.mac_ver()[0]}")

    ok = check_project(root)
    ok = check_git(root) and ok

    # Python is the only runtime required by this script. Other commands are
    # reported but not all are hard requirements for every launch mode.
    for command in OPTIONAL_COMMANDS:
        ok = check_command(command, required=False) and ok
    ok = check_docker() and ok

    config_path = root / "config.yaml"
    if config_path.exists():
        emit("WARN", "config.yaml exists; confirm it is ignored and contains no live credentials")
    else:
        emit("INFO", "config.yaml not present; use the project’s approved configuration path if required")

    if ok:
        emit("PASS", "preflight complete: no required checks failed")
        return 0
    emit("FAIL", "preflight complete: resolve required failures before launch")
    return 1


def parse_args(argv: Sequence[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="repository root (default: current directory)")
    parser.add_argument("--check", action="store_true", help="run the preflight check (the default action)")
    parser.add_argument("--print-command", action="store_true", help="print the approved start command without running it")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="optional command after --, executed only after a passing preflight")
    return parser.parse_args(argv)


def normalise_command(args: argparse.Namespace) -> list[str]:
    command = list(args.command)
    if command and command[0] == "--":
        command.pop(0)
    if command:
        return command
    configured = os.environ.get("KYLA_BOOT_COMMAND", "").strip()
    if configured:
        # Deliberately do not split or shell-evaluate environment text. An
        # approved command should be passed as argv after -- instead.
        emit("WARN", "KYLA_BOOT_COMMAND is set but ignored; pass argv after -- to avoid shell parsing")
    return []


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    root = args.root.expanduser().resolve()
    if not root.is_dir():
        emit("FAIL", f"root does not exist: {root}")
        return 2

    status = preflight(root)
    command = normalise_command(args)
    if args.print_command:
        if command:
            print(" ".join(command))
        else:
            print("No command supplied. Example: python3 scripts/kyla_boot.py -- docker compose up --build")
        return status
    if status != 0:
        return status
    if not command:
        emit("INFO", "nothing started; preflight-only mode")
        return 0

    emit("INFO", "starting approved command; Ctrl-C is forwarded to the child process")
    try:
        completed = subprocess.run(command, cwd=root, check=False)
    except OSError as exc:
        emit("FAIL", f"could not start command: {exc}")
        return 127
    emit("INFO", f"command exited with status {completed.returncode}")
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
