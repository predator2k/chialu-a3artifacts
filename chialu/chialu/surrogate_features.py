"""The input of the whole-unit PPA surrogate: `rows + plan + one-hot`.

The feature design decided by the earlier study (coeff/xgb, coeff/varlen,
coeff/xplan_features.py; docs/model-input.md), kept as it was and fed
with the current flow's declarations:

* `EST__`: the numeric model's own area, delay and coverage
  (`chialu.eda.estimate` under the point's sharing scheme): a prior that
  already encodes "sum of the parts, longest mode path", for the model
  to learn where that composition is wrong.
* `ROW__<structure id>__area|delay`: the database row the estimate
  priced for every structure of the unit's manifest, aligned by
  structure id. The manifest is fixed per target (it derives from the
  modes' formats and ops alone), so a column keeps its meaning in every
  plan, and the id carries the structure's place (mode, lane, kind) in
  the datapath. A structure realized by a shared group takes the group's
  row (the unit that implements it); one without a row is 0.
* `AGG__`: order statistics of the rows (sums, maxima, top-k), which a
  tree would need many splits to rebuild.
* `PLAN__` / `SHR__` / `KIND__` / `GEO__`: the sharing scheme: the rule
  each axis takes (add/mul/log/pair/fmt/sw/intfp), the groups it makes,
  the kinds grouped, and the union geometry a group spans (sum of member
  widths over the widest, formats, modes, lanes).
* `OH__<variable>__<value>`: a one-hot of every declared `core.*`
  variable and `x_form`, nested families and pins included. A slot that the chosen
  parent family does not have is simply absent (all its columns 0), so
  the variable-length configuration tree becomes a fixed-width vector.

The earlier corpus varied only the top-level families; here every searched
variable is drawn, including conditional subtrees and the internal X form.
"""
from __future__ import annotations

import json
from collections import Counter

TOKENS = ("add", "mul", "log", "pair", "fmt", "sw", "intfp", "fadd", "fmul", "fcmp", "fdiv", "round", "unpack", "fma")
RULES = ("none", "all", "per_mode", "per_lane", "comparator", "stage", "arith", "pcc", "rep")
KINDS = ("adder", "multiplier", "logic", "comparator", "shifter", "bitcount",
         "rounder", "unpacker", "fp_adder", "fp_multiplier", "fp_comparator", "fp_fma")


def manifest_table(manifest) -> dict:
    """{structure id: {kind, width, format, mode, lane}} of the slotted structures."""
    from chialu.targets.rtl.structures import is_inline
    return {s.id: {"kind": s.kind, "width": int(s.width or 0), "format": s.format, "mode": s.mode, "lane": s.lane}
            for s in manifest if s.slot and not is_inline(s)}


def plan_tokens(plan_name: str) -> dict:
    """{axis: rule} of a scheme name (`add-none_mul-all_log-per_lane_sw-pcc`). A rule may hold an
    underscore itself (per_lane, per_mode), so the name splits only before `<axis>-`; splitting at every
    underscore read `log-per_lane` as `log: per` and left every PLAN__*_per_lane/per_mode column unset."""
    import re
    out = {}
    for tok in re.split(r"_(?=[a-z]+-)", str(plan_name)):
        if "-" in tok:
            k, v = tok.split("-", 1)
            out[k] = v
    return out


def scheme_groups(plan):
    """Explicit banks plus FMA banks selected through their sharing pins."""
    groups = {g: list(v.get("members") or []) for g, v in ((plan or {}).get("shared") or {}).items()}
    for sid, entry in ((plan or {}).get("structures") or {}).items():
        if sid.endswith(".fp_fma") and entry.get("pin", {}).get("sharing") == "shared_across_formats":
            groups.setdefault(f"fp_fma_bank_{sid.split('.')[1]}", []).append(sid)
    return groups


