# Claude setup for KYLA

This guide gives Mel two safe ways to work with Claude on `kyla-quant`. The repository is a research and paper-trading scaffold: keep changes reviewable, local credentials private, and the R13 gate in place.

## Path A: Claude Code CLI

Claude Code works from a checked-out repository and can inspect the files that are available in that working directory.

```bash
npm install -g @anthropic-ai/claude-code
cd kyla-quant
claude
```

When Claude Code asks you to authenticate, complete the browser login with the appropriate ChatGPT/Claude account for the service you are using. Claude Code itself uses the Anthropic/Claude account associated with your plan; use a ChatGPT account only in the separate ChatGPT workflow where it applies. Never paste a password, session cookie, or API key into the terminal transcript, a chat, or a GitHub issue.

### How KYLA specs drive Claude's builds

- **KYLA writes the specification.** New requirements, acceptance criteria, safety constraints, and implementation notes are written under `docs/` (for example, a new `*_SPEC.md`).
- **Claude Code implements the specification.** In the repository root, ask Claude Code to read the named spec, inspect the relevant existing code, propose a small plan, implement it, and show the diff for review.
- **The human owner approves the result.** Tests, security review, paper-only boundaries, and the R13 review remain required; a spec is not permission to deploy or place live orders.

To feed Claude a new spec:

1. Put the approved spec in `docs/` and give it a clear filename.
2. Start Claude Code from the repository root: `cd kyla-quant && claude`.
3. Tell it exactly which file to read, for example: `Read docs/NEW_FEATURE_SPEC.md, summarize the acceptance criteria, then implement only that scope.`
4. Ask for a plan and a diff before accepting edits. Point Claude to related files and tests when the spec depends on them.
5. Review the changes locally, run the appropriate checks, and record any follow-up spec changes under `docs/`.

### MCP note (Phase 2)

MCP is **not required for the current CLI workflow**. It is a Phase 2 integration for when KYLA exposes MCP servers that Claude can call. Until those servers, permissions, and audit boundaries exist, feed Claude approved files from `docs/` and keep access limited to the local repository.

## Path B: Anthropic API key

Use this path only when a KYLA agent needs to call the Anthropic API programmatically.

1. Create or retrieve the key at [console.anthropic.com](https://console.anthropic.com/).
2. In the repository root, create a local file named `.env` and add the key:

   ```dotenv
   ANTHROPIC_API_KEY=your_real_key_goes_here
   ```

   `your_real_key_goes_here` is a placeholder, not a credential. Replace it only in your private local `.env`; never put a real key in this document, a chat, a screenshot, a log, or GitHub.
3. Confirm that `.gitignore` contains `.env`, `.env.*`, and `!.env.example`. This repository ignores those files while allowing the safe placeholder template.
4. Keep `.env` on the local machine with restrictive permissions where practical, and rotate/revoke the key at the Anthropic console if it is exposed.

### Safe Node.js example

This example uses the environment variable and contains no real key. It makes one small, explicitly requested call; it does not place trades or expose the key in its output.

```bash
set -a
. ./.env
set +a

node <<'NODE'
const key = process.env.ANTHROPIC_API_KEY;

if (!key || key === "your_anthropic_api_key_here" || key === "your_real_key_goes_here") {
  throw new Error("Set a real ANTHROPIC_API_KEY in the local .env file first.");
}

const response = await fetch("https://api.anthropic.com/v1/messages", {
  method: "POST",
  headers: {
    "content-type": "application/json",
    "x-api-key": key,
    "anthropic-version": "2023-06-01"
  },
  body: JSON.stringify({
    model: "claude-3-5-haiku-latest",
    max_tokens: 32,
    messages: [{ role: "user", content: "Return the word READY." }]
  })
});

console.log(`Anthropic API status: ${response.status}`);
console.log(await response.text());
NODE
```

Node 18+ provides the `fetch` API used above. The response should be inspected locally; do not paste a response containing sensitive project data into chat.

A simple key check that does not print the key is:

```bash
set -a; . ./.env; set +a
curl -fsS https://api.anthropic.com/v1/models \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  >/dev/null && echo "Anthropic API key accepted"
```

Anthropic API usage is pay-per-token. Prefer high-value, bounded tasks, use small prompts and output limits, and avoid polling or exploratory loops that can spend money without producing durable value. A successful status only verifies authentication; it does not approve a production or trading workflow.

## Secret boundary

- `.env` is for local secrets only; `.env.example` is the committed placeholder template.
- Placeholders are visibly fake (`your_anthropic_api_key_here`); real secrets must never appear in committed files.
- Never commit credentials, share them in chat, or put them in GitHub issues, pull requests, logs, screenshots, or generated reports.
- If a secret is ever exposed, revoke/rotate it immediately and review the repository history.
