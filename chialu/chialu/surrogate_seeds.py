"""Seeds from a whole-unit PPA surrogate: sample, synthesize, certify, search, verify.

    python3 -m chialu.surrogate_seeds <target.yaml> --run-dir <dir> [--numeric <target.numeric.yaml>]
        [--target-rho R] [--margin M] [--confidence C] [--initial-train N] [--max-initial 1000]
        [--test-size N] [--max-rounds K] [--cv-floor 3] [--exhaustive-below N]
        [--verify 24] [--schemes 6] [--iterations 3000] [--top 8]
        [--inflight 50] [--render-jobs 8] [--seed 0] [--prefix front] [--local]

The numeric stage's estimate sums rows of modules synthesized alone and
misjudges a whole unit at the evaluation's least-delay mapping; this
stage learns the whole unit from its own syntheses instead. It follows
the protocol and the model input decided by the earlier study
($CHIALU_HOME/coeff: xgb/report.md, varlen/report.md,
calibration.py, xplan_features.py; docs/surrogate.md), under
`<run-dir>/surrogate/`:

1. the space: the numeric run file's searched declaration (every
   `core.*` family and choice, nested slots and pins included) times
   the sharing schemes `chialu.plans.sharing_schemes` enumerates for
   the seed; its size is counted (`count.json`, an upper bound).
   A space no larger than `exhaustive_below` is synthesized whole and
   ranked by measurement; no model is needed.
2. the sample, a stream of random declarations
   (`adir.backends.numeric.sample_declaration`), each under a random
   scheme and made consistent with it (`surrogate_features.scheme_repair`),
   turned into a plan as `chialu.front_seeds` does (`realize`), rendered
   through the seed's `plan_seed` and checked by the declaration node
   in `--render-jobs` forked processes (a point the seed refuses is
   recorded with its reason and replaced by the next), then evaluated by
   the search run file's nodes (lint, conformance, the fault gate where
   the file has one, yosys_stat, synth_ppa at its clock and mapping)
   with the seed-relative synthesis gates removed
   (`<name>.surrogate.yaml` beside the run file), `--inflight` at a
   time through the cluster, pinned to the driver's node (whose workers
   import this checkout). Every row lands in `dataset.jsonl`, resumable.
   The model trains on these rows alone, never on another archive.
3. certification, the incremental protocol: the first `initial_train`
   measured points train the models, the next `test_size` (a fresh
   validation set, sized by sampling theory: Fisher z, the population
   size does not enter) measure them; a metric passes when the lower
   confidence bound of its Spearman rho clears `target_rho`, or when it
   barely varies (coefficient of variation under `cv_floor` percent, the
   designs being about equal on it). On a failure the validation set
   joins the training set and a new one is drawn, up to `max_rounds`.
   The knobs are the run file's `search.extensions.calibration`
   (`exhaustive_below`, `ranking.{target_rho, margin, confidence,
   rows_per_column, initial_train, test_size, increment, max_rounds,
   cv_floor_pct}`), each overridable on the command line.
4. the model: XGBoost regressors of log area and log delay (3.2.0,
   depth 5, 400 trees, learning rate 0.05) over `rows + plan + one-hot`
   (chialu.surrogate_features): the estimate's own area/delay/coverage,
   the database row of every structure aligned by structure id, their
   order statistics, the sharing scheme's rules, groups and union
   geometry, and a one-hot of every declared variable. Saved as
   `model.pkl` and `ml/models/<pdk>.<alu>.pkl`.
5. the search: the numeric stage's NSGA-II (`adir run` of the numeric
   run file, backend nsga2) with the estimate node replaced by the
   surrogate node `chialu.eda.surrogate` (`<name>.numeric.surrogate.s<k>.yaml`
   beside the numeric file, a copy in the run directory), one run of
   `--iterations` predictions per sharing scheme, as the numeric stage
   runs one per scheme; the `--schemes` schemes are those of the
   measured front and those whose points reach the predicted front.
   `--verify` points of the merged predicted front (spread along it,
   then the next layers) are synthesized.
6. the seeds: the non-dominated points of every measured feasible row
   (sample, validation and verification), at most `--top` spread along
   the front, written fastest first into `<run-dir>/discovered.json`
   as plans named `<prefix>_<k>` (the earlier `<prefix>_*` plans
   replaced), as `chialu.front_seeds` writes the numeric front.
"""
from __future__ import annotations

import argparse
import json
import math
import random
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]


# ------------------------------------------------------------------ run files and the space

SIM_NODES = ("chialu.eda.conformance", "chialu.eda.fault", "chialu.eda.checker_gen")


def surrogate_run_file(run_file: Path, gates: str = "full", synth_repeats: int = 5) -> Path:
    """The search run file without the review node (pipeline.without_review),
    without synth_unit and with every seed-relative gate dropped, so every
    point is synthesized whole (`<name>.surrogate.yaml` beside it). With
    `gates="sample"` the simulation gates go too (conformance, the fault
    gate and its checker; `<name>.surrogate_sample.yaml`): a training
    point needs its synthesized area and delay, which no simulation
    changes, and the fault gate alone costs four minutes and six slots a
    point. Every point that becomes a seed is evaluated with the full gates."""
    import yaml
    from chialu.pipeline import without_review
    d = without_review(yaml.safe_load(run_file.read_text()))
    a = d["adir"]
    nodes = a["evaluate"]["nodes"]
    nodes["synth_ppa"].setdefault("inputs", {})["repeats"] = synth_repeats
    if gates == "sample":
        # the agent's reports (summary, critical path, area by hierarchy) cost a fourth, hierarchy-kept
        # mapping, about 40% of the node's time, and never touch the metric; a training point is read
        # for its area, delay and cells alone
        nodes["synth_ppa"]["inputs"]["report"] = False
    drop =("chialu.eda.synth_unit",) + (SIM_NODES if gates == "sample" else ())
    gone = [k for k, v in nodes.items() if str((v or {}).get("node", "")) in drop]
    for k in gone:
        del nodes[k]
    for v in nodes.values():
        if v and v.get("when"):
            w = [c for c in v["when"] if "seed." not in str(c) and not any(g in str(c) for g in gone)]
            if w:
                v["when"] = w
            else:
                v.pop("when")
    a["constraints"] = [c for c in a.get("constraints", []) if str(c.get("metric", "")).split(".")[0] not in gone]
    fb = a["evaluate"].get("feedback")
    if fb:
        a["evaluate"]["feedback"] = [f for f in fb if str(f).split(".")[0] not in gone]
    s = a.setdefault("search", {})
    s.setdefault("seeds", {})["generated"] = []
    s["seeds"]["discover"] = 0
    suffix = ".surrogate.yaml" if gates == "full" else ".surrogate_sample.yaml"
    out = run_file.with_name(run_file.stem.replace(".nollm", "") + suffix)
    out.write_text(yaml.safe_dump(d, sort_keys=False, width=200))
    return out


# ------------------------------------------------------------------ the space

def log10_count(num) -> float:
    """log10 of the number of declarations of a numeric instance: an upper
    bound (a conditional child multiplies in under the parent values that
    activate it; member conditions are not applied)."""
    children: dict = {}
    top = []
    for v in num.variable_order():
        b = num.bindings.get(v.name)
        if b is None or b.time != "search":
            continue
        pb = num.bindings.get(v.when[0]) if v.when is not None else None
        if pb is not None and pb.time == "search":
            children.setdefault(v.when[0], []).append(v)
        else:
            top.append(v)

    def lc(v) -> float:
        b = num.bindings[v.name]
        try:
            members = list(b.domain.members())
        except Exception:  # noqa: BLE001 - a continuous domain counts as 1000 values
            return 3.0
        terms = [sum(lc(c) for c in children.get(v.name, []) if c.condition_holds(m)) for m in members]
        mx = max(terms) if terms else 0.0
        return mx + math.log10(sum(10 ** (t - mx) for t in terms)) if terms else 0.0
    return sum(lc(v) for v in top)


def enumerate_declarations(num, limit: int) -> list:
    """Every distinct active declaration of a small space (grid then pruned)."""
    from adir.backends.numeric import _prune, grid_declarations
    out, seen = [], set()
    for vals in grid_declarations(num, 10 ** 7):
        v = _prune(num, vals)
        key = json.dumps(v, sort_keys=True, default=str)
        if key not in seen:
            seen.add(key)
            out.append(v)
            if len(out) > limit:
                break
    return out


def schemes_of(inst, ctx, level: str = "natural") -> tuple:
    """([(name, plan)] of the sharing schemes the seed realizes, manifest)."""
    from chialu.modules.generators import spec_of
    from chialu.plans import sharing_schemes
    from chialu.targets import derive
    manifest = derive.seed_alu_text(spec_of(ctx), None).structures

    def admits(sid: str, family: str) -> bool:
        st = manifest.get(sid)
        b = inst.bindings.get(f"core.{st.slot}.{st.index}.family") if st is not None else None
        if b is None:
            return False
        return b.value == family if b.time == "fixed" else b.domain.contains(family)
    return list(sharing_schemes(manifest, level, admits)), manifest




def nondominated(points: list) -> list:
    """Indices of the non-dominated (area, delay) points, by area."""
    order = sorted(range(len(points)), key=lambda i: (points[i][0], points[i][1]))
    out, best_d = [], float("inf")
    for i in order:
        if points[i][1] < best_d:
            out.append(i)
            best_d = points[i][1]
    return out


def spread(idx: list, k: int) -> list:
    if len(idx) <= k:
        return list(idx)
    return [idx[j] for j in sorted({round(i * (len(idx) - 1) / (k - 1)) for i in range(k)})]




