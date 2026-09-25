"""Evaluating one candidate (design section 9.3): the static checks,
the declaration, the derived graph, the constraints, the goal, the score,
and the record."""
from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from . import artifacts as A
from .archive import Archive
from .declaration import Declaration, check_declaration, parse_block, render_block
from .errors import UNDECIDED, BindError
from .expr import as_value, evaluate, parse as _parse_expr, references as _expr_refs, to_json
from .graph import Runner, root_of
from .instance import BindContext, Instance
from .metrics import combined_score, feasibility
from .nodes import Executor


@dataclass
class Candidate:
    """A candidate: the program text a backend produced (or a
    declaration-only program under a numeric backend), split into the
    seed artifact's members."""
    program: str
    texts: dict = field(default_factory=dict)       # member -> text without markers
    marked: dict = field(default_factory=dict)      # member -> text with markers
    declaration: Declaration = field(default_factory=Declaration)
    is_seed: bool = False
    seed_name: str = ""
    parent_id: Optional[str] = None
    iteration: Optional[int] = None
    meta: dict = field(default_factory=dict)

    @property
    def sha256(self) -> str:
        return hashlib.sha256(self.program.encode()).hexdigest()


class Resolver:
    """Answers every reference of an expression for one candidate."""

    def __init__(self, instance: Instance, run: Path, candidate: Candidate,
                 seed_values: dict, archive: Optional[Archive]):
        self.instance = instance
        self.run = run
        self.candidate = candidate
        self.seed_values = seed_values or {}
        self.archive = archive
        self.outputs: dict = {}
        self._decl_outputs: Optional[dict] = None
        self._goal_values: Optional[list] = None
        self._seed_ref: Optional[dict] = None

    # what the declaration node produces
    def declaration_outputs(self) -> dict:
        if self._decl_outputs is None:
            ctx = BindContext(self.instance, self.run, self.candidate, self.candidate.declaration)
            self._decl_outputs = check_declaration(self.instance, self.candidate.declaration, ctx)
        return self._decl_outputs

    def decl_value(self, name: str):
        outs = self.declaration_outputs()
        key = f"decl.{name}"
        if key in outs:
            return outs[key]
        # a family root: the mapping of its members
        prefix = key + "."
        found = {k[len(prefix):]: v for k, v in outs.items() if k.startswith(prefix)}
        if not found:
            return UNDECIDED
        nested: dict = {}
        for k, v in found.items():
            parts = k.split(".")
            cur = nested
            for p in parts[:-1]:
                cur = cur.setdefault(p, {})
            cur[parts[-1]] = v
        return nested

    def artifact_text(self, path: str, member: Optional[str]) -> Any:
        a = self.instance.artifacts[path]
        if a.role == "seed" and self.candidate.texts:
            texts = self.candidate.texts
        else:
            texts = a.texts
        if member is None:
            if a.is_family:
                return {m: texts[m] for m in a.members}
            return texts.get("", "")
        return texts[member]

    def assembled(self) -> str:
        parts = []
        lang = None
        for a in self.instance.artifacts.values():
            if a.role == "seed":
                lang = a.language
                t = self.artifact_text(a.path, None)
                parts.append("\n".join(t.values()) if isinstance(t, dict) else t)
        for a in self.instance.artifacts.values():
            if a.role == "fixed" and a.kind == "text" and (lang is None or a.language == lang):
                t = self.artifact_text(a.path, None)
                parts.append("\n".join(t.values()) if isinstance(t, dict) else t)
        return "\n".join(parts)

    def _walk(self, cur, parts: list):
        for p in parts:
            cur = as_value(cur)
            if isinstance(cur, dict) and p in cur:
                cur = cur[p]
            elif isinstance(cur, list) and p.isdigit() and int(p) < len(cur):
                cur = cur[int(p)]
            else:
                return UNDECIDED
        return cur

    def seed_reference(self) -> dict:
        """What `seed.*` means for a candidate: the measurements of the seed its lineage starts from (its
        parent's parent's ... seed), else each value's maximum over all seeds, else the first seed's values.
        Measured against the first seed alone, a screen such as `cells le 2 * seed.cells` refused every other
        seed's neighbourhood where that seed is larger than the first (exp9 fp_alu_cmp chiALU fronts 3 and 4)."""
        if self._seed_ref is not None:
            return self._seed_ref
        ref = None
        recs = []
        if self.archive is not None:
            try:
                recs = list(self.archive.records())
            except Exception:  # noqa: BLE001 -- no archive, no lineage
                recs = []
        by_id = {r.get("candidate_id"): r for r in recs}
        cur, seen = by_id.get(self.candidate.parent_id or ""), set()
        while cur is not None and cur.get("candidate_id") not in seen:
            if cur.get("is_seed"):
                ref = _measured_values(cur)
                break
            seen.add(cur.get("candidate_id"))
            cur = by_id.get(cur.get("parent_id") or "")
        if ref is None:
            seeds = [_measured_values(r) for r in recs if r.get("is_seed")]
            if seeds:
                ref = seeds[0]
                for other in seeds[1:]:
                    ref = _key_max(ref, other)
        self._seed_ref = ref if ref is not None else dict(self.seed_values)
        return self._seed_ref

    def goal_values(self) -> list:
        g = self.instance.goal
        return [g.value(self, i) for i in range(len(g.levels))]

    def __call__(self, ref: str):
        parts = ref.split(".")
        root = parts[0]
        inst = self.instance
        if root == "candidate":
            if len(parts) == 1:
                return self.assembled()
            if parts[1] == "touched":
                # the members whose text differs from the parent's (evaluate_entry); [] for a seed
                return list((self.candidate.meta or {}).get("touched") or [])
            return self.artifact_text(parts[1], parts[2] if len(parts) > 2 else None)
        if root == "artifacts":
            return self.artifact_text(parts[1], parts[2] if len(parts) > 2 else None)
        if root == "vars":
            name = ".".join(parts[1:])
            if name in inst.bindings:
                b = inst.bindings[name]
                return b.value if b.time == "fixed" else list(b.members)
            base = ".".join(parts[1:-1])
            b = inst.bindings[base]
            dom = b.variable.domain
            if b.time == "fixed":
                return dom.field_of(b.value, parts[-1])
            return {str(m): dom.field_of(m, parts[-1]) for m in b.members}
        if root == "decl":
            return self.decl_value(".".join(parts[1:]))
        if root == "run":
            return str(inst.run_dir if parts[1] == "dir" else inst.agent_dir)
        if root == "seed":
            if self.candidate.is_seed:
                return self(".".join(parts[1:]))      # every seed is its own reference
            return self._walk(self.seed_reference(), parts[1:])
        if root == "archive":
            if self.archive is None:
                return UNDECIDED
            if parts[1] == "goal":
                level = int(parts[2]) - 1 if len(parts) > 2 else 0
                return self.archive.goal_values(level)
            return self.archive.metric_values(".".join(parts[1:]))
        if root == "goal":
            level = int(parts[1]) - 1 if len(parts) > 1 else 0
            return self.goal_values()[level]
        if root in self.outputs:
            out = self.outputs[root]
            if out is UNDECIDED:
                return UNDECIDED
            return self._walk(out, parts[1:])
        if root in inst.nodes:
            return UNDECIDED
        raise KeyError(ref)


