"""The synthesis database as tables: the library families of a structure
kind at the unit's own width (the rows `chialu.synthdb` writes under
chialu/synth/<pdk>/), for the timing section of the prompts
(chialu.prompts: chialu_timing) and the pruning of a run's family
domains (chialu.prune). A width the database lacks is interpolated from
the nearest one on the kind's law, and a structure's components are
summed for the decomposition the timing section shows."""
from __future__ import annotations

import json
import os
from pathlib import Path

DB_DIR = Path(__file__).resolve().parent / "synth"
KINDS = ("adder", "incrementer", "lzc", "shifter", "comparator", "bitcount", "multiplier", "fp_adder",
         "fp_multiplier", "fp_comparator", "rounder", "unpacker")
_CACHE: dict = {}


def load(pdk: str) -> list:
    """The rows of a PDK's database (cached), [] without one."""
    from chialu import synthdb
    d = synthdb.db_dir(pdk)
    legacy = DB_DIR / f"{pdk}.jsonl"
    stamp = tuple(sorted((str(f), f.stat().st_mtime) for f in
                         (list(d.glob("*.jsonl")) + list(d.glob("*/*.jsonl")) if d.is_dir() else [])
                         + ([legacy] if legacy.exists() else [])))
    if stamp not in _CACHE:
        _CACHE.clear()
        rows = synthdb.views(pdk)
        _CACHE[stamp] = [r for r in rows if r["status"] == "ok" and r["delay_ps"] is not None]
    return _CACHE[stamp]


def pdk_of(instance) -> str:
    """The PDK a run synthesizes on: the `pdk` input of its synthesis
    nodes, else CHIALU_PDK, else the one database present, else
    nangate45."""
    graph = getattr(instance, "graph", None)
    for node in (getattr(graph, "nodes", None) or {}).values():
        inputs = getattr(node, "inputs", None) or (node.get("inputs") if isinstance(node, dict) else None) or {}
        v = inputs.get("pdk") if isinstance(inputs, dict) else None
        if isinstance(v, str) and v and not v.startswith(("vars.", "candidate.", "seed.")):
            return v.strip("'\"")
    if os.environ.get("CHIALU_PDK"):
        return os.environ["CHIALU_PDK"]
    dirs = sorted(d.name for d in DB_DIR.glob("*") if d.is_dir()) if DB_DIR.is_dir() else []
    if len(dirs) == 1:
        return dirs[0]
    dbs = sorted(DB_DIR.glob("*.jsonl")) if DB_DIR.is_dir() else []
    return dbs[0].stem if len(dbs) == 1 else "nangate45"


def nearest(rows: list, kind: str, width: int, clock_ps: int | None = None) -> tuple:
    """(the width the rows come from, None): the width itself when the
    database has it, else the nearest one the query interpolates from."""
    ws = sorted({int(r["width"]) for r in rows if r["kind"] == kind})
    if not ws:
        return None, None
    if width in ws:
        return width, None
    return min(ws, key=lambda w: (abs(w - width), w)), None


def table(rows: list, kind: str, width: int, clock_ps: int | None = None) -> list:
    """The rows of a kind at a width, fastest first (a width the database
    lacks is interpolated from the nearest one on the kind's law)."""
    from chialu import synthdb
    sel = [r for r in rows if r["kind"] == kind]
    if not sel:
        return []
    widths = {int(r["width"]) for r in sel}
    if width in widths:
        out = [dict(r, from_width=width) for r in sel if int(r["width"]) == width]
    else:
        src = min(widths, key=lambda w: (abs(w - width), w))
        out = []
        for r in sel:
            if int(r["width"]) != src:
                continue
            f = synthdb._scale(synthdb._law(kind, r["family"]), src, width)
            out.append(dict(r, from_width=src, width=width, delay_ps=(r["delay_ps"] or 0) * f,
                            area_um2=(r.get("area_um2") or 0) * (width / src if src else 1), interpolated=True))
    return sorted(out, key=lambda r: (r["delay_ps"], r.get("area_um2") or 0))


def best(rows: list, kind: str, width: int, clock_ps: int | None = None) -> dict:
    """{family: its fastest row} at a width."""
    out: dict = {}
    for r in table(rows, kind, width, clock_ps):
        if r["family"] not in out:
            out[r["family"]] = r
    return out