# ------------------------------------------------------------------ sample sizes (coeff/calibration.py)

_Z = {0.90: 1.2816, 0.95: 1.6449, 0.975: 1.9600, 0.99: 2.3263, 0.995: 2.5758, 0.999: 3.0902}


def z_for(confidence: float) -> float:
    if confidence in _Z:
        return _Z[confidence]
    lo = max([c for c in _Z if c <= confidence], default=0.90)
    hi = min([c for c in _Z if c >= confidence], default=0.999)
    if hi == lo:
        return _Z[lo]
    return _Z[lo] + (confidence - lo) / (hi - lo) * (_Z[hi] - _Z[lo])


def test_size(target_rho: float, margin: float, confidence: float) -> int:
    """Points needed to certify rho >= target_rho when the truth is target_rho + margin
    (Fisher z: SE = 1/sqrt(n-3); the size of the space does not enter)."""
    dz = math.atanh(min(0.999, target_rho + margin)) - math.atanh(target_rho)
    return max(30, int(math.ceil(3 + (z_for(confidence) / dz) ** 2)))


def rho_lower_bound(rho_hat: float, n: int, confidence: float) -> float:
    if n <= 4 or rho_hat != rho_hat:
        return -1.0
    rho_hat = max(-0.999, min(0.999, rho_hat))
    return math.tanh(math.atanh(rho_hat) - z_for(confidence) / math.sqrt(n - 3))


def onehot_columns(num) -> int:
    """The one-hot width of a numeric instance's searched variables (the training set is a learning
    curve over these columns)."""
    n = 0
    for b in num.bindings.values():
        if b.time != "search":
            continue
        try:
            n += len(list(b.domain.members()))
        except Exception:  # noqa: BLE001
            n += 10
    return n


def calibration_knobs(run_file: Path, a) -> dict:
    """The run file's `search.extensions.calibration`, with the command line's overrides."""
    import yaml
    d = yaml.safe_load(run_file.read_text())
    cal = ((((d.get("adir") or {}).get("search") or {}).get("extensions") or {}).get("calibration") or {})
    r = dict(cal.get("ranking") or {})
    k = {"exhaustive_below": cal.get("exhaustive_below", 2000), "target_rho": r.get("target_rho", 0.90),
         "margin": r.get("margin", 0.03), "confidence": r.get("confidence", 0.99),
         "rows_per_column": r.get("rows_per_column", 10), "initial_train": r.get("initial_train"),
         "test_size": r.get("test_size"), "increment": r.get("increment"), "max_rounds": r.get("max_rounds", 6),
         "cv_floor_pct": r.get("cv_floor_pct", 3.0), "max_error_ratio": r.get("max_error_ratio", 0.5),
         "min_per_scheme": r.get("min_per_scheme", 20),
         "model": cal.get("model", "xgboost"), "gnn": dict(cal.get("gnn") or {}),
         "min_delay_gap_pct": cal.get("min_delay_gap_pct", 5),
         "min_area_gap_pct": cal.get("min_area_gap_pct", 2)}
    for name in ("exhaustive_below", "target_rho", "margin", "confidence", "initial_train", "test_size",
                 "max_rounds", "increment", "model", "min_delay_gap_pct", "min_area_gap_pct"):
        v = getattr(a, name, None)
        if v is not None:
            k[name] = v
    if getattr(a, "cv_floor", None) is not None:
        k["cv_floor_pct"] = a.cv_floor
    if getattr(a, "max_error_ratio", None) is not None:
        k["max_error_ratio"] = a.max_error_ratio
    if getattr(a, "min_per_scheme", None) is not None:
        k["min_per_scheme"] = a.min_per_scheme
    if k["model"] not in ("xgboost", "gnn"):
        raise ValueError("calibration.model must be xgboost or gnn")
    from chialu.surrogate_metrics import gap_threshold
    for key in ("min_delay_gap_pct", "min_area_gap_pct"):
        gap_threshold(k[key])
    k["source"] = f"{run_file.name}: search.extensions.calibration, overridden by the command line"
    return k


# ------------------------------------------------------------------ the model

XGB = dict(n_estimators=400, max_depth=5, learning_rate=0.05)       # the study's setting (coeff/xgb)


def fit(feats: list, ys: dict, seed: int = 0, weights=None, schemes=None, min_per_scheme: int = 0, *,
        model: str = "xgboost", gnn=None, graphs=None, graph_space=None) -> dict:
    """Typed XGBoost/GNN bundle over feature dicts or complete graphs (`weights`: per-row sample
    weights, e.g. heavier on the measured front's region). `schemes` (the training rows' sharing schemes)
    is kept in the bundle as {scheme: rows}, with `min_per_scheme`: a scheme with fewer training rows is
    one the model never learned, and `scheme_trained` refuses to predict under it."""
    if model == "gnn":
        from chialu.surrogate_gnn import fit as fit_gnn
        out = fit_gnn(graphs, ys, seed, weights, gnn, graph_space)
    elif model == "xgboost":
        import numpy as np
        from xgboost import XGBRegressor
        from chialu.surrogate_features import vector
        names = sorted({k for f in feats for k in f})
        X = np.stack([vector(f, names) for f in feats])
        models = {}
        for t, y in ys.items():
            m = XGBRegressor(**XGB, random_state=seed, n_jobs=8, verbosity=0)
            m.fit(X, np.log(np.asarray(y, dtype=float)), sample_weight=None if weights is None else np.asarray(weights, float))
            models[t] = m
        out = {"model_type": "xgboost", "models": models, "names": names}
    else:
        raise ValueError(f"unknown surrogate model {model!r}")
    if schemes is not None:
        from collections import Counter
        out["schemes"] = dict(Counter(schemes))
        out["min_per_scheme"] = int(min_per_scheme)
    return out


def scheme_trained(bundle: dict, scheme: str) -> bool:
    """Whether the model saw `scheme` in training at least `min_per_scheme` times. A bundle from before the
    count was kept (no `schemes`) answers True, so old models still load; every model this flow fits now
    carries it, and the numeric stage searches only the schemes that pass."""
    seen = bundle.get("schemes")
    if seen is None:
        return True
    return seen.get(scheme, 0) >= max(1, int(bundle.get("min_per_scheme") or 1))


def predict(bundle: dict, feats: list, *, graphs=None) -> dict:
    if bundle.get("model_type", "xgboost") == "gnn":
        from chialu.surrogate_gnn import predict as predict_gnn
        return predict_gnn(bundle, graphs)
    if bundle.get("model_type", "xgboost") != "xgboost":
        raise ValueError(f"unknown surrogate model {bundle['model_type']!r}")
    import numpy as np
    from chialu.surrogate_features import vector
    X = np.stack([vector(f, bundle["names"]) for f in feats])
    return {t: np.exp(m.predict(X)) for t, m in bundle["models"].items()}


def log_std(values) -> float:
    """The standard deviation of log(values): the spread of designs on the scale every error here is taken on."""
    import numpy as np
    return float(np.std(np.log(np.asarray(values, dtype=float))))


def accuracy(pred, true, confidence: float, spread=None, min_gap_pct=5) -> dict:
    """The model's error on measured points, every figure on the log scale the model is fitted on (a
    heavy tail of large designs would otherwise decide the RMSE, the spread and R^2 alike). `rmse` and
    `std` are of log(metric) -- about the relative error and the relative spread; `r2` is 1 - MSE/var of
    the log values; Spearman rho is the same on either scale. `spread` is log_std over the designs the
    error is weighed against (the training and validation sets together): `err_ratio` = rmse / spread
    says how much of the difference between designs the model's error covers (= sqrt(1 - R^2) against
    that population); near or above 1 the model cannot tell those designs apart."""
    import numpy as np
    from scipy.stats import spearmanr
    p, y = np.log(np.asarray(pred, dtype=float)), np.log(np.asarray(true, dtype=float))
    sr = spearmanr(p, y) if len(y) > 2 else None
    rho = float(sr.correlation) if sr is not None else float("nan")
    pval = float(sr.pvalue) if sr is not None else float("nan")
    mse = float(np.mean((p - y) ** 2))
    std = float(y.std())
    out = {"n": int(len(y)), "scale": "log", "spearman": round(rho, 3), "p_value": float(f"{pval:.3g}"),
           "rho_lower": round(rho_lower_bound(rho, len(y), confidence), 3),
           "mae": round(float(np.mean(np.abs(p - y))), 4), "rmse": round(float(np.sqrt(mse)), 4),
           "std": round(std, 4), "r2": round(1 - mse / std ** 2, 3) if std > 0 else None,
           "cv_pct": round(100 * std, 2)}
    from chialu.surrogate_metrics import pair_metrics
    order = pair_metrics(y, p, min_gap_pct)
    out["spearman_all_pairs"] = out.pop("spearman")
    out["p_value_all_pairs"] = out.pop("p_value")
    out["rho_lower_all_pairs"] = out.pop("rho_lower")
    out.update(order)
    out["rank_correlation"] = order["rho"]
    # Fisher's design-count approximation is retained, never using pair count as n.
    rho = order["rho"]
    out["rho_lower"] = rho_lower_bound(rho, len(y), confidence) if rho is not None else float("nan")
    if spread is not None and spread > 0:
        out["spread_std"] = round(float(spread), 4)
        out["err_ratio"] = round(float(np.sqrt(mse)) / float(spread), 3)
    return out


METRICS = ("area_um2", "delay_ps")


# ------------------------------------------------------------------ the cluster