def _measured_values(record: dict) -> dict:
    return {n: m.get("value") for n, m in (record.get("measurements") or {}).items() if isinstance(m, dict)}


def _key_max(a, b):
    """`a` and `b` merged, each number the larger of the two (dicts merged key by key; `a`'s value kept
    where the two are not both numbers)."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = dict(b)
        out.update({k: (_key_max(v, b[k]) if k in b else v) for k, v in a.items()})
        return out
    if isinstance(a, (int, float)) and isinstance(b, (int, float)) and not isinstance(a, bool) \
            and not isinstance(b, bool):
        return max(a, b)
    return a if a is not None else b


def goal_measured(goal, values: list) -> bool:
    """Whether the goal has the values a feasible record needs: every level of a Pareto goal, at least the
    first of a ranked one."""
    if not values:
        return False
    if getattr(goal, "kind", None) == "pareto":
        return all(as_value(v) is not UNDECIDED and v is not None for v in values)
    return goal.highest_level(values) >= 0


def program_from_seed_text(instance: Instance, texts: dict, decl_vars: dict,
                           decl_lines: list) -> str:
    """The backend program of a seed: markers around the mutable regions
    of every member, the declaration block at the top of the first."""
    a = instance.seed_artifacts()[0]
    prefix = a.prefix(instance.template.comment_syntax)
    block = render_block(decl_vars, decl_lines, prefix)
    return A.assemble_program(a, texts, block, instance.template.comment_syntax)


def declaration_program(instance: Instance, decl_vars: dict, decl_lines=()) -> str:
    """The program of a numeric backend: the declaration block alone."""
    return render_block(decl_vars, list(decl_lines), "")


def replan_program(instance: Instance, program: str, parent: Optional[dict],
                   parent_program: Optional[str]) -> Optional[str]:
    """The program re-rendered by the template's `replan` hook when the
    candidate's declaration changes the plan its parent had (a sharing
    plan regroups structures, or a declared family the template realizes
    by construction changes): the hook returns the texts, vars and lines
    of the new plan's seed and the regions whose text the parent keeps;
    None leaves the program as the model wrote it. A hook whose
    signature takes `parent_program` receives the parent's text, so it
    can keep the regions the candidate edited."""
    import inspect
    hook = getattr(instance.template, "replan", None)
    seeds = instance.seed_artifacts()
    if hook is None or not seeds or parent is None:
        return None
    takes_program = "parent_program" in inspect.signature(hook).parameters
    a = seeds[0]
    try:
        cand = candidate_from_program(instance, program)
    except BindError:
        return None
    pd = parent.get("declarations") or {}
    parent_decl = Declaration(vars=dict(pd.get("vars") or {}), lines=[tuple(x) for x in pd.get("lines") or []],
                              present=True)
    ctx = instance.ctx(candidate=cand, declaration=cand.declaration)
    res = (hook(ctx, cand.declaration, parent_decl, parent_program=parent_program) if takes_program
           else hook(ctx, cand.declaration, parent_decl))
    if not res:
        return None
    texts, vars_, lines, keep = res
    if isinstance(texts, str):
        texts = {"": texts}
    new = program_from_seed_text(instance, texts, dict(vars_), list(lines))
    if keep and parent_program:
        new = A.swap_regions(a, new, parent_program, list(keep))
    return new


def candidate_from_program(instance: Instance, program: str, **meta) -> Candidate:
    seeds = instance.seed_artifacts()
    if not seeds:
        c = Candidate(program=program, **meta)
        c.declaration = parse_block(program)
        return c
    a = seeds[0]
    marked = A.split_program(a, program)
    texts = {m: A.strip_markers(t) for m, t in marked.items()}
    decl_member = a.declaration_member or (a.members[0] if a.is_family else "")
    c = Candidate(program=program, texts=texts, marked=marked, **meta)
    c.declaration = parse_block(texts.get(decl_member, ""))
    if not c.declaration.present:
        for t in texts.values():
            d = parse_block(t)
            if d.present:
                c.declaration = d
                break
    return c


def static_checks(instance: Instance, cand: Candidate, seed_programs: list,
                  parent_program: Optional[str] = None) -> list:
    """`evolve_bounds`: the fixed part of the candidate equals the fixed
    part of some seed program or of its parent's program (a parent the
    template re-rendered for a new plan has a fixed part of its own,
    which its children inherit); a candidate the template re-rendered
    (`replanned`) carries the template's fixed part and passes.
    `input_immutable` holds by construction for text artifacts (inputs
    are not in the program)."""
    problems = []
    seeds = instance.seed_artifacts()
    if not seeds or cand.is_seed or cand.meta.get("replanned"):
        return problems
    a = seeds[0]
    try:
        mine = {m: A.fixed_part(t) for m, t in cand.marked.items()}
    except BindError as e:
        return [f"evolve_bounds: {e.msg}"]
    ok = False
    baselines = list(seed_programs) + ([parent_program] if parent_program else [])
    for sp in baselines:
        try:
            theirs = {m: A.fixed_part(t) for m, t in A.split_program(a, sp).items()}
        except BindError:
            continue
        if theirs == mine:
            ok = True
            break
    if not ok and baselines:
        problems.append("evolve_bounds: text outside the EVOLVE blocks differs from every seed and from the parent")
    return problems


def evaluate_candidate(instance: Instance, run: Path, cand: Candidate, *,
                       seed_values: Optional[dict] = None, archive: Optional[Archive] = None,
                       executor: Optional[Executor] = None, seed_programs: Optional[list] = None,
                       pins: Optional[dict] = None, mode: str = "evaluate",
                       log=None, parent_program: Optional[str] = None) -> dict:
    """The record of one candidate; appended to `archive` when given.
    `parent_program` is the parent's program text, a baseline of the
    static checks beside the seeds."""
    run = Path(run)
    t0 = time.time()
    executor = executor or Executor(run / "cache")
    pins = pins if pins is not None else load_pins(run)
    seed_values = seed_values if seed_values is not None else load_seed_values(run)
    resolver = Resolver(instance, run, cand, seed_values, archive)
    constraint_results = {c.index: None for c in instance.constraints}
    static = static_checks(instance, cand, seed_programs or [], parent_program)
    results: list = []

    def decidable(c):
        return all(root_of(r) not in instance.nodes or root_of(r) in resolver.outputs
                   for r in c.refs)

    def on_done(node_name):
        stop_ok = True
        for c in instance.constraints:
            if not c.hard or constraint_results[c.index] is not None:
                continue
            if not decidable(c):
                continue
            r = c.evaluate(resolver)
            r.update({"text": c.text, "hard": True, "satisfies": c.satisfies})
            constraint_results[c.index] = r
            if r["status"] != "satisfied":
                stop_ok = False
        return stop_ok

    runner = Runner(instance.graph, executor, resolver, pins, on_done, mode, log)
    # a member the tail rule stopped waiting for is carried at its parent's value, so the
    # round still scores and the search still gets a signal; it earns no credit for the
    # member it did not measure, and `giveup.max_skips` bounds how long that can stand
    parent_rec = archive.get(cand.parent_id) if (archive is not None and cand.parent_id) else None
    runner.carry_from = ((parent_rec or {}).get("measurements") or {}) or \
                        {k: {"value": v} for k, v in (seed_values or {}).items() if k != "__goal__"}
    if static:
        runner.cancelled = True
    resolver.outputs = runner.outputs
    runner.run()
    for c in instance.constraints:
        if constraint_results[c.index] is None:
            r = c.evaluate(resolver)
            r.update({"text": c.text, "hard": c.hard, "satisfies": c.satisfies})
            constraint_results[c.index] = r
    results = [constraint_results[c.index] for c in instance.constraints]
    if static:
        results.insert(0, {"text": "static checks", "hard": True, "status": "violated",
                           "detail": "; ".join(static), "slack": None, "satisfies": None})
    feas = feasibility(results)
    goal_values = resolver.goal_values()
    unmeasured = None
    if feas["feasible"] and instance.goal.levels and not goal_measured(instance.goal, goal_values):
        # a gate skipped the goal's nodes: every hard row holds, but nothing measured the goal, so the
        # candidate is not feasible (a record feasible without goal values reads as a design nobody measured)
        feas = {**feas, "feasible": False}
        unmeasured = "; ".join(f"{n}: {why}" for n, why in runner.skipped.items()) or "no goal value"
    seed_goal = [as_value(v) for v in (seed_values.get("__goal__") or [])]
    if cand.is_seed and not seed_goal:
        seed_goal = goal_values
    score = combined_score(instance.goal, goal_values, seed_goal, feas, runner.screen_distance)
    level = instance.goal.highest_level(goal_values)
    measurements = {}
    for n, out in runner.outputs.items():
        if out is UNDECIDED:
            continue
        value = to_json(out)
        # the members this node stopped waiting for keep the value they had, and the record
        # names them: a number the agent reads as the effect of its edit must not be one
        # that nothing this round measured
        for member in runner.gave_up.get(n, []):
            src = ((runner.carry_from.get(n) or {}).get("value") or {})
            if isinstance(value, dict):
                for out_name, curve in value.items():
                    if isinstance(curve, dict) and isinstance(src.get(out_name), dict):
                        curve[member] = src[out_name].get(member)
        # a transient output (a compiled binary, a netlist) reached the nodes that
        # needed it through `runner.outputs`; the record keeps its size, not its bytes
        transient = instance.nodes[n].spec.transient if n in instance.nodes else []
        if transient and isinstance(value, dict):
            value = dict(value)
            for k in transient:
                if k in value:
                    v = value[k]
                    value[k] = f"<transient: {len(v)} bytes>" if isinstance(v, str) else None
        measurements[n] = {"value": value, "node_hash": runner.node_hashes.get(n)}
    decl_out = resolver.declaration_outputs() if instance.decl_node in runner.outputs else {}
    fb = {}
    for e in instance.feedback:
        try:
            v = to_json(e.value(resolver))
        except Exception as ex:  # noqa: BLE001
            v = None
        if v is not None:
            fb[e.text] = v
    if runner.gave_up:
        # the agent reads the feedback as the effect of its edit, so a number nothing
        # measured this round has to say so; the value itself is the parent's
        fb["carried from the parent, not measured this round"] = {
            n: sorted(set(ms)) for n, ms in runner.gave_up.items() if ms}
    stderr = None
    for n in instance.graph.active:
        out = runner.outputs.get(n)
        if isinstance(out, dict) and out.get("ok") is False and out.get("detail"):
            stderr = str(out["detail"])
            break
    if static:
        stderr = "; ".join(static)
    cid = cand.meta.get("candidate_id") or (f"seed:{cand.seed_name}" if cand.is_seed else uuid.uuid4().hex[:12])
    record = {
        "run": run.name, "iteration": cand.iteration, "candidate_id": cid,
        "parent_id": cand.parent_id, "seed_name": cand.seed_name if cand.is_seed else None,
        "is_seed": cand.is_seed,
        **{k: instance.hashes[k] for k in ("unit_id", "space_hash", "evaluator_hash")},
        "search_hash": instance.hashes.get("search_hash"),
        "model": cand.meta.get("model"), "operator": cand.meta.get("operator"),
        "prompt_config": cand.meta.get("prompt_config"), "tactic_id": cand.meta.get("tactic_id"),
        "instruction_id": cand.meta.get("instruction_id"),
        "declarations": {"vars": cand.declaration.vars,
                         "lines": [[k, t] for k, t in cand.declaration.lines],
                         "verified": decl_out.get("ok")},
        "constraints": results, "measurements": {n: m for n, m in measurements.items()},
        "skipped": runner.skipped, "gave_up": {n: sorted(set(m)) for n, m in runner.gave_up.items() if m},
        "hard_fail": feas["hard_fail"], "feasible": feas["feasible"],
        "goal_values": [None if v is UNDECIDED else v for v in goal_values],
        "fidelity_level": level, "touched": cand.meta.get("touched", []),
        "sub": cand.meta.get("sub", []),
        "score": {"combined_score": score, "rule": instance.goal.score_rule},
        "source_sha256": cand.sha256, "source_path": cand.meta.get("source_path"),
        "cost": {"seconds": round(time.time() - t0, 3), "node_calls": executor.calls,
                 "cache_hits": executor.hits, **(cand.meta.get("cost") or {})},
        "feedback": fb, "stderr": stderr,
        "decision": "pending",
    }
    if unmeasured:
        record["goal_unmeasured"] = unmeasured[:500]
    if cand.meta.get("duplicate_of"):
        # the same program text as a candidate already evaluated: measured again (the node cache makes it
        # cheap) and recorded as usual, and its feedback says so, so the next round does not submit it again
        record["duplicate_of"] = cand.meta["duplicate_of"]
        fb["duplicate"] = (f"this program is byte-identical to candidate {cand.meta['duplicate_of']}, which was "
                           "already evaluated: the submission changed nothing new")
    record["retracted"] = _retract_for(instance, run, cand, results)
    entries = (cand.meta or {}).get("history") or []
    if entries:
        from .composer import note_effect
        note_effect(run, entries, effect_text(instance, record, parent_rec),
                    candidate_id=cid, parent_id=cand.parent_id)
    if archive is not None:
        archive.append(record)
    save_pins(run, pins)
    return record


def _pct(new, old) -> Optional[str]:
    if not (isinstance(new, (int, float)) and isinstance(old, (int, float))) or not old:
        return None
    return f"{new / old - 1:+.2%}"


def _first_error(text) -> str:
    """A compiler's diagnostic from its output: the first line naming an
    error, else the text -- the lines before it are the file and the
    function, which the note has no room for."""
    lines = str(text or "").splitlines()
    return next((ln.strip() for ln in lines if "error" in ln.lower()), str(text or "").strip())


def _failing_members(record: dict, row: dict) -> str:
    """The members a row over a mapped measurement failed on: `min(gem5.ok)`
    says only that one did, and the edit's effect is which one."""
    try:
        refs = _expr_refs(_parse_expr(row.get("text") or ""))
    except Exception:  # noqa: BLE001 -- a row whose text will not parse names no member
        return ""
    out = []
    for ref in refs:
        node, _, name = ref.partition(".")
        v = (((record.get("measurements") or {}).get(node) or {}).get("value") or {}).get(name) if name else None
        if isinstance(v, dict):
            bad = [k for k, x in v.items() if x is False or x is None or x == 0]
            if bad:
                out.append(f"{ref} fails on {', '.join(map(str, bad))}")
    return "; ".join(out)


