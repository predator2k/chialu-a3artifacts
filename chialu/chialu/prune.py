"""Prune a run's family domains by the synthesis database: for every
slotted structure of the bound unit, a family whose fastest library
variant at the structure's width exceeds the run's clock_ps (times the
structure's share of it) by more than the threshold leaves the family
variable's search domain; a family slightly over stays, and a family
the database does not cover stays. Prints the table and the overlay
(`core.<kind>.<index>.family: {search: [...]}`), and with --out writes
the run file with those domains. `--best delay` (or `area`) fixes every
structure to the database's best family at its width instead, with the
pins of the row that won: the no-model reference a searched run is
measured against.

    python3 -m chialu.prune <run.yaml> [--pdk nangate45] [--threshold 0.10] [--fraction 1.0] [--out run.pruned.yaml]
    python3 -m chialu.prune <run.yaml> --best delay [--out run.best.yaml]
"""
from __future__ import annotations

import argparse
import sys

import yaml

from chialu import timing


def prune(instance, pdk: str, threshold: float, fraction: float) -> tuple[list, dict]:
    """(table rows, overlay) for an instance: one table row per family
    per structure variable, the overlay the search domains that shrink."""
    rows = timing.load(pdk)
    clock = timing.clock_of(instance)
    if not rows:
        raise SystemExit(f"prune: no database for {pdk} (run python3 -m chialu.synthdb build --pdk {pdk})")
    if clock is None:
        raise SystemExit("prune: the run binds no clock_ps")
    limit = clock * fraction * (1.0 + threshold)
    manifest = (instance.elaboration.info or {}).get("manifest") or []
    table, overlay = [], {}
    seen = set()
    for s in manifest:
        slot = s.get("slot") or s.get("kind")
        if slot not in timing.KINDS:
            continue
        from chialu.prompts import var_prefix
        name = var_prefix(s) + "family"
        if name in seen:
            continue
        seen.add(name)
        b = instance.bindings.get(name)
        if b is None or b.time != "search" or not b.domain.finite():
            continue
        members = list(b.domain.members())
        best = timing.best(rows, slot, int(s["width"]), clock)
        kept = []
        for fam in members:
            r = best.get(fam)
            delay = r["delay_ps"] if r else None
            keep = delay is None or delay <= limit
            if keep:
                kept.append(fam)
            table.append({"variable": name, "width": int(s["width"]), "family": fam,
                          "delay_ps": delay, "area_um2": r["area_um2"] if r else None,
                          "variant": r["variant"] if r else "", "keep": keep})
        if kept and kept != members:
            overlay[name] = {"search": kept} if len(kept) > 1 else {"fixed": kept[0]}
    return table, overlay


def best_declaration(instance, pdk: str, metric: str = "delay") -> tuple[list, dict]:
    """(table rows, overlay) that fix every slotted structure to the
    database's best family at that structure's width, with the pins of
    the row that won: the no-model reference a run is measured against
    (the evaluation's tier 2). `metric` is delay or area."""
    from chialu.prompts import var_prefix
    rows = timing.load(pdk)
    clock = timing.clock_of(instance)
    if not rows:
        raise SystemExit(f"prune: no database for {pdk} (run python3 -m chialu.synthdb build --pdk {pdk})")
    manifest = (instance.elaboration.info or {}).get("manifest") or []
    table, overlay, seen = [], {}, set()
    for s in manifest:
        slot = s.get("slot") or s.get("kind")
        if slot not in timing.KINDS or not s.get("width"):
            continue
        name = var_prefix(s) + "family"
        if name in seen:
            continue
        seen.add(name)
        b = instance.bindings.get(name)
        if b is None or not b.domain.finite():
            continue
        members = set(b.domain.members())

        def admitted(r) -> bool:
            # the row's family and every pin it fixes are values the unit's variables admit (an exact
            # unit's slots refuse the approximate families a database row may carry as a component)
            if r["family"] not in members:
                return False
            for pin, value in (r.get("pins") or {}).items():
                if str(pin).startswith("_"):
                    continue
                pb = instance.bindings.get(var_prefix(s) + str(pin))
                if pb is not None and pb.domain.finite() and value not in set(pb.domain.members()):
                    return False
            return True
        cand = [r for r in timing.best(rows, slot, int(s["width"]), clock).values() if admitted(r)]
        if not cand:
            continue
        key = (lambda r: (r["delay_ps"], r.get("area_um2") or 0)) if metric == "delay" \
            else (lambda r: (r.get("area_um2") or 0, r["delay_ps"]))
        r = min(cand, key=key)
        overlay[name] = {"fixed": r["family"]}
        for pin, value in sorted((r.get("pins") or {}).items()):
            if str(pin).startswith("_"):
                continue
            pv = var_prefix(s) + str(pin)
            if instance.bindings.get(pv) is not None:
                overlay[pv] = {"fixed": value}
        table.append({"variable": name, "width": int(s["width"]), "family": r["family"],
                      "variant": r.get("variant", "-"), "delay_ps": r["delay_ps"],
                      "area_um2": r.get("area_um2"), "from_width": r.get("from_width")})
    return table, overlay


