#!/usr/bin/env python3
"""pace: claims-ledger guard, reply word cap, comprehension gate, stats.

Inert unless the project root has pace.toml. Hook crashes fail open (exit 0)
and are logged to .pace/log.jsonl. Hooks read the Claude Code, Codex, Gemini CLI,
Cursor, Copilot CLI and Devin payload shapes. Subcommands:
  guard   pre-tool hook (shell commands and file edits)
  stop    end-of-turn hook (word cap)
  session session-start hook: tells a new or resumed agent which promises are in force
  install-git-hook  add the pre-commit line to this clone's git hooks (idempotent; for cloud setup scripts)
  harvest [--all] [--limit N]  list promise-like sentences already in the repo's specs and docs
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
# harvest: strong promise wording, then weaker wording shown only with --all
STRONG = re.compile(r"\b(never|must not|shall not|shall|guarantee[sd]?|under no circumstances|at no time|"
                    r"(?:is|are) not (?:allowed|permitted)|no \w+(?: \w+)? without)\b", re.I)
RFC2119 = re.compile(r"\b(MUST(?: NOT)?|SHALL(?: NOT)?|REQUIRED|NON-NEGOTIABLE|RULE-\d+)\b")  # spec-tool normative words
WEAK = re.compile(r"\b(must|always|only|required to|mandatory)\b", re.I)
DOC_EXT = {".md", ".mdx", ".txt", ".rst", ".adoc"}
SKIP_DIRS = {"node_modules", "vendor", "dist", "build", ".git", ".agents", ".claude", ".cursor", ".codex",
             ".gemini", ".devin", ".cline", ".pace", "walkthroughs"}
SPEC_SOURCES = [  # (fnmatch glob, label): where spec-driven tools keep requirements (their docs, Nov 2026); listed first
    ("openspec/specs/*.md", "openspec"), ("openspec/changes/*.md", "openspec"),
    (".specify/memory/constitution.md", "spec-kit"), ("specs/*/spec.md", "spec-kit"), ("specs/*/plan.md", "spec-kit"),
    (".kiro/specs/*.md", "kiro"), (".kiro/steering/*.md", "kiro"),
    (".planning/REQUIREMENTS.md", "gsd"), (".planning/PROJECT.md", "gsd"),
    ("_bmad-output/*.md", "bmad"),
    ("docs/superpowers/specs/*.md", "superpowers"), ("docs/superpowers/plans/*.md", "superpowers"),
]


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


def parse_toml(text):
    try:
        import tomllib  # Python 3.11+
        return tomllib.loads(text)
    except ImportError:
        pass
    # ponytail: subset parser for Python 3.8-3.10 (common on cloud images): [table], [[array]],
    # key = "str" | 'str' | int | float | bool | [array]. Anything else raises, and hooks fail open.
    data, cur = {}, None
    cur = data
    for n, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        m = re.fullmatch(r"\[\[\s*([\w.-]+)\s*\]\]\s*(#.*)?", line) or re.fullmatch(r"\[\s*([\w.-]+)\s*\]\s*(#.*)?", line)
        if m:
            cur = {}
            if line.startswith("[["):
                data.setdefault(m.group(1), []).append(cur)
            else:
                cur = data.setdefault(m.group(1), {})
            continue
        m = re.fullmatch(r"([\w-]+)\s*=\s*(.+)", line)
        if not m:
            raise ValueError(f"pace.toml line {n}: cannot parse {line!r}")
        cur[m.group(1)] = _toml_value(m.group(2), n)
    return data


def _toml_value(v, n):
    if v[0] in "\"[":
        val, end = json.JSONDecoder().raw_decode(v)
    elif v[0] == "'":
        end = v.index("'", 1) + 1
        val = v[1:end - 1]
    else:
        tok = v.split("#", 1)[0].strip()
        end = len(v) if "#" not in v else v.index("#")
        val = {"true": True, "false": False}.get(tok)
        if val is None:
            try:
                val = int(tok)
            except ValueError:
                try:
                    val = float(tok)
                except ValueError:
                    raise ValueError(f"pace.toml line {n}: unsupported value {v!r}") from None
    rest = v[end:].strip()
    if rest and not rest.startswith("#"):
        raise ValueError(f"pace.toml line {n}: unexpected {rest!r}")
    return val


def load(r):
    f = r / "pace.toml"
    if not f.exists():
        return None
    d = parse_toml(f.read_text())
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
    """-> [(claim, status, output tail)], status in holds | BREAK | known-break | error | uncompiled.
    known-break: the owner marked an existing violation with known_break = "why"; reported, never blocks."""
    out = []
    for c in claims:
        cmd = check_cmd(r, c)
        if not cmd:
            out.append((c, "uncompiled", "no check yet"))
            continue
        try:
            p = subprocess.run(cmd, cwd=r, capture_output=True, text=True, timeout=CHECK_TIMEOUT)
            status = "holds" if p.returncode == 0 else "known-break" if c.get("known_break") else "BREAK"
            out.append((c, status, (p.stdout + p.stderr).strip()[-400:]))
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
    if cfg["mode"] != "enforce":  # visible in the transcript, so observe works where .pace/ doesn't survive (cloud)
        print(json.dumps({"systemMessage": "pace (observe mode, not blocking): enforce mode would stop this. "
                          + "; ".join(f'{c["id"]}: "{c.get("said", "")}"' for c, _, _ in breaks)}))
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
        note = (f"\n       {last_line(o)}" if s in ("BREAK", "error")
                else f"\n       known break: {c['known_break']}" if s == "known-break"
                else "\n       fixed: the owner can remove known_break" if s == "holds" and c.get("known_break") else "")
        print(f'{c["id"]:<6} {s:<11} {c.get("said", "")}' + note)
    print(f'mode: {led[0]["mode"]}')
    return 1 if any(s == "BREAK" for _, s, _ in res) else 0


GIT_HOOK_MARK = "# agent-pace: replay the claims ledger before each commit"


def cmd_install_git_hook(r):
    """Fresh clones (cloud sandboxes) have no git hooks; run this from the environment's setup script."""
    try:
        hooks = Path(subprocess.run(["git", "rev-parse", "--git-path", "hooks"], cwd=r, capture_output=True,
                                    text=True, timeout=30, check=True).stdout.strip())
    except (OSError, subprocess.SubprocessError):
        print("pace: not a git repository:", r)
        return 1
    hooks = hooks if hooks.is_absolute() else r / hooks
    me = Path(__file__).resolve()
    script = f'"$(git rev-parse --show-toplevel)/{me.relative_to(r).as_posix()}"' if r in me.parents else f'"{me}"'
    block = (f"\n{GIT_HOOK_MARK}\nPY=$(command -v python3 || command -v python || command -v py)\n"
             f'if [ -n "$PY" ]; then "$PY" {script} pre-commit || exit 1; fi\n')
    f = hooks / "pre-commit"
    text = f.read_text() if f.exists() else "#!/bin/sh\n"
    if GIT_HOOK_MARK in text:
        print(f"pace: already installed in {f}")
        return 0
    hooks.mkdir(parents=True, exist_ok=True)
    f.write_text(text.rstrip("\n") + "\n" + block)
    f.chmod(f.stat().st_mode | 0o111)
    print(f"pace: pre-commit hook installed in {f}")
    return 0


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


