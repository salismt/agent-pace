"""Self-check for scripts/pace.py. Run: python3 tests/test_pace.py"""
import json, os, subprocess, sys, tempfile
from pathlib import Path

PACE = Path(__file__).resolve().parent.parent / "plugin" / "scripts" / "pace.py"


def run(root, args, ev=None, project_env=True):
    env = {"PATH": os.environ["PATH"], "HOME": os.environ["HOME"]}
    if project_env:
        env["CLAUDE_PROJECT_DIR"] = str(root)
    p = subprocess.run([sys.executable, str(PACE), *args], input=json.dumps(ev) if ev is not None else None,
                       capture_output=True, text=True, env=env, cwd=root)
    return p.returncode, p.stdout, p.stderr


def project(mode):
    r = Path(tempfile.mkdtemp())
    (r / "claims" / "checks").mkdir(parents=True)
    (r / "claims" / "checks" / "C1.sh").write_text("exit 0\n")
    (r / "claims" / "checks" / "C2.sh").write_text("echo 'funds row with custodian=us'; exit 1\n")
    (r / "pace.toml").write_text(f'[pace]\nmode = "{mode}"\nword_cap = 20\n'
                                 '[[claim]]\nid = "C1"\nsaid = "ok"\n'
                                 '[[claim]]\nid = "C2"\nsaid = "We never hold customer funds."\nto = "regulator"\n'
                                 '[[claim]]\nid = "C3"\nsaid = "uncompiled one"\n')
    return r


def log(r):
    f = r / ".pace" / "log.jsonl"
    return [json.loads(l) for l in open(f)] if f.exists() else []


def edit(path, tool="Write"):
    return {"tool_name": tool, "tool_input": {"file_path": str(path)}}


def bash(cmd):
    return {"tool_name": "Bash", "tool_input": {"command": cmd}}


r = project("enforce")
# ledger and existing checks are founder-owned; new checks are allowed
assert run(r, ["guard"], edit(r / "pace.toml"))[0] == 2
assert run(r, ["guard"], edit("pace.toml", "Edit"))[0] == 2  # relative path
assert run(r, ["guard"], edit(r / "claims/checks/C2.sh", "Edit"))[0] == 2
assert run(r, ["guard"], edit(r / "claims/checks/C9.sh"))[0] == 0
assert run(r, ["guard"], edit(r / "src/app.py"))[0] == 0
# bash writes to protected paths are blocked, reads are not
for c in ["sed -i '' s/a/b/ pace.toml", "echo x > pace.toml", "rm claims/checks/C2.sh", "git checkout -- pace.toml"]:
    assert run(r, ["guard"], bash(c))[0] == 2, c
for c in ["cat pace.toml", "grep said pace.toml 2>/dev/null", "ls claims/checks", "sed -n 1,5p pace.toml"]:
    assert run(r, ["guard"], bash(c))[0] == 0, c
# commit replays the ledger: C2 breaks -> blocked in enforce, with the claim text
code, _, err = run(r, ["guard"], bash("git commit -m x"))
assert code == 2 and "C2" in err and "never hold customer funds" in err and "C1" not in err, err
assert run(r, ["guard"], bash("git status"))[0] == 0
assert log(r)[-1]["event"] == "continuity_break" and log(r)[-1]["claims"] == ["C2"]
# check CLI
code, out, _ = run(r, ["check"])
assert code == 1 and "BREAK" in out and "uncompiled" in out and "holds" in out, out

# git pre-commit mode (any agent tool): enforce blocks with the claim text
code, _, err = run(r, ["pre-commit"])
assert code == 1 and "never hold customer funds" in err, err

# observe: same break is logged, not blocked
o = project("observe")
assert run(o, ["guard"], bash("rtk git push origin main"))[0] == 0
assert log(o)[-1]["mode"] == "observe"
code, _, err = run(o, ["pre-commit"])
assert code == 0 and "observe mode: commit allowed" in err, err
assert run(o, ["guard"], edit(o / "pace.toml"))[0] == 2  # protection holds in observe too

# inert without pace.toml, even for a file named pace.toml
bare = Path(tempfile.mkdtemp())
assert run(bare, ["guard"], edit(bare / "pace.toml")) == (0, "", "")
assert run(bare, ["guard"], bash("git commit -m x")) == (0, "", "")


# word cap: only the final reply (text after the last tool call) counts
def transcript(final_words):
    t = Path(tempfile.mkdtemp()) / "t.jsonl"
    lines = [{"type": "user", "message": {"content": "do it"}},
             {"type": "assistant", "message": {"content": [{"type": "text", "text": "word " * 50},
                                                           {"type": "tool_use", "name": "Bash"}]}},
             {"type": "user", "message": {"content": [{"type": "tool_result", "content": "ok"}]}},
             {"type": "assistant", "message": {"content": [{"type": "text", "text": "word " * final_words}]}}]
    t.write_text("\n".join(json.dumps(l) for l in lines))
    return str(t)


