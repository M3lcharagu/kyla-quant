"""SOPHIA v0.2: a deterministic dispatcher with in-memory inboxes."""

from typing import Dict, List, Mapping, Union

from .agents import AGENTS, get_agent


# The inbox store is deliberately simple. Persistence can be added without changing
# the public broadcast/route API.
INBOXES: Dict[str, List[object]] = {agent["id"]: [] for agent in AGENTS}


def broadcast(message: object) -> Dict[str, object]:
    """Append ``message`` to every real agent inbox and report the recipients."""

    recipients = []
    for agent in AGENTS:
        agent_id = agent["id"]
        INBOXES[agent_id].append(message)
        recipients.append(agent_id)
    return {"message": message, "recipients": recipients}


def _decision(requested_agent: str, agent_id: str, domain: str, keyword: str) -> Dict[str, str]:
    return {
        "requested_agent": requested_agent,
        "agent": requested_agent,
        "agent_id": agent_id,
        "domain": domain,
        "matched_keyword": keyword,
    }


def route(message: Union[str, Mapping[str, object]]) -> Dict[str, str]:
    """Route a message using stable keyword precedence.

    ``quant`` is a useful public routing label, but it is not a registered worker
    id in v0.2. Trading requests therefore use the ``shell`` worker as the real
    recipient while retaining ``agent='quant'`` for a clear caller-facing result.
    """

    text = str(message if isinstance(message, str) else message.get("message", message)).casefold()
    rules = (
        (("trade", "trading", "forex", "crypto", "market"), "quant", "shell", "trading"),
        (("website", "web site", "webpage"), "cursor", "cursor", "websites"),
        (("edit", "editing", "content"), "claude", "claude", "content"),
        (("publish", "publishing", "newsletter"), "docker-agent", "docker-agent", "publishing"),
        (("photo", "photography", "image"), "cursor", "cursor", "photography"),
        (("client", "customer"), "copilot", "copilot", "client work"),
        (("cs study", "computer science", "study"), "droid", "droid", "CS study"),
        (("qa", "quality assurance", "test"), "codex", "codex", "QA"),
        (("business", "operations", "ops"), "copilot", "copilot", "business ops"),
        (("research", "investigate"), "claude", "claude", "research"),
        (("accountability", "habit", "life"), "droid", "droid", "life accountability"),
    )
    for keywords, requested, actual, domain in rules:
        for keyword in keywords:
            if keyword in text:
                return _decision(requested, actual, domain, keyword)

    # The default is a review/research handoff, keeping unknown messages safe and visible.
    return _decision("claude", "claude", "research", "default")


def clear_inboxes() -> None:
    """Empty all in-memory inboxes; useful for tests and local sandbox runs."""

    for inbox in INBOXES.values():
        inbox.clear()
