"""Training loop reused from coeff/gnn/train_gnn.py; architecture and G1..G8 preserved.

Outer certification labels never enter this loop. Inner early stopping chooses
an epoch count; the caller then refits on every supplied training graph. Row
weights carry the seed loop's front emphasis into the same standardized loss.
"""
import copy
import time
import numpy as np
import torch
import torch.nn.functional as F
if __package__:
    from .surrogate_gnn_model import GraphStore, PPAGNN, mark
else:
    from surrogate_gnn_model import GraphStore, PPAGNN, mark

BASE = dict(backbone="dag", sweeps=1, rounds=4, agg="summax", hidden=128, dropout=0.1, cat_drop=0.1,
            arrival=True, drop_globals=(), readout="both", tau=0.3, lr=2e-3, wd=1e-4, batch=512, epochs=250, patience=40,
            rank=0.0, rank_tol=0.05, rank_scale=0.02, select="mse")
CONFIGS = {
    "G1_dag": {},                                              # main: DAG sweep, sum+max, typed edges, arrival,
                                                               # sum-pool area / soft-max delay heads + pooled MLP
    "G2_dag_pna": {"agg": "pna"},                              # PNA multi-aggregator
    "G3_dag_rank": {"rank": 0.5, "select": "mix"},             # + pairwise delay ranking on similar-area pairs
    "G4_gin": {"backbone": "gin", "rounds": 4},                # plain K-round MPNN baseline, no topological order
    "G5_dag_noest": {"drop_globals": ("est_",)},               # without the old estimate's priors in the globals
    "G6_dag_noarr": {"arrival": False},                        # without the max-plus arrival channel
    "G7_dag_pool": {"readout": "pool"},                        # pooled-MLP readout only (no sum/soft-max heads)
    "G8_dag2": {"sweeps": 2},                                  # two DAG sweeps (second initialized from the first)
}


def predict(model, store, ids, bs=512):
    model.eval()
    out = []
    with torch.no_grad():
        for i in range(0, len(ids), bs):  # noqa
            out.append(model(mark(store, store.batch(ids[i:i + bs]))).double().cpu().numpy())
    return np.concatenate(out)


def rank_loss(p, y, tol, scale, min_delay_gap_pct=5):
    """Logistic loss on delay order for in-batch pairs of similar true log area."""
    da = (y[:, None, 0] - y[None, :, 0]).abs()
    dd = y[:, None, 1] - y[None, :, 1]
    m = (da < tol) & (dd.abs() >= np.log1p(min_delay_gap_pct / 100) - 1e-12) & (dd.abs() > 0)
    m = torch.triu(m, 1)
    if not m.any():
        return p.sum() * 0
    dp = p[:, None, 1] - p[None, :, 1]
    return F.softplus(-torch.sign(dd[m]) * dp[m] / scale).mean()


def val_score(cfg, cmp, yv, pv, sd):
    mse = ((pv - yv) / sd) ** 2
    if cfg["select"] == "mix":
        return -float(mse[:, 0].mean()) + cmp.ranking_score(yv, pv[:, 1], cfg.get("min_delay_gap_pct", 5))
    return -float(mse.mean())


def train_member(store, cfg, cmp, tr, va, seed, fixed_epochs=None, log=print):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    model = PPAGNN(store, cfg).to(store.device)
    opt = torch.optim.AdamW(model.parameters(), lr=cfg["lr"], weight_decay=cfg["wd"], fused=store.device.type == "cuda")
    sched = torch.optim.lr_scheduler.ReduceLROnPlateau(opt, factor=0.5, patience=6)
    sd = store.y_sd
    sd_np = sd.double().cpu().numpy()
    yv = store.y[np.asarray(va)] if va is not None else None
    best, best_state, best_ep, bad, hist = -np.inf, None, 0, 0, []
    epochs = fixed_epochs or cfg["epochs"]
    t0 = time.time()
    for ep in range(1, epochs + 1):
        model.train()
        perm = rng.permutation(tr)
        tot = 0.0
        for i in range(0, len(perm), cfg["batch"]):
            ids = perm[i:i + cfg["batch"]]
            if len(ids) < 2:
                continue
            p = model(mark(store, store.batch(ids)))
            y = store.targets(ids)
            row_loss = (((p - y) / sd) ** 2).mean(1)
            weight = torch.as_tensor(store.weights[ids], dtype=row_loss.dtype, device=store.device)
            loss = (row_loss * weight).sum() / weight.sum()
            if cfg["rank"] > 0:
                loss = loss + cfg["rank"] * rank_loss(p, y, cfg["rank_tol"], cfg["rank_scale"], cfg.get("min_delay_gap_pct", 5))
            opt.zero_grad(set_to_none=True)
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 5.0)
            opt.step()
            tot += loss.item() * len(ids)
        if fixed_epochs:
            hist.append({"ep": ep, "train": tot / len(perm)})
            continue
        pv = predict(model, store, va)
        s = val_score(cfg, cmp, yv, pv, sd_np)
        sched.step(-s)
        hist.append({"ep": ep, "train": tot / len(perm), "val": s,
                     "val_rmse": np.sqrt(((pv - yv) ** 2).mean(0)).round(4).tolist()})
        if s > best:
            best, best_state, best_ep, bad = s, copy.deepcopy(model.state_dict()), ep, 0
        else:
            bad += 1
        if ep % 10 == 0 or bad == 0:
            log(f"    ep {ep:3d} train {tot / len(perm):.4f} val {s:.4f} rmse {hist[-1]['val_rmse']} "
                f"{'*' if bad == 0 else ''} {time.time() - t0:.0f}s")
        if bad >= cfg["patience"]:
            break
    if best_state is not None:
        model.load_state_dict(best_state)
    return model, {"best_epoch": best_ep if not fixed_epochs else epochs, "best_val": best,
                   "epochs_run": len(hist), "seconds": time.time() - t0, "history": hist}
