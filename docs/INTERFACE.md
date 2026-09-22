# KYLA UI/UX specification

## Dashboard layout

The local shell is a fast, dependency-free dark premium UI:

1. Top bar: KYLA mark, `LOCAL / MOCK STATE`, R13 lock, truthful runtime note.
2. Hero: Kilimani command-center framing and visible `PAPER ONLY` boundary.
3. Status strip: SOPHIA broadcast, local runtime, storage posture, last audit; all statuses are local/mock.
4. Core grid: exactly `claude`, `codex`, `copilot`, `cursor`, `docker-agent`, `droid`, `shell`.
5. Specialist grid: exactly `trading`, `web dev`, `content creation`, `copywriting`, `publishing`, `photography`, `client work`, `CS study`, `business ops`, `research`, `QA`, `life accountability`.
6. Command panel, recent activity, and a static future-penthouse preview.
7. Footer guardrails: paper-only, no connected services, R13 checkpoint, no live execution.

## Command bar

The focusable local mock accepts `help` or `/help`, `status` or `/status`, `rooms`, and `open <room>`. Enter submits, Escape clears, and unknown commands become a local note. Nothing can place an order, publish, send a message, or claim an integration.

## WhatsApp command syntax (exact)

`/status` · `/trade` · `/content` · `/help`

Whitespace after a command may be ignored; aliases must not silently expand actions. `/trade` is paper-only, `/content` points to the local content plan, `/status` is local/mock, and `/help` returns this list. The optional adapter is non-production until reviewed.

## Voice and text

Text is the source of truth. Voice is opt-in, transcribed into a visible draft, has listening/stop/error states, and cannot bypass R13 or approvals. The base dashboard does not need microphone permission. Use concise confirmations, explicit uncertainty, and visible audit history.

## Mobile-first rules

Design from 320px upward; one-column cards first; 44px tap targets; no hover-only information; no horizontal scroll; safe-area insets; responsive type; portrait support; lazy-load future 3D; cap particles; respect reduced data/motion; keep 2D actions usable without WebGL, Docker, accounts, or third-party APIs.

## Accessibility/performance basics

Use semantic landmarks, one `h1`, labelled forms, keyboard order, visible focus, sufficient contrast, text labels in addition to color, `aria-live` command results, and `prefers-reduced-motion`. Keep assets local/small, avoid frameworks/analytics/polling in MVP, prevent layout shift, and provide a readable no-JS message. Check narrow width, keyboard-only, reduced motion, and JavaScript-disabled states; record actual checks rather than claiming unrun tests.
