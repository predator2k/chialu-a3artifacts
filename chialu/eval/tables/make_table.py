"""Table A and its figure from run archives (docs/evaluation-plan.md).

    python3 eval/tables/make_table.py --out eval/tables/out \\
        --method chiALU=run/fp_alu_cmp/results_db.jsonl \\
        --method best_of_n=run/fp_alu_cmp.free_best_of_n/results_db.jsonl \\
        --method plain_loop=run/fp_alu_cmp.plain/plain_loop.jsonl \\
        [--seeds run/fp_alu_cmp/results_db.jsonl] [--reference FPnew=area,delay] [--clock 8000]

A method row: the feasible records' front over (area_um2, delay_ps),
the hypervolume of that front in one fixed box shared by every row of
the table (from the origin to --box-factor, 1.2, times the baseline
seed's area and delay; the largest area and delay among the rows when no
baseline is recorded), the
best feasible area, the minimum delay, the feasible fraction, the
number of evaluated records and the calls to 95% of the final
hypervolume. The seeds (tier 2) and the reference designs (tier 1) are
rows at the foot. The figure plots every method's front, the seeds and
the references.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def records(path: Path) -> list:
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def points_of(recs: list) -> list:
    """[(area, delay, index)] of the feasible records with both goal values."""
    pts = []
    for i, r in enumerate(recs):
        g = r.get("goal_values")
        if r.get("feasible") and g and len(g) >= 2 and g[0] is not None and g[1] is not None:
            pts.append((float(g[0]), float(g[1]), i))
    return pts


def front(pts: list) -> list:
    out = []
    for p in sorted(pts):
        if all(not (q[0] <= p[0] and q[1] <= p[1] and (q[0], q[1]) != (p[0], p[1])) for q in pts):
            out.append(p)
    return out


def hypervolume(pts: list, ref: tuple) -> float:
    """The fraction of the box [0, ref] the front of `pts` dominates (2-D)."""
    f = [p for p in front(pts) if p[0] <= ref[0] and p[1] <= ref[1]]
    if not f:
        return 0.0
    f.sort()
    area, prev_a = 0.0, 0.0
    # sweep by area ascending: each point covers (ref_a - a) x (prev_delay - d)? use the standard staircase
    hv, last_d = 0.0, ref[1]
    for a_, d_, _i in f:
        hv += (ref[0] - a_) * (last_d - d_) if d_ < last_d else 0.0
        last_d = min(last_d, d_)
    return hv / (ref[0] * ref[1])


def table_ref(point_sets: list) -> tuple:
    """The hypervolume's reference point, one per table: the largest area and the largest
    delay among every row's feasible points, the seeds and the references. The comparison
    targets map for their least delay (MIN_DELAY_PS in targets/make_targets.py), so no clock
    bounds a front, and the seed's own point as the reference would score a front that
    trades delay for area at zero; one shared box ranks every row on the same measure."""
    pts = [p for ps in point_sets for p in ps]
    return (max((p[0] for p in pts), default=1.0), max((p[1] for p in pts), default=1.0))


def summarize(label: str, recs: list, seed: tuple | None, clock: float | None = None, ref: tuple | None = None) -> dict:
    """A method's row under `ref` (table_ref); with `clock` and a seed the box is the
    earlier (seed area, clock) one, whose runs admitted only delays under the clock."""
    pts = points_of(recs)
    if ref is None:
        ref = seed or (max((p[0] for p in pts), default=1.0), max((p[1] for p in pts), default=1.0))
    if clock and seed:
        ref = (seed[0], float(clock))
    hv = hypervolume(pts, ref)
    # the seeds count toward the front (they are where the method starts: chiALU's numeric front, the others'
    # one baseline) but not toward the candidates the search evaluated
    n_seed = sum(1 for r in recs if r.get("is_seed"))
    n = len(recs) - n_seed
    feas = sum(1 for p in pts if not recs[p[2]].get("is_seed"))
    calls95 = None
    if pts and hv > 0:
        for i in range(len(recs)):
            if hypervolume([p for p in pts if p[2] <= i], ref) >= 0.95 * hv:
                calls95 = max(0, i + 1 - n_seed)
                break
    return {"method": label, "records": n, "feasible": feas, "feasible_fraction": round(feas / n, 3) if n else None,
            "hypervolume": round(hv, 4), "best_area_um2": round(min((p[0] for p in pts), default=float("nan")), 1),
            "min_delay_ps": round(min((p[1] for p in pts), default=float("nan")), 1), "calls_to_95pct": calls95,
            "front": [(round(a, 1), round(d, 1)) for a, d, _ in front(pts)]}


def usage_of(path: Path) -> dict:
    """The model calls of a run beside its archive: ADIR's `llm_calls.jsonl` (one row per call, the review's
    included) or the plain loop's `call_<k>/usage.json`; calls, tokens, cost and the agent's wall hours."""
    d = path.parent
    rows = []
    if (d / "llm_calls.jsonl").is_file():
        for l in (d / "llm_calls.jsonl").read_text().splitlines():
            try:
                r = json.loads(l)
            except ValueError:
                continue
            rows.append((r.get("usage") or {}, r.get("wall_s") or 0.0))
    else:
        for c in sorted(d.glob("call_*")):
            try:
                u = json.loads((c / "usage.json").read_text()) if (c / "usage.json").is_file() else {}
                w = (json.loads((c / "call.json").read_text()) if (c / "call.json").is_file() else {}).get("wall_s") or 0.0
            except ValueError:
                u, w = {}, 0.0
            rows.append((u, w))
    tot = lambda k: sum(float(u.get(k) or 0) for u, _ in rows)
    return {"model_calls": len(rows), "input_tokens": int(tot("input_tokens")), "output_tokens": int(tot("output_tokens")),
            "cost_usd": round(tot("cost_usd"), 2), "agent_hours": round(sum(float(w or 0) for _, w in rows) / 3600, 2)}


def aggregate(label: str, reps: list) -> dict:
    """The repetitions of one method (every --method under the same label) as one row: the mean and the
    sample standard deviation of each number over the repetitions that have it, and the n."""
    import math
    out = {"method": f"{label} (mean +- sd, n={len(reps)})", "repetitions": len(reps)}
    for k in ("records", "feasible", "feasible_fraction", "hypervolume", "best_area_um2", "min_delay_ps", "calls_to_95pct",
              "model_calls", "input_tokens", "output_tokens", "cost_usd", "agent_hours"):
        xs = [float(r[k]) for r in reps if isinstance(r.get(k), (int, float)) and not math.isnan(float(r[k]))]
        if not xs:
            out[k] = None
            continue
        m = sum(xs) / len(xs)
        sd = math.sqrt(sum((x - m) ** 2 for x in xs) / (len(xs) - 1)) if len(xs) > 1 else 0.0
        digits = 4 if k in ("hypervolume", "feasible_fraction") else 1
        out[k] = f"{round(m, digits)} +- {round(sd, digits)}"
        out[k + "_values"] = xs
    out["front"] = []
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--method", action="append", default=[], help="label=results_db.jsonl (or plain_loop.jsonl)")
    ap.add_argument("--seeds", help="the archive whose seed records are the tier-2 rows (default: the first method's)")
    ap.add_argument("--reference", action="append", default=[], help="label=area_um2,delay_ps of a reference design")
    ap.add_argument("--clock", type=float, default=None, help="the earlier (seed area, clock) box")
    ap.add_argument("--baseline", help="area_um2,delay_ps of the baseline the box is fixed by (default: the seeds')")
    ap.add_argument("--box-factor", type=float, default=1.2,
                    help="the fixed hypervolume box, this multiple of the baseline's area and delay (0: the rows' largest)")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    methods = [(m.split("=", 1)[0], Path(m.split("=", 1)[1])) for m in a.method]
    seeds_path = Path(a.seeds) if a.seeds else (methods[0][1] if methods else None)
    seed_recs = [r for r in records(seeds_path) if r.get("is_seed") or r.get("seed_name")] if seeds_path and seeds_path.is_file() else []
    seed_pt = None
    # the baseline seed, else the run's first seed (an ALU run seeds from the numeric front alone, whose first
    # point is the fastest and the score reference; front_1 is the baseline program there)
    base = (next((r for r in seed_recs if r.get("seed_name") == "baseline" and r.get("feasible")), None)
            or next((r for r in seed_recs if r.get("feasible")), None))
    if base and base.get("goal_values"):
        seed_pt = (float(base["goal_values"][0]), float(base["goal_values"][1]))
    if a.baseline:
        seed_pt = tuple(map(float, a.baseline.split(",")))
    refs = [tuple(map(float, r.split("=", 1)[1].split(","))) for r in a.reference]
    seed_pts = [(float(r["goal_values"][0]), float(r["goal_values"][1])) for r in seed_recs
                if r.get("feasible") and r.get("goal_values")]
    if seed_pt and a.box_factor:
        # a box fixed by the baseline: it does not move with the rows' results, so repetitions and
        # methods compare in one measure; a point outside it scores nothing
        box = (a.box_factor * seed_pt[0], a.box_factor * seed_pt[1])
    else:
        box = table_ref([[(x, y) for x, y, _ in points_of(records(p))] for _, p in methods if p.is_file()]
                        + [seed_pts, refs])
    missing = [f"{label}={p}" for label, p in methods if not p.is_file()]
    if missing:
        import sys
        print("WARNING: no archive for " + ", ".join(missing), file=sys.stderr)
    rows = [dict(summarize(label, records(p), seed_pt, a.clock, box), **usage_of(p)) for label, p in methods if p.is_file()]
    # a label given more than once is a method's repetitions: each keeps its row (labelled r1, r2, ...)
    # and an aggregate row follows the last
    labels = [label for label, p in methods if p.is_file()]
    if len(set(labels)) < len(labels):
        seen, grouped = {}, []
        for label, r in zip(labels, rows):
            seen.setdefault(label, []).append(r)
        for label in dict.fromkeys(labels):
            reps = seen[label]
            if len(reps) == 1:
                grouped.append(reps[0])
                continue
            for i, r in enumerate(reps, 1):
                grouped.append(dict(r, method=f"{label} r{i}"))
            grouped.append(aggregate(label, reps))
        table_rows = grouped
    else:
        table_rows = rows
    box_note = ("seed area x clock box" if a.clock else
                f"box {box[0]:.1f} um2 x {box[1]:.1f} ps" + (f", {a.box_factor} x the baseline" if seed_pt and a.box_factor else ", the rows' largest"))
    lines = [f"| method | candidates | feasible | hypervolume ({box_note}) | best area um2 | min delay ps | candidates to 95% "
             "| model calls | tokens in / out | cost USD | agent hours |",
             "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for r in table_rows:
        lines.append(f"| {r['method']} | {r['records']} | {r['feasible']} ({r['feasible_fraction']}) | {r['hypervolume']} | "
                     f"{r['best_area_um2']} | {r['min_delay_ps']} | {r['calls_to_95pct']} | {r.get('model_calls')} | "
                     f"{r.get('input_tokens')} / {r.get('output_tokens')} | {r.get('cost_usd')} | {r.get('agent_hours')} |")
    if missing:
        lines += ["", "Missing archives: " + ", ".join(missing)]
    lines += ["", "| seed (tier 2) | feasible | area um2 | delay ps |", "| --- | --- | --- | --- |"]
    for r in seed_recs:
        g = r.get("goal_values") or [None, None]
        lines.append(f"| {r.get('seed_name')} | {r.get('feasible')} | {g[0]} | {g[1]} |")
    if a.reference:
        lines += ["", "| reference design | area um2 | delay ps |", "| --- | --- | --- |"]
        for ref in a.reference:
            label, vals = ref.split("=", 1)
            area, delay = vals.split(",")
            lines.append(f"| {label} | {area} | {delay} |")
    (out / "table_a.md").write_text("\n".join(lines) + "\n")
    (out / "table_a.json").write_text(json.dumps({"methods": table_rows, "seeds": [{k: r.get(k) for k in ("seed_name", "feasible", "goal_values")} for r in seed_recs],
                                                  "seed_point": seed_pt}, indent=1))
    print("\n".join(lines))
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(6, 4.5))
        for (label, p), r in zip([m for m in methods if m[1].is_file()], rows):
            label = r["method"] if len(set(labels)) < len(labels) else label
            pts = points_of(records(p))
            if pts:
                ax.scatter([q[0] for q in pts], [q[1] for q in pts], s=10, alpha=0.3)
                fr = r["front"]
                ax.plot([q[0] for q in fr], [q[1] for q in fr], marker="o", label=label)
        for r in seed_recs:
            g = r.get("goal_values") or [None, None]
            if r.get("feasible") and g[0] is not None:
                ax.scatter([g[0]], [g[1]], marker="s", s=50, color="black")
                ax.annotate(r.get("seed_name"), (g[0], g[1]), fontsize=7)
        for ref in a.reference:
            label, vals = ref.split("=", 1)
            area, delay = (float(x) for x in vals.split(","))
            ax.scatter([area], [delay], marker="*", s=120, color="red")
            ax.annotate(label, (area, delay), fontsize=8, color="red")
        if a.clock:
            ax.axhline(a.clock, linestyle=":", color="gray")
        ax.set_xlabel("area (um2)")
        ax.set_ylabel("delay (ps)")
        ax.legend(fontsize=8)
        fig.tight_layout()
        fig.savefig(out / "figure_1.png", dpi=150)
        print(f"figure {out / 'figure_1.png'}")
    except ImportError:
        print("matplotlib absent: no figure")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
