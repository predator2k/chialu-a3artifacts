"""GNN surrogate of whole-ALU PPA over chialu.surrogate_graph's design graphs (plain torch, no PyG).

Data (`GraphStore`): the packed npz of pack_graphs.py, resident on the GPU; a batch
is a list of graph ids gathered with offset arithmetic (no python per graph).

Model (`PPAGNN`):
  encoder   one embedding table per categorical column (shared by every node, so the
            same choice in every mode shares parameters through the generic path),
            an MLP on the (signed-log, standardized) numeric columns, and the graph's
            globals broadcast to every node;
  backbone  "dag": an asynchronous, direction-aware sweep in topological order
            (DAGNN / D-VAE style): the nodes of level L (longest distance from a leaf)
            are updated once, from their already final predecessors, by a GRU cell
            whose input is the aggregation (sum+max, or PNA sum/max/mean/std) of
            typed messages MLP([h_u, edge-type emb, mode emb, edge_w, arrival]).
            `arrival` is a non-learned max-plus sweep of the in-place unit delays
            (edge_w) along the same order: at the top node it is the estimate's
            longest mode path, the STA-like recurrence the survey asks to align with.
            `sweeps` > 1 repeats the sweep, initialized from the previous one.
            "gin": a plain K-round MPNN (GIN-style residual update from forward and
            backward sum+max aggregation), the baseline without topological order;
  readout   log area = logsumexp over all nodes of a per-node score (a sum pool in
            linear area); log delay = tau * logsumexp(score/tau) over the mode and top
            nodes (a soft max); plus ("both", default) a correction MLP of [h_top,
            mean pool, max pool, globals]. Alone the structured heads learned delay
            badly (the top is ~9 GRU steps from the choices: val delay RMSE stuck at
            the label std); the pooled term gives the choices a direct path.
            "pool" = the correction MLP only. Natural log units; the loss standardizes.
"""
from __future__ import annotations

import json
import math

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

HIGH_CARD = ("gpath", "name", "value", "family")   # columns whose ids get dropped out in training


def slog(x):
    return torch.sign(x) * torch.log1p(torch.abs(x))