def effect_text(instance: Instance, record: dict, parent: Optional[dict]) -> str:
    """What one evaluated edit measured, against its parent: the line a
    later round reads under the edit's history entry.

    A refused edit names the first hard row it broke. A measured one
    gives each goal level's value beside the parent's, with the change
    and whether it went the goal's way, then the per-member change of
    every mapped measurement the goal is computed from -- a geomean over
    four shapes that moved by a percent can be two shapes twelve percent
    worse, and the edit that did it has to be recognisable as that. The
    members a node gave up on are named, since their numbers are the
    parent's.
    """
    head = f"candidate {record.get('candidate_id')}" + (
        f", from {parent.get('candidate_id')}" if parent else "")
    if record.get("retracted") or not record.get("feasible"):
        row = next((r for r in record.get("constraints") or []
                    if r.get("hard") and r.get("status") == "violated"), None)
        why = (f"{row.get('text')}: {row.get('detail') or _failing_members(record, row) or _first_error(record.get('stderr')) or 'violated'}" if row
               else (record.get("stderr") or "infeasible"))
        verdict = "retracted" if record.get("retracted") else "infeasible"
        return f"({head}) {verdict} -- {' '.join(str(why).split())[:240]}"
    parts = []
    pg = (parent or {}).get("goal_values") or []
    for i, (direction, expr) in enumerate(instance.goal.levels):
        gv = record.get("goal_values") or []
        v = gv[i] if i < len(gv) else None
        if v is None:
            continue
        old = pg[i] if i < len(pg) else None
        if isinstance(old, (int, float)):
            better = instance.goal.better(v, old, i)
            way = "better" if better else ("unchanged" if v == old else "worse")
            parts.append(f"{expr.text} {old:.6g} -> {v:.6g} ({_pct(v, old) or 'n/a'}, {way}; {direction})")
        else:
            parts.append(f"{expr.text} {v:.6g} ({direction})")
    pm = (parent or {}).get("measurements") or {}
    cm = record.get("measurements") or {}
    seen = set()
    for ref in instance.goal.refs:
        if ref.startswith("seed.") or ref in seen:
            continue
        seen.add(ref)
        node, _, out = ref.partition(".")
        cur = ((cm.get(node) or {}).get("value") or {}).get(out) if out else None
        old = ((pm.get(node) or {}).get("value") or {}).get(out) if out else None
        if not (isinstance(cur, dict) and isinstance(old, dict)):
            continue
        each = [f"{k} {_pct(cur[k], old.get(k))}" for k in cur if _pct(cur[k], old.get(k))]
        if each:
            parts.append(f"{ref} per member " + ", ".join(each[:16]))
    gave = {m for ms in (record.get("gave_up") or {}).values() for m in ms}
    if gave:
        parts.append(f"not measured this round, carried from the parent: {', '.join(sorted(gave))}")
    return f"({head}) " + ("; ".join(parts) if parts else "measured, no goal value")


