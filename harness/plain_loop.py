#!/usr/bin/env python3
"""The plain agent loop of Table A (chiALU's docs/evaluation-plan.md, section
4): one agent CLI is given the seed program, the evaluator and the metrics and
is asked to improve the unit, once per model call, without ADIR. No prompt
composition, no declarations, no archive context, no plans, no knowledge cards
and no review reach the agent; the seed, the evaluator functions, the model
invocation and the call budget are chiALU's.

    PYTHONPATH=<chialu>:<chialu>/third_party/adir python3 harness/plain_loop.py \\
        targets/eval/fp_alu_cmp.yaml --agent opencode --provider google-vertex \\
        --model gemini-3.1-pro-preview --effort medium --calls 200 --out runs/plain/fp_alu_cmp

The run file is loaded the way chiALU's flow loads it (`adir.instance.load`,
`adir.seeds.seed_programs`); the candidate is judged by the evaluator nodes
the run file names, called as plain functions (`chialu.eda.lint`,
`chialu.eda.conformance`, `chialu.eda.yosys_stat`, `chialu.eda.synth_ppa`)
under the run file's gating; the agent is invoked through the same
`adir.backends.skydiscover.AgentLLM` construction the flow uses, so the model,
the provider, the reasoning effort and the per-attempt timeout match chiALU's
row. Every candidate is one JSON line of `<out>/results_db.jsonl` in the shape
of ADIR's archive record, so one table script reads both.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import re
import shutil
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

HERE = Path(__file__).resolve().parent
A3_ROOT = HERE.parent
STAGES = ("lint", "conformance", "fault", "stat", "synth")   # fault runs where the run file has the node
DEFAULT_TIMEOUT_S = 1200          # the run files' solution timeout_s: one attempt
# the feedback expressions of the run file this loop reproduces (review and synth_unit have no plain-loop counterpart)
FEEDBACK_KEYS = ("conformance.detail", "fault.detail", "synth_ppa.detail", "synth_ppa.summary", "synth_ppa.critical_path",
                 "synth_ppa.paths", "synth_ppa.area_by_hierarchy")
CANDIDATE_FILE = "candidate.sv"
PARENT_FILE = "program.sv"
SYSTEM_TEXT = (
    "You are a digital hardware designer. You optimize a combinational SystemVerilog unit for cell area and "
    "critical-path delay while keeping its interface and its bit-exact behavior. "
    "You work inside the directory of this call with your file tools (read, list, search, edit); you cannot "
    "run commands, and the evaluator runs after your reply."
)


def log(msg: str, out: Optional[Path] = None):
    line = f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}"
    print(line, flush=True)
    if out is not None:
        with open(out / "run.log", "a") as f:
            f.write(line + "\n")


# ------------------------------------------------------------------ the target

@dataclass
class Target:
    inst: object
    run_file: Path
    top: str
    pdk: str
    clock_ps: int
    effort: str
    synth_timeout_s: int
    verify_files: dict
    seed_name: str
    seed_rtl: str
    cells_screen: float
    spec: dict = field(default_factory=dict)
    fixed: dict = field(default_factory=dict)
    runtime: dict = field(default_factory=dict)
    # whether the run file bounds the delay by the clock (`synth_ppa.abc_delay_ps le vars.clock_ps`); a
    # least-delay target (`min_delay` in make_targets.py, clock_ps 300) maps every design for its least delay
    # and carries no such constraint
    synth_repeats: int = 5
    clock_bound: bool = True
    # the fault gate of a checked target (int_subword_alu): the checker the run file's checker_gen node renders
    # for the undeclared (default) check rules, which is what a plain program without declarations gets, and the
    # run file's fault.* constraints as (metric field, op, bound)
    checker_rtl: Optional[str] = None
    fault_rows: list = field(default_factory=list)


def chialu_root() -> Path:
    import chialu
    return Path(chialu.__file__).resolve().parents[1]


def find_run_file(p: str) -> Path:
    """The run file: as given, else relative to the chiALU tree on PYTHONPATH."""
    q = Path(p)
    if q.is_file():
        return q.resolve()
    r = chialu_root() / p
    if r.is_file():
        return r.resolve()
    raise SystemExit(f"run file {p} not found (tried {q.resolve()} and {r})")


def plain_rtl(program: str) -> str:
    """The RTL of an ADIR program text without ADIR's material: the member
    markers, the EVOLVE markers and the declaration block (VAR and
    STRUCTURE lines) are comments the flow's evaluator ignores, so the
    text synthesizes to the same netlist."""
    from adir import artifacts as A
    from adir.declaration import MARK_END, MARK_START
    out, inside = [], False
    for line in program.splitlines(keepends=True):
        body = re.sub(r"^\s*(//|#|--|\*|;)?\s?", "", line, count=1).strip()
        if not inside and body == MARK_START:
            inside = True
            continue
        if inside:
            if body == MARK_END:
                inside = False
            continue
        if A.EVOLVE_START in line or A.EVOLVE_END in line or A.MEMBER_MARK in line:
            continue
        out.append(line)
    return "".join(out)


def seed_text(seed: Path, fpnew_point: str) -> tuple:
    """(name, text) of a hand seed. A file under baselines/fpnew/ is the
    FPnew wrapper, which is joined with the CVFPU sources of files.txt by
    that directory's build.py (`joined`), the design point from
    --fpnew-point; any other file is the complete program itself."""
    seed = seed.resolve()
    build = seed.parent / "build.py"
    if seed.parent.name == "fpnew" and build.is_file():
        spec = importlib.util.spec_from_file_location("fpnew_build", build)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return f"{seed.stem}_{fpnew_point.lower()}", mod.joined(fpnew_point, seed.name)
    return seed.stem, plain_rtl(seed.read_text())


def _cells_screen(nodes: dict) -> float:
    """The factor k of the run file's `yosys_stat.cells le k * seed.yosys_stat.cells` screen, 2.0 without one."""
    for spec in nodes.values():
        for w in (spec.get("when") or []) if isinstance(spec, dict) else []:
            m = re.match(r"yosys_stat\.cells\s+le\s+([\d.]+)\s*\*\s*seed\.yosys_stat\.cells", str(w))
            if m:
                return float(m.group(1))
    return 2.0


