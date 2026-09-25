"""summary.json, report.md and the report-only nodes for the front
(design section 10.4)."""
from __future__ import annotations

import json
from pathlib import Path

from .evaluate import Resolver, candidate_from_program, evaluate_candidate, load_seed_values
from .expr import to_json
from .graph import Runner
from .instance import Instance
from .nodes import Executor


def report(inst: Instance, run: Path, executor=None) -> dict:
    run = Path(run)
    archive = inst.archive(run)
    recs = archive.records()
    goal = inst.goal
    front = archive.front(goal)
    ranked = archive.ranked(goal)
    executor = executor or Executor(run / "cache")
    seed_values = load_seed_values(run)
    report_values = {}
    if inst.report and front:
        for r in front:
            src = Path(r["source_path"]) if r.get("source_path") else None
            if not src or not src.is_file():
                continue
            cand = candidate_from_program(inst, src.read_text(), is_seed=bool(r.get("is_seed")),
                                          seed_name=r.get("seed_name") or "")
            resolver = Resolver(inst, run, cand, seed_values, archive)
            runner = Runner(inst.graph, executor, resolver, {}, None, mode="report")
            resolver.outputs = runner.outputs
            runner.run()
            report_values[r["candidate_id"]] = {e.text: to_json(e.value(resolver)) for e in inst.report}
    levels = len(goal.levels)
    corr = {}
    for i in range(levels - 1):
        pairs = [(r["goal_values"][i], r["goal_values"][i + 1]) for r in recs
                 if r.get("goal_values") and len(r["goal_values"]) > i + 1
                 and r["goal_values"][i] is not None and r["goal_values"][i + 1] is not None]
        corr[f"{i + 1}->{i + 2}"] = _spearman(pairs)
    cost = {"records": len(recs), "seconds": round(sum((r.get("cost") or {}).get("seconds", 0) for r in recs), 1),
            "node_calls": sum((r.get("cost") or {}).get("node_calls", 0) for r in recs)}
    summary = {
        "unit_id": inst.hashes["unit_id"], "space_hash": inst.hashes["space_hash"],
        "evaluator_hash": inst.hashes["evaluator_hash"],
        "records": len(recs), "feasible": sum(1 for r in recs if r.get("feasible")),
        "hard_failures": sum(1 for r in recs if r.get("hard_fail")),
        "front": [r["candidate_id"] for r in front],
        "best": ranked[0]["candidate_id"] if ranked else None,
        "best_score": ranked[0]["score"]["combined_score"] if ranked else None,
        "report_values": report_values, "level_rank_correlation": corr, "cost": cost,
        "per_seed": _per_seed(recs), "per_declaration": _per_decl(recs),
        "requirements": inst.requirements,
        "hard_constraints": [c.text for c in inst.constraints if c.hard],
    }
    (run / "summary.json").write_text(json.dumps(summary, indent=1, default=str))
    (run / "report.md").write_text(_markdown(inst, summary, front, ranked[:10]))
    best_dir = run / "best"
    best_dir.mkdir(exist_ok=True)
    for r in front:
        src = Path(r["source_path"]) if r.get("source_path") else None
        if src and src.is_file():
            (best_dir / f"{r['candidate_id'].replace(':', '_')}{src.suffix}").write_text(src.read_text())
    return summary


def _per_seed(recs):
    out = {}
    for r in recs:
        s = r.get("seed_name") or (r.get("parent_id") or "").replace("seed:", "") or "?"
        d = out.setdefault(s, {"records": 0, "feasible": 0, "best_score": None})
        d["records"] += 1
        d["feasible"] += 1 if r.get("feasible") else 0
        sc = r["score"]["combined_score"]
        if d["best_score"] is None or sc > d["best_score"]:
            d["best_score"] = sc
    return out


def _per_decl(recs):
    out = {}
    for r in recs:
        for k, v in (r.get("declarations") or {}).get("vars", {}).items():
            d = out.setdefault(k, {}).setdefault(str(v), {"records": 0, "best_score": None})
            d["records"] += 1
            sc = r["score"]["combined_score"]
            if d["best_score"] is None or sc > d["best_score"]:
                d["best_score"] = sc
    return out


def _spearman(pairs):
    if len(pairs) < 3:
        return None

    def ranks(xs):
        order = sorted(range(len(xs)), key=lambda i: xs[i])
        r = [0.0] * len(xs)
        for rank, i in enumerate(order):
            r[i] = rank
        return r
    a = ranks([p[0] for p in pairs])
    b = ranks([p[1] for p in pairs])
    n = len(pairs)
    d2 = sum((x - y) ** 2 for x, y in zip(a, b))
    return round(1 - 6 * d2 / (n * (n * n - 1)), 3)


def _markdown(inst, summary, front, top):
    L = [f"# {inst.template.name}: run report", "",
         f"* records: {summary['records']}, feasible: {summary['feasible']}, "
         f"hard failures: {summary['hard_failures']}",
         f"* best: {summary['best']} (score {summary['best_score']})",
         f"* hard constraints active: {', '.join(summary['hard_constraints']) or 'none'}",
         f"* requirements discharged: {', '.join(summary['requirements']) or 'none'}",
         f"* cost: {summary['cost']}", ""]
    if summary["level_rank_correlation"]:
        L += ["## Fidelity levels", ""] + [f"* rank correlation {k}: {v}" for k, v in
                                          summary["level_rank_correlation"].items()] + [""]
    L += ["## Front", ""]
    for r in front:
        L.append(f"* {r['candidate_id']}: goal {r['goal_values']}, declarations {r['declarations']['vars']}")
        rv = summary["report_values"].get(r["candidate_id"])
        if rv:
            L.append(f"    * report: {rv}")
    L += ["", "## Top records", ""]
    for r in top:
        L.append(f"* {r['candidate_id']}: score {r['score']['combined_score']:.3f}, level "
                 f"{r['fidelity_level']}, {'feasible' if r['feasible'] else 'infeasible'}, "
                 f"goal {r['goal_values']}")
    return "\n".join(L) + "\n"
