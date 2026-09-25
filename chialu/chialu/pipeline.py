"""The chain on one ALU run file (docs/demo-plan.md, docs/surrogate.md).

    python3 -m chialu.pipeline <target.yaml> --run-dir <dir> [--numeric <target.numeric.yaml>]
                               [--top 6] [--schemes 6] [--search-iterations 1]
                               [--no-llm] [--stage train|numeric|seeds|search] [--local]
                               [--surrogate-max-rounds K] [--surrogate-verify 24] [--surrogate-iterations 2000]

The stages, each writing under `<run-dir>/` (default: all four, in order):

1. `train`: the per-target XGBoost area/delay model (`chialu.surrogate_seeds --stage sample`): the space is
   counted and synthesized whole when small; else random declarations of the complete numeric space under
   random sharing schemes are rendered and synthesized at the run file's mapping through the cluster, and
   the regressors are trained and certified on fresh validation batches by the protocol of the run file's
   `search.extensions.calibration` (dataset, models, report under `<run-dir>/surrogate`).
2. `numeric`: the seeds from the model (`chialu.surrogate_seeds --stage search --stage seeds`): NSGA-II over
   the numeric run file's space per sharing scheme, scored by the trained model (the `chialu.eda.surrogate`
   node), the predicted front's points verified by synthesis (and the model refitted on them), and the
   measured front written as `front_*` plans into `<run-dir>/discovered.json`.
3. `seeds`: `adir seeds` renders and evaluates every seed of the search run (the front's plans) through the
   conformance, fault and synthesis gates. `--local` runs the nodes in this process.
4. `search`: `adir run` of the search run file for `--search-iterations` iterations (the LLM loop).

The database-sum estimate the numeric stage once searched (`chialu.eda.estimate`, calibrated on the
baseline) misjudged whole units at the evaluation's least-delay mapping by up to 3x; it is retired from
the chain and kept only as `--stage legacy_calibrate` / `legacy_numeric`. Its per-structure rows remain
features of the model (docs/surrogate.md).

`--no-llm` writes a copy of the run file without the review node (the
derived file, named by its content's hash, lands beside the run file, where its
relative paths hold; `derived_run_file`)
and uses it for the seeds and search stages, so the chain runs without
a model where none is wanted; the search stage then needs a model and
is skipped.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path


def derived_run_file(target: Path, no_llm: bool, synth_repeats: int = 5) -> Path:
    """Copy the target with an explicit repeat count for every synthesis node.
    No-model stages also drop review and discovery (`<name>.nollm.<sha>.yaml`);
    other stages use `<name>.pipeline.<sha>.yaml`, leaving the source target intact.
    Both copies stay beside the source so relative artifact paths (knowledge,
    role, task script, the domain library on sys.path) resolve as the target's do.

    `<sha>` is the first 12 hex digits of the derived text's SHA-256, so the
    name is a function of the content: concurrent pipelines (the repetitions of
    one target, started together) that derive the same text share one file and
    ones that derive different texts (another repeat count, an edited target)
    never overwrite each other's. The text goes to a unique temporary file in
    the same directory and is renamed into place, so a reader never sees a
    partly written file; an existing file with the same bytes is left alone."""
    import hashlib
    import os
    import tempfile
    import yaml
    d = yaml.safe_load(target.read_text())
    if no_llm:
        d = without_review(d)
    for node in d["adir"]["evaluate"]["nodes"].values():
        if node.get("node") in ("chialu.eda.synth_ppa", "chialu.eda.synth_unit"):
            node.setdefault("inputs", {})["repeats"] = synth_repeats
    text = yaml.safe_dump(d, sort_keys=False, width=200)
    sha = hashlib.sha256(text.encode()).hexdigest()[:12]
    out = target.with_name(f"{target.stem}.{'nollm' if no_llm else 'pipeline'}.{sha}.yaml")
    try:
        if out.read_text() == text:
            return out
    except OSError:
        pass
    fd, tmp = tempfile.mkstemp(prefix=f".{out.name}.", suffix=".tmp", dir=str(out.parent))
    try:
        with os.fdopen(fd, "w") as f:
            f.write(text)
        os.replace(tmp, out)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    return out


def without_review(d: dict) -> dict:
    """A run file's document without the review node, its constraint and
    feedback, and any discover role (in place; returned)."""
    a = d["adir"]
    nodes = a.get("evaluate", {}).get("nodes", {})
    for k in [k for k, v in nodes.items() if str((v or {}).get("node", "")).startswith("chialu.review")]:
        del nodes[k]
    a["constraints"] = [c for c in a.get("constraints", []) if not str(c.get("metric", "")).startswith("review.")]
    fb = a.get("evaluate", {}).get("feedback")
    if fb:
        a["evaluate"]["feedback"] = [f for f in fb if not str(f).startswith("review.")]
    s = a.get("search", {})
    if "seeds" in s:
        s["seeds"]["discover"] = 0
    s.pop("discover", None)
    if isinstance(s.get("models"), dict):
        s["models"].pop("discover", None)
    return d


def calibration_run_file(run_file: Path) -> Path:
    """A copy of the search run file whose seeds are the baseline plan
    alone (`<name>.calib.yaml` beside it)."""
    import yaml
    d = yaml.safe_load(run_file.read_text())
    s = d["adir"].setdefault("search", {})
    seeds = s.setdefault("seeds", {})
    seeds["generated"] = ["baseline"]
    seeds["discover"] = 0
    s.pop("discover", None)
    if isinstance(s.get("models"), dict):
        s["models"].pop("discover", None)
    stem = run_file.name.split(".nollm")[0].split(".pipeline")[0].removesuffix(".yaml")
    out = run_file.with_name(stem + ".calib.yaml")
    out.write_text(yaml.safe_dump(d, sort_keys=False, width=200))
    return out


def calibrated_numeric_file(numeric: Path, area_scale: float, delay_scale: float,
                            glue: dict | None = None) -> Path:
    """The numeric run file with the estimate node's scales, the
    target's glue and its context factors set (`<name>.numeric.cal.yaml`
    beside it). The glue is what the top adds around the structures (the
    OR of a mode's unit buses, the mode mux, the flag map), which no row
    of a module synthesized alone carries; the factors
    (`glue["factors"]`, {"<kind>/<family>": factor}) are what a unit of
    that kind and family costs where it stands against that row."""
    import yaml
    d = yaml.safe_load(numeric.read_text())
    nodes = d["adir"].get("evaluate", {}).get("nodes", {})
    for v in nodes.values():
        if str((v or {}).get("node", "")) == "chialu.eda.estimate":
            v.setdefault("inputs", {})["area_scale"] = round(float(area_scale), 4)
            v["inputs"]["delay_scale"] = round(float(delay_scale), 4)
            # a profile the tools refused carries a note alone: the inputs stay empty, and the
            # estimate reports the glue and the context as unmodeled rather than as zero
            if glue and (glue.get("mode") or glue.get("top")):
                v["inputs"]["glue_json"] = json.dumps({"mode": glue.get("mode") or {},
                                                       "top": glue.get("top") or 0.0})
            if glue and glue.get("factors"):
                v["inputs"]["context_json"] = json.dumps(glue["factors"])
    out = numeric.with_name(numeric.stem + ".cal.yaml")
    out.write_text(yaml.safe_dump(d, sort_keys=False, width=200))
    return out


def measure_glue(run_file: Path, numeric: Path, out: Path, jobs: int = 8, repeats: int = 5) -> dict:
    """The target's glue and context factors from a profile of its
    baseline seed, written to `out`: one cut per unit bus, mode bus and
    output of the rendered top, and every unit module measured alone
    beside them (`chialu.profile.measure_glue` over
    `chialu.profile.seed_units`), on the PDK, effort and clock the
    numeric run file's estimate node names. Returns {} with a `note`
    when the flow's tools are absent or the profile fails, and the
    estimate then reports the glue and the context as unmodeled."""
    import yaml
    from chialu import profile as PROF
    nd = yaml.safe_load(numeric.read_text())
    est = next((v.get("inputs") or {} for v in nd["adir"]["evaluate"]["nodes"].values()
                if str((v or {}).get("node", "")) == "chialu.eda.estimate"), {})
    clock = (yaml.safe_load(run_file.read_text())["adir"]["variables"].get("clock_ps") or {}).get("fixed") or 2000
    try:
        text, top, _spec = PROF.seed_of(run_file)
        units = PROF.seed_units(run_file)
        g = PROF.measure_glue(text, top, est.get("pdk", "nangate45"), int(clock), est.get("effort", "medium"),
                              jobs, units=units, repeats=repeats)
    except Exception as e:  # noqa: BLE001 - a host without the flow's tools calibrates without the glue
        g = {"note": f"{type(e).__name__}: {str(e)[:160]}"}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(g, indent=1))
    return g


def default_declaration(ctx, manifest) -> dict:
    """The declaration the estimate node reads (`decl.core` nested by
    slot and index) at the instance's defaults: every structure's family
    and choices from generators.families_of."""
    from chialu.modules.generators import families_of
    decl: dict = {}
    for base, (fam, pins) in families_of(ctx, manifest).items():
        d = decl
        for part in base.split(".")[1:]:
            d = d.setdefault(part, {})
        d["family"] = fam
        for k, v in (pins or {}).items():
            dd = d
            ks = str(k).split(".")
            for part in ks[:-1]:
                dd = dd.setdefault(part, {})
            dd[ks[-1]] = v
    return decl


def scheme_plans(run_file: Path, run: Path, numeric: Path, keep: int, level: str) -> tuple:
    """([(name, plan, estimate)], enumerated, priced) of the sharing
    schemes the numeric stage runs under: every scheme
    chialu.plans.sharing_schemes enumerates for the unit, each priced by
    the estimate node at the instance's default families (under the
    calibrated scales), the non-dominated ones by area and delay kept,
    spread to `keep` along the front (the rest of `keep` filled by
    area)."""
    import yaml
    import chialu.priors  # noqa: F401  the priors the run file names
    from adir.instance import load
    from adir.registry import underlying
    from chialu import eda
    from chialu.modules.generators import spec_of
    from chialu.plans import sharing_schemes
    from chialu.targets import derive
    inst = load(str(run_file), run_dir_override=str(run))
    ctx = inst.ctx(run_dir=run)
    spec = spec_of(ctx)
    manifest = derive.seed_alu_text(spec, None).structures
    decl = default_declaration(ctx, manifest)
    files = {"spec.json": json.dumps(spec)}
    nd = yaml.safe_load(numeric.read_text())
    est_in = next((v.get("inputs") or {} for v in nd["adir"]["evaluate"]["nodes"].values()
                   if str((v or {}).get("node", "")) == "chialu.eda.estimate"), {})
    pdk, effort = est_in.get("pdk", "nangate45"), est_in.get("effort", "medium")
    ka, kd = float(est_in.get("area_scale", 1.0)), float(est_in.get("delay_scale", 1.0))
    glue_json = str(est_in.get("glue_json") or "")      # the calibrated file's; a scheme's delay carries it too
    context_json = str(est_in.get("context_json") or "")
    def admits(sid: str, family: str) -> bool:
        st = manifest.get(sid)
        b = inst.bindings.get(f"core.{st.slot}.{st.index}.family") if st is not None else None
        if b is None:
            return False
        return b.value == family if b.time == "fixed" else b.domain.contains(family)

    cands = list(sharing_schemes(manifest, level, admits))
    priced = []
    for name, plan in cands:
        r = underlying(eda.estimate)(files, decl, pdk, effort, ka, kd, json.dumps(plan), glue_json, context_json)
        if r.get("ok") and r.get("area_um2") and r.get("delay_ps"):
            priced.append((name, plan, {"area_um2": r["area_um2"], "delay_ps": r["delay_ps"], "coverage": r.get("coverage")}))
    front = [x for x in priced if not any(o[2]["area_um2"] <= x[2]["area_um2"] and o[2]["delay_ps"] <= x[2]["delay_ps"]
                                          and (o[2]["area_um2"], o[2]["delay_ps"]) != (x[2]["area_um2"], x[2]["delay_ps"])
                                          for o in priced)]
    front.sort(key=lambda x: (x[2]["area_um2"], x[2]["delay_ps"]))
    seen_points, dedup = set(), []
    for x in front:                                  # one scheme per estimated point (many schemes price alike)
        pt = (x[2]["area_um2"], x[2]["delay_ps"])
        if pt not in seen_points:
            seen_points.add(pt)
            dedup.append(x)
    chosen = dedup if len(dedup) <= keep else [dedup[round(i * (len(dedup) - 1) / (keep - 1))] for i in range(keep)]
    if len(chosen) < keep:
        rest = sorted((x for x in priced if x not in chosen), key=lambda x: (x[2]["area_um2"], x[2]["delay_ps"]))
        for x in rest:
            pt = (x[2]["area_um2"], x[2]["delay_ps"])
            if pt not in seen_points:
                seen_points.add(pt)
                chosen.append(x)
            if len(chosen) >= keep:
                break
    return chosen, len(cands), len(priced)


def scheme_numeric_file(numeric: Path, k: int, plan: dict) -> Path:
    """The numeric run file of one scheme: the (calibrated) file with the
    estimate node's `plan_json` set (`<name>.numeric.s<k>.cal.yaml`)."""
    import yaml
    d = yaml.safe_load(numeric.read_text())
    for v in d["adir"].get("evaluate", {}).get("nodes", {}).values():
        if str((v or {}).get("node", "")) == "chialu.eda.estimate":
            v.setdefault("inputs", {})["plan_json"] = json.dumps(plan)
    stem = numeric.name.split(".numeric")[0]
    out = numeric.with_name(f"{stem}.numeric.s{k}.cal.yaml")
    out.write_text(yaml.safe_dump(d, sort_keys=False, width=200))
    return out