def load_target(run_file: Path, scratch: Path, seed: Optional[Path], fpnew_point: str,
                clock_ps: Optional[int]) -> Target:
    from adir.instance import load
    from adir.seeds import seed_programs
    scratch.mkdir(parents=True, exist_ok=True)
    inst = load(str(run_file), run_dir_override=str(scratch))
    nodes = inst.raw["evaluate"]["nodes"]
    sp = nodes["synth_ppa"]["inputs"]
    if seed is not None:
        seed_name, seed_rtl = seed_text(seed, fpnew_point)
    elif (chialu_root() / "targets" / "seeds" / f"{run_file.stem}.baseline.sv").is_file():
        # the generic rows' seed file (chiALU targets/make_plain_seeds.py): the baseline with its declaration
        # and every library annotation stripped, so the plain loop and the generic backends start from one text
        seed_name = "baseline"
        seed_rtl = plain_rtl((chialu_root() / "targets" / "seeds" / f"{run_file.stem}.baseline.sv").read_text())
    else:
        # the baseline program as the generator renders it; an ALU run file seeds its search from the numeric
        # stage's front instead, which the plain loop does not share
        from adir.seeds import _seed_texts, program_from_seed_text
        res = inst.template.seed_generator(inst.ctx(), "baseline")
        texts, vars_, lines = _seed_texts(inst.seed_artifacts()[0], res, "baseline")
        seed_name, seed_rtl = "baseline", plain_rtl(program_from_seed_text(inst, texts, vars_, lines))
    info = inst.elaboration.info or {}
    checker_rtl, fault_rows = None, []
    if "fault" in nodes:
        from chialu import eda
        from adir.registry import underlying
        files = dict(inst.artifacts["verify_bundle"].texts)
        cg = underlying(eda.checker_gen)(files, None)
        if not cg.get("ok"):
            raise SystemExit(f"{run_file}: checker_gen: {cg.get('detail')}")
        checker_rtl = cg["rtl_text"]
        for c in inst.raw.get("constraints") or []:
            if isinstance(c, dict) and str(c.get("metric", "")).startswith("fault."):
                op = next(k for k in ("eq", "le", "ge", "lt", "gt") if k in c)
                fault_rows.append((str(c["metric"]).split(".", 1)[1], op, c[op], bool(c.get("hard", True))))
    return Target(
        inst=inst, run_file=run_file, top=str(sp["top"]), pdk=str(sp.get("pdk") or "nangate45"),
        clock_ps=int(clock_ps or inst.bindings["clock_ps"].value), effort=str(sp.get("effort") or "medium"),
        synth_timeout_s=int(sp.get("timeout_s") or 1200), synth_repeats=int(sp.get("repeats", 5)),
        verify_files=dict(inst.artifacts["verify_bundle"].texts), seed_name=seed_name, seed_rtl=seed_rtl,
        cells_screen=_cells_screen(nodes), spec=dict(info.get("spec") or {}),
        fixed={k: b.value for k, b in inst.bindings.items() if b.time == "fixed"},
        runtime={k: list(b.members) for k, b in inst.bindings.items() if b.time == "runtime"},
        clock_bound=any(str(c.get("metric")) == "synth_ppa.abc_delay_ps" and "le" in c
                        for c in (inst.raw.get("constraints") or []) if isinstance(c, dict)),
        checker_rtl=checker_rtl, fault_rows=fault_rows)


# --------------------------------------------------------------- the evaluator

class Evaluator:
    """The run file's evaluator nodes as plain functions, in the run
    file's gating: lint, conformance and yosys_stat run on every
    candidate (none carries a `when`); synth_ppa runs when conformance
    passes and the gate count stays within `cells_screen` times the
    seed's, which is the screen the run file states."""

    def __init__(self, t: Target, stages: tuple, synth_infeasible: bool = False):
        from adir.registry import underlying
        from chialu import eda
        self.t = t
        self.stages = stages
        self.synth_infeasible = synth_infeasible
        self.seed_cells: Optional[int] = None
        self.lint = underlying(eda.lint)
        self.conformance = underlying(eda.conformance)
        self.stat = underlying(eda.yosys_stat)
        self.fault = underlying(eda.fault)
        self.synth = underlying(eda.synth_ppa)

    def run(self, rtl: str) -> tuple:
        """(measurements by node, skipped by node, screen distance, seconds)."""
        from adir.metrics import _signed_slack
        t = self.t
        m, sk, screen = {}, {}, None
        t0 = time.time()
        if "lint" in self.stages:
            m["lint"] = self.lint(rtl)
        else:
            sk["lint"] = "stage off"
        if "conformance" in self.stages:
            m["conformance"] = self.conformance(rtl, t.verify_files)
        else:
            sk["conformance"] = "stage off"
        if t.checker_rtl is not None:
            if "fault" in self.stages:
                m["fault"] = self.fault(rtl, t.verify_files, t.checker_rtl)
            else:
                sk["fault"] = "stage off"
        if "stat" in self.stages:
            m["yosys_stat"] = self.stat(rtl, t.top)
        else:
            sk["yosys_stat"] = "stage off"
        passed = "conformance" in m and bool(m["conformance"].get("pass"))
        cells = (m.get("yosys_stat") or {}).get("cells")
        limit = self.seed_cells * t.cells_screen if self.seed_cells else None
        if "synth" not in self.stages:
            sk["synth_ppa"] = "stage off"
        elif not passed and not self.synth_infeasible:
            sk["synth_ppa"] = "when conformance.pass is False"
        elif limit is not None and cells is not None and cells > limit:
            sk["synth_ppa"] = f"when yosys_stat.cells le {t.cells_screen} * seed.yosys_stat.cells is False ({cells} > {limit:.0f})"
            screen = -(_signed_slack("le", cells, limit) or 0.0)
        else:
            m["synth_ppa"] = self.synth(rtl, t.top, t.pdk, t.clock_ps, timeout_s=t.synth_timeout_s, effort=t.effort, repeats=t.synth_repeats)
        return m, sk, screen, round(time.time() - t0, 3)


# ----------------------------------------------------------------- the record

def _row(text: str, hard: bool, op: str, lhs, rhs) -> dict:
    """One constraint result in ADIR's shape (adir.metrics.Constraint.evaluate)."""
    from adir.metrics import _signed_slack
    if lhs is None or rhs is None:
        return {"status": "undecided", "slack": None, "lhs": None, "rhs": None, "text": text, "hard": hard,
                "satisfies": None}
    a = int(lhs) if isinstance(lhs, bool) else lhs
    b = int(rhs) if isinstance(rhs, bool) else rhs
    ok = {"le": a <= b, "ge": a >= b, "eq": a == b}[op]
    return {"status": "satisfied" if ok else "violated", "slack": _signed_slack(op, a, b), "lhs": lhs, "rhs": rhs,
            "text": text, "hard": hard, "satisfies": None}


def _num(node: dict, key: str):
    v = (node or {}).get(key)
    return v if isinstance(v, (int, float)) and not isinstance(v, bool) else None


