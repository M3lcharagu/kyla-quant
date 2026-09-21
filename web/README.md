# KYLA mobile PWA

`web/` is a build-free, vanilla JavaScript dashboard for the `kyla-quant` repository. It is designed for a phone first and can be installed to an iPhone home screen as a standalone PWA.

## Install on iPhone Safari

1. Publish or serve this directory over HTTPS. Safari does not install service workers from ordinary `file://` pages.
2. Open the published `web/index.html` in Safari.
3. Tap **Share**, choose **Add to Home Screen**, edit the name to **KYLA** if needed, then tap **Add**.
4. Launch KYLA from the new home-screen icon. The app shell is cached for later launches; data refreshes when the network is available.

The PWA manifest is `manifest.webmanifest`. Add the real `icon-192.png` and `icon-512.png` files to `web/icons/` when they are ready. See `web/icons/README.txt`; no binary icon files are generated here.

## Free static hosting

- **Vercel:** import the repository as a static project, keep the repository root as the project root, and use no build command. The dashboard URL is `/web/`. If the project root is set to `web/` instead, also publish the referenced `docs/` and `products/` paths or adjust those links for that deployment.
- **GitHub Pages or another static host:** publish the repository root as static files and open `/web/`. No bundler, package manager, server runtime, or external CDN is required.
- For local review, run a simple static server from the repository root, for example `python3 -m http.server`, then open `http://localhost:8000/web/`. Do not open the HTML directly as a `file://` URL if you want service-worker behavior.

## Clicky analytics

Mel, [sign up free at https://heyclicky.com](https://heyclicky.com), then create a site for the deployed URL. Paste that site's ID into the `YOUR_SITE_ID` placeholder in this snippet before deploying:

```html
<script async data-id="YOUR_SITE_ID" src="https://static.getclicky.com/js"></script>
```

## Updating dashboard data

Overwrite `web/data/dashboard.json` with verified values after a run. Keep the keys used by the dashboard:

```json
{
  "placeholder": false,
  "paper_trades": 42,
  "win_rate": 54.8,
  "strategies_passing": 2,
  "last_backtest_date": "2026-09-21",
  "updated_at": "2026-09-21T22:00:00Z",
  "source": "Describe the run or report used"
}
```

`win_rate` is a number in percent, not a decimal. Do not present fabricated performance as live evidence: keep `placeholder` true until the source run is documented.

## Optional paper-trade journal

When available, the dashboard looks for `journal/paper_trades.json`, `paper_trades.json`, and `web/data/paper_trades.json`. It accepts an array of trades or an object containing a `trades`/`paper_trades` array. The autopilot schedule displayed in the app mirrors `scripts/autopilot.sh`: paper checks every 15 minutes during 09:00–16:00, a daily backtest at 22:00, and a Sunday journal report at 18:00 (host scheduler timezone).