class GraphStore:
    """The whole packed dataset on one device; `batch(ids)` gathers a disjoint union."""

    def __init__(self, path, device):
        d = np.load(path)
        self.meta = json.loads(str(d["meta"]))
        self.names = [str(n) for n in d["names"]]
        self.schemes = [str(s) for s in d["schemes"]]
        self.index = {n: i for i, n in enumerate(self.names)}
        self.y = d["y"].astype(np.float64)
        dev = torch.device(device)
        t = lambda a, dt: torch.as_tensor(np.ascontiguousarray(a), dtype=dt, device=dev)
        self.x_cat = t(d["x_cat"], torch.long)
        self.x_num_raw = t(d["x_num"], torch.float32)
        self.ei = t(d["edge_index"], torch.long)
        self.et = t(d["edge_type"], torch.long)
        self.em = t(d["edge_mode"], torch.long) + 1          # -1 (no mode) -> 0
        self.ew = t(d["edge_w"], torch.float32)
        self.level = t(d["level"], torch.long)
        self.g_raw = t(d["globals"], torch.float32)
        self.noff = t(d["node_off"], torch.long)
        self.eoff = t(d["edge_off"], torch.long)
        self.ncnt = self.noff[1:] - self.noff[:-1]
        self.ecnt = self.eoff[1:] - self.eoff[:-1]
        # the level of an edge's destination (per-graph local ids -> global)
        egraph = torch.repeat_interleave(torch.arange(len(self.names), device=dev), self.ecnt)
        self.elevel = self.level[self.ei[1] + self.noff[egraph]]
        self.max_level = int(self.level.max())
        self.cat_card = [int(v) + 1 for v in d["x_cat"].max(0)]
        vs = self.meta.get("vocab_sizes", {})
        for j, f in enumerate(self.meta["cat_fields"]):
            v = vs.get("value" if f == "family" else f)
            if v:
                self.cat_card[j] = max(self.cat_card[j], v)
        nt = self.meta.get("node_types", ["top", "mode"])
        self.top_id, self.mode_id = nt.index("top") + 1, nt.index("mode") + 1
        self.n_etype = max(int(d["edge_type"].max()) + 1, len(self.meta.get("edge_types", [])) + 1)
        self.n_emode = int(d["edge_mode"].max()) + 2
        self.global_names = self.meta["global_names"]
        self.device = dev

    def standardize(self, train_ids, drop_globals=()):
        """Numeric/global scaling from the training graphs only (signed log, then z-score)."""
        ids = torch.as_tensor(train_ids, device=self.device)
        nidx, _, _, _ = self._gather(ids, self.noff, self.ncnt)
        xn = slog(self.x_num_raw)
        mu, sd = xn[nidx].mean(0), xn[nidx].std(0)
        sd = torch.where(sd > 1e-6, sd, torch.ones_like(sd))
        self.x_num = (xn - mu) / sd
        g = slog(self.g_raw)
        gm, gs = g[ids].mean(0), g[ids].std(0)
        gs = torch.where(gs > 1e-6, gs, torch.ones_like(gs))
        self.g = (g - gm) / gs
        keep = torch.ones(g.shape[1], dtype=torch.bool, device=self.device)
        for j, n in enumerate(self.global_names):
            if any(n.startswith(p) for p in drop_globals):
                keep[j] = False
        self.g = self.g[:, keep]
        yt = torch.as_tensor(self.y[np.asarray(train_ids)], dtype=torch.float32)
        self.y_mu, self.y_sd = yt.mean(0).to(self.device), yt.std(0).to(self.device)
        self.y_sd = self.y_sd.clamp_min(1e-6)
        self.mean_nodes = float(self.ncnt[ids].float().mean())
        # Persist training-only scaling so an inference batch cannot change predictions.
        self.scaler = {k: v.detach().cpu().numpy() for k, v in
                       dict(mu=mu, sd=sd, gm=gm, gs=gs, keep=keep,
                            y_mu=self.y_mu, y_sd=self.y_sd).items()}
        self.scaler["mean_nodes"] = self.mean_nodes

    def apply_scaler(self, scaler):
        t = lambda k: torch.as_tensor(scaler[k], device=self.device)
        self.x_num = (slog(self.x_num_raw) - t("mu")) / t("sd")
        self.g = ((slog(self.g_raw) - t("gm")) / t("gs"))[:, t("keep")]
        self.y_mu, self.y_sd = t("y_mu"), t("y_sd")
        self.mean_nodes = scaler["mean_nodes"]
        self.scaler = scaler

    @staticmethod
    def _gather(ids, off, cnt):
        c = cnt[ids]
        starts = off[ids]
        tot = int(c.sum())
        bstart = torch.cumsum(c, 0) - c
        rep_b = torch.repeat_interleave(torch.arange(len(ids), device=ids.device), c, output_size=tot)
        idx = starts[rep_b] + torch.arange(tot, device=ids.device) - bstart[rep_b]
        return idx, rep_b, bstart, tot

    def batch(self, ids):
        ids = torch.as_tensor(ids, device=self.device)
        nidx, nb, nbstart, n = self._gather(ids, self.noff, self.ncnt)
        eidx, eb, _, _ = self._gather(ids, self.eoff, self.ecnt)
        ei = self.ei[:, eidx] + nbstart[eb]
        return {"n": n, "B": len(ids), "x_cat": self.x_cat[nidx], "x_num": self.x_num[nidx], "nb": nb,
                "ei": ei, "et": self.et[eidx], "em": self.em[eidx], "ew": self.ew[eidx],
                "level": self.level[nidx], "elevel": self.elevel[eidx], "g": self.g[ids],
                "ntype": self.x_cat[nidx, 0]}

    def targets(self, ids):
        return torch.as_tensor(self.y[np.asarray(ids)], dtype=torch.float32, device=self.device)


def mlp(i, h, o, n=2, drop=0.0, norm=True):
    layers, d = [], i
    for _ in range(n - 1):
        layers += [nn.Linear(d, h)] + ([nn.LayerNorm(h)] if norm else []) + [nn.SiLU()] + ([nn.Dropout(drop)] if drop else [])
        d = h
    layers.append(nn.Linear(d, o))
    return nn.Sequential(*layers)


def seg_softmax_lse(s, seg, nseg):
    """Per-segment logsumexp of scalar scores s[N] (segments without members -> -inf)."""
    m = torch.full((nseg,), -1e30, device=s.device, dtype=s.dtype).scatter_reduce(0, seg, s, "amax", include_self=True)
    m = m.detach()
    z = torch.zeros(nseg, device=s.device, dtype=s.dtype).index_add(0, seg, torch.exp(s - m[seg]))
    return m + torch.log(z.clamp_min(1e-30))