_PINNED: dict = {}
_LOCK = threading.Lock()


class _Pinned:
    """A node function whose ray task is pinned to one node besides its
    own resources (`chia_remote`, which adir's Executor calls first)."""

    def __init__(self, fn, resources: dict):
        import ray
        from adir.registry import underlying
        self.__wrapped__ = fn
        self._remote = ray.remote(underlying(fn)).options(resources=resources, num_cpus=0)

    def chia_remote(self, **kw):
        kw.pop("_chia_tag", None)
        return self._remote.remote(**kw)


def pinned_executor(cache_dir: Path, node_ip: str | None, workers: int = 6):
    """adir's Executor with every ray task pinned to `node_ip` (the
    driver's node): a node whose workers read another checkout of the
    code (<host> reads /mnt/ssd/.../chialu-a3eval, not this tree, and the
    run's PYTHONPATH does not exist there) must not measure a point."""
    import dataclasses
    from adir.nodes import Executor

    class PinnedExecutor(Executor):
        def run(self, spec, kwargs):
            if node_ip and spec.fn is not None and self._ray_ok():
                with _LOCK:
                    w = _PINNED.get(spec.name)
                    if w is None:
                        res = dict(spec.resources or {})
                        res[f"node:{node_ip}"] = 0.001
                        w = _PINNED[spec.name] = _Pinned(spec.fn, res)
                spec = dataclasses.replace(spec, fn=w)
            return super().run(spec, kwargs)
    return PinnedExecutor(cache_dir, workers=workers)


# ------------------------------------------------------------------ the numeric run file over the surrogate

def surrogate_declaration(record, model_type="xgboost"):
    """Preserve all bound variables for graphs; keep legacy XGBoost projection exact."""
    from chialu.front_seeds import declared
    if model_type == "gnn":
        from chialu.surrogate_gnn import bound_vars
        full = ((record.get("measurements") or {}).get("declaration") or {}).get("value") or {}
        return bound_vars(full) or dict((record.get("declarations") or {}).get("vars") or {})
    return {k: v for k, v in declared(record).items() if k.startswith("core.") or k == "x_form"}


def surrogate_numeric_file(numeric: Path, model: Path, est: dict, k: int | None = None, scheme: str = "unshared",
                           plan: dict | None = None, population: int = 40, model_type: str = "xgboost") -> Path:
    """The numeric run file with the surrogate node in place of the
    estimate: NSGA-II (the file's backend) over the same declaration
    space, its goal the front of the surrogate's predicted area and delay
    under one sharing scheme (`<name>.numeric.surrogate[.s<k>].yaml`
    beside the numeric file, as the pipeline derives its `.cal` files)."""
    import yaml
    d = yaml.safe_load(numeric.read_text())
    a = d["adir"]
    nodes = a["evaluate"]["nodes"]
    for n in [n for n, v in nodes.items() if str((v or {}).get("node", "")) == "chialu.eda.estimate"]:
        del nodes[n]
    q = lambda s: f"'{s}'" if s else ""           # noqa: E731  a quoted input is a literal, not an expression
    nodes["surrogate"] = {"node": "chialu.eda.surrogate",
                          "inputs": {"files": "artifacts.verify_bundle", "decl": "decl.core", "model": q(str(model)),
                                     "plan_json": q(json.dumps(plan)) if plan else "", "scheme": q(scheme),
                                     "pdk": est.get("pdk", "nangate45"), "effort": est.get("effort", "medium"),
                                     "glue_json": q(est.get("glue_json") or ""),
                                     "context_json": q(est.get("context_json") or "")}}
    if model_type == "gnn":
        # decl.core omits checker choices; the declaration node holds all bound scalar variables.
        nodes["surrogate"]["inputs"]["full_decl"] = "declaration"
    a["evaluate"]["feedback"] = ["surrogate.detail"]
    if "search" in (a["variables"].get("x_form") or {}):
        nodes["surrogate"]["inputs"]["x_form"] = "decl.x_form"
    elif "fixed" in (a["variables"].get("x_form") or {}):
        nodes["surrogate"]["inputs"]["x_form"] = q(a["variables"]["x_form"]["fixed"])
    a["constraints"] = [{"metric": "declaration.ok", "eq": True, "hard": True},
                        {"metric": "surrogate.ok", "eq": True, "hard": True}]
    a["goal"] = {"pareto": [{"minimize": "surrogate.area_um2"}, {"minimize": "surrogate.delay_ps"}],
                 "score": {"rule": "ratio_to_seed", "infeasible": "slack"}}
    s = a.setdefault("search", {})
    s["backend"] = "nsga2"
    s.setdefault("numeric", {})["population"] = population
    s.pop("stop", None)                                  # the predictions are cheap: the iterations are the budget
    stem = numeric.name.split(".numeric")[0]
    out = numeric.with_name(f"{stem}.numeric.surrogate" + (f".s{k}" if k is not None else "") + ".yaml")
    out.write_text(yaml.safe_dump(d, sort_keys=False, width=200))
    return out


def estimate_inputs(numeric: Path) -> dict:
    """The estimate node's pdk, effort, glue and context of the (calibrated) numeric run file."""
    import yaml
    cal = numeric.with_name(numeric.stem + ".cal.yaml")
    d = yaml.safe_load((cal if cal.is_file() else numeric).read_text())
    for v in d["adir"]["evaluate"]["nodes"].values():
        if str((v or {}).get("node", "")) == "chialu.eda.estimate":
            i = v.get("inputs") or {}
            return {"pdk": i.get("pdk", "nangate45"), "effort": i.get("effort", "medium"),
                    "glue_json": i.get("glue_json") or "", "context_json": i.get("context_json") or ""}
    return {"pdk": "nangate45", "effort": "medium", "glue_json": "", "context_json": ""}


# ------------------------------------------------------------------ rendering and pricing in forked workers

_W: dict = {}


def _render(job: tuple) -> dict:
    """A drawn point made into a plan, rendered, checked by the declaration
    node and featurized, in a worker forked from the stage (the loaded
    instances inherited, not reloaded)."""
    name, vals, scheme = job
    if name == "__warm__":
        time.sleep(1.0)
        return {"name": name}
    from adir.declaration import check_declaration
    from adir.evaluate import candidate_from_program
    from chialu.front_seeds import realize
    from chialu.surrogate_features import features, scheme_repair
    st = _W["stage"]
    out = {"name": name, "scheme": scheme}
    try:
        plan_s = st.scheme_plan[scheme]
        vals = scheme_repair(vals, plan_s)
        out["vals"] = vals
        plan, err = realize(st.inst, st.ctx, st.manifest, {"declarations": {"vars": vals}}, name, 0, plan_s)
        if plan is None:
            out["rejected"] = err
            return out
        out["plan"] = plan
        program = st.program(name, plan)
        cand = candidate_from_program(st.inst, program)
        chk = check_declaration(st.inst, cand.declaration, st.inst.ctx(declaration=cand.declaration))
        if not chk.get("ok"):
            out["rejected"] = f"declaration: {str(chk.get('detail'))[:300]}"
            return out
        out["program"] = program
        out["feat"] = features(st.files, vals, scheme, plan_s, st.table, st.est_in)
    except Exception as e:  # noqa: BLE001
        out["rejected"] = f"{type(e).__name__}: {str(e)[:300]}"
    return out


def _featurize(job: tuple) -> tuple:
    name, vals, scheme = job
    from chialu.surrogate_features import features
    st = _W["stage"]
    return name, features(st.files, vals, scheme, st.scheme_plan[scheme], st.table, st.est_in)


# ------------------------------------------------------------------ the stage

