# Hermes Agent

Status: **tested live** (Hermes Agent v0.22.5, November 2026) with `hermes hooks test` against a real project: commit on a break blocked, `pace.toml` edits blocked through `write_file`, `patch` and `execute_code`, a plain command allowed, a long reply sent back once, and the promises added on the first turn. Not yet run in a full model session.

Hermes runs Claude-style shell hooks, but only from your user config (`~/.hermes/config.yaml`, one per profile). There is no project-level hook file. The hooks below find the git root of Hermes's working directory and do nothing in a repo without `.agents/scripts/pace.py`, so they are safe to add once for every project.

1. Do the [common setup](README.md#common-setup-every-agent-except-claude-code), and copy the adapters too: `cp -R /tmp/agent-pace/adapters .agents/`.
2. Merge [`adapters/hermes/config.yaml`](../../adapters/hermes/config.yaml) into the `hooks:` section of `~/.hermes/config.yaml`.
3. Approve the hooks once: start `hermes chat` and accept the prompt. Gateway and unattended runs never prompt; they need `--accept-hooks`, `HERMES_ACCEPT_HOOKS=1` or `hooks_auto_accept: true`.
4. Let Hermes load the skills from `.agents/skills`: `hermes skills trust` in the project.
5. Check it without a model: `hermes hooks doctor`.

## How it maps

| pace needs | Hermes gives |
|---|---|
| Shell command | `pre_tool_call`, `tool_name: "terminal"`, `tool_input.command` |
| Python code | `execute_code`, `tool_input.code` (guarded too, since it can write files) |
| Edited file path | `write_file` / `patch`, `tool_input.path`; V4A patches carry the paths inside `tool_input.patch` |
| Reply text | `pre_verify`, `extra.final_response`; sent back once (`extra.attempt`) |
| Session start | `pre_llm_call` returns `{"context": ...}` on the first turn |
| Block | exit code 2, reason from stderr |

## Limits

- `pre_verify` runs only on turns that changed a file through `write_file` or `patch`. Chat-only replies are not capped.
- Hermes gives a `pre_tool_call` hook about 30 s before it blocks the tool anyway. A commit replays every claim check, so keep checks fast.
- Approval is tied to the exact hook command, not to `pace.py`'s contents. Review changes to `.agents/scripts/` in git as you would any code.
