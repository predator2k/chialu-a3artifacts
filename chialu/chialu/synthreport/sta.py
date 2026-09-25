"""Static timing of a mapped, flattened yosys JSON netlist under ABC's
`stime` model (no wire load, load = the fanout pins' capacitances, primary
inputs at 0 ps with 0 slew, primary outputs unloaded, rise/fall paired by
the arc's timing_sense), plus the ownership of every cell by the hierarchy
instance its output logic feeds, path extraction and path queries."""
from __future__ import annotations

import fnmatch
import json
import re
from collections import defaultdict, deque

from .liberty import lookup

INF = float("inf")
R, F = 0, 1


class Netlist:
    def __init__(self, json_path: str, lib: dict, top: str | None = None):
        d = json.load(open(json_path))
        mods = d["modules"]
        if top is None or top not in mods:
            tops = [n for n, m in mods.items() if str((m.get("attributes") or {}).get("top", "")).strip("0") == "1"]
            top = tops[0] if tops else next(iter(mods))
        self.top = top
        m = mods[top]
        self.lib = lib
        self.cells: dict = {}
        self.driver: dict = {}
        self.loads: dict = defaultdict(list)
        self.pi: list = []
        self.po: list = []
        self.port_of_bit: dict = {}
        for pname, p in m["ports"].items():
            for i, b in enumerate(p["bits"]):
                if isinstance(b, int):
                    self.port_of_bit.setdefault(b, (pname, i, len(p["bits"]), p["direction"]))
                    if p["direction"] in ("input", "inout"):
                        self.pi.append(b)
                    if p["direction"] in ("output", "inout"):
                        self.po.append(b)
        self.names: dict = defaultdict(list)
        for nname, n in m["netnames"].items():
            bits = n["bits"]
            hid = int(n.get("hide_name", 0))
            for i, b in enumerate(bits):
                if isinstance(b, int):
                    self.names[b].append((hid, nname, i, len(bits)))
        self.scopes: dict = {}
        self.unknown: dict = defaultdict(int)
        for cname, c in m["cells"].items():
            t = c["type"]
            if t == "$scopeinfo":
                self.scopes[cname] = str((c.get("attributes") or {}).get("module", "")).lstrip("\\")
                continue
            lc = lib.get(t)
            if lc is None:
                self.unknown[t] += 1
                continue
            ins, out = [], None
            for pin, bits in c["connections"].items():
                p = lc["pins"].get(pin)
                if p is None or not bits:
                    continue
                b = bits[0]
                if p["dir"] == "output":
                    if isinstance(b, int):
                        out = (pin, b)
                elif isinstance(b, int):
                    ins.append((pin, b))
            self.cells[cname] = {"type": t, "ins": ins, "out": out, "area": lc["area"] or 0.0}
            if out is not None:
                self.driver[out[1]] = (cname, out[0])
            for pin, b in ins:
                self.loads[b].append((cname, pin))
        self.unknown = dict(self.unknown)
        self.order = self._topo()

    def _topo(self):
        indeg = {c: sum(1 for _, b in v["ins"] if b in self.driver) for c, v in self.cells.items()}
        q = deque(c for c, n in indeg.items() if n == 0)
        order = []
        while q:
            c = q.popleft()
            order.append(c)
            out = self.cells[c]["out"]
            if out is None:
                continue
            for lc, _pin in self.loads.get(out[1], ()):
                indeg[lc] -= 1
                if indeg[lc] == 0:
                    q.append(lc)
        seen = set(order)
        rest = [c for c in self.cells if c not in seen]
        self.loop_cells = len(rest)
        return order + rest

    # ----------------------------------------------------------- names
    def name(self, b: int) -> str:
        """The display name of a net bit: the top-level port when it is
        one, else the shallowest public name (a unit's port rather than
        the alias deeper inside it), else the shortest hidden name."""
        if b in self.port_of_bit:
            p = self.port_of_bit[b]
            return f"{p[0]}[{p[1]}]" if p[2] > 1 else p[0]
        cands = self.names.get(b) or []
        pub = [c for c in cands if c[0] == 0]
        if pub:
            pick = min(pub, key=lambda c: (c[1].count("."), len(c[1])))
        elif cands:
            pick = min(cands, key=lambda c: len(c[1]))
        else:
            return f"<net {b}>"
        _hid, n, i, w = pick
        return f"{n}[{i}]" if w > 1 else n

    def public_names(self, b: int) -> list:
        return [(n, i, w) for hid, n, i, w in self.names.get(b, ()) if hid == 0]

    def area(self) -> float:
        return sum(c["area"] for c in self.cells.values())


