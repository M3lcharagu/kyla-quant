#!/usr/bin/env node
'use strict';

const fs = require('node:fs');
const path = require('node:path');

function help() {
  console.log(`Usage: node browser/open.js [options]

Open an approved HTTP(S) URL with Playwright, save visible body text and a screenshot, then exit.

Options:
  --url <url>                  URL (default: https://example.com)
  --out <path-without-ext>     Output prefix (default: browser/output/page)
  --headed                     Show the browser window
  --chrome                     Prefer a common local Chrome/Chromium path
  --executable-path <path>     Use this Chrome/Chromium executable
  --timeout <ms>               Navigation timeout (default: 30000)
  --help                       Show this help

Safety: only http/https URLs without embedded credentials are accepted. No CAPTCHA bypass.
`);
}

function parseArgs(argv) {
  const args = { url: 'https://example.com', out: path.join('browser', 'output', 'page'), headed: false, chrome: false, timeout: 30000 };
  for (let i = 0; i < argv.length; i += 1) {
    const token = argv[i];
    if (token === '--help') return { help: true };
    if (token === '--headed') args.headed = true;
    else if (token === '--chrome') args.chrome = true;
    else if (['--url', '--out', '--executable-path', '--timeout'].includes(token)) {
      const value = argv[++i];
      if (!value) throw new Error(`${token} requires a value`);
      if (token === '--url') args.url = value;
      if (token === '--out') args.out = value;
      if (token === '--executable-path') args.executablePath = value;
      if (token === '--timeout') args.timeout = Number(value);
    } else throw new Error(`Unknown option: ${token}`);
  }
  if (!Number.isInteger(args.timeout) || args.timeout < 1000) throw new Error('--timeout must be an integer >= 1000');
  const parsed = new URL(args.url);
  if (!['http:', 'https:'].includes(parsed.protocol) || parsed.username || parsed.password) throw new Error('URL must be http(s) without embedded credentials');
  return args;
}

function commonChromePath() {
  if (process.platform !== 'darwin') return undefined;
  const candidates = [
    '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    '/Applications/Chromium.app/Contents/MacOS/Chromium',
    `${process.env.HOME || ''}/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`,
  ];
  return candidates.find((candidate) => candidate && fs.existsSync(candidate));
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  if (args.help) return help();
  let chromium;
  try { ({ chromium } = require('playwright')); } catch (error) {
    throw new Error('Playwright is not installed. Run npm install, then optionally npx playwright install chromium.');
  }
  const executablePath = args.executablePath || process.env.CHROME_PATH || (args.chrome ? commonChromePath() : undefined);
  const browser = await chromium.launch({ headless: !args.headed, ...(executablePath ? { executablePath } : {}) });
  try {
    const page = await browser.newPage();
    await page.goto(args.url, { waitUntil: 'domcontentloaded', timeout: args.timeout });
    const text = await page.locator('body').innerText();
    fs.mkdirSync(path.dirname(args.out), { recursive: true });
    fs.writeFileSync(`${args.out}.txt`, `${text.trim()}\n`, 'utf8');
    await page.screenshot({ path: `${args.out}.png`, fullPage: true });
    console.log(JSON.stringify({ url: args.url, text: `${args.out}.txt`, screenshot: `${args.out}.png` }, null, 2));
  } finally { await browser.close(); }
}

main().catch((error) => { console.error(`Browser starter stopped: ${error.message}`); process.exitCode = 1; });
