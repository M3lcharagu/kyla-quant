# KYLA v0.2 dashboard prototype

A single-file browser prototype for KYLA, styled as a dark-luxury research operations desk in a Kilimani penthouse. It is intentionally DOM/CSS-first: the skyline is inline SVG/CSS, the interaction is inline JavaScript, and there is no build step, framework, or external CDN dependency. An optional Google Fonts integration can be added later without changing the local-first fallback.

## Open it

- Double-click `index.html` and open it in a browser, or
- Serve the directory locally:

  ```bash
  cd dashboard
  python3 -m http.server
  ```

  Then visit the local address printed by Python.

The command line is a small interaction prototype. Type `help` (or a command beginning with `help`) to see its console-style response. Other input is acknowledged as a future shell command.

## What is here

- KYLA wordmark and v0.2 command-deck framing
- Pure CSS/SVG Nairobi skyline silhouette
- Mac, sandbox, triggers, and quant-engine status placeholders
- Seven agent cards with initials, status dots, roles, and domain tags
- A responsive paper-only watchlist and local command console

## Next work

1. Add rooms for agent conversations, notes, and decision trails.
2. Connect the dashboard to live market data and real trigger state.
3. Add voice input/output and a richer command router.
4. Explore WebGL/three.js later for hero scenes; keeping the interface DOM/CSS-first helps it stay smooth on a 2012 Mac.

This is a **design prototype**, not a live product and not connected to a backend, broker, market-data feed, or execution system. All values and statuses shown are illustrative placeholders.