def instance_prefix(cell_name: str) -> str:
    """The hierarchy instance a flattened cell name carries, in the form of
    the `$scopeinfo` paths (a.b.c): yosys 0.68's flatten names a private
    object of a flattened instance `$flatten\\a.\\b.$name`; '' for a
    top-level cell."""
    n = cell_name
    if n.startswith("$flatten\\"):
        n = n[len("$flatten\\"):]
    i = n.find("$")
    if i < 0:
        return ""
    return n[:i].rstrip(".").replace(".\\", ".")


class SubNetlist:
    """The cells of one instance subtree as a netlist of their own: the
    nets they read from outside are its inputs, the nets read outside (or
    by nobody) its outputs, which carry no load (a standalone view)."""

    def __init__(self, nl: Netlist, cells: set):
        self.lib = nl.lib
        self.cells = {c: nl.cells[c] for c in cells}
        self.driver = {}
        self.loads = defaultdict(list)
        for c, v in self.cells.items():
            if v["out"] is not None:
                self.driver[v["out"][1]] = (c, v["out"][0])
            for pin, b in v["ins"]:
                self.loads[b].append((c, pin))
        self.pi = sorted({b for v in self.cells.values() for _p, b in v["ins"] if b not in self.driver})
        outs = set()
        for c, v in self.cells.items():
            if v["out"] is None:
                continue
            ob = v["out"][1]
            ext = [lc for lc, _p in nl.loads.get(ob, ()) if lc not in cells]
            if ext or ob in nl.port_of_bit or not nl.loads.get(ob):
                outs.add(ob)
        self.po = sorted(outs)
        self.port_of_bit = {b: nl.port_of_bit[b] for b in nl.port_of_bit if b in self.driver or b in set(self.pi)}
        self.names = nl.names
        self.scopes = nl.scopes
        self.order = [c for c in nl.order if c in self.cells]
        self.loop_cells = 0
        self.name = nl.name
        self.public_names = nl.public_names

    def area(self) -> float:
        return sum(c["area"] for c in self.cells.values())


def subtree_delays(nl: Netlist, own: dict, min_cells: int = 40, max_depth: int = 4) -> dict:
    """{instance path: longest internal path in ns} for every instance whose
    subtree holds at least `min_cells` cells, each timed as a standalone
    netlist (inputs at 0, outputs unloaded)."""
    members = defaultdict(set)
    for cname, os_ in own.items():
        for o in os_:
            p = o
            while p:
                members[p].add(cname)
                p = p.rsplit(".", 1)[0] if "." in p else ""
    out = {}
    for p, cells in members.items():
        if len(cells) < min_cells or p.count(".") >= max_depth:
            continue
        sub = SubNetlist(nl, cells)
        tm = Timing(sub)
        out[p] = max((tm.arrival(b)[0] for b in sub.po), default=0.0)
    return out


# ------------------------------------------------------------- timing