class Stage:
    def __init__(self, a):
        self.a = a
        self.target = Path(a.target).resolve()
        self.run = Path(a.run_dir).resolve()
        self.out = self.run / "surrogate"
        self.out.mkdir(parents=True, exist_ok=True)
        self.numeric = Path(a.numeric).resolve() if a.numeric else self.target.with_name(self.target.stem + ".numeric.yaml")
        self.rng = random.Random(a.seed)
        self.lock = threading.Lock()
        self.data_file = self.out / "dataset.jsonl"
        self.rows = [json.loads(l) for l in self.data_file.read_text().splitlines() if l.strip()] \
            if self.data_file.is_file() else []
        if any(r.get("synth_ok") and r.get("repeats", 1) != a.synth_repeats for r in self.rows):
            raise ValueError("dataset repeat count differs; re-label into a fresh run directory")
        self.report = json.loads((self.out / "report.json").read_text()) if (self.out / "report.json").is_file() else {}
        self.model_file = self.out / "model.pkl"

    def log(self, msg: str) -> None:
        line = f"[surrogate {time.strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with (self.out / "log.txt").open("a") as f:
            f.write(line + "\n")

    def save_report(self) -> None:
        (self.out / "report.json").write_text(json.dumps(self.report, indent=1, default=str))

    def setup(self) -> None:
        from adir.instance import load
        import chialu.priors  # noqa: F401  the priors the run files name
        from chialu.modules.generators import spec_of
        from chialu.surrogate_features import manifest_table
        self.eval_file = surrogate_run_file(self.target, synth_repeats=self.a.synth_repeats)
        t0 = time.time()
        self.inst = load(str(self.eval_file), run_dir_override=str(self.out / "eval"))
        self.ctx = self.inst.ctx(run_dir=self.out / "eval")
        self.inst_sample = load(str(surrogate_run_file(self.target, "sample", self.a.synth_repeats)), run_dir_override=str(self.out / "eval"))
        self.num = load(str(self.numeric), run_dir_override=str(self.out / "numeric"))
        self.schemes, self.manifest = schemes_of(self.inst, self.ctx, self.a.sharing_level)
        self.scheme_plan = {n: p for n, p in self.schemes}
        self.table = manifest_table(self.manifest)
        self.files = {"spec.json": json.dumps(spec_of(self.num.ctx(run_dir=self.out / "numeric")))}
        self.est_in = estimate_inputs(self.numeric)
        self.knobs = calibration_knobs(self.target, self.a)
        if self.knobs["model"] == "gnn":
            from chialu.surrogate_graph import build_space
            self.graph_space = build_space([self.numeric], self.est_in.get("pdk", "nangate45"), self.a.sharing_level)
        lc = log10_count(self.num)
        self.report["space"] = {"log10_declarations": round(lc, 2), "schemes": len(self.schemes),
                                "log10_points": round(lc + math.log10(max(1, len(self.schemes))), 2),
                                "searched_variables": len(self.num.searched()),
                                "onehot_columns": onehot_columns(self.num),
                                "scheme_names": [n for n, _ in self.schemes]}
        self.report["knobs"] = self.knobs
        self.log(f"{self.target.name}: space 10^{self.report['space']['log10_points']} "
                 f"({len(self.num.searched())} searched variables, {self.report['space']['onehot_columns']} one-hot "
                 f"columns, {len(self.schemes)} schemes); run files loaded in {time.time() - t0:.0f}s; knobs {self.knobs}")
        (self.out / "count.json").write_text(json.dumps(self.report["space"], indent=1))
        # the renderers fork from this process before ray (and any xgboost) starts in it
        import multiprocessing as mp
        from concurrent.futures import ProcessPoolExecutor
        _W["stage"] = self
        self.pool = ProcessPoolExecutor(max_workers=self.a.render_jobs, mp_context=mp.get_context("fork"))
        list(self.pool.map(_render, [("__warm__", {}, "")] * (2 * self.a.render_jobs)))
        from adir.cli import connect
        self.cluster = connect(self.inst, local=self.a.local)
        if not self.cluster and not self.a.local:
            raise SystemExit("no ray cluster (set RAY_ADDRESS) and --local not given")
        self.node_ip = None
        if self.cluster and not self.a.any_node:
            import ray
            self.node_ip = ray.util.get_node_ip_address()
            self.log(f"evaluations pinned to this node ({self.node_ip}); --any-node lifts it")

    # -- points
    def coverage_items(self, base: list, per_family: int = 2, per_value: int = 1, cap: int = 3000) -> tuple:
        """Training points that make every searched member appear: a uniform draw reaches a deep choice only
        when every ancestor happens to open it (a product of 1/k), so on the complete space most nested
        members never occur in a few thousand random points. For each (variable, member) the random training
        points hold fewer than `per_family` (family selectors) or `per_value` (other finite choices) times, a
        point is drawn with that member and an activating path of ancestors forced (activation_path) and the
        rest random, under a scheme without shared groups (whose tying would overwrite the forced member);
        families first, at most `cap` points. Deterministic (its own seed), so a rerun resumes it.
        Returns (items, coverage report)."""
        import json as _json
        from collections import Counter
        from adir.backends.numeric import activation_path, sample_declaration
        rng = random.Random(self.a.seed + 7919)
        counts = Counter()
        for _n, vals, _s in base:
            counts.update((k, _json.dumps(v)) for k, v in vals.items())
        plain = [n for n, p in self.schemes if not (p or {}).get("shared")] or [n for n, _p in self.schemes]
        # the complete tree holds members no declaration of this target can reach (an ancestor's domain, narrowed
        # to what the target's widths and formats build, admits no member that opens them): they are counted
        # apart, not as gaps
        probe = random.Random(self.a.seed + 104729)
        pairs, unreachable = [], {"families": 0, "all": 0}
        for var in self.num.searched():
            b = self.num.bindings[var.name]
            if not b.domain.finite():
                continue
            fam = var.name.endswith(".family")
            for m in b.domain.members():
                if (_json.dumps(m) and counts[(var.name, _json.dumps(m))] == 0
                        and activation_path(self.num, var.name, m, probe) is None):
                    unreachable["all"] += 1
                    unreachable["families"] += fam
                    continue
                pairs.append((0 if fam else 1, var.name, m, per_family if fam else per_value))
        pairs.sort(key=lambda t: t[0])

        def covered(kind=None):
            sel = [p for p in pairs if kind is None or p[0] == kind]
            return sum(1 for _k, n, m, need in sel if counts[(n, _json.dumps(m))] >= 1), len(sel)
        before = {"families": covered(0), "all": covered()}
        out = []
        for _kind, name, m, need in pairs:
            if len(out) >= cap:
                break
            key = (name, _json.dumps(m))
            tries = 0
            while counts[key] < need and tries < 4 and len(out) < cap:
                tries += 1
                path = activation_path(self.num, name, m, rng)
                if path is None:
                    break
                vals = sample_declaration(self.num, rng, path)
                if vals.get(name) != m:
                    continue
                out.append((f"c{len(out):05d}", vals, rng.choice(plain)))
                counts.update((k, _json.dumps(v)) for k, v in vals.items())
        after = {"families": covered(0), "all": covered()}
        return out, {"before": before, "after": after, "points": len(out), "per_family": per_family,
                     "per_value": per_value, "cap": cap, "unreachable": unreachable,
                     "note": "covered/total over reachable (variable, member) pairs; unreachable pairs counted apart"}

    def draw(self, scheme: str | None = None) -> tuple:
        from adir.backends.numeric import sample_declaration
        name = scheme if scheme is not None else self.rng.choice(self.schemes)[0]
        return sample_declaration(self.num, self.rng), name

    def balanced_schemes(self, n: int) -> list:
        """`n` scheme names, every scheme equally often: shuffled rounds of the whole list (seeded), so the
        training and validation stretches of the stream each hold every scheme about n / #schemes times
        instead of whatever an independent draw per point gives."""
        rng = random.Random(self.a.seed + 15485863)
        names = [nm for nm, _p in self.schemes]
        out = []
        while len(out) < n:
            rnd = list(names)
            rng.shuffle(rnd)
            out += rnd
        return out[:n]

    def scheme_topup(self, tr: list, rnd: int) -> list:
        """Training rows for the schemes the training set holds fewer than `min_per_scheme` measured feasible
        rows of (the seed refuses some points of a scheme, some fail): points drawn under exactly those
        schemes and measured, so the model has seen every scheme it will be asked about. Deterministic per
        round (its own seed, names s<round>_<n>), so a rerun resumes it; up to three passes. The validation
        set is left as drawn."""
        from collections import Counter
        from adir.backends.numeric import sample_declaration
        need = int(self.knobs.get("min_per_scheme") or 0)
        if need <= 0:
            return []
        got_all, names = [], {}
        for attempt in range(3):
            counts = Counter(r["scheme"] for r in tr + got_all if usable(r))
            short = [(nm, need - counts[nm]) for nm, _p in self.schemes if counts[nm] < need]
            if not short:
                break
            rng = random.Random(self.a.seed * 7919 + rnd * 101 + attempt)
            items = []
            for nm, gap in short:
                for _ in range(int(gap * (1.5 + attempt))):
                    items.append((f"s{rnd}_{attempt}_{len(items):05d}", sample_declaration(self.num, rng), nm))
            self.log(f"round {rnd}: {len(short)} schemes under {need} training rows; topping up with {len(items)} points")
            got = self.measure(items, f"scheme_topup{rnd}", len(items), "sample")
            self.ensure_features(got)
            for r in got:
                if r["name"] not in names:
                    names[r["name"]] = 1
                    got_all.append(r)
        counts = Counter(r["scheme"] for r in tr + got_all if usable(r))
        still = sorted(nm for nm, _p in self.schemes if counts[nm] < need)
        self.report["sample"].setdefault("scheme_coverage", {})[f"round{rnd}"] = {
            "min_per_scheme": need, "schemes": len(self.schemes), "topped_up_rows": len(got_all),
            "min_rows": min((counts[nm] for nm, _p in self.schemes), default=0),
            "below_min_after_topup": still}
        if still:
            self.log(f"WARNING round {rnd}: {len(still)} schemes still under {need} training rows (the model will "
                     f"not be used under them): {still[:10]}")
        return got_all

    def program(self, name: str, plan: dict) -> str:
        from adir.evaluate import program_from_seed_text
        from adir.seeds import _seed_texts
        res = self.inst.template.plan_seed(self.ctx, name, plan)
        texts, vars_, lines = _seed_texts(self.inst.seed_artifacts()[0], res, name)
        return program_from_seed_text(self.inst, texts, vars_, lines)

    def evaluate(self, name: str, program: str, gates: str = "full") -> dict:
        from adir.evaluate import candidate_from_program, evaluate_candidate
        edir = self.out / "eval"
        inst = self.inst if gates == "full" else self.inst_sample
        cand = candidate_from_program(inst, program, is_seed=True, seed_name=name,
                                      meta={"candidate_id": f"surrogate:{name}"})
        rec = evaluate_candidate(inst, edir, cand, seed_values={}, archive=None,
                                 executor=pinned_executor(edir / "cache", self.node_ip), log=None, pins={})
        m = rec.get("measurements") or {}
        sp = (m.get("synth_ppa") or {}).get("value") or {}
        conf = (m.get("conformance") or {}).get("value") or {}
        from chialu.synth_records import trace
        return {**trace(sp), "feasible": bool(rec.get("feasible")), "synth_ok": bool(sp.get("ok")), "gates": gates,
                "area_um2": sp.get("area_um2"), "delay_ps": sp.get("abc_delay_ps"),
                "conformance": conf.get("pass"), "cells": sp.get("cells"),
                "detail": None if rec.get("feasible") and sp.get("ok") else str(rec.get("stderr") or sp.get("detail") or "")[:300]}

    def append(self, row: dict) -> None:
        with self.lock:
            self.rows.append(row)
            with self.data_file.open("a") as f:
                f.write(json.dumps(row, default=str) + "\n")

    def measure(self, items: list, source: str, want: int, gates: str = "full") -> list:
        """Render [(name, vals, scheme)] in the forked workers, in order, and
        evaluate on the cluster until `want` of them are measured feasible
        (rows already in the dataset count; a rerun resumes); a point the
        seed refuses is recorded with its reason. Returns the measured
        feasible rows among `items`, in stream order."""
        from concurrent.futures import FIRST_COMPLETED, wait
        done = {r["name"]: r for r in self.rows}
        order = {n: i for i, (n, _v, _s) in enumerate(items)}
        have = lambda: sum(1 for n, _v, _s in items if n in done and usable(done[n]))   # noqa: E731
        fresh = iter([it for it in items if it[0] not in done])
        t0, refused, n_done = time.time(), 0, 0
        evals = ThreadPoolExecutor(max_workers=self.a.inflight)
        pending_render: set = set()
        pending_eval: dict = {}

        def feed():
            # enough renders to cover the shortfall, with room for refusals and failures
            short = want - have() - len(pending_eval)
            while len(pending_render) < min(2 * self.a.render_jobs, max(0, short) + self.a.render_jobs) and short > 0:
                nxt = next(fresh, None)
                if nxt is None:
                    return
                pending_render.add(self.pool.submit(_render, nxt))
                short -= 0.5
        feed()
        while pending_render or pending_eval:
            ready, _ = wait(list(pending_render) + list(pending_eval), return_when=FIRST_COMPLETED)
            for fu in ready:
                if fu in pending_render:
                    pending_render.discard(fu)
                    r = fu.result()
                    row = {"name": r["name"], "source": source, "scheme": r["scheme"], "vals": r.get("vals"),
                           "plan": r.get("plan"), "feat": r.get("feat")}
                    if r.get("rejected"):
                        refused += 1
                        row.update({"feasible": False, "rejected": r["rejected"]})
                        self.append(row)
                        done[row["name"]] = row
                        continue
                    if have() + len(pending_eval) >= want:
                        continue                       # enough in flight; this one stays unmeasured
                    pending_eval[evals.submit(self.evaluate, row["name"], r["program"], gates)] = row
                else:
                    row = pending_eval.pop(fu)
                    try:
                        row.update(fu.result())
                    except Exception as e:  # noqa: BLE001
                        row.update({"feasible": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
                    row["seconds"] = round(time.time() - t0, 1)
                    self.append(row)
                    done[row["name"]] = row
                    n_done += 1
                    if n_done % 25 == 0:
                        self.log(f"{source}: {have()}/{want} measured feasible, {n_done} evaluated this call, "
                                 f"{len(pending_eval)} in flight, {refused} refused by the seed, {time.time() - t0:.0f}s")
            feed()
        evals.shutdown()
        got = sorted((done[n] for n, _v, _s in items if n in done and usable(done[n])), key=lambda r: order[r["name"]])
        self.log(f"{source}: {len(got)}/{want} measured feasible; {n_done} evaluated, {refused} refused by the seed, "
                 f"{time.time() - t0:.0f}s")
        return got[:want] if want else got

    def ensure_features(self, rows: list) -> None:
        """Features for rows measured before they were stored with them."""
        need = [(r["name"], r["vals"], r["scheme"]) for r in rows if not r.get("feat") and r.get("vals") is not None]
        if not need:
            return
        by = {r["name"]: r for r in rows}
        for name, f in self.pool.map(_featurize, need, chunksize=8):
            by[name]["feat"] = f
        self.log(f"featurized {len(need)} rows measured earlier")

    def graph_rows(self, rows, bundle=None):
        model_type = bundle.get("model_type", "xgboost") if bundle is not None else self.knobs["model"]
        if model_type != "gnn":
            return None
        from chialu.surrogate_gnn import graph_input
        space = bundle["graph_space"] if bundle is not None else self.graph_space
        return [graph_input(space, self.files, r["vals"], r["scheme"],
                            self.scheme_plan[r["scheme"]], self.est_in) for r in rows]

    def fit_rows(self, rows, weights=None):
        """The same dispatch covers certification and front-weighted refitting."""
        return fit([r["feat"] for r in rows], {t: [r[t] for r in rows] for t in METRICS}, self.a.seed,
                   weights, schemes=[r["scheme"] for r in rows], min_per_scheme=int(self.knobs.get("min_per_scheme") or 0),
                   model=self.knobs["model"], gnn=dict(self.knobs["gnn"], min_delay_gap_pct=self.knobs["min_delay_gap_pct"]),
                   graphs=self.graph_rows(rows), graph_space=getattr(self, "graph_space", None))

    def predict_rows(self, bundle, rows):
        return predict(bundle, [r.get("feat", {}) for r in rows], graphs=self.graph_rows(rows, bundle))

    def metric_gap(self, metric):
        return self.knobs["min_area_gap_pct" if metric == "area_um2" else "min_delay_gap_pct"]

    # -- the protocol
    def sample(self) -> dict:
        """Exhaustive below the threshold; else the incremental protocol. Returns the certified bundle."""
        k = self.knobs
        lp = self.report["space"]["log10_points"]
        if lp <= math.log10(max(1, k["exhaustive_below"])):
            decls = enumerate_declarations(self.num, int(k["exhaustive_below"]))
            items = [(f"e{i:05d}_{j}", d, s) for j, (s, _p) in enumerate(self.schemes) for i, d in enumerate(decls)]
            self.report["sample"] = {"mode": "exhaustive", "points": len(items)}
            self.measure(items, "exhaustive", len(items))
            self.save_report()
            return {}
        n_train = int(k["initial_train"] or min(self.a.max_initial,
                                                 max(400, math.ceil(self.report["space"]["onehot_columns"] * k["rows_per_column"]))))
        n_test = int(k["test_size"] or test_size(k["target_rho"], k["margin"], k["confidence"]))
        increment = int(k["increment"] or n_test)
        budget = n_train + int(k["max_rounds"]) * (increment + n_test)
        items = []
        # twice the budget: room for points the seed refuses or that fail (the complete space now renders
        # raw, so few are); the draws are sequential from one seed, so a larger budget keeps the earlier names
        for i, sch in enumerate(self.balanced_schemes(2 * budget)):
            vals, s = self.draw(sch)
            items.append((f"r{i:05d}", vals, s))
        self.report["sample"] = {"mode": "incremental", "initial_train": n_train, "test_size": n_test,
                                 "increment": increment, "max_rounds": k["max_rounds"], "rounds": []}
        self.log(f"protocol: train {n_train}, validate {n_test} per round (Fisher z: rho >= {k['target_rho']} at "
                 f"{k['confidence']} when the truth is {k['target_rho'] + k['margin']:.2f}), add {increment} per failed "
                 f"round, at most {k['max_rounds']} rounds; CV floor {k['cv_floor_pct']}%")
        # coverage: training points that make every member of the complete space occur (the validation sets
        # stay uniform draws, so rho and the error are those of the space itself)
        cov_items, cov_rep = self.coverage_items(items[:n_train], cap=int(getattr(self.a, "coverage_cap", 3000)))
        self.report["sample"]["coverage"] = cov_rep
        self.log(f"coverage (reachable members; unreachable: {cov_rep['unreachable']['families']} family, "
                 f"{cov_rep['unreachable']['all']} in all): random training points cover family members {cov_rep['before']['families'][0]}/"
                 f"{cov_rep['before']['families'][1]}, all members {cov_rep['before']['all'][0]}/{cov_rep['before']['all'][1]}; "
                 f"{cov_rep['points']} forced points raise that to {cov_rep['after']['families'][0]}/"
                 f"{cov_rep['after']['families'][1]} and {cov_rep['after']['all'][0]}/{cov_rep['after']['all'][1]}")
        got_cov = self.measure(cov_items, "coverage", len(cov_items), "sample") if cov_items else []
        self.ensure_features(got_cov)
        train_n, bundle = n_train, None
        for rnd in range(1, int(k["max_rounds"]) + 1):
            got = self.measure(items, f"round{rnd}", train_n + n_test, "sample")
            self.ensure_features(got)
            tr, va = got_cov + got[:train_n], got[train_n:train_n + n_test]
            tr = tr + self.scheme_topup(tr, rnd)
            bundle = self.fit_rows(tr)
            pred = self.predict_rows(bundle, va)
            acc, verdict = {}, {}
            import numpy as np
            for t in METRICS:
                # the error is weighed against the spread of every measured design so far (training and
                # validation sets together): a model whose error covers the differences between designs
                # ranks noise, whatever its rho
                spread = log_std([r[t] for r in got])
                acc[t] = accuracy(pred[t], [r[t] for r in va], k["confidence"], spread, self.metric_gap(t))
                acc[t]["cv_all_pct"] = round(100 * spread, 2)       # the log std: about the CV
                ratio = acc[t].get("err_ratio", float("inf"))
                if acc[t]["cv_all_pct"] < k["cv_floor_pct"]:
                    verdict[t] = f"pass: CV {acc[t]['cv_all_pct']}% < {k['cv_floor_pct']}% (the designs are about equal)"
                elif acc[t]["rho_lower"] >= k["target_rho"] and ratio <= k["max_error_ratio"]:
                    verdict[t] = (f"pass: rho {acc[t]['rank_correlation']} (lower bound {acc[t]['rho_lower']}) >= {k['target_rho']}, "
                                  f"error/spread {ratio} <= {k['max_error_ratio']}")
                else:
                    verdict[t] = (f"fail: rho {acc[t]['rank_correlation']} (lower bound {acc[t]['rho_lower']}, target {k['target_rho']}), "
                                  f"error/spread {ratio} (limit {k['max_error_ratio']})")
            self.report["sample"]["rounds"].append({"round": rnd, "train": len(tr), "validate": len(va),
                                                    "accuracy": acc, "verdict": verdict,
                                                    "train_names": [tr[0]["name"], tr[-1]["name"]] if tr else [],
                                                    "validate_names": [va[0]["name"], va[-1]["name"]] if va else []})
            self.log(f"round {rnd}: train {len(tr)}, validate {len(va)}; " + "; ".join(
                f"{t}: rho {acc[t]['rank_correlation']} (lb {acc[t]['rho_lower']}, pairs {acc[t]['pairs']}, p_all_pairs {acc[t]['p_value_all_pairs']}), log RMSE {acc[t]['rmse']} vs log spread "
                f"{acc[t].get('spread_std')} (ratio {acc[t].get('err_ratio')}), log R^2 {acc[t]['r2']}, "
                f"CV {acc[t]['cv_all_pct']}% -> {verdict[t]}" for t in METRICS))
            self.save_bundle(bundle, f"round{rnd}", len(tr), acc)
            self.save_report()
            self.train_rows, self.val_rows = tr, va
            if all(v.startswith("pass") for v in verdict.values()):
                self.report["sample"]["certified"] = True
                break
            train_n += increment                      # the failed validation set joins the training set
        else:
            self.report["sample"]["certified"] = False
        rs = [r for r in self.rows if r["name"].startswith("r")]
        self.report["sample"].update({"drawn": len(rs), "refused_by_seed": sum(1 for r in rs if r.get("rejected")),
                                      "evaluated": sum(1 for r in rs if not r.get("rejected")),
                                      "measured_feasible": sum(1 for r in rs if usable(r)),
                                      "failed": sorted({str(r.get("detail") or r.get("error"))[:100] for r in rs
                                                        if not r.get("rejected") and not usable(r)})[:10],
                                      "refusals": sorted({str(r.get("rejected"))[:110] for r in rs if r.get("rejected")})[:12]})
        self.save_report()
        return bundle

    def save_bundle(self, bundle: dict, tag: str, n_train: int, acc: dict) -> None:
        import pickle
        meta = {"target": self.target.name, "pdk": self.est_in.get("pdk"), "features": "chialu.surrogate_features",
                "model_type": bundle.get("model_type", "xgboost"),
                "model_config": bundle.get("cfg", XGB), "log_target": True, "train_rows": n_train, "accuracy": acc, "tag": tag,
                "trained_on": f"{self.data_file} (this flow's own whole-unit syntheses only)"}
        if bundle.get("model_type", "xgboost") == "xgboost":
            meta["xgb"] = XGB
        else:
            meta["features"] = "chialu.surrogate_graph"
        meta["min_delay_gap_pct"] = self.knobs["min_delay_gap_pct"]
        meta["min_area_gap_pct"] = self.knobs["min_area_gap_pct"]
        blob = pickle.dumps({**bundle, "meta": meta})
        self.model_file.write_bytes(blob)
        (self.out / f"model.{tag}.pkl").write_bytes(blob)
        models = REPO / "ml" / "models"
        models.mkdir(parents=True, exist_ok=True)
        (models / f"{self.est_in.get('pdk', 'nangate45')}.{self.target.stem}.pkl").write_bytes(blob)

    # -- the search
    def retrain(self, rnd: int) -> dict:
        """The models refitted on the training rows plus every point verified so far (the search's own
        points, where the previous model was exploited), scored on the same held-out validation set."""
        extra = [r for r in self.rows if usable(r) and r.get("feat")
                 and str(r.get("source", "")).startswith(("verify", "refine"))]
        tr = list(self.train_rows) + extra
        # fine-tuning toward the front: the rows in the measured front's first layers weigh `--front-weight`
        # times the rest, so the model spends its capacity where the seeds are chosen
        pts = [(r["area_um2"], r["delay_ps"]) for r in tr]
        near, left = set(), list(range(len(pts)))
        for _layer in range(int(self.a.front_layers)):
            if not left:
                break
            lay = [left[j] for j in nondominated([pts[i] for i in left])]
            near |= set(lay)
            left = [i for i in left if i not in near]
        weights = [float(self.a.front_weight) if i in near else 1.0 for i in range(len(tr))]
        bundle = self.fit_rows(tr, weights)
        pred = self.predict_rows(bundle, self.val_rows)
        acc = {t: accuracy(pred[t], [r[t] for r in self.val_rows], self.knobs["confidence"],
                           min_gap_pct=self.metric_gap(t)) for t in METRICS}
        self.report.setdefault("search", {}).setdefault(f"round{rnd}", {})["retrain"] = {
            "train": len(tr), "verified_added": len(extra), "front_weighted": len(near),
            "front_weight": self.a.front_weight, "validate": len(self.val_rows), "accuracy": acc}
        self.log(f"search round {rnd}: refitted on {len(tr)} rows ({len(extra)} verified points added); holdout "
                 + "; ".join(f"{t} rho {acc[t]['rank_correlation']} log RMSE {acc[t]['rmse']}, log R^2 {acc[t]['r2']}" for t in METRICS))
        self.save_bundle(bundle, f"search{rnd}", len(tr), acc)
        self.save_report()
        return bundle

    def pick_schemes(self, bundle: dict) -> list:
        """The schemes of the measured front, then those whose measured points the model ranks best
        (by predicted non-domination), up to `--schemes`; a scheme the seed refused every time is left out,
        and so is one the model did not see `min_per_scheme` times in training (it would be extrapolating)."""
        ok = [r for r in self.rows if usable(r) and scheme_trained(bundle, r["scheme"])]
        chosen = []
        fr = nondominated([(r["area_um2"], r["delay_ps"]) for r in ok])      # by area, ascending
        # both ends of the front first, alternately (the fastest point, the smallest, the next fastest, ...),
        # so a cap on the schemes cannot leave one end of the front unsearched
        both = [fr[j] for k in range((len(fr) + 1) // 2) for j in dict.fromkeys((len(fr) - 1 - k, k))]
        for i in both:
            if ok[i]["scheme"] not in chosen:
                chosen.append(ok[i]["scheme"])
        feats = [r for r in ok if r.get("feat")]
        if feats and len(chosen) < self.a.schemes:
            pred = self.predict_rows(bundle, feats)
            pts = list(zip(pred["area_um2"], pred["delay_ps"]))
            left = list(range(len(pts)))
            while left and len(chosen) < self.a.schemes:
                lay = [left[j] for j in nondominated([pts[i] for i in left])]
                for i in lay:
                    if feats[i]["scheme"] not in chosen and len(chosen) < self.a.schemes:
                        chosen.append(feats[i]["scheme"])
                ls = set(lay)
                left = [i for i in left if i not in ls]
        chosen = chosen[: max(self.a.schemes, 1)]
        self.log(f"schemes for NSGA-II: {chosen}")
        return chosen

    def nsga(self, bundle: dict, rnd: int) -> list:
        """NSGA-II over the surrogate under each chosen scheme; [(vals, scheme, area, delay)] of every
        feasible record (the predictions)."""
        import subprocess
        root = self.out / "nsga" / f"round{rnd}"
        prev = (self.report.get("search") or {}).get(f"round{rnd}", {}).get("schemes")
        reuse = bool(prev) and all(
            (d / "results_db.jsonl").is_file() and sum(1 for _ in (d / "results_db.jsonl").open()) >= self.a.iterations
            for d in (root / f"s{k}_{n}"[:90] for k, n in enumerate(prev, 1)))
        chosen = prev if reuse else self.pick_schemes(bundle)
        model = self.out / f"model.search{rnd}.pkl"
        if not reuse:
            model.write_bytes(self.model_file.read_bytes())
        procs, t0 = [], time.time()
        for k, name in enumerate(chosen, 1):
            if reuse:
                procs.append((name, root / f"s{k}_{name}"[:90], None))
                continue
            f = surrogate_numeric_file(self.numeric, model, self.est_in, k, name, self.scheme_plan[name],
                                       self.a.population, bundle.get("model_type", "xgboost"))
            d = root / f"s{k}_{name}"[:90]
            d.mkdir(parents=True, exist_ok=True)
            (d / "run_file.yaml").write_text(f.read_text())
            (d / "scheme.json").write_text(json.dumps({"name": name, "plan": self.scheme_plan[name], "run_file": str(f)}))
            cmd = [sys.executable, "-m", "adir.cli", "run", str(f), "--run-dir", str(d), "--iterations",
                   str(self.a.iterations), "--local"]
            procs.append((name, d, subprocess.Popen(cmd, stdout=(d / "adir.log").open("w"), stderr=subprocess.STDOUT)))
            time.sleep(1)
        out = []
        if reuse:
            self.log(f"NSGA-II round {rnd}: the finished runs under {root} are reused")
        for name, d, p in procs:
            rc = p.wait() if p is not None else "reused"
            f = d / "results_db.jsonl"
            n = 0
            for line in (f.read_text().splitlines() if f.is_file() else []):
                if not line.strip():
                    continue
                r = json.loads(line)
                g = r.get("goal_values") or []
                if r.get("feasible") and len(g) >= 2 and all(isinstance(x, (int, float)) for x in g[:2]):
                    out.append((surrogate_declaration(r, bundle.get("model_type", "xgboost")), name, float(g[0]), float(g[1])))
                    n += 1
            self.log(f"NSGA-II round {rnd} {name}: exit {rc}, {n} feasible records")
        self.report.setdefault("search", {}).setdefault(f"round{rnd}", {}).update(
            {"schemes": chosen, "iterations_per_scheme": self.a.iterations, "records": len(out),
             "seconds": round(time.time() - t0, 1)})
        self.save_report()
        return out

    def verify(self, bundle: dict, recs: list, rnd: int) -> None:
        """Synthesize `--verify` points of the predicted front (merged over the schemes, spread along it,
        then the next layers; a point the seed refuses or one already measured gives way)."""
        from chialu.surrogate_features import scheme_repair
        pts = [(a_, d_) for _v, _s, a_, d_ in recs]
        order, left = [], list(range(len(pts)))
        for _layer in range(30):
            if not left:
                break
            lay = [left[j] for j in nondominated([pts[i] for i in left])]
            sp = spread(lay, self.a.verify)
            order += sp + [i for i in lay if i not in set(sp)]
            ls = set(lay)
            left = [i for i in left if i not in ls]
        # points measured before this round give way; this round's own rows do not (a rerun regenerates the
        # same names for the same points, and `measure` then finds them measured)
        seen = {json.dumps([r["scheme"], r.get("vals")], sort_keys=True, default=str) for r in self.rows
                if r.get("source") != f"verify{rnd}"}
        items, pred = [], {}
        for i in order:
            v, s, pa, pd = recs[i]
            v = scheme_repair(v, self.scheme_plan[s])
            key = json.dumps([s, v], sort_keys=True, default=str)
            if key in seen:
                continue
            seen.add(key)
            name = f"v{rnd}_{len(items) + 1:04d}"
            items.append((name, v, s))
            pred[name] = (pa, pd)
            if len(items) >= 6 * self.a.verify:
                break
        got = self.measure(items, f"verify{rnd}", self.a.verify)
        rep = self.report["search"][f"round{rnd}"]
        rep["predicted_front"] = len(nondominated(pts))
        rep["verified"] = {r["name"]: {"predicted": [round(pred[r["name"]][0], 1), round(pred[r["name"]][1], 1)],
                                       "measured": [r["area_um2"], r["delay_ps"]], "scheme": r["scheme"],
                                       "synthesis_record": {"dataset": str(self.data_file), "name": r["name"]}}
                           for r in got if r["name"] in pred}
        ok = [r for r in got if r["name"] in pred]
        if len(ok) > 2:
            import numpy as np
            allrows = [r for r in self.rows if usable(r)]
            rep["verify_accuracy"] = {}
            for j, t in enumerate(METRICS):
                a_all = accuracy([pred[r["name"]][j] for r in ok], [r[t] for r in ok], self.knobs["confidence"],
                                 log_std([r[t] for r in allrows]) if allrows else None, self.metric_gap(t))
                # against the verified points' own spread: the designs near the front differ little, and an
                # error as large as their spread cannot tell them apart
                a_all["err_ratio_front"] = round(a_all["rmse"] / a_all["std"], 3) if a_all["std"] > 0 else None
                rep["verify_accuracy"][t] = a_all
            self.log(f"verify round {rnd}: {len(ok)} measured; " + "; ".join(
                f"{t}: RMSE {v['rmse']}, error/spread over all designs {v.get('err_ratio')}, "
                f"over the verified front {v['err_ratio_front']}, rho {v['rank_correlation']}"
                for t, v in rep["verify_accuracy"].items()))
            for t, v in rep["verify_accuracy"].items():
                if (v.get("err_ratio_front") or 0) > 1:
                    self.log(f"WARNING {t}: the model's error on the verified front ({v['rmse']}) exceeds the spread "
                             f"of those designs ({v['std']}): it cannot rank them; the seeds rest on their measurements")
        self.save_report()

    def refine(self, bundle: dict, rnd: int) -> None:
        """Front refinement: neighbours of the measured front (each front design with 1-3 of its choices
        redrawn, the rest kept; `--refine-pool` per design), scored by the model, and the `--refine` best
        predicted (non-dominated layers, spread along each) synthesized. The next round's model is refitted
        on them (retrain), so the model is corrected exactly where the seeds will be picked."""
        from adir.backends.numeric import sample_declaration
        from chialu.surrogate_features import features, scheme_repair
        rng = random.Random(self.a.seed * 1000003 + rnd)
        # only under schemes the model was trained on: a neighbour is ranked by the model before it is measured
        ok = [r for r in self.rows if usable(r) and r.get("vals") is not None and scheme_trained(bundle, r["scheme"])]
        pts = [(r["area_um2"], r["delay_ps"]) for r in ok]
        base, left = [], list(range(len(pts)))
        for _layer in range(int(self.a.front_layers)):
            if not left:
                break
            lay = [left[j] for j in nondominated([pts[i] for i in left])]
            base += lay
            left = [i for i in left if i not in set(lay)]
        seen = {json.dumps([r["scheme"], r.get("vals")], sort_keys=True, default=str) for r in self.rows}
        cand = []
        for i in base:
            r = ok[i]
            keys = list(r["vals"])
            for _ in range(int(self.a.refine_pool)):
                drop = set(rng.sample(keys, min(len(keys), rng.randint(1, 3)))) if keys else set()
                forced = {k: v for k, v in r["vals"].items() if k not in drop}
                v = scheme_repair(sample_declaration(self.num, rng, forced), self.scheme_plan[r["scheme"]])
                key = json.dumps([r["scheme"], v], sort_keys=True, default=str)
                if key in seen:
                    continue
                seen.add(key)
                cand.append((v, r["scheme"]))
        if not cand:
            return
        feats = [features(self.files, v, s_, self.scheme_plan[s_], self.table, self.est_in) for v, s_ in cand]
        pred = self.predict_rows(bundle, [{"feat": f, "vals": v, "scheme": sch}
                                          for f, (v, sch) in zip(feats, cand)])
        cpts = list(zip(pred["area_um2"], pred["delay_ps"]))
        order, left = [], list(range(len(cpts)))
        while left and len(order) < int(self.a.refine):
            lay = [left[j] for j in nondominated([cpts[i] for i in left])]
            order += spread(lay, int(self.a.refine) - len(order))
            left = [i for i in left if i not in set(lay)]
        items = [(f"f{rnd}_{n + 1:04d}", cand[i][0], cand[i][1]) for n, i in enumerate(order)]
        got = self.measure(items, f"refine{rnd}", len(items))
        self.report.setdefault("search", {}).setdefault(f"round{rnd}", {})["refine"] = {
            "front_designs": len(base), "candidates": len(cand), "synthesized": len(got)}
        self.log(f"refine round {rnd}: {len(base)} front designs, {len(cand)} neighbours scored, "
                 f"{len(got)} of the best predicted synthesized")
        self.save_report()

    def front_hv(self, box=None):
        """(hypervolume of the measured front in `box`, box): the box is fixed at the first call, 1.2 times the
        median area and delay measured -- the region the front lives in; a box at the extremes (a few designs
        are 10x the median) makes every front change a rounding error -- so rounds compare in one measure."""
        import statistics
        ok = [(r["area_um2"], r["delay_ps"]) for r in self.rows if usable(r)]
        if box is None:
            box = (1.2 * statistics.median(a for a, _ in ok), 1.2 * statistics.median(d for _, d in ok))
        fr = sorted(ok[i] for i in nondominated(ok))
        hv, ymin = 0.0, box[1]
        for x, y in fr:
            if y < ymin and x < box[0]:
                hv += (box[0] - x) * (ymin - y)
                ymin = y
        return hv / (box[0] * box[1]), box

    def confirm_front(self) -> None:
        """Evaluate with the full gates (conformance, the fault gate) every point of the measured front
        that was measured with the sample gates alone, until the front holds fully checked points only."""
        confirmed = 0
        for _it in range(8):
            ok = [r for r in self.rows if usable(r) and r.get("plan") and not r["name"].endswith("~full")]
            full = {r["name"][: -len("~full")]: r for r in self.rows if r["name"].endswith("~full")}
            cand = [r for r in ok if r.get("gates") != "sample" or (r["name"] in full and usable(full[r["name"]]))]
            cand += [r for r in ok if r.get("gates") == "sample" and r["name"] not in full]
            fr = [cand[i] for i in nondominated([(r["area_um2"], r["delay_ps"]) for r in cand])]
            todo = [r for r in fr if r.get("gates") == "sample" and r["name"] not in full]
            if not todo:
                break
            self.measure([(r["name"] + "~full", r["vals"], r["scheme"]) for r in todo], "confirm", len(todo), "full")
            confirmed += len(todo)
        self.report["confirmed_with_full_gates"] = confirmed

    def seeds(self) -> None:
        from chialu.synth_records import trace
        a = self.a
        self.confirm_front()
        # the fully gated points: rows measured with the full graph (a sample row stands for itself only
        # through its `~full` re-evaluation)
        ok = [r for r in self.rows if usable(r) and r.get("plan") and r.get("gates") != "sample"]
        pts = [(r["area_um2"], r["delay_ps"]) for r in ok]
        fr = nondominated(pts)                      # by area, ascending
        kept = list(reversed(spread(fr, a.top)))    # fastest first: the first seed is the score reference
        f = self.run / "discovered.json"
        doc = json.loads(f.read_text()) if f.is_file() else {"plans": {}, "rejected": {}}
        plans = {k: v for k, v in (doc.get("plans") or {}).items() if not k.startswith(a.prefix + "_")}
        out = []
        for k, i in enumerate(kept, 1):
            r = ok[i]
            plan = dict(r["plan"])
            plan["why"] = (f"surrogate stage point {k}: measured {r['area_um2']:.1f} um2, {r['delay_ps']:.1f} ps "
                           f"({r['source']} {r['name']}, sharing scheme {r['scheme']})")
            plans[f"{a.prefix}_{k}"] = plan
            out.append({"seed": f"{a.prefix}_{k}", "name": r["name"], "source": r["source"], "scheme": r["scheme"],
                        "area_um2": r["area_um2"], "delay_ps": r["delay_ps"],
                        "synthesis": trace(r)})
        doc["plans"] = plans
        doc["synthesis"] = {**{k: v for k, v in doc.get("synthesis", {}).items()
                              if k in plans and not k.startswith(a.prefix + "_")},
                            **{r["seed"]: r["synthesis"] for r in out}}
        doc.setdefault("rejected", {})
        f.write_text(json.dumps(doc, indent=1))
        self.report["front"] = [{"name": ok[i]["name"], "source": ok[i]["source"], "area_um2": ok[i]["area_um2"],
                                 "delay_ps": ok[i]["delay_ps"], "scheme": ok[i]["scheme"], "synthesis": trace(ok[i])} for i in fr]
        self.report["seeds"] = out
        self.save_report()
        self.log(f"seeds -> {f}: " + "; ".join(f"{o['seed']} {o['area_um2']:.1f} um2 / {o['delay_ps']:.1f} ps ({o['name']})"
                                                for o in out))


def usable(r: dict) -> bool:
    return bool(r.get("feasible")) and bool(r.get("synth_ok")) and bool(r.get("area_um2")) and bool(r.get("delay_ps"))


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", help="the search run file (its review node and seed-relative gates are dropped)")
    ap.add_argument("--run-dir", required=True)
    ap.add_argument("--synth-repeats", type=int, default=3,
                    help="ABC mappings per synthesis, per-metric median (default 3, as the targets and chialu.pipeline)")
    ap.add_argument("--numeric", help="the numeric run file whose space is sampled (default <target>.numeric.yaml)")
    g = ap.add_argument_group("the protocol (default: the run file's search.extensions.calibration)")
    g.add_argument("--model", choices=("xgboost", "gnn"))
    g.add_argument("--min-delay-gap-pct", type=float)
    g.add_argument("--min-area-gap-pct", type=float)
    g.add_argument("--exhaustive-below", type=int, default=None, dest="exhaustive_below")
    g.add_argument("--target-rho", type=float, default=None, dest="target_rho")
    g.add_argument("--margin", type=float, default=None)
    g.add_argument("--confidence", type=float, default=None)
    g.add_argument("--initial-train", type=int, default=None, dest="initial_train")
    g.add_argument("--test-size", type=int, default=None, dest="test_size")
    g.add_argument("--max-rounds", type=int, default=None, dest="max_rounds")
    g.add_argument("--increment", type=int, default=None,
                   help="designs added to the training set after a failed certification round (default: the test size)")
    g.add_argument("--cv-floor", type=float, default=None, help="percent; a metric varying less needs no ranking")
    g.add_argument("--coverage-cap", type=int, default=3000, dest="coverage_cap",
                   help="forced training points at most, making every searched member occur (0: none)")
    g.add_argument("--min-per-scheme", type=int, default=None, dest="min_per_scheme",
                   help="measured training rows every sharing scheme must have; schemes are drawn balanced, the short "
                        "ones topped up, and the model is used only under schemes that reach it (default 20)")
    g.add_argument("--max-error-ratio", type=float, default=None, dest="max_error_ratio",
                   help="the largest holdout RMSE / spread of the measured designs a metric may have (default 0.5)")
    g.add_argument("--max-initial", type=int, default=1000,
                   help="cap on the initial training set derived from rows_per_column x one-hot columns")
    ap.add_argument("--verify", type=int, default=100, help="predicted-front points synthesized per search round")
    ap.add_argument("--refine", type=int, default=200, help="measured-front neighbours synthesized per round (0: none)")
    ap.add_argument("--refine-pool", type=int, default=40, dest="refine_pool",
                    help="neighbours drawn per front design (1-3 choices redrawn) before the model picks")
    ap.add_argument("--front-layers", type=int, default=3, dest="front_layers",
                    help="non-dominated layers counted as the front (refinement bases, weighted in the refit)")
    ap.add_argument("--front-weight", type=float, default=5.0, dest="front_weight",
                    help="sample weight of the front's rows when the model is refitted")
    ap.add_argument("--converge", type=float, default=0.005,
                    help="stop when two rounds in a row improve the measured front's hypervolume by less than this")
    ap.add_argument("--rounds", type=int, default=6,
                    help="NSGA-II/verify rounds; each after the first refits on the points verified so far")
    ap.add_argument("--schemes", type=int, default=6, help="sharing schemes NSGA-II runs under (one run each)")
    ap.add_argument("--iterations", type=int, default=3000, help="NSGA-II evaluations per scheme (surrogate predictions)")
    ap.add_argument("--population", type=int, default=40)
    ap.add_argument("--top", type=int, default=8, help="measured front points written as seeds")
    ap.add_argument("--prefix", default="front", help="seed name prefix in discovered.json (its earlier plans are replaced)")
    ap.add_argument("--inflight", type=int, default=50, help="whole-unit evaluations in flight on the cluster")
    ap.add_argument("--render-jobs", type=int, default=8, help="local processes rendering and pricing plans")
    ap.add_argument("--sharing-level", default="natural", choices=("natural", "all"))
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--stage", action="append", choices=("sample", "search", "seeds"),
                    help="run these steps alone (default: all; a rerun resumes the dataset)")
    ap.add_argument("--local", action="store_true", help="run the nodes in this process (no cluster)")
    ap.add_argument("--any-node", action="store_true",
                    help="let the cluster place evaluations on any node (by default they stay on the driver's node, "
                         "whose workers import this checkout)")
    a = ap.parse_args(argv)
    steps = a.stage or ["sample", "search", "seeds"]
    # gating: a step whose input an earlier step makes is refused when that input is missing, instead of
    # quietly running the earlier step (a search without a trained model would start sampling)
    out = Path(a.run_dir).resolve() / "surrogate"
    rep = json.loads((out / "report.json").read_text()) if (out / "report.json").is_file() else {}
    exhaustive = (rep.get("sample") or {}).get("mode") == "exhaustive"
    if "search" in steps and "sample" not in steps and not (out / "model.pkl").is_file() and not exhaustive:
        print(f"[surrogate] no trained model in {out} (model.pkl): run the sample step first "
              f"(chialu.surrogate_seeds ... --stage sample, or chialu.pipeline --stage train)", file=sys.stderr)
        return 2
    if "seeds" in steps and not ({"sample", "search"} & set(steps)) and not (out / "dataset.jsonl").is_file():
        print(f"[surrogate] no measured designs in {out} (dataset.jsonl): run the sample and search steps first "
              f"(chialu.pipeline --stage train --stage numeric)", file=sys.stderr)
        return 2
    st = Stage(a)
    # every invocation of a step, with its command line and random seed, stays in the report: a run
    # directory's dataset and front are the product of several invocations (sample, then search and seeds)
    inv = {"argv": [sys.executable, "-m", "chialu.surrogate_seeds"] + list(sys.argv[1:] if argv is None else argv),
           "stages": steps, "seed": a.seed, "synth_repeats": a.synth_repeats, "local": a.local,
           "started": time.strftime("%Y-%m-%d %H:%M:%S"), "exit": None}
    st.report.setdefault("invocations", []).append(inv)
    st.save_report()
    st.setup()
    bundle = st.sample() if ("sample" in steps or "search" in steps) else None
    if bundle and "search" in steps:
        # the front loop: search the model, synthesize its predicted front and the measured front's
        # neighbours, refit (heavier on the front), until the measured front stops improving
        hv0, box = st.front_hv()
        stale = 0
        for rnd in range(1, a.rounds + 1):
            if rnd > 1:
                bundle = st.retrain(rnd)
            recs = st.nsga(bundle, rnd)
            st.verify(bundle, recs, rnd)
            if a.refine > 0:
                st.refine(bundle, rnd)
            hv, _ = st.front_hv(box)
            gain = (hv - hv0) / hv0 if hv0 > 0 else float("inf")
            st.report.setdefault("search", {}).setdefault(f"round{rnd}", {})["front_hv"] = {"hv": round(hv, 5), "gain": round(gain, 5)}
            st.log(f"front round {rnd}: measured-front hypervolume {hv:.5f} ({100 * gain:+.2f}% over the previous round)")
            st.save_report()
            stale = stale + 1 if gain < a.converge else 0
            hv0 = hv
            if stale >= 2:
                st.log(f"front converged: two rounds under {100 * a.converge:.2f}% improvement")
                break
    if "seeds" in steps:
        st.seeds()
    st.pool.shutdown()
    inv.update(exit=0, finished=time.strftime("%Y-%m-%d %H:%M:%S"))
    st.save_report()
    st.log(f"report {st.out / 'report.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
