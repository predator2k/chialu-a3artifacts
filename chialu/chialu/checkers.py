"""Which checker parameters meet a detection bound (docs/checker-spec-plan.md).

    python3 -m chialu.checkers select --formats int16,fp16 --ops add,sub,adc,sbb,neg,abs,mul_wide \\
        --random-alias 5e-2 --single-bit 1.0 [--fallback duplicate] [--families multi_residue,rns_redundant] \\
        [--pdk nangate45] [--dual]
    python3 -m chialu.checkers explain --family residue --pin modulus=7 --formats int16 --ops add,sub \\
        [--random-alias 5e-2] [--single-bit 1.0]
    python3 -m chialu.checkers floor --formats int16 [--ops ...]
    python3 -m chialu.checkers emit --formats ... --ops ... [--random-alias ..] [--top N]

`select` walks every family of checker_space() and every point of its
own choices (and of the comparator family, which enters the model
through its weight compare), computes `output_alias` and the
single-bit floor for the named formats, keeps the points that meet
both bounds and cover the named ops under the given fallback, and
prints them sorted by the area the synthesis database holds for the
point (the kind `checker`; a database without the kind leaves the
columns empty and orders by the alias rate). `explain` prints one
point's numbers and the reason a bound rejects it; `floor` the lowest
`output_alias` and the highest single-bit floor each family reaches;
`emit` the survivors as a `choices:` block for a run file.

A format is `fmt` or `NxFMT` (N lanes: a code's escape compounds per
lane). A (format, op) pair the unit's legality table does not admit is
dropped and reported. `feasible_families` (chialu.targets.rtl.alu_checker)
is the library function behind `select`; the build calls the same one.
"""
from __future__ import annotations

import argparse
import json
import sys

from chialu.targets.rtl.alu_checker import FALLBACKS, FAMILIES, feasibility


def parse_formats(text: str) -> tuple:
    """([(count, Format)], {name: count}) of `fmt,NxFMT,...`."""
    from chialu.verify.formats import parse_format
    modes, lanes = [], {}
    for item in str(text).split(","):
        item = item.strip()
        if not item:
            continue
        count = 1
        head, sep, tail = item.partition("x")
        if sep and head.isdigit() and tail:
            count, item = int(head), tail
        f = parse_format(item)
        modes.append((count, f))
        lanes[f.name] = max(count, lanes.get(f.name, 1))
    if not modes:
        raise ValueError("no format")
    return modes, lanes


def rule_pairs(modes, ops) -> tuple:
    """(the legal (Format, op) pairs, the pairs dropped as illegal)."""
    from chialu.verify.alu_ref import legal_pairs
    legal = legal_pairs(modes, list(ops))
    pairs, dropped = [], []
    for i, (_n, f) in enumerate(modes):
        for op in ops:
            (pairs if (i, op) in legal else dropped).append((f, op))
    return pairs, dropped


def parse_pins(items) -> dict:
    """{pin: value} of `--pin k=v` items; a value parses as JSON when it can."""
    out = {}
    for item in items or ():
        k, sep, v = str(item).partition("=")
        if not sep:
            raise ValueError(f"--pin {item!r}: k=v")
        try:
            out[k] = json.loads(v)
        except json.JSONDecodeError:
            out[k] = v
    return out


def point_cost(pdk: str | None, point: dict, width: int) -> dict:
    """{area_um2, delay_ps} of a point from the synthesis database's
    `checker` kind (the smallest row whose pins carry the point's own
    pins and comparator family), or {} without a row."""
    if not pdk:
        return {}
    from chialu import synthdb
    try:
        rows = synthdb.at_width(pdk, "checker", width, family=point["family"])
    except Exception:  # noqa: BLE001  a database that is absent or unreadable leaves the columns empty
        return {}
    want = {str(k): v for k, v in point["pins"].items()}
    if point.get("comparator"):
        want["comparator.family"] = point["comparator"]["family"]
    best = None
    for r in rows:
        pins = r.get("pins") or {}
        if all(str(pins.get(k)) == str(v) for k, v in want.items()):
            if best is None or (r.get("area_um2") or 0) < (best.get("area_um2") or 0):
                best = r
    if best is None:
        return {}
    return {"area_um2": best.get("area_um2"), "delay_ps": best.get("delay_ps"),
            "interpolated": bool(best.get("interpolated"))}


def _pins_text(point: dict) -> str:
    parts = [f"{k}={v}" for k, v in point["pins"].items()]
    if point.get("comparator"):
        parts.append("comparator=" + ",".join(str(v) for v in point["comparator"].values()))
    return " ".join(parts) or "-"