def plan_features(plan_name: str, plan: dict | None, table: dict) -> dict:
    """coeff/xplan_features.plan_features: the rules, the groups, the kinds grouped, the union geometry."""
    f = {}
    toks = plan_tokens(plan_name)
    for t in TOKENS:
        for r in RULES:
            f[f"PLAN__{t}_{r}"] = 1.0 if toks.get(t) == r else 0.0
        if t in toks:
            f[f"PLAN__{t}_{toks[t]}"] = 1.0
    groups = list(scheme_groups(plan).items())
    groups = [(g, m) for g, m in groups if len(m) >= 2]
    f["SHR__n_groups"] = float(len(groups))
    sizes = [len(m) for _g, m in groups] or [0]
    f["SHR__max_gsize"] = float(max(sizes))
    f["SHR__sum_grouped"] = float(sum(sizes))
    f["SHR__mean_gsize"] = float(sum(sizes) / max(1, len(groups)))
    f["SHR__frac_grouped"] = float(sum(sizes)) / max(1, len(table))
    per_kind = Counter()
    for _g, m in groups:
        for sid in m:
            if sid in table:
                per_kind[table[sid]["kind"]] += 1
    for kind in KINDS:
        f[f"KIND__{kind}_grouped"] = float(per_kind.get(kind, 0))
    for _g, m in groups:
        sts = [table[s] for s in m if s in table]
        if not sts:
            continue
        pre = f"GEO__{sts[0]['kind']}"
        w = [s["width"] for s in sts] or [0]
        f[pre + "_sum_over_max_w"] = max(f.get(pre + "_sum_over_max_w", 0.0), sum(w) / max(1, max(w)))
        f[pre + "_fmtspan"] = max(f.get(pre + "_fmtspan", 0.0), float(len({s["format"] for s in sts})))
        f[pre + "_modespan"] = max(f.get(pre + "_modespan", 0.0), float(len({s["mode"] for s in sts})))
        f[pre + "_lanespan"] = max(f.get(pre + "_lanespan", 0.0), float(len({s["lane"] for s in sts})))
        f[pre + "_gsize"] = max(f.get(pre + "_gsize", 0.0), float(len(sts)))
    return f


def row_features(rows: list, table: dict, plan: dict | None) -> dict:
    """coeff/xplan_features.row_features, with a shared group's row given to each of its members
    (the estimate prices a group as one unit under the group's name)."""
    members = scheme_groups(plan)
    by: dict = {}
    for r in rows:
        rid = str(r.get("id"))
        for sid in members.get(rid, [rid]):
            by.setdefault(sid, r)
    f = {}
    for i in sorted(table):
        r = by.get(i)
        f[f"ROW__{i}__area"] = float(r.get("area_um2") or 0.0) if r else 0.0
        f[f"ROW__{i}__delay"] = float(r.get("delay_ps") or 0.0) if r else 0.0
    a = [float(r.get("area_um2") or 0.0) for r in rows] or [0.0]
    d = [float(r.get("delay_ps") or 0.0) for r in rows] or [0.0]
    f["AGG__area_sum"], f["AGG__area_max"], f["AGG__area_mean"] = sum(a), max(a), sum(a) / len(a)
    f["AGG__delay_max"], f["AGG__delay_mean"] = max(d), sum(d) / len(d)
    ds, as_ = sorted(d, reverse=True), sorted(a, reverse=True)
    for k in (1, 2, 3, 5):
        f[f"AGG__delay_top{k}"] = float(sum(ds[:k]))
        f[f"AGG__area_top{k}"] = float(sum(as_[:k]))
    f["AGG__n_rows"] = float(len(rows))
    return f


def nest(vals: dict) -> dict:
    """The `decl.core` form of `core.*` variables (nested by slot, index and choice)."""
    out: dict = {}
    for name, v in vals.items():
        parts = str(name).split(".")
        if parts[0] != "core" or len(parts) < 2:
            continue
        d = out
        for p in parts[1:-1]:
            nxt = d.get(p)
            if not isinstance(nxt, dict):
                nxt = d[p] = {}
            d = nxt
        d[parts[-1]] = v
    return out


