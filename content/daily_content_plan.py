#!/usr/bin/env python3
"""Build a deterministic daily clip plan without APIs or external packages."""

from __future__ import annotations

import argparse
import json
from datetime import date
from typing import Iterable

TOPICS = [
    "one practical trading lesson",
    "a behind-the-scenes build note",
    "a short creator mindset reminder",
    "one local business growth idea",
]


def build_plan(topics: Iterable[str], count: int = 4, day: str | None = None) -> dict:
    """Return a repeatable 3-5 clip plan from non-empty topic strings."""
    cleaned_topics = [topic.strip() for topic in topics if topic.strip()]
    if not cleaned_topics:
        raise ValueError("Provide at least one non-empty topic.")
    if day is not None:
        try:
            date.fromisoformat(day)
        except ValueError as exc:
            raise ValueError("--date must use YYYY-MM-DD.") from exc
    count = max(3, min(5, count))
    plan_date = day or date.today().isoformat()
    clips = []
    for index in range(count):
        topic = cleaned_topics[index % len(cleaned_topics)]
        clips.append({
            "clip": index + 1,
            "topic": topic,
            "segment_prompt": f"Hook, useful point, and close about {topic}.",
            "edit": "Auto-edit via CapCut/Canva",
            "publish": ["TikTok @lemmi1_", "Instagram @lemmi1_"],
        })
    return {"date": plan_date, "clips": clips}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Generate a deterministic, no-API daily content plan.",
        epilog='Example: python3 content/daily_content_plan.py --topic "build log" --count 3',
    )
    parser.add_argument("--topic", action="append", dest="topics", help="Topic to include; repeat for more topics.")
    parser.add_argument("--count", type=int, default=4, help="Number of clips, clamped to 3-5 (default: 4).")
    parser.add_argument("--date", help="Optional YYYY-MM-DD label; defaults to today.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    try:
        plan = build_plan(args.topics or TOPICS, args.count, args.date)
    except ValueError as error:
        raise SystemExit(str(error)) from error
    print(json.dumps(plan, indent=2))


if __name__ == "__main__":
    main()
