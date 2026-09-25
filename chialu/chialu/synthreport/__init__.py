"""The synthesis reports a coding agent reads beside the metric: the
critical path cell by cell with the unit instance each cell belongs to,
the latest endpoints, and the area of every unit of the flattened design
(`chialu.eda.synth_ppa` returns them as `summary`, `critical_path`,
`paths` and `area_by_hierarchy`; the run file's `feedback:` carries them
to the prompt, the composer writes the long ones as files of the call
directory).

ABC's mapping drops every hierarchical name (its boundary nets are the
top's ports alone), so the reports come from a second mapping of the
same pre-mapping netlist with `keep` on the unit instances' port nets:
its area and delay stay within a few per cent of the metric (measured on
the host: +0.1 % and +1.9 % on int_subword_alu, +3.2 % and +0.8 % on
fp_alu_cmp), and the header states both. The timing is a static
analysis under ABC's `stime` model (no wire load, the fanout pins'
capacitances as load, inputs at 0 ps, outputs unloaded), which matches
ABC's `Delay =` on the flow's own netlist to the last digit.
"""
from __future__ import annotations

import json
import re
import subprocess
import time
from pathlib import Path

from .liberty import load as load_liberty
from .render import PS, endpoint_line, path_text, tree_text
from .sta import Netlist, Timing, area_tree, boundary_owner, cell_owners, port_dirs

GLOB_CHARS = set("*?[]")
# the listings the node's yosys script writes before ABC, which the second mapping and the attribution read
LISTINGS_BEFORE_SYNTH = "tee -q -o ports_in.txt select -list */i:*\ntee -q -o ports_out.txt select -list */o:*\n"
LISTINGS_AFTER_SYNTH = ("tee -q -o premap_wires.txt select -list w:*\ntee -q -o scopeinfo.txt dump t:$scopeinfo\n"
                        "write_rtlil premap.il\n")


def members_of(rtl) -> dict:
    """{module name: member name} of a multi-file seed (the member
    dictionary ADIR hands the nodes), or from `// ADIR-MEMBER` markers
    of a joined text; {} for a plain text."""
    out: dict = {}
    if isinstance(rtl, dict):
        for member, text in rtl.items():
            for mod in re.findall(r"^\s*module\s+([A-Za-z_]\w*)", str(text), re.M):
                out[mod] = str(member)
        return out
    member = None
    for line in str(rtl or "").splitlines():
        m = re.match(r"\s*//\s*ADIR-MEMBER\s+(\S+)", line)
        if m:
            member = m.group(1)
            continue
        m = re.match(r"\s*module\s+([A-Za-z_]\w*)", line)
        if m and member:
            out[m.group(1)] = member
    return out


def _numbers(log: str) -> dict:
    out = {"area_um2": None, "cells": None, "abc_delay_ps": None}
    m = re.search(r"Chip area for top module.*?:\s*([\d.]+)", log) or re.search(r"Chip area for module.*?:\s*([\d.]+)", log)
    if m:
        out["area_um2"] = float(m.group(1))
    ms = list(re.finditer(r"Number of cells:\s*(\d+)", log)) or \
        list(re.finditer(r"^\s*(\d+)\s+(?:[\d.]+(?:[eE][+-]?\d+)?\s+)?cells\s*$", log, re.M))
    if ms:
        out["cells"] = int(ms[-1].group(1))
    dm = re.findall(r"Delay\s*=\s*([\d.]+)\s*ps", log)
    if dm:
        out["abc_delay_ps"] = float(dm[-1])
    return out


def _scopes_from_dump(text: str) -> dict:
    out, cur = {}, None
    for line in text.splitlines():
        m = re.match(r"\s*cell \$scopeinfo \\?(\S+)", line)
        if m:
            cur = m.group(1)
            continue
        m = re.match(r'\s*attribute \\module "\\\\?([^"]+)"', line)
        if m and cur is not None:
            out[cur] = m.group(1)
    return out


def kept_wires(work: Path, unit_glob: str = "u_*") -> list:
    """The public hierarchical nets one level under a unit instance
    (`u_m0_l0_adder.sum`): the boundary the attribution needs."""
    wires = [ln.split("/", 1)[1] for ln in (work / "premap_wires.txt").read_text().splitlines() if "/" in ln]
    rx = re.compile(r"^(" + "[^.]*".join(re.escape(p) for p in unit_glob.split("*")) + r")\.[^.]+$")
    return [w for w in wires if not w.startswith("$") and rx.match(w) and not (set(w) & GLOB_CHARS)]