def build_record(t: Target, out: Path, cid: str, parent_id: Optional[str], rtl: str, m: dict, sk: dict,
                 screen: Optional[float], seconds: float, seed_goal: list, *, call: int, is_seed: bool,
                 status: str, meta: dict) -> dict:
    """The archive record of one candidate, field for field the record
    `adir.evaluate.evaluate_candidate` writes, with the plain loop's
    fields beside them: `call`, `status`, `session_id` and the model
    cost under `cost`."""
    from adir.errors import UNDECIDED
    from adir.expr import to_json
    from adir.metrics import combined_score, feasibility
    goal = t.inst.goal
    lint_ok = m["lint"].get("ok") if "lint" in m else None
    conf = m["conformance"].get("pass") if "conformance" in m else None
    synth = m.get("synth_ppa") or {}
    area = _num(synth, "area_um2") if synth.get("ok") else None
    delay = _num(synth, "abc_delay_ps") if synth.get("ok") else None
    rows = [_row("lint.ok == true", True, "eq", lint_ok, True if lint_ok is not None else None),
            _row("conformance.pass == true", True, "eq", conf, True if conf is not None else None)]
    fault = m.get("fault")
    for field_, op, bound, hard in t.fault_rows:
        v = fault.get(field_) if isinstance(fault, dict) else None
        rows.append(_row(f"fault.{field_} {'==' if op == 'eq' else '<=' if op == 'le' else op} {str(bound).lower()}",
                         hard, op, v, bound if v is not None else None))
    if t.clock_bound:
        rows.append(_row("synth_ppa.abc_delay_ps <= vars.clock_ps", False, "le", delay, t.clock_ps if delay is not None else None))
    if status == "no_program":
        rows.insert(0, {"text": "program", "hard": True, "status": "violated", "detail": "no program was written",
                        "slack": None, "satisfies": None})
    feas = feasibility(rows)
    values = [area if area is not None else UNDECIDED, delay if delay is not None else UNDECIDED]
    seed_values = [v if v is not None else UNDECIDED for v in (seed_goal or values)]
    score = combined_score(goal, values, seed_values, feas, screen)
    level = goal.highest_level(values)
    feedback = {}
    for key in FEEDBACK_KEYS:
        node, field_ = key.split(".", 1)
        v = (m.get(node) or {}).get(field_)
        if v not in (None, ""):
            feedback[key] = v
    stderr = None
    for n in ("lint", "conformance", "fault", "yosys_stat", "synth_ppa"):
        o = m.get(n)
        if isinstance(o, dict) and (o.get("ok") is False or o.get("pass") is False) and o.get("detail"):
            stderr = str(o["detail"])
            break
    if status == "no_program":
        stderr = meta.get("stderr") or "no program was written"
    h = t.inst.hashes
    src = out / "programs" / (cid.replace(":", "_") + ".sv")
    return {
        "run": out.name, "iteration": None if is_seed else call, "call": call, "candidate_id": cid,
        "parent_id": parent_id, "seed_name": t.seed_name if is_seed else None, "is_seed": is_seed,
        "unit_id": h.get("unit_id"), "space_hash": h.get("space_hash"), "evaluator_hash": h.get("evaluator_hash"),
        "search_hash": meta.get("search_hash"),
        "model": None if is_seed else meta.get("model"), "operator": None if is_seed else "plain_loop",
        "prompt_config": None if is_seed else meta.get("prompt_config"), "tactic_id": None, "instruction_id": None,
        "declarations": {"vars": {}, "lines": [], "verified": None},
        "constraints": rows, "measurements": {n: {"value": to_json(v), "node_hash": None} for n, v in m.items()},
        "skipped": sk, "hard_fail": feas["hard_fail"], "feasible": feas["feasible"],
        "goal_values": [area, delay], "fidelity_level": level, "touched": [], "sub": [],
        "score": {"combined_score": score, "rule": goal.score_rule},
        "source_sha256": hashlib.sha256(rtl.encode()).hexdigest(), "source_path": str(src),
        "cost": {"seconds": seconds, "node_calls": len(m), "cache_hits": 0,
                 "synth_seconds": _num(synth, "seconds") or 0.0, **(meta.get("cost") or {})},
        "feedback": feedback, "stderr": stderr, "decision": "pending",
        "status": status, "session_id": meta.get("session_id"),
    }


def describe(rec: dict, t: Target) -> str:
    """One paragraph on a record for the prompt: the verdict and the numbers, or the failing gate's detail."""
    stalled = rec.get("status") == "stalled"
    if not rec["measurements"]:
        if stalled:
            return "the call stalled at the time limit and produced no program"
        return "the call ended without writing a program"
    prefix = "the call stalled at the time limit; the program it left is " if stalled else ""
    m = {n: v["value"] for n, v in rec["measurements"].items()}
    lint, conf, stat, synth = m.get("lint"), m.get("conformance"), m.get("yosys_stat"), m.get("synth_ppa")
    parts = []
    if lint is not None and not lint.get("ok"):
        parts.append("lint failed: " + str(lint.get("detail") or "")[-1500:].strip())
    if conf is not None and not conf.get("pass"):
        parts.append("conformance failed: " + str(conf.get("detail") or "")[:2500].strip())
    fault = m.get("fault")
    bad = [r["text"] for r in rec.get("constraints", []) if r["text"].startswith("fault.") and r.get("status") == "violated"]
    if fault is not None and bad:
        parts.append("fault gate failed (" + "; ".join(bad) + "): " + str(fault.get("detail") or "")[:1500].strip())
    if stat is not None and stat.get("cells") is not None:
        parts.append(f"{stat['cells']} gates before mapping")
    if "synth_ppa" in rec.get("skipped", {}) and not parts:
        parts.append("not synthesized: " + rec["skipped"]["synth_ppa"])
    elif "synth_ppa" in rec.get("skipped", {}) and stat is not None and "seed.yosys_stat" in rec["skipped"]["synth_ppa"]:
        parts.append("not synthesized: " + rec["skipped"]["synth_ppa"])
    if synth is not None:
        if synth.get("ok"):
            over = "" if not t.clock_bound or synth["abc_delay_ps"] <= t.clock_ps else f", above the {t.clock_ps} ps clock target: infeasible"
            parts.append(f"area {synth['area_um2']:.1f} um2, delay {synth['abc_delay_ps']:.1f} ps{over}, {synth['cells']} cells")
        else:
            parts.append("synthesis failed: " + str(synth.get("detail") or "")[-1500:].strip())
    verdict = "feasible" if rec["feasible"] else "infeasible"
    return prefix + (f"{verdict}; " + "; ".join(parts) if parts else verdict)


# ------------------------------------------------------------------ the agent

@dataclass
class AgentResult:
    status: str                       # ok | stalled | failed
    reply: str = ""
    transcript: str = ""
    usage: dict = field(default_factory=dict)
    session_id: Optional[str] = None
    stderr: str = ""
    returncode: Optional[int] = None
    wall_s: float = 0.0
    recovered: bool = False           # the reply, usage and transcript come from the session store, not the CLI's return
    attempts: list = field(default_factory=list)   # the CHIA node's attempts of this call (session id, usage, error each)


def recover_opencode_session(node, work_dir: Path, since_s: float) -> Optional[dict]:
    """The session opencode kept for a call whose CLI did not return (a
    stalled attempt, which the CHIA node reports without a session id):
    `opencode session list` names the session by the call directory,
    `opencode export` gives its messages, and the node's own parser
    gives the reply so far, the token counts and the transcript, so a
    stalled call's cost enters the record.

    Both commands run in the call's directory: `session list` lists the
    sessions of the project of its working directory, and the call's
    sessions belong to the directory's project (it is outside every git
    repository), not to the repository this loop runs from. Their output
    goes to a file, since opencode cuts a piped stdout at 64 KiB."""
    import subprocess
    import tempfile
    binary = getattr(node, "opencode_bin", "opencode")
    env = dict(os.environ)
    wd = str(Path(work_dir).resolve())

    def _out(cmd: list, timeout: int) -> str:
        fd, path = tempfile.mkstemp(suffix=".json", prefix="plain_loop_opencode_")
        try:
            with os.fdopen(fd, "w") as fh:
                subprocess.run(cmd, stdout=fh, stderr=subprocess.DEVNULL, timeout=timeout, env=env,
                               stdin=subprocess.DEVNULL, cwd=wd)
            return Path(path).read_text()
        finally:
            try:
                os.unlink(path)
            except OSError:
                pass

    try:
        sessions = json.loads(_out([binary, "session", "list", "--format", "json", "-n", "1000"], 120) or "[]")
    except Exception:  # noqa: BLE001
        return None
    found = [x for x in sessions if isinstance(x, dict) and x.get("directory") == wd
             and (x.get("created") or 0) >= (since_s - 120) * 1000]
    if not found:
        return None
    sid = max(found, key=lambda x: x.get("created") or 0)["id"]
    try:
        export = json.loads(_out([binary, "export", sid], 300) or "{}")
    except Exception:  # noqa: BLE001
        return None
    try:
        text, meta, stream, err = node._extract_from_export(export)
    except Exception:  # noqa: BLE001
        return None
    return {"session_id": sid, "reply": text or "", "usage": dict(meta or {}), "transcript": stream or "",
            "error": err}