class Aggregate(nn.Module):
    def __init__(self, h, kind):
        super().__init__()
        self.kinds = {"summax": ("sum", "max"), "pna": ("sum", "max", "mean", "std"), "sum": ("sum",)}[kind]
        self.out = nn.Linear(h * len(self.kinds) + 1, h)

    def forward(self, msg, dst, n):
        h = msg.shape[1]
        deg = torch.zeros(n, device=msg.device).index_add(0, dst, torch.ones_like(dst, dtype=msg.dtype))
        outs = []
        s = torch.zeros(n, h, device=msg.device, dtype=msg.dtype).index_add(0, dst, msg)
        for k in self.kinds:
            if k == "sum":
                outs.append(s)
            elif k == "max":
                outs.append(torch.zeros(n, h, device=msg.device, dtype=msg.dtype).scatter_reduce(
                    0, dst[:, None].expand(-1, h), msg, "amax", include_self=False))
            elif k == "mean":
                outs.append(s / deg.clamp_min(1)[:, None])
            elif k == "std":
                sq = torch.zeros(n, h, device=msg.device, dtype=msg.dtype).index_add(0, dst, msg * msg)
                mean = s / deg.clamp_min(1)[:, None]
                outs.append(torch.sqrt((sq / deg.clamp_min(1)[:, None] - mean * mean).clamp_min(0) + 1e-6))
        outs.append(torch.log1p(deg)[:, None])
        return self.out(torch.cat(outs, 1))


