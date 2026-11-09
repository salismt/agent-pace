# DeepSeek Harness (dsh)

Status: **partly tested** (`@deepseek-ai/dsh` 0.1.0-rc.6, November 2026). The plugin loads in a real `dsh --profile headless` boot, and its guard was run with dsh's own tool payloads (`bash`, `write`, `edit`, `str_replace_editor`): breaks and writes to owner-only files blocked, reads allowed. Not yet run in a session with a model.

dsh has no shell hooks. It loads plugins per profile, so agent-pace ships one: [`adapters/dsh/pace.mjs`](../../adapters/dsh/pace.mjs). It registers a tool guard that walks up from the session's working directory to `.agents/scripts/pace.py`, so it is inert in projects without agent-pace.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code). dsh reads skills from `.agents/skills` and rules from `AGENTS.md`.
2. Install the plugin into each profile you use (`tui`, `headless`, `web`, …). Plugin names resolve against the profile folder, so the file has to live there:

```bash
P=${DSH_HOME:-$HOME/.dsh}/profiles/tui
mkdir -p "$P" && cp /tmp/agent-pace/adapters/dsh/pace.mjs "$P/agent-pace.mjs"
```

3. Add it to that profile's `cordis.patch.yml` (replace an empty `[]`):

```yaml
- insert:
    - id: agent-pace
      name: ./agent-pace.mjs
```

4. Check that it composes: `dsh --profile tui --dump-config | grep agent-pace`.
5. Add the `AGENTS.md` lines from [other-agents.md](other-agents.md#rules-file-agents-without-skills), because dsh has no session hook pace uses.

## How it maps

| pace needs | dsh gives |
|---|---|
| Shell command | `ctx.tools.guard`, `exec.name: "bash"`, `exec.arguments.command` |
| Edited file path | `write` / `edit`, `arguments.file_path`; `str_replace_editor`, `arguments.path` |
| Reply text | Not available to a guard, so the word cap doesn't run |
| Block | the guard returns the reason string; later plugins can't undo it |
