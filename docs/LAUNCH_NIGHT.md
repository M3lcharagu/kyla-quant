# KYLA Quant — Catalina launch night checklist

This is the operator runbook for a clean macOS Catalina launch-night setup. Work from a fresh Terminal window, keep secrets out of shell history, and check every box in order. The kit is intentionally conservative: it verifies the host and project before attempting to start anything.

> **Scope:** macOS Catalina (10.15) host preparation and a local KYLA Quant smoke start. This document does not install software or create credentials for you.

## 0. Launch-night rules

- [ ] Confirm the Mac is the machine you intend to use and that you have an administrator account.
- [ ] Connect stable power and network; close unrelated high-load applications.
- [ ] Record the repository branch and commit before changing anything:
  ```sh
  git -C kyla-quant status --short --branch
  git -C kyla-quant rev-parse HEAD
  ```
- [ ] Never paste API keys, broker passwords, seed phrases, or account tokens into this checklist, an issue, or a terminal transcript.
- [ ] Use a demo/paper account for launch night. Do not enable live trading until the smoke test, risk limits, and human approval are complete.

## 1. macOS and Apple command-line tools

- [ ] Install all pending Catalina system updates and restart if macOS requests it.
- [ ] Open **System Preferences → Security & Privacy → Privacy** and grant only the minimum permissions requested by the tools below.
- [ ] Install Apple Command Line Tools if needed:
  ```sh
  xcode-select --install
  xcode-select -p
  ```
  Official Apple reference: [TN2339 — Building from the Command Line with Xcode FAQ](https://developer.apple.com/library/archive/technotes/tn2339/_index.html)
- [ ] Confirm the selected developer directory is valid:
  ```sh
  xcrun --find git
  ```
- [ ] If the installer reports that the tools are already installed, continue; do not repeatedly reinstall them.

## 2. Homebrew

- [ ] Install or update Homebrew using the official instructions. For this launch kit, use the Homebrew 7.0.0 release guidance: [Homebrew 7.0.0](https://brew.sh/2026/09/13/homebrew-7.0.0/).
- [ ] Verify the installation and shell environment:
  ```sh
  brew --version
  brew doctor
  ```
- [ ] If `brew` is not found after installation, follow the installer’s printed shell configuration command, then open a new Terminal window.
- [ ] Do not use a third-party tap for launch-night dependencies unless it has been reviewed and approved.

## 3. Runtime and source control

- [ ] Install the supported Node.js release from the official download page: [Node.js downloads](https://nodejs.org/en/download).
- [ ] Verify Node and npm:
  ```sh
  node --version
  npm --version
  ```
- [ ] Install Git using the official macOS instructions: [Git for macOS](https://git-scm.com/install/mac).
- [ ] Verify Git identity and repository access without printing credentials:
  ```sh
  git --version
  git config --get user.name
  git config --get user.email
  git -C kyla-quant remote -v
  ```
- [ ] Clone or open the repository on `main`, then confirm a clean working tree before launch preparation.

## 4. Operator tools

- [ ] Install Visual Studio Code only if it is part of your operator workflow; review the official platform requirements first: [VS Code requirements](https://code.visualstudio.com/docs/supporting/requirements).
- [ ] Confirm the `code` command is available, or open the project from the VS Code application:
  ```sh
  code --version
  ```
- [ ] Install MetaTrader 5 only when the broker/integration requires it, following the official macOS installation guide: [MetaTrader 5 — installation on macOS](https://www.metatrader5.com/en/terminal/help/start_advanced/install_mac).
- [ ] Open MetaTrader 5 once, complete its broker/demo login interactively, and verify that the intended account is selected. Do not store the password in this repository.
- [ ] Install Docker Desktop using the official guide: [Install Docker Desktop on Mac](https://docs.docker.com/desktop/setup/install/mac-install/).
- [ ] Check Docker Desktop’s release notes before upgrading or troubleshooting: [Docker Desktop release notes](https://docs.docker.com/desktop/release-notes/).
- [ ] Start Docker Desktop manually and wait until it reports that Docker is running:
  ```sh
  docker version
  docker info
  ```

## 5. Repository and configuration

- [ ] From the repository root, verify the expected project shape:
  ```sh
  test -f Dockerfile
  test -f config.example.yaml
  test -d src
  test -f requirements.txt
  ```
- [ ] Create a local configuration from the example only if the project’s current configuration contract requires it. Keep the real file untracked:
  ```sh
  cp config.example.yaml config.yaml
  git status --short
  ```
- [ ] Replace every placeholder with a demo/paper value using the project’s approved secret-management path.
- [ ] Confirm `.gitignore` covers local configuration, credentials, logs, caches, and runtime state. If it does not, stop and fix that before adding secrets.
- [ ] Do not commit `config.yaml`, `.env` files, broker exports, private keys, or terminal logs.
- [ ] Check for accidental secrets before starting:
  ```sh
  git diff --check
  git status --short
  ```

## 6. Dependency-free preflight

The included script uses only Python’s standard library. It does not install packages, contact a network service, or read secret values. Run it from the repository root:

```sh
python3 scripts/kyla_boot.py --check
```

- [ ] Review every `PASS`, `WARN`, and `FAIL` line.
- [ ] Treat missing required project files, an unavailable Python 3 interpreter, or a failing Docker daemon as a stop condition.
- [ ] A missing optional command is acceptable only when that integration is not part of tonight’s launch.
- [ ] To print the exact command that would be used for a controlled application start without running it:
  ```sh
  python3 scripts/kyla_boot.py --print-command
  ```
- [ ] If a start command has been explicitly approved, pass it after `--` (or set `KYLA_BOOT_COMMAND`) and review it before execution:
  ```sh
  python3 scripts/kyla_boot.py -- docker compose up --build
  ```

## 7. Smoke launch — demo/paper only

- [ ] Confirm the selected broker/demo account, symbol universe, time zone, and market-data mode.
- [ ] Confirm position size, maximum daily loss, maximum open positions, and kill-switch behavior.
- [ ] Confirm the machine clock and time zone are correct; do not trade on stale data.
- [ ] Run the preflight once more immediately before starting.
- [ ] Start the approved command in a visible terminal session. Keep the terminal open for the first observation window.
- [ ] Verify the service reaches a healthy/ready state and that logs contain no authentication, connectivity, or schema errors.
- [ ] Verify that an order cannot be submitted accidentally during the smoke test; use dry-run/paper mode and a deliberately small test scope.
- [ ] Observe at least one complete data/update cycle and record the timestamp, selected account, and outcome in the operator log.

## 8. Go/no-go gate

### Go only when all are true

- [ ] Preflight has no required failures.
- [ ] Docker/other required runtime is healthy.
- [ ] Demo/paper credentials work without being stored in Git.
- [ ] Market data is current and the expected instrument mapping is visible.
- [ ] Risk limits and the kill switch were checked by a human.
- [ ] The operator knows how to stop the process and has the logs available.

### No-go / stop immediately when any are true

- [ ] A live account, unknown account, or unapproved broker is selected.
- [ ] Secrets appear in `git diff`, logs, screenshots, or shell history.
- [ ] Data is stale, symbols are mismatched, or time zones are unclear.
- [ ] A risk limit, kill switch, or shutdown path is untested.
- [ ] Docker or the service is repeatedly restarting, unhealthy, or producing unexplained errors.

## 9. Shutdown and rollback

- [ ] Stop the application using its documented graceful shutdown command.
- [ ] Confirm no new orders/jobs are being submitted and that open work is accounted for.
- [ ] Stop the local runtime only after the application has stopped:
  ```sh
  docker compose down
  ```
- [ ] Preserve only sanitized logs and the launch timestamp; remove credentials and sensitive payloads.
- [ ] Record the exact Git commit, configuration version (not its secret values), runtime versions, and observed result.
- [ ] If behavior is unexpected, disable the integration/kill switch, stop the runtime, and do not retry with live funds.

## 10. Exit record

Fill this in after the smoke test, without recording secrets:

- **Date/time and time zone:** ______________________________
- **Git commit:** __________________________________________
- **Operator:** ____________________________________________
- **Runtime versions:** ____________________________________
- **Account mode (demo/paper/live):** ______________________
- **Data/instrument scope:** _______________________________
- **Preflight result:** _____________________________________
- **Smoke-test result:** ____________________________________
- **Go/no-go decision and approver:** _______________________
- **Follow-up issue or note:** _____________________________
