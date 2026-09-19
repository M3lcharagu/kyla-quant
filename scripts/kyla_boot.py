#!/usr/bin/env python3
"""Dependency-free KYLA Quant launch-night boot check.

This file intentionally uses only Python's standard library so it can run with
stock Python 3.8 on macOS Catalina. It reports useful diagnostics, but the
check is informational: missing optional tools never make the process fail.
"""

import datetime
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional, Sequence, Tuple


RESET = "\033[0m"
BOLD_CYAN = "\033[1;36m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"


def print_banner() -> None:
    """Print a small ANSI-styled banner without requiring terminal packages."""
    print(BOLD_CYAN + "=" * 64 + RESET)
    print(BOLD_CYAN + "  KYLA QUANT  |  CATALINA LAUNCH BOOT CHECK" + RESET)
    print(CYAN + "  dependency-free / standard library only / Python 3.8+" + RESET)
    print(BOLD_CYAN + "=" * 64 + RESET)


def emit(level: str, message: str) -> None:
    colors = {"PASS": GREEN, "WARN": YELLOW, "FAIL": RED, "INFO": CYAN}
    color = colors.get(level, "")
    print("{0}[{1}]{2} {3}".format(color, level, RESET, message))


def run_command(command: Sequence[str], cwd: Optional[Path] = None,
                timeout: int = 8) -> Optional[Tuple[int, str]]:
    """Run a command without a shell; return (status, combined output)."""
    try:
        result = subprocess.run(
            list(command),
            cwd=str(cwd) if cwd is not None else None,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=timeout,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.returncode, (result.stdout or "").strip()


def locate_repo_root() -> Path:
    """Find the checkout by walking from this file and the current directory."""
    starts = [Path(__file__).resolve().parent, Path.cwd().resolve()]
    seen = set()
    for start in starts:
        for candidate in [start] + list(start.parents):
            if candidate in seen:
                continue
            seen.add(candidate)
            if (candidate / ".git").exists():
                return candidate
    # Keep diagnostics useful even when the script is copied outside a checkout.
    return Path.cwd().resolve()


def format_bytes(value: Optional[int]) -> str:
    if value is None:
        return "unavailable"
    units = ("B", "KiB", "MiB", "GiB", "TiB")
    amount = float(value)
    unit = units[0]
    for unit in units:
        if amount < 1024.0 or unit == units[-1]:
            return "{0:.1f} {1}".format(amount, unit)
        amount /= 1024.0
    return "unavailable"


def read_memory_bytes() -> Optional[int]:
    """Read total RAM on macOS, with a harmless Linux fallback."""
    result = run_command(["sysctl", "-n", "hw.memsize"], timeout=3)
    if result is not None and result[0] == 0:
        try:
            return int(result[1].splitlines()[0].strip())
        except (IndexError, ValueError):
            pass

    meminfo = Path("/proc/meminfo")
    if meminfo.is_file():
        try:
            for line in meminfo.read_text(encoding="utf-8").splitlines():
                if line.startswith("MemTotal:"):
                    return int(line.split()[1]) * 1024
        except (OSError, IndexError, ValueError):
            pass
    return None


def report_system(repo_root: Path) -> None:
    cpu_count = os.cpu_count()
    emit("INFO", "CPU: {0} logical core(s)".format(cpu_count or "unknown"))
    emit("INFO", "RAM: {0}".format(format_bytes(read_memory_bytes())))

    try:
        usage = shutil.disk_usage(str(repo_root))
        emit(
            "INFO",
            "Disk ({0}): {1} free of {2}".format(
                repo_root, format_bytes(usage.free), format_bytes(usage.total)
            ),
        )
    except OSError as exc:
        emit("WARN", "Disk check unavailable: {0}".format(exc))

    emit(
        "INFO",
        "Host: {0} {1}".format(platform.system(), platform.release()),
    )


def report_version(label: str, command: Sequence[str], optional: bool = True) -> None:
    result = run_command(command, timeout=5)
    if result is None:
        emit("WARN" if optional else "FAIL", "{0}: not found".format(label))
        return
    status, output = result
    first_line = output.splitlines()[0] if output else "no version output"
    if status != 0:
        emit("WARN" if optional else "FAIL", "{0}: {1}".format(label, first_line))
        return
    emit("INFO", "{0}: {1}".format(label, first_line))


def report_git_status(repo_root: Path) -> None:
    if not (repo_root / ".git").exists():
        emit("WARN", "Git status: repository root was not detected")
        return
    if shutil.which("git") is None:
        emit("WARN", "Git status: git is not installed (optional)")
        return

    result = run_command(
        ["git", "-C", str(repo_root), "status", "--short", "--branch"],
        timeout=8,
    )
    if result is None or result[0] != 0:
        emit("WARN", "Git status: unable to read checkout")
        return

    lines = result[1].splitlines()
    emit("INFO", "Git status ({0}):".format(repo_root))
    if not lines:
        emit("INFO", "  clean (no status output)")
    else:
        for line in lines:
            print("  " + line)


def report_time() -> None:
    # EAT is UTC+03:00. Using a fixed offset keeps this compatible with stock
    # Python 3.8, where zoneinfo is not part of the standard library yet.
    eat = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=3)
    emit("INFO", "Current date/time EAT (UTC+03:00): {0}".format(
        eat.strftime("%Y-%m-%d %H:%M:%S")
    ))


def main() -> int:
    """Run every diagnostic and always return success for an informational check."""
    print_banner()
    try:
        repo_root = locate_repo_root()
        emit("INFO", "Repo root: {0}".format(repo_root))
        report_system(repo_root)
        report_version("python3", ["python3", "--version"])
        if shutil.which("python3") is None:
            emit("INFO", "running interpreter: {0}".format(sys.executable))
        report_version("node", ["node", "--version"])
        report_version("git", ["git", "--version"])
        report_git_status(repo_root)
        report_time()
        emit("PASS", "KYLA boot check complete (informational; exit 0)")
    except Exception as exc:
        # A diagnostic must not block launch night because a host query failed.
        emit("WARN", "boot check encountered a non-fatal diagnostic error: {0}".format(exc))
        emit("PASS", "KYLA boot check complete (informational; exit 0)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
