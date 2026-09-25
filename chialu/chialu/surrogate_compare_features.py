"""Comparison-only path/count features; production XGBoost columns stay unchanged."""
import fnmatch
import math
from collections import Counter
from chialu.surrogate_features import scheme_groups


def _path_members(rows: list, table: dict, plan: dict | None) -> dict:
    """Resolve selectors in partition order, including implicit per-lane FMA banks.

    Mixed adder/comparator groups still have separate estimate rows; attach their
    group geometry without treating those two rows as an extra series stage.
    """
    groups, used = {}, set()
    for group, selectors in scheme_groups(plan).items():
        members = []
        for selector in selectors:
            selected = [sid for sid, s in table.items()
                        if sid == selector or s["kind"] == selector or fnmatch.fnmatchcase(sid, selector)]
            members.extend(sid for sid in selected if sid not in used and sid not in members)
        groups[group] = members
        used.update(members)
    for row in rows:
        rid = str(row["id"])
        if rid.startswith("fp_fma_bank_l") and not groups.get(rid):
            lane = int(rid.rsplit("l", 1)[1])
            groups[rid] = [sid for sid, s in table.items() if s["kind"] == "fp_fma"
                           and s["lane"] == lane and s["mode"] in row.get("modes", [])]
    # A mixed int/FP bank can have both a bank row and an individual FP
    # remainder row. That remainder is dedicated; it does not inherit the
    # bank's fan-in. Mixed pairs with only individual rows retain group geometry.
    row_ids = {str(row["id"]) for row in rows}
    by_member = {sid: members for group, members in groups.items() if group not in row_ids for sid in members}
    return {str(r["id"]): groups.get(str(r["id"]), by_member.get(str(r["id"]),
            [str(r["id"])] if str(r["id"]) in table else [])) for r in rows}


