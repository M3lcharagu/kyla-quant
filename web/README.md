# KYLA mobile PWA

`web/` is a build-free vanilla JavaScript dashboard with one `web/index.html`, no framework/CDN dependency, and an offline-capable service worker.

## Tabs

- **QUANT** — dashboard KPIs, interactive strategy cards, and the source evidence table.
- **AUTOPILOT** — read-only paper-trading status and documented schedule.
- **3D HUB** — link to the separate KYLA OS spatial deployment.
- **PRODUCTS** — links to the two static product pages.
- **AGENTS** — exactly seven repository workers: claude, codex, copilot, cursor, docker-agent, droid, shell. Cards show repository-based roles, personality, handles, input/output sources, and a local command form.
- **WORKFLOWS** — exactly 17 entries: three n8n recipes plus Wrath, Greed, Sloth, Pride, Lust, Envy, Gluttony, Chastity, Temperance, Charity, Diligence, Patience, Kindness, Humility.

## AGENTS command queue

Submitting a command only appends `{agent, command, queuedAt, status}` to the browser `localStorage` key `kylaPendingCommandLog`. The UI labels this as a pending command queue with no real execution; it never sends commands to a shell, agent, or network service.

## WORKFLOWS data

`web/data/workflows.json` is the source for all 17 interactive cards. Each entry includes name, mapping, schedule, placeholder status, description, agents, inputs, and outputs. The registry is precached by `web/service-worker.js` and is suitable for offline review.

## 3D mode

The dashboard toggle applies a subtle CSS perspective to the app shell and a small `translateZ` lift to cards. It uses no WebGL and honors `prefers-reduced-motion`, keeping the effect lightweight for iPhone 11-class hardware.

## Install and Clicky

Serve `web/` over HTTPS, open `web/index.html` in Safari, then use **Share → Add to Home Screen**. The footer includes a Clicky badge and a commented optional snippet using `YOUR_SITE_ID`; enable it only after configuring a site, so the PWA remains offline-capable without analytics.