def _requirement(args) -> dict | None:
    req = {}
    if getattr(args, "random_alias", None) is not None:
        req["random_alias"] = float(args.random_alias)
    if getattr(args, "single_bit", None) is not None:
        req["single_bit"] = float(args.single_bit)
    return req or None


def _declared(args, pins=None) -> list | None:
    fams = [f.strip() for f in (args.families or "").split(",") if f.strip()] if getattr(args, "families", None) else None
    if getattr(args, "family", None):
        return [{"family": args.family, **(pins or {})}]
    if fams:
        return [{"family": f} for f in fams]
    return None


def run(args, pins=None) -> tuple:
    modes, lanes = parse_formats(args.formats)
    ops = [o.strip() for o in str(args.ops or "").split(",") if o.strip()]
    if not ops:
        raise ValueError("--ops names at least one op")
    pairs, dropped = rule_pairs(modes, ops)
    if not pairs:
        raise ValueError("no legal (format, op) pair: " + ", ".join(f"{f.name}/{op}" for f, op in dropped))
    cands, rej = feasibility(pairs, _requirement(args), args.fallback, _declared(args, pins),
                             dual_possible=bool(getattr(args, "dual", False)), lanes=lanes)
    width = max(f.width for _n, f in modes)
    for p in cands + rej:
        p["cost"] = point_cost(getattr(args, "pdk", None), p, width)
    cands.sort(key=lambda p: (p["cost"].get("area_um2") is None, p["cost"].get("area_um2") or 0.0,
                              p["output_alias"], p["family"], json.dumps(p["pins"], sort_keys=True, default=str)))
    return cands, rej, dropped


def _table(points: list, out=None) -> None:
    out = out if out is not None else sys.stdout
    head = f"{'family':<28} {'pins':<58} {'output_alias':>12} {'single_bit':>10} {'area um2':>10} {'delay ps':>9}  mechanism"
    print(head, file=out)
    for p in points:
        cost = p.get("cost") or {}
        area = f"{cost['area_um2']:.0f}" if cost.get("area_um2") is not None else "-"
        delay = f"{cost['delay_ps']:.0f}" if cost.get("delay_ps") is not None else "-"
        mech = f"code {p['code_pairs']}, replica {p['replica_pairs']}, unchecked {p['unchecked_pairs']}"
        print(f"{p['family']:<28} {_pins_text(p):<58} {p['output_alias']:>12.4g} {p['single_bit']:>10.4g} "
              f"{area:>10} {delay:>9}  {mech}", file=out)


def cmd_select(args) -> int:
    cands, rej, dropped = run(args)
    _table(cands)
    classes = {}
    for p in rej:
        classes[p["reject_class"]] = classes.get(p["reject_class"], 0) + 1
    tail = ", ".join(f"{n} on {'the alias' if c == 'alias' else 'the single-bit floor' if c == 'single_bit' else 'op coverage'}"
                     for c, n in sorted(classes.items()))
    total = len(cands) + len(rej)
    print(f"[chialu.checkers] {len(cands)} of {total} points meet the bound" + (f"; {tail}" if tail else ""))
    if dropped:
        print("[chialu.checkers] illegal pairs dropped: " + ", ".join(f"{f.name}/{op}" for f, op in dropped))
    if args.json:
        with open(args.json, "w") as fh:
            json.dump({"candidates": cands, "rejected": rej,
                       "dropped": [f"{f.name}/{op}" for f, op in dropped]}, fh, indent=1, default=str)
    return 0 if cands else 1


def cmd_explain(args) -> int:
    pins = parse_pins(args.pin)
    if not args.family:
        raise ValueError("explain needs --family")
    cands, rej, dropped = run(args, pins)
    points = cands + rej
    if not points:
        print(f"[chialu.checkers] no point of {args.family} at {pins}")
        return 1
    for p in points:
        verdict = "meets the bound" if "reject" not in p else f"rejected on {p['reject_class']}: {p['reject']}"
        print(f"{p['family']} {_pins_text(p)}: output_alias {p['output_alias']:.4g} (moduli {p['moduli'] or '-'}), "
              f"single_bit {p['single_bit']:.4g}, exact compare {p['exact']}; {verdict}")
        for pair, mech in p["mechanism"].items():
            print(f"    {pair}: {mech}")
    if dropped:
        print("[chialu.checkers] illegal pairs dropped: " + ", ".join(f"{f.name}/{op}" for f, op in dropped))
    return 0 if cands else 1


