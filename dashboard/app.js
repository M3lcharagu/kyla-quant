const coreAgents = [
  ["OR", "Orin", "Command center & context", "command"],
  ["SA", "Sable", "Risk & permissions", "risk"],
  ["CH", "Chroma", "Signal curation", "signals"],
  ["MA", "Maven", "Macro & regime", "macro"],
  ["VA", "Vale", "Execution planning", "execution"],
  ["EC", "Echo", "Journal & evidence", "journal"],
  ["LU", "Lumen", "Portfolio pulse", "portfolio"]
];

const specialists = [
  ["SP", "Sophia", "R13 QA / security / legal", "specialist"],
  ["DR", "Data reliability", "Freshness & provenance", "specialist"],
  ["RO", "Research ops", "Reproducible experiments", "specialist"],
  ["PO", "Product ops", "Content & delivery", "specialist"]
];

const grid = document.querySelector("#agent-grid");
const consoleEl = document.querySelector("#console");
const form = document.querySelector("#command-form");
const input = document.querySelector("#command");

function card([initials, name, role, tag], isSpecialist = false) {
  const article = document.createElement("article");
  article.className = "agent-card";
  article.innerHTML = `
    <div class="agent-top"><span class="avatar">${initials}</span><span class="agent-state">${isSpecialist ? "on call" : "ready"}</span></div>
    <div><div class="agent-name">${name}</div><div class="agent-role">${role}</div><span class="agent-tag">${tag}</span></div>`;
  return article;
}

coreAgents.forEach((agent) => grid.appendChild(card(agent)));
specialists.forEach((agent) => grid.appendChild(card(agent, true)));

function appendLine(text, className = "") {
  const line = document.createElement("p");
  if (className) line.className = className;
  line.textContent = text;
  consoleEl.appendChild(line);
  consoleEl.scrollTop = consoleEl.scrollHeight;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  const command = input.value.trim();
  if (!command) return;
  appendLine(`› ${command}`);
  const normalized = command.toLowerCase();
  const response = normalized === "help"
    ? "Available: help, rooms, status. This shell has no external actions."
    : normalized === "rooms"
      ? "Rooms: Orin, Sable, Chroma, Maven, Vale, Echo, Lumen + specialists on call."
      : normalized === "status"
        ? "Local shell / paper only / R13 locked / no live execution."
        : "Prototype shell: command recorded locally; no action taken.";
  appendLine(response);
  input.value = "";
});