def _retract_for(instance: Instance, run: Path, cand: Candidate, results: list) -> list:
    """Retract the history entries of a candidate a `rollback` node refused.

    The agent writes its note when it answers, before anything is built,
    so the note stands for an edit nothing has yet judged. A node marked
    `rollback` is that judgement: where a hard row over it is violated --
    the candidate did not compile, did not conform -- the edit did not
    survive, and a later round that read the note would be reading a
    change that never stood. The note stays in the file and leaves the
    prompt; the record says it was retracted and why.
    """
    entries = (cand.meta or {}).get("history") or []
    if not entries:
        return []
    marked = [n for n, ni in instance.nodes.items() if ni.rollback]
    if not marked:
        return []
    for row in results:
        if not row.get("hard") or row.get("status") != "violated":
            continue
        try:
            refs = _expr_refs(_parse_expr(row.get("text") or ""))
        except Exception:  # noqa: BLE001 -- a row whose text will not parse names no node
            continue
        hit = [m for m in marked if any(r == m or r.startswith(f"{m}.") for r in refs)]
        if not hit:
            continue
        from .composer import retract_history
        return retract_history(run, entries, f"{hit[0]}: {row.get('detail') or row.get('text')}"[:200])
    return []


def malformed_record(instance: Instance, run: Path, program: str, error: str, *,
                     archive=None, infrastructure: bool = False, **meta) -> dict:
    """The record of a program the candidate parser refused (member
    markers lost, no declaration block): a hard failure at score 0 with
    the parser's message as `stderr` and feedback, so the archive keeps
    the attempt and the model reads why it failed."""
    import hashlib
    cid = uuid.uuid4().hex[:12]
    record = {
        "run": run.name, "iteration": meta.get("iteration"), "candidate_id": cid,
        "parent_id": meta.get("parent_id"), "seed_name": None, "is_seed": False,
        **{k: instance.hashes[k] for k in ("unit_id", "space_hash", "evaluator_hash")},
        "search_hash": instance.hashes.get("search_hash"),
        "model": meta.get("model"), "operator": meta.get("operator"),
        "prompt_config": meta.get("prompt_config"), "tactic_id": meta.get("tactic_id"),
        "instruction_id": meta.get("instruction_id"),
        "declarations": {"vars": {}, "lines": [], "verified": False},
        "constraints": [], "measurements": {}, "skipped": [], "hard_fail": True, "feasible": False,
        "goal_values": [None] * len(instance.goal.levels),
        "fidelity_level": 0, "touched": [], "sub": [],
        "score": {"combined_score": 0.0, "rule": instance.goal.score_rule},
        "source_sha256": hashlib.sha256(program.encode()).hexdigest(),
        "source_path": meta.get("source_path"),
        "cost": {"seconds": 0.0, "node_calls": 0, "cache_hits": 0},
        "feedback": {"program": error}, "stderr": error, "decision": "pending",
    }
    if infrastructure:
        # ray failed on every evaluation of it: not evaluated, which is no verdict on the candidate
        record.update({"hard_fail": False, "not_evaluated": "infrastructure",
                       "feedback": {"evaluation": f"not evaluated (cluster failure): {error}"}})
    if meta.get("history"):
        from .composer import note_effect
        what = "not evaluated (cluster failure)" if infrastructure else "refused before evaluation"
        note_effect(run, meta["history"], f"(candidate {cid}) {what} -- " + " ".join(str(error).split())[:240],
                    candidate_id=cid, parent_id=meta.get("parent_id"))
    if archive is not None:
        archive.append(record)
    return record


