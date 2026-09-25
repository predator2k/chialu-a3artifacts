"""Noise-aware order statistics on explicitly natural-log truth and predictions.

A pair is informative only when its measured ratio clears the configured gap.
Predicted ties earn half credit; true ties never supply an order. The rank
correlation is the cosine of rank differences over retained pairs: with every
pair it equals Spearman, while a noise pair contributes nothing after filtering.
Its filtered value has no ordinary Spearman/Kendall p-value. Pair counts are
reported as counts, never treated as independent sample sizes for inference.
"""
import math

import numpy as np


def gap_threshold(pct):
    pct = float(pct)
    if not math.isfinite(pct) or pct < 0:
        raise ValueError("minimum gap must be finite and nonnegative")
    return math.log1p(pct / 100)


def pair_metrics(log_true, log_pred, min_gap_pct=5, *, pairs=None):
    """Order accuracy, tau-a and rank correlation; inputs are NEVER logged here.

    The bins partition non-tied truth pairs as [0,2), [2,5), [5,10),
    [10,20], (20,infinity) percent. Explicit pair indices restrict the population
    (e.g. close-area hard pairs); the gap is always applied to TRUE differences.
    """
    from scipy.stats import rankdata
    y, p = np.asarray(log_true, float), np.asarray(log_pred, float)
    threshold = gap_threshold(min_gap_pct)
    if y.ndim != 1 or p.shape != y.shape or not np.isfinite(y).all() or not np.isfinite(p).all():
        raise ValueError("expected equal finite one-dimensional natural-log arrays")
    i, j = np.triu_indices(len(y), 1) if pairs is None else pairs
    dy, dp = y[i] - y[j], p[i] - p[j]
    gap = np.abs(dy)
    signs = np.sign(dy) * np.sign(dp)
    ry, rp = rankdata(y), rankdata(p)
    dry, drp = ry[i] - ry[j], rp[i] - rp[j]
    informative = gap > 0

    def score(mask):
        n = int(mask.sum())
        denom = np.sqrt(np.sum(dry[mask] ** 2) * np.sum(drp[mask] ** 2))
        return {"pairs": n,
                "accuracy": float(np.mean((signs[mask] + 1) / 2)) if n else None,
                "tau": float(signs[mask].mean()) if n else None,
                "rho": float(np.sum(dry[mask] * drp[mask]) / denom) if denom else None}

    # A small tolerance admits ratios exactly on the boundary after log subtraction.
    out = score(informative & (gap >= threshold - 1e-12))
    out.update({k + "_all_pairs": v for k, v in score(informative).items()})
    out["min_gap_pct"] = float(min_gap_pct)
    out["candidate_pairs"] = len(i)
    out["gap_bins"] = {}
    edges = [0, *[gap_threshold(x) for x in (2, 5, 10, 20)], np.inf]
    for k, label in enumerate(("0-2", "2-5", "5-10", "10-20", ">20")):
        lo, hi = edges[k:k + 2]
        mask = informative & (gap >= lo - 1e-12) & (gap < hi - 1e-12)
        if k == 3:
            mask = informative & (gap >= lo - 1e-12) & (gap <= hi + 1e-12)
        elif k == 4:
            mask = informative & (gap > lo + 1e-12)
        out["gap_bins"][label] = score(mask)
    return out


def front_indices(points):
    """Strict minimization front, preserving all equal-coordinate designs."""
    points = np.asarray(points, float)
    if not len(points):
        return np.empty(0, dtype=int)
    order = np.lexsort((points[:, 1], points[:, 0]))
    p = points[order]
    new = p[:, 1] < np.minimum.accumulate(np.r_[np.inf, p[:-1, 1]])
    first = np.r_[True, np.any(p[1:] != p[:-1], axis=1)]
    starts = np.maximum.accumulate(np.where(first, np.arange(len(p)), 0))
    return order[new[starts]]


def pareto_layers(points, count=3):
    """Depths 1..count; 0 means outside those layers (ties share a layer)."""
    points = np.asarray(points, float)
    depths = np.zeros(len(points), dtype=int)
    remaining = np.arange(len(points))
    for layer in range(1, count + 1):
        if not len(remaining):
            break
        front = front_indices(points[remaining])
        depths[remaining[front]] = layer
        remaining = remaining[depths[remaining] == 0]
    return depths


def ranking_score(y, p, min_delay_gap_pct=5):
    """Shared XGBoost/G3 tuning criterion: significant front and hard-pair tau.

    Numpy only so the exact same selector can run in the torch interpreter.
    No significant pair means ranking supplies no evidence; fall back to MSE.
    """
    y, p = np.asarray(y, float), np.asarray(p, float)
    threshold = gap_threshold(min_delay_gap_pct)
    i, j = np.triu_indices(len(y), 1)
    dd = y[i, 1] - y[j, 1]
    keep = (dd != 0) & (np.abs(dd) >= threshold - 1e-12)
    signs = np.sign(dd) * np.sign(p[i] - p[j])
    front = pareto_layers(y) > 0
    masks = [keep & front[i] & front[j], keep & (np.abs(y[i, 0] - y[j, 0]) < .02)]
    terms = [float(signs[m].mean()) for m in masks if m.any()]
    return float(np.mean(terms)) if terms else -float(np.mean((y[:, 1] - p) ** 2))
