"""Where a unit's delay goes: the cut synthesis of a seed's top module.

A cut is the top module with its outputs demoted to internal wires and
one new output driven by the wire being cut, so synthesis keeps the cone
feeding that wire alone and the mapper's delay is the depth of that
point. The profile is every top-level wire's cut, the dataflow between
those wires, and the increment a stage adds over the deepest wire it
reads. The whole top and every structure module alone are measured with
the same flow, so a stage's cost stands beside the structure's own.

    python3 -m chialu.profile --target targets/fp_alu.yaml --pdk nangate45
    python3 -m chialu.profile --rtl seed.sv --top alu_core --clock 2000
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CUT_PORT = "cut_o"

_MODULE_RE = re.compile(r"^module\s+(\w+)\s*(?:#\s*\(.*?\))?\s*\((.*?)\)\s*;", re.S | re.M)
_DECL_RE = re.compile(r"^[ \t]*(?:wire|logic|reg)[ \t]+(signed[ \t]+)?(\[[^\]]*\][ \t]*)?([A-Za-z_]\w*)[ \t]*;", re.M)
_PORT_RE = re.compile(r"\b(input|output|inout)\b[ \t]*(?:wire|logic|reg)?[ \t]*(signed[ \t]+)?(\[[^\]]*\])?[ \t]*([A-Za-z_]\w*)")
_ID_RE = re.compile(r"(?<![\w'])([A-Za-z_]\w*)")
_KEYWORDS = {"begin", "end", "if", "else", "case", "endcase", "default", "for", "while", "assign", "always",
             "always_comb", "always_ff", "always_latch", "posedge", "negedge", "or", "and", "not", "xor",
             "unique", "priority", "casez", "casex", "signed", "unsigned", "logic", "wire", "reg", "int",
             "integer", "localparam", "parameter", "function", "endfunction", "return", "automatic", "void",
             "input", "output", "inout", "module", "endmodule", "generate", "endgenerate", "genvar", "bit"}


# ---- the seed -----------------------------------------------------------------------------
def instance_of(target: Path):
    """(the run file's instance, the normalized spec of its unit)."""
    import tempfile
    from adir.instance import load
    inst = load(str(target), run_dir_override=tempfile.mkdtemp(prefix="chialu_profile_"))
    info = inst.elaboration.info
    spec = dict(info["spec"])
    spec["dut_name"] = info["top"]
    unit = spec.get("unit")
    if unit == "alu":
        from chialu.verify.alu_ref import normalize_spec
        spec = normalize_spec(spec)
    elif unit == "vec_dot_acc":
        from chialu.verify.dot_ref import normalize_dot_spec
        spec = normalize_dot_spec(spec)
    elif unit == "vec_sfu":
        from chialu.verify.sfu_ref import normalize_sfu_spec
        spec = normalize_sfu_spec(spec)
    return inst, spec


def seed_of(target: Path) -> tuple:
    """(the seed's text, its top module, its spec) of a run file."""
    from chialu.targets import derive
    inst, spec = instance_of(target)
    return derive.seed_for(spec), inst.elaboration.info["top"], spec


def seed_units(target: Path) -> dict:
    """{unit module: {"kind", "family", "wires"}} for the units of an ALU
    run file's baseline seed: the module realizing one physical
    structure or a shared group, the family declared for its first
    structure (the instance's defaults, which is what the baseline seed
    is rendered at), and the unit's result buses in the top
    (`y_m<mode>_<unit>`), which a glue profile cuts. `context_factors`
    reads it to price a row in place. {} for a unit class other than the
    ALU, whose seed has no structure modules."""
    from chialu.modules.generators import families_of
    from chialu.targets import derive
    from chialu.targets.rtl.alu_seed import sv_ident
    from chialu.targets.rtl.structures import is_inline
    inst, spec = instance_of(target)
    if spec.get("unit") != "alu":
        return {}
    from chialu.targets.rtl.alu_seed import structure_manifest
    families = families_of(inst.ctx(), structure_manifest(spec))
    seed = derive.seed_alu_text(spec, families=families)
    manifest = seed.structures
    top = spec.get("dut_name", "alu_core")
    m, b0, b1 = module_span(seed.text, top)
    declared = [n for n, _r in wires_of(seed.text[b0:b1])]
    out: dict = {}
    for u in seed.units:
        first = next((manifest.get(x) for x in u.members
                      if manifest.get(x) is not None and manifest.get(x).slot
                      and not is_inline(manifest.get(x))), None)
        if first is None:
            continue
        fam = families.get(f"core.{first.slot}.{first.index}")
        fam = (fam[0] if isinstance(fam, tuple) else fam)
        # every bus the unit drives, whatever the kind writes (`y_`, `d_` and `fl_` for a unit with
        # a result, the unpacker's `xa_`/`xb_`/`den_` buses): the top declares one per (mode, unit)
        buses = {f"m{mi}_{sv_ident(u.name)}" for mi in u.modes(manifest)}
        out[u.module] = {"kind": u.kind, "family": getattr(fam, "name", fam) or "default",
                         "wires": [w for w in declared if any(w.endswith("_" + b) for b in buses)]}
    return out


# ---- the top module's shape ---------------------------------------------------------------
def module_span(text: str, name: str) -> tuple:
    """(the header match, the body's start, the body's end) of a module."""
    for m in _MODULE_RE.finditer(text):
        if m.group(1) == name:
            end = text.find("\nendmodule", m.end())
            return m, m.end(), (end if end >= 0 else len(text))
    raise KeyError(f"module {name} not found")


def ports_of(header: str) -> list:
    """[(direction, the range text, the name)] of an ANSI port header."""
    out, last = [], "input"
    for m in _PORT_RE.finditer(header):
        last = m.group(1)
        out.append((last, (m.group(3) or "").strip(), m.group(4)))
    return out


def wires_of(body: str) -> list:
    """[(name, the range text)] of the module's own declarations."""
    return [(m.group(3), (m.group(2) or "").strip()) for m in _DECL_RE.finditer(body)]


def port_dirs(text: str) -> dict:
    """{module: {port: direction}} of every module of the program."""
    out = {}
    for m in _MODULE_RE.finditer(text):
        out[m.group(1)] = {name: d for d, _r, name in ports_of(m.group(2))}
    return out


# ---- the dataflow between the top's own wires -----------------------------------------------
def _ids(expr: str) -> set:
    return {i for i in _ID_RE.findall(expr) if i not in _KEYWORDS}


def _blocks(body: str) -> list:
    """(the driven names, the read names) of every top-level statement:
    a continuous assignment, a procedural block, or an instance."""
    out = []
    i, n = 0, len(body)
    while i < n:
        m = re.compile(r"\bassign\b|\balways(?:_comb|_ff|_latch)?\b|^[ \t]*([A-Za-z_]\w*)[ \t]+([A-Za-z_]\w*)[ \t]*\(",
                       re.M).search(body, i)
        if m is None:
            break
        if m.group(0).startswith("assign"):
            end = body.find(";", m.end())
            stmt = body[m.end():end if end > 0 else n]
            lhs, _, rhs = stmt.partition("=")
            out.append((_ids(lhs), _ids(rhs)))
            i = (end + 1) if end > 0 else n
        elif m.group(0).startswith("always"):
            start = body.find("begin", m.end())
            if start < 0:                                    # a one-statement block
                end = body.find(";", m.end())
                stmt = body[m.end():end if end > 0 else n]
                lhs, _, rhs = stmt.partition("=")
                out.append((_ids(lhs), _ids(rhs)))
                i = (end + 1) if end > 0 else n
                continue
            depth, j = 0, start
            while j < n:
                w = re.compile(r"\b(begin|end)\b").search(body, j)
                if w is None:
                    j = n
                    break
                depth += 1 if w.group(1) == "begin" else -1
                j = w.end()
                if depth == 0:
                    break
            stmt = body[start:j]
            driven = set()
            for a in re.finditer(r"([A-Za-z_]\w*)\s*(?:\[[^\];]*\])?\s*(?:<=|=)(?!=)", stmt):
                driven.add(a.group(1))
            out.append((driven, _ids(stmt) - driven))
            i = j
        else:                                                # an instance
            end = body.find(");", m.end())
            conns = body[m.end():end if end > 0 else n]
            out.append(("instance", m.group(1), conns))
            i = (end + 2) if end > 0 else n
    return out


def dataflow(text: str, top: str) -> dict:
    """{wire: the top's wires its driver reads}: the sources of every
    wire the top drives, from the continuous assignments, the procedural
    blocks and the instance connections."""
    m, b0, b1 = module_span(text, top)
    body = text[b0:b1]
    dirs = port_dirs(text)
    names = {w for w, _r in wires_of(body)} | {p for _d, _r, p in ports_of(m.group(2))}
    src: dict = {}
    for st in _blocks(body):
        if st and st[0] == "instance":
            _tag, mod, conns = st
            pd = dirs.get(mod) or {}
            driven, read = set(), set()
            for c in re.finditer(r"\.(\w+)\s*\(([^()]*(?:\([^()]*\)[^()]*)*)\)", conns):
                side = driven if pd.get(c.group(1)) == "output" else read
                side |= _ids(c.group(2)) & names
            for w in driven & names:
                src.setdefault(w, set()).update(read & names)
        else:
            driven, read = st
            for w in driven & names:
                src.setdefault(w, set()).update(read & names)
    return {w: sorted(s - {w}) for w, s in src.items()}


# ---- the cut ---------------------------------------------------------------------------------
def cut_text(text: str, top: str, wire: str, rng: str) -> str:
    """The program with the top module cut at a wire: the inputs stay,
    the outputs become internal declarations, and the only output is the
    cut wire."""
    m, b0, b1 = module_span(text, top)
    ports = ports_of(m.group(2))
    keep = [f"  input {r} {n}" if r else f"  input {n}" for d, r, n in ports if d == "input"]
    demoted = "".join(f"  logic {r} {n};\n" if r else f"  logic {n};\n" for d, r, n in ports if d != "input")
    head = f"module {top} (\n" + ",\n".join(keep + [f"  output {rng} {CUT_PORT}" if rng else f"  output {CUT_PORT}"]) + "\n);\n"
    body = demoted + text[b0:b1] + f"\n  assign {CUT_PORT} = {wire};\n"
    return text[:m.start()] + head + body + "\nendmodule" + text[b1 + len("\nendmodule"):]


def _bits(rng: str) -> int:
    mm = re.match(r"\[\s*(\d+)\s*:\s*(\d+)\s*\]", rng or "")
    return abs(int(mm.group(1)) - int(mm.group(2))) + 1 if mm else 1


# ---- the measurement --------------------------------------------------------------------------
def measure(rtl: str, top: str, pdk, clock_ps: int, effort: str, timeout_s: int, repeats: int = 5) -> dict:
    """The mapped delay and area of a program's top module. A cone that
    maps to no library cell is a constant, which the flow reports as a
    missing area line; it is recorded as a zero-delay cut rather than as
    a failure."""
    from chialu import eda
    from chialu.synth_records import trace
    from adir.registry import underlying
    r = underlying(eda.synth_ppa)(rtl, top, pdk, clock_ps, timeout_s=timeout_s, effort=effort, repeats=repeats, report=False)
    if not r.get("ok") and "no area in the yosys log" in (r.get("detail") or ""):
        return {**trace(r), "ok": True, "delay_ps": 0.0, "area_um2": 0.0, "cells": 0, "seconds": r.get("seconds"),
                "detail": "constant (the cone maps to no cell)"}
    from chialu.synth_records import trace
    return {**trace(r), "ok": bool(r.get("ok")), "delay_ps": r.get("abc_delay_ps"), "area_um2": r.get("area_um2"),
            "cells": r.get("cells"), "seconds": r.get("seconds"), "detail": (r.get("detail") or "")[:200]}


def profile(text: str, top: str, pdk_name: str, clock_ps: int, effort: str = "medium", jobs: int = 8,
            timeout_s: int = 1800, pattern: str | None = None, modules: bool = True, repeats: int = 5) -> dict:
    """The cut of every top-level wire, the whole top, and every
    structure module alone."""
    m, b0, b1 = module_span(text, top)
    body = text[b0:b1]
    decls = wires_of(body)
    seen_n: dict = {}
    for n, _r in decls:
        seen_n[n] = seen_n.get(n, 0) + 1
    ambiguous = sorted(n for n, c in seen_n.items() if c > 1)
    if ambiguous:                                        # a name declared in a nested scope as well
        print(f"[profile] {len(ambiguous)} names are declared more than once and are not cut: "
              f"{', '.join(ambiguous[:12])}", flush=True)
    cuts = [(n, r) for n, r in decls if seen_n[n] == 1]
    cuts += [(n, r) for d, r, n in ports_of(m.group(2)) if d != "input"]
    if pattern:
        rx = re.compile(pattern)
        cuts = [c for c in cuts if rx.search(c[0])]
    flow = dataflow(text, top)
    t0 = time.time()

    def one_cut(c):
        name, rng = c
        return name, measure(cut_text(text, top, name, rng), top, pdk_name, clock_ps, effort, timeout_s, repeats)

    rows: dict = {}
    with ThreadPoolExecutor(max_workers=jobs) as pool:
        for name, r in pool.map(one_cut, cuts):
            rows[name] = dict(r, wire=name, bits=_bits(dict(cuts).get(name, "")), sources=flow.get(name, []))
            print(f"  cut {name:44s} {('%8.0f ps' % r['delay_ps']) if r['delay_ps'] is not None else 'FAIL':>12s} "
                  f"{(r['area_um2'] or 0):9.0f} um2  {r['seconds']:5.1f}s", flush=True)
    whole = measure(text, top, pdk_name, clock_ps, effort, timeout_s, repeats)
    mods: dict = {}
    if modules:
        names = [mm.group(1) for mm in _MODULE_RE.finditer(text) if mm.group(1) != top]

        def one_mod(name):
            return name, measure(text, name, pdk_name, clock_ps, effort, timeout_s, repeats)
        with ThreadPoolExecutor(max_workers=jobs) as pool:
            for name, r in pool.map(one_mod, names):
                mods[name] = r
    # the increment a stage adds over the deepest wire its driver reads
    for name, r in rows.items():
        srcs = [rows[s]["delay_ps"] for s in r["sources"] if rows.get(s, {}).get("delay_ps") is not None]
        r["from_ps"] = max(srcs) if srcs else 0.0
        r["stage_ps"] = (r["delay_ps"] - r["from_ps"]) if r["delay_ps"] is not None else None
    return {"top": top, "pdk": pdk_name, "clock_ps": clock_ps, "effort": effort, "whole": whole,
            "cuts": rows, "modules": mods, "seconds": round(time.time() - t0, 1)}


# ---- the glue the top adds around the structures ----------------------------------------------
# the wires a glue measurement cuts: the unit buses of every mode (`y_m0_m0_l0_fp_adder`), the mode
# buses they are ORed into (`y_m0`, `fl_m0`, `d_m0`) and the unit's outputs (`y`, `d`, `flags`)
GLUE_PATTERN = r"^(y|d|flags)$|^(y|d|fl|x|xa|xb|xd)_m\d+"
_MODE_BUS = re.compile(r"^(y|d|fl)_m(\d+)$")


def glue_of(p: dict) -> dict:
    """What the top adds around the structures, from a profile of a
    rendered seed: per mode the OR of its units' result buses (the mode
    bus's cut above the deepest unit bus it reads), and once for the
    unit the mode mux and the flag map (an output's cut above the
    deepest mode bus). A structure estimate sums the rows of the
    structures alone, so this is what it does not carry; it is the
    unit's, not a candidate's, and the same for every declaration of a
    target. {"mode": {mode: ps}, "top": ps, "outputs": {...}}."""
    cuts = {k: v for k, v in (p.get("cuts") or {}).items() if v.get("delay_ps") is not None}

    def cut(name):
        r = cuts.get(name)
        return float(r["delay_ps"]) if r else None

    per_mode: dict = {}
    mode_buses: dict = {}
    for name, row in cuts.items():
        m = _MODE_BUS.match(name)
        if not m:
            continue
        mode = int(m.group(2))
        mode_buses.setdefault(mode, []).append(name)
        sources = [cut(s) for s in (row.get("sources") or []) if cut(s) is not None]
        if not sources:
            continue                                    # a mode with one unit assigns its bus through
        per_mode[mode] = max(per_mode.get(mode, 0.0), max(0.0, float(row["delay_ps"]) - max(sources)))
    deepest_mode = max((cut(b) for bs in mode_buses.values() for b in bs if cut(b) is not None), default=None)
    outputs = {n: cut(n) for n in ("y", "d", "flags") if cut(n) is not None}
    top = 0.0
    if deepest_mode is not None and outputs:
        top = max(0.0, max(outputs.values()) - deepest_mode)
    return {"mode": {str(k): round(v, 1) for k, v in sorted(per_mode.items())}, "top": round(top, 1),
            "outputs": {k: round(v, 1) for k, v in outputs.items()},
            "deepest_mode_bus_ps": None if deepest_mode is None else round(deepest_mode, 1)}


def context_factors(p: dict, units: dict) -> dict:
    """{"kind/family": factor} from a profile of a rendered seed: per unit
    module the increment its output buses add over the wires their
    drivers read (its delay in context, where the mapper saw when its
    inputs arrive and what its result feeds) against the same module
    synthesized alone, which is what a database row is. `units` is
    {module: {"kind", "family", "wires": [the module's buses in the
    top]}}. A factor below one says the unit overlaps its producer,
    above one that the row understates it in place; the mean over the
    units of one (kind, family)."""
    cuts = {k: v for k, v in (p.get("cuts") or {}).items() if v.get("stage_ps") is not None}
    mods = p.get("modules") or {}
    acc: dict = {}
    for module, info in units.items():
        alone = (mods.get(module) or {}).get("delay_ps")
        incs = [cuts[w]["stage_ps"] for w in (info.get("wires") or []) if w in cuts]
        if not alone or not incs:
            continue
        key = f"{info['kind']}/{info['family']}"
        e = acc.setdefault(key, [0.0, 0])
        e[0] += max(MIN_FACTOR, max(incs) / float(alone))
        e[1] += 1
    return {k: round(v[0] / v[1], 4) for k, v in acc.items() if v[1]}


# a unit whose cut is shallower than this fraction of its standalone delay is overlapped so far that the
# measurement is more likely a cut that did not keep the unit's cone; the factor stops there
MIN_FACTOR = 0.05


def measure_glue(text: str, top: str, pdk_name: str, clock_ps: int, effort: str = "medium", jobs: int = 8,
                 timeout_s: int = 1800, units: dict | None = None, repeats: int = 5) -> dict:
    """The glue of a seed text: one cut per bus of `GLUE_PATTERN`. With
    `units` ({module: {"kind", "family", "wires"}}) every unit module is
    measured alone as well and the context factors come back beside the
    glue. Raises what the flow raises when the tools are absent, which
    the caller reports."""
    p = profile(text, top, pdk_name, clock_ps, effort, jobs, timeout_s, GLUE_PATTERN, bool(units), repeats)
    g = glue_of(p)
    g["synthesis_profile"] = p
    g["whole_ps"] = (p.get("whole") or {}).get("delay_ps")
    g["cuts"] = len(p.get("cuts") or {})
    if units:
        wired = {m: dict(i, wires=[w for w in (p.get("cuts") or {}) if w in set(i.get("wires") or [])])
                 for m, i in units.items()}
        g["factors"] = context_factors(p, wired)
        g["modules"] = {m: (p.get("modules") or {}).get(m, {}).get("delay_ps") for m in units}
    return g


def render(p: dict, show: int = 24) -> str:
    L = [f"# {p['top']} on {p['pdk']} at {p['clock_ps']} ps ({p['effort']} effort)", "",
         f"whole top: {p['whole']['delay_ps']:.0f} ps, {p['whole']['area_um2']:.0f} um2, "
         f"{p['whole']['cells']} cells" if p["whole"]["ok"] else f"whole top: FAILED ({p['whole']['detail']})", ""]
    rows = [r for r in p["cuts"].values() if r["delay_ps"] is not None]
    L += ["Each cut is mapped on its own, so its delay is the depth of that point under a mapper",
          "that saw only its cone. The cuts order the stages against each other; they do not add up",
          "to the whole top, and a cut can stand above it. The increment is measured over the wires",
          "the driver reads, so a wire driven by one procedural block that reads the module's inputs",
          "shows the whole cone as its increment rather than one stage.", "",
          "## The deepest cuts", "",
          f"  {'wire':44s} {'bits':>4s} {'delay ps':>9s} {'from ps':>8s} {'stage ps':>9s} {'area um2':>9s}"]
    for r in sorted(rows, key=lambda r: -r["delay_ps"])[:show]:
        L.append(f"  {r['wire']:44s} {r['bits']:4d} {r['delay_ps']:9.0f} {r['from_ps']:8.0f} "
                 f"{(r['stage_ps'] or 0):9.0f} {(r['area_um2'] or 0):9.0f}")
    L += ["", "## The stages that add the most", "",
          f"  {'wire':44s} {'stage ps':>9s} {'reads':s}"]
    for r in sorted(rows, key=lambda r: -(r["stage_ps"] or 0))[:show]:
        L.append(f"  {r['wire']:44s} {(r['stage_ps'] or 0):9.0f} {', '.join(r['sources'][:4]) or '-'}")
    if p["modules"]:
        L += ["", "## Every structure module alone", "",
              f"  {'module':44s} {'delay ps':>9s} {'area um2':>9s}"]
        for name, r in sorted(p["modules"].items(), key=lambda kv: -(kv[1]["delay_ps"] or 0)):
            L.append(f"  {name:44s} {(r['delay_ps'] or 0):9.0f} {(r['area_um2'] or 0):9.0f}")
    fails = [r for r in p["cuts"].values() if r["delay_ps"] is None]
    if fails:
        L += ["", f"## {len(fails)} cuts failed", ""] + [f"  {r['wire']}: {r['detail']}" for r in fails[:10]]
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python3 -m chialu.profile", description=__doc__.split("\n\n")[0])
    ap.add_argument("--target", default=None, help="a run file under targets/")
    ap.add_argument("--rtl", default=None, help="a seed file instead of a run file")
    ap.add_argument("--top", default=None, help="the top module (with --rtl)")
    ap.add_argument("--pdk", default="nangate45")
    ap.add_argument("--clock", type=int, default=None, help="ABC's delay target (default: the run file's clock_ps)")
    ap.add_argument("--synth-repeats", type=int, default=5)
    ap.add_argument("--effort", default="medium", choices=("low", "medium", "high"))
    ap.add_argument("--jobs", type=int, default=max(2, (os.cpu_count() or 4) - 2))
    ap.add_argument("--timeout", type=int, default=1800)
    ap.add_argument("--wires", default=None, help="a regular expression selecting the cut wires")
    ap.add_argument("--no-modules", action="store_true", help="skip the per-module runs")
    ap.add_argument("--factors", action="store_true",
                    help="also print what each (kind, family) costs in place against its own module "
                         "(the estimate's context factors; needs --target and the per-module runs)")
    ap.add_argument("--json", default=None, help="write the profile as JSON")
    ap.add_argument("--out", default=None, help="write the table to a file as well")
    a = ap.parse_args(list(sys.argv[1:] if argv is None else argv))
    if a.factors and (not a.target or a.no_modules):
        print("[profile] --factors needs --target and the per-module runs")
        return 2
    clock = a.clock
    if a.rtl:
        text, top = Path(a.rtl).read_text(), a.top
        if not top:
            print("[profile] --rtl needs --top")
            return 2
    elif a.target:
        text, top, _spec = seed_of(Path(a.target))
        if clock is None:
            import yaml
            y = yaml.safe_load(Path(a.target).read_text())
            v = ((y.get("adir") or {}).get("variables") or {}).get("clock_ps") or {}
            clock = int(v.get("fixed") or 2000)
    else:
        print("[profile] --target or --rtl is required")
        return 2
    clock = clock or 2000
    print(f"[profile] {top} on {a.pdk} at {clock} ps, {a.jobs} jobs", flush=True)
    p = profile(text, top, a.pdk, clock, a.effort, a.jobs, a.timeout, a.wires, not a.no_modules, a.synth_repeats)
    out = render(p)
    if a.factors:
        f = context_factors(p, seed_units(Path(a.target)))
        p["factors"] = f
        out += ("\n\n## What a (kind, family) costs in place against its own module\n\n"
                + "\n".join(f"  {k:46s} {v}" for k, v in sorted(f.items())))
    print(out)
    if a.json:
        Path(a.json).write_text(json.dumps(p, indent=1))
    if a.out:
        Path(a.out).write_text(out + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