def report(work: Path, top: str, lib_path: str, abc_script: Path, members: dict | None = None,
           unit_glob: str = "u_*", top_n: int = 20, full: int = 3, flow: dict | None = None,
           timeout_s: int = 900, clock_ps: int | None = None) -> dict:
    """The reports of a design whose pre-mapping netlist and listings sit
    in `work` (LISTINGS_BEFORE_SYNTH and LISTINGS_AFTER_SYNTH in the
    node's yosys script): {summary, critical_path, paths,
    area_by_hierarchy, numbers, seconds}, or {"error": ...}."""
    t0 = time.time()
    work = Path(work)
    members = members or {}
    keep = kept_wires(work, unit_glob)
    (work / "report_keep.ys").write_text(
        "read_rtlil premap.il\n" + "".join(f"setattr -set keep 1 w:{w}\n" for w in keep)
        + f"write_rtlil report_input.il\nabc -liberty {lib_path} -script {abc_script}\nopt_clean\nstat -liberty {lib_path}\nwrite_json mapped_keep.json\n")
    r = subprocess.run(["yosys", "-q", "-l", "report_keep.log", "report_keep.ys"], cwd=str(work),
                       capture_output=True, text=True, timeout=timeout_s)
    log = (work / "report_keep.log").read_text() if (work / "report_keep.log").is_file() else ""
    if r.returncode != 0 or not (work / "mapped_keep.json").is_file():
        return {"error": f"the name-kept mapping failed: {(r.stderr or log)[-600:]}", "seconds": round(time.time() - t0, 1)}
    nums = _numbers(log)
    lib = load_liberty(lib_path)
    nl = Netlist(str(work / "mapped_keep.json"), lib, top)
    for k, v in _scopes_from_dump((work / "scopeinfo.txt").read_text()).items():
        nl.scopes.setdefault(k, v)
    dirs = port_dirs((work / "ports_in.txt").read_text(), (work / "ports_out.txt").read_text())
    tm = Timing(nl)
    own = cell_owners(nl, boundary_owner(nl, dirs, unit_only=True))
    tree = area_tree(nl, own)
    sta_delay = max((tm.arrival(b)[0] for b in nl.po), default=0.0) * PS
    flow = flow or {}
    head = (f"# {top} at clock {clock_ps} ps on {Path(lib_path).name}\n"
            f"the metric (synth_ppa, per-metric median of {flow.get('repeats', 1)}; "
            f"cells from run {flow.get('cells_run_index', 0)}): area {flow.get('area_um2')} um2, {flow.get('cells')} cells, "
            f"ABC delay {flow.get('abc_delay_ps')} ps\n"
            f"these reports (the same netlist mapped with `keep` on {len(keep)} unit port nets, so cells keep an owner): "
            f"area {nums.get('area_um2')} um2, {nums.get('cells')} cells, ABC delay {nums.get('abc_delay_ps')} ps, "
            f"this timing analysis {sta_delay:.1f} ps; the numbers differ from the metric by a few per cent\n")
    # the unit table
    units = sorted((p for p in tree if p and "." not in p), key=lambda p: -tree[p]["area"])
    total = nl.area()
    unit_ports = {p: ([], []) for p in units}
    for b, cands in nl.names.items():
        for hid, n, _i, _w in cands:
            if hid or n.count(".") != 1:
                continue
            inst, port = n.split(".", 1)
            if inst not in unit_ports:
                continue
            d = (dirs.get(nl.scopes.get(inst, "")) or {}).get(port.split("$")[0])
            if d == "input":
                unit_ports[inst][0].append(b)
            elif d == "output":
                unit_ports[inst][1].append(b)
    S = [head, "## Units of the flattened design (shared = logic ABC merged between instances, split equally)",
         f"{'instance':<26} {'module':<34} {'member':<20} {'area um2':>9} {'%':>6} {'cells':>7} {'shared':>7} {'in arr':>7} {'out arr':>8}"]
    for p in units:
        ins, outs = unit_ports[p]
        ain = max((tm.arrival(b)[0] for b in ins), default=0.0) * PS
        aout = max((tm.arrival(b)[0] for b in outs), default=0.0) * PS
        mod = nl.scopes.get(p, "")
        S.append(f"{p:<26} {mod[:34]:<34} {members.get(mod, '-')[:20]:<20} {tree[p]['area']:9.1f} "
                 f"{100 * tree[p]['area'] / total if total else 0:6.1f} {tree[p]['cells']:7.0f} {tree[p]['shared_cells']:7.0f} "
                 f"{ain:7.0f} {aout:8.0f}")
    glue = tree[""]["area"] - sum(tree[p]["area"] for p in units)
    S.append(f"{'top glue (operand decode, the op mux, the flags)':<82} {glue:9.1f} {100 * glue / total if total else 0:6.1f}")
    S.append(f"{'total':<82} {total:9.1f}")
    S.append("in arr / out arr: the latest arrival (ps) at the unit's input / output port nets; a unit whose out arr "
             "is near the total is on the critical path, one whose in arr is late waits for another unit")
    paths = tm.endpoint_paths(top_n)
    crit_line = ""
    if paths:
        arr, b, _e, steps = paths[0]
        crit_line = endpoint_line(nl, own, 1, arr, b, steps).strip()
    P = [head, f"## The {len(paths)} latest endpoints; owner(cells, ps) per segment of the path", ""]
    for i, (arr, b, _e, steps) in enumerate(paths, 1):
        P.append(endpoint_line(nl, own, i, arr, b, steps))
    P.append("")
    P.append(f"## The first {min(full, len(paths))} of them cell by cell")
    for i, (arr, b, _e, steps) in enumerate(paths[:full], 1):
        P.append(path_text(nl, tm, own, steps, f"### {i}. {nl.name(b)} at {arr * PS:.1f} ps"))
    A = [head]
    A += tree_text(tree, nl.scopes, total, f"## Area per instance of the flattened design (cells shared between "
                                          f"instances split equally; total {total:.1f} um2)")
    A += ["", "## Structure members -> modules -> instances", f"{'member':<24} {'module':<40} {'instances':<30} {'area':>9}"]
    by_member: dict = {}
    for inst, mod in sorted(nl.scopes.items()):
        mem = members.get(mod)
        if mem:
            by_member.setdefault((mem, mod), []).append(inst)
    for (mem, mod), insts in sorted(by_member.items()):
        fa = sum(tree.get(i, {}).get("area", 0.0) for i in insts)
        if fa:
            A.append(f"{mem:<24} {mod[:40]:<40} {', '.join(insts)[:30]:<30} {fa:9.1f}")
    return {"summary": "\n".join(S) + "\n", "critical_path": crit_line[:400], "paths": "\n".join(P) + "\n",
            "area_by_hierarchy": "\n".join(A) + "\n", "numbers": {**nums, "sta_delay_ps": round(sta_delay, 2)},
            "seconds": round(time.time() - t0, 1)}
