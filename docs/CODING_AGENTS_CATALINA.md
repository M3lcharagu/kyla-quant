# Coding agents on macOS Catalina research note

## Evidence posture

This note records the supplied research and labels uncertain or unverified points explicitly. It does not claim that compatibility was tested on Catalina.

## Best first choice: aider

**aider — best first choice.** The supplied research identifies aider as Python-based, multi-provider, and licensed under Apache-2.0. There is no official Catalina guarantee, so Catalina operation remains a practical candidate rather than a confirmed compatibility result.

## Candidates requiring verification

- **Cursor CLI — candidate.** A Catalina / macOS 10.15 compatibility claim was encountered, but it is unconfirmed here. Treat the claim as **unverified** until checked against the exact current CLI build and its runtime requirements.
- **OpenCode — possible candidate.** The supplied research identifies it as MIT-licensed, but its minimum macOS version is unverified. Do not infer Catalina support from the license or project name.

## Explicit skips

The following are skipped for a Catalina-first setup based on the supplied research:

- **Codex CLI.** Skip.
- **Qwen Code.** Skip.
- **Gemini CLI.** Skip; the supplied research notes Node 20+ / macOS 15 requirements.
- **Goose.** Skip; the supplied research notes macOS 12+.
- **Continue.dev.** Skip; the supplied research describes it as unmaintained.
- **Cody.** Skip; its minimum version is undocumented in the supplied research.

These are research triage decisions, not claims that every release or installation path has been tested.

## Claude-related notes

- The official **Claude Code CLI** requires macOS 13+ according to the supplied research, so it is not a Catalina-compatible first choice.
- **tct68/claudex** is an MIT-licensed workspace manager, but it also requires the Claude Code CLI. It therefore does not remove the underlying macOS requirement.
- The supplied research states that the **`ANTHROPIC_API_KEY` path works on Catalina regardless**. This is recorded as a supplied research fact, not as a claim that a complete Catalina installation or every client using that path was tested.

## Practical conclusion

Start with aider, while verifying Python, provider, and dependency requirements on the actual Catalina machine. Keep Cursor CLI and OpenCode as unconfirmed candidates. Keep the explicit skips above out of the Catalina plan unless their requirements change and are rechecked. No compatibility testing is claimed by this document.