def _tool_output_denied(cfg: dict) -> dict:
    """*cfg* with opencode's shared tool-output directory denied to the agent. opencode appends
    `external_directory: {<data>/opencode/tool-output/*: allow}` after the config's rules (the last
    matching rule wins) unless the config denies exactly that glob, and every run's truncated tool
    outputs land there; CHIA's node applies the same rule (chia.models.opencode.deny_tool_output)."""
    try:
        from chia.models.opencode import deny_tool_output
        return deny_tool_output(cfg)
    except ImportError:   # a CHIA without it: the same rules, spelled here
        cfg = dict(cfg)
        data = os.environ.get("XDG_DATA_HOME") or os.path.join(os.environ.get("HOME") or os.path.expanduser("~"),
                                                                ".local", "share")
        glob = os.path.join(os.path.normpath(os.path.join(data, "opencode", "tool-output")), "*")
        for key, pats in (("external_directory", [glob]), ("read", ["*opencode/tool-output", "*opencode/tool-output/*"])):
            v = cfg.get(key)
            rules = dict(v) if isinstance(v, dict) else ({"*": v} if isinstance(v, str) else {})
            for p in pats:
                rules.pop(p, None)
                rules[p] = "deny"
            cfg[key] = rules
        return cfg


def _allow_writes(node, agent: str):
    """The one departure from the flow's permission set: the agent may
    edit files inside the call directory, since it writes the candidate
    there. The shell, the web and every path outside stay denied."""
    if agent == "opencode":
        cfg = dict(getattr(node, "config", None) or {})
        cfg["edit"] = "allow"                        # inside the call directory: every outside path stays denied
        for k in ("bash", "webfetch", "task"):       # never commands, the web or subagents
            cfg[k] = "deny"
        # never outside paths: ADIR's block (adir.backends.skydiscover.opencode_permissions) gives them as
        # {"*": deny, <tool-output glob>: deny}, whose last rule keeps opencode from appending its own allow of
        # the tool-output directory; the catch-all is forced to deny and the tool-output rules are kept last
        ext = cfg.get("external_directory")
        cfg["external_directory"] = {"*": "deny", **{k: v for k, v in ext.items() if k != "*" and v == "deny"}} \
            if isinstance(ext, dict) else "deny"
        node.config = _tool_output_denied(cfg)      # nor opencode's tool-output directory, which every run shares
    elif agent == "claude":
        args = list(getattr(node, "extra_cli_args", []) or [])
        for i, a in enumerate(args):
            if a == "--disallowedTools" and i + 1 < len(args):
                keep = [x for x in args[i + 1].split(",") if x not in ("Edit", "Write", "MultiEdit")]
                args[i + 1] = ",".join(keep)
        node.extra_cli_args = args
    elif agent == "codex":
        node.sandbox = "workspace-write"


_BILLING_SIGNS = ("billingerror", "billing_error", "insufficient balance", "insufficient_balance", "insufficient credit",
                  "available credits", "payment required", "credit balance is too low")
_HTTP_402 = re.compile(r"(?:status(?:code)?|http|code|error)[^0-9a-z]{0,4}402(?![0-9.])")


def is_billing(text: str) -> bool:
    """A provider's out-of-credit refusal, in a failed call's stderr or error: CHIA's BillingError,
    DeepSeek's HTTP 402 'Insufficient Balance', openrouter's 'exceed your available credits' (and
    whatever ADIR's own check knows). Every later call would fail at once, so the loop stops."""
    t = (text or "").lower()
    if any(s in t for s in _BILLING_SIGNS) or _HTTP_402.search(t):
        return True
    try:
        from adir.backends.skydiscover import is_billing_error
        return bool(is_billing_error(text or ""))
    except ImportError:
        return False


class Agent:
    """The flow's model client: `AgentLLM` of adir.backends.skydiscover
    builds the CHIA agent node with the run file's spec (agent, provider,
    model, effort, timeout), which is the construction chiALU's solution
    calls use; `retries` is 1 so that one invocation is one attempt and a
    stalled attempt counts against the budget as the protocol states."""

    def __init__(self, agent: str, provider: str, model: str, effort: str, timeout_s: int,
                 max_output_tokens: Optional[int] = None):
        from adir.backends.skydiscover import AgentLLM
        self.agent = agent
        self.spec = {"agent": agent, "model": model, "timeout_s": int(timeout_s), "retries": 1}
        if effort:
            self.spec["effort"] = effort
        if agent == "opencode" and provider:
            self.spec["provider"] = provider
        if max_output_tokens:
            self.spec["max_output_tokens"] = int(max_output_tokens)   # opencode's output cap, as the solution role's
        self.llm = AgentLLM(self.spec, None, None)
        self.llm._cls()                      # raises RuntimeError without CHIA's agent nodes
        self.timeout_s = int(timeout_s)

    def call(self, system: str, user: str, work_dir: Path) -> AgentResult:
        """One call. The agent works in a copy of `work_dir` outside every git repository
        (adir.confine: opencode confines its file tools to the git worktree, not to the directory),
        and what it leaves there is copied back to `work_dir`."""
        from adir.confine import git_root, run_agent_root
        work_dir = Path(work_dir)
        if git_root(work_dir) is None:
            return self._call(system, user, work_dir)
        ws = run_agent_root(work_dir.parent, "calls") / work_dir.name
        if ws.exists():
            shutil.rmtree(ws)
        shutil.copytree(work_dir, ws)
        try:
            return self._call(system, user, ws)
        finally:
            shutil.copytree(ws, work_dir, dirs_exist_ok=True)

    def _call(self, system: str, user: str, work_dir: Path) -> AgentResult:
        from adir.backends.skydiscover import set_opencode_env
        node = self.llm._make(system, str(work_dir))
        _allow_writes(node, self.agent)
        if self.agent == "opencode":
            set_opencode_env(self.spec)
        t0 = time.time()
        try:
            res = node.prompt(user)
        except Exception as e:  # noqa: BLE001 - a typed CLI error (auth, rate limit, ...) is a failed call
            wall = time.time() - t0
            status = "stalled" if wall >= 0.95 * self.timeout_s else "failed"
            # CHIA's typed errors carry the call's attempts (session id, usage each) and their summed usage
            attempts = list(getattr(e, "attempts", None) or [])
            sids = [a.get("session_id") for a in attempts if isinstance(a, dict) and a.get("session_id")]
            out = AgentResult(status=status, stderr=f"{type(e).__name__}: {str(e)[:2000]}", wall_s=round(wall, 1),
                              usage=dict(getattr(e, "usage", None) or {}), attempts=attempts,
                              session_id=sids[-1] if sids else None)
            return self._recover(node, out, work_dir, t0)
        wall = time.time() - t0
        usage = getattr(res, "usage", None)
        if not isinstance(usage, dict):
            usage = {k: getattr(res, k, None) for k in ("input_tokens", "output_tokens", "cost_usd")}
            usage = {k: v for k, v in usage.items() if v}
        ok = bool(getattr(res, "success", False))
        status = "ok" if ok else ("stalled" if wall >= 0.95 * self.timeout_s else "failed")
        out = AgentResult(status=status, reply=str(getattr(res, "result", "") or ""),
                          transcript=str(getattr(res, "stream_result", "") or ""), usage=usage,
                          session_id=getattr(res, "session_id", None), stderr=str(getattr(res, "stderr", "") or ""),
                          returncode=getattr(res, "returncode", None), wall_s=round(wall, 1),
                          attempts=list(getattr(res, "attempts", None) or []))
        return self._recover(node, out, work_dir, t0)

    def _recover(self, node, out: AgentResult, work_dir: Path, t0: float) -> AgentResult:
        """A call without a session id (the CLI timed out or failed before its export) takes its reply so far,
        its usage and its transcript from opencode's session store."""
        if self.agent != "opencode" or out.session_id:
            return out
        rec = recover_opencode_session(node, work_dir, t0)
        if rec is None:
            return out
        out.session_id = rec["session_id"]
        out.usage = rec["usage"] or out.usage
        out.transcript = rec["transcript"] or out.transcript
        if not out.reply:
            out.reply = rec["reply"]
        if rec.get("error") and not out.stderr:
            out.stderr = json.dumps(rec["error"])[:2000]
        out.recovered = True
        return out


