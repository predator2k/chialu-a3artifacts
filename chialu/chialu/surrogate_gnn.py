"""Torch-optional adapter: export graphs here, train/predict in a chosen Python.

Bundles contain numpy state arrays and the declared graph vocabulary, so loading
one never imports torch. A subprocess uses the same packaged model for local CPU
or SSH GPU execution; there is no dependency on the original experiment folder.
Remote jobs receive only these worker sources, graph arrays and model state.
"""
from pathlib import Path
import io
import json
import os
import pickle
import shlex
import subprocess
import sys
import tempfile
import zipfile

import numpy as np

WORKER_FILES = ("surrogate_gnn_worker.py", "surrogate_gnn_model.py", "surrogate_gnn_train.py",
                "surrogate_gnn_pack.py", "surrogate_metrics.py")


def options(config=None):
    out = dict(config="G5", ensemble_size=3, epochs=250, patience=40, device="cpu", python=sys.executable,
               host=None, workdir=None, threads=2, timeout=3600)
    out.update(config or {})
    for key in ("ensemble_size", "epochs", "patience", "threads"):
        if int(out[key]) < 1:
            raise ValueError(f"gnn.{key} must be positive")
    if int(out["threads"]) > 8:
        raise ValueError("gnn.threads must be <= 8")
    if out["host"] and (str(out["host"]).startswith("-") or not out["workdir"]):
        raise ValueError("gnn.host requires a remote workdir and cannot start with '-'")
    return out


def bound_vars(declaration):
    """The declaration node's active scalar bindings, including check.* and x_form.

    Domain-line outputs are lists and are not search variables. Taking the bound
    output rather than the sampled proposal also removes inactive family choices.
    """
    return {k[5:]: v for k, v in declaration.items()
            if isinstance(k, str) and k.startswith("decl.") and not isinstance(v, (dict, list))}


def graph_input(space_data, files, vals, scheme, plan, est):
    """Export the same complete graph in training and the EDA prediction node."""
    from chialu.surrogate_graph import Space, Context, design_graph, completeness
    space = Space(space_data)
    target = next(iter(space_data["targets"]))
    ctx = Context(space, target, spec=json.loads(files["spec.json"]), est=est,
                  pdk=est.get("pdk", "nangate45"), effort=est.get("effort", "medium"))
    graph = design_graph(ctx, vals, scheme, plan)
    issues = completeness(graph, ctx, vals, plan)
    if issues:
        raise ValueError(f"incomplete GNN graph: {issues[:5]}")
    a = graph.arrays(space)
    a["scheme"] = scheme
    a["meta"] = dict(cat_fields=list(a["cat_fields"]), num_fields=list(a["num_fields"]),
                     global_names=list(a["global_names"]),
                     vocab_sizes={k: len(v) + 1 for k, v in space.vocab.items()},
                     node_types=space.vocab["node_type"], edge_types=space.vocab["edge_type"])
    return a


# The remote Python creates an isolated child of the explicitly configured workdir,
# cleans only that child and streams the result back. No scp or shared filesystem.
REMOTE = '''import io, os, subprocess, sys, tempfile, zipfile
root = sys.argv[1]
os.makedirs(root, exist_ok=True)
with tempfile.TemporaryDirectory(prefix="chialu-gnn-", dir=root) as d:
    zipfile.ZipFile(io.BytesIO(sys.stdin.buffer.read())).extractall(d)
    env = dict(os.environ, TMPDIR=d, PYTHONDONTWRITEBYTECODE="1", OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="1")
    r = subprocess.run([sys.executable, os.path.join(d, "surrogate_gnn_worker.py"), d], env=env, stdout=sys.stderr)
    if r.returncode: sys.exit(r.returncode)
    with open(os.path.join(d, "result.pkl"), "rb") as f: sys.stdout.buffer.write(f.read())
'''


def execute(request, config):
    """Run a bounded worker; subprocess stdout is reserved for the returned bundle."""
    cfg = options(config)
    request = dict(request, options=cfg)
    root = Path(__file__).parent
    env = dict(os.environ, OMP_NUM_THREADS=str(cfg["threads"]), MKL_NUM_THREADS=str(cfg["threads"]),
               OPENBLAS_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
    if cfg["host"]:
        payload = io.BytesIO()
        with zipfile.ZipFile(payload, "w", zipfile.ZIP_DEFLATED) as z:
            for name in WORKER_FILES:
                z.writestr(name, (root / name).read_bytes())
            z.writestr("request.pkl", pickle.dumps(request))
        cmd = ["ssh", "-o", "BatchMode=yes", str(cfg["host"]),
               shlex.join([str(cfg["python"]), "-c", REMOTE, str(cfg["workdir"])])]
        result = subprocess.run(cmd, input=payload.getvalue(), capture_output=True, env=env, timeout=cfg["timeout"])
        data = result.stdout
    else:
        with tempfile.TemporaryDirectory(prefix="chialu-gnn-", dir=os.environ.get("TMPDIR")) as td:
            d = Path(td)
            (d / "request.pkl").write_bytes(pickle.dumps(request))
            result = subprocess.run([str(cfg["python"]), str(root / WORKER_FILES[0]), td],
                                    capture_output=True, env=env, timeout=cfg["timeout"])
            data = (d / "result.pkl").read_bytes() if result.returncode == 0 else b""
    if result.returncode:
        raise RuntimeError(f"GNN worker failed ({cfg['python']}): {result.stderr.decode(errors='replace')[-4000:]}")
    return pickle.loads(data)


def fit(graphs, ys, seed=0, weights=None, config=None, graph_space=None):
    cfg = options(config)
    if graphs is None or len(graphs) < 4:
        raise ValueError("GNN fitting needs at least four complete graphs")
    y = np.column_stack([ys[k] for k in ("area_um2", "delay_ps")])
    if len(y) != len(graphs) or not np.isfinite(y).all() or (y <= 0).any():
        raise ValueError("GNN targets must be finite positive physical values, one per graph")
    weights = np.ones(len(y)) if weights is None else np.asarray(weights, float)
    if weights.shape != (len(y),) or not np.isfinite(weights).all() or (weights <= 0).any():
        raise ValueError("GNN sample weights must be finite and positive")
    out = execute(dict(action="fit", graphs=graphs, log_y=np.log(y), seed=seed, weights=weights), cfg)
    return dict(out, model_type="gnn", gnn=cfg, graph_space=graph_space)


def predict(bundle, graphs):
    if graphs is None:
        raise ValueError("GNN prediction requires complete graphs")
    if not graphs:
        return {k: np.empty(0) for k in ("area_um2", "delay_ps")}
    p = execute(dict(action="predict", graphs=graphs, bundle=bundle), bundle["gnn"])
    return {k: np.exp(p[:, j]) for j, k in enumerate(("area_um2", "delay_ps"))}