def features(files: dict, vals: dict, scheme: str, plan: dict | None, table: dict, est: dict) -> dict:
    """The feature dict of one declaration (`core.*` values) under one sharing scheme. `est` holds
    the estimate node's pdk, effort, glue_json and context_json."""
    from adir.registry import underlying
    from chialu import eda
    r = underlying(eda.estimate)(files, nest(vals), est.get("pdk", "nangate45"), est.get("effort", "medium"),
                                 1.0, 1.0, json.dumps(plan) if plan else "", est.get("glue_json") or "",
                                 est.get("context_json") or "")
    f = {"EST__area": float(r.get("area_um2") or 0.0), "EST__delay": float(r.get("delay_ps") or 0.0),
         "EST__coverage": float(r.get("coverage") or 0.0)}
    f.update(row_features(r.get("rows") or [], table, plan))
    f.update(plan_features(scheme, plan, table))
    for name, v in built_vals(vals, plan).items():
        if (str(name).startswith("core.") or name == "x_form") and not isinstance(v, (dict, list)):
            key = name[len("core."):] if name.startswith("core.") else name
            f[f"OH__{key}__{v}"] = 1.0
    return f


def built_vals(vals: dict, plan: dict | None) -> dict:
    """The declaration as the scheme builds it: a unit-level component the scheme decides (`components`,
    e.g. sw-pcc / sw-rep fix `core.subword`) takes the plan's family and pins, and the declared component's
    other choices go (they belong to a family that is not built). About half the int rows declared another
    subword family than the one built, and the one-hot carried the unbuilt one."""
    out = dict(vals)
    for comp, entry in ((plan or {}).get("components") or {}).items():
        fam = entry.get("family")
        if fam is None:
            continue
        pre = f"core.{comp}."
        if out.get(pre + "family") != fam:
            for k in [k for k in out if k.startswith(pre)]:
                del out[k]
        out[pre + "family"] = fam
        for k, v in (entry.get("pin") or {}).items():
            out[pre + k] = v
    return out


def vector(f: dict, names: list):
    import numpy as np
    return np.array([f.get(n, 0.0) for n in names], dtype=np.float32)


def decl_vars(decl: dict, prefix: str = "core") -> dict:
    """The `core.*` variables of a nested declaration (`decl.core`)."""
    out: dict = {}
    for k, v in (decl or {}).items():
        if isinstance(v, dict):
            out.update(decl_vars(v, f"{prefix}.{k}"))
        else:
            out[f"{prefix}.{k}"] = v
    return out


