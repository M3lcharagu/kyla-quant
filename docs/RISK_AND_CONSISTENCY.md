# Risk and consistency

Risk is fixed per trade and calculated from equity, stop distance, and the configured risk fraction. The funded-account default is 0.25%–0.5% of risk capital per trade; this scaffold defaults to 0.25%. Max daily loss, max trades per day, cooldown, news lock, and a manual kill switch are independent controls.

There is no martingale. A loss must not increase the next position size. A stale feed, invalid stop, event lock, daily limit, or missing approval fails closed. Paper execution must reconcile intended and actual fills and write a complete journal row.

Before paper or live progression, document:

- data source and freshness evidence;
- spread, slippage, and commission assumptions;
- stop/target and 43–45 minute exit behavior;
- daily loss and kill-switch test evidence;
- walk-forward and out-of-sample results;
- Mel approval.

This is a consistency control document, not financial advice and not a claim of profitability.
