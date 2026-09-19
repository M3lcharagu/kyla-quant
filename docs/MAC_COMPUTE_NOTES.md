# Mac compute notes

Target constraints: an 8GB Intel Mac, with Docker capped at 3–4GB memory. Prefer a small Python environment, modest data windows, and sequential jobs. Do not run several backtests, feature builds, or containers concurrently.

Whisper is not needed here. This repository is market-data and QA focused; no speech-to-text dependency is required.

Recommended habits:

- use Docker or a virtual environment, not both for the same job;
- process one symbol/timeframe and one walk-forward fold at a time;
- write intermediate artifacts to ignored paths;
- cap worker counts at one unless memory has been measured;
- close notebooks and delete stale cache files before long runs;
- use small smoke datasets before full validation;
- record hardware, Python version, data snapshot, and commit hash in reports.

These are operational constraints, not performance guarantees.