def _absolute_paths(doc: dict, run_file: str) -> dict:
    """The run file's relative paths (the knowledge directory, the role
    file, the task file or script) made absolute against the source run
    file's directory, so the copy written elsewhere still finds them."""
    from pathlib import Path
    base = Path(run_file).resolve().parent
    adir = doc.get("adir") or {}

    def fix(value):
        if isinstance(value, str) and value and not Path(value).is_absolute() and ":" not in value:
            cand = base / value
            if cand.exists():
                return str(cand.resolve())
        return value
    if isinstance(adir.get("knowledge"), str):
        adir["knowledge"] = fix(adir["knowledge"])
    for key in ("role", "task"):
        block = adir.get(key)
        if isinstance(block, dict):
            for k in ("file", "script", "context"):
                if k in block:
                    block[k] = fix(block[k])
    return doc


def _render_check(run_file: str) -> list:
    """The pins the seed generator refuses as inactive when the run file's
    baseline is rendered (`<name>: inactive (...)` in its message), or an
    empty list when it renders."""
    import re
    from adir.instance import load
    try:
        inst = load(run_file)          # the load elaborates the unit, which is where a fixed inactive pin is refused
        inst.template.seed_generator(inst.ctx(), "baseline")
    except Exception as e:  # noqa: BLE001
        # the seed's `<name>: inactive (...)`, and the loader's `variables.<name>: bound, but inactive under ...`
        return [m.group(1) for m in re.finditer(r"(?:variables\.)?([A-Za-z_][\w.]*): (?:bound, but )?inactive", str(e))]
    return []


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("run_file")
    ap.add_argument("--pdk", default=None, help="the database (default: the run's synthesis nodes' pdk)")
    ap.add_argument("--threshold", type=float, default=0.10, help="a family this far over the limit still stays")
    ap.add_argument("--fraction", type=float, default=1.0, help="the structure's share of the clock")
    ap.add_argument("--out", default=None, help="write the run file with the pruned domains here")
    ap.add_argument("--best", default=None, choices=("delay", "area"),
                    help="fix every structure to the database's best family instead of pruning the domains")
    args = ap.parse_args(argv)
    from adir.instance import load
    inst = load(args.run_file)
    pdk = args.pdk or timing.pdk_of(inst)
    if args.best:
        table, overlay = best_declaration(inst, pdk, args.best)
        print(f"[prune] {pdk}, the database's best family per structure by {args.best}")
        for r in table:
            src = "" if r.get("from_width") == r["width"] else f" (from {r.get('from_width')} bits)"
            print(f"  {r['variable']:44s} {r['width']:4d} bits  {r['family']:30s} "
                  f"{r['delay_ps']:8.0f} ps {(r.get('area_um2') or 0):9.0f} um2{src}")
        print("[prune] overlay:")
        print(yaml.safe_dump(overlay, sort_keys=False).rstrip())
        if args.out:
            # a database row records a component's default pins even where the family it was measured
            # with does not open that component (an unpacker whose stored-subnormal decode has no
            # normalization count still carries lzc.family); the seed refuses such a pin, so the written
            # run file is rendered and the refused pins leave the overlay until it renders
            for _ in range(len(overlay) + 1):
                doc = _absolute_paths(yaml.safe_load(open(args.run_file)), args.run_file)
                vars_ = doc.setdefault("adir", {}).setdefault("variables", {})
                vars_.update(overlay)
                with open(args.out, "w") as fh:
                    fh.write(f"# the database's best structures of {args.run_file} by {args.best}, written by "
                             f"chialu.prune on {pdk}; comments of the source file are not carried over\n")
                    yaml.safe_dump(doc, fh, sort_keys=False)
                refused = [n for n in _render_check(args.out) if n in overlay]
                if not refused:
                    break
                for n in refused:
                    print(f"[prune] {n}: inactive under the chosen families, dropped from the overlay")
                    del overlay[n]
            print(f"[prune] wrote {args.out}")
        return 0
    table, overlay = prune(inst, pdk, args.threshold, args.fraction)
    clock = timing.clock_of(inst)
    print(f"[prune] {pdk}, clock {clock} ps, limit {clock * args.fraction * (1 + args.threshold):.0f} ps "
          f"(fraction {args.fraction}, threshold {args.threshold:.0%})")
    cur = None
    for r in table:
        if r["variable"] != cur:
            cur = r["variable"]
            print(f"  {cur} ({r['width']} bits)")
        d = f"{r['delay_ps']:.0f} ps" if r["delay_ps"] is not None else "not in the database"
        a = f", {r['area_um2']:.0f} um2" if r["area_um2"] is not None else ""
        print(f"    {'keep ' if r['keep'] else 'drop '} {r['family']:38s} {d}{a}"
              + (f" ({r['variant']})" if r["variant"] and r["variant"] != "-" else ""))
    if not overlay:
        print("[prune] every family stays")
    else:
        print("[prune] overlay:")
        print(yaml.safe_dump(overlay, sort_keys=False).rstrip())
    if args.out:
        doc = _absolute_paths(yaml.safe_load(open(args.run_file)), args.run_file)
        vars_ = doc.setdefault("adir", {}).setdefault("variables", {})
        for name, dom in overlay.items():
            vars_[name] = dom
        with open(args.out, "w") as fh:
            fh.write(f"# pruned from {args.run_file} by chialu.prune on {pdk} (threshold {args.threshold}, "
                     f"fraction {args.fraction}); comments of the source file are not carried over\n")
            yaml.safe_dump(doc, fh, sort_keys=False)
        print(f"[prune] wrote {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