def backend_result(instance: Instance, record: dict) -> dict:
    """What the evaluator entry returns to the backend (design section
    9.3): `metrics` holds the numbers (`combined_score`, every numeric
    node output flattened with dots, `goal.<n>`, `error` on a hard
    failure) and `candidate_id`, which the backend renders in the
    prompt so the model client finds the parent record; `metadata`
    holds the declarations and the short strings; `artifacts` holds the
    feedback, the declaration block and `stderr`."""
    metrics: dict = {"combined_score": record["score"]["combined_score"],
                     "candidate_id": record["candidate_id"],
                     "feasible": int(bool(record["feasible"])),
                     "fidelity_level": record["fidelity_level"]}
    metadata: dict = {"candidate_id": record["candidate_id"],
                      "fidelity_level": record["fidelity_level"],
                      "feasible": record["feasible"]}
    for n, m in record["measurements"].items():
        _flatten_numeric(n, m["value"], metrics, metadata)
    for i, v in enumerate(record.get("goal_values") or []):
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            metrics[f"goal.{i + 1}"] = v
    for k, v in record["declarations"]["vars"].items():
        metadata[f"decl.{k}"] = v
    if record["hard_fail"]:
        metrics["error"] = 0.0
        if record.get("stderr"):
            metrics["error_message"] = str(record["stderr"])[:500]
    if instance.goal.kind == "pareto":
        metadata["pareto_objectives"] = record["goal_values"]
    artifacts = {k: (v if isinstance(v, str) else json.dumps(v, default=str)[:20000])
                 for k, v in record["feedback"].items()}
    d = record["declarations"]
    artifacts["declarations"] = render_block(d.get("vars") or {},
                                             [tuple(x) for x in d.get("lines") or []], "").strip()
    if record.get("stderr"):
        artifacts["stderr"] = record["stderr"][:20000]
    return {"metrics": metrics, "metadata": metadata, "artifacts": artifacts}


