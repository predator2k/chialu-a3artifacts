"""chirecipe's CHIA nodes: the recipe run (yosys under the candidate's
script), the equivalence of the mapped netlist against the RTL, the
timing of the mapped netlist, and the recipe renderer of the grid
template. The PDK descriptors and the liberty files come from chiALU."""
from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from adir import node
from chialu.eda import _pdk, _sv2v, liberty_files

FORBIDDEN = ("exec", "!", "shell", "script", "tcl", "plugin", "tee", "write_", "dump", "log",
             "history", "cd", "read_", "include")
ABC_FAMILIES = {
    "none": "",
    "resyn2": "balance;rewrite;refactor;balance;rewrite;rewrite,-z;balance;refactor,-z;rewrite,-z;balance;",
    "compress2rs": "balance,-l;resub,-K,6,-l;rewrite,-l;resub,-K,6,-N,2,-l;refactor,-l;resub,-K,8,-l;"
                   "balance,-l;resub,-K,8,-N,2,-l;rewrite,-l;resub,-K,10,-l;rewrite,-z,-l;"
                   "resub,-K,10,-N,2,-l;balance,-l;resub,-K,12,-l;refactor,-z,-l;resub,-K,12,-N,2,-l;"
                   "rewrite,-z,-l;balance,-l;",
    "dch": "&get,-n;&dc2;&put;",
}
MAP_EFFORT = {1: "&get,-n;&nf,-D,{clock_ps}", 2: "&get,-n;&nf,-C,32,-F,8,-p,-D,{clock_ps}",
              3: "&get,-n;&dch,-f;&nf,-C,32,-F,8,-p,-D,{clock_ps}"}


def _abc_binary() -> str:
    yosys = shutil.which("yosys") or "yosys"
    for cand in (shutil.which("yosys-abc"), str(Path(yosys).resolve().with_name("yosys-abc"))):
        if cand and Path(cand).is_file():
            return cand
    return "yosys-abc"


def check_recipe(recipe: str) -> str:
    """The reason a recipe is refused, or ''. The script may only read
    the RTL and the liberty file through their placeholders."""
    for ln in recipe.splitlines():
        s = ln.strip()
        if not s or s.startswith("#"):
            continue
        head = s.split()[0]
        if head in ("read_verilog", "read_liberty"):
            if "{rtl}" not in s and "{liberty}" not in s:
                return f"a read of something other than {{rtl}} or {{liberty}}: {s[:80]}"
            continue
        if head.startswith(FORBIDDEN) or head in FORBIDDEN or "/" in s:
            return f"a command the recipe may not use: {s[:80]}"
    if "{rtl}" not in recipe or "{top}" not in recipe:
        return "the recipe must read {rtl} and name {top}"
    return ""


def pass_trace(log: str, limit: int = 80) -> str:
    """The passes the run executed in order, each with the cell count
    where the log reports one after it."""
    out, last = [], None
    for ln in log.splitlines():
        m = re.match(r"^\d+(?:\.\d+)*\. Executing (\S+) pass", ln)
        if m:
            name = m.group(1)
            if name != last:
                out.append(name)
                last = name
            continue
        m = re.search(r"ABC RESULTS:\s+internal signals:\s+(\d+)|Number of cells:\s+(\d+)", ln)
        if m and out:
            out[-1] = f"{out[-1]}[{m.group(1) or m.group(2)}]"
    return " > ".join(out[-limit:])


@node(outputs=["ok", "area_um2", "cells", "abc_delay_ps", "seconds", "netlist", "detail", "pass_trace"],
      resources={"eda": 1.0})
