#!/usr/bin/env python3
"""pace: claims-ledger guard, reply word cap, comprehension gate, stats.

Inert unless the project root has pace.toml. Hook crashes fail open (exit 0)
and are logged to .pace/log.jsonl. Hooks read the Claude Code, Codex, Gemini CLI,
Cursor, Copilot CLI and Devin payload shapes. Subcommands:
  guard   pre-tool hook (shell commands and file edits)
  stop    end-of-turn hook (word cap)
  check   replay the ledger, print one line per claim, exit 1 on a break
  pre-commit  git hook for any agent tool: replay, block only in enforce mode
  gate    --contract coverage-contract.json [--walkthroughs DIR]
  review  --task T --minutes N --accepted yes|no
  stats   read-speed and observe-log numbers for this project
"""
import argparse, csv, glob, json, os, re, statistics, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path

GATE = re.compile(r"\bgit\s+(commit|push|merge)\b|\bgh\s+pr\s+(create|merge)\b")
_P = r"[^|;&]*(pace\.toml|claims/checks)"
WRITE = re.compile(
    r">>?\s*['\"]?\S*(pace\.toml|claims/checks)"
    r"|\b(tee|mv|rm|cp|truncate|ln|chmod|touch)\b" + _P +
    r"|\b(sed|perl)\s+-\w*i" + _P +
    r"|\bgit\s+(checkout|restore|rm|mv)\b" + _P +
    r"|open\([^)]*(pace\.toml|claims/checks)[^)]*['\"][wax+]")
NO_VERIFY = re.compile(r"\bgit\s+commit\b[^|;&]*(--no-verify|\s-\w*n)")
SHELL_TOOLS = {"Bash", "Shell", "bash", "exec", "run_shell_command", "run_commands"}  # Claude/Codex, Cursor, Copilot, Devin, Gemini, Cline
PATCH_FILE = re.compile(r"^\*\*\* (?:Update|Add|Delete) File: (.+)$|^\*\*\* Move to: (.+)$", re.M)  # Codex apply_patch
# ponytail: regex guard on Bash. A determined script can still write; the git history of pace.toml is the backstop.
CHECK_TIMEOUT = 120


def project_root(ev=None):
    """Nearest folder with pace.toml, from the tool's project dir or cwd up to the git root."""
    ev = ev or {}
    roots = ev.get("workspace_roots") or [None]  # Cursor
    start = Path(os.environ.get("CLAUDE_PROJECT_DIR") or os.environ.get("GEMINI_PROJECT_DIR")
                 or os.environ.get("DEVIN_PROJECT_DIR") or roots[0] or ev.get("cwd") or os.getcwd()).resolve()
    for d in [start, *start.parents]:
        if (d / "pace.toml").exists():
            return d
        if (d / ".git").exists():
            break
    return start


def load(r):
    f = r / "pace.toml"
    if not f.exists():
        return None
    import tomllib  # Python 3.11+; on older Pythons the hook fails open and logs a hook_error
    d = tomllib.loads(f.read_text())
    return {"mode": "observe", "word_cap": 150, **d.get("pace", {})}, d.get("claim", [])