class PPAGNN(nn.Module):
    def __init__(self, store: GraphStore, cfg: dict):
        super().__init__()
        self.cfg = cfg
        H = cfg["hidden"]
        self.backbone = cfg["backbone"]
        self.cat_fields = store.meta["cat_fields"]
        self.embs = nn.ModuleList(nn.Embedding(c, 32 if c > 64 else 8) for c in store.cat_card)
        cat_dim = sum(e.embedding_dim for e in self.embs)
        n_num = store.x_num.shape[1]
        n_g = store.g.shape[1]
        self.node_in = mlp(cat_dim + n_num, H, H, 2, cfg["dropout"])
        self.g_enc = mlp(n_g, H, H, 2, cfg["dropout"])
        self.g_to_node = nn.Linear(H, H)
        self.etype = nn.Embedding(store.n_etype, 16)
        self.emode = nn.Embedding(store.n_emode, 4)
        e_dim = 16 + 4 + 2
        if self.backbone == "dag":
            self.sweeps = nn.ModuleList()
            for _ in range(cfg["sweeps"]):
                self.sweeps.append(nn.ModuleDict({"msg": mlp(H + e_dim, H, H, 2), "agg": Aggregate(H, cfg["agg"]),
                                                  "gru": nn.GRUCell(H, H)}))
        else:
            self.rounds = nn.ModuleList()
            for _ in range(cfg["rounds"]):
                self.rounds.append(nn.ModuleDict({"fmsg": mlp(H + e_dim, H, H, 2), "bmsg": mlp(H + e_dim, H, H, 2),
                                                  "fagg": Aggregate(H, cfg["agg"]), "bagg": Aggregate(H, cfg["agg"]),
                                                  "upd": mlp(3 * H, H, H, 2), "norm": nn.LayerNorm(H)}))
        self.area_node = mlp(H, H, 1, 2)
        self.delay_node = mlp(H, H, 1, 2)
        self.readout_kind = cfg.get("readout", "both")
        self.corr = mlp(4 * H, H, 2, 2, cfg["dropout"])
        self.register_buffer("y_mu", store.y_mu.clone().float())
        self.log_tau = nn.Parameter(torch.tensor(math.log(cfg.get("tau", 0.05))))
        with torch.no_grad():   # start near the training means: sum of exp over ~mean_nodes nodes, max over modes
            self.area_node[-1].bias.fill_(float(store.y_mu[0]) - math.log(store.mean_nodes))
            self.delay_node[-1].bias.fill_(float(store.y_mu[1]))
            self.corr[-1].weight.mul_(0.1)
            self.corr[-1].bias.zero_()

    def encode(self, b):
        xc = b["x_cat"]
        if self.training and self.cfg["cat_drop"] > 0:
            xc = xc.clone()
            for j, f in enumerate(self.cat_fields):
                if f in HIGH_CARD:
                    m = torch.rand(len(xc), device=xc.device) < self.cfg["cat_drop"]
                    xc[m, j] = 0
        e = torch.cat([emb(xc[:, j]) for j, emb in enumerate(self.embs)] + [b["x_num"]], 1)
        g = self.g_enc(b["g"])
        return self.node_in(e) + self.g_to_node(g)[b["nb"]], g

    def arrival(self, b, order, ecounts):
        """Max-plus sweep of the unit delays along the topological levels (no gradient)."""
        with torch.no_grad():
            src, dst = b["ei"]
            w = torch.expm1(b["ew"])
            arr = torch.zeros(b["n"], device=w.device)
            start = ecounts[0]
            for L in range(1, len(ecounts)):
                sl = order[start:start + ecounts[L]]
                start += ecounts[L]
                if not len(sl):
                    continue
                cand = arr[src[sl]] + w[sl]
                arr = arr.scatter_reduce(0, dst[sl], cand, "amax", include_self=True)
            return torch.log1p(arr[src] + w) / 8.0

    def forward(self, b):
        h0, g = self.encode(b)
        src, dst = b["ei"]
        n = b["n"]
        L = int(b["level"].max()) + 1
        order = torch.argsort(b["elevel"])
        ecounts = torch.bincount(b["elevel"], minlength=L).tolist()
        arr = self.arrival(b, order, ecounts) if self.cfg["arrival"] else torch.zeros_like(b["ew"])
        efeat = torch.cat([self.etype(b["et"]), self.emode(b["em"]), b["ew"][:, None] / 8.0, arr[:, None]], 1)
        if self.backbone == "dag":
            norder = torch.argsort(b["level"])
            ncounts = torch.bincount(b["level"], minlength=L).tolist()
            h_init = h0
            for sw in self.sweeps:
                # level 0 (leaves): no messages, the GRU sees a zero input
                h = sw["gru"](torch.zeros_like(h_init), h_init)
                es, ns = ecounts[0], ncounts[0]
                for lv in range(1, L):
                    esl = order[es:es + ecounts[lv]]
                    nsl = norder[ns:ns + ncounts[lv]]
                    es += ecounts[lv]
                    ns += ncounts[lv]
                    if not len(nsl):
                        continue
                    m = sw["msg"](torch.cat([h[src[esl]], efeat[esl]], 1))
                    agg = sw["agg"](m, dst[esl], n)[nsl]
                    h = h.index_copy(0, nsl, sw["gru"](agg, h_init[nsl]))
                h_init = h
        else:
            h = h0
            for r in self.rounds:
                fm = r["fagg"](r["fmsg"](torch.cat([h[src], efeat], 1)), dst, n)
                bm = r["bagg"](r["bmsg"](torch.cat([h[dst], efeat], 1)), src, n)
                h = r["norm"](h + r["upd"](torch.cat([h, fm, bm], 1)))
        return self.readout(h, g, b, b["B"])

    def readout(self, h, g, b, B):
        nb = b["nb"]
        H = h.shape[1]
        top = torch.zeros(B, H, device=h.device).index_add(0, nb[b["is_top"]], h[b["is_top"]])
        cnt = torch.bincount(nb, minlength=B).clamp_min(1)[:, None].float()
        mean = torch.zeros(B, H, device=h.device).index_add(0, nb, h) / cnt
        mx = torch.zeros(B, H, device=h.device).scatter_reduce(0, nb[:, None].expand(-1, H), h, "amax", include_self=False)
        corr = self.corr(torch.cat([top, mean, mx, g], 1))
        if self.readout_kind == "pool":      # plain pooled MLP (ablation / fallback)
            return self.y_mu + corr
        area = seg_softmax_lse(self.area_node(h).squeeze(1), nb, B)
        sel = b["is_delay"]
        tau = torch.exp(self.log_tau)
        delay = tau * seg_softmax_lse(self.delay_node(h[sel]).squeeze(1) / tau, nb[sel], B)
        return torch.stack([area, delay], 1) + corr


def mark(store: GraphStore, b):
    b["is_top"] = b["ntype"] == store.top_id
    b["is_delay"] = b["is_top"] | (b["ntype"] == store.mode_id)
    return b
