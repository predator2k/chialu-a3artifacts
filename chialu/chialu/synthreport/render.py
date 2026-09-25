"""Text renderings of paths and area trees for the coding agent."""
from __future__ import annotations

from .sta import INF, Netlist, Timing, primary_owner

PS = 1000.0     # liberty ns -> ps


def label(o: str) -> str:
    return o if o else "top"


def segments(nl: Netlist, own: dict, steps: list, t0: float = 0.0) -> list:
    """Consecutive cells of one owner: [(owner, n cells, t_in ps, t_out ps,
    entry net, exit net)]."""
    out = []
    t = t0
    for cname, _pin, _ie, _oe, d, ib, ob in steps:
        o = primary_owner(own.get(cname, frozenset([""])))
        t_in, t = t, t + d * PS
        if out and out[-1][0] == o:
            s = out[-1]
            out[-1] = (o, s[1] + 1, s[2], t, s[4], nl.name(ob))
        else:
            out.append((o, 1, t_in, t, nl.name(ib), nl.name(ob)))
    return out


def path_text(nl: Netlist, tm: Timing, own: dict, steps: list, title: str, t0: float = 0.0) -> str:
    L = [title]
    if not steps:
        return "\n".join(L + ["(no path)", ""])
    start, end = steps[0][5], steps[-1][6]
    total = t0 + sum(s[4] for s in steps) * PS
    L.append(f"start {nl.name(start)} ({'input' if start in nl.port_of_bit else 'net'})  ->  end {nl.name(end)}"
             f" ({'output' if end in nl.port_of_bit and nl.port_of_bit[end][3] == 'output' else 'net'})"
             f"   {total:.1f} ps   {len(steps)} cells")
    L.append("segments (consecutive cells owned by one hierarchy instance):")
    for o, n, ti, to, ent, ext in segments(nl, own, steps, t0):
        L.append(f"  {label(o):<28} {n:>3} cells  {ti:7.1f} -> {to:7.1f} ps  (+{to - ti:6.1f})   in via {ent}   out via {ext}")
    L.append("")
    L.append(f"{'#':>3} {'arrival':>8} {'incr':>6} {'edge':>4}  {'cell':<11} {'owner':<26} {'output net':<44} {'fo':>3} {'load':>6} {'slew':>6}")
    t = t0
    for i, (cname, pin, ie, oe, d, ib, ob) in enumerate(steps, 1):
        t += d * PS
        c = nl.cells[cname]
        os_ = own.get(cname, frozenset([""]))
        o = primary_owner(os_)
        slew = tm.arr.get(ob, [0, 0, 0, 0])[2 + oe] * PS
        load = tm.load.get(ob, (0.0, 0.0))[oe]
        edge = f"{'rf'[ie]}->{'rf'[oe]}"
        L.append(f"{i:>3} {t:8.1f} {d * PS:6.1f} {edge:>5}  {c['type']:<11} {o:<26} {nl.name(ob)[:44]:<44} {len(nl.loads.get(ob, ())):>3} {load:6.1f} {slew:6.1f}")
    L.append("edge: input edge -> output edge (r rise, f fall); load in fF at the cell output; slew in ps; shared(...) = logic ABC merged between instances")
    legend = {}
    for cname, *_rest in steps:
        os_ = own.get(cname, frozenset([""]))
        if len(os_) > 2:
            legend.setdefault(primary_owner(os_), sorted(o if o else "top" for o in os_))
    for k, v in legend.items():
        L.append(f"  {k} = {', '.join(v)}")
    L.append("")
    return "\n".join(L)


def endpoint_line(nl: Netlist, own: dict, i: int, a: float, b: int, steps: list) -> str:
    segs = segments(nl, own, steps)
    chain = " -> ".join(f"{label(o)}({n}, {to - ti:.0f} ps)" for o, n, ti, to, _e, _x in segs)
    start = nl.name(steps[0][5]) if steps else "?"
    return f"{i:>3}. {nl.name(b):<22} {a * PS:8.1f} ps  from {start:<20} {len(steps):>3} cells   {chain}"


def tree_text(tree: dict, scopes: dict, total: float, title: str, cells_label: str = "cells", delays: dict | None = None,
              min_pct: float = 0.25, max_depth: int = 5) -> list:
    """The instance tree, largest first; a child under `min_pct` of the total
    or deeper than `max_depth` is folded into one '(n more instances)' line."""
    L = [title, f"{'instance':<46} {'module':<40} {'area um2':>9} {'%':>6} {cells_label:>8}" + (f" {'delay ps':>9}" if delays else "")]
    paths = sorted(tree, key=lambda p: (p.count("."), p))
    children = {}
    for p in paths:
        parent = p.rsplit(".", 1)[0] if "." in p else ("" if p else None)
        if parent is not None:
            children.setdefault(parent, []).append(p)

    def walk(p, depth):
        t = tree[p]
        name = ("  " * depth) + (p.rsplit(".", 1)[-1] if p else "top (whole design)")
        mod = scopes.get(p, "") if p else ""
        dl = f" {delays[p]:9.0f}" if delays and p in delays else (f" {'':>9}" if delays else "")
        L.append(f"{name:<46} {mod[:40]:<40} {t['area']:9.1f} {100 * t['area'] / total if total else 0:6.1f} {t['cells']:8.1f}{dl}")
        kids = sorted(children.get(p, []), key=lambda c: -tree[c]["area"])
        shown = [c for c in kids if depth < max_depth and 100 * tree[c]["area"] / (total or 1) >= min_pct]
        for c in shown:
            walk(c, depth + 1)
        rest = [c for c in kids if c not in shown]
        if rest:
            ra = sum(tree[c]["area"] for c in rest)
            rc = sum(tree[c]["cells"] for c in rest)
            L.append(f"{'  ' * (depth + 1) + f'({len(rest)} more instances)':<46} {'':<40} {ra:9.1f} {100 * ra / total if total else 0:6.1f} {rc:8.1f}")
    walk("", 0)
    return L