def session(r, cfg, claims):
    """SessionStart: give a new or resumed agent the promises before it changes anything."""
    if not claims:
        return 0
    lines = [f'- {c["id"]}: "{c.get("said", "")}" (to {c.get("to", "?")})'
             + (f' [known break: {c["known_break"]}]' if c.get("known_break") else "") for c in claims]
    logf = r / ".pace" / "log.jsonl"
    brk = [json.loads(l) for l in open(logf) if '"continuity_break"' in l] if logf.exists() else []
    last = f'\nLast continuity break: {", ".join(brk[-1]["claims"])} at {brk[-1]["ts"]}.' if brk else ""
    print(f'agent-pace is on in this project (mode: {cfg["mode"]}). Every commit must keep these promises from pace.toml:\n'
          + "\n".join(lines) +
          "\npace.toml and files in claims/checks/ are owner-only. If a check fails, stop and tell the user "
          "which change broke which promise." + last)
    return 0


def repo_files(r):
    try:
        out = subprocess.run(["git", "ls-files"], cwd=r, capture_output=True, text=True, timeout=30)
        if out.returncode == 0:
            return [r / f for f in out.stdout.splitlines()]
    except (OSError, subprocess.TimeoutExpired):
        pass
    return [p for p in r.rglob("*") if p.is_file()]


