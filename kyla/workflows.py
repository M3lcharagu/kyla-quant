"""The fourteen KYLA rooms: named, inspectable workflow recipes."""


WORKFLOWS = {
    "PRIDE": {
        "name": "PRIDE",
        "agents": ["shell", "claude"],
        "domain": "trading/research",
        "inputs": ["market context", "research question", "risk limits"],
        "outputs": ["evidence-backed research brief", "decision journal"],
        "cadence": "daily",
    },
    "GREED": {
        "name": "GREED",
        "agents": ["copilot", "codex"],
        "domain": "business ops/software",
        "inputs": ["opportunity list", "client needs", "capacity"],
        "outputs": ["prioritized backlog", "delivery plan"],
        "cadence": "weekly",
    },
    "LUST": {
        "name": "LUST",
        "agents": ["cursor", "droid"],
        "domain": "photography/client work",
        "inputs": ["visual brief", "assets", "client preferences"],
        "outputs": ["creative concepts", "asset shortlist", "client questions"],
        "cadence": "on-demand",
    },
    "ENVY": {
        "name": "ENVY",
        "agents": ["claude", "cursor"],
        "domain": "research/websites",
        "inputs": ["competitor examples", "research notes", "site goals"],
        "outputs": ["gap analysis", "website improvement brief"],
        "cadence": "weekly",
    },
    "GLUTTONY": {
        "name": "GLUTTONY",
        "agents": ["docker-agent", "shell"],
        "domain": "publishing/content",
        "inputs": ["content queue", "source material", "release checklist"],
        "outputs": ["packaged draft", "sandbox artifact", "release notes"],
        "cadence": "daily",
    },
    "WRATH": {
        "name": "WRATH",
        "agents": ["codex", "shell"],
        "domain": "QA/software",
        "inputs": ["failed test", "bug report", "reproduction steps"],
        "outputs": ["minimal fix", "regression test", "failure report"],
        "cadence": "on-demand",
    },
    "SLOTH": {
        "name": "SLOTH",
        "agents": ["droid", "docker-agent"],
        "domain": "life accountability/business ops",
        "inputs": ["overdue tasks", "daily plan", "friction notes"],
        "outputs": ["next smallest action", "accountability check-in"],
        "cadence": "daily",
    },
    "CHASTITY": {
        "name": "CHASTITY",
        "agents": ["claude", "docker-agent"],
        "domain": "content/publishing",
        "inputs": ["draft", "license information", "style guide"],
        "outputs": ["clean draft", "license/source notes", "publication checklist"],
        "cadence": "on-demand",
    },
    "TEMPERANCE": {
        "name": "TEMPERANCE",
        "agents": ["shell", "claude"],
        "domain": "trading/research",
        "inputs": ["strategy hypothesis", "backtest evidence", "risk budget"],
        "outputs": ["balanced review", "go/no-go conditions"],
        "cadence": "weekly",
    },
    "CHARITY": {
        "name": "CHARITY",
        "agents": ["droid", "claude"],
        "domain": "client work/CS study",
        "inputs": ["question", "learner context", "client context"],
        "outputs": ["plain-language explanation", "helpful handoff"],
        "cadence": "on-demand",
    },
    "DILIGENCE": {
        "name": "DILIGENCE",
        "agents": ["codex", "copilot"],
        "domain": "software/websites",
        "inputs": ["specification", "repository", "acceptance criteria"],
        "outputs": ["implemented change", "tests", "deployment checklist"],
        "cadence": "daily",
    },
    "PATIENCE": {
        "name": "PATIENCE",
        "agents": ["droid", "shell"],
        "domain": "life accountability/CS study",
        "inputs": ["long-term goal", "study log", "progress evidence"],
        "outputs": ["steady practice plan", "progress review"],
        "cadence": "weekly",
    },
    "KINDNESS": {
        "name": "KINDNESS",
        "agents": ["droid", "claude"],
        "domain": "client work/content",
        "inputs": ["audience needs", "draft response", "tone guidance"],
        "outputs": ["empathetic response", "clear next steps"],
        "cadence": "on-demand",
    },
    "HUMILITY": {
        "name": "HUMILITY",
        "agents": ["copilot", "claude"],
        "domain": "QA/research",
        "inputs": ["claim", "counterevidence", "review checklist"],
        "outputs": ["uncertainty log", "correction plan", "reviewed claim"],
        "cadence": "weekly",
    },
}


def get_workflow(name: str):
    """Return a workflow recipe by name, case-insensitively."""

    return WORKFLOWS.get(name.upper())


def list_workflows():
    """Return the fourteen workflow recipes in registry order."""

    return list(WORKFLOWS.values())
