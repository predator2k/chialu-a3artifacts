"""The PPA surrogate over ADIR's candidate records: a regressor from a
declaration block to the mapped area and delay, one model pair per PDK
under ml/models, which chialu.priors reads as the `chialu_structure_area`
prior (`search.seeds.rank.prior` in a run file).

Data: results_db.jsonl archives (`archive.path` under a run directory,
or the shared file several runs append to). A usable record carries a
`synth_ppa` measurement with `ok` true on the given PDK and a
declaration block. The features are the block's own VAR values
(chialu.priors.declaration_features), which is what ADIR's seed ranker
hands the prior, so a decision at its default counts in neither place.

Usage:
    python3 ml/surrogate.py train --pdk nangate45 [run/*/results_db.jsonl]
    python3 ml/surrogate.py check --pdk nangate45 [run/*/results_db.jsonl]
    python3 ml/surrogate.py warm  --pdk nangate45 --max-delay 12000 [run/*/results_db.jsonl]

train: fits the area and delay regressors, reports the holdout MAE and
       saves ml/models/<pdk>.<target>.pkl.
check: the predicted-versus-measured table of the trained models over
       the records, with the rank correlation.
warm:  the archived candidate of least area under a delay bound, with
       its source_path, which a run file lists under `search.seeds.files`.
"""

from __future__ import annotations

import argparse
import glob
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from chialu.priors import (MODELS, declaration_features, feature_vector,  # noqa: E402
                           load_model)

DEFAULT_DBS = str(REPO_ROOT / "run" / "*" / "results_db.jsonl")
TARGETS = ("area_um2", "abc_delay_ps")


def load_rows(paths: list, pdk: str) -> list:
    """The usable rows of the archives: one per record with a successful
    synth_ppa on `pdk`, the same candidate of the same run counted once."""
    rows, seen = [], set()
    for path in paths:
        with open(path) as f:
            for line in f:
                if not line.strip():
                    continue
                r = json.loads(line)
                sp = ((r.get("measurements") or {}).get("synth_ppa") or {}).get("value") or {}
                if not sp.get("ok") or sp.get("pdk") != pdk or sp.get("area_um2") is None:
                    continue
                key = (r.get("run"), r.get("candidate_id"), r.get("source_sha256"))
                if key in seen:
                    continue
                seen.add(key)
                rows.append({"run": r.get("run"), "candidate_id": r.get("candidate_id"),
                             "unit_id": r.get("unit_id"), "source_path": r.get("source_path"),
                             "area_um2": float(sp["area_um2"]),
                             "abc_delay_ps": sp.get("abc_delay_ps"),
                             "vars": (r.get("declarations") or {}).get("vars") or {}})
    return rows


def featurize(rows: list):
    """(X, vocab): the feature counts of every row's block over the
    vocabulary of the rows."""
    feats = [declaration_features(r["vars"]) for r in rows]
    vocab = sorted({k for f in feats for k in f})
    return [feature_vector(f, vocab) for f in feats], vocab


def _fit(X, y):
    try:
        from xgboost import XGBRegressor
        m = XGBRegressor(n_estimators=300, max_depth=5, learning_rate=0.08, subsample=0.9)
    except ImportError:
        from sklearn.ensemble import GradientBoostingRegressor
        m = GradientBoostingRegressor(n_estimators=300, max_depth=4)
    m.fit(X, y)
    return m