class Timing:
    """Forward arrivals/slews per net (list [ar, af, sr, sf] in ns) and the
    arc that set each maximum; backward remaining delay per net edge."""

    def __init__(self, nl: Netlist, start_bits=None):
        self.nl = nl
        lib = nl.lib
        self.load = {}
        for b, ls in nl.loads.items():
            lr = lf = 0.0
            for cname, pin in ls:
                p = lib[nl.cells[cname]["type"]]["pins"][pin]
                lr += p["rise_cap"]
                lf += p["fall_cap"]
            self.load[b] = (lr, lf)
        starts = set(nl.pi) if start_bits is None else set(start_bits)
        arr = {}
        for b in nl.pi:
            arr[b] = [0.0, 0.0, 0.0, 0.0] if b in starts else [-INF, -INF, 0.0, 0.0]
        pred = {}
        arcs = {}       # (cell, in pin) -> [(in edge, out edge, delay)]
        for cname in nl.order:
            c = nl.cells[cname]
            if c["out"] is None:
                continue
            opin, ob = c["out"]
            lr, lf = self.load.get(ob, (0.0, 0.0))
            best = [-INF, -INF, 0.0, 0.0]
            bp = [None, None]
            lc = lib[c["type"]]
            for pin, ib in c["ins"]:
                a = arr.get(ib)
                if a is None:
                    continue
                used = []
                for arc in lc["arcs_by_pin"].get((pin, opin), ()):
                    t = arc["tables"]
                    sense = arc["sense"]
                    cand = []
                    if sense in ("positive_unate", "non_unate"):
                        if a[R] > -INF and t.get("cell_rise"):
                            cand.append((R, R, lookup(t["cell_rise"], a[2], lr), lookup(t["rise_transition"], a[2], lr) if t.get("rise_transition") else 0.0))
                        if a[F] > -INF and t.get("cell_fall"):
                            cand.append((F, F, lookup(t["cell_fall"], a[3], lf), lookup(t["fall_transition"], a[3], lf) if t.get("fall_transition") else 0.0))
                    if sense in ("negative_unate", "non_unate"):
                        if a[F] > -INF and t.get("cell_rise"):
                            cand.append((F, R, lookup(t["cell_rise"], a[3], lr), lookup(t["rise_transition"], a[3], lr) if t.get("rise_transition") else 0.0))
                        if a[R] > -INF and t.get("cell_fall"):
                            cand.append((R, F, lookup(t["cell_fall"], a[2], lf), lookup(t["fall_transition"], a[2], lf) if t.get("fall_transition") else 0.0))
                    for ie, oe, d, s in cand:
                        at = a[ie] + d
                        if at > best[oe]:
                            best[oe] = at
                            bp[oe] = (ib, ie, d, pin)
                        if s > best[oe + 2]:
                            best[oe + 2] = s
                        used.append((ie, oe, d))
                if used:
                    arcs[(cname, pin)] = used
            arr[ob] = best
            pred[ob] = bp
        self.arr, self.pred, self.arcs = arr, pred, arcs
        # backward: the remaining delay from a net edge to the latest endpoint it reaches
        late = defaultdict(lambda: [-INF, -INF])
        succ = {}
        for b in nl.po:
            a = arr.get(b)
            if a is None:
                continue
            for e in (R, F):
                if a[e] > -INF:
                    late[b][e] = 0.0
        for cname in reversed(nl.order):
            c = nl.cells[cname]
            if c["out"] is None:
                continue
            ob = c["out"][1]
            lo = late[ob]
            for pin, ib in c["ins"]:
                for ie, oe, d in arcs.get((cname, pin), ()):
                    if lo[oe] > -INF and d + lo[oe] > late[ib][ie]:
                        late[ib][ie] = d + lo[oe]
                        succ[(ib, ie)] = (cname, pin, oe, d)
        self.late, self.succ = late, succ

    # ------------------------------------------------------ path pieces
    def arrival(self, b: int):
        a = self.arr.get(b)
        if a is None:
            return -INF, R
        return (a[R], R) if a[R] >= a[F] else (a[F], F)

    def back(self, b: int, e: int) -> list:
        """The path into net edge (b, e): [(cell, in pin, in edge, out edge,
        delay, in bit, out bit)] from the startpoint on."""
        steps = []
        seen = 0
        while b in self.pred and self.pred[b][e] is not None and seen < 100000:
            ib, ie, d, pin = self.pred[b][e]
            cname, _ = self.nl.driver[b]
            steps.append((cname, pin, ie, e, d, ib, b))
            b, e = ib, ie
            seen += 1
        steps.reverse()
        return steps

    def forward(self, b: int, e: int) -> list:
        steps = []
        seen = 0
        while (b, e) in self.succ and seen < 100000:
            cname, pin, oe, d = self.succ[(b, e)]
            ob = self.nl.cells[cname]["out"][1]
            steps.append((cname, pin, e, oe, d, b, ob))
            b, e = ob, oe
            seen += 1
        return steps

    def endpoint_paths(self, n: int, to_bits=None) -> list:
        """The n latest endpoints: [(arrival ns, bit, edge, steps)]."""
        rows = []
        for b in (to_bits if to_bits is not None else self.nl.po):
            a, e = self.arrival(b)
            if a > -INF:
                rows.append((a, b, e))
        rows.sort(key=lambda r: -r[0])
        return [(a, b, e, self.back(b, e)) for a, b, e in rows[:n]]

    def through(self, bits, n: int = 1) -> list:
        """The n worst paths through any of the net bits: [(total ns, bit,
        edge, steps)] with the path assembled backward and forward."""
        rows = []
        for b in bits:
            a = self.arr.get(b)
            if a is None:
                continue
            for e in (R, F):
                if a[e] > -INF and self.late[b][e] > -INF:
                    rows.append((a[e] + self.late[b][e], b, e))
        rows.sort(key=lambda r: -r[0])
        out, seen_paths = [], set()
        for tot, b, e in rows:
            steps = self.back(b, e) + self.forward(b, e)
            key = tuple(s[0] for s in steps)
            if key in seen_paths:
                continue
            seen_paths.add(key)
            out.append((tot, b, e, steps))
            if len(out) >= n:
                break
        return out


# ------------------------------------------------------------ owners

def port_dirs(in_txt: str, out_txt: str) -> dict:
    """{module: {port: 'input'|'output'}} from the `select -list */i:*` and
    `select -list */o:*` listings (lines of the form module/port)."""
    dirs: dict = defaultdict(dict)
    for txt, kind in ((in_txt, "input"), (out_txt, "output")):
        for line in (txt or "").splitlines():
            line = line.strip()
            if not line or "/" not in line:
                continue
            mod, port = line.rsplit("/", 1)
            dirs[mod.lstrip("\\")][port.lstrip("\\")] = kind
    return dirs


