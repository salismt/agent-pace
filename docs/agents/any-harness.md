# Add agent-pace to any harness

agent-pace doesn't depend on one agent. All the logic is in one Python script, `pace.py`, and every harness talks to it the same way: send JSON on stdin, read the exit code. A new harness needs only a thin adapter that translates its hook or plugin event into that call. The existing adapters are 30 to 60 lines each.

## Pick the deepest level your harness allows

| Level | What the harness needs | What you get | Examples |
|---|---|---|---|
| 1. Git hook | It commits with `git` | Ledger replayed on every commit | Any agent: [other-agents.md](other-agents.md) |
| 2. Rules file | It reads `AGENTS.md` or skills | The agent runs `pace.py check` itself and knows the rules | Every harness here reads `AGENTS.md` or `.agents/skills` |
| 3. Shell hook | It runs a command before each tool call | Blocks commits on a break, protects `pace.toml`, blocks `--no-verify` | Claude Code, Codex, Gemini, Cursor, Copilot, Devin, Hermes |
| 4. Plugin | It loads a JS/TS/Python module with a pre-tool event | Same as level 3, through a wrapper | Pi, OpenClaw, DeepSeek Harness |

Use level 1 everywhere: it is the floor that still works when an agent has no hooks. Add level 3 or 4 when the harness allows it. Add the end-of-turn word cap and the session-start hook if the harness has those events.

## The contract

Run `python3 <project>/.agents/scripts/pace.py <command>` with one JSON object on stdin. Find the project by walking up from the agent's working directory to the folder that holds `.agents/scripts/pace.py`. If there is none, do nothing: that keeps the adapter inert in other projects.

### `guard`: before each tool call

Input. Send the harness's own tool name and arguments; you don't need to rename anything:

```json
{"tool_name": "<the harness's tool name>", "tool_input": {"command": "git commit -m x"}, "cwd": "/path/to/project"}
```

`pace.py` reads these, in this order:

| What | Fields it accepts |
|---|---|
| Tool name | `tool_name`, `toolName`, `tool` |
| Arguments | `tool_input`, `toolArgs`, `args`, `arguments`, `input`, `params`, or the top level of the event. A JSON string is decoded |
| Shell command | `command`, `cmd`, `code` (a string, or an argv list) |
| File path | `file_path`, `filePath`, `notebook_path`, `path`, `file`, `filename`, `target_file`, `paths` |
| Patch text | `patch`, `input`, `command` holding `*** Begin Patch` (the Codex/V4A format) |
| Project | `cwd`, `workspace_roots`, or env `CLAUDE_PROJECT_DIR`, `GEMINI_PROJECT_DIR`, `DEVIN_PROJECT_DIR` |

A call is treated as a shell command when the tool name is a known shell tool or contains `bash`, `shell`, `exec`, `terminal`, `command` or `run_`, or when it has a command and no file path. Otherwise it is a file edit. So a call shaped like `str_replace_editor {command: "create", path: ...}` counts as an edit.

Output:

| Exit | Meaning | What the adapter does |
|---|---|---|
| `2` | Block. The reason is on stderr | Deny the tool call and show the reason to the model |
| `0` | Allow | Let it run. In observe mode stdout may hold `{"systemMessage": "..."}` with what enforce mode would have blocked; show it if the harness can |

Keep the call synchronous, or wait for it. A commit replays every claim check (up to 120 s each), so give the hook a long timeout. If the harness blocks a hook that times out (OpenClaw 15 s, Hermes 30 s), keep your checks fast.

### `stop`: at the end of a reply (optional)

Input: `{"last_assistant_message": "<final reply text>", "stop_hook_active": false}`. Set `stop_hook_active` (or skip the call) when this reply is already the rewrite, so a reply is sent back once at most.

Output: nothing when the reply is within `word_cap`. Otherwise stdout holds `{"decision": "block", "reason": "..."}`; send `reason` back to the model as a new user message or a revise instruction. Exit is always `0`.

### `session`: when a session starts (optional)

Input: `{}`. Output: plain text listing the promises in `pace.toml` and the last break. Add it to the model's context once per session. If the harness has no session event, the `AGENTS.md` lines in [other-agents.md](other-agents.md#rules-file-agents-without-skills) do the same job.

### Rules every adapter keeps

- **Fail open.** If Python is missing, the script is missing, or the call errors, allow the tool call. `pace.py` itself fails open on its own errors. A broken guard must never stop work.
- **Try `python3`, then `python`, then `py`.** Windows often has only `py`.
- **Check the script exists before calling it.** `python3 missing.py` also exits `2`, which would block every tool call.

## Adapter template (Node, no dependencies)

```js
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

function script(cwd) {                       // nearest .agents/scripts/pace.py, stopping at the git root
  for (let d = cwd; ; d = dirname(d)) {
    const p = join(d, ".agents", "scripts", "pace.py");
    if (existsSync(p)) return p;
    if (existsSync(join(d, ".git")) || dirname(d) === d) return null;
  }
}

export function paceGuard(toolName, args, cwd) {   // -> reason string to block, or undefined to allow
  const p = script(cwd);
  if (!p) return undefined;
  for (const py of ["python3", "python", "py"]) {
    const r = spawnSync(py, [p, "guard"], { cwd, encoding: "utf8", timeout: 900_000,
      input: JSON.stringify({ tool_name: toolName, tool_input: args, cwd }) });
    if (!r.error) return r.status === 2 ? r.stderr.trim() || "blocked by agent-pace" : undefined;
  }
  return undefined;
}
```

Then call `paceGuard` from the harness's pre-tool event and translate the result into its block shape. The working adapters in [`adapters/`](../../adapters) show three variations: Pi returns `{block, reason}`, OpenClaw returns `{block, blockReason}`, and DeepSeek Harness returns the reason string.

## Test a new adapter

1. Make a scratch git repo with the [common setup](README.md#common-setup-every-agent-except-claude-code), `mode = "enforce"`, `word_cap = 20`, and one claim whose check fails.
2. Check each case: `git commit` is blocked with the claim in the reason; writing `pace.toml` is blocked; a plain `ls` is allowed; a 40-word reply is sent back once; the session context lists the claim.
3. If the harness has a scripted or fake model, run it end to end. Pi's built-in `faux` provider did this for the Pi adapter. Otherwise, call the adapter's handler directly with the payload shapes from the harness source, as for OpenClaw.
4. Add the payload shapes to `tests/test_pace.py`, write `docs/agents/<harness>.md`, add a row to the [support table](README.md), and open a pull request.
