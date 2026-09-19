# KYLA Quant — Catalina launch-night checklist

Use a fresh Terminal window. Complete this checklist in order. Keep credentials
out of shell history and logs, use demo/paper settings only, and stop before
any live activity unless a human has explicitly approved it.

## 1. Confirm the Mac and the launch conditions

- [ ] **Confirm the operating system.** Check **macOS 10.15 Catalina** in
  **Apple menu → About This Mac**.  
  **Verify:** Catalina is confirmed; if the Mac is another version, pause and
  adapt the commands before continuing.

- [ ] **Confirm free disk space.** In Terminal, run `df -h .` and leave enough
  space for the checkout, Python packages, logs, and any selected installers.
  **Verify:** the filesystem containing the checkout is not nearly full.

- [ ] **Confirm RAM and close heavy applications.** Open **Activity Monitor →
  Memory**, close unnecessary workloads, and note that memory pressure is
  green.  
  **Verify:** memory pressure is acceptable before running the sandbox.

- [ ] **Connect power and check battery.** Plug in the Mac and confirm the
  battery is charging (or has enough charge to finish the smoke test).  
  **Verify:** the Mac will not sleep or run out of power during the first
  cloud test.

- [ ] **Confirm internet access.** Open a normal web page and confirm the
  connection can reach GitHub.  
  **Verify:** GitHub loads without a captive-portal or DNS error.

## 2. Prepare the Catalina development environment

- [ ] **Install Apple Command Line Tools if needed.** Run
  `xcode-select --install` and use Apple's installer; do not assume the full
  Xcode application is necessary for this checklist.  
  **Verify:** `xcode-select -p` prints an installed developer-tools path.

- [ ] **Understand the Homebrew limitation.** Homebrew's official supported
  use no longer covers Catalina, and the official current installer may not
  work on Catalina. Do not make Homebrew a prerequisite for tonight.  
  **Verify:** continue with the official package alternatives below if `brew`
  is absent or unavailable.

- [ ] **Install Python 3.10, if it is not already available.** Use the
  official **python.org Downloads** page and its macOS **3.10 installer
  package (.pkg)** only. Do not use a random mirror or an unverified package.
  **Verify:** `python3 --version` reports Python 3.10.x (or document the
  already-installed compatible Python before proceeding).

- [ ] **Install Node.js LTS, if the project work tonight needs it.** Use the
  official **nodejs.org Downloads** page and its macOS **LTS installer
  package (.pkg)** only. Node is optional for the dependency-free boot check.
  **Verify:** `node --version` reports the installed LTS version, or record
  that Node is intentionally absent for this cloud-only smoke test.

- [ ] **Install VS Code, if an editor is wanted.** Use the official **Visual
  Studio Code macOS download** and the supplied macOS **zip** only.  
  **Verify:** VS Code opens; do not add editor extensions as a prerequisite
  for the first sandbox test.

- [ ] **Do not install local Docker for launch night.** Local Docker is
  explicitly deferred; the first smoke test runs in GitHub Actions instead.
  **Verify:** no local Docker daemon is required to complete this checklist.

## 3. Get the repository and run the local boot check

- [ ] **Clone the repository and enter the requested branch.** Run:
  `git clone https://github.com/M3lcharagu/kyla-quant.git && cd kyla-quant && git
  switch main`  
  **Verify:** `git branch --show-current` prints `main` and the checkout is
  the `M3lcharagu/kyla-quant` repository.

- [ ] **Make the two launch helpers executable.** Run
  `chmod +x scripts/kyla_boot.py scripts/kyla_sandbox.sh`.  
  **Verify:** `ls -l scripts/kyla_boot.py scripts/kyla_sandbox.sh` shows the
  executable bit; the Python script still requires only the standard library.

- [ ] **Run the dependency-free boot check from the repository root.** Run
  `python3 scripts/kyla_boot.py`. It prints a styled KYLA banner, CPU, RAM,
  disk, `python3`/Node/git versions, repository status, and the current date
  and time labeled EAT. Missing optional Node or git must be a warning, not a
  failed process.  
  **Verify:** the command exits with status 0 and the expected diagnostic
  sections are visible.

- [ ] **Review the local state before the cloud test.** Run `git status
  --short` and confirm there are no unreviewed local changes or credential
  files.  
  **Verify:** only changes you intentionally made are present.

## 4. Authenticate and run the first GitHub cloud sandbox test

- [ ] **Check GitHub CLI authentication if `gh` is installed.** Run
  `gh auth status --hostname github.com`; if it is not authenticated, run
  `gh auth login --hostname github.com` and complete the interactive login.
  **Verify:** `gh auth status --hostname github.com` reports an authenticated
  GitHub account with access to `M3lcharagu/kyla-quant`. If `gh` is unavailable,
  use the manual Actions page in the next step instead.

- [ ] **Run the existing sandbox helper for the first cloud test.** From the
  repository root, run `./scripts/kyla_sandbox.sh 'python3 -V'`. This invokes
  `.github/workflows/kyla-sandbox.yml` through `workflow_dispatch` and uses the
  existing `scripts/kyla_sandbox.sh` interface.  
  **Verify:** the helper prints a GitHub Actions run URL and the run reaches a
  completed, successful state.

- [ ] **Use the preserved manual Actions fallback when needed.** Open
  https://github.com/M3lcharagu/kyla-quant/actions/workflows/kyla-sandbox.yml,
  choose **Run workflow**, enter `python3 -V` in the required command field,
  and start it.  
  **Verify:** inspect the run log and download the `kyla-sandbox-log` artifact;
  stop on a failed step, stale-data warning, unexpected account, secret
  exposure, or any unapproved live-trading condition.

- [ ] **Keep all sandbox activity non-live.** Use read-only or demo/paper
  commands only; never put tokens in command input, logs, or committed files.
  **Verify:** the workflow command and its logs contain no secrets and no live
  trading action.

## 5. Explicitly defer non-essential launch work

- [ ] **Defer the animated 3D UI.** Record it as a follow-up rather than
  starting it during launch night.  
  **Verify:** the first acceptance target remains the cloud sandbox result.

- [ ] **Defer the voice wake word.** Do not configure microphones, wake-word
  services, or background listeners tonight.  
  **Verify:** no voice process is running and the scope remains the verified
  sandbox smoke test.

- [ ] **Defer local Docker and any container launch.** Keep the GitHub-hosted
  sandbox as the only launch-night execution environment.  
  **Verify:** no local Docker setup is required or treated as a blocker.

## 6. Stop and record the result

- [ ] **Record the first successful run URL, timestamp, branch, command, and
  artifact result.** Keep the record free of credentials.  
  **Verify:** another person can identify exactly which GitHub Actions run was
  checked without receiving a token.

- [ ] **Stop after a clean sandbox result.** Do not expand scope into live
  trading or the deferred UI/voice/container work without a new review.  
  **Verify:** the launch-night acceptance state is documented as
  **cloud sandbox passed; local Docker, animated 3D UI, and voice wake word
  deferred**.

## Tonight's copy-paste Terminal sequence

Run these in order from a fresh Terminal. The `gh` line performs a status check
and opens login only when needed; if GitHub CLI is not installed, use the manual
Actions fallback above.

```sh
git clone https://github.com/M3lcharagu/kyla-quant.git
cd kyla-quant
git switch main
chmod +x scripts/kyla_boot.py scripts/kyla_sandbox.sh
python3 scripts/kyla_boot.py
gh auth status --hostname github.com || gh auth login --hostname github.com
./scripts/kyla_sandbox.sh 'python3 -V'
```
