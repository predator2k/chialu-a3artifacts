#!/usr/bin/env python3
"""Checks of the exp10 smoke runs (run/<prefix>.*) against the 2026-09-25 audit's fixes.

    python3 smoke_check.py [--prefix smoke10] [--iterations 3] [--root $CHIALU/run]

Per run:
  prompts   every solution prompt: no "declaration.decl" (the Metrics leak into the controls, #2);
            SUBMISSION_NOTE exactly once; UNIT_HIERARCHY_NOTE once on the int target, never elsewhere
  dups      no two evaluated candidates with the same program sha256 (#1)
  seeds     every seed record has all goal values or feasible=False (#3); the chiALU fp run has front_3/front_4
  models    every LLM call and session is deepseek/deepseek-flash; no child session, no task tool (#18/#21)
  reads     no tool touches a path outside the session's workspace; no bash (#4)
  synth     synthesis median of 3 everywhere (#19)
  done      the run finished its iterations (status.json/iteration.txt, summary.json, pipeline.json)
Prints one line per failed check and a summary; exit 1 when anything failed or no run was found.
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import sys
from pathlib import Path

from adir.confine import SUBMISSION_NOTE, UNIT_HIERARCHY_NOTE

PATH_KEYS = ("filePath", "path", "file_path", "directory")
FAILS: list = []


def fail(run: str, check: str, msg: str) -> None:
    FAILS.append((run, check, msg))
    print(f"FAIL {run} [{check}] {msg}")


def jsonl(p: Path) -> list:
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def js(p: Path):
    try:
        return json.loads(p.read_text())
    except Exception:  # noqa: BLE001
        return None


def solution_prompts(run: Path) -> list:
    if (run / "prompts").is_dir():                       # adir: prompts/<time>_<role>_<parent>.md
        return sorted(p for p in (run / "prompts").glob("*.md") if "_solution_" in p.name)
    return sorted(run.glob("call_*/prompt.md"))          # the plain loop


def check_prompts(run: Path, name: str, is_int: bool) -> None:
    ps = solution_prompts(run)
    if not ps:
        fail(name, "prompts", "no solution prompt recorded")
    for p in ps:
        t = p.read_text(errors="replace")
        if "declaration.decl" in t:
            fail(name, "prompts", f"{p.name}: contains 'declaration.decl'")
        n = t.count(SUBMISSION_NOTE)
        if n != 1:
            fail(name, "prompts", f"{p.name}: SUBMISSION_NOTE {n} times")
        u = t.count(UNIT_HIERARCHY_NOTE)
        if u != (1 if is_int else 0):
            fail(name, "prompts", f"{p.name}: UNIT_HIERARCHY_NOTE {u} times ({'int' if is_int else 'not int'})")


def evaluated(recs: list) -> list:
    """The records of candidates that went through evaluation (a candidate refused before it, e.g. as a
    duplicate, carries no measurements)."""
    return [r for r in recs if r.get("measurements")]


def check_records(run: Path, name: str, recs: list, it: int) -> None:
    seen: dict = {}
    for r in evaluated(recs):
        sha = r.get("source_sha256")
        if sha:
            if sha in seen:
                fail(name, "dups", f"{r.get('candidate_id')} has the program of {seen[sha]} ({sha[:12]})")
            else:
                seen[sha] = r.get("candidate_id")
    seeds = [r for r in recs if r.get("is_seed")]
    if not seeds:
        fail(name, "seeds", "no seed record")
    for r in seeds:
        g = r.get("goal_values")
        has_goals = isinstance(g, list) and g and all(isinstance(x, (int, float)) for x in g)
        if not has_goals and r.get("feasible") is not False:
            fail(name, "seeds", f"{r.get('candidate_id')}: feasible={r.get('feasible')} goal_values={g}")
    if ".fp_alu_cmp.chialu" in name:
        names = {r.get("seed_name") for r in seeds}
        for want in ("front_3", "front_4"):
            if want not in names:
                fail(name, "seeds", f"no seed record for {want}")
    for r in recs:
        v = ((r.get("measurements") or {}).get("synth_ppa") or {}).get("value")
        if isinstance(v, dict) and "runs" in v and len(v["runs"] or []) != 3:
            fail(name, "synth", f"{r.get('candidate_id')}: synth_ppa median of {len(v['runs'] or [])} runs")
    if not any(isinstance(((r.get("measurements") or {}).get("synth_ppa") or {}).get("value"), dict) for r in recs):
        fail(name, "synth", "no synth_ppa measurement in any record")


def inside(path: str, root: str) -> bool:
    p = os.path.normpath(path if os.path.isabs(path) else os.path.join(root, path))
    root = os.path.normpath(root)
    return p == root or p.startswith(root + os.sep)


def check_sessions(run: Path, name: str) -> None:
    sdir = run / "sessions"
    idx = js(sdir / "index.json") or {}
    files = sorted(sdir.glob("*.json.gz"))
    if not files:
        fail(name, "models", "no archived session (sessions/*.json.gz)")
    for sid, e in (idx.items() if isinstance(idx, dict) else []):
        if isinstance(e, dict) and not e.get("file") and (e.get("missing") or e.get("reason") or e.get("error")):
            fail(name, "models", f"session {sid} not archived: {e}")
    for f in files:
        try:
            d = json.loads(gzip.open(f).read())
        except Exception as ex:  # noqa: BLE001
            fail(name, "models", f"{f.name}: unreadable ({ex})")
            continue
        if not isinstance(d, dict):
            fail(name, "models", f"{f.name}: not a session export")
            continue
        info = d.get("info") or {}
        sid, ws = info.get("id", f.name), info.get("directory") or ""
        m = info.get("model") or {}
        if m and (m.get("providerID"), m.get("id")) != ("deepseek", "deepseek-flash"):
            fail(name, "models", f"{sid}: session model {m}")
        if info.get("parentID"):
            fail(name, "models", f"{sid}: a child session (parent {info['parentID']})")
        for msg in d.get("messages") or []:
            mi = msg.get("info") or {}
            mm = mi.get("model") or {}
            prov, mod = mm.get("providerID") or mi.get("providerID"), mm.get("modelID") or mi.get("modelID")
            if (prov or mod) and (prov, mod) != ("deepseek", "deepseek-flash"):
                fail(name, "models", f"{sid}: message {mi.get('id')} on {prov}/{mod}")
            for part in msg.get("parts") or []:
                if part.get("type") in ("subtask", "agent"):
                    fail(name, "models", f"{sid}: a {part.get('type')} part")
                if part.get("type") != "tool":
                    continue
                tool = part.get("tool")
                st = part.get("state") or {}
                inp = st.get("input") or {}
                if tool == "task":
                    fail(name, "models", f"{sid}: task tool call ({st.get('status')})")
                if tool == "bash" and st.get("status") == "completed":
                    fail(name, "reads", f"{sid}: bash ran: {str(inp.get('command'))[:120]}")
                if not ws:
                    continue
                for k in PATH_KEYS:
                    v = inp.get(k)
                    if isinstance(v, str) and v and not inside(v, ws):
                        # a denied call is no read; opencode marks it an error
                        state = st.get("status")
                        if state == "completed":
                            fail(name, "reads", f"{sid}: {tool} {k}={v} outside {ws}")
                pat = inp.get("pattern")
                if tool == "glob" and isinstance(pat, str) and os.path.isabs(pat) and not inside(pat, ws) \
                        and st.get("status") == "completed":
                    fail(name, "reads", f"{sid}: glob pattern {pat} outside {ws}")


def check_calls(run: Path, name: str) -> None:
    calls = jsonl(run / "llm_calls.jsonl")
    for c in calls:
        if (c.get("provider"), c.get("model")) != ("deepseek", "deepseek-flash"):
            fail(name, "models", f"llm call {c.get('time')} role {c.get('role')}: {c.get('provider')}/{c.get('model')}")


def check_done(run: Path, name: str, it: int) -> None:
    if ".plain" in name:
        s = js(run / "summary.json") or {}
        if int(s.get("calls") or 0) < it:
            fail(name, "done", f"summary.json calls={s.get('calls')} < {it}")
        if s.get("synth_repeats") != 3:
            fail(name, "synth", f"summary.json synth_repeats={s.get('synth_repeats')}")
        return
    st = js(run / "status.json") or {}
    try:
        n = int((run / "iteration.txt").read_text().strip())
    except Exception:  # noqa: BLE001
        n = 0
    if st.get("state") != "done" or n < it:
        fail(name, "done", f"status {st.get('state')}, iteration.txt {n} < {it}" if n < it else f"status {st.get('state')}")
    if ".chialu" in name:
        pj = js(run / "pipeline.json") or {}
        ex = {k: (v.get("exit") if isinstance(v, dict) else v) for k, v in (pj.get("stages") or {}).items()}
        if ex.get("seeds") != 0 or ex.get("search") != 0:
            fail(name, "done", f"pipeline stages {ex}")
        if pj.get("synth_repeats") != 3:
            fail(name, "synth", f"pipeline.json synth_repeats={pj.get('synth_repeats')}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--prefix", default="smoke10")
    ap.add_argument("--iterations", type=int, default=3)
    ap.add_argument("--root", default=os.path.join(os.environ.get("CHIALU", "."), "run"))
    a = ap.parse_args()
    runs = sorted(p for p in Path(a.root).glob(f"{a.prefix}.*") if p.is_dir())
    if not runs:
        print(f"FAIL no run {a.root}/{a.prefix}.*")
        return 1
    for run in runs:
        name = run.name
        recs = jsonl(run / "results_db.jsonl")
        check_prompts(run, name, ".int_subword_alu." in name + ".")
        check_records(run, name, recs, a.iterations)
        check_calls(run, name)
        check_sessions(run, name)
        check_done(run, name, a.iterations)
    bad = sorted({r for r, _, _ in FAILS})
    print(f"{len(runs)} runs, {len(FAILS)} failed checks" + (f" in {', '.join(bad)}" if bad else "; all checks passed"))
    return 1 if FAILS else 0


if __name__ == "__main__":
    sys.exit(main())