# ----------------------------------------------------------------- the prompt

def _words(items: list) -> str:
    items = [str(i) for i in items]
    if len(items) <= 1:
        return "".join(items)
    return ", ".join(items[:-1]) + " and " + items[-1]


def unit_text(t: Target) -> str:
    """The unit as the run file binds it: the modes, the ops, the rounding
    modes and the flags, from the elaboration's spec; the behavior itself
    is defined by the conformance vectors."""
    spec = t.spec
    lines = [f"The module `{t.top}` is a combinational unit; its interface is the port list in the file."]
    modes = spec.get("modes") or []
    if modes:
        ms = [f"{m.get('count', 1)} x `{m.get('format')}`" + (" lanes" if int(m.get("count", 1)) > 1 else "")
              for m in modes if isinstance(m, dict)]
        lines.append(f"Modes, selected per instruction by the `mode` port: {_words(ms)}.")
    ops = spec.get("ops") or t.runtime.get("ops") or []
    if ops:
        lines.append(f"Ops, selected by the `op` port: {_words([f'`{o}`' for o in ops])}.")
    rnd = t.runtime.get("rounding") or ([t.fixed["rounding"]] if t.fixed.get("rounding") else [])
    if rnd:
        lines.append(f"Rounding modes{' selected at run time' if len(rnd) > 1 else ''}: {_words([f'`{r}`' for r in rnd])}.")
    flags = t.fixed.get("flags") or spec.get("flags") or []
    if flags:
        lines.append(f"The `flags` output carries {_words([f'`{f}`' for f in flags])} in that order per lane and is checked bit-exact.")
    n_random = t.fixed.get("verify.n_random")
    lines.append("The exact behavior is defined by the reference vectors of the conformance testbench"
                 + (f" ({n_random} random vectors per case plus the corner cases of every format)" if n_random else "")
                 + ": every result bit and every flag bit must match.")
    return " ".join(lines)


def write_feedback(d: Path, rec: dict, sub: str = "") -> list:
    """The record's feedback texts as files under <call>/feedback[/<sub>]/, as the flow's feedback_depth: files."""
    fb = rec.get("feedback") or {}
    if not fb:
        return []
    fdir = d / "feedback" / sub if sub else d / "feedback"
    fdir.mkdir(parents=True, exist_ok=True)
    out = []
    for key, text in fb.items():
        f = fdir / (re.sub(r"[^\w.-]+", "_", key) + ".txt")
        f.write_text(str(text))
        rel = f.relative_to(d)
        n = str(text).count("\n") + 1
        out.append(f"* `{rel}` ({n} line{'s' if n != 1 else ''}): {key}")
    return out


def user_text(t: Target, k: int, calls: int, parent: dict, best: dict, last: Optional[dict], front: list,
              seed: dict, d: Path, evaluator_cmd: str) -> str:
    rtl = (d / PARENT_FILE).read_text()
    n_lines = rtl.count("\n") + 1
    fb_parent = write_feedback(d, parent)
    fb_last = write_feedback(d, last, "last") if last is not None and last is not parent else []
    who = "the seed" if parent.get("is_seed") else f"candidate `{parent['candidate_id']}` of call {parent.get('call')}"
    L = [
        "# Task",
        (f"Improve the unit `{t.top}` in `{CANDIDATE_FILE}`: reduce its cell area and its critical-path delay at the "
         f"{t.clock_ps} ps clock target on {t.pdk} (yosys and ABC, {t.effort} effort). " if t.clock_bound else
         f"Improve the unit `{t.top}` in `{CANDIDATE_FILE}`: reduce its cell area and its critical-path delay on "
         f"{t.pdk} (yosys and ABC, {t.effort} effort), where every candidate is mapped for its least delay. ")
        + "Keep the module name, every port (name, width, direction) and the exact behavior. A candidate that changes "
        "any result or flag bit fails conformance and is infeasible"
        + ("; a delay above the clock target is infeasible. " if t.clock_bound else ". ")
        + "Both area and delay count: the goal is the front of (area, delay) over the feasible candidates.",
        "",
        "# The unit",
        unit_text(t),
        "",
        "# Files in this directory",
        f"* `{PARENT_FILE}` ({len(rtl) / 1024:.1f} KB, {n_lines} lines): the current program, {who}, unchanged, for reference",
        f"* `{CANDIDATE_FILE}`: a copy of `{PARENT_FILE}`. Edit this file in place; it is the program the evaluator reads after your reply.",
    ]
    L += fb_parent
    if fb_last:
        L.append("* `feedback/last/`: the evaluator's texts for the last candidate")
        L += ["  " + x for x in fb_last]
    L += [
        "",
        "# Evaluator",
        f"After your reply the loop runs `{evaluator_cmd}` on `{CANDIDATE_FILE}`, which is chiALU's evaluator: "
        "(1) yosys lint through read_slang with a hierarchy check, no latch and no driver conflict; "
        "(2) Verilator conformance against the reference vectors, bit-exact, flags included; "
        + ("(2b) the fault campaign of the residue checker the harness attaches to your core's result: "
           + ", ".join(f"{f} {'=' if op == 'eq' else '<=' if op == 'le' else op} {str(b).lower()}" for f, op, b, _h in t.fault_rows)
           + ", a hard gate like conformance; " if t.checker_rtl is not None else "")
        + "(3) a yosys gate count; "
        + (f"(4) yosys and ABC mapping on {t.pdk} at {t.clock_ps} ps, {t.effort} effort, which reports area_um2, " if t.clock_bound else
         f"(4) yosys and ABC mapping on {t.pdk} for the least delay (a {t.clock_ps} ps target no design reaches), {t.effort} effort, which reports area_um2, ")
        + 
        "abc_delay_ps and cells. A candidate that fails lint or conformance is not synthesized; a candidate whose gate "
        f"count exceeds {t.cells_screen:g} times the seed's is not synthesized.",
        "",
        "# Results so far",
        f"* seed: {describe(seed, t)}",
    ]
    if best is not seed:
        L.append(f"* best so far (candidate `{best['candidate_id']}`, call {best.get('call')}): {describe(best, t)}")
    else:
        L.append("* best so far: the seed")
    if last is not None and last is not seed:
        L.append(f"* last candidate (call {last.get('call')}): {describe(last, t)}")
    if front:
        pts = ", ".join(f"({r['goal_values'][0]:.1f} um2, {r['goal_values'][1]:.1f} ps)" for r in front)
        L.append(f"* feasible front (area, delay): {pts}")
    cp = (parent.get("feedback") or {}).get("synth_ppa.critical_path")
    if cp:
        L.append(f"* critical path of the current program: {str(cp).strip()}")
    L += [
        "",
        "# Reply",
        f"Edit `{CANDIDATE_FILE}` so that it holds the complete new program (every module the unit needs, the interface "
        f"unchanged). Then reply with a short summary of what you changed and why. This is call {k}.",
    ]
    return "\n".join(L) + "\n"


