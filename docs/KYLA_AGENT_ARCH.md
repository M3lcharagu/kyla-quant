# KYLA agent framework (v0.2)

This is the friendly map of KYLA for Mel: a small team of workers, one dispatcher,
one safety gate, and fourteen named rooms. The code is intentionally understandable
before it is ambitious.

## The workers

`kyla/agents.py` is the roster. There are seven workers: Claude, Codex, Copilot,
Cursor, Docker Agent, Droid, and Shell. Each record says what the worker is for,
which domains it covers (trading, software, websites, content, copywriting,
publishing, photography, client work, CS study, business ops, research, QA, and
life accountability), what it can receive and produce, and whether it is a `stub`.
A stub is a safe interface and a named place to grow; it is not a claim that a live
vendor connection exists.

## SOPHIA, the dispatcher

`kyla/sophia.py` is SOPHIA. `broadcast(message)` puts the same message in every
worker's in-memory inbox. `route(message)` uses deterministic keyword rules so a
human can predict the handoff. A trading request reports `agent="quant"` and
`domain="trading"`, but records `agent_id="shell"`: there is no worker with the
id `quant`, so Shell is the real v0.2 trading/research recipient. Website requests
go to Cursor's website domain; edit requests go to Claude's content domain.

The inbox is a sandbox dictionary, not a queue service. Restarting Python clears it.
A persisted JSON store, retries, authentication, and real adapters are future work.

## R13, the gatekeeper

`kyla/r13_gate.py` is the deterministic R13 v0.1 gate. It checks for common secret
shapes (`sk-`, `AKIA`, long `0x` hex values, and `password=`), checks URLs against a
small allowed-domain list, requires evidence markers for trading and publishing
outputs, and blocks obvious financial advice aimed at clients or other third
parties. It returns a report with PASS/FAIL, individual checks, evidence state,
license notes, and a disclaimer.

R13 is not an LLM reviewer, a lawyer, or a financial adviser. It is a repeatable
first filter. A human should still review context, licenses, evidence, and risk.

## The fourteen rooms

`kyla/workflows.py` names fourteen rooms: PRIDE, GREED, LUST, ENVY, GLUTTONY,
WRATH, SLOTH, CHASTITY, TEMPERANCE, CHARITY, DILIGENCE, PATIENCE, KINDNESS, and
HUMILITY. Each room records its agents, domain, inputs, outputs, and cadence
(`daily`, `weekly`, or `on-demand`). A room is an SOP-shaped recipe, not an
autonomous promise.

## Sandbox + GitHub

GitHub is the source-of-truth sandbox for this framework. Changes land as a commit,
with tests kept beside the code. The existing repository's `kyla-sandbox` workflow
can run a supplied command on Ubuntu and save a log artifact. This makes it possible
to inspect a change before connecting any live account or external service.

The current implementation is a stub where it should be: no model calls, no vendor
credentials, no live trading, no automatic publishing, and no hidden background
worker. Real adapters can be added behind these small interfaces only after their
credentials, permissions, rate limits, tests, and human approval paths are explicit.
