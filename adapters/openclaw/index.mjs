// agent-pace for OpenClaw. Install once: openclaw plugins install -l <project>/.agents/adapters/openclaw
// Runs <project>/.agents/scripts/pace.py: guard before exec/edit/write/apply_patch, the word cap before the reply is final.
// Inert in projects without pace.py; fails open without Python. OpenClaw blocks a hook that runs past 15 s: keep checks fast.
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

const GUARDED = new Set(["exec", "edit", "write", "apply_patch"]);
const workspace = new Map(); // sessionKey -> workspaceDir

function script(cwd) {
  for (let d = cwd; ; d = dirname(d)) {
    const p = join(d, ".agents", "scripts", "pace.py");
    if (existsSync(p)) return p;
    if (existsSync(join(d, ".git")) || dirname(d) === d) return null;
  }
}

function run(py, p, sub, payload, cwd) {
  return new Promise((resolve) => {
    const c = spawn(py, [p, sub], { cwd, timeout: 12_000 });
    let out = "", err = "";
    c.stdout.on("data", (d) => (out += d));
    c.stderr.on("data", (d) => (err += d));
    c.on("error", () => resolve(null));
    c.on("close", (code) => resolve({ code, out, err: err.trim() }));
    c.stdin.end(JSON.stringify({ ...payload, cwd }));
  });
}

async function pace(sub, payload, cwd) {
  const p = script(cwd);
  if (!p) return null;
  for (const py of ["python3", "python", "py"]) {
    const r = await run(py, p, sub, payload, cwd);
    if (r) return r;
  }
  return null;
}

export default {
  id: "agent-pace",
  name: "agent-pace",
  description: "Replays the claims ledger (pace.toml) before commits and protects owner-only files.",
  register(api) {
    api.on("model_call_started", (_e, ctx) => {
      if (ctx.sessionKey && ctx.workspaceDir) workspace.set(ctx.sessionKey, ctx.workspaceDir);
    });
    api.on("before_tool_call", async (event, ctx) => {
      if (!GUARDED.has(event.toolName)) return;
      const cwd = event.params?.workdir ?? workspace.get(ctx.sessionKey) ?? process.cwd();
      const r = await pace("guard", { tool_name: event.toolName, tool_input: event.params }, cwd);
      if (r?.code === 2) return { block: true, blockReason: r.err || "blocked by agent-pace" };
    });
    // Needs hooks.allowConversationAccess: true on this plugin's config entry.
    api.on("before_agent_finalize", async (event, ctx) => {
      if (event.stopHookActive) return; // send back once only
      const cwd = event.cwd ?? ctx.workspaceDir ?? process.cwd();
      const r = await pace("stop", { last_assistant_message: event.lastAssistantMessage }, cwd);
      let reason;
      try { reason = JSON.parse(r?.out || "{}").reason; } catch {}
      if (reason) return { action: "revise", reason, retry: { instruction: reason } };
    });
  },
};