def path_features(rows: list, table: dict, plan: dict | None) -> dict:
    """Cheap DB-path descriptors, with exactly estimate's max-per-kind composition.

    These are paths through independently priced units, not measured STA paths.
    Lanes run in parallel: take each series kind's maximum, then add the
    parallel-op maximum. Sharing geometry describes mux *proxies*, not gate
    delays: modes are mux inputs, whereas lanes within a mode are concurrent.
    No extra DB lookups, rendering, labels, or learned vocabulary are required.
    """
    from chialu.eda import SERIES_KINDS
    members = _path_members(rows, table, plan)
    units = []
    for row in rows:
        rid = str(row["id"])
        sts = [table[sid] for sid in members[rid]]
        modes = set(row.get("modes") or [s["mode"] for s in sts])
        widths = [s["width"] for s in sts]
        kind = str(row.get("kind", "unknown"))
        # Packed integer banks span the full per-mode bus. Other banks use the
        # widest member. This is a width proxy, not the FP union exponent geometry.
        bus = max((sum(s["width"] for s in sts if s["mode"] == m and s["kind"] == kind)
                   for m in modes), default=0)
        union = bus if kind in ("adder", "multiplier", "logic") else max(widths, default=0)
        if kind == "adder" and any(s["kind"] == "fp_adder" for s in sts):
            fine = max(1, min(s["width"] for s in sts if s["kind"] == "adder"))
            sig = max(s["width"] for s in sts if s["kind"] == "fp_adder")
            union = math.ceil(max(bus, sig + 1) / fine) * fine
        mode_span = max(len(modes), len({s["mode"] for s in sts}))
        geom = {"members": len(sts), "shared": float(len(sts) > 1), "modes": mode_span,
                "lanes": len({s["lane"] for s in sts}), "formats": len({s["format"] for s in sts}),
                "union_width_proxy": union,
                "union_over_member_width": union / max(1.0, sum(widths) / max(1, len(widths))),
                "mux_depth_proxy": math.ceil(math.log2(max(1, mode_span))),
                "mux_bit_proxy": max(0, mode_span - 1) * union}
        units.append({"id": rid, "kind": kind, "family": str(row.get("family", "unknown")),
                      "delay": float(row.get("delay_ps") or 0.0),
                      "area": float(row.get("area_um2") or 0.0), "modes": modes, "geom": geom})
    # Sorting also makes ties independent of DB row order.
    units.sort(key=lambda u: (-u["delay"], u["id"]))
    modes = sorted({s["mode"] for s in table.values()} | {m for u in units for m in u["modes"]})
    f, paths = {}, []
    kinds = sorted({s["kind"] for s in table.values()} | {u["kind"] for u in units})

    def describe(us, pre):
        by_kind = {}
        for u in us:
            by_kind.setdefault(u["kind"], u)
        parallel = [u for u in us if u["kind"] not in SERIES_KINDS]
        path = [by_kind[k] for k in SERIES_KINDS if k in by_kind] + parallel[:1]
        series = sum(by_kind[k]["delay"] for k in SERIES_KINDS if k in by_kind)
        par = parallel[0]["delay"] if parallel else 0.0
        f[pre + "series_sum"], f[pre + "parallel_max"], f[pre + "total"] = series, par, series + par
        f[pre + "n_units"] = float(len(us))
        f[pre + "path_n_units"] = float(len(path))
        f[pre + "path_shared_units"] = sum(u["geom"]["shared"] for u in path)
        f[pre + "path_delay_weighted_area"] = sum(u["area"] * u["delay"] for u in path) / max(series + par, 1e-12)
        f[pre + "mode_delay_weighted_area"] = sum(u["area"] * u["delay"] for u in us) / max(sum(u["delay"] for u in us), 1e-12)
        for k in (1, 2, 3, 5):
            f[pre + f"delay_top{k}"] = sum(u["delay"] for u in us[:k])
        for kind in kinds:
            f[pre + f"kind_{kind}__delay"] = by_kind[kind]["delay"] if kind in by_kind else 0.0
        for key in ("members", "modes", "lanes", "formats", "union_width_proxy",
                    "union_over_member_width", "mux_depth_proxy", "mux_bit_proxy"):
            f[pre + f"path_{key}_sum"] = sum(u["geom"][key] for u in path)
            f[pre + f"path_{key}_max"] = max((u["geom"][key] for u in path), default=0.0)
        return series + par, path

    for mode in modes:
        us = [u for u in units if mode in u["modes"]]
        total, path = describe(us, f"PATH__m{mode}__")
        paths.append((total, mode, us, path))
    paths.sort(key=lambda p: (-p[0], p[1]))
    totals = [p[0] for p in paths]
    f["PATH__max"] = totals[0] if totals else 0.0
    f["PATH__second"] = totals[1] if len(totals) > 1 else 0.0
    f["PATH__gap"] = f["PATH__max"] - f["PATH__second"]
    f["PATH__relative_gap"] = f["PATH__gap"] / max(f["PATH__max"], 1e-12)
    if paths:
        _, mode, us, path = paths[0]
        f[f"PATH__critical_mode__m{mode}"] = 1.0
        describe(us, "PATH__critical__")
        if path:
            critical = min(path, key=lambda u: (-u["delay"], u["id"]))
            f[f"PATH__critical_kind__{critical['kind']}"] = 1.0
            f[f"PATH__critical_family__{critical['kind']}__{critical['family']}"] = 1.0
            for key, value in critical["geom"].items():
                f[f"PATH__critical_unit__{key}"] = float(value)
    return {k: float(v) for k, v in f.items()}


def value_count_features(vals: dict) -> dict:
    """Pool active scalar choices across positions, without fitting a vocabulary.

    Families share a column even in different nested slots. Pins pool by leaf
    name and value, and by top-level slot, so unrelated numeric pins do not
    collide. Counts are per declaration slot, not duplicated per physical lane.
    """
    f = Counter()
    for name, value in vals.items():
        if not str(name).startswith("core.") or isinstance(value, (dict, list)):
            continue
        parts = str(name).split(".")
        if len(parts) < 3:
            continue
        leaf, slot = parts[-1], parts[1]
        f[f"COUNT__{leaf}__{value}"] += 1
        f[f"COUNT__slot_{slot}__{leaf}__{value}"] += 1
    return {k: float(v) for k, v in f.items()}
