# Local PC and cloud servers

agent-pace runs wherever the agent runs: your laptop, a remote dev box, a CI runner, or a vendor's cloud sandbox (Claude Code on the web, Codex cloud, Copilot coding agent, Cursor cloud agents, Devin). For the same protection in all of them, follow three rules.

## Three rules that make it portable

1. **Commit the files; don't rely on per-machine installs.** Cloud sandboxes start from a fresh clone of your repo. They don't see your `~/.claude`, `~/.codex` or `~/.cursor`, and Claude Code on the web doesn't install plugins. So commit:
   - `pace.toml` and `claims/checks/`
   - `.agents/` (from the [common setup](README.md#common-setup-every-agent-except-claude-code))
   - your agent's hook file: `.claude/settings.json`, `.codex/hooks.json`, `.github/hooks/agent-pace.json`, `.cursor/hooks.json`, `.gemini/settings.json` or `.pi/extensions/pace.ts`
2. **Install the git hook in the environment's setup script.** Git hooks live in `.git/hooks`, which is never committed, so every fresh clone starts without one. Add this line to the setup script:
   ```bash
   python3 .agents/scripts/pace.py install-git-hook
   ```
   It is idempotent and keeps any pre-commit hook that's already there. This is your safety net for agents with no hooks (Codex cloud) and for commits made outside the agent.
3. **Read observe-mode results in the transcript.** A cloud container is thrown away after the session, and `.pace/log.jsonl` with it. In observe mode, pace therefore also prints each would-be block to the session transcript ("pace (observe mode, not blocking): …"). Enforce-mode blocks always appear in the transcript.

pace needs Python 3.8 or newer and makes no network calls, so a sandbox with internet off is fine. Hook commands try `python3`, then `python`, then `py`.

## Per product

| Where it runs | What runs there | Setup script | Notes |
|---|---|---|---|
| **Your PC** (macOS, Linux) | Everything | Not needed | Claude Code can use the plugin; other agents use `.agents/` |
| **Your PC** (Windows) | Everything | Not needed | Claude Code runs hook commands in Git Bash, so install Git for Windows. `python3` is usually missing there; the hooks fall back to `python`, then `py`. Without Git Bash, hooks run in PowerShell, fail, and pace stays off (it fails open) |
| **Claude Code on the web** | `.claude/settings.json` hooks (single-repo sessions) | Environment setup script at claude.ai/code | Plugins are **not** installed in cloud sessions: commit `.agents/` and the `.claude/settings.json` block from [cursor.md](cursor.md) |
| **Claude Code GitHub Actions** | Project `.claude/settings.json` hooks | Workflow steps | On PR events the action restores `.claude/` from the base branch, so hooks must be merged first |
| **Codex cloud** | No repo hooks (not supported in cloud tasks) | Setup script in environment settings | Use `install-git-hook` in the setup script, plus the `AGENTS.md` lines in [other-agents.md](other-agents.md#rules-file-agents-without-skills) |
| **GitHub Copilot coding agent** | `.github/hooks/*.json` on the default branch | `.github/workflows/copilot-setup-steps.yml` | Use the block in [copilot-cli.md](copilot-cli.md#copilot-coding-agent-cloud) |
| **Cursor cloud agents** | `.cursor/hooks.json` (not `~/.cursor`) | `install` in `.cursor/environment.json` | Use the block in [cursor.md](cursor.md#cursor-cloud-agents). Session-start hooks don't run there |
| **Gemini CLI in GitHub Actions** | Project `.gemini/settings.json` hooks | Workflow steps | Don't use the action's `settings` input; it overwrites `.gemini/settings.json` and drops the hooks |
| **Devin cloud sessions** | Hooks through Devin plugins | `initialize` in `.devin/blueprint.yaml` | Use `install-git-hook` in `initialize`. Whether plain repo hook files run in cloud sessions isn't documented |
| **Self-hosted on a server** (Hermes or OpenClaw gateway, Pi, DeepSeek Harness) | Same as on your PC | Your server's provisioning | Hermes, OpenClaw and dsh read hooks or plugins from the user's home folder, not the repo: add their setup from [hermes.md](hermes.md), [openclaw.md](openclaw.md) or [deepseek-harness.md](deepseek-harness.md) to the image. Unattended Hermes needs `HERMES_ACCEPT_HOOKS=1`; unattended Pi needs `--approve` |

Sources: each vendor's docs, November 2026. Live-tested so far: Claude Code and Codex CLI on a local PC, and the git hook plus the hook payloads in clean Linux containers on Python 3.8 and 3.12. The vendor cloud products themselves have not been tested yet.

## Setup script examples

```bash
# Claude Code on the web, Codex cloud, Devin initialize: one line
python3 .agents/scripts/pace.py install-git-hook
```

```yaml
# .github/workflows/copilot-setup-steps.yml
jobs:
  copilot-setup-steps:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: python3 .agents/scripts/pace.py install-git-hook
```

`.cursor/environment.json`:

```json
{ "install": "python3 .agents/scripts/pace.py install-git-hook" }
```

## Optional: a server-side check

Every layer above runs where the agent runs. If an agent can still push without hooks, add one job to your CI so the pull request shows the ledger result:

```yaml
- run: python3 .agents/scripts/pace.py check
```
