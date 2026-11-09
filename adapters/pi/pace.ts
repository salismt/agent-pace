// agent-pace for pi (https://pi.dev). Copy to .pi/extensions/pace.ts in your project.
// Runs .agents/scripts/pace.py: guard before each tool call, the promises at session start, the word cap at the end of a run.
// Does nothing in a project without .agents/scripts/pace.py, and fails open if Python is missing.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

function script(cwd: string): string | null {
  for (let d = cwd; ; d = dirname(d)) {
    const p = join(d, ".agents", "scripts", "pace.py");
    if (existsSync(p)) return p;
    if (existsSync(join(d, ".git")) || dirname(d) === d) return null;
  }
}

function pace(sub: string, payload: object, cwd: string) {
  const p = script(cwd);
  if (!p) return null;
  for (const py of ["python3", "python", "py"]) {
    const r = spawnSync(py, [p, sub], { cwd, encoding: "utf8", input: JSON.stringify({ ...payload, cwd }), timeout: 900_000 });
    if (!r.error) return r;
  }
  return null;
}

function json(s: string | undefined): any {
  try { return JSON.parse(s ?? ""); } catch { return {}; }
}

export default function (pi: any) {
  let told = false;    // promises go in once per session
  let resent = false;  // the word cap sends a reply back once only

  pi.on("tool_call", async (event: any, ctx: any) => {
    const r = pace("guard", { tool_name: event.toolName, tool_input: event.input }, ctx.cwd);
    if (r?.status === 2) return { block: true, reason: r.stderr.trim() || "blocked by agent-pace" };
    const note = json(r?.stdout).systemMessage;  // observe mode: show what enforce mode would block
    if (note && ctx.hasUI) ctx.ui.notify(note, "warning");
  });

  pi.on("before_agent_start", async (_event: any, ctx: any) => {
    if (told) return;
    told = true;
    const text = pace("session", {}, ctx.cwd)?.stdout.trim();
    if (text) return { message: { customType: "agent-pace", content: text, display: false } };
  });

  pi.on("agent_end", async (event: any, ctx: any) => {
    if (resent) { resent = false; return; }
    const last = [...(event.messages ?? [])].reverse().find((m: any) => m.role === "assistant");
    const content = last?.content;
    const text = typeof content === "string" ? content
      : (content ?? []).filter((b: any) => b.type === "text").map((b: any) => b.text).join("\n");
    const reason = json(pace("stop", { last_assistant_message: text }, ctx.cwd)?.stdout).reason;
    if (reason) { resent = true; pi.sendUserMessage(reason, { deliverAs: "followUp" }); }
  });
}
