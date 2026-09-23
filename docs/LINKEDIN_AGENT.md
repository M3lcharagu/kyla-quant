# KYLA LinkedIn agent integration note

## Verdict

**USEFUL narrowly.** Treat [`linkedin-agent-skill`](https://github.com/Jakeschincariol/linkedin-agent-skill) as a drafting + humanization module for KYLA's content lane—not as a LinkedIn automation layer. Retain KYLA's seven-agent orchestration and manual publishing.

This note records a research snapshot, not a promise that the upstream project or LinkedIn will behave the same way in the future.

## What was verified

Upstream repository: <https://github.com/Jakeschincariol/linkedin-agent-skill>

- License: MIT (repository metadata and [`LICENSE`](https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/LICENSE)).
- Stars: **608**.
- Latest push: **September 17, 2026** (`2026-09-17T11:27:52Z` in the GitHub repository metadata).
- The star count and activity date are **time-sensitive research snapshot values**, observed on September 23, 2026 UTC; they can change.
- The upstream README describes eleven free Claude skills, no signup, and no API key. This note does not add a dependency, credential, LinkedIn API access, or publishing integration.

## The eleven skills and their functions

The following names and boundaries are the upstream content-lane surface, kept intentionally narrow:

1. `li-post` — drafts posts from 3 hook options.
2. `li-comment` — comments on other people's posts.
3. `li-reply` — handles replies under your posts.
4. `li-profile` — audits/rewrites profiles.
5. `li-plan` — plans weekly content/engagement.
6. `li-human` — local humanizer with typography cleanup, 113-term slop replacement, and 5 heuristic checks.
7. `li-carousel` — creates carousel copy/PDF.
8. `li-repurpose` — repurposes content.
9. `li-dm` — drafts connection messages/follow-ups.
10. `li-inbox` — categorizes messages.
11. `li-audit` — ranks past posts.

`li-post` uses the hook catalog below and produces three hook options before a draft. `li-human` is the useful local boundary for KYLA: its Python scripts clean text and score it with heuristics; they do not call a detector service or publish anything.

## The 21 `hooks.json` formulas

Source file: [`skills/li-post/hooks.json`](https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/skills/li-post/hooks.json). The formula names and templates below mirror the upstream catalog. **Contrarian Take** and **Number Reveal** are confirmed source entries (IDs 1 and 2).

| # | Formula | Template |
|---:|---|---|
| 1 | **Contrarian Take** *(confirmed)* | `Everyone says {common advice}. After {specific experience}, I think that is wrong.` |
| 2 | **Number Reveal** *(confirmed)* | `I {did thing} for {N} {days/weeks}. Here is what actually happened.` |
| 3 | Mistake Confession | `{Specific cost} is what {one mistake} cost me.` |
| 4 | Before / After | `{Time ago} I was {low state}. Today I {high state}. The difference was {one thing}.` |
| 5 | The List Promise | `{N} things I wish someone had told me before {milestone}.` |
| 6 | Insider Secret | `After {N} years {doing thing}, here is the part nobody puts in the {job posting/course/pitch}.` |
| 7 | The Callout | `If you are still {doing outdated thing}, stop.` |
| 8 | Question Trap | `{Specific scenario with a real cost}. What do you do?` |
| 9 | Story Cold Open | `"{Line of dialogue}"` followed by `{Who said it, when, and why it mattered}.` |
| 10 | The Receipt | `{Screenshot or hard number}. {One sentence of context}.` |
| 11 | Myth Bust | `{Popular explanation} is not why {bad outcome} is happening to you.` |
| 12 | The Comparison | `{Expensive option} vs {cheap option}. {Surprising verdict}.` |
| 13 | Permission Slip | `You are allowed to {thing the reader feels guilty about}.` |
| 14 | Pattern Interrupt | `{One word or three-word line, full stop.}` |
| 15 | The Warning | `{Common practice} is quietly costing you {specific thing they care about}.` |
| 16 | Good vs Great | `Good {role} {do X}. Great {role} {do Y}.` |
| 17 | Time Anchor | `{Task} used to take me {long time}. It now takes {short time}.` |
| 18 | The Unpopular Rule | `I do not {widely accepted practice}. Ever. Here is why.` |
| 19 | Curiosity Gap | `The {superlative} {thing} I ever {verb} {broke the obvious rule}.` |
| 20 | The Walk-Away | `I {fired/quit/deleted/cancelled} {valuable thing}. {Result}.` |
| 21 | The Direct Value | `Here is the exact {artifact} I used to {specific outcome}. Steal it.` |

These are prompts, not evidence. Any number, result, testimonial, screenshot, or outcome inserted into a hook must be real and reviewable.

## How it operates

- **Claude Code / plugin:** use the upstream skill folders in Claude Code, or install the upstream plugin as described in its [`README`](https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/README.md).
- **Any Claude chat:** paste a relevant upstream `SKILL.md` into a chat. This is the portable route when Claude Code or a plugin is unavailable.
- **Local humanizer:** the `li-human` Python scripts run locally and dependency-free on the user's text. The upstream README describes typography cleanup, replacement of a 113-term slop lexicon, and a five-check heuristic panel. Nothing needs to be uploaded for those local passes.
- **Boundary:** generate, edit, review, and export copy; then a person manually publishes it. There is no API key, no LinkedIn API, and no auto-publish in this KYLA integration.

## Catalina and phone notes

- Claude Code requires macOS 13+, so **the paste-skills path is the Catalina route**.
- The Python scripts work locally on Catalina without third-party dependencies.
- Phone use works through a Claude chat, but without local Python; use the chat route for drafting and reserve local humanizer checks for a Mac that can run the scripts.

## KYLA assignment and limits

Use this only inside KYLA's **content lane**:

1. KYLA agents provide the factual brief, audience, voice constraints, and source material.
2. `li-post` supplies alternatives from the hook catalog; `li-human` is an optional local cleanup/check pass.
3. A human verifies facts, tone, disclosures, links, names, and claims.
4. A human manually publishes on LinkedIn.

Do not add these skills to KYLA's orchestration as autonomous agents, do not give them credentials, and do not turn them into a browser or posting bot. The integration does not change KYLA's seven-agent orchestration or manual-publishing rule. It also does not add Python packages, secrets, environment variables, LinkedIn API access, or auto-publishing.

## Safety, legal, and quality notes

- The upstream README explicitly says the skills do not post to LinkedIn and warns that browser or third-party automation can violate the [LinkedIn User Agreement](https://www.linkedin.com/legal/user-agreement) and restrict accounts. Manual publication is a safety boundary, not a missing feature.
- Treat DMs, inbox content, profile data, and engagement data as personal data. Minimize copying, redact unnecessary identifiers, obtain consent where appropriate, and do not paste confidential material into an unapproved chat.
- Review every generated claim and number against its source. Never let a hook invent metrics, clients, outcomes, or credentials. Preserve required sponsorship, affiliate, employment, and other disclosures.
- The five checks are local heuristics, not GPTZero, Originality, Copyleaks, Winston, Turnitin, or any other detector API; a score is not proof of authorship or compliance. “Humanizer” does not mean undetectable and is not a guarantee against platform review.
- The MIT license permits reuse subject to its terms and preserving the license notice; it does not grant permission to ignore LinkedIn rules or other third-party rights.

## Exact sources

- Upstream repository: <https://github.com/Jakeschincariol/linkedin-agent-skill>
- Upstream README / installation and limitations: <https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/README.md>
- Hook catalog: <https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/skills/li-post/hooks.json>
- Humanizer skill: <https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/skills/li-human/SKILL.md>
- MIT license: <https://github.com/Jakeschincariol/linkedin-agent-skill/blob/main/LICENSE>
- LinkedIn User Agreement: <https://www.linkedin.com/legal/user-agreement>