def scheme_repair(vals: dict, plan: dict | None) -> dict:
    """Project a sampled point onto the scheme's conditional space.

    Tie shared FP slots, separate add/multiply only in participating modes,
    and exclude fixed-format fused rounding from shared unrounded banks.
    Dedicated modes keep their independently sampled families and pins.
    The sampler, surrogate features and front renderer use this same point.
    """
    if not plan:
        return dict(vals)
    out = dict(vals)
    groups = list(((plan or {}).get("shared") or {}).values())
    separate = {str(m).split(".")[0] for g in groups for m in g.get("members", [])
                if str(m).rsplit(".", 1)[-1] in ("fp_adder", "fp_multiplier")}
    for mode in separate:
        prefix = f"core.fp_fma.{mode}."
        out = {k: v for k, v in out.items() if not k.startswith(prefix)}
        out[prefix + "family"] = "separate_multiplier_and_adder"
    # Sharing owns the whole slot selection, including inner cells. Connected
    # lane groups must agree too: the variables are per mode, not per lane.
    components, canonical = [], set()
    for g in groups:
        members = [str(m).split(".") for m in g.get("members", [])]
        if not members or any(m[-1] != members[0][-1] for m in members):
            continue
        from chialu.plans import FLOAT_SHARE_KINDS
        if members[0][-1] not in FLOAT_SHARE_KINDS:
            continue
        prefixes = {f"core.{m[-1]}.{m[0]}." for m in members}
        if g.get("canonical"):
            c = str(g["canonical"]).split(".")
            canonical.add(f"core.{c[-1]}.{c[0]}.")
        for old in components[:]:
            if old & prefixes:
                prefixes |= old
                components.remove(old)
        components.append(prefixes)
    for prefixes in components:
        # the bank's narrowest member (plans._narrowest) when the scheme names it: its domains are a subset
        # of the wider members', so its choices are valid for all of them
        first = sorted(prefixes & canonical)[0] if prefixes & canonical else sorted(prefixes)[0]
        choices = {k[len(first):]: v for k, v in out.items() if k.startswith(first)}
        if first.startswith("core.fp_multiplier.") and choices.get("family") == "round_fused_in_reduction":
            # A shared multiplier returns unrounded X. This family injects
            # rounding for one fixed format, so it is outside this scheme's
            # conditional space. Retain the common multiplier/exponent cells.
            choices = {k: v for k, v in choices.items() if k.startswith(("sig_mul.", "exp_adder."))}
            choices["family"] = "sig_mul_then_round"
        out = {k: v for k, v in out.items() if not any(k.startswith(p) for p in prefixes)}
        for prefix in prefixes:
            out.update({prefix + k: v for k, v in choices.items()})
    fma_modes = sorted({sid.split(".")[0] for sid, entry in ((plan or {}).get("structures") or {}).items()
                        if sid.endswith(".fp_fma") and entry.get("pin", {}).get("sharing") == "shared_across_formats"})
    if fma_modes:
        first = f"core.fp_fma.{fma_modes[0]}."
        choices = {k[len(first):]: v for k, v in out.items() if k.startswith(first)}
        if choices.get("family") not in ("classic_fma", "reduced_latency_fma", "multipath_fma", "bridge_fma"):
            choices = {"family": "classic_fma"}
        choices["sharing"] = "shared_across_formats"
        # The shared FMA also produces unrounded X; its optional local
        # rounding stage has the same fixed-format restriction.
        if choices.get("rounding_position") == "fused_with_cpa_dual_sum":
            choices["rounding_position"] = "post_cpa"
        for mode in fma_modes:
            prefix = f"core.fp_fma.{mode}."
            out = {k: v for k, v in out.items() if not k.startswith(prefix)}
            out.update({prefix + k: v for k, v in choices.items()})
    # An explicit scheme determines the sharing subsets. Do not let randomly
    # drawn implicit selectors widen them or invent a singleton bank.
    for k, v in list(out.items()):
        if k.startswith(("core.rounder.", "core.unpacker.")) and k.endswith(".family") and v == "shared_across_formats":
            out[k] = "shared_per_lane"
        if k.startswith("core.fp_fma.") and k.endswith(".sharing") and k.split(".")[2] not in fma_modes:
            out[k] = "dedicated_per_mode"
    # a partitioned carry chain is one lane-partitioned adder serving every mode, so the modes' adders
    # take one declaration: the first mode's (measured: every sw-pcc point with differing adder families
    # was refused by the seed, "one lane-partitioned adder serves modes [..], whose declared adder
    # families differ")
    sub = (((plan or {}).get("components") or {}).get("subword") or {}).get("family") or out.get("core.subword.family")
    if sub == "partitioned_carry_chain":
        idx = sorted({k.split(".")[2] for k in out if k.startswith("core.adder.") and k.count(".") >= 3})
        if len(idx) > 1:
            first = {k[len(f"core.adder.{idx[0]}."):]: v for k, v in out.items() if k.startswith(f"core.adder.{idx[0]}.")}
            out = {k: v for k, v in out.items() if not any(k.startswith(f"core.adder.{i}.") for i in idx[1:])}
            for i in idx[1:]:
                out.update({f"core.adder.{i}.{c}": v for c, v in first.items()})
    return out
