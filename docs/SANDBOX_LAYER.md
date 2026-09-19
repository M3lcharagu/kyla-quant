# GitHub cloud sandbox

Kyla sandbox runs execute on a fresh `ubuntu-latest` GitHub-hosted runner, with a 15-minute timeout and `contents: read`. Output is streamed to `artifacts/kyla-sandbox.log` and uploaded with `actions/upload-artifact@v4`, even when the command fails. The workflow preserves the command's exit status.

## Manual UI

Open [Run workflow](https://github.com/M3lcharagu/kyla-quant/actions/workflows/kyla-sandbox.yml), choose `main`, enter the required **command**, optionally enter a repository **script** path, and select **Run workflow**. A supplied script takes precedence over the command.

## GitHub CLI

```sh
./scripts/kyla_sandbox.sh 'python3 -m pytest -q'
./scripts/kyla_sandbox.sh --script scripts/smoke.sh
./scripts/kyla_sandbox.sh --repo M3lcharagu/kyla-quant 'python3 -V'
```

The wrapper checks for `gh` and authentication, dispatches the workflow, watches the newest run with `--exit-status`, prints its URL, and returns failure when the run fails. Install/authenticate the CLI with `brew install gh` and `gh auth login`.

## Exact repository-dispatch curl

Set `GITHUB_TOKEN` to a token allowed to dispatch workflows; do not put secrets in the command or script input. Use GitHub Actions secrets for sensitive values consumed by the workflow.

```sh
curl --fail-with-body --request POST \
  --url https://api.github.com/repos/M3lcharagu/kyla-quant/dispatches \
  --header "Accept: application/vnd.github+json" \
  --header "Authorization: Bearer ${GITHUB_TOKEN}" \
  --header "X-GitHub-Api-Version: 2022-11-28" \
  --header "Content-Type: application/json" \
  --data '{"event_type":"kyla-sandbox","client_payload":{"command":"python3 -V","script":""}}'
```

The `event_type` must be `kyla-sandbox`; `client_payload.command` and `client_payload.script` are accepted by the workflow. The workflow dispatch endpoint is exactly `POST https://api.github.com/repos/M3lcharagu/kyla-quant/dispatches`.

## Cost and safety

GitHub-hosted Actions are free for public repositories subject to GitHub policy, runner availability, and usage limits. Private repositories include 2,000 Actions minutes/month on the Free plan; verify current billing and limits before relying on it. Never include API keys, passwords, tokens, or other secrets in command/script input or logs. Store sensitive values in GitHub repository or environment secrets and reference them from the workflow only when needed.

This cloud sandbox replaces the local Docker requirement for launch-night smoke commands; it does not require starting Docker Desktop.