_FENCE = re.compile(r"```[ \t]*(?:systemverilog|verilog|sv)?[ \t]*\n(.*?)```", re.S | re.I)


def fenced_program(reply: str, top: str) -> Optional[str]:
    """The largest fenced block of the reply that holds the top module: the fallback where the agent
    answered with the program instead of writing the file."""
    best = None
    for m in _FENCE.finditer(reply or ""):
        body = m.group(1)
        if re.search(rf"^\s*module\s+{re.escape(top)}\b", body, re.M) and "endmodule" in body:
            if best is None or len(body) > len(best):
                best = body
    return best


# ------------------------------------------------------------------- the loop

def _count(out: Path, updates: dict):
    """summary.json counters in ADIR's names (adir.backends.skydiscover._count) plus the loop's fields."""
    f = out / "summary.json"
    try:
        d = json.loads(f.read_text()) if f.is_file() else {}
    except ValueError:
        d = {}
    for k, v in updates.items():
        if isinstance(v, (int, float)) and not isinstance(v, bool) and k.startswith(("llm_", "input_tokens", "output_tokens",
                                                                                      "reasoning_tokens", "cost_microusd",
                                                                                      "synth_seconds", "eval_seconds",
                                                                                      "agent_seconds")):
            d[k] = (d.get(k) or 0) + v
        else:
            d[k] = v
    f.write_text(json.dumps(d, indent=1, default=str))


def summarize(out: Path, archive, goal, t: Target, calls_done: int, t_start: float):
    recs = archive.records()
    cands = [r for r in recs if not r.get("is_seed")]
    feas = [r for r in cands if r.get("feasible")]
    front = archive.front(goal)
    best = pick_best(recs)
    upd = {
        "synthesis_records": {"path": str(out / "results_db.jsonl"),
                              "lookup": "candidate_id; measurements.synth_ppa.value"},
        "synth_repeats": t.synth_repeats,
        "calls": calls_done, "candidates": len(cands), "feasible": len(feas),
        "feasible_fraction": (len(feas) / len(cands)) if cands else None,
        "stalled": sum(1 for r in cands if r.get("status") == "stalled"),
        "failed": sum(1 for r in cands if r.get("status") == "failed"),
        "no_program": sum(1 for r in cands if r.get("status") == "no_program"),
        "best_area_um2": min((r["goal_values"][0] for r in feas), default=None),
        "min_delay_ps": min((r["goal_values"][1] for r in feas), default=None),
        "best": {"candidate_id": best["candidate_id"], "call": best.get("call"), "area_um2": best["goal_values"][0],
                 "abc_delay_ps": best["goal_values"][1], "score": best["score"]["combined_score"],
                 "feasible": best["feasible"]} if best else None,
        "front": [{"candidate_id": r["candidate_id"], "call": r.get("call"), "area_um2": r["goal_values"][0],
                   "abc_delay_ps": r["goal_values"][1]} for r in front],
        "seed": next(({"candidate_id": r["candidate_id"], "feasible": r["feasible"], "area_um2": r["goal_values"][0],
                       "abc_delay_ps": r["goal_values"][1]} for r in recs if r.get("is_seed")), None),
        "wall_seconds": round(time.time() - t_start, 1),
    }
    _count(out, upd)


def pick_best(recs: list) -> Optional[dict]:
    """The parent of the next call: the feasible record with the highest
    score (the later one on a tie), else the seed."""
    feas = [r for r in recs if r.get("feasible")]
    if feas:
        return max(feas, key=lambda r: (r["score"]["combined_score"], r.get("call") or 0))
    return next((r for r in recs if r.get("is_seed")), None)


def evaluate_program(ev: Evaluator, t: Target, out: Path, archive, rtl: str, *, cid: str, parent_id: Optional[str],
                     seed_goal: list, call: int, is_seed: bool, status: str, meta: dict) -> dict:
    m, sk, screen, seconds = ev.run(rtl) if status not in ("no_program",) else ({}, {}, None, 0.0)
    rec = build_record(t, out, cid, parent_id, rtl, m, sk, screen, seconds, seed_goal, call=call, is_seed=is_seed,
                       status=status, meta=meta)
    (out / "programs").mkdir(exist_ok=True)
    Path(rec["source_path"]).write_text(rtl)
    archive.append(rec)
    return rec


