#!/usr/bin/env node
'use strict';

/**
 * KYLA paper-signal scaffold.
 * No network calls, broker calls, live execution, or performance claims.
 */

const REQUIRED = ['time', 'open', 'high', 'low', 'close'];

function validateCandles(candles) {
  if (!Array.isArray(candles) || candles.length === 0) {
    return { ok: false, reason: 'Expected a non-empty JSON array of candles.' };
  }
  for (let i = 0; i < candles.length; i += 1) {
    const candle = candles[i];
    if (!candle || REQUIRED.some((key) => typeof candle[key] !== 'number' || !Number.isFinite(candle[key]))) {
      return { ok: false, reason: `Invalid candle at index ${i}; required numeric fields: ${REQUIRED.join(', ')}.` };
    }
    if (candle.high < Math.max(candle.open, candle.close) || candle.low > Math.min(candle.open, candle.close) || candle.high < candle.low) {
      return { ok: false, reason: `Invalid OHLC relationship at index ${i}.` };
    }
  }
  return { ok: true };
}

/**
 * Reserved interface for the reviewed trendline + POI + FVG strategy.
 * See strategy_placeholder.md. Until the rules are specified and gated, HOLD.
 */
function trendlinePoiFvgScaffold() {
  return {
    implemented: false,
    action: 'HOLD',
    reason: 'Trendline + POI + FVG rules are a reviewed placeholder, not implemented.'
  };
}

function paperSignal(candles) {
  const validation = validateCandles(candles);
  if (!validation.ok) {
    return { mode: 'paper', action: 'HOLD', accepted: false, reason: validation.reason };
  }

  const strategy = trendlinePoiFvgScaffold(candles);
  return {
    mode: 'paper',
    action: strategy.action,
    accepted: false,
    strategy: 'trendline-poi-fvg-placeholder',
    reason: strategy.reason,
    live_execution: false,
    disclaimer: 'Research scaffold only; not financial advice or production execution.'
  };
}

async function main() {
  const file = process.argv[2];
  if (!file) {
    console.error('Usage: node trading/paper_signal.js path/to/candles.json');
    process.exitCode = 2;
    return;
  }

  try {
    const raw = await require('node:fs').promises.readFile(file, 'utf8');
    const candles = JSON.parse(raw);
    process.stdout.write(`${JSON.stringify(paperSignal(candles), null, 2)}\n`);
  } catch (error) {
    process.stdout.write(`${JSON.stringify({ mode: 'paper', action: 'HOLD', accepted: false, reason: `Could not read valid candle JSON: ${error.message}` }, null, 2)}\n`);
    process.exitCode = 1;
  }
}

if (require.main === module) main();

module.exports = { paperSignal, trendlinePoiFvgScaffold, validateCandles };
