# OpenCode, Amp, Cline, and any agent that uses git

These agents extend through JavaScript plugins (OpenCode, Amp) or file hooks that abort the whole run (Cline), not through the shell hooks `pace.py` speaks. For them, pace enforces the ledger where every agent ends up anyway: `git commit`. To go further, a JavaScript plugin can call `pace.py` before each tool call: see [any-harness.md](any-harness.md) for the contract and a template.

What you get: the ledger is replayed on every commit, plus the skills. What you don't get: owner-only protection for `pace.toml` and the word cap.

## Git pre-commit (any agent)

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code). For Cline, copy into `.cline/` instead of `.agents/` (Cline reads skills from `.cline/skills`), and use that path below.
2. Install the hook. On a PC, run this once per clone. On a cloud server, put it in the environment's setup script (see [cloud.md](cloud.md)):

```bash
python3 .agents/scripts/pace.py install-git-hook
```

It adds one block to `.git/hooks/pre-commit` (or your `core.hooksPath`), keeps any hook that's already there, and does nothing if it's already installed. Using the [pre-commit](https://pre-commit.com) framework instead:

```yaml
- repo: local
  hooks:
    - id: agent-pace
      name: agent-pace claims ledger
      entry: python3 .agents/scripts/pace.py pre-commit
      language: system
      pass_filenames: false
      always_run: true
```

In observe mode the hook prints the break and lets the commit through. In enforce mode it blocks the commit.

## Limits

- `git commit --no-verify` skips git hooks. The shell-hook integrations (Claude Code, Codex, Gemini, Cursor, Copilot, Devin) block `--no-verify`; the git hook alone can't.
- Without a pre-edit hook, nothing stops an agent from editing `pace.toml`. Review its git history, or protect it with CODEOWNERS on your git host.

## Rules file (agents without skills)

If your agent reads `AGENTS.md` but not skills, add:

```markdown
## Claims ledger (agent-pace)
- `pace.toml` and existing files in `claims/checks/` are owner-only. Never edit them.
- When you start or resume work, run `python3 .agents/scripts/pace.py check` before the first change, and read the promises in `pace.toml`.
- Before committing, run `python3 .agents/scripts/pace.py check`. On a `BREAK`, don't commit and don't change the check: tell the user in one line which change broke which claim, then stop.
```