def seed_goal(run: Path, name: str):
    """(feasible, goal_values) of a seed's record in a run's archive, or None."""
    f = run / "results_db.jsonl"
    if not f.is_file():
        return None
    for line in f.read_text().splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("seed_name") == name or r.get("candidate_id") == f"seed:{name}":
            return bool(r.get("feasible")), r.get("goal_values")
    return None


def sh(cmd: list, log: Path, timeout: int | None = None) -> int:
    """Run a command, its output appended to `log`, and return its code."""
    with log.open("a") as f:
        f.write(f"\n$ {' '.join(cmd)}\n")
        f.flush()
        t0 = time.time()
        r = subprocess.run(cmd, stdout=f, stderr=subprocess.STDOUT, timeout=timeout)
        f.write(f"[exit {r.returncode} after {time.time() - t0:.0f}s]\n")
    return r.returncode


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--synth-repeats", type=int, default=3)
    ap.add_argument("--numeric", help="the numeric run file (default: <target>.numeric.yaml beside the target)")
    ap.add_argument("--numeric-iterations", type=int, default=200)
    ap.add_argument("--numeric-backend", default=None, help="nsga2 (the file's default) or smac")
    ap.add_argument("--top", type=int, default=6, help="front points kept as seeds")
    ap.add_argument("--schemes", type=int, default=6, help="sharing schemes the numeric stage runs under (0: none, the unshared "
                                                          "structure set alone)")
    ap.add_argument("--sharing-level", default="natural", choices=("natural", "all"),
                    help="the schemes enumerated: per kind none/all/per mode/per lane, or every set partition")
    ap.add_argument("--search-iterations", type=int, default=1)
    ap.add_argument("--no-llm", action="store_true")
    ap.add_argument("--local", action="store_true", help="run the nodes in this process (no cluster)")
    ap.add_argument("--resume", action="store_true",
                    help="continue the search from its last checkpoint to --search-iterations in all; the earlier "
                         "stages stand as they are unless --stage names them")
    ap.add_argument("--search-seed", type=int, default=None,
                    help="the search's random seed (adir run --seed): one per repetition; a resumed run keeps its own")
    ap.add_argument("--surrogate-max-rounds", type=int, default=None,
                    help="validation rounds of the surrogate's protocol (default: the run file's "
                         "search.extensions.calibration.ranking.max_rounds)")
    ap.add_argument("--surrogate-verify", type=int, default=100, help="predicted-front points verified by synthesis")
    ap.add_argument("--surrogate-inflight", type=int, default=50)
    ap.add_argument("--surrogate-iterations", type=int, default=2000, help="NSGA-II predictions per scheme")
    ap.add_argument("--stage", action="append",
                    choices=("train", "numeric", "seeds", "search", "legacy_calibrate", "legacy_numeric", "surrogate"),
                    help="run these stages alone (default: train, numeric, seeds, search). legacy_calibrate and "
                         "legacy_numeric are the retired database-sum estimate; surrogate is train + numeric at once")
    a = ap.parse_args(argv)
    target = Path(a.target).resolve()
    run = Path(a.run_dir).resolve()
    run.mkdir(parents=True, exist_ok=True)
    # an earlier invocation on this run directory (the seeds stage, then the search in a second command, or a
    # resumed search): its stages' records stand unless this one reruns them, and its repeat count must match
    previous = json.loads((run / "pipeline.json").read_text()) if (run / "pipeline.json").is_file() else None
    if previous is not None and previous.get("synth_repeats", 1) != a.synth_repeats:
        raise ValueError("cannot resume with a different synthesis repeat count; use a fresh run directory"
                         if a.resume else
                         f"{run} holds a pipeline run with synth_repeats {previous.get('synth_repeats', 1)}, not "
                         f"{a.synth_repeats}; use a fresh run directory")
    log = run / "pipeline.log"
    stages = a.stage or (["search"] if a.resume else ["train", "numeric", "seeds", "search"])
    if "surrogate" in stages:
        stages = [x for x in stages if x != "surrogate"] + ["train", "numeric"]
    if a.resume and a.search_seed is None and (run / "pipeline.json").is_file():
        a.search_seed = (json.loads((run / "pipeline.json").read_text()).get("stages", {}).get("search") or {}).get("seed")
    adir = [sys.executable, "-m", "adir.cli"]
    local = ["--local"] if a.local else []
    run_file = derived_run_file(target, a.no_llm, a.synth_repeats)
    numeric = Path(a.numeric).resolve() if a.numeric else target.with_name(target.stem + ".numeric.yaml")
    # the derived file this run used, kept in the run directory as a record (the adir commands read the one
    # beside the target, where its relative paths resolve)
    shutil.copyfile(run_file, run / "run_file.yaml")
    report = {"target": str(target), "run_file": str(run_file), "run_dir": str(run), "synth_repeats": a.synth_repeats,
              "argv": [sys.executable, "-m", "chialu.pipeline"] + list(sys.argv[1:] if argv is None else argv),
              "stages": {}}
    if previous is not None:
        report["stages"] = previous.get("stages", {})   # the earlier invocations' stages stand
    report["invocations"] = list((previous or {}).get("invocations") or []) + [
        {"argv": report["argv"], "stages": stages, "exit": None, "time": time.time()}]
    print(f"[pipeline] {target.name} -> {run} (run file {run_file.name})")

    if "legacy_calibrate" in stages:
        crun = run / "calibrate"
        if crun.exists():
            shutil.rmtree(crun)
        cal = {"area_scale": 1.0, "delay_scale": 1.0}
        if not numeric.is_file():
            cal["note"] = f"no numeric run file {numeric}"
        else:
            rc = sh(adir + ["seeds", str(calibration_run_file(run_file)), "--run-dir", str(crun)] + local, log)
            # the glue first, so the estimate the scales are fitted against already carries it
            glue = measure_glue(run_file, numeric, crun / "glue.json", repeats=a.synth_repeats)
            cal["glue"] = {k: v for k, v in glue.items() if k not in ("cuts", "modules")}
            with_glue = calibrated_numeric_file(numeric, 1.0, 1.0, glue)
            rc2 = sh(adir + ["seeds", str(with_glue), "--run-dir", str(crun / "estimate")] + local, log)
            measured, estimated = seed_goal(crun, "baseline"), seed_goal(crun / "estimate", "baseline")
            cal.update({"exit": rc, "estimate_exit": rc2, "measured": measured, "estimated": estimated,
                        "synthesis_records": str(crun / "results_db.jsonl")})
            # the baseline's synthesized area and delay stand whether or not a soft constraint (the review's
            # score, the clock) marks the seed infeasible; only missing numbers leave the scales at 1.0
            have = lambda g: bool(g) and bool(g[1]) and len(g[1]) >= 2 and all(isinstance(x, (int, float)) and x for x in g[1][:2])
            if have(measured) and have(estimated):
                cal["area_scale"] = round(measured[1][0] / estimated[1][0], 4)
                cal["delay_scale"] = round(measured[1][1] / estimated[1][1], 4)
                cal["file"] = str(calibrated_numeric_file(numeric, cal["area_scale"], cal["delay_scale"], glue))
            else:
                cal["note"] = "the baseline was not measured or not estimated; the scales stay 1.0"
                stale = numeric.with_name(numeric.stem + ".cal.yaml")
                if stale.is_file():
                    stale.unlink()             # an earlier calibration must not stand in for this one
        report["stages"]["calibrate"] = cal
        g = cal.get("glue") or {}
        print(f"[pipeline] calibrate: measured {cal.get('measured')}, estimated {cal.get('estimated')}; "
              f"area x{cal['area_scale']}, delay x{cal['delay_scale']}"
              + (f"; glue {g.get('top')} ps at the top, {g.get('mode')} per mode" if g.get("mode")
                 else f"; no glue ({g.get('note', 'not measured')})" if g else "")
              + (f"; {len(g['factors'])} context factors" if g.get("factors") else "")
              + (f" ({cal['note']})" if cal.get("note") else ""))

    if "legacy_numeric" in stages:
        if not numeric.is_file():
            print(f"[pipeline] numeric: no run file {numeric}")
            return 2
        cal_file = numeric.with_name(numeric.stem + ".cal.yaml")
        numeric_used = cal_file if cal_file.is_file() else numeric
        nrun = run / "numeric"
        if nrun.exists():
            shutil.rmtree(nrun)
        nrun.mkdir(parents=True)
        # the sharing schemes the search runs under: enumerated for the unit and priced at the default families;
        # each gets its own numeric run and the fronts are merged
        if a.schemes > 0:
            chosen, n_all, n_priced = scheme_plans(run_file, run, numeric_used, a.schemes, a.sharing_level)
            print(f"[pipeline] schemes: {n_all} enumerated, {n_priced} priced, {len(chosen)} kept: "
                  + "; ".join(f"{n} ({e['area_um2']:.0f} um2, {e['delay_ps']:.0f} ps)" for n, _p, e in chosen))
        else:
            chosen, n_all, n_priced = [("unshared", None, {})], 0, 0
        per_scheme = max(30, a.numeric_iterations // max(1, len(chosen)))
        runs, rc = [], 0
        for k, (name, plan, est) in enumerate(chosen, 1):
            sdir = nrun / f"s{k}_{name}"[:80]
            file_k = scheme_numeric_file(numeric_used, k, plan) if plan is not None else numeric_used
            cmd = adir + ["run", str(file_k), "--run-dir", str(sdir), "--iterations", str(per_scheme)] + local
            if a.numeric_backend:
                cmd += ["--backend", a.numeric_backend]
            rc_k = sh(cmd, log)
            rc = rc or rc_k
            (sdir / "scheme.json").write_text(json.dumps({"name": name, "plan": plan, "estimate": est, "run_file": str(file_k)}, indent=1))
            n_k = sum(1 for _ in (sdir / "results_db.jsonl").open()) if (sdir / "results_db.jsonl").is_file() else 0
            runs.append({"scheme": name, "exit": rc_k, "records": n_k, "estimate": est})
        n_rec = sum(r["records"] for r in runs)
        rc2 = sh([sys.executable, "-m", "chialu.front_seeds", str(run_file), "--numeric-run", str(nrun),
                  "--run-dir", str(run), "--top", str(a.top)], log)
        plans = json.loads((run / "discovered.json").read_text()).get("plans", {}) if (run / "discovered.json").is_file() else {}
        report["stages"]["numeric"] = {"exit": rc, "records": n_rec, "front_seeds_exit": rc2, "run_file": str(numeric_used),
                                       "schemes": runs, "schemes_enumerated": n_all, "schemes_priced": n_priced,
                                       "front": sorted(k for k in plans if k.startswith("front_"))}
        print(f"[pipeline] numeric ({numeric_used.name}): exit {rc}, {n_rec} records over {len(runs)} scheme(s); "
              f"front seeds {report['stages']['numeric']['front']}")

    surrogate_cmd = [sys.executable, "-m", "chialu.surrogate_seeds", str(target), "--run-dir", str(run),
                     "--synth-repeats", str(a.synth_repeats), "--numeric", str(numeric), "--verify", str(a.surrogate_verify), "--inflight", str(a.surrogate_inflight),
                     "--top", str(a.top), "--iterations", str(a.surrogate_iterations), "--schemes", str(max(1, a.schemes)),
                     "--sharing-level", a.sharing_level] + local \
        + (["--max-rounds", str(a.surrogate_max_rounds)] if a.surrogate_max_rounds is not None else [])

    def surrogate_report():
        f = run / "surrogate" / "report.json"
        return json.loads(f.read_text()) if f.is_file() else {}

    def missing(stage: str, what: str, first: str) -> int:
        print(f"[pipeline] {stage}: {what} is missing in {run}; run `--stage {first}` first "
              f"(or name both stages in one invocation)", file=sys.stderr)
        report["stages"][stage] = {"exit": 2, "error": f"missing {what}; run --stage {first} first"}
        report["exit"] = report["invocations"][-1]["exit"] = 2
        (run / "pipeline.json").write_text(json.dumps(report, indent=1, default=str))
        return 2

    def listed_seeds(f: Path) -> list:
        import yaml
        try:
            return list(((yaml.safe_load(f.read_text()).get("adir") or {}).get("search") or {}).get("seeds", {}).get("generated") or [])
        except Exception:  # noqa: BLE001
            return []

    # gating: each stage checks what the one before it writes, unless that stage runs in this invocation
    if "numeric" in stages and "train" not in stages and not (run / "surrogate" / "model.pkl").is_file() \
            and ((surrogate_report().get("sample") or {}).get("mode") != "exhaustive"):
        return missing("numeric", "the trained model (surrogate/model.pkl)", "train")
    fronts = {}
    if (run / "discovered.json").is_file():
        fronts = {k: v for k, v in (json.loads((run / "discovered.json").read_text()).get("plans") or {}).items()}
    if "seeds" in stages and "numeric" not in stages and not fronts and not listed_seeds(run_file):
        return missing("seeds", "the numeric stage's seeds (discovered.json front_* plans)", "numeric")
    if "search" in stages and "seeds" not in stages:
        db = run / "results_db.jsonl"
        has_seeds = db.is_file() and any(json.loads(l).get("is_seed") for l in db.read_text().splitlines() if l.strip())
        if not has_seeds:
            return missing("search", "the evaluated seeds (results_db.jsonl seed records)", "seeds")

    if "train" in stages:
        # the model: whole units sampled over the complete space and synthesized at the run file's mapping,
        # XGBoost area/delay regressors certified on fresh validation batches (search.extensions.calibration)
        rc = sh(surrogate_cmd + ["--stage", "sample"], log)
        rep = surrogate_report()
        report["stages"]["train"] = {"exit": rc, "space": rep.get("space"), "sample": rep.get("sample"),
                                     "model": rep.get("model")}
        print(f"[pipeline] train: exit {rc}; model {rep.get('model')}")

    if "numeric" in stages:
        # the seeds: NSGA-II over the trained model's predictions (the chialu.eda.surrogate node) per sharing
        # scheme, the predicted front verified by synthesis, the measured front written as front_* plans
        rc = sh(surrogate_cmd + ["--stage", "search", "--stage", "seeds"], log)
        rep = surrogate_report()
        report["stages"]["numeric"] = {"exit": rc, "seeds": rep.get("seeds")}
        print(f"[pipeline] numeric: exit {rc}; seeds " + "; ".join(
            f"{o['seed']} {o['area_um2']:.0f} um2 / {o['delay_ps']:.0f} ps" for o in rep.get("seeds") or []))

    if "seeds" in stages:
        rc = sh(adir + ["seeds", str(run_file), "--run-dir", str(run)] + local, log)
        recs = []
        if (run / "results_db.jsonl").is_file():
            recs = [json.loads(l) for l in (run / "results_db.jsonl").read_text().splitlines() if l.strip()]
        seeds = {r.get("seed_name"): {"feasible": r.get("feasible"), "goal": r.get("goal_values")}
                 for r in recs if r.get("is_seed") or r.get("seed_name")}
        report["stages"]["seeds"] = {"exit": rc, "seeds": seeds}
        print(f"[pipeline] seeds: exit {rc}; " + "; ".join(f"{k}: {'feasible' if v['feasible'] else 'infeasible'} {v['goal']}"
                                                          for k, v in seeds.items()))

    if "search" in stages:
        # the report so far on disk before the search, so a search killed partway leaves its seed and the
        # earlier stages behind for --resume
        report["stages"]["search"] = {"exit": None, "iterations": a.search_iterations, "seed": a.search_seed,
                                      "legs": ((report["stages"].get("search") or {}).get("legs") or []) if a.resume else []}
        (run / "pipeline.json").write_text(json.dumps(report, indent=1, default=str))
        if a.no_llm:
            report["stages"]["search"] = "skipped (--no-llm: the rewrite needs a model)"
        else:
            # --resume continues from the search's last checkpoint (one per iteration); --search-iterations is the
            # run's total, so the same command finishes a stopped run and a larger number extends a finished one
            rc = sh(adir + ["run", str(run_file), "--run-dir", str(run), "--iterations", str(a.search_iterations)]
                    + (["--resume"] if a.resume else []) + (["--seed", str(a.search_seed)] if a.search_seed is not None else [])
                    + local, log)
            legs = ((report["stages"].get("search") or {}).get("legs") or []) if a.resume else []
            legs.append({"exit": rc, "iterations": a.search_iterations, "resume": a.resume, "time": time.time()})
            report["stages"]["search"] = {"exit": rc, "iterations": a.search_iterations, "seed": a.search_seed, "legs": legs}
        print(f"[pipeline] search: {report['stages']['search']}")

    rc = stages_exit(report["stages"], stages)
    report["exit"] = rc
    report["invocations"][-1]["exit"] = rc
    (run / "pipeline.json").write_text(json.dumps(report, indent=1, default=str))
    print(f"[pipeline] report {run / 'pipeline.json'}; log {log}; exit {rc}")
    return rc


# the exit codes a stage's record carries: its command's and its helpers'
_EXIT_KEYS = ("exit", "estimate_exit", "front_seeds_exit")


def stages_exit(records: dict, ran) -> int:
    """The pipeline's exit code: the largest exit code of the stages this
    invocation ran (a signal's negative code counts as 128 + the signal, as
    a shell reports it), so a failed stage makes the pipeline fail. A stage
    that did not run in this invocation (a resumed run's earlier legs) does
    not count; a skipped search (a string record) is no failure."""
    names = {"legacy_calibrate": "calibrate", "legacy_numeric": "numeric"}
    codes = [0]
    for stage in dict.fromkeys(names.get(x, x) for x in ran):
        rec = records.get(stage)
        if not isinstance(rec, dict):
            continue
        for k in _EXIT_KEYS:
            v = rec.get(k)
            if isinstance(v, int) and not isinstance(v, bool):
                codes.append(128 - v if v < 0 else v)
    return max(codes)


if __name__ == "__main__":
    sys.exit(main())
