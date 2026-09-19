"""Stdlib-only registry for KYLA's seven sandbox workers."""

from copy import deepcopy
from typing import Dict, List, Optional


AGENTS = (
    {
        "id": "claude",
        "name": "Claude",
        "role": "Research, writing, synthesis, and review worker",
        "domain": ["research", "content", "copywriting", "publishing", "QA"],
        "input_sources": ["briefs", "documents", "research notes", "review requests"],
        "output_sources": ["drafts", "summaries", "citations", "QA notes"],
        "status": "stub",
    },
    {
        "id": "codex",
        "name": "Codex",
        "role": "Software implementation and test worker",
        "domain": ["software", "websites", "QA"],
        "input_sources": ["issues", "specifications", "repositories", "test failures"],
        "output_sources": ["code", "tests", "patches", "technical notes"],
        "status": "stub",
    },
    {
        "id": "copilot",
        "name": "Copilot",
        "role": "Business operations and client-delivery worker",
        "domain": ["business ops", "client work", "software"],
        "input_sources": ["client briefs", "task lists", "operating procedures"],
        "output_sources": ["plans", "status updates", "checklists", "handoffs"],
        "status": "stub",
    },
    {
        "id": "cursor",
        "name": "Cursor",
        "role": "Website and visual-production worker",
        "domain": ["websites", "photography", "content"],
        "input_sources": ["design briefs", "assets", "wireframes", "image requests"],
        "output_sources": ["site changes", "image selects", "captions", "asset notes"],
        "status": "stub",
    },
    {
        "id": "docker-agent",
        "name": "Docker Agent",
        "role": "Reproducible sandbox and publishing worker",
        "domain": ["publishing", "content", "business ops"],
        "input_sources": ["build instructions", "release checklists", "content packages"],
        "output_sources": ["sandbox artifacts", "published packages", "build logs"],
        "status": "stub",
    },
    {
        "id": "droid",
        "name": "Droid",
        "role": "Personal accountability, study, and client-support worker",
        "domain": ["CS study", "client work", "life accountability"],
        "input_sources": ["goals", "study plans", "client questions", "daily check-ins"],
        "output_sources": ["reminders", "study prompts", "follow-ups", "progress logs"],
        "status": "stub",
    },
    {
        "id": "shell",
        "name": "Shell",
        "role": "Trading research, automation, and operational worker",
        "domain": ["trading", "research", "business ops", "life accountability"],
        "input_sources": ["market data", "research prompts", "commands", "journals"],
        "output_sources": ["analysis", "backtest reports", "automation logs", "risk notes"],
        "status": "stub",
    },
)

_AGENT_BY_ID = {agent["id"]: agent for agent in AGENTS}


def get_agent(id: str) -> Optional[Dict[str, object]]:
    """Return a copy of an agent record, or ``None`` for an unknown id."""

    return deepcopy(_AGENT_BY_ID.get(id))


def list_agents(domain: Optional[str] = None) -> List[Dict[str, object]]:
    """Return all agents, or those whose domain list contains ``domain``."""

    if domain is None:
        return [deepcopy(agent) for agent in AGENTS]
    wanted = domain.strip().casefold()
    return [
        deepcopy(agent)
        for agent in AGENTS
        if any(wanted == str(agent_domain).casefold() for agent_domain in agent["domain"])
    ]