def run_loop(a) -> int:
    from adir.archive import Archive
    out = Path(a.out).resolve()
    if (out / "results_db.jsonl").is_file() and not a.resume:
        # a second run into the same directory would append to the first's archive: one run per directory,
        # a repetition in a directory of its own, and --resume to continue one
        raise SystemExit(f"{out} already holds a run (results_db.jsonl); use --resume to continue it or another --out")
    out.mkdir(parents=True, exist_ok=True)
    t_start = time.time()
    run_file = find_run_file(a.run_file)
    stages = tuple(s.strip() for s in a.stages.split(",") if s.strip())
    bad = [s for s in stages if s not in STAGES]
    if bad:
        raise SystemExit(f"--stages: unknown {bad}; one or more of {','.join(STAGES)}")
    log(f"loading {run_file}", out)
    t = load_target(run_file, out / "adir_scratch", Path(a.seed) if a.seed else None, a.fpnew_point, a.clock_ps)
    search_hash = hashlib.sha256(json.dumps({"agent": a.agent, "provider": a.provider, "model": a.model, "effort": a.effort,
                                             "timeout_s": a.timeout_s, "stages": stages,   # not --calls: extending a run keeps its hash
                                             "synth_report": not a.no_synth_report}, sort_keys=True).encode()).hexdigest()
    evaluator_cmd = f"python3 harness/plain_loop.py {a.run_file} --evaluate {CANDIDATE_FILE}"
    (out / "target.json").write_text(json.dumps({
        "run_file": str(run_file), "top": t.top, "pdk": t.pdk, "clock_ps": t.clock_ps, "effort": t.effort,
        "synth_timeout_s": t.synth_timeout_s, "cells_screen": t.cells_screen, "seed": t.seed_name,
        "seed_sha256": hashlib.sha256(t.seed_rtl.encode()).hexdigest(), "stages": stages,
        "agent": {"agent": a.agent, "provider": a.provider, "model": a.model, "effort": a.effort,
                  "timeout_s": a.timeout_s}, "calls": a.calls, "search_hash": search_hash,
        "synth_report": not a.no_synth_report, "synth_infeasible": a.synth_infeasible,
        "hashes": {k: t.inst.hashes.get(k) for k in ("unit_id", "space_hash", "evaluator_hash")},
        "verify_files": {k: hashlib.sha256(v.encode()).hexdigest() for k, v in t.verify_files.items()},
    }, indent=1))
    ev = Evaluator(t, stages, a.synth_infeasible)
    archive = Archive("jsonl", out / "results_db.jsonl")
    agent = None
    if a.agent != "none" and a.calls > 0:
        # the solution role's output cap in the run file (max_output_tokens), so the plain loop's calls
        # have the tokens the search's have
        role = ((t.inst.raw.get("search") or {}).get("models") or {}).get("solution") or {}
        agent = Agent(a.agent, a.provider, a.model, a.effort, a.timeout_s, role.get("max_output_tokens"))
    meta_common = {"search_hash": search_hash, "model": a.model,
                   "prompt_config": {"agent": a.agent, "provider": a.provider, "effort": a.effort, "loop": "plain"}}

    seed_dir = out / "seed"
    first, last = 1, None
    if a.resume and (seed_dir / "evaluation.json").is_file():
        # a resumed run: the seed and every completed call are read back (a call counts once its
        # evaluation.json exists); a call directory left without one is cut short and done again.
        # --calls is the run's total, so the same command finishes a stopped run and a larger one extends it
        seed_rec = json.loads((seed_dir / "evaluation.json").read_text())
        done = sorted(int(p.name.split("_")[1]) for p in out.glob("call_*") if (p / "evaluation.json").is_file())
        k_done = 0
        while k_done + 1 in done:
            k_done += 1
        for p in out.glob("call_*"):
            if int(p.name.split("_")[1]) > k_done:
                shutil.rmtree(p, ignore_errors=True)
        # a call stopped between its archive line and its evaluation.json is done again, so its line goes too
        db = out / "results_db.jsonl"
        lines = [l for l in db.read_text().splitlines() if l.strip()] if db.is_file() else []
        keep = [l for l in lines if json.loads(l).get("is_seed") or (json.loads(l).get("call") or 0) <= k_done]
        if len(keep) != len(lines):
            db.write_text("".join(l + "\n" for l in keep))
        if k_done:
            last = json.loads((out / f"call_{k_done}" / "evaluation.json").read_text())
        first = k_done + 1
        log(f"resuming: the seed and {k_done} calls read back; calls {first}..{a.calls} to go", out)
    else:
        # the seed: evaluated first, as ADIR's seeds stage does; it costs no model call
        log(f"evaluating the seed {t.seed_name} ({len(t.seed_rtl) / 1024:.0f} KB)", out)
        seed_dir.mkdir(exist_ok=True)
        (seed_dir / PARENT_FILE).write_text(t.seed_rtl)
        seed_rec = evaluate_program(ev, t, out, archive, t.seed_rtl, cid=f"seed:{t.seed_name}", parent_id=None, seed_goal=[],
                                    call=0, is_seed=True, status="ok", meta={"search_hash": search_hash})
        (seed_dir / "evaluation.json").write_text(json.dumps(seed_rec, indent=1, default=str))
        (seed_dir / "seed_values.json").write_text(json.dumps({"__goal__": seed_rec["goal_values"], **{
            n: v["value"] for n, v in seed_rec["measurements"].items()}}, default=str))
        log(f"seed: {describe(seed_rec, t)} ({seed_rec['cost']['seconds']} s)", out)
        _count(out, {"synth_seconds": seed_rec["cost"]["synth_seconds"], "eval_seconds": seed_rec["cost"]["seconds"]})
        if seed_rec["feasible"]:
            (out / "best.sv").write_text(t.seed_rtl)
        summarize(out, archive, t.inst.goal, t, 0, t_start)
    ev.seed_cells = ((seed_rec["measurements"].get("yosys_stat") or {}).get("value") or {}).get("cells")
    seed_goal = seed_rec["goal_values"]

    for k in range(first, a.calls + 1):
        if agent is None:
            break
        recs = archive.records()
        parent = pick_best(recs) or seed_rec
        d = out / f"call_{k}"
        d.mkdir(exist_ok=True)
        parent_rtl = Path(parent["source_path"]).read_text()
        (d / PARENT_FILE).write_text(parent_rtl)
        (d / CANDIDATE_FILE).write_text(parent_rtl)
        user = user_text(t, k, a.calls, parent, pick_best(recs) or seed_rec, last, archive.front(t.inst.goal),
                         seed_rec, d, evaluator_cmd)
        from adir.confine import with_submission_note
        system = with_submission_note(SYSTEM_TEXT)       # the sentence every method's solution prompt carries
        (d / "prompt.md").write_text(f"<!-- role solution; plain loop call {k} -->\n\n# System\n\n{system}\n\n# User\n\n{user}\n")
        log(f"call {k}/{a.calls}: {a.agent} {a.provider + '/' if a.provider else ''}{a.model} on {parent['candidate_id']}", out)
        res = agent.call(system, user, d)
        if res.status != "ok" and is_billing(res.stderr):
            # no credit: every later call would fail at once and still count; this call is not kept (no
            # evaluation.json, so --resume does it again once the account is topped up) and the loop stops
            shutil.rmtree(d, ignore_errors=True)
            log(f"call {k}: the provider refused for billing ({res.stderr[:200]}); stopping, resume later", out)
            (out / "stopped_by_billing").write_text(time.strftime("%Y-%m-%dT%H:%M:%S") + "\n")
            return 3
        with open(d / "prompt.md", "a") as f:
            f.write(f"\n\n# Reply\n\n{res.reply if res.status == 'ok' else f'({res.status}: {res.stderr[-800:]})'}\n")
        (d / "reply.md").write_text(res.reply)
        (d / "transcript.md").write_text(res.transcript)
        (d / "usage.json").write_text(json.dumps(res.usage, indent=1, default=str))
        cand = (d / CANDIDATE_FILE).read_text() if (d / CANDIDATE_FILE).is_file() else parent_rtl
        source = "file"
        if cand == parent_rtl:
            fb = fenced_program(res.reply, t.top)
            if fb:
                cand, source = fb, "reply"
                (d / CANDIDATE_FILE).write_text(cand)
        status = res.status if cand != parent_rtl else ("no_program" if res.status == "ok" else res.status)
        usage = res.usage or {}
        cost = {"llm_calls": 1, "llm_wall_s": res.wall_s, "stalled": res.status == "stalled",
                **{key: usage.get(key) for key in ("input_tokens", "output_tokens", "reasoning_tokens", "cache_read",
                                                    "cache_write", "cost_usd", "num_turns") if usage.get(key) is not None}}
        (d / "call.json").write_text(json.dumps({"call": k, "status": res.status, "program": source if cand != parent_rtl else None,
                                                 "wall_s": res.wall_s, "returncode": res.returncode, "recovered": res.recovered,
                                                 "session_id": res.session_id, "usage": usage, "stderr": res.stderr[-2000:],
                                                 "attempts": res.attempts,
                                                 "parent_id": parent["candidate_id"]}, indent=1, default=str))
        cid = uuid.uuid4().hex[:12]
        if cand != parent_rtl:
            log(f"call {k}: {res.status} in {res.wall_s} s, program from the {source}; evaluating {cid}", out)
            rec = evaluate_program(ev, t, out, archive, cand, cid=cid, parent_id=parent["candidate_id"], seed_goal=seed_goal,
                                   call=k, is_seed=False, status=status,
                                   meta={**meta_common, "cost": cost, "session_id": res.session_id})
        else:
            log(f"call {k}: {res.status} in {res.wall_s} s, no program", out)
            rec = evaluate_program(ev, t, out, archive, parent_rtl, cid=cid, parent_id=parent["candidate_id"],
                                   seed_goal=seed_goal, call=k, is_seed=False, status="no_program" if status == "ok" else status,
                                   meta={**meta_common, "cost": cost, "session_id": res.session_id, "stderr": res.stderr})
        (d / "evaluation.json").write_text(json.dumps(rec, indent=1, default=str))
        log(f"call {k}: {rec['candidate_id']} {describe(rec, t)} (eval {rec['cost']['seconds']} s, score {rec['score']['combined_score']:.4f})", out)
        _count(out, {"llm_calls": 1, "llm_calls.solution": 1, "llm_failures": 0 if res.status == "ok" else 1,
                     "input_tokens": int(usage.get("input_tokens") or 0), "output_tokens": int(usage.get("output_tokens") or 0),
                     "reasoning_tokens": int(usage.get("reasoning_tokens") or 0),
                     "cost_microusd": int(round(float(usage.get("cost_usd") or 0) * 1e6)),
                     "synth_seconds": rec["cost"]["synth_seconds"], "eval_seconds": rec["cost"]["seconds"],
                     "agent_seconds": res.wall_s})
        best = pick_best(archive.records())
        if best is not None and best.get("feasible"):
            (out / "best.sv").write_text(Path(best["source_path"]).read_text())
        summarize(out, archive, t.inst.goal, t, k, t_start)
        last = rec
    summarize(out, archive, t.inst.goal, t, min(a.calls, len([r for r in archive.records() if not r.get("is_seed")])), t_start)
    log(f"done: {json.dumps({k: v for k, v in json.loads((out / 'summary.json').read_text()).items() if k in ('calls', 'feasible', 'best_area_um2', 'min_delay_ps', 'stalled')})}", out)
    return 0