code, out, _ = run(r, ["stop"], {"transcript_path": transcript(30)})
assert code == 0 and json.loads(out)["decision"] == "block" and "30 words" in out, out
assert run(r, ["stop"], {"transcript_path": transcript(10)})[1] == ""        # 50 narration words don't count
assert run(r, ["stop"], {"transcript_path": transcript(30), "stop_hook_active": True})[1] == ""  # block once
assert run(o, ["stop"], {"transcript_path": transcript(30)})[1] == "" and log(o)[-1]["event"] == "word_cap"

# other tools' payload shapes (per their docs)
patch = "*** Begin Patch\n*** Update File: pace.toml\n@@\n-a\n+b\n*** End Patch"
assert run(r, ["guard"], {"tool_name": "apply_patch", "tool_input": {"command": patch}})[0] == 2              # Codex
assert run(r, ["guard"], {"tool_name": "apply_patch", "tool_input": {"command": patch.replace("pace.toml", "src/a.py")}})[0] == 0
assert run(r, ["guard"], {"command": "sed -i '' s/a/b/ pace.toml", "hook_event_name": "beforeShellExecution"})[0] == 2  # Cursor
assert run(r, ["guard"], {"tool_name": "Shell", "tool_input": {"command": "git commit -m x"}})[0] == 2        # Cursor via .claude
assert run(r, ["guard"], {"tool_name": "run_shell_command", "tool_input": {"command": "git push"}})[0] == 2    # Gemini
assert run(r, ["guard"], {"tool_name": "write_file", "tool_input": {"file_path": "pace.toml"}})[0] == 2        # Gemini
assert run(r, ["guard"], {"toolName": "bash", "toolArgs": json.dumps({"command": "rm pace.toml"})})[0] == 2   # Copilot
assert run(r, ["guard"], {"tool_name": "exec", "tool_input": {"command": "git status"}})[0] == 0              # Devin
assert run(r, ["guard"], bash("git commit --no-verify -m x"))[0] == 2
assert run(r, ["guard"], bash("git commit --amend -m x"))[0] == 2 and "continuity break" in run(r, ["guard"], bash("git commit --amend -m x"))[2]
code, out, _ = run(r, ["stop"], {"hook_event_name": "Stop", "last_assistant_message": "word " * 30})          # Codex
assert json.loads(out)["decision"] == "block", out
code, out, _ = run(r, ["stop"], {"hook_event_name": "AfterAgent", "prompt_response": "word " * 30})           # Gemini
assert json.loads(out)["decision"] == "deny", out
assert run(r, ["stop"], {"hook_event_name": "stop", "loop_count": 1, "last_assistant_message": "word " * 30})[1] == ""  # Cursor, once
# root found by walking up from a subfolder, without CLAUDE_PROJECT_DIR (Codex passes cwd)
(r / ".git").mkdir(exist_ok=True); (r / "src").mkdir(exist_ok=True)
assert run(r / "src", ["guard"], {"tool_name": "Bash", "cwd": str(r / "src"), "tool_input": {"command": "rm ../pace.toml"}},
           project_env=False)[0] == 2

# fail open: broken pace.toml never blocks, error is logged
(o / "pace.toml").write_text("not = [valid")
assert run(o, ["guard"], bash("git commit -m x"))[0] == 0 and log(o)[-1]["event"] == "hook_error"

# comprehension gate
g = Path(tempfile.mkdtemp())
(g / "coverage-contract.json").write_text(json.dumps({"acceptance": [
    {"id": "AC-01", "tier": "core"}, {"id": "AC-02"}, {"id": "AC-03", "tier": "throwaway"}]}))
(g / "walkthroughs").mkdir()
(g / "walkthroughs" / "AC-01.md").write_text("# AC-01\n## What changed\nx\n## Explain-back\n")
code, out, _ = run(g, ["gate", "--contract", str(g / "coverage-contract.json")])
assert code == 1 and "AC-01: awaiting explain-back" in out and "AC-02: no walkthrough" in out and "AC-03" not in out, out
(g / "walkthroughs" / "AC-01.md").write_text("# AC-01\n## Explain-back\n2026-11-09: it flags claims missing a code.\n")
(g / "walkthroughs" / "AC-02.md").write_text("# AC-02\n## Explain-back\n2026-11-09: retries once.\n")
assert run(g, ["gate", "--contract", str(g / "coverage-contract.json")])[0] == 0

# review log + stats run
assert run(r, ["review", "--task", "PRD-007", "--minutes", "12", "--accepted", "yes"])[0] == 0
code, out, _ = run(r, ["stats"])
assert code == 0 and "reviews logged: 1, median 12 min, accepted 1" in out and "(claims ['C2'])" in out, out
print("pace: all checks passed")