def cmd_floor(args) -> int:
    args.random_alias = None
    args.single_bit = None
    modes, lanes = parse_formats(args.formats)
    ops = [o.strip() for o in str(args.ops or "add,sub,adc,sbb,neg,abs,mul_wide,fadd,fsub,fmul").split(",") if o.strip()]
    pairs, _dropped = rule_pairs(modes, ops)
    cands, rej, _ = run(argparse.Namespace(formats=args.formats, ops=",".join(ops), fallback="duplicate",
                                           families=args.families, family=None, dual=False, pdk=None,
                                           random_alias=None, single_bit=None))
    rows = {}
    for p in cands + rej:
        r = rows.setdefault(p["family"], {"alias": None, "single_bit": None, "at": None, "points": 0})
        r["points"] += 1
        if p["code_pairs"] and (r["alias"] is None or p["output_alias"] < r["alias"]):
            r["alias"], r["at"] = p["output_alias"], _pins_text(p)
        if r["single_bit"] is None or p["single_bit"] > r["single_bit"]:
            r["single_bit"] = p["single_bit"]
    print(f"{'family':<28} {'lowest output_alias':>20} {'highest single_bit':>19} {'points':>7}  at")
    for fam in FAMILIES:
        r = rows.get(fam)
        if r is None:
            continue
        alias = f"{r['alias']:.4g}" if r["alias"] is not None else "no coded pair"
        print(f"{fam:<28} {alias:>20} {r['single_bit']:>19.4g} {r['points']:>7}  {r['at'] or '-'}")
    return 0


def emit_choices(cands: list, top: int | None = None) -> list:
    """The survivors as `choices` entries, one per family, each pin the
    union of its surviving values (a scalar when one), capped at the
    cheapest `top` points; the build prunes a combination of the union
    the requirement rejects, so a union is safe to paste."""
    chosen = cands[:top] if top else cands
    entries: dict = {}
    for p in chosen:
        e = entries.setdefault(p["family"], {"family": p["family"]})
        for k, v in p["pins"].items():
            e.setdefault(k, [])
            if v not in e[k]:
                e[k].append(v)
        if p.get("comparator"):
            e.setdefault("comparator.family", [])
            if p["comparator"]["family"] not in e["comparator.family"]:
                e["comparator.family"].append(p["comparator"]["family"])
            for k, v in p["comparator"].items():
                if k == "family":
                    continue
                e.setdefault(f"comparator.{k}", [])
                if v not in e[f"comparator.{k}"]:
                    e[f"comparator.{k}"].append(v)
    out = []
    for e in entries.values():
        out.append({k: (v[0] if isinstance(v, list) and len(v) == 1 else v) for k, v in e.items()})
    return out


def cmd_emit(args) -> int:
    cands, _rej, _dropped = run(args)
    if not cands:
        print("[chialu.checkers] no point meets the bound; nothing to emit", file=sys.stderr)
        return 1
    import yaml
    print(yaml.safe_dump({"choices": emit_choices(cands, args.top)}, sort_keys=False, default_flow_style=None).rstrip())
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    def common(p, ops_required=True):
        p.add_argument("--formats", required=True, help="fmt or NxFMT, comma-separated")
        p.add_argument("--ops", required=ops_required, help="op names, comma-separated")
        p.add_argument("--random-alias", type=float, default=None, help="the largest output_alias admitted")
        p.add_argument("--single-bit", type=float, default=None, help="the smallest single-bit floor admitted")
        p.add_argument("--fallback", choices=FALLBACKS, default="duplicate")
        p.add_argument("--families", default=None, help="restrict to these families")
        p.add_argument("--family", default=None, help="one family (explain)")
        p.add_argument("--dual", action="store_true", help="the unit exposes a second unary result (neg/abs are duplicated)")
        p.add_argument("--pdk", default=None, help="order by the synthesis database of this PDK")
        p.add_argument("--json", default=None, help="write the points to this file")

    s = sub.add_parser("select", help="the points that meet the bound, cheapest first")
    common(s)
    e = sub.add_parser("explain", help="one point's numbers and the reason a bound rejects it")
    common(e)
    e.add_argument("--pin", action="append", default=[], help="k=v of the family's own pins or comparator.family")
    f = sub.add_parser("floor", help="the lowest output_alias each family reaches")
    common(f, ops_required=False)
    m = sub.add_parser("emit", help="the survivors as a choices: block")
    common(m)
    m.add_argument("--top", type=int, default=None, help="the cheapest N points")
    args = ap.parse_args(argv)
    try:
        return {"select": cmd_select, "explain": cmd_explain, "floor": cmd_floor, "emit": cmd_emit}[args.cmd](args)
    except ValueError as e:
        print(f"[chialu.checkers] {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
