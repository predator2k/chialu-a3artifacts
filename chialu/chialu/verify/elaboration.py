"""The hierarchy, parameters and port widths a design elaborates to.

`elaborate` runs Verilator's `--json-only` front end over the source
and reads the tree it writes, so the answer is the design as
elaborated rather than as written: a parameter carries the value the
instance passed and a port the width that value produced.
"""
from pathlib import Path
import json
import re
import subprocess


_CONST_RE = re.compile(r"^(?:(\d+)'s?[hH])?([0-9a-fA-F_]+)$")


def _nodes(tree, want, out=None):
    """Every node of a Verilator tree of one `type`."""
    out = [] if out is None else out
    if isinstance(tree, dict):
        if tree.get("type") == want:
            out.append(tree)
        for v in tree.values():
            if isinstance(v, (list, dict)):
                _nodes(v, want, out)
    elif isinstance(tree, list):
        for x in tree:
            _nodes(x, want, out)
    return out


def _const_value(node):
    """A CONST node's value as an int, from its `32'sh1f` spelling."""
    m = _CONST_RE.match(str(node.get("name", "")).strip())
    if not m:
        return None
    try:
        return int(m.group(2).replace("_", ""), 16)
    except ValueError:
        return None


def _width(dtype) -> int:
    """A dtype's width from its `15:0` range; a dtype without one is one bit."""
    r = str((dtype or {}).get("range") or "")
    m = re.match(r"^\s*(\d+)\s*:\s*(\d+)\s*$", r)
    if not m:
        return 1
    return abs(int(m.group(1)) - int(m.group(2))) + 1


def _cells(tree, scope=()):
    """(generate scope, cell) for every cell of a module: the names of the
    generate blocks around it, outermost first. The cells a generate loop
    replicates share one local name (`chunk[0].u_chunk`, `chunk[1].u_chunk`),
    so the scope is what tells them apart in a path."""
    if isinstance(tree, dict):
        if tree.get("type") == "CELL":
            yield scope, tree
        if tree.get("type") == "GENBLOCK" and tree.get("name"):
            scope = scope + (str(tree["name"]),)
        for v in tree.values():
            if isinstance(v, (list, dict)):
                yield from _cells(v, scope)
    elif isinstance(tree, list):
        for x in tree:
            yield from _cells(x, scope)


def inspect_tree_json(tree) -> list:
    """The elaborated instances of a Verilator `--json-only` tree, in the
    one entry per instance with its module,
    its parameter values and its port directions and widths. The
    hierarchy is walked from the top module through its cells, so an
    instance appears once per path rather than once per module. Each row
    also carries `signals`, the widths of the module's own variables,
    which a caller reads to check an internal width."""
    modules = {m.get("addr"): m for m in _nodes(tree, "MODULE") if m.get("addr")}
    dtypes = {}
    for kind in ("BASICDTYPE", "PACKARRAYDTYPE", "UNPACKARRAYDTYPE", "STRUCTDTYPE", "ENUMDTYPE"):
        for d in _nodes(tree, kind):
            if d.get("addr"):
                dtypes.setdefault(d["addr"], d)

    def facts(mod):
        params, ports, signals = {}, {}, {}
        for v in _nodes(mod, "VAR"):
            if v.get("isParam") or v.get("varType") in ("GPARAM", "LPARAM"):
                consts = _nodes(v.get("valuep") or [], "CONST")
                val = _const_value(consts[0]) if consts else None
                if val is not None:
                    params[v.get("name")] = val
            elif v.get("varType") == "PORT" or str(v.get("direction", "NONE")).upper() in ("INPUT", "OUTPUT", "INOUT", "REF"):
                # an ANSI `input wire` port is a WIRE with a direction in Verilator's tree, a bare one a PORT
                ports[v.get("name")] = {"direction": str(v.get("direction", "")).lower(),
                                        "width": _width(dtypes.get(v.get("dtypep")))}
            else:
                # the module's own signals, which a caller reads to check an internal width
                signals[v.get("name")] = _width(dtypes.get(v.get("dtypep")))
        return params, ports, signals

    top = None
    for m in modules.values():
        if m.get("topModule") or m.get("level") == 1:
            top = m
            break
    if top is None:
        tops = [m for m in modules.values() if not str(m.get("name", "")).startswith("@")]
        top = tops[0] if tops else None
    if top is None:
        return []
    out, seen = [], set()

    def walk(mod, name, path):
        params, ports, signals = facts(mod)
        # `instance` is the local name a parent wrote, and `path` carries the whole hierarchy
        out.append({"id": mod.get("addr"), "instance": name, "path": path,
                    "module": mod.get("origName") or mod.get("name"),
                    "parameters": params, "ports": ports, "signals": signals})
        for scope, cell in _cells(mod):
            sub = modules.get(cell.get("modp"))
            child = str(cell.get("name"))
            where = path + "." + "".join(s + "." for s in scope) + child
            key = (cell.get("modp"), where)
            if sub is not None and key not in seen:
                seen.add(key)
                walk(sub, child, where)

    root = str(top.get("origName") or top.get("name"))
    walk(top, root, root)
    return out


def elaborate_and_run(source, top, directory, compile_timeout=1800, run_timeout=1800):
    """(rows, completed process): `elaborate` and one run of the model it
    built."""
    rows = elaborate(source, top, directory, timeout=compile_timeout)
    run = subprocess.run(["./obj_sim/sim"], cwd=str(Path(directory)), capture_output=True, text=True,
                         timeout=run_timeout)
    return rows, run


def hierarchy_of_files(sources, directory, top, timeout=120) -> list:
    """The elaborated hierarchy of files already written under
    `directory`. A caller that has written its design and its testbench
    uses this rather than joining them back into one string for
    `elaborate`."""
    from chialu.verify.simulate import scaled
    directory = Path(directory)
    r = subprocess.run(["verilator", "--json-only", "--no-json-ids", "-Wno-fatal", "-Wno-lint",
                        "-Wno-style", "--top-module", top, "-Mdir", "obj_elab",
                        *[str(s) for s in sources]],
                       cwd=str(directory), capture_output=True, text=True, timeout=scaled(timeout))
    (directory / "verilator_elab.log").write_text(r.stdout + r.stderr)
    r.check_returncode()
    trees = sorted((directory / "obj_elab").glob("*.tree.json"))
    if not trees:
        raise RuntimeError("verilator wrote no tree; see verilator_elab.log")
    return inspect_tree_json(json.loads(trees[0].read_text()))


def elaborate(source, top, directory, timeout=600):
    """The elaborated hierarchy of `source` under `top`, through
    Verilator, which reads the generated SystemVerilog directly.

    A runnable model is built beside it at `obj_sim/sim`, which several
    callers run after elaborating.
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    sv = directory / "design.sv"
    sv.write_text(source)
    from chialu.verify import simulate as SIM
    build = subprocess.run(["verilator", *SIM.VERILATOR_FLAGS, "-j", str(SIM.VERILATOR_JOBS),
                            "--top-module", top, "-Mdir", "obj_sim", "-o", "sim", sv.name],
                           cwd=str(directory), capture_output=True, text=True, timeout=SIM.scaled(timeout))
    (directory / "verilator.log").write_text(build.stdout + build.stderr)
    build.check_returncode()
    return hierarchy_of_files([sv.name], directory, top, timeout=timeout)
