"""Table A progress: per run the iterations done, candidates, feasible, the best area and delay among
feasible candidates (seeds excluded and included), model calls and cost. Writes a markdown file."""
import json, glob, sys, time, statistics
from pathlib import Path
R = Path("$A3EVAL/3rdparty/chialu/run")
out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("$A3EVAL/results/tablea_status.md")
MAXIT = int(sys.argv[2]) if len(sys.argv) > 2 else None     # count only candidates of iterations <= MAXIT
MEASUREMENTS = Path(__file__).resolve().parents[2] / "measurements" / "median5"
def measured(name):
    return json.loads((MEASUREMENTS / (name + ".json")).read_text())["repeats5"]
MEASUREMENTS = Path(__file__).resolve().parents[2] / "measurements" / "median5"
def measured(name):
    return json.loads((MEASUREMENTS / (name + ".json")).read_text())["repeats5"]
BASE = {name: (measured(name)["area_um2"], measured(name)["abc_delay_ps"])
        for name in ("int_subword_alu", "fp_alu_cmp", "fp_alu_cmp_hf")}
def reference(label, name):
    r = measured(name)
    return f"{label} {r['area_um2']:,.3f} / {r['abc_delay_ps']:,.2f}"
REF = {"fp_alu_cmp": "; ".join((reference("FPnew MERGED", "fpnew_fpnew_merged_alu_core"),
                               reference("PARALLEL", "fpnew_fpnew_parallel_alu_core"),
                               reference("TransDot", "transdot_transdot_merged_alu_core"))),
       "fp_alu_cmp_hf": reference("HardFloat", "hardfloat_alu_core"), "int_subword_alu": "none"}
def measured5(record):
    value = ((record.get("measurements") or {}).get("synth_ppa") or {}).get("value") or {}
    return value.get("repeats") == 5 and value.get("successful_runs") == 5
def hv(pts, box):
    pts = sorted(p for p in pts if p[0] < box[0] and p[1] < box[1]); area, ymin = 0.0, box[1]
    for x, y in pts:
        if y < ymin: area += (box[0] - x) * (ymin - y); ymin = y
    return area / (box[0] * box[1])
lines = [f"# Table A {'at ' + str(MAXIT) + ' iterations' if MAXIT else 'progress'} ({time.strftime('%Y-%m-%d %H:%M')})", "",
         "Per run: candidates (seeds excluded), feasible, the best feasible area and delay found by the method "
         "(seeds excluded), the hypervolume of all feasible points including seeds in the box 1.2x the baseline, "
         "model calls and cost. PPA/HV include only five-run measurements; historical single-run rows are excluded. "
         "Baseline receipts: measurements/median5/<target>.json.", ""]
for t in BASE:
    box = (1.2 * BASE[t][0], 1.2 * BASE[t][1])
    lines += [f"## {t} (baseline {BASE[t][0]:,} / {BASE[t][1]:,}; references: {REF[t]})", "",
              "| method | rep | iters | cands | feasible | best area | best delay | HV | calls | cost $ |",
              "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |"]
    for m in ("chialu", "best_of_n", "beam_search", "adaevolve", "plain"):
        hvs = []
        for k in (1, 2, 3):
            d = R / f"exp.{t}.{m}.r{k}"
            db = d / "results_db.jsonl"
            if not db.is_file():
                lines.append(f"| {m} | {k} | – | – | – | – | – | – | – | – |"); continue
            recs = [json.loads(l) for l in db.read_text().splitlines() if l.strip()]
            kids = [r for r in recs if not r.get("is_seed")]
            if MAXIT is not None:
                kids = [r for r in kids if (r.get("call") if r.get("call") is not None else r.get("iteration") or 0) <= MAXIT]
            feas = [r["goal_values"] for r in kids if measured5(r) and r.get("feasible") and r.get("goal_values") and None not in r["goal_values"][:2]]
            allf = feas + [r["goal_values"] for r in recs if r.get("is_seed") and measured5(r) and r.get("feasible") and r.get("goal_values") and None not in r["goal_values"][:2]]
            h = hv([tuple(g[:2]) for g in allf], box); hvs.append(h)
            calls, cost = 0, 0.0
            if (d / "llm_calls.jsonl").is_file():
                for l in (d / "llm_calls.jsonl").read_text().splitlines():
                    try: r = json.loads(l)
                    except ValueError: continue
                    calls += 1; cost += float((r.get("usage") or {}).get("cost_usd") or 0)
            else:
                for c in d.glob("call_*/usage.json"):
                    calls += 1; cost += float(json.loads(c.read_text()).get("cost_usd") or 0)
            ck = [int(p.name.split("_")[1]) + 1 for p in (d / "skydiscover" / "checkpoints").glob("checkpoint_*")] if (d / "skydiscover").is_dir() else []
            iters = max(ck) if ck else len(list(d.glob("call_*")))
            if MAXIT is not None:
                iters = min(iters, MAXIT)
            ba = min((g[0] for g in feas), default=None); bd = min((g[1] for g in feas), default=None)
            lines.append(f"| {m} | {k} | {iters} | {len(kids)} | {len(feas)} | {ba if ba is None else round(ba, 1)} | "
                         f"{bd if bd is None else round(bd, 1)} | {h:.4f} | {calls} | {cost:.2f} |")
        if hvs:
            sd = statistics.stdev(hvs) if len(hvs) > 1 else 0.0
            lines.append(f"| **{m} mean** | | | | | | | **{statistics.mean(hvs):.4f} +- {sd:.4f}** | | |")
    lines.append("")
out.write_text("\n".join(lines) + "\n")
print(out)