def synth_recipe(recipe: str, rtl: str, top: str, pdk, clock_ps: int, timeout_s: int = 600) -> dict:
    """Yosys under the candidate's script. `{rtl}`, `{liberty}`, `{top}`
    and `{clock_ps}` are substituted; `opt_clean`, the liberty
    statistics and the netlist write are appended, so the area, the
    cell count and the netlist come from the script's own run."""
    t0 = time.time()
    bad = check_recipe(recipe)
    if bad:
        return {"ok": False, "detail": f"recipe refused: {bad}", "seconds": 0.0}
    pdk = _pdk(pdk)
    lib = liberty_files(pdk)[0]
    with tempfile.TemporaryDirectory() as td:
        rtl_path, err = _sv2v(rtl, td)
        if rtl_path is None:
            return {"ok": False, "detail": f"sv2v: {err}", "seconds": round(time.time() - t0, 1)}
        net = Path(td) / "net.v"
        script = (recipe.replace("{rtl}", str(rtl_path)).replace("{liberty}", lib)
                  .replace("{top}", top).replace("{clock_ps}", str(int(clock_ps))))
        script += f"\nopt_clean\nstat -liberty {lib}\nwrite_verilog -noattr {net}\n"
        ys = Path(td) / "recipe.ys"
        ys.write_text(script)
        logp = Path(td) / "yosys.log"
        try:
            r = subprocess.run(["yosys", "-q", "-l", str(logp), str(ys)], capture_output=True,
                               text=True, timeout=timeout_s, cwd=td)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": f"yosys timeout after {timeout_s}s",
                    "seconds": round(time.time() - t0, 1)}
        log = logp.read_text() if logp.exists() else ""
        trace = pass_trace(log)
        if r.returncode != 0 or not net.is_file():
            return {"ok": False, "detail": (r.stderr or log)[-3000:], "pass_trace": trace,
                    "seconds": round(time.time() - t0, 1)}
        netlist = net.read_text()
    area = cells = delay = None
    m = re.search(r"Chip area for (?:top )?module.*?:\s*([\d.]+)", log)
    if m:
        area = float(m.group(1))
    m = re.search(r"Number of cells:\s*(\d+)", log)
    if m:
        cells = int(m.group(1))
    dm = re.findall(r"Delay\s*=\s*([\d.]+)\s*ps", log)
    if dm:
        delay = float(dm[-1])
    if len(re.findall(r"Chip area for module", log)) > 1:
        return {"ok": False, "detail": "the recipe left a module hierarchy (no flatten)",
                "pass_trace": trace, "seconds": round(time.time() - t0, 1)}
    return {"ok": area is not None, "area_um2": area, "cells": cells, "abc_delay_ps": delay,
            "seconds": round(time.time() - t0, 1), "netlist": netlist, "pass_trace": trace,
            "detail": "" if area is not None else "no liberty area in the log"}


ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _yosys(script: str, td: str, timeout_s: int):
    ys = Path(td) / f"s{abs(hash(script)) % 10**8}.ys"
    ys.write_text(script)
    return subprocess.run(["yosys", "-q", str(ys)], capture_output=True, text=True,
                          timeout=timeout_s, cwd=td)


@node(outputs=["pass", "detail", "seconds"], resources={"eda": 1.0})
def equiv_netlist(netlist: str, rtl: str, top: str, pdk, timeout_s: int = 300) -> dict:
    """Combinational equivalence of the mapped netlist against the RTL:
    both become AIG-level BLIF in yosys (the netlist's cells read from
    the liberty file with their functions, then flattened) and ABC's
    `cec` proves them equal by SAT sweeping. pass True/False, or None
    when undecided within the timeout."""
    t0 = time.time()
    pdk = _pdk(pdk)
    lib = liberty_files(pdk)[0]
    with tempfile.TemporaryDirectory() as td:
        rtl_path, err = _sv2v(rtl, td)
        if rtl_path is None:
            return {"pass": None, "detail": f"sv2v: {err}"}
        net = Path(td) / "net.v"
        net.write_text(netlist)
        lower = "proc; flatten; opt_clean; techmap; opt -fast; aigmap; opt_clean"
        try:
            r = _yosys(f"read_verilog {rtl_path}\nhierarchy -check -top {top}\n{lower}\n"
                       f"write_blif gold.blif\n", td, timeout_s)
            if r.returncode != 0:
                return {"pass": None, "detail": "gold: " + (r.stderr or r.stdout)[-1200:],
                        "seconds": round(time.time() - t0, 1)}
            r = _yosys(f"read_liberty -ignore_miss_func {lib}\nread_verilog {net}\n"
                       f"hierarchy -check -top {top}\n{lower}\nwrite_blif gate.blif\n", td, timeout_s)
            if r.returncode != 0:
                return {"pass": None, "detail": "gate: " + (r.stderr or r.stdout)[-1200:],
                        "seconds": round(time.time() - t0, 1)}
            r = subprocess.run([_abc_binary(), "-c", "cec gold.blif gate.blif"], capture_output=True,
                               text=True, timeout=timeout_s, cwd=td)
        except subprocess.TimeoutExpired:
            return {"pass": None, "detail": f"equivalence timeout {timeout_s}s",
                    "seconds": round(time.time() - t0, 1)}
    text = ANSI.sub("", r.stdout + r.stderr)
    if "Networks are equivalent" in text:
        return {"pass": True, "detail": "", "seconds": round(time.time() - t0, 1)}
    if "NOT EQUIVALENT" in text:
        m = re.search(r"Verification failed for.*", text)
        return {"pass": False, "detail": m.group(0)[:500] if m else "not equivalent",
                "seconds": round(time.time() - t0, 1)}
    return {"pass": None, "detail": text[-1200:], "seconds": round(time.time() - t0, 1)}


