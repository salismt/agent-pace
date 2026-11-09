// agent-pace for DeepSeek Harness (dsh). Copy to $DSH_HOME/profiles/<profile>/agent-pace.mjs and add to that
// profile's cordis.patch.yml:   - insert: [{ id: agent-pace, name: ./agent-pace.mjs }]
// Runs <project>/.agents/scripts/pace.py guard before every tool call. Inert in projects without it; fails open without Python.
import { spawnSync } from "node:child_process";
import { existsSync } from "node:fs";
import { dirname, join } from "node:path";

function script(cwd) {
  for (let d = cwd; ; d = dirname(d)) {
    const p = join(d, ".agents", "scripts", "pace.py");
    if (existsSync(p)) return p;
    if (existsSync(join(d, ".git")) || dirname(d) === d) return null;
  }
}

export function guard(exec) {
  const cwd = exec.agent?.session?.header?.cwd ?? process.cwd();
  const p = script(cwd);
  if (!p) return undefined;
  for (const py of ["python3", "python", "py"]) {
    const r = spawnSync(py, [p, "guard"], { cwd, encoding: "utf8", timeout: 900_000,
      input: JSON.stringify({ tool_name: exec.name, tool_input: exec.arguments, cwd }) });
    if (!r.error) return r.status === 2 ? r.stderr.trim() || "blocked by agent-pace" : undefined;
  }
  return undefined;
}

export const name = "agent-pace";
export const inject = ["tools"];
export function apply(ctx) {
  ctx.tools.guard(guard);
}