def boundary_owner(nl: Netlist, dirs: dict, unit_only: bool = True) -> dict:
    """{bit: owner instance path} for the nets that bound the attribution:
    a public hierarchical name `inst.port` is owned by `inst` when `port`
    is an output or an internal wire of inst's module and by inst's parent
    when it is an input; a primary output belongs to the top ('')."""
    owner = {}
    for b, cands in nl.names.items():
        best_out, best_in = None, None
        for hid, n, _i, _w in cands:
            if hid or "." not in n:
                continue
            base = n.split("$")[0]
            if "." not in base:
                continue
            inst, port = base.rsplit(".", 1)
            if unit_only and "." in inst:
                continue
            mod = nl.scopes.get(inst)
            if mod is None:
                continue
            d = (dirs.get(mod) or {}).get(port)
            if d == "input":
                parent = inst.rsplit(".", 1)[0] if "." in inst else ""
                if best_in is None or parent.count(".") < best_in.count("."):
                    best_in = parent
            else:
                if best_out is None or inst.count(".") > best_out.count("."):
                    best_out = inst
        if best_out is not None:
            owner[b] = best_out
        elif b in nl.port_of_bit and nl.port_of_bit[b][3] == "output":
            owner[b] = ""
        elif best_in is not None:
            owner[b] = best_in
    for b in nl.po:
        owner.setdefault(b, "")
    return owner


def cell_owners(nl: Netlist, bowner: dict) -> dict:
    """{cell: frozenset(owners)}: a cell belongs to the owners of the first
    boundary nets its output reaches (several when ABC shared its logic)."""
    own = {}
    for cname in reversed(nl.order):
        c = nl.cells[cname]
        if c["out"] is None:
            own[cname] = frozenset([""])
            continue
        ob = c["out"][1]
        if ob in bowner:
            own[cname] = frozenset([bowner[ob]])
            continue
        s = set()
        for lc, _pin in nl.loads.get(ob, ()):
            s |= own.get(lc, frozenset())
        own[cname] = frozenset(s) if s else frozenset([""])
    return own


def primary_owner(owners: frozenset) -> str:
    """One label for a cell: its instance, 'top' for the logic outside every
    unit, `shared(a,b)` or `shared(k)` when ABC merged it between owners."""
    if not owners:
        return "top"
    if len(owners) == 1:
        o = next(iter(owners))
        return o if o else "top"
    if len(owners) == 2:
        return "shared(" + ",".join(sorted(o if o else "top" for o in owners)) + ")"
    return f"shared({len(owners)})"


def area_tree(nl: Netlist, own: dict) -> dict:
    """{instance path: {'area', 'cells', 'shared_area', 'shared_cells'}} with
    fractional shares of shared cells, subtree sums included."""
    tree: dict = defaultdict(lambda: {"area": 0.0, "cells": 0.0, "shared_area": 0.0, "shared_cells": 0.0})
    for cname, c in nl.cells.items():
        os_ = own.get(cname, frozenset([""]))
        k = len(os_)
        for o in os_:
            path = o
            while True:
                t = tree[path]
                t["area"] += c["area"] / k
                t["cells"] += 1.0 / k
                if k > 1:
                    t["shared_area"] += c["area"] / k
                    t["shared_cells"] += 1.0 / k
                if path == "":
                    break
                path = path.rsplit(".", 1)[0] if "." in path else ""
    return tree


# ---------------------------------------------------------- matching

def match_bits(nl: Netlist, pattern: str, own: dict | None = None) -> set:
    """Net bits whose public name matches the glob (an instance name
    matches every net named under it, and every output of its cells)."""
    pat = pattern
    bits = set()
    rx = re.compile(fnmatch.translate(pat))
    rx_under = re.compile(fnmatch.translate(pat + ".*"))
    rx_bit = re.compile(fnmatch.translate(pat + "[[]*[]]"))
    for b, cands in nl.names.items():
        for hid, n, i, w in cands:
            if hid:
                continue
            full = f"{n}[{i}]" if w > 1 else n
            if rx.match(n) or rx.match(full) or rx_under.match(n) or rx_bit.match(full):
                bits.add(b)
                break
    if own is not None:
        for cname, os_ in own.items():
            if any(o and (rx.match(o) or rx_under.match(o)) for o in os_):
                out = nl.cells[cname]["out"]
                if out is not None:
                    bits.add(out[1])
    return bits


def port_bits(nl: Netlist, pattern: str, direction: str) -> list:
    rx = re.compile(fnmatch.translate(pattern))
    out = []
    for b, (pname, i, w, d) in nl.port_of_bit.items():
        if d != direction:
            continue
        full = f"{pname}[{i}]" if w > 1 else pname
        if rx.match(pname) or rx.match(full):
            out.append(b)
    return out
