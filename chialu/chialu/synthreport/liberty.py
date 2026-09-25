"""A minimal liberty reader for delay reports: per cell the area, the pins
(direction, capacitances) and the combinational timing arcs with their NLDM
tables (cell_rise, cell_fall, rise_transition, fall_transition), and the
bilinear table lookup ABC's `stime` uses (Scl_LibLookup: interpolation
inside the table, linear extrapolation outside). Times are in the liberty's
unit (ns for nangate45), loads in its capacitance unit (fF)."""
from __future__ import annotations

import os
import pickle
import re

_GROUP = re.compile(r'^([A-Za-z_]\w*)\s*\(([^)]*)\)\s*\{$')
_ATTR = re.compile(r'^([A-Za-z_]\w*)\s*:\s*(.+?)\s*;$')
_TABLE = re.compile(r'^(index_1|index_2|values)\s*\((.*)\)\s*;?$')
_NUM = re.compile(r'[-+]?\d*\.?\d+(?:[eE][-+]?\d+)?')
TABLES = ("cell_rise", "cell_fall", "rise_transition", "fall_transition")
COMBINATIONAL = (None, "combinational", "combinational_rise", "combinational_fall")


def parse(path: str) -> dict:
    text = open(path).read().replace("\\\n", " ")
    cells: dict = {}
    stack: list = []
    cell = pin = timing = table = None
    unit = {"time_ns": 1.0, "cap_ff": 1.0}
    for raw in text.split("\n"):
        s = raw.strip()
        if not s or s[0] in "/*":
            continue
        m = _GROUP.match(s)
        if m:
            g, args = m.group(1), m.group(2).strip().strip('"')
            stack.append(g)
            if g == "cell":
                cell = {"name": args, "area": 0.0, "pins": {}, "arcs": []}
                cells[args] = cell
            elif g == "pin" and cell is not None:
                pin = {"name": args, "dir": None, "cap": None, "rise_cap": None, "fall_cap": None}
                cell["pins"][args] = pin
            elif g == "timing":
                timing = {"related_pin": None, "sense": "non_unate", "type": None, "when": None, "tables": {}, "pin": pin}
            elif g in TABLES and timing is not None:
                table = {"index_1": None, "index_2": None, "values": None}
                timing["tables"][g] = table
            continue
        if s.startswith("}"):
            g = stack.pop() if stack else None
            if g == "cell":
                cell = None
            elif g == "pin":
                pin = None
            elif g == "timing":
                if timing is not None and cell is not None and timing.get("pin") is not None \
                        and timing["type"] in COMBINATIONAL and timing["related_pin"] and timing["tables"]:
                    for rp in timing["related_pin"].split():
                        cell["arcs"].append(dict(timing, related_pin=rp, out=timing["pin"]["name"]))
                timing = None
            elif g in TABLES:
                table = None
            continue
        m = _ATTR.match(s)
        if not m:
            m2 = _TABLE.match(s)
            if m2 and table is not None:
                table[m2.group(1)] = [float(x) for x in _NUM.findall(m2.group(2))]
            continue
        k, v = m.group(1), m.group(2).strip().strip('"')
        if cell is None:
            if k == "time_unit":
                unit["time_ns"] = {"1ns": 1.0, "1ps": 0.001, "10ps": 0.01, "100ps": 0.1}.get(v, 1.0)
            continue
        if pin is None:
            if k == "area":
                cell["area"] = float(v)
        elif timing is None:
            if k == "direction":
                pin["dir"] = v
            elif k == "capacitance":
                pin["cap"] = float(v)
            elif k == "rise_capacitance":
                pin["rise_cap"] = float(v)
            elif k == "fall_capacitance":
                pin["fall_cap"] = float(v)
        else:
            if k == "related_pin":
                timing["related_pin"] = v
            elif k == "timing_sense":
                timing["sense"] = v
            elif k == "timing_type":
                timing["type"] = v
            elif k == "when":
                timing["when"] = v
    for c in cells.values():
        groups = {}
        for a in c["arcs"]:
            groups.setdefault((a["related_pin"], a["out"]), []).append(a)
        # ABC's reader (sclLiberty.c: Scl_LibertyReadPinTimingAll + Scl_LibertyComputeWorstCase) merges the
        # timing groups of one related pin into one arc: the first group's timing_sense, and per table the
        # elementwise maximum over the groups (a `when` condition is not read)
        by = {}
        for key, arcs in groups.items():
            first = arcs[0]
            merged = {"related_pin": key[0], "out": key[1], "sense": first["sense"], "type": first["type"],
                      "when": None, "tables": {}}
            for tname in TABLES:
                tabs = [a["tables"][tname] for a in arcs if a["tables"].get(tname) and a["tables"][tname].get("values")]
                if not tabs:
                    continue
                base = tabs[0]
                vals = list(base["values"])
                for t in tabs[1:]:
                    if len(t["values"]) == len(vals) and t["index_1"] == base["index_1"] and t["index_2"] == base["index_2"]:
                        vals = [max(x, y) for x, y in zip(vals, t["values"])]
                merged["tables"][tname] = {"index_1": base["index_1"], "index_2": base["index_2"], "values": vals}
            by[key] = [merged]
        c["arcs_by_pin"] = by
        for p in c["pins"].values():
            if p["rise_cap"] is None:
                p["rise_cap"] = p["cap"] or 0.0
            if p["fall_cap"] is None:
                p["fall_cap"] = p["cap"] or 0.0
    cells["__units__"] = unit
    return cells


def load(path: str, cache_dir: str | None = None) -> dict:
    """The parsed library, cached as a pickle keyed by path and mtime
    (under ~/.cache/chialu/liberty unless a directory is given)."""
    st = os.stat(path)
    cache_dir = cache_dir or os.environ.get("CHIALU_LIBERTY_CACHE") or os.path.join(os.path.expanduser("~"), ".cache", "chialu", "liberty")
    os.makedirs(cache_dir, exist_ok=True)
    key = os.path.join(cache_dir, f"{os.path.basename(path)}.{int(st.st_mtime)}.{st.st_size}.v2.pkl")
    if os.path.isfile(key):
        with open(key, "rb") as f:
            return pickle.load(f)
    lib = parse(path)
    with open(key, "wb") as f:
        pickle.dump(lib, f)
    return lib


def lookup(tbl: dict, slew: float, load: float) -> float:
    """ABC's Scl_LibLookup: index_1 is the input slew, index_2 the output load;
    bilinear between the two nearest samples, extrapolated at the ends."""
    x, y, v = tbl["index_1"], tbl["index_2"], tbl["values"]
    if x is None or y is None or v is None:
        return 0.0
    nx, ny = len(x), len(y)
    if ny == 0 or nx == 0:
        return 0.0
    if nx == 1 and ny == 1:
        return v[0]

    def seg(idx, val):
        n = len(idx)
        if n == 1:
            return 0, 0, 0.0
        i = 1
        while i < n - 1 and idx[i] <= val:
            i += 1
        i -= 1
        return i, i + 1, (val - idx[i]) / (idx[i + 1] - idx[i])

    i0, i1, tx = seg(x, slew)
    j0, j1, ty = seg(y, load)

    def at(i, j):
        return v[i * ny + j]

    p0 = at(i0, j0) + ty * (at(i0, j1) - at(i0, j0))
    p1 = at(i1, j0) + ty * (at(i1, j1) - at(i1, j0))
    return p0 + tx * (p1 - p0)