def _flatten_numeric(prefix, v, metrics, metadata, depth=0):
    if isinstance(v, bool):
        metrics[prefix] = int(v)
    elif isinstance(v, (int, float)):
        metrics[prefix] = v
    elif isinstance(v, dict) and depth < 3:
        if {"mean", "lo", "hi"} <= set(v):
            metrics[prefix] = v["mean"]
            return
        for k, x in v.items():
            _flatten_numeric(f"{prefix}.{k}", x, metrics, metadata, depth + 1)
    elif isinstance(v, str) and len(v) < 200:
        metadata[prefix] = v


def load_pins(run: Path) -> dict:
    f = Path(run) / "pins.json"
    return json.loads(f.read_text()) if f.is_file() else {}


def save_pins(run: Path, pins: dict):
    if pins:
        Path(run).mkdir(parents=True, exist_ok=True)
        (Path(run) / "pins.json").write_text(json.dumps(pins, default=str))


def load_seed_values(run: Path) -> dict:
    f = Path(run) / "seeds" / "seed_values.json"
    return json.loads(f.read_text()) if f.is_file() else {}


def seed_programs_of(run: Path) -> list:
    out = []
    d = Path(run) / "seeds"
    if d.is_dir():
        for p in sorted(d.glob("*/program.*")):
            out.append(p.read_text())
    return out