def cmd_train(args) -> int:
    rows = load_rows(args.db, args.pdk)
    if len(rows) < args.min_rows:
        print(f"[surrogate] {len(rows)} usable rows on {args.pdk}; {args.min_rows} needed "
              f"(--min-rows)")
        return 1
    X, vocab = featurize(rows)
    import pickle
    MODELS.mkdir(parents=True, exist_ok=True)
    report = {}
    for target in TARGETS:
        keep = [i for i, r in enumerate(rows) if r[target] is not None]
        Xt = [X[i] for i in keep]
        y = [float(rows[i][target]) for i in keep]
        if len(y) < 2:
            report[target] = {"rows": len(y), "skipped": "too few rows"}
            continue
        cut = max(1, len(y) // 5)
        m_cv = _fit(Xt[:-cut], y[:-cut]) if len(y) - cut >= 1 else None
        mae = None
        if m_cv is not None:
            pred = m_cv.predict(Xt[-cut:])
            mae = sum(abs(float(p) - t) for p, t in zip(pred, y[-cut:])) / cut
        m = _fit(Xt, y)
        with (MODELS / f"{args.pdk}.{target}.pkl").open("wb") as f:
            pickle.dump({"model": m, "vocab": vocab, "pdk": args.pdk, "target": target,
                         "rows": len(y)}, f)
        report[target] = {"rows": len(y), "features": len(vocab),
                          "holdout_mae": None if mae is None else round(float(mae), 2)}
    print(json.dumps(report, indent=1))
    return 0


def _rank_correlation(a: list, b: list):
    """Spearman's rank correlation of two equal-length lists, None for
    fewer than three points or a constant list."""
    n = len(a)
    if n < 3:
        return None

    def ranks(v):
        order = sorted(range(n), key=lambda i: v[i])
        r = [0.0] * n
        i = 0
        while i < n:
            j = i
            while j + 1 < n and v[order[j + 1]] == v[order[i]]:
                j += 1
            for k in range(i, j + 1):
                r[order[k]] = (i + j) / 2 + 1
            i = j + 1
        return r
    ra, rb = ranks(a), ranks(b)
    ma, mb = sum(ra) / n, sum(rb) / n
    cov = sum((x - ma) * (y - mb) for x, y in zip(ra, rb))
    va = sum((x - ma) ** 2 for x in ra)
    vb = sum((y - mb) ** 2 for y in rb)
    if va == 0 or vb == 0:
        return None
    return cov / (va * vb) ** 0.5


def cmd_check(args) -> int:
    rows = load_rows(args.db, args.pdk)
    if not rows:
        print(f"[surrogate] no usable rows on {args.pdk}")
        return 1
    bundles = {t: load_model(args.pdk, t) for t in TARGETS}
    if not any(bundles.values()):
        print(f"[surrogate] no model under {MODELS} for {args.pdk}; run train first")
        return 1
    print(f"| run | candidate | measured area | predicted area | measured delay | predicted delay |")
    print("| --- | --- | --- | --- | --- | --- |")
    measured = {t: [] for t in TARGETS}
    predicted = {t: [] for t in TARGETS}
    for r in rows:
        feats = declaration_features(r["vars"])
        cells = [r["run"], r["candidate_id"]]
        for t in TARGETS:
            b = bundles[t]
            p = float(b["model"].predict([feature_vector(feats, b["vocab"])])[0]) if b else None
            if r[t] is not None and p is not None:
                measured[t].append(float(r[t]))
                predicted[t].append(p)
            cells += ["-" if r[t] is None else f"{float(r[t]):.4g}",
                      "-" if p is None else f"{p:.4g}"]
        print("| " + " | ".join(str(c) for c in cells) + " |")
    for t in TARGETS:
        rho = _rank_correlation(measured[t], predicted[t])
        mae = (sum(abs(p - m) for p, m in zip(predicted[t], measured[t])) / len(measured[t])
               if measured[t] else None)
        print(f"\n{t}: {len(measured[t])} rows, MAE {mae if mae is None else round(mae, 2)}, "
              f"rank correlation {rho if rho is None else round(rho, 3)}")
    return 0


def cmd_warm(args) -> int:
    rows = load_rows(args.db, args.pdk)
    if args.unit_id:
        rows = [r for r in rows if r["unit_id"] == args.unit_id]
    if not rows:
        print("no archived candidate")
        return 1
    within = [r for r in rows if args.max_delay is None
              or (r["abc_delay_ps"] is not None and r["abc_delay_ps"] <= args.max_delay)]
    if within:
        best = min(within, key=lambda r: r["area_um2"])
        note = "least area within the delay bound"
    else:
        # nothing archived meets the bound: the nearest point, of least delay
        best = min(rows, key=lambda r: r["abc_delay_ps"] if r["abc_delay_ps"] is not None
                   else float("inf"))
        note = "no candidate within the delay bound; the one of least delay"
    print(json.dumps({"run": best["run"], "candidate_id": best["candidate_id"],
                      "unit_id": best["unit_id"], "area_um2": best["area_um2"],
                      "abc_delay_ps": best["abc_delay_ps"], "source_path": best["source_path"],
                      "exists": bool(best["source_path"]) and Path(best["source_path"]).is_file(),
                      "note": note}, indent=1))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("train", "check", "warm"):
        p = sub.add_parser(name)
        p.add_argument("db", nargs="*", help=f"results_db.jsonl files (default {DEFAULT_DBS})")
        p.add_argument("--pdk", default="nangate45")
        if name == "train":
            p.add_argument("--min-rows", type=int, default=50)
        if name == "warm":
            p.add_argument("--max-delay", type=float, default=None, help="ABC delay bound, ps")
            p.add_argument("--unit-id", default=None, help="restrict to one unit_id")
    args = ap.parse_args()
    args.db = args.db or sorted(glob.glob(DEFAULT_DBS))
    if not args.db:
        print(f"[surrogate] no archive: {DEFAULT_DBS}")
        return 1
    return {"train": cmd_train, "check": cmd_check, "warm": cmd_warm}[args.cmd](args)


if __name__ == "__main__":
    raise SystemExit(main())
