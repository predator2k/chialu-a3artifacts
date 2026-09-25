"""Features for predicting a design's synthesized PPA across plans of one target.

Cross-plan transfer is possible at all because the plans of one target share a structure manifest:
`AluInt.register_op` and its float counterpart derive a mode's structures from the mode's format and
its op list alone, reading no binding and no family choice, so plan A and plan B see the same 24
structures and differ only in which of them one physical unit realizes. Two consequences shape what
is built here.

First, the per-structure database rows align by structure id across plans, so a column can mean
"what the database says m1.l0.multiplier costs" in every plan at once. A one-hot of the family
choice cannot: its columns are per (slot, index) and the same family at a different width is a
different cost. Within one plan the two carry identical information -- measured at rho 0.950 for
both -- but only the rows keep their meaning when the plan changes.

Second, since the structures are fixed, everything a plan contributes is about GROUPING, so that is
what the plan features describe: which kinds are shared and under which rule, how large the groups
are, and the geometry the group has to span -- the sum of its members' widths against the widest
member, and how many distinct formats, modes and lanes it must serve. Those spans are the mechanism
behind the mispricing the numeric model shows: a group is one datapath at the union geometry with
its operands muxed, and the estimate prices it as if it were one member.
"""
import json
from collections import Counter

TOKENS = ("add", "mul", "log", "pair", "fmt", "sw", "intfp")
RULES = ("none", "all", "per_mode", "per_lane", "comparator", "stage", "arith", "pcc", "rep")


def plan_tokens(plan_name: str) -> dict:
    """The sharing rule each kind takes, read off the scheme name."""
    out = {}
    for tok in plan_name.split("_"):
        if "-" in tok:
            k, v = tok.split("-", 1)
            out[k] = v
    return out


def plan_features(plan_name: str, plan: dict, manifest_by_id: dict) -> dict:
    f = {}
    toks = plan_tokens(plan_name)
    for t in TOKENS:
        for r in RULES:
            f[f"PLAN__{t}_{r}"] = 1.0 if toks.get(t) == r else 0.0
    groups = [(g, list(v.get("members") or [])) for g, v in (plan.get("shared") or {}).items()]
    groups = [(g, m) for g, m in groups if len(m) >= 2]
    f["SHR__n_groups"] = float(len(groups))
    sizes = [len(m) for _g, m in groups] or [0]
    f["SHR__max_gsize"] = float(max(sizes))
    f["SHR__sum_grouped"] = float(sum(sizes))
    f["SHR__mean_gsize"] = float(sum(sizes) / max(1, len(groups)))
    f["SHR__frac_grouped"] = float(sum(sizes)) / max(1, len(manifest_by_id))
    per_kind = Counter()
    for _g, m in groups:
        for sid in m:
            s = manifest_by_id.get(sid)
            if s:
                per_kind[s["kind"]] += 1
    for kind in ("adder", "multiplier", "logic", "comparator", "shifter", "bitcount",
                 "rounder", "unpacker", "fp_adder", "fp_multiplier", "fp_comparator", "fp_fma"):
        f[f"KIND__{kind}_grouped"] = float(per_kind.get(kind, 0))
    # the union geometry a group has to span, which is what the estimate prices as one member
    for _g, m in groups:
        sts = [manifest_by_id[s] for s in m if s in manifest_by_id]
        if not sts:
            continue
        kind = sts[0]["kind"]
        w = [s["width"] for s in sts] or [0]
        pre = f"GEO__{kind}"
        f[pre + "_sum_over_max_w"] = max(f.get(pre + "_sum_over_max_w", 0.0), sum(w) / max(1, max(w)))
        f[pre + "_fmtspan"] = max(f.get(pre + "_fmtspan", 0.0), float(len({s["format"] for s in sts})))
        f[pre + "_modespan"] = max(f.get(pre + "_modespan", 0.0), float(len({s["mode"] for s in sts})))
        f[pre + "_lanespan"] = max(f.get(pre + "_lanespan", 0.0), float(len({s["lane"] for s in sts})))
        f[pre + "_gsize"] = max(f.get(pre + "_gsize", 0.0), float(len(sts)))
    return f


def row_features(rows: list, ids: list) -> dict:
    """Per-structure database rows, aligned by structure id, plus composition-free aggregates."""
    by = {r["id"]: r for r in rows}
    f = {}
    for i in ids:
        r = by.get(i)
        f[f"ROW__{i}__area"] = float(r["area_um2"]) if r else 0.0
        f[f"ROW__{i}__delay"] = float(r["delay_ps"]) if r else 0.0
    a = [float(r["area_um2"]) for r in rows] or [0.0]
    d = [float(r["delay_ps"]) for r in rows] or [0.0]
    f["AGG__area_sum"], f["AGG__area_max"], f["AGG__area_mean"] = sum(a), max(a), sum(a) / len(a)
    f["AGG__delay_max"], f["AGG__delay_mean"] = max(d), sum(d) / len(d)
    ds = sorted(d, reverse=True)
    for k in (1, 2, 3, 5):
        f[f"AGG__delay_top{k}"] = float(sum(ds[:k]))
        f[f"AGG__area_top{k}"] = float(sum(sorted(a, reverse=True)[:k]))
    f["AGG__n_rows"] = float(len(rows))
    return f


def build(meas: dict, vec: dict, plan_name: str, plan: dict, manifest_by_id: dict, ids: list) -> dict:
    f = {"EST__area": float(meas["est_area"]), "EST__delay": float(meas["est_delay"]),
         "EST__coverage": float(meas.get("coverage") or 0.0)}
    f.update(row_features(vec.get("rows") or [], ids))
    f.update(plan_features(plan_name, plan, manifest_by_id))
    return f