def log(r, **e):
    (r / ".pace").mkdir(exist_ok=True)
    e["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with open(r / ".pace" / "log.jsonl", "a") as f:
        f.write(json.dumps(e) + "\n")


def deny(msg):
    print(msg, file=sys.stderr)
    return 2


def check_cmd(r, c):
    """argv for claims/checks/<id>.sh|.py; checks are files only, so every one is reviewable in git."""
    for p in sorted((r / "claims" / "checks").glob(f"{c['id']}.*")):
        if p.suffix in (".sh", ".py"):
            return ["bash" if p.suffix == ".sh" else sys.executable, str(p)]
    return None


def replay(r, claims):
    """-> [(claim, status, output tail)], status in holds | BREAK | error | uncompiled."""
    out = []
    for c in claims:
        cmd = check_cmd(r, c)
        if not cmd:
            out.append((c, "uncompiled", "no check yet"))
            continue
        try:
            p = subprocess.run(cmd, cwd=r, capture_output=True, text=True, timeout=CHECK_TIMEOUT)
            out.append((c, "holds" if p.returncode == 0 else "BREAK", (p.stdout + p.stderr).strip()[-400:]))
        except subprocess.TimeoutExpired:
            out.append((c, "error", f"check timed out after {CHECK_TIMEOUT} s"))
    return out


def last_line(text):
    return text.strip().splitlines()[-1] if text.strip() else ""


def tool_call(ev):
    """-> ("shell", command, []) or ("edit", "", [paths]) from any supported hook payload."""
    tool = ev.get("tool_name") or ev.get("toolName") or ""
    inp = ev.get("tool_input") or ev.get("toolArgs") or {}
    if isinstance(inp, str):
        try:
            inp = json.loads(inp)
        except ValueError:
            inp = {}
    if not tool and isinstance(ev.get("command"), str):  # Cursor beforeShellExecution
        return "shell", ev["command"], []
    cmd = inp.get("command", "") if isinstance(inp, dict) else ""
    if tool == "apply_patch":
        return "edit", "", [a or b for a, b in PATCH_FILE.findall(cmd)]
    if tool in SHELL_TOOLS:
        return "shell", cmd, []
    f = isinstance(inp, dict) and (inp.get("file_path") or inp.get("notebook_path") or inp.get("filePath") or inp.get("path"))
    return "edit", "", [f] if f else []


def guard(r, cfg, claims, ev):
    kind, cmd, paths = tool_call(ev)
    ledger, checks = r / "pace.toml", r / "claims" / "checks"
    if kind == "edit":
        for f in paths:
            p = (r / f.strip()).resolve()
            if p == ledger:
                return deny("pace: pace.toml is owner-only. Show the change as a TOML block for the user to paste.")
            if checks in p.parents and p.exists():
                return deny(f"pace: {p.name} is an existing claim check. Never change a check to make it pass; "
                            "tell the user which change broke it.")
        return 0
    if claims and NO_VERIFY.search(cmd):
        return deny("pace: --no-verify skips the claims ledger. Commit without it.")
    if WRITE.search(cmd):
        return deny("pace: this command may write to pace.toml or claims/checks/. Read them only; "
                    "create a new check file with the Write tool.")
    if not claims or not GATE.search(cmd):
        return 0
    breaks = [x for x in replay(r, claims) if x[1] == "BREAK"]
    if not breaks:
        return 0
    log(r, event="continuity_break", mode=cfg["mode"], claims=[c["id"] for c, _, _ in breaks], command=cmd[:200])
    if cfg["mode"] != "enforce":
        return 0
    return deny(break_message(breaks))


def break_message(breaks):
    lines = [f'- {c["id"]}: "{c.get("said", "")}" (said to {c.get("to", "?")}). Check output: {last_line(o) or "failed"}'
             for c, _, o in breaks]
    return ("pace: continuity break. This change contradicts a promise in pace.toml:\n" + "\n".join(lines) +
            "\nDo not edit the claim or its check. Tell the user in one line which change caused it, then stop.")


def reply_words(transcript):
    """Words in the final reply: assistant text after the last tool call of the last user turn."""
    n = 0
    for line in open(transcript, errors="ignore"):
        try:
            e = json.loads(line)
        except ValueError:
            continue
        if e.get("isSidechain"):
            continue
        c = (e.get("message") or {}).get("content")
        blocks = [b for b in c if isinstance(b, dict)] if isinstance(c, list) else []
        if e.get("type") == "user" and (isinstance(c, str) or any(b.get("type") == "text" for b in blocks)):
            n = 0
        elif e.get("type") == "assistant":
            if any(b.get("type") == "tool_use" for b in blocks):
                n = 0  # text next to a tool call is narration, not the reply
            else:
                n += sum(len(b.get("text", "").split()) for b in blocks if b.get("type") == "text")
    return n


def stop(r, cfg, ev):
    cap = int(cfg.get("word_cap") or 0)
    if not cap or ev.get("stop_hook_active") or ev.get("loop_count"):  # send back once only
        return 0
    text = ev.get("last_assistant_message") or ev.get("prompt_response")  # Codex, Gemini
    path = ev.get("transcript_path") or ev.get("transcriptPath")
    if isinstance(text, str):
        n = len(text.split())
    elif path and os.path.exists(path):
        n = reply_words(path)  # Claude Code transcript format; other formats count 0 and never block
    else:
        return 0
    if n <= cap:
        return 0
    log(r, event="word_cap", mode=cfg["mode"], words=n, cap=cap)
    if cfg["mode"] == "enforce":
        reason = (f"pace: your reply is {n} words; the cap here is {cap}. Put the detail in a file and reply again "
                  f"in {cap} words or fewer: the result, one question, or the blocker.")
        event = ev.get("hook_event_name", "")
        print(json.dumps({"followup_message": reason} if event == "stop"  # Cursor
                         else {"decision": "deny" if event == "AfterAgent" else "block", "reason": reason}))  # Gemini | rest
    return 0


def cmd_check(r, led):
    if not led:
        print("pace: no pace.toml in", r)
        return 0
    res = replay(r, led[1])
    for c, s, o in res:
        print(f'{c["id"]:<6} {s:<11} {c.get("said", "")}' + (f"\n       {last_line(o)}" if s in ("BREAK", "error") else ""))
    print(f'mode: {led[0]["mode"]}')
    return 1 if any(s == "BREAK" for _, s, _ in res) else 0


def cmd_pre_commit(r, led):
    """git pre-commit hook, for any agent tool: replay the ledger, block only in enforce mode."""
    if not led:
        return 0
    cfg, claims = led
    breaks = [x for x in replay(r, claims) if x[1] == "BREAK"]
    if not breaks:
        return 0
    log(r, event="continuity_break", mode=cfg["mode"], claims=[c["id"] for c, _, _ in breaks], command="git pre-commit")
    print(break_message(breaks) + ("" if cfg["mode"] == "enforce" else "\n(observe mode: commit allowed)"), file=sys.stderr)
    return 1 if cfg["mode"] == "enforce" else 0


def cmd_gate(contract, wdir):
    wdir = Path(wdir) if wdir else Path(contract).parent / "walkthroughs"
    bad = 0
    for a in json.load(open(contract))["acceptance"]:
        if a.get("tier", "core") != "core":  # untagged counts as core
            continue
        f = wdir / f"{a['id']}.md"
        t = f.read_text() if f.exists() else ""
        m = re.search(r"^## Explain-back[^\n]*\n(.*?)(?=^## |\Z)", t, re.S | re.M)
        s = "no walkthrough" if not t.strip() else "explained" if m and m.group(1).strip() else "awaiting explain-back"
        bad += s != "explained"
        print(f"{a['id']}: {s}")
    return 1 if bad else 0


def cmd_review(r, task, minutes, accepted):
    (r / ".pace").mkdir(exist_ok=True)
    f = r / ".pace" / "reviews.csv"
    new = not f.exists()
    with open(f, "a", newline="") as fh:
        w = csv.writer(fh)
        if new:
            w.writerow(["date", "task", "minutes", "accepted"])
        w.writerow([datetime.now().date().isoformat(), task, minutes, accepted])
    print(f"pace: logged to {f}")
    return 0


def cmd_stats(r, days=60, wpm=250):
    enc = re.sub(r"[^A-Za-z0-9]", "-", str(r))
    cut, rows = time.time() - days * 86400, []
    for f in glob.glob(os.path.expanduser(f"~/.claude/projects/{enc}*/*.jsonl")):
        if os.path.getmtime(f) < cut:
            continue
        words, last_ts = 0, None
        for line in open(f, errors="ignore"):
            try:
                e = json.loads(line)
            except ValueError:
                continue
            if e.get("isSidechain"):
                continue
            ts, c = e.get("timestamp"), (e.get("message") or {}).get("content")
            if e.get("type") == "assistant" and isinstance(c, list):
                words += sum(len(b.get("text", "").split()) for b in c if isinstance(b, dict) and b.get("type") == "text")
                last_ts = ts or last_ts
            elif e.get("type") == "user":
                text = c if isinstance(c, str) else "".join(
                    b.get("text", "") for b in (c or []) if isinstance(b, dict) and b.get("type") == "text")
                if not text or text.startswith(("<", "Base directory")) or "tool_use_id" in line[:400]:
                    continue
                if words >= 150 and last_ts and ts:
                    gap = (datetime.fromisoformat(ts.replace("Z", "+00:00")) -
                           datetime.fromisoformat(last_ts.replace("Z", "+00:00"))).total_seconds()
                    if 0 < gap < 3600:
                        rows.append((words, gap))
                words = 0
    print(f"last {days} days, transcripts for {r}")
    if rows:
        fast = sum(1 for w, g in rows if g < 0.5 * w / wpm * 60)
        print(f"  your replies after an agent output of 150+ words: {len(rows)}")
        print(f"  sent faster than half the skim time at {wpm} wpm: {fast} ({fast / len(rows):.0%})")
        print(f"  median agent output before your reply: {statistics.median(w for w, _ in rows):.0f} words")
    else:
        print("  no replies after long agent outputs found")
    logf = r / ".pace" / "log.jsonl"
    ev = [json.loads(l) for l in open(logf)] if logf.exists() else []
    cap = [e for e in ev if e.get("event") == "word_cap"]
    brk = [e for e in ev if e.get("event") == "continuity_break"]
    err = [e for e in ev if e.get("event") == "hook_error"]
    print(f"  word-cap hits: {len(cap)}" + (f" (median {statistics.median(e['words'] for e in cap):.0f} words)" if cap else ""))
    print(f"  continuity breaks: {len(brk)}" + (f" (claims {sorted({i for e in brk for i in e['claims']})})" if brk else ""))
    print(f"  hook errors: {len(err)}")
    revf = r / ".pace" / "reviews.csv"
    rev = list(csv.DictReader(open(revf))) if revf.exists() else []
    if rev:
        print(f"  reviews logged: {len(rev)}, median {statistics.median(float(x['minutes']) for x in rev):.0f} min, "
              f"accepted {sum(x['accepted'].lower().startswith('y') for x in rev)}")
    else:
        print("  reviews logged: 0")
    return 0


def main():
    sub = sys.argv[1] if len(sys.argv) > 1 else ""
    if sub in ("guard", "stop"):
        r = None
        try:
            ev = json.load(sys.stdin)
            r = project_root(ev)
            led = load(r)
            if not led:
                return 0
            return guard(r, *led, ev) if sub == "guard" else stop(r, led[0], ev)
        except Exception as e:  # fail open: a broken hook must never stop work
            if sub == "stop" and isinstance(e, ImportError):  # say it once per reply, not on every tool call
                print(json.dumps({"systemMessage": "pace: needs Python 3.11+ (tomllib), so it is doing nothing here."}))
            try:
                log(r or project_root(), event="hook_error", hook=sub, error=repr(e)[:300])
            except Exception:
                pass
            return 0
    ap = argparse.ArgumentParser(prog="pace")
    sp = ap.add_subparsers(dest="sub", required=True)
    sp.add_parser("check")
    sp.add_parser("pre-commit")
    sp.add_parser("stats")
    g = sp.add_parser("gate")
    g.add_argument("--contract", required=True)
    g.add_argument("--walkthroughs")
    v = sp.add_parser("review")
    v.add_argument("--task", required=True)
    v.add_argument("--minutes", type=float, required=True)
    v.add_argument("--accepted", choices=["yes", "no"], required=True)
    a = ap.parse_args()
    r = project_root()
    if a.sub == "check":
        return cmd_check(r, load(r))
    if a.sub == "pre-commit":
        return cmd_pre_commit(r, load(r))
    if a.sub == "gate":
        return cmd_gate(a.contract, a.walkthroughs)
    if a.sub == "review":
        return cmd_review(r, a.task, a.minutes, a.accepted)
    return cmd_stats(r)


if __name__ == "__main__":
    sys.exit(main())
