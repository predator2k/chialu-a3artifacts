"""Internal fault sites of an ALU candidate (docs/checker-spec-plan.md,
"The fault campaign"): the nets declared inside the candidate's unit
modules, their lane modules and the modules those instantiate, each
named by its hierarchical path under the core instance, with the modes
and ops the unit serves (from the seed's STRUCTURE lines in the top).

A fault at a site is a one-bit corruption of that net while a vector is
applied; a corruption that leaves the data output unchanged is masked
and is not a fault of the campaign. The site set is what the text
declares with a literal width (`logic [15:0] s;`, `wire c;`): a library
module's parametric nets contribute their one-bit nets alone, and a
net declared inside a generate block, an always block or a function is
no site (its name lives in that scope).
"""
from __future__ import annotations

import re

MODULE_RE = re.compile(r"^module\s+(\w+)\b(.*?)^endmodule", re.M | re.S)
INST_RE = re.compile(r"^\s*(\w+)\s+(?:#\s*\((?:[^()]|\([^()]*\))*\)\s*)?(\w+)\s*\(", re.M)
NET_RE = re.compile(r"^\s*(?:logic|wire|reg)\s+(?:signed\s+)?(?:\[\s*(\d+)\s*:\s*(\d+)\s*\]\s*)?(\w+)\s*(?:;|,|=)", re.M)
STRUCT_RE = re.compile(r"^\s*//\s*(?://\s*)?STRUCTURE\s+(\S+)\s+kind=(\w+)\b.*?\bmode=(\d+)\b.*?\bops=(\S+).*?\bsv=(\w+)", re.M)
UNIT_RE = re.compile(r"^\s*//\s*UNIT\s+(\S+)\s+module=(\w+)\s+kind=(\w+)", re.M)
YPORT_RE = re.compile(r"\boutput\s+(?:logic|wire|reg)?\s*(?:\[[^\]]+\]\s*)?y_m(\d+)\b")
MAX_DEPTH = 4
KEYWORDS = {"assign", "always_comb", "always", "if", "else", "for", "case", "begin", "end", "function",
            "module", "endmodule", "initial", "return", "logic", "wire", "reg", "input", "output"}


def modules_of(text: str) -> dict:
    return {m.group(1): m.group(2) for m in MODULE_RE.finditer(text)}


SCOPE_RE = re.compile(r"\b(begin|end|case|endcase|function|endfunction|task|endtask|generate|endgenerate|fork|join)\b")
COMMENT_RE = re.compile(r"/\*.*?\*/|//[^\n]*", re.S)


def module_scope(body: str) -> str:
    """The lines of a module body outside every block: a net declared
    inside a generate loop, a generate `if`, an always block or a
    function lives in that scope (`genblk1[3].all1`, a block local), so
    its module-level name is no hierarchical path."""
    depth = 0
    kept = []
    for line in COMMENT_RE.sub("", body).splitlines():
        opens = closes = 0
        for tok in SCOPE_RE.findall(line):
            if tok in ("begin", "case", "function", "task", "generate", "fork"):
                opens += 1
            else:
                closes += 1
        if depth == 0 and closes == 0:
            kept.append(line)
        depth = max(0, depth + opens - closes)
    return "\n".join(kept)


def _nets(body: str) -> list:
    """[(net, width)] of the literal-width nets a module body declares at
    module scope."""
    out = []
    for hi, lo, name in NET_RE.findall(module_scope(body)):
        if hi == "" and lo == "":
            out.append((name, 1))
        else:
            out.append((name, abs(int(hi) - int(lo)) + 1))
    return out


def _instances(body: str, modules: dict) -> list:
    """[(module, instance)] of the module instances a body holds."""
    out = []
    for mod, inst in INST_RE.findall(body):
        if mod in modules and mod not in KEYWORDS and inst not in KEYWORDS:
            out.append((mod, inst))
    return out


def unit_map(text: str, top: str = "alu_core") -> dict:
    """{unit module: {"instance", "modes", "ops", "kind"}} of the top's unit
    modules: the instance name from the top's body, the modes and ops from
    the STRUCTURE lines that name the module (a unit without a line
    serves the modes its y_m<mode> ports name and every op)."""
    modules = modules_of(text)
    if top not in modules:
        return {}
    body = modules[top]
    units: dict = {}
    for mod, inst in _instances(body, modules):
        if mod.startswith(top + "_u_"):
            units[mod] = {"instance": inst, "modes": set(), "ops": set(), "kind": None}
    for _sid, kind, mode, ops, sv in STRUCT_RE.findall(text):
        if sv in units:
            units[sv]["modes"].add(int(mode))
            units[sv]["ops"].update(o for o in ops.split(",") if o)
            units[sv]["kind"] = units[sv]["kind"] or kind
    for _name, mod, kind in UNIT_RE.findall(text):
        if mod in units:
            units[mod]["kind"] = units[mod]["kind"] or kind
    for mod, u in units.items():
        if not u["modes"]:
            u["modes"] = {int(m) for m in YPORT_RE.findall(modules[mod])}
        if not u["ops"]:
            u["ops"] = None                        # every op
    return units


def unit_sites(text: str, unit_module: str, instance: str, core: str = "core") -> list:
    """[(hierarchical path, width)] of the nets under one unit instance,
    the unit's own and those of the modules it instantiates (to MAX_DEPTH)."""
    modules = modules_of(text)
    out = []

    def walk(mod, prefix, depth):
        body = modules.get(mod)
        if body is None or depth > MAX_DEPTH:
            return
        for net, width in _nets(body):
            out.append((f"{prefix}.{net}", width))
        for sub, inst in _instances(body, modules):
            walk(sub, f"{prefix}.{inst}", depth + 1)
    walk(unit_module, f"{core}.{instance}", 1)
    return out


def sites_by_pair(text: str, top: str = "alu_core", core: str = "core") -> dict:
    """{(mode, op): [(path, width)]} for every (mode, op) a unit of the
    candidate serves; a unit that names no ops serves every op of its
    modes (the caller intersects with the unit's legal pairs)."""
    units = unit_map(text, top)
    per_unit = {mod: unit_sites(text, mod, u["instance"], core) for mod, u in units.items()}
    out: dict = {}
    for mod, u in units.items():
        for mi in u["modes"]:
            for op in (u["ops"] if u["ops"] is not None else ("*",)):
                out.setdefault((mi, op), []).extend(per_unit[mod])
    return out


def sites_for(pairs, table: dict) -> list:
    """The sites serving any of `pairs` [(mode, op)], from sites_by_pair's table."""
    seen, out = set(), []
    for mi, op in pairs:
        for key in ((mi, op), (mi, "*")):
            for site in table.get(key, ()):
                if site not in seen:
                    seen.add(site)
                    out.append(site)
    return out
