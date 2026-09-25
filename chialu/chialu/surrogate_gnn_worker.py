"""Standalone torch worker, shipped verbatim for optional SSH execution.

Only numpy and torch are required in the worker interpreter. The early-stopping
split uses the supplied training rows alone; refitting incorporates every row
counted by scheme_trained. Prediction reuses each member's saved scaler and
embedding dimensions, never fitting anything to a prediction batch.
"""
import os
from pathlib import Path
import pickle
import sys

import numpy as np
import torch

if __package__:
    from .surrogate_gnn_model import GraphStore, PPAGNN
    from .surrogate_gnn_pack import pack
    from .surrogate_gnn_train import BASE, CONFIGS, train_member, predict
    from . import surrogate_metrics as RankMetric
else:
    from surrogate_gnn_model import GraphStore, PPAGNN
    from surrogate_gnn_pack import pack
    from surrogate_gnn_train import BASE, CONFIGS, train_member, predict
    import surrogate_metrics as RankMetric


def run(request, directory):
    opts = request["options"]
    torch.set_num_threads(int(opts["threads"]))
    torch.set_num_interop_threads(1)
    graphs = request["graphs"]
    path = directory / "graphs.npz"
    pack(graphs, request.get("log_y", np.zeros((len(graphs), 2))), path)
    store = GraphStore(path, opts["device"])
    if request["action"] == "fit":
        name = opts["config"]
        name = next((k for k in CONFIGS if k.split("_")[0] == name), name)
        if name not in CONFIGS:
            raise ValueError(f"unknown GNN config {name!r}; expected G1..G8")
        cfg = dict(BASE, **CONFIGS[name])
        overrides = dict(opts.get("hyperparameters") or {})
        overrides.update({k: v for k, v in opts.items() if k in BASE})
        unknown = set(overrides) - set(BASE)
        if unknown:
            raise ValueError(f"unknown GNN hyperparameters: {sorted(unknown)}")
        cfg.update(overrides)
        cfg["min_delay_gap_pct"] = opts.get("min_delay_gap_pct", 5)
        store.weights = request["weights"]
        ids = np.arange(len(graphs))
        perm = np.random.default_rng(request["seed"]).permutation(ids)
        nval = max(1, min(len(ids) - 2, int(np.ceil(len(ids) * .2))))
        tr, va = perm[nval:], perm[:nval]
        members = []
        for m in range(int(opts["ensemble_size"])):
            seed = request["seed"] + 17 * m
            store.standardize(tr, cfg["drop_globals"])
            model, info = train_member(store, cfg, RankMetric, tr, va, seed, log=lambda s: None)
            store.standardize(ids, cfg["drop_globals"])
            model, refit = train_member(store, cfg, RankMetric, ids, None, seed,
                                       fixed_epochs=info["best_epoch"], log=lambda s: None)
            members.append(dict(state={k: v.detach().cpu().numpy() for k, v in model.state_dict().items()},
                                scaler=store.scaler, epochs=info["best_epoch"], epochs_run=info["epochs_run"],
                                cat_card=store.cat_card, n_etype=store.n_etype, n_emode=store.n_emode))
        return dict(members=members, cfg=cfg, torch_version=str(torch.__version__), log_target=True)
    bundle = request["bundle"]
    preds = []
    for member in bundle["members"]:
        store.apply_scaler(member["scaler"])
        store.cat_card, store.n_etype, store.n_emode = member["cat_card"], member["n_etype"], member["n_emode"]
        model = PPAGNN(store, bundle["cfg"]).to(store.device)
        model.load_state_dict({k: torch.as_tensor(v, device=store.device) for k, v in member["state"].items()})
        preds.append(predict(model, store, np.arange(len(graphs)), bundle["cfg"]["batch"]))
    return np.mean(preds, axis=0)


if __name__ == "__main__":
    directory = Path(sys.argv[1])
    request = pickle.loads((directory / "request.pkl").read_bytes())
    (directory / "result.pkl").write_bytes(pickle.dumps(run(request, directory)))