@node(outputs=["ok", "delay_ps", "critical_path", "detail", "seconds"], resources={"eda": 0.5})
def sta(netlist: str, pdk, clock_ps: int, timeout_s: int = 120, fallback_delay_ps=None) -> dict:
    """The library delay of the mapped netlist from ABC's `stime` on the
    netlist read back with the liberty file (after yosys strips the
    unused wires ABC's mapped reader refuses), and its critical path.
    When ABC cannot read the netlist, `fallback_delay_ps` (the delay
    the synthesis log reported) stands in."""
    t0 = time.time()
    pdk = _pdk(pdk)
    lib = liberty_files(pdk)[0]
    with tempfile.TemporaryDirectory() as td:
        net = Path(td) / "net.v"
        net.write_text(netlist)
        try:
            r = _yosys(f"read_liberty -lib {lib}\nread_verilog {net}\nhierarchy -auto-top\n"
                       f"opt_clean -purge\nwrite_verilog -noattr -noexpr -nodec clean.v\n", td, timeout_s)
            r = subprocess.run([_abc_binary(), "-c", f"read_lib {lib}; read_verilog -m clean.v; topo; stime -p"],
                               capture_output=True, text=True, timeout=timeout_s, cwd=td)
        except subprocess.TimeoutExpired:
            return {"ok": False, "detail": f"abc timeout {timeout_s}s",
                    "seconds": round(time.time() - t0, 1)}
    text = ANSI.sub("", r.stdout + r.stderr)
    m = re.findall(r"Delay\s*=\s*([\d.]+)\s*ps", text)
    if not m:
        if isinstance(fallback_delay_ps, (int, float)):
            return {"ok": True, "delay_ps": float(fallback_delay_ps), "critical_path": "",
                    "detail": "ABC could not read the netlist; the synthesis log's delay stands in: "
                              + text[-300:], "seconds": round(time.time() - t0, 1)}
        return {"ok": False, "detail": text[-1500:], "seconds": round(time.time() - t0, 1)}
    path = "\n".join(ln.rstrip() for ln in text.splitlines()
                     if re.match(r"^\s*(Path\s+\d+\s+--|Start-point)", ln))[:3000]
    return {"ok": True, "delay_ps": float(m[-1]), "critical_path": path or text[-1500:],
            "detail": "", "seconds": round(time.time() - t0, 1)}


@node(outputs=["ok", "recipe"])
def render_recipe(family: str, map_effort: int, opt_full: bool, share: bool) -> dict:
    """The recipe of a RecipeGrid declaration: yosys's synth (with or
    without SHARE and opt -full), then ABC with the family's passes and
    the mapping effort."""
    abc = "+strash;" + ABC_FAMILIES[str(family)] + MAP_EFFORT[int(map_effort)] + ";&put;topo;stime"
    lines = ["read_verilog -sv {rtl}", "hierarchy -check -top {top}",
             "synth -top {top} -flatten -noabc" + ("" if share else " -noshare")]
    if opt_full:
        lines.append("opt -full")
    lines.append(f"abc -liberty {{liberty}} -script {abc}")
    return {"ok": True, "recipe": "\n".join(lines) + "\n"}
