#!/usr/bin/env python3
"""Optional browser-use example; the dependency is deliberately not bundled."""

import argparse
import asyncio


def main() -> None:
    parser = argparse.ArgumentParser(description="Optional browser-use read-only example.")
    parser.add_argument("--task", default="Open https://example.com and report the page title.")
    args = parser.parse_args()
    try:
        from browser_use import Agent  # type: ignore
    except ImportError as exc:
        raise SystemExit("browser-use is optional and not installed. Review its official docs and install it in an isolated environment before running this example.") from exc

    async def run() -> None:
        agent = Agent(task=args.task)
        await agent.run()

    asyncio.run(run())


if __name__ == "__main__":
    main()
