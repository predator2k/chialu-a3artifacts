"""Reproducible, synthesis-free surrogate ablations; see docs/surrogate.md.

``metrics(log_true, log_pred)`` and the JSON design-name splits are the public
comparison interface. Columns are always (area, delay), both natural logs.
No Ray, RTL generation, synthesis, or writes to the source dataset are needed.
"""
from __future__ import annotations

import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager
from functools import lru_cache
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

import numpy as np
from scipy.stats import kendalltau, spearmanr
from chialu.surrogate_metrics import pair_metrics, gap_threshold, front_indices, pareto_layers, ranking_score

VERSION = 1
REPO = Path(__file__).resolve().parents[1]
DATA_ROOT = Path("$A3EVAL/3rdparty/chialu/run")
SPLIT_ROOT = Path("$CHIALU_HOME/coeff/compare")
TARGETS = {"int_subword_alu": "targets/int_subword_alu.numeric.yaml",
           "fp_alu_cmp": "targets/eval/fp_alu_cmp.numeric.yaml",
           "fp_alu_cmp_hf": "targets/eval/fp_alu_cmp_hf.numeric.yaml"}
LADDER = ("B0", "B1", "B2", "B3", "B4")


def _json(path, data):
    """Atomic output, never a partial JSON checkpoint."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".new")
    tmp.write_text(json.dumps(data, indent=2, allow_nan=False) + "\n")
    tmp.replace(path)


def _digest(data):
    return hashlib.sha256(data).hexdigest()


def _code_digest():
    """Shared metric/feature code is part of checkpoint identity after extraction."""
    return _digest(b"".join((REPO / "chialu" / name).read_bytes() for name in
                            ("surrogate_compare.py", "surrogate_metrics.py", "surrogate_compare_features.py")))


def _number(value):
    return float(value) if np.isfinite(value) else None


def _correlation(a, b, kendall=False):
    if len(a) < 3 or np.ptp(a) == 0 or np.ptp(b) == 0:
        return None, None
    result = (kendalltau if kendall else spearmanr)(a, b)
    return _number(result.statistic), _number(result.pvalue)


def select_front(points, k=24):
    """Budgeted Pareto selection: peel layers, then spread in area order.

    The selection uses only the supplied coordinates. For predictions it never
    uses measured area, measured delay, or the measured-front membership.
    """
    points = np.asarray(points, float)
    if k < 1:
        raise ValueError("top_k must be positive")
    remaining, chosen = np.arange(len(points)), []
    while len(chosen) < min(k, len(points)):
        front = front_indices(points[remaining])
        need = k - len(chosen)
        take = front if len(front) <= need else front[np.linspace(0, len(front) - 1, need, dtype=int)]
        chosen.extend(remaining[take].tolist())
        keep = np.ones(len(remaining), dtype=bool)
        keep[front] = False
        remaining = remaining[keep]
    return np.asarray(chosen, dtype=int)


def hypervolume(points, reference):
    """Two-dimensional dominated hypervolume, on the supplied log axes."""
    points, reference = np.asarray(points, float), np.asarray(reference, float)
    p = points[np.all(points < reference, axis=1)]
    p = p[front_indices(p)]
    last, hv = reference[1], 0.0
    for area, delay in p:
        if delay < last:
            hv += (reference[0] - area) * (last - delay)
            last = delay
    return float(hv)


def hard_pairs(log_true, tolerance=0.02, min_delay_gap_pct=5):
    """All unordered close-area pairs; measured delay ties are uninformative."""
    y = np.asarray(log_true, float)
    order = np.argsort(y[:, 0], kind="stable")
    area = y[order, 0]
    ends = np.searchsorted(area, area + tolerance, side="left")
    left = np.repeat(np.arange(len(y)), np.maximum(ends - np.arange(len(y)) - 1, 0))
    right = np.concatenate([np.arange(i + 1, end) for i, end in enumerate(ends)]) if len(y) else np.empty(0, int)
    i, j = order[left], order[right]
    informative = (y[i, 1] != y[j, 1]) & (np.abs(y[i, 1] - y[j, 1]) >= gap_threshold(min_delay_gap_pct) - 1e-12)
    return i[informative], j[informative]


def metric_context(log_true, top_k=24, reference=None, sample_ids=None,
                   min_delay_gap_pct=5, min_area_gap_pct=2):
    """Reusable truth-only state; useful when scoring many models on one split."""
    y = np.asarray(log_true, float)
    if y.ndim != 2 or y.shape[1] != 2 or not len(y) or not np.isfinite(y).all():
        raise ValueError("expected nonempty finite (n, 2) natural-log targets")
    reference = np.max(y, axis=0) + 0.05 if reference is None else np.asarray(reference, float)
    # A bootstrap observation can be repeated for correlations/pair weights,
    # but synthesizing the same design twice must not consume two budget slots.
    selection = np.arange(len(y)) if sample_ids is None else np.unique(sample_ids, return_index=True)[1]
    selection_y = y[selection]
    return {"y": y, "layers": pareto_layers(y), "pairs": hard_pairs(y, min_delay_gap_pct=0),
            "min_delay_gap_pct": min_delay_gap_pct, "min_area_gap_pct": min_area_gap_pct, "top_k": top_k,
            "selection_indices": selection, "selection_layers": pareto_layers(selection_y, 1),
            "oracle_selection": select_front(selection_y, top_k), "reference": reference,
            "oracle_hv": hypervolume(y, reference)}


def metrics(log_true, log_pred, *, top_k=24, reference=None, context=None,
            min_delay_gap_pct=5, min_area_gap_pct=2):
    """Public metrics for XGBoost/GNN comparisons, ALL on natural-log targets.

    Undefined correlations/R²/normalized RMSE are None, never silently zero.
    Front correlations use the union of true layers 1--3, plus each layer.
    Hard pairs have |delta log area| < .02; predicted ties earn half credit.
    topk_recall compares budget-k Pareto selections; front_recall_at_k uses the
    entire true first front as denominator. HV regret evaluates the measured
    coordinates of the predicted selection against the entire true front.
    The default common reference is max(true log targets) + .05 per axis.
    """
    ctx = metric_context(log_true, top_k, reference, min_delay_gap_pct=min_delay_gap_pct,
                         min_area_gap_pct=min_area_gap_pct) if context is None else context
    y, p = ctx["y"], np.asarray(log_pred, float)
    if p.shape != y.shape or not np.isfinite(p).all():
        raise ValueError("predictions must be finite and have the targets' (n, 2) shape")
    out = {"n": len(y), "min_delay_gap_pct": ctx["min_delay_gap_pct"],
           "min_area_gap_pct": ctx["min_area_gap_pct"]}
    for col, name in enumerate(("area", "delay")):
        rho, pv = _correlation(y[:, col], p[:, col])
        rmse = float(np.sqrt(np.mean((p[:, col] - y[:, col]) ** 2)))
        std = float(np.std(y[:, col])) if np.ptp(y[:, col]) else 0.0
        out.update({name + "_rho_all_pairs": rho, name + "_p_all_pairs": pv, name + "_rmse": rmse,
                    name + "_std": std, name + "_rmse_std": rmse / std if std else None,
                    name + "_r2": 1 - (rmse / std) ** 2 if std else None})
        order = pair_metrics(y[:, col], p[:, col], ctx["min_" + name + "_gap_pct"])
        out.update({name + "_" + key: value for key, value in order.items() if key != "rho_all_pairs"})
    for prefix, mask in [("front", ctx["layers"] > 0)] + [
            (f"layer{layer}", ctx["layers"] == layer) for layer in (1, 2, 3)]:
        out[prefix + "_n"] = int(mask.sum())
        order = pair_metrics(y[mask, 1], p[mask, 1], ctx["min_delay_gap_pct"])
        out.update({prefix + "_" + key: value for key, value in order.items()})
        out[prefix + "_rho_all_pairs"], out[prefix + "_p_all_pairs"] = _correlation(y[mask, 1], p[mask, 1])
        out[prefix + "_tau_all_pairs"], out[prefix + "_tau_p_all_pairs"] = _correlation(y[mask, 1], p[mask, 1], True)
    order = pair_metrics(y[:, 1], p[:, 1], ctx["min_delay_gap_pct"], pairs=ctx["pairs"])
    out.update({"hard_" + key: value for key, value in order.items()})
    select_y, select_p = y[ctx["selection_indices"]], p[ctx["selection_indices"]]
    selected = select_front(select_p, ctx["top_k"])
    out["topk_recall"] = len(np.intersect1d(selected, ctx["oracle_selection"])) / len(selected)
    out["front_recall_at_k"] = float(np.sum(ctx["selection_layers"][selected] == 1) / np.sum(ctx["selection_layers"] == 1))
    hv = ctx["oracle_hv"]
    out["hv_regret"] = max(0.0, 1 - hypervolume(select_y[selected], ctx["reference"]) / hv) if hv else None
    predicted_front = front_indices(select_p)
    out["predicted_front_n"] = len(predicted_front)
    out["predicted_front_hv_regret"] = max(0.0, 1 - hypervolume(select_y[predicted_front], ctx["reference"]) / hv) if hv else None
    return out


def load_dataset(path):
    """Freeze complete lines of an append-only archive, filtering invalid labels."""
    raw = Path(path).read_bytes()
    rows, excluded, names = [], Counter(), set()
    lines = raw.splitlines(keepends=True)
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1 and not line.endswith(b"\n"):
                excluded["incomplete_tail"] += 1
                continue
            raise
        if row["name"] in names:
            raise ValueError(f"duplicate design name: {row['name']}")
        names.add(row["name"])
        if not row.get("feasible", True) or not row.get("synth_ok", True):
            excluded["infeasible_or_synthesis_failed"] += 1
            continue
        labels = [row.get("area_um2"), row.get("delay_ps")]
        if any(not isinstance(v, (float, int)) or not math.isfinite(v) or v <= 0 for v in labels):
            excluded["invalid_label"] += 1
            continue
        if not isinstance(row.get("vals"), dict) or not isinstance(row.get("feat"), dict):
            excluded["missing_inputs"] += 1
            continue
        rows.append(row)
    rows.sort(key=lambda r: r["name"])
    if not rows:
        raise ValueError(f"no usable measured designs: {path}")
    return rows, {"source": str(Path(path).resolve()), "sha256": _digest(raw), "bytes": len(raw),
                  "n": len(rows), "excluded": dict(excluded),
                  "sources": dict(Counter(r.get("source", "unknown") for r in rows)),
                  "schemes": dict(Counter(r["scheme"] for r in rows))}


def design_key(row):
    """Repeated measurements of the same declaration must stay on one side."""
    return _digest(json.dumps([row["scheme"], row["vals"]], sort_keys=True).encode())


def _holdout(rows, indices, seed, *, schemes=False):
    from sklearn.model_selection import GroupShuffleSplit
    indices = np.asarray(indices, dtype=int)
    groups = [rows[i]["scheme"] if schemes else design_key(rows[i]) for i in indices]
    if len(set(groups)) < 2:
        raise ValueError("a holdout needs at least two independent design/scheme groups")
    train, test = next(GroupShuffleSplit(n_splits=1, test_size=0.2, random_state=seed).split(indices, groups=groups))
    return indices[train], indices[test]


def make_splits(rows, seeds=range(5)):
    """S1 design holdout; S2 actual selected points only; S3 whole-scheme holdout.

    S3 leaves a random group of 20% of scheme names out for each seed (five
    repeated group holdouts, not exhaustive leave-one-of-144-schemes-out CV).
    Inner tuning splits obey the outer split's grouping policy.
    """
    all_i = np.arange(len(rows))
    initial = [i for i, r in enumerate(rows) if r.get("source") in ("round1", "coverage")]
    selected = [i for i, r in enumerate(rows) if str(r.get("source", "")).startswith(("verify", "refine"))
                or re.match(r"^(?:f\d+_|v\d+_)", r["name"])]
    selected_keys = {design_key(rows[i]) for i in selected}
    initial = [i for i in initial if design_key(rows[i]) not in selected_keys]
    folds = []
    skipped = {} if initial and selected else {"S2": "No measured model-selected/front-loop points, or no initial sample."}
    for seed in seeds:
        for protocol in ("S1", "S2", "S3"):
            if protocol == "S2":
                if protocol in skipped:
                    continue
                train, test = np.asarray(initial), np.asarray(selected)
            else:
                train, test = _holdout(rows, all_i, seed, schemes=protocol == "S3")
            inner_train, inner_valid = _holdout(rows, train, seed + 10000, schemes=protocol == "S3")
            fold = {"id": f"{protocol}_seed{seed}", "protocol": protocol, "seed": int(seed)}
            for key, idx in (("train", train), ("test", test), ("tune_train", inner_train), ("tune_valid", inner_valid)):
                fold[key] = [rows[i]["name"] for i in idx]
            folds.append(fold)
    return {"version": VERSION, "seeds": list(seeds), "skipped": skipped, "folds": folds,
            "protocol": {"S1": "80/20 grouped by design identity",
                         "S2": "round1+coverage -> measured verify/refine; later random rounds excluded",
                         "S3": "80/20 of scheme names, entire schemes withheld; repeated group holdout",
                         "tuning": "80/20 within outer training; same grouping as outer split"}}


def validate_splits(rows, splits):
    """Reject missing names or train/test leakage, including inner tuning."""
    by = {r["name"]: r for r in rows}
    identities = {n: design_key(r) for n, r in by.items()}
    seen = set()
    for fold in splits["folds"]:
        if fold["id"] in seen:
            raise ValueError(f"duplicate split id: {fold['id']}")
        seen.add(fold["id"])
        for key in ("train", "test", "tune_train", "tune_valid"):
            names = fold[key]
            if not names or len(set(names)) != len(names) or not set(names) <= set(by):
                raise ValueError(f"{fold['id']} {key}: empty, duplicate, or unknown names")
        if set(fold["tune_train"]) | set(fold["tune_valid"]) != set(fold["train"]):
            raise ValueError(f"{fold['id']}: tuning must partition the outer training set")
        for a, b in (("train", "test"), ("tune_train", "tune_valid")):
            if {identities[n] for n in fold[a]} & {identities[n] for n in fold[b]}:
                raise ValueError(f"{fold['id']}: design leakage between {a}/{b}")
            if fold["protocol"] == "S3" and {by[n]["scheme"] for n in fold[a]} & {by[n]["scheme"] for n in fold[b]}:
                raise ValueError(f"{fold['id']}: scheme leakage between {a}/{b}")


def context_of(numeric):
    """Bind the spec without creating a run, rendering RTL, or connecting to Ray."""
    import yaml
    import chialu.priors  # noqa: F401 - template registration
    from adir.instance import Instance, _bind_variables
    from adir.registry import get_template
    from chialu.modules.generators import spec_of
    from chialu.targets.rtl.alu_seed import structure_manifest
    from chialu.surrogate_features import manifest_table
    from chialu.surrogate_seeds import estimate_inputs
    inst = Instance()
    inst.path = Path(numeric).resolve()
    inst.base_dir = inst.path.parent
    inst.raw = yaml.safe_load(inst.path.read_text())["adir"]
    inst.search = inst.raw["search"]
    inst.template = get_template(inst.raw["module"])
    _bind_variables(inst, inst.raw["variables"])
    spec = spec_of(inst.ctx())
    return {"files": {"spec.json": json.dumps(spec)}, "table": manifest_table(structure_manifest(spec)),
            "est": estimate_inputs(inst.path)}


def db_signature(pdk):
    from chialu.synthdb import db_dir
    root = db_dir(pdk)
    files = sorted(root.rglob("*.jsonl"))
    if not files:
        raise ValueError(f"no synthesis DB rows in {root}; set CHIALU_SYNTH_DIR to a populated DB")
    return {"root": str(root.resolve()), "files": {str(p.relative_to(root)): _digest(p.read_bytes()) for p in files}}


@contextmanager
def frozen_lookups():
    """Cache read-only DB views for this single-process snapshot pass only.

    The normal reader deliberately reloads shards to see concurrent rebuilds.
    An offline comparison instead verifies the DB signature before/after the
    pass. Cache its immutable views and default points, restoring all functions
    on exit; estimate_structure still performs its original interpolation and
    pin-delta calculation. No DB/cache file is written in the source tree.
    """
    from chialu import synthdb
    originals = {name: getattr(synthdb, name) for name in ("views", "at_width", "point_of")}

    @lru_cache(maxsize=None)
    def point(kind, family, pins):
        return originals["point_of"](kind, family, json.loads(pins))

    synthdb.views = lru_cache(maxsize=None)(synthdb.views)
    synthdb.at_width = lru_cache(maxsize=None)(synthdb.at_width)
    synthdb.point_of = lambda kind, family, pins: point(kind, family, json.dumps(pins, sort_keys=True))
    try:
        yield
    finally:
        for name, original in originals.items():
            setattr(synthdb, name, original)


def augment(rows, ctx, cache, recompute_base=False, require_cache_key=None):
    """One estimate lookup per design, with an input/DB/code-addressed cache."""
    from adir.registry import underlying
    from chialu import eda
    from chialu.surrogate_features import nest, row_features, plan_features
    from chialu.surrogate_compare_features import path_features, value_count_features
    db = db_signature(ctx["est"]["pdk"])
    identity = {"db": db, "context": ctx, "recompute_base": recompute_base, "feature_version": VERSION,
                "flow_policy": os.environ.get("CHIALU_DB_FLOW", "warn"),
                "code": {n: _digest((REPO / "chialu" / n).read_bytes()) for n in (
                    "surrogate_features.py", "surrogate_compare_features.py", "eda.py", "synthdb.py", "plans.py")},
                "inputs": _digest(json.dumps(rows, sort_keys=True).encode())}
    key = _digest(json.dumps(identity, sort_keys=True).encode())
    if require_cache_key is not None and key != require_cache_key:
        raise ValueError("feature inputs changed; choose a new --output to preserve existing predictions")
    meta = cache.with_suffix(".meta.json")
    if cache.exists() and meta.exists() and json.loads(meta.read_text()).get("key") == key:
        with gzip.open(cache, "rt") as handle:
            augmented = [json.loads(line) for line in handle]
        print(f"reusing {len(augmented)} cached feature rows", flush=True)
        return augmented, json.loads(meta.read_text())
    result, mismatch, missing = [], 0, 0
    start = time.monotonic()
    est, table = ctx["est"], ctx["table"]
    for i, row in enumerate(rows):
        r = underlying(eda.estimate)(ctx["files"], nest(row["vals"]), est["pdk"], est["effort"], 1.0, 1.0,
                                    json.dumps(row.get("plan") or {}), est["glue_json"], est["context_json"])
        if not r.get("ok"):
            raise ValueError(f"estimate failed for {row['name']}: {r.get('detail')}")
        missing += bool(r.get("missing"))
        recalculated = {"EST__area": float(r["area_um2"]), "EST__delay": float(r["delay_ps"]),
                        "EST__coverage": float(r["coverage"])}
        recalculated.update(row_features(r["rows"], table, row["plan"]))
        recalculated.update(plan_features(row["scheme"], row["plan"], table))
        recalculated.update({k: v for k, v in row["feat"].items() if k.startswith("OH__")})
        mismatch += any(abs(recalculated.get(k, 0) - row["feat"].get(k, 0)) > 1e-5
                        for k in set(recalculated) | set(row["feat"]))
        result.append({"name": row["name"], "base": recalculated if recompute_base else row["feat"],
                       "path": path_features(r["rows"], table, row["plan"]),
                       "counts": value_count_features(row["vals"]), "rows": r["rows"]})
        if (i + 1) % 500 == 0:
            print(f"features {i + 1}/{len(rows)}, {time.monotonic() - start:.1f}s", flush=True)
    info = {"key": key, "identity": identity, "seconds": time.monotonic() - start,
            "legacy_mismatch_designs": mismatch, "designs_missing_db_rows": missing}
    if db_signature(est["pdk"]) != db:
        raise ValueError("synthesis DB changed during feature preparation; use a stable DB snapshot")
    cache.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(cache, "wt") as handle:
        for row in result:
            handle.write(json.dumps(row) + "\n")
    _json(meta, info)
    return result, info


def _matrix(feats, train, other):
    """Training-only vocabulary, explicit zeroes exactly as surrogate_seeds.fit."""
    from sklearn.feature_extraction import DictVectorizer
    vec = DictVectorizer(sparse=False, dtype=np.float32, sort=True)
    x = vec.fit_transform([feats[i] for i in train])
    return x, vec.transform([feats[i] for i in other]), vec.feature_names_


def tuning_grid():
    from chialu.surrogate_seeds import XGB
    return [dict(XGB), dict(n_estimators=600, max_depth=3, learning_rate=0.05,
                           min_child_weight=4, subsample=0.9, colsample_bytree=0.9),
            dict(n_estimators=400, max_depth=7, learning_rate=0.05, min_child_weight=4,
                 subsample=0.85, colsample_bytree=0.8),
            dict(n_estimators=800, max_depth=5, learning_rate=0.03, min_child_weight=6,
                 reg_lambda=5, subsample=0.9, colsample_bytree=0.9)]


def _regressor(x, y, params, seed, jobs):
    from xgboost import XGBRegressor
    m = XGBRegressor(**params, random_state=seed, n_jobs=jobs, verbosity=0)
    return m.fit(x, y)


def rank_labels(log_y, schemes, grouping, objective):
    """Sorted query groups, and labels where larger always means faster.

    Pairwise keeps continuous delay ordering. NDCG uses integer relevance 0..7
    from training-only delay octiles (including its required nonnegative range).
    """
    if objective not in ("rank:pairwise", "rank:ndcg"):
        raise ValueError(f"unknown ranking objective: {objective}")
    if grouping == "area":
        raw = np.floor(log_y[:, 0] / 0.02).astype(int)
    elif grouping == "scheme":
        raw = np.asarray(schemes)
    else:
        raise ValueError(f"unknown ranking grouping: {grouping}")
    _, qid = np.unique(raw, return_inverse=True)
    if objective == "rank:ndcg":
        cuts = np.quantile(log_y[:, 1], np.arange(1, 8) / 8)
        relevance = 7 - np.searchsorted(cuts, log_y[:, 1], side="left")
    else:
        relevance = -log_y[:, 1]
    order = np.argsort(qid, kind="stable")
    return order, qid[order], relevance[order]


def _ranker(x, y, schemes, params, seed, jobs, objective, grouping):
    from xgboost import XGBRanker
    order, qid, labels = rank_labels(y, schemes, grouping, objective)
    # LambdaRank Hessians have a different scale from squared-error Hessians.
    # Regression's min_child_weight=4/6 can prevent any NDCG split at all.
    params = dict(params, min_child_weight=0.1)
    m = XGBRanker(**params, random_state=seed, n_jobs=jobs, verbosity=0,
                  objective=objective, lambdarank_pair_method="mean", lambdarank_num_pair_per_sample=8)
    return m.fit(x[order], labels, qid=qid)


def _calibration(model, xtrain, xvalid, yvalid):
    """Held-out affine score -> log-delay calibration after train-score scaling.

    A refit can change arbitrary rank-score scale. Standardize by each model's
    training scores; fit the decreasing map only on the inner validation set.
    Neither calibration nor query groups ever see outer-test labels.
    """
    scores = model.predict(xtrain)
    z = (model.predict(xvalid) - scores.mean()) / max(float(scores.std()), 1e-12)
    slope = float(np.mean((z - z.mean()) * (yvalid - yvalid.mean())) / max(float(z.var()), 1e-12))
    slope = min(-1e-9, slope)
    return {"intercept": float(yvalid.mean() - slope * z.mean()), "slope": slope}


def run_fold(rows, augmented, fold, jobs, output, gaps=None):
    """Fit a complete ablation ladder on one saved outer/inner split."""
    gaps = gaps or {}
    lookup = {r["name"]: i for i, r in enumerate(rows)}
    tr, te, itr, iva = ([lookup[n] for n in fold[key]] for key in ("train", "test", "tune_train", "tune_valid"))
    y = np.log([[r["area_um2"], r["delay_ps"]] for r in rows])
    seed = fold["seed"]
    base = [r["base"] for r in augmented]
    path = [dict(r["base"], **r["path"]) for r in augmented]
    counts = [dict(r["base"], **r["path"], **r["counts"]) for r in augmented]
    xt, xv, _ = _matrix(base, itr, iva)
    grid, best, tuning = tuning_grid(), {}, {"regression": {}, "ranking": []}
    for col, target in enumerate(("area", "delay")):
        trials = []
        for params in grid:
            started = time.monotonic()
            m = _regressor(xt, y[itr, col], params, seed, jobs)
            p = m.predict(xv)
            score = -float(np.mean((p - y[iva, col]) ** 2)) if col == 0 else ranking_score(y[iva], p, gaps.get("min_delay_gap_pct", 5))
            trials.append({"params": params, "score": score, "seconds": time.monotonic() - started})
            print(f"{fold['id']} {target} tuning depth={params['max_depth']} trees={params['n_estimators']}: "
                  f"{score:.4f}, {trials[-1]['seconds']:.1f}s", flush=True)
        best[target] = max(trials, key=lambda t: t["score"])["params"]
        tuning["regression"][target] = trials
        print(f"{fold['id']} tuned {target}: {best[target]}", flush=True)
    del xt, xv
    predictions, dimensions = {}, {}
    for name, feats in (("B0", base), ("B1", base), ("B2", path), ("B3", counts)):
        xt, xe, names = _matrix(feats, tr, te)
        prediction = []
        for col, target in enumerate(("area", "delay")):
            params = grid[0] if name == "B0" else best[target]
            prediction.append(_regressor(xt, y[tr, col], params, seed, jobs).predict(xe))
        predictions[name] = np.column_stack(prediction)
        dimensions[name] = len(names)
        del xt, xe
        print(f"{fold['id']} {name} fitted", flush=True)
    xt, xv, _ = _matrix(counts, itr, iva)
    for objective in ("rank:pairwise", "rank:ndcg"):
        for grouping in ("area", "scheme"):
            m = _ranker(xt, y[itr], [rows[i]["scheme"] for i in itr], best["delay"], seed, jobs, objective, grouping)
            score = ranking_score(y[iva], -m.predict(xv), gaps.get("min_delay_gap_pct", 5))
            calibration = _calibration(m, xt, xv, y[iva, 1])
            tuning["ranking"].append({"objective": objective, "grouping": grouping,
                                       "score": score, "calibration": calibration})
    rank = max(tuning["ranking"], key=lambda t: t["score"])
    del xt, xv
    xt, xe, names = _matrix(counts, tr, te)
    m = _ranker(xt, y[tr], [rows[i]["scheme"] for i in tr], best["delay"], seed, jobs, rank["objective"], rank["grouping"])
    train_scores = m.predict(xt)
    z = (m.predict(xe) - train_scores.mean()) / max(float(train_scores.std()), 1e-12)
    p = rank["calibration"]["intercept"] + rank["calibration"]["slope"] * z
    predictions["B4"] = np.column_stack((predictions["B3"][:, 0], p))
    dimensions["B4"] = len(names)
    ctx = metric_context(y[te], **gaps)
    report = {"fold": fold["id"], "protocol": fold["protocol"], "seed": seed,
              "train_n": len(tr), "test_n": len(te), "dimensions": dimensions,
              "tuning": tuning, "chosen": {**best, "rank": rank},
              "metrics": {k: metrics(y[te], p, context=ctx) for k, p in predictions.items()}}
    _json(output.with_suffix(".json"), report)
    np.savez_compressed(output.with_suffix(".npz"), names=np.asarray(fold["test"]), truth=y[te], **predictions)
    return report


CI_METRICS = ("area_rho", "area_r2", "area_rmse", "area_rmse_std", "delay_rho", "delay_r2",
              "delay_rmse", "delay_rmse_std", "front_rho", "front_tau", "hard_accuracy",
              "topk_recall", "front_recall_at_k", "hv_regret")
LOWER_BETTER = {"area_rmse", "area_rmse_std", "delay_rmse", "delay_rmse_std", "hv_regret"}


def paired_bootstrap(log_true, baseline, candidate, *, n_bootstrap=300, seed=0, top_k=24,
                     min_delay_gap_pct=5, min_area_gap_pct=2):
    """Paired design bootstrap of one held-out test set (positive delta = gain).

    Recompute fronts and hard pairs within every sampled design set; reuse the
    original test reference point. A draw always selects the same designs for
    both models. Return the effective replicate count for undefined metrics.
    """
    y, b, c = map(np.asarray, (log_true, baseline, candidate))
    reference = y.max(axis=0) + 0.05
    gaps = dict(min_delay_gap_pct=min_delay_gap_pct, min_area_gap_pct=min_area_gap_pct)
    full_ctx = metric_context(y, top_k, reference, **gaps)
    bm, cm = metrics(y, b, context=full_ctx), metrics(y, c, context=full_ctx)
    draws = {key: [] for key in CI_METRICS}
    rng = np.random.default_rng(seed)
    for _ in range(n_bootstrap):
        take = rng.integers(0, len(y), len(y))
        ctx = metric_context(y[take], top_k, reference, sample_ids=take, **gaps)
        mb, mc = metrics(y[take], b[take], context=ctx), metrics(y[take], c[take], context=ctx)
        for key in draws:
            if mb[key] is not None and mc[key] is not None:
                draws[key].append((mb[key] - mc[key]) if key in LOWER_BETTER else (mc[key] - mb[key]))
    result = {}
    for key, values in draws.items():
        delta = None if bm[key] is None or cm[key] is None else (
            bm[key] - cm[key] if key in LOWER_BETTER else cm[key] - bm[key])
        result[key] = {"gain": delta, "ci95": np.quantile(values, [.025, .975]).tolist() if values else None,
                       "valid_replicates": len(values)}
    return result


def summarize(reports, output, n_bootstrap, gaps=None):
    """Paired bootstrap, clustering repeated test appearances by design name.

    A single multinomial resampling of unique test designs supplies weights to
    every fold. Thus a design appearing in several seeds is never counted as
    independent evidence. Fits/splits stay fixed; these intervals quantify test
    design sampling uncertainty, not model-selection or synthesis-run noise.
    """
    gaps = gaps or {"min_delay_gap_pct": 5, "min_area_gap_pct": 2}
    # Re-score saved log arrays when thresholds change; never reuse stale fold metrics.
    reports = [dict(r) for r in reports]
    for r in reports:
        with np.load(output / (r["fold"] + ".npz")) as saved:
            r["metrics"] = {m: metrics(saved["truth"], saved[m], **gaps) for m in LADDER}
        _json(output / (r["fold"] + ".json"), r)
    identity = {"method": "shared-design-bootstrap-v2", "gaps": gaps, "replicates": n_bootstrap,
                "metrics_code_sha256": _code_digest(),
                "predictions": {r["fold"]: _digest((output / (r["fold"] + ".npz")).read_bytes()) for r in reports}}
    summary_path = output / "summary.json"
    if summary_path.exists():
        existing = json.loads(summary_path.read_text())
        if existing.get("identity") == identity and existing.get("complete"):
            return existing
    summary = {"identity": identity, "complete": False,
               "ci_method": "paired bootstrap clustered by design name across seeds; positive gain is better; fits fixed",
               "n_bootstrap": n_bootstrap, "protocols": {}}
    for protocol in sorted({r["protocol"] for r in reports}):
        group = [r for r in reports if r["protocol"] == protocol]
        table = {}
        for model in LADDER:
            table[model] = {}
            for key in group[0]["metrics"][model]:
                values = [r["metrics"][model][key] for r in group if r["metrics"][model][key] is not None]
                # P-values are per-fold evidence and are not averaged.
                table[model][key] = values if key.endswith(("_p", "_p_all_pairs")) or any(isinstance(v, dict) for v in values) else (float(np.mean(values)) if values else None)
        summary["protocols"][protocol] = {"mean_metrics": table, "folds": [r["fold"] for r in group]}
    loaded = {r["fold"]: dict(np.load(output / (r["fold"] + ".npz"))) for r in reports}
    names = sorted({str(n) for saved in loaded.values() for n in saved["names"]})
    index = {n: i for i, n in enumerate(names)}
    by_fold = {f: np.asarray([index[str(n)] for n in s["names"]]) for f, s in loaded.items()}
    # Each bootstrap row is shared across folds/models, including all undefined
    # metric positions. This alignment matters when taking the mean of seeds.
    draws = {f: {m: np.full((n_bootstrap, len(CI_METRICS)), np.nan) for m in LADDER} for f in loaded}
    rng = np.random.default_rng(20000)
    for boot in range(n_bootstrap):
        multiplicity = np.bincount(rng.integers(0, len(names), len(names)), minlength=len(names))
        for fold, saved in loaded.items():
            take = np.repeat(np.arange(len(saved["truth"])), multiplicity[by_fold[fold]])
            if not len(take):
                continue
            y = saved["truth"][take]
            ctx = metric_context(y, reference=saved["truth"].max(axis=0) + .05, sample_ids=take, **gaps)
            for model in LADDER:
                measured = metrics(y, saved[model][take], context=ctx)
                draws[fold][model][boot] = [measured[k] if measured[k] is not None else np.nan for k in CI_METRICS]
        if (boot + 1) % 25 == 0:
            print(f"paired design bootstrap {boot + 1}/{n_bootstrap}", flush=True)

    def intervals(point, samples):
        result = {}
        for baseline, models in (("B0", LADDER[1:]), ("B1", LADDER[2:])):
            result["vs_" + baseline] = {}
            for model in models:
                entry = {}
                for col, key in enumerate(CI_METRICS):
                    sign = -1 if key in LOWER_BETTER else 1
                    values = sign * (samples[model][:, col] - samples[baseline][:, col])
                    values = values[np.isfinite(values)]
                    a, b = point[model][key], point[baseline][key]
                    entry[key] = {"gain": sign * (a - b) if a is not None and b is not None else None,
                                  "ci95": np.quantile(values, [.025, .975]).tolist() if len(values) else None,
                                  "valid_replicates": len(values)}
                result["vs_" + baseline][model] = entry
        return result

    for report in reports:
        _json(output / (report["fold"] + ".ci.json"), intervals(report["metrics"], draws[report["fold"]]))
    for protocol, group in summary["protocols"].items():
        samples = {}
        for model in LADDER:
            values = np.stack([draws[f][model] for f in group["folds"]])
            count = np.sum(np.isfinite(values), axis=0)
            samples[model] = np.divide(np.nansum(values, axis=0), count,
                                      out=np.full(count.shape, np.nan), where=count > 0)
        group["paired_ci"] = intervals(group["mean_metrics"], samples)
    summary["complete"] = True
    _json(summary_path, summary)
    return summary


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=tuple(TARGETS), default="int_subword_alu")
    parser.add_argument("--dataset", type=Path)
    parser.add_argument("--numeric", type=Path)
    parser.add_argument("--output", type=Path, default=REPO / "run/surrogate_compare/results")
    parser.add_argument("--splits-dir", type=Path, default=SPLIT_ROOT)
    parser.add_argument("--seeds", type=int, nargs="+", default=list(range(5)))
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument("--workers", type=int, default=1, help="Independent folds in parallel; workers*jobs+1 <= 30")
    parser.add_argument("--bootstrap", type=int, default=300)
    parser.add_argument("--recompute-base", action="store_true", help="Reprice B0 too, required when changing the DB")
    parser.add_argument("--prepare-only", action="store_true")
    parser.add_argument("--summarize-only", action="store_true")
    parser.add_argument("--calibration", type=Path, help="Search YAML supplying the minimum gaps")
    parser.add_argument("--min-delay-gap-pct", type=float)
    parser.add_argument("--min-area-gap-pct", type=float)
    args = parser.parse_args(argv)
    from chialu.surrogate_seeds import calibration_knobs
    cal = calibration_knobs(args.calibration or REPO / TARGETS[args.target].replace(".numeric", ""), args)
    gaps = {k: cal[k] for k in ("min_delay_gap_pct", "min_area_gap_pct")}
    if args.jobs < 1 or args.workers < 1 or args.workers * args.jobs + 1 > 30 or args.bootstrap < 1:
        parser.error("workers/jobs must be positive, workers*jobs+1 <= 30, and bootstrap must be positive")
    if min(args.seeds) < 0 or len(set(args.seeds)) != len(args.seeds):
        parser.error("seeds must be distinct nonnegative integers")
    # These limits cover libraries loaded lazily below as well as XGBoost.
    from threadpoolctl import threadpool_limits
    threadpool_limits(limits=args.jobs, user_api="openmp")
    threadpool_limits(limits=1, user_api="blas")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    dataset = args.dataset or DATA_ROOT / (args.target + ".surrogate2") / "surrogate/dataset.jsonl"
    rows, data_info = load_dataset(dataset)
    manifest_path = output / "manifest.json"
    completed = bool(list(output.glob("S*_seed*.npz")))
    recorded = json.loads(manifest_path.read_text()) if manifest_path.exists() else None
    if completed and (recorded is None or recorded["dataset"]["sha256"] != data_info["sha256"]
                      or recorded["seeds"] != args.seeds):
        raise ValueError("output holds a different dataset/split; choose a new --output")
    splits_path = args.splits_dir / ("splits_" + args.target + ".json")
    if splits_path.exists():
        splits = json.loads(splits_path.read_text())
        if splits.get("dataset_sha256") != data_info["sha256"] or splits.get("seeds") != args.seeds:
            raise ValueError(f"frozen split inputs changed: {splits_path}; use a different --splits-dir")
    else:
        splits = make_splits(rows, args.seeds)
        splits["dataset_sha256"] = data_info["sha256"]
        splits["target"] = args.target
        _json(splits_path, splits)
    validate_splits(rows, splits)
    if not completed:
        _json(output / "splits.json", splits)
        _json(output / "dataset.json", data_info)
    for protocol, reason in splits["skipped"].items():
        print(f"{protocol} unavailable: {reason}", flush=True)
    if args.summarize_only:
        reports = [json.loads((output / (fold["id"] + ".json")).read_text()) for fold in splits["folds"]]
        summarize(reports, output, args.bootstrap, gaps)
        return 0
    ctx = context_of(args.numeric or REPO / TARGETS[args.target])
    if completed and any(recorded[key] != value for key, value in {
            "context": ctx, "jobs": args.jobs, "workers": args.workers,
            "recomputed_base": args.recompute_base, "training_code_sha256": _code_digest()}.items()):
        raise ValueError("training settings changed; choose a new --output to preserve existing predictions")
    with frozen_lookups():
        augmented, feature_info = augment(rows, ctx, output / "features.jsonl.gz", args.recompute_base,
                                         recorded["feature_cache_key"] if completed else None)
    import scipy
    import sklearn
    import xgboost
    manifest = {"version": VERSION, "dataset": data_info, "feature_cache_key": feature_info["key"],
                "db": feature_info["identity"]["db"], "context": ctx,
                "recomputed_base": args.recompute_base, "legacy_mismatch_designs": feature_info["legacy_mismatch_designs"],
                "jobs": args.jobs, "workers": args.workers, "seeds": args.seeds,
                "training_code_sha256": _code_digest(),
                "grid": tuning_grid(), "bootstrap": args.bootstrap, "gaps": gaps,
                "versions": {"numpy": np.__version__, "scipy": scipy.__version__,
                             "sklearn": sklearn.__version__, "xgboost": xgboost.__version__}}
    if manifest_path.exists() and json.loads(manifest_path.read_text()) != manifest and list(output.glob("S*_seed*.npz")):
        raise ValueError(f"run settings changed: {manifest_path}; choose a new --output")
    _json(manifest_path, manifest)
    if args.prepare_only:
        return 0
    reports, pending = [], []
    for fold in splits["folds"]:
        checkpoint = output / (fold["id"] + ".json")
        if checkpoint.exists() and checkpoint.with_suffix(".npz").exists():
            report = json.loads(checkpoint.read_text())
            print(f"reusing {fold['id']} predictions", flush=True)
        else:
            pending.append(fold)
            continue
        reports.append(report)
    # Threads share the immutable feature dictionaries; each XGBoost fit has a
    # bounded CPU team. There is no fork after OpenMP initialization.
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = [pool.submit(run_fold, rows, augmented, fold, args.jobs, output / fold["id"], gaps) for fold in pending]
        for future in as_completed(futures):
            reports.append(future.result())
    reports.sort(key=lambda r: r["fold"])
    summarize(reports, output, args.bootstrap, gaps)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
