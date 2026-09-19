# KYLA Quant — Catalina launch night checklist

Use a fresh Terminal, confirm the intended repository and branch, keep credentials out of shell history and logs, and use demo/paper settings until a human approves any live activity.

## Launch-night cloud sandbox

The GitHub-hosted sandbox replaces local Docker for launch-night smoke checks. Do not start Docker Desktop or a local container just to run these checks.

```sh
cd kyla-quant
git status --short
git rev-parse --abbrev-ref HEAD
gh auth status --hostname github.com
./scripts/kyla_sandbox.sh 'python3 -V'
./scripts/kyla_sandbox.sh --script scripts/smoke.sh
```

Manual UI: open https://github.com/M3lcharagu/kyla-quant/actions/workflows/kyla-sandbox.yml, choose `main`, enter the command (and optional script), then run it. For an API dispatch:

```sh
curl --fail-with-body --request POST \
  --url https://api.github.com/repos/M3lcharagu/kyla-quant/dispatches \
  --header "Accept: application/vnd.github+json" \
  --header "Authorization: Bearer ${GITHUB_TOKEN}" \
  --header "X-GitHub-Api-Version: 2022-11-28" \
  --header "Content-Type: application/json" \
  --data '{"event_type":"kyla-sandbox","client_payload":{"command":"python3 -V","script":""}}'
```

Review the workflow result and downloaded `kyla-sandbox-log` artifact. Stop on any failure, stale-data warning, unexpected account, secret exposure, or unapproved live-trading condition. Use GitHub Actions secrets for sensitive values; never place them in command input or logs.