def run_evaluate(a) -> int:
    """`--evaluate FILE`: the evaluator alone on one program; the JSON result on stdout."""
    run_file = find_run_file(a.run_file)
    stages = tuple(s.strip() for s in a.stages.split(",") if s.strip())
    scratch = Path(a.out).resolve() / "adir_scratch" if a.out else Path(os.environ.get("TMPDIR", "/tmp")) / f"plain_loop_{uuid.uuid4().hex[:8]}"
    t = load_target(run_file, scratch, None, a.fpnew_point, a.clock_ps)
    rtl = plain_rtl(Path(a.evaluate).read_text())
    ev = Evaluator(t, stages, a.synth_infeasible)
    m, sk, screen, seconds = ev.run(rtl)
    rec = build_record(t, Path(a.out or "."), "eval", None, rtl, m, sk, screen, seconds, [], call=0, is_seed=False,
                       status="ok", meta={})
    print(json.dumps({"feasible": rec["feasible"], "goal_values": rec["goal_values"], "constraints": rec["constraints"],
                      "skipped": sk, "seconds": seconds, "verdict": describe(rec, t),
                      "measurements": {n: {kk: vv for kk, vv in v.items() if kk not in ("paths", "area_by_hierarchy", "summary")}
                                       for n, v in m.items()}}, indent=1, default=str))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run_file", help="the ADIR run file (targets/eval/fp_alu_cmp.yaml), as given or relative to the chiALU tree")
    ap.add_argument("--agent", default="opencode", choices=["opencode", "claude", "codex", "none"],
                    help="the agent CLI through its CHIA node; none evaluates the seed alone")
    # the evaluation's model (targets/make_targets.py: MODEL, PROVIDER, EFFORT), decided 2026-09-23
    ap.add_argument("--model", default="deepseek-flash")          # 2026-09-25: the DeepSeek platform, as every target
    ap.add_argument("--provider", default="deepseek", help="opencode's provider id (opencode only)")
    ap.add_argument("--effort", default="high", help="reasoning effort: opencode --variant, claude --effort, codex reasoning_effort")
    ap.add_argument("--calls", type=int, default=20,
                    help="the budget: one agent invocation per call (one candidate, one iteration), stalled ones included; "
                         "with --resume the run's total")
    ap.add_argument("--resume", action="store_true",
                    help="continue the run under --out from its last completed call to --calls in all")
    ap.add_argument("--out", default="", help="the run directory (results_db.jsonl, call_<k>/, best.sv, summary.json)")
    ap.add_argument("--seed", default="", help="a hand seed instead of the run file's baseline seed (baselines/fpnew/fpnew_alu_core.sv is joined with the CVFPU sources)")
    ap.add_argument("--fpnew-point", default="MERGED", choices=["MERGED", "PARALLEL"], help="the FPnew design point of a baselines/fpnew seed")
    ap.add_argument("--clock-ps", type=int, default=None, help="the clock target; the run file's vars.clock_ps by default")
    ap.add_argument("--timeout-s", type=int, default=DEFAULT_TIMEOUT_S, help="one attempt's limit; a call that reaches it is recorded as stalled and counts")
    ap.add_argument("--stages", default=",".join(STAGES), help="the evaluator stages to run (a Mac without read_slang runs conformance alone)")
    ap.add_argument("--no-synth-report", action="store_true", help="CHIALU_SYNTH_REPORT=0: no critical path, summary, paths or area by hierarchy as feedback")
    ap.add_argument("--synth-infeasible", action="store_true", help="synthesize a candidate that fails conformance too (its numbers are kept, its feasibility is not)")
    ap.add_argument("--verilator-jobs", type=int, default=None, help="CHIALU_VERILATOR_JOBS for the conformance build (the environment's value, else chiALU's default)")
    ap.add_argument("--evaluate", default="", help="evaluate this program file alone and print the result; no agent")
    a = ap.parse_args(argv)
    os.environ["CHIALU_SYNTH_REPORT"] = "0" if a.no_synth_report else "1"
    if a.verilator_jobs:
        os.environ["CHIALU_VERILATOR_JOBS"] = str(a.verilator_jobs)
    if a.evaluate:
        return run_evaluate(a)
    if not a.out:
        ap.error("--out is required")
    return run_loop(a)


if __name__ == "__main__":
    sys.exit(main())
