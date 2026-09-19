#!/usr/bin/env bash
set -u

repo=M3lcharagu/kyla-quant
script=
command=
manual_url="https://github.com/${repo}/actions/workflows/kyla-sandbox.yml"

while (($#)); do
  case "$1" in
    --script)
      (($# >= 2)) || { echo "--script requires a path" >&2; exit 2; }
      script=$2; shift 2 ;;
    --repo)
      (($# >= 2)) || { echo "--repo requires owner/repo" >&2; exit 2; }
      repo=$2; manual_url="https://github.com/${repo}/actions/workflows/kyla-sandbox.yml"; shift 2 ;;
    --)
      shift; command="$*"; break ;;
    *)
      if [[ -n "$command" ]]; then command+=" $1"; else command=$1; fi
      shift ;;
  esac
done

if ! command -v gh >/dev/null 2>&1; then
  printf '%s\n%s\n' 'brew install gh' "$manual_url" >&2
  exit 127
fi
if ! gh auth status --hostname github.com >/dev/null 2>&1; then
  printf 'GitHub CLI is not authenticated. Run: gh auth login\n%s\n' "$manual_url" >&2
  exit 1
fi
if [[ -z "$command" && -z "$script" ]]; then
  echo 'Provide a command or --script PATH.' >&2
  exit 2
fi

# command is required by workflow_dispatch; a script-only run uses a no-op command.
dispatch_command=${command:-:}
gh workflow run kyla-sandbox.yml --repo "$repo" --ref main -f "command=$dispatch_command" ${script:+-f "script=$script"}
sleep 2
run_id=$(gh run list --repo "$repo" --workflow kyla-sandbox.yml --event workflow_dispatch --limit 1 --json databaseId --jq '.[0].databaseId')
if [[ -z "$run_id" || "$run_id" == "null" ]]; then
  echo 'Unable to find the dispatched workflow run.' >&2
  exit 1
fi
run_url=$(gh run view "$run_id" --repo "$repo" --json url --jq .url)
printf 'Run: %s\n' "$run_url"
if gh run watch "$run_id" --repo "$repo" --exit-status; then
  echo 'Sandbox succeeded.'
else
  echo 'Sandbox failed; failed-step logs:' >&2
  gh run view "$run_id" --repo "$repo" --log-failed >&2 || true
  printf 'Run: %s\n' "$run_url" >&2
  exit 1
fi
