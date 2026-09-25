"""Numpy-only graph packing; topology routine reused from coeff/gnn/pack_graphs.py."""
import json
import numpy as np


def topo_levels(n, ei):
    """Longest-path depth from sources; raises on a cycle."""
    src, dst = ei
    indeg = np.bincount(dst, minlength=n)
    order = np.argsort(src, kind="stable")
    starts = np.searchsorted(src[order], np.arange(n + 1))
    level = np.zeros(n, dtype=np.int64)
    frontier = list(np.flatnonzero(indeg == 0))
    indeg = indeg.copy()
    seen = 0
    while frontier:
        nxt = []
        for u in frontier:
            seen += 1
            for e in order[starts[u]:starts[u + 1]]:
                v = dst[e]
                level[v] = max(level[v], level[u] + 1)
                indeg[v] -= 1
                if indeg[v] == 0:
                    nxt.append(v)
        frontier = nxt
    if seen != n:
        raise ValueError(f"graph has a cycle ({n - seen} nodes unreached)")
    return level


def pack(graphs, log_y, path):
    """Pack local edge indices and offsets without transforming log labels again."""
    if not graphs:
        raise ValueError("GNN requires at least one graph")
    meta = graphs[0]["meta"]
    if any(g["meta"] != meta for g in graphs):
        raise ValueError("graph schemas differ")
    node_off = np.r_[0, np.cumsum([len(g["x_cat"]) for g in graphs])]
    edge_off = np.r_[0, np.cumsum([g["edge_index"].shape[1] for g in graphs])]
    data = {k: np.concatenate([g[k] for g in graphs], axis=1 if k == "edge_index" else 0)
            for k in ("x_cat", "x_num", "edge_index", "edge_type", "edge_mode", "edge_w")}
    np.savez_compressed(path, **data, globals=np.stack([g["globals"] for g in graphs]),
                        level=np.concatenate([topo_levels(len(g["x_cat"]), g["edge_index"]) for g in graphs]),
                        node_off=node_off, edge_off=edge_off, y=np.asarray(log_y, float),
                        names=np.asarray([str(i) for i in range(len(graphs))]),
                        schemes=np.asarray([g.get("scheme", "") for g in graphs]), meta=np.array(json.dumps(meta)))