def cmd_harvest(r, led, show_all, limit):
    """Brownfield: list sentences in specs and docs that read like promises, specs first. Writes nothing."""
    from fnmatch import fnmatch
    said = [c.get("said", "").lower() for c in (led[1] if led else []) if c.get("said")]
    found = []
    for f in repo_files(r):
        rel = f.relative_to(r).as_posix()
        if f.suffix.lower() not in DOC_EXT or SKIP_DIRS & set(rel.split("/")[:-1]) or "changelog" in f.name.lower():
            continue
        label = next((lab for g, lab in SPEC_SOURCES if fnmatch(rel, g)), "doc")
        fence = False
        for i, line in enumerate(open(f, errors="ignore"), 1):
            if line.lstrip().startswith(("```", "~~~")):
                fence = not fence
            text = line.strip().lstrip("-*>#0123456789. ").replace("**", "").strip()
            if fence or len(text) < 12 or "SUB-SKILL" in text:  # skip agent-workflow boilerplate
                continue
            strength = 2 if STRONG.search(text) or RFC2119.search(text) else 1 if show_all and WEAK.search(text) else 0
            if strength:
                known = any(s and s in text.lower() for s in said)
                found.append((label == "doc", -strength, rel, i, label, text[:180], known))
    found.sort()
    for _, _, rel, i, label, text, known in found[:limit]:
        print(f"{rel}:{i}  [{label}]{'  (in ledger)' if known else ''}\n    {text}")
    files = len({x[2] for x in found})
    print(f"\n{len(found)} candidate sentences in {files} files" + (f", showing {limit}" if len(found) > limit else "")
          + ". Keep only promises made to someone outside the code; the claims skill turns each one into a check.")
    return 0


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
    if sub in ("guard", "stop", "session"):
        r = None
        try:
            ev = json.load(sys.stdin)
            r = project_root(ev)
            led = load(r)
            if not led:
                return 0
            return guard(r, *led, ev) if sub == "guard" else stop(r, led[0], ev) if sub == "stop" else session(r, *led)
        except Exception as e:  # fail open: a broken hook must never stop work
            try:
                log(r or project_root(), event="hook_error", hook=sub, error=repr(e)[:300])
            except Exception:
                pass
            return 0
    ap = argparse.ArgumentParser(prog="pace")
    sp = ap.add_subparsers(dest="sub", required=True)
    sp.add_parser("check")
    sp.add_parser("pre-commit")
    sp.add_parser("install-git-hook")
    sp.add_parser("stats")
    h = sp.add_parser("harvest")
    h.add_argument("--all", action="store_true", help="also show weaker wording (must, always, only)")
    h.add_argument("--limit", type=int, default=60)
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
    if a.sub == "install-git-hook":
        return cmd_install_git_hook(r)
    if a.sub == "pre-commit":
        return cmd_pre_commit(r, load(r))
    if a.sub == "gate":
        return cmd_gate(a.contract, a.walkthroughs)
    if a.sub == "harvest":
        return cmd_harvest(r, load(r), a.all, a.limit)
    if a.sub == "review":
        return cmd_review(r, a.task, a.minutes, a.accepted)
    return cmd_stats(r)


if __name__ == "__main__":
    sys.exit(main())