def structures_of(instance) -> list:
    """(kind, slot, width, index) of every slotted structure of the
    bound unit whose kind the database covers, one per (kind, width)."""
    manifest = (instance.elaboration.info or {}).get("manifest") or []
    seen, out = set(), []
    for s in manifest:
        kind = s.get("kind")
        slot = s.get("slot") or kind
        if slot not in KINDS or not s.get("width"):
            continue
        key = (slot, int(s["width"]))
        if key in seen:
            continue
        seen.add(key)
        out.append((kind, slot, int(s["width"]), s.get("id")))
    return out


def clock_of(instance) -> int | None:
    b = instance.bindings.get("clock_ps")
    return int(b.value) if b is not None and b.value is not None else None


def render(instance) -> str:
    """The timing section: per structure kind and width of the unit, the
    library families' fastest variant at the run's clock, the delay and
    area from standalone synthesis, and how far over the clock a family
    stands. Empty without a database or a clock."""
    clock = clock_of(instance)
    pdk = pdk_of(instance)
    rows = load(pdk)
    if not rows or clock is None:
        return ""
    least = least_delay(instance)
    if least:
        L = [f"## Library timing on {pdk}", "",
             "Standalone synthesis of the family library's modules (yosys + ABC; chialu/synth), the fastest "
             "variant of each family. A family's delay here is its datapath alone; the unit adds operand "
             "decode, the op mux and the flags. The run maps every design for its least delay, so the "
             "table ranks the families by delay with their area beside it; the Pareto goal weighs both.", ""]
    else:
        L = [f"## Library timing on {pdk} at the run's clock ({clock} ps)", "",
             "Standalone synthesis of the family library's modules (yosys + ABC at the clock as the "
             "delay target; chialu/synth). A family's delay here is its datapath alone; the "
             "unit adds operand decode, the op mux and the flags. A family far over the clock cannot "
             "meet it in any arrangement; one slightly over may, once the synthesizer sees the whole "
             "path, and is worth an attempt. The area is the family's own; the Pareto goal weighs it "
             "at the run's clock.", ""]
    for kind, slot, width, sid in structures_of(instance):
        fams = best(rows, slot, width, clock)
        if not fams:
            continue
        src = {int(r.get("from_width") or width) for r in fams.values()}
        note = "" if src == {width} else f" (measured at {', '.join(str(w) for w in sorted(src))} bits and scaled)"
        L.append(f"* `{slot}` at {width} bits{note}:")
        L.append("")
        if least:
            L.append("  | family | fastest variant | delay ps | area um2 |")
            L.append("  | --- | --- | --- | --- |")
        else:
            L.append("  | family | fastest variant | delay ps | area um2 | vs clock |")
            L.append("  | --- | --- | --- | --- | --- |")
        for fam, r in sorted(fams.items(), key=lambda kv: kv[1]["delay_ps"]):
            row = f"  | {fam} | {r.get('variant', '-')} | {r['delay_ps']:.0f} | {(r.get('area_um2') or 0):.0f} |"
            if not least:
                over = (r["delay_ps"] - clock) / clock
                row += f" {'+' if over > 0 else ''}{over * 100:.0f}% |"
            L.append(row)
        L.append("")
    comp = components_line(rows, instance, clock)
    if comp:
        L += comp + [""]
    return "\n".join(L) if len(L) > 4 else ""


def least_delay(instance) -> bool:
    """A run that maps every design for its least delay: its clock is a target below every design's
    reach (MIN_DELAY_PS of targets/make_targets.py) and no constraint bounds the delay by it."""
    texts = [getattr(c, "text", "") for c in (getattr(instance, "constraints", None) or [])]
    return not any("abc_delay_ps" in t and "<=" in t for t in texts)


def components_line(rows: list, instance, clock: int) -> list:
    """The component kinds a structure instantiates, at the structure's
    width: what the unit's delay is made of (the incrementer of a
    rounding, the leading-zero counter of a normalization, the shifter of
    an alignment), so the reader sees where a path's picoseconds go."""
    parts = []
    for kind, slot, width, _sid in structures_of(instance):
        for comp in ("incrementer", "lzc", "shifter"):
            if comp == slot:
                continue
            b = best(rows, comp, width, clock)
            if not b:
                continue
            fam, r = min(b.items(), key=lambda kv: kv[1]["delay_ps"])
            parts.append((comp, width, fam, r))
        break
    if not parts:
        return []
    L = ["* the component kinds at that width (what a structure's own slots cost):", "",
         "  | component | fastest family | delay ps | area um2 |", "  | --- | --- | --- | --- |"]
    for comp, width, fam, r in parts:
        L.append(f"  | {comp} | {fam} | {r['delay_ps']:.0f} | {(r.get('area_um2') or 0):.0f} |")
    return L
