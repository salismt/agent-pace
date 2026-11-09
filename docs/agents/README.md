# agent-pace with your agent

agent-pace is one Python script (`pace.py`) plus three skills. Claude Code installs it as a plugin. Every other agent uses the same files copied into the project, and a hook config in that agent's own format.

| Agent | Guide | Ledger on commit | Owner-only files (edits) | Owner-only files (shell) | Word cap | Skills | Status |
|---|---|---|---|---|---|---|---|
| Claude Code | [claude-code.md](claude-code.md) | yes | yes | yes | yes | yes | tested live |
| OpenAI Codex CLI | [codex.md](codex.md) | yes | yes | yes | yes | yes | tested live |
| Gemini CLI | [gemini-cli.md](gemini-cli.md) | yes | yes | yes | yes | yes | from docs |
| Cursor | [cursor.md](cursor.md) | yes | likely | yes | no | yes | from docs |
| GitHub Copilot CLI | [copilot-cli.md](copilot-cli.md) | yes | likely | yes | no | yes | from docs |
| Devin (formerly Windsurf) | [devin.md](devin.md) | yes | likely | yes | no | yes | from docs |
| OpenCode, Amp, Cline | [other-agents.md](other-agents.md) | yes (git hook) | no | no | no | yes | from docs |
| Anything that uses git | [other-agents.md](other-agents.md) | yes (git hook) | no | no | no | via AGENTS.md | unit-tested |

- **tested live:** run in a real session of that agent; see the main README for the output.
- **from docs:** built from the vendor's hook reference (November 2026) and covered by unit tests with that payload shape, but not yet run in that agent. Reports welcome.
- **likely:** the vendor's docs don't name the file-path field for edits. pace looks for `file_path`, `filePath` and `path`.
- **Word cap "no":** that agent's stop hook doesn't hand over the reply text, or its transcript format isn't one pace reads. The cap never blocks there, so it can't cause false stops.

## Common setup (every agent except Claude Code)

From your project root:

```bash
git clone --depth 1 https://github.com/salismt/agent-pace /tmp/agent-pace
mkdir -p .agents && cp -R /tmp/agent-pace/plugin/{skills,scripts,templates} .agents/
cp .agents/templates/pace.toml pace.toml
```

This gives you:

```
pace.toml                    your promises (owner-only)
.agents/skills/              claims, comprehension-gate, pace (read by Codex, Cursor, Gemini, Copilot, Devin, OpenCode, Amp)
.agents/scripts/pace.py      the hooks and commands
.agents/templates/pace.toml  the starting ledger
```

Then add the hook config from your agent's guide. Commit `.agents/` and `pace.toml` so everyone on the repo gets the same checks.

Needs Python 3.8+. Running on a cloud server (Claude Code on the web, Codex cloud, Copilot coding agent, Cursor cloud agents, Devin)? Read [cloud.md](cloud.md) first. pace starts in observe mode: it logs what it would block to `.pace/log.jsonl` and blocks nothing until you set `mode = "enforce"`.
