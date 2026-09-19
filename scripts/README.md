# KYLA launch scripts

This directory contains a deliberately small, dependency-free launch helper for the Catalina launch-night runbook.

## `kyla_boot.py`

`kyla_boot.py` uses only Python 3’s standard library. It does not install packages, mutate configuration, call an API, contact a network service, or print secret values.

From the repository root:

```sh
python3 scripts/kyla_boot.py --check
```

The default mode checks:

- the expected repository files and directories;
- that the checkout is a readable Git repository;
- whether common operator commands are present (`brew`, `node`, `npm`, `git`, `code`, and `docker`);
- whether the Docker daemon is ready when Docker is installed; and
- whether a local `config.yaml` needs a manual secret-safety review.

A missing optional command is reported as a warning. Missing project files, an unreadable checkout, or an installed-but-unavailable Docker daemon are failures. The script does not assume every launch uses every integration.

Print a command without running it:

```sh
python3 scripts/kyla_boot.py --print-command
```

After human approval, pass an argument vector after `--` to run it in the repository root:

```sh
python3 scripts/kyla_boot.py -- docker compose up --build
```

Passing arguments rather than a shell string avoids shell parsing and prevents accidental expansion of secrets. `KYLA_BOOT_COMMAND` is intentionally not shell-evaluated and is ignored by the runner; use explicit arguments after `--`.

## Optional shell wrapper

If executable permissions are preserved after checkout, the convenience wrapper can be used as:

```sh
scripts/kyla.sh --check
```

If permissions were not preserved, invoke it with `sh scripts/kyla.sh --check` or run `python3 scripts/kyla_boot.py` directly.

## Related runbook

See [`docs/LAUNCH_NIGHT.md`](../docs/LAUNCH_NIGHT.md) for the full Catalina preparation, safety gate, smoke-launch, shutdown, and rollback checklist. It links only to official vendor documentation:

- [Homebrew 7.0.0](https://brew.sh/2026/09/13/homebrew-7.0.0/)
- [Node.js downloads](https://nodejs.org/en/download)
- [Apple TN2339](https://developer.apple.com/library/archive/technotes/tn2339/_index.html)
- [Git for macOS](https://git-scm.com/install/mac)
- [VS Code requirements](https://code.visualstudio.com/docs/supporting/requirements)
- [MetaTrader 5 on macOS](https://www.metatrader5.com/en/terminal/help/start_advanced/install_mac)
- [Docker Desktop on Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
- [Docker Desktop release notes](https://docs.docker.com/desktop/release-notes/)
