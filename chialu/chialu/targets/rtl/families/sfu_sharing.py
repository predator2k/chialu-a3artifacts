"""Selector-controlled sharing of structured SFU construction records.

Operations with compatible signedness and operator shape can share a
resource. A promoted resource sign-extends its inputs and retains each
consumer's original truncation through a separate alias. Library instances
share only when their module and parameter set match. Inputs are selected
before the resource. Grouping
uses evaluator invocation and dependency depth, and the resulting graph is
checked for cycles before emitting RTL. A function never shares two of its
own simultaneous operations.
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
import re

from chialu.targets.rtl.families.sfu import Ref


@dataclass
class Node:
    fi: int
    kind: str
    stage: str
    depth: int
    outputs: tuple
    inputs: tuple
    template: object
    payload: object = None

    @property
    def shape(self):
        return (self.kind, self.stage, self.depth,
                tuple((r.w, r.s) for r in self.outputs),
                tuple((r.w, r.s) for r in self.inputs), self.template)


@dataclass
class Group:
    index: int
    rows: list = field(default_factory=list)
    inputs: list = field(default_factory=list)

    @property
    def outputs(self):
        return tuple(Ref(f"shared_n{self.index}_{i}", max(row.outputs[i].w for row in self.rows), r.s)
                     for i, r in enumerate(self.rows[0].outputs))


def _replace(text, symbols, ordered):
    def one(match):
        key = match.group()
        if key not in symbols:
            return key
        if key not in ordered:
            ordered.append(key)
        return f"__arg{ordered.index(key)}__"
    # A numeric literal such as 1'b1 is not a reference to a wire named b1.
    return re.sub(r"(?<![A-Za-z_0-9$'])\b[A-Za-z_][A-Za-z_0-9]*\b", one, text)


def _nodes(net, fi):
    refs = {r.name: r for _, r in net.ports}
    refs.update({r.name: r for kind, _, r, _ in net.events if r is not None})
    declared = {r.name for kind, _, r, _ in net.events if kind == "declare"}
    depths = {r.name: ("input", 0) for d, r in net.ports if d == "input"}
    nodes, outputs = [], {}
    for kind, stage, ref, payload in net.events:
        if kind == "declare":
            continue
        if kind == "output":
            outputs[ref.name] = payload.name
            continue
        args = []
        if kind == "wire":
            template = _replace(payload, refs, args)
            outs = (ref,)
        elif kind == "rom":
            values, idx, bank = payload
            args = [idx.name]
            template = ("rom", bank)
            outs = (ref,)
        elif kind == "instance":
            module, conns = payload
            outnames = [value for value in conns.values() if value in declared and value not in depths]
            outs = tuple(refs[value] for value in outnames)
            if not outs:
                raise ValueError(f"cannot classify outputs of shared SFU instance {module.name}")
            template = (module.name, tuple(sorted(module.params.items())),
                        tuple((key, f"__out{outnames.index(value)}__" if value in outnames
                               else _replace(value, refs, args)) for key, value in conns.items()))
        else:
            raise ValueError(f"unknown SFU construction event {kind}")
        inputs = tuple(refs[key] for key in args)
        node = Node(fi, kind, stage, 0, outs, inputs, template, payload)
        resource = kind in ("rom", "instance") or _arithmetic(node)
        depth = int(resource) + max((depths[key][1] for key in args if depths[key][0] == stage), default=0)
        node.depth = depth
        nodes.append(node)
        for out in outs:
            depths[out.name] = (stage, depth)
    return nodes, outputs


def _range(stage):
    return stage == "range"


def _arithmetic(node):
    return node.kind == "instance" or (node.kind == "wire" and
           bool(re.search(r"(?<!')\+|\*|(?<![0-9])-|<<|>>|\?", node.template)))


class SharedNet:
    """A multi-function net with physical sharing and a standalone replay model."""

    def __init__(self, name, nets, strategy):
        if strategy not in ("shared_evaluator", "shared_range_reduction", "fully_shared_rom_evaluator"):
            raise ValueError(f"unknown SFU sharing strategy {strategy!r}")
        if len(nets) < 2:
            raise ValueError(f"sharing={strategy} needs at least two named functions")
        ports = [[(d, r.name, r.w, r.s) for d, r in n.ports] for n in nets]
        if any(p != ports[0] for p in ports[1:]):
            raise ValueError("shared SFU functions need the same scalar or vector interface")
        self.name, self.nets, self.strategy = name, nets, strategy
        self.sw = max(1, (len(nets) - 1).bit_length())
        self.ports = list(nets[0].ports) + [("input", Ref("fn_sel", self.sw, False))]
        self.groups, self.maps, self.results = [], [], []
        self.aliases = {}
        self.pattern = all([r.name for d, r in n.ports if d == "output"] == ["y"] for n in nets)
        by_shape, by_exact = defaultdict(list), defaultdict(list)
        self.stats = {"merged_operations": 0, "merged_evaluator_operations": 0,
                      "merged_range_operations": 0, "merged_roms": 0}
        for fi, net in enumerate(nets):
            mapped = {r.name: r for d, r in net.ports if d == "input"}
            nodes, outputs = _nodes(net, fi)
            for node in nodes:
                actual = tuple(mapped[r.name] for r in node.inputs)
                exact = (node.shape, tuple((self.aliases.get(r.name, (r.name,)), r.w, r.s) for r in actual),
                         tuple(node.payload[0]) if node.kind == "rom" else None)
                eligible = ((strategy == "shared_range_reduction" and _range(node.stage)) or
                            (strategy == "shared_evaluator" and node.stage.startswith("evaluator")) or
                            strategy == "fully_shared_rom_evaluator")
                # The range-reduction strategy shares identical computations;
                # evaluators select their operands before compatible resources.
                candidate = next((g for g in by_exact[exact]
                                  if all(row.fi != fi for row in g.rows)), None) if eligible else None
                shape = node.shape
                promote = (node.kind == "wire" and _arithmetic(node)) or (
                    node.kind == "rom" and (strategy == "fully_shared_rom_evaluator" or self.pattern))
                if eligible and strategy != "shared_range_reduction" and promote:
                    # Promote compatible resources to their widest consumer.
                    # Per-function aliases restore each original truncation.
                    shape = (node.kind, node.stage, node.depth, tuple(r.s for r in node.outputs),
                             tuple(r.s for r in node.inputs), node.template)
                if candidate is None and eligible and strategy != "shared_range_reduction" and (
                        node.kind == "instance" or (node.kind == "wire" and _arithmetic(node)) or
                        (node.kind == "rom" and (strategy == "fully_shared_rom_evaluator" or self.pattern))):
                    candidate = next((g for g in by_shape[shape]
                                      if all(row.fi != fi for row in g.rows)), None)
                if candidate is None:
                    candidate = Group(len(self.groups))
                    self.groups.append(candidate)
                    by_shape[shape].append(candidate)
                else:
                    self.stats["merged_operations"] += 1
                    if node.kind == "rom":
                        self.stats["merged_roms"] += 1
                    if _arithmetic(node):
                        if node.stage.startswith("evaluator"):
                            self.stats["merged_evaluator_operations"] += 1
                        if _range(node.stage):
                            self.stats["merged_range_operations"] += 1
                candidate.rows.append(node)
                candidate.inputs.append(actual)
                if candidate not in by_exact[exact]:
                    by_exact[exact].append(candidate)
                for oi, before in enumerate(node.outputs):
                    alias = Ref(f"shared_f{fi}_{before.name}", before.w, before.s)
                    self.aliases[alias.name] = (candidate.index, oi)
                    mapped[before.name] = alias
            self.maps.append(mapped)
            self.results.append({key: mapped[value] for key, value in outputs.items()})
        criterion = {"shared_evaluator": "merged_evaluator_operations",
                     "shared_range_reduction": "merged_range_operations",
                     "fully_shared_rom_evaluator": "merged_roms"}[strategy]
        if strategy == "shared_evaluator" and self.pattern:
            criterion = "merged_roms"
        if strategy == "fully_shared_rom_evaluator" and not any(kind == "rom" for n in nets for kind, *_ in n.events):
            criterion = "merged_evaluator_operations"
        if self.stats[criterion] == 0:
            raise ValueError(f"sharing={strategy} has no compatible active resources for these functions; "
                             "choose a target whose functions exercise the selected sharing")
        self._order()
        bank_groups = defaultdict(set)
        for group in self.groups:
            if group.rows[0].kind != "rom":
                continue
            members = tuple((row.fi, row.payload[2]) for row in group.rows)
            for row in group.rows:
                if row.payload[2] is not None:
                    bank_groups[(row.fi, row.payload[2])].add(members)
        if any(len(sets) > 1 for sets in bank_groups.values()):
            raise ValueError("requested SFU sharing cannot preserve the selected multiport table banks for these functions")

    def _order(self):
        owners = {r.name: g.index for g in self.groups for r in g.outputs}
        owners.update({name: position[0] for name, position in self.aliases.items()})
        done, active, ordered = set(), set(), []
        def visit(g):
            if g.index in active:
                raise ValueError("SFU resource sharing would create a combinational cycle")
            if g.index in done:
                return
            active.add(g.index)
            for row in g.inputs:
                for r in row:
                    if r.name in owners:
                        visit(self.groups[owners[r.name]])
            active.remove(g.index)
            done.add(g.index)
            ordered.append(g)
        for g in self.groups:
            visit(g)
        self.ordered = ordered

    def run(self, inputs):
        fi = int(inputs["fn_sel"])
        if fi >= len(self.nets):
            return {r.name: 0 for d, r in self.ports if d == "output"}
        return self.nets[fi].run({k: v for k, v in inputs.items() if k != "fn_sel"})

    def _select(self, rows, default="'0"):
        if len(rows) == 1:
            return rows[0][1]
        expr = default
        for fi, value in reversed(rows):
            expr = f"(fn_sel == {self.sw}'d{fi}) ? {value} : ({expr})"
        return expr

    def render(self):
        from chialu.targets.rtl.families.mul import dedupe_modules
        def decl(r):
            return ("signed " if r.s else "") + (f"[{r.w-1}:0] " if r.w > 1 else "") + r.name
        L = [f"// SFU sharing={self.strategy}: " + ", ".join(f"{k}={v}" for k, v in self.stats.items()),
             f"module {self.name} (", ",\n".join(f"  {d} logic {decl(r)}" for d, r in self.ports), ");"]
        memories = {}
        for group in self.ordered:
            node = group.rows[0]
            names = []
            for ai, ref in enumerate(node.inputs):
                width = max(row.inputs[ai].w for row in group.rows)
                values = []
                for row, refs in zip(group.rows, group.inputs):
                    value = refs[ai]
                    expr = value.name
                    if value.w < width:
                        fill = f"{expr}[{value.w-1}]" if value.s and value.w > 1 else expr if value.s else "1'b0"
                        expr = f"{{{{{width-value.w}{{{fill}}}}}, {expr}}}"
                    values.append((row.fi, expr))
                if all(value == values[0][1] for _, value in values):
                    names.append(values[0][1])
                else:
                    name = f"shared_i{group.index}_{ai}"
                    L.append(f"  logic {decl(Ref(name, width, ref.s))}; assign {name} = {self._select(values)};")
                    names.append(name)
            outs = group.outputs
            for out in outs:
                L.append(f"  logic {decl(out)};")
            def subst(expr):
                for i, value in enumerate(names):
                    expr = expr.replace(f"__arg{i}__", value)
                for i, out in enumerate(outs):
                    expr = expr.replace(f"__out{i}__", out.name)
                return expr
            if node.kind == "wire":
                L.append(f"  assign {outs[0].name} = {subst(node.template)};")
            elif node.kind == "instance":
                module, params, conns = node.template
                ps = " #(" + ", ".join(f".{k}({v})" for k, v in params) + ")" if params else ""
                L.append(f"  {module}{ps} u_shared{group.index} (" + ", ".join(f".{k}({subst(v)})" for k, v in conns) + ");")
            else:
                out = outs[0]
                stride = 1 << max(row.inputs[0].w for row in group.rows)
                merged = len(group.rows) > 1
                size = stride * (1 << self.sw) if merged else len(node.payload[0])
                table = [0] * size
                for row in group.rows:
                    offset = row.fi * stride if merged else 0
                    table[offset:offset + len(row.payload[0])] = row.payload[0]
                bank = tuple((row.fi, row.payload[2]) for row in group.rows) if node.payload[2] is not None else (group.index,)
                mem = memories.get(bank)
                if mem is None:
                    mem = f"shared_t{group.index}"
                    memories[bank] = mem
                    L.append(f"  logic [{out.w-1}:0] {mem} [0:{size-1}];")
                    L.append("  initial begin " + " ".join(f"{mem}[{i}]={out.w}'d{value & ((1 << out.w)-1)};"
                                                           for i, value in enumerate(table)) + " end")
                addr = "{fn_sel, " + names[0] + "}" if merged else names[0]
                rd = f"{mem}[{addr}]"
                if not merged and size < stride:
                    rd = f"({names[0]} < {size}) ? {rd} : {out.w}'d0"
                if out.s:
                    rd = f"$signed({rd})"
                L.append(f"  assign {out.name} = {rd};")
            for row in group.rows:
                for oi, original in enumerate(row.outputs):
                    alias = Ref(f"shared_f{row.fi}_{original.name}", original.w, original.s)
                    L.append(f"  logic {decl(alias)}; assign {alias.name} = {outs[oi].name};")
        for direction, out in self.ports:
            if direction == "output":
                L.append(f"  assign {out.name} = {self._select([(fi, row[out.name].name) for fi, row in enumerate(self.results)])};")
        L.append("endmodule")
        extra = dedupe_modules("\n".join(text for n in self.nets for text in n.extra))
        return "\n".join(L) + "\n" + extra
