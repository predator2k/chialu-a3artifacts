"""Family spaces: a domain library's microarchitecture vocabulary as
conditional variables (design section 3.4).

A `Space` is a set of families. A `Family` declares its design choices
(a domain each), the component slots it opens (a Space each), its
execution style, its paper handles, its mutations and its doc.
`Space.variables(prefix)` compiles the space to variables:

    <prefix>.family              enum over the family names
    <prefix>.<choice>            one per design choice, active under the
                                 families that declare it
    <prefix>.<slot>.family ...   the slot's space, active under the family
                                 that opens it

A choice name shared by several families becomes one variable whose
domain is the union of their domains.

A family carries its behavior classification: `neutral` (every member
computes the unit's contract under any bound options), `conditional`
(it does so when the named `requires` predicates hold, which the domain
library evaluates over the bound contract) or `selector` (it selects
the computed function and belongs to an approximate unit's space
alone). The empty default means unregistered; a domain library decides
what an unregistered family may enter."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .domains import Bool, Domain, Enum, Range
from .errors import BindError
from .variables import Variable

BEHAVIORS = ("neutral", "conditional", "selector")


@dataclass
class Family:
    name: str
    design_choices: dict = field(default_factory=dict)
    components: dict = field(default_factory=dict)
    execution_style: str = "feed_forward"
    papers: tuple = ()
    mutations: tuple = ()
    doc: str = ""
    algorithm_level: bool = False      # changes the algorithm model, so a pinned reference recomputes
    behavior: str = ""                 # neutral | conditional | selector; empty: unregistered
    requires: tuple = ()               # the predicate names a conditional family needs, all of them
    evidence: str = ""                 # where the neutrality under the condition is shown

    def __post_init__(self):
        # an algorithm-level family selects the computed function: it is a selector unless classified otherwise
        if self.algorithm_level and not self.behavior:
            self.behavior = "selector"
        if self.behavior and self.behavior not in BEHAVIORS:
            raise BindError(self.name, f"behavior {self.behavior!r} (one of {BEHAVIORS})")
        self.requires = tuple(self.requires or ())
        if self.requires and self.behavior != "conditional":
            raise BindError(self.name, "requires belongs to a conditional family")

    @property
    def family(self) -> str:
        return self.name


@dataclass
class Space:
    families: list
    forbidden: tuple = ()
    free_form_allowed: bool = True
    doc: str = ""

    def __post_init__(self):
        names = [f.name for f in self.families]
        if len(set(names)) != len(names):
            raise BindError("space", f"duplicate family names in {names}")

    @property
    def candidates(self):
        return self.families

    def family(self, name: str) -> Family:
        for f in self.families:
            if f.name == name:
                return f
        raise BindError("space", f"no family {name!r} (has: {[f.name for f in self.families]})")

    def variables(self, prefix: str, binding_times=("fixed", "search"),
                  indexed_by=None, when=None, depth: int = 0, max_depth=None) -> list:
        """The variables of this space under `prefix`. `when` is the
        condition the slot's family variable inherits from the family
        that opens the slot. `max_depth` stops the recursion into
        component slots: 0 gives the space's own family and choices,
        1 adds the slots they open, and so on; a deeper slot stays a
        decision of the text, described in the cards."""
        if depth > 12:
            raise BindError(prefix, "family spaces nest too deep")
        fam_name = f"{prefix}.family"
        out = [Variable(fam_name, Enum(tuple(f.name for f in self.families)),
                        binding_times, when=when, indexed_by=indexed_by,
                        doc=self.doc or f"the family of {prefix}")]
        choices: dict = {}
        for f in self.families:
            for choice, dom in f.design_choices.items():
                choices.setdefault(choice, []).append((f.name, dom))
        for choice, entries in choices.items():
            dom = _union(prefix, choice, [d for _, d in entries])
            out.append(Variable(f"{prefix}.{choice}", dom, binding_times,
                                when=(fam_name, tuple(n for n, _ in entries)),
                                indexed_by=indexed_by,
                                doc=f"{choice} of {', '.join(n for n, _ in entries)}"))
        # a slot several families open is one slot, active under any of
        # them, over the union of the sub-spaces' families
        slots: dict = {}
        for f in self.families:
            for slot, sub in f.components.items():
                entry = slots.setdefault(slot, ([], []))
                for sf in sub.families:
                    if not any(x.name == sf.name for x in entry[0]):
                        entry[0].append(sf)
                entry[1].append(f.name)
        if max_depth is not None and depth + 1 > max_depth:
            return out
        for slot, (fams, openers) in slots.items():
            sub = Space(fams)
            out += sub.variables(f"{prefix}.{slot}", binding_times, indexed_by,
                                 when=(fam_name, tuple(openers)), depth=depth + 1, max_depth=max_depth)
        return out

    def describe(self, indent: str = "  ") -> str:
        lines = []
        for f in self.families:
            lines.append(f"{indent}* {f.name}" + (f": {f.doc}" if f.doc else ""))
            for k, ch in f.design_choices.items():
                lines.append(f"{indent}    {k}: {ch.describe()}")
            if f.mutations:
                lines.append(f"{indent}    mutations: {', '.join(f.mutations)}")
            for slot, sub in f.components.items():
                lines.append(f"{indent}    {slot} ->")
                lines.append(sub.describe(indent + "      "))
        return "\n".join(lines)


def _union(prefix: str, choice: str, doms: list) -> Domain:
    first = doms[0]
    if all(d == first for d in doms):
        return first
    if all(isinstance(d, Enum) for d in doms):
        members = []
        for d in doms:
            for m in d.members_:
                if not any(m == x for x in members):
                    members.append(m)
        return Enum(tuple(members))
    if all(isinstance(d, Range) for d in doms):
        lo = min(d.lo for d in doms)
        hi = max(d.hi for d in doms)
        step = min(d.step for d in doms)
        return Range(lo, hi, step)
    if all(isinstance(d, Bool) for d in doms):
        return first
    raise BindError(f"{prefix}.{choice}", "families declare this choice with domains "
                                          "of different kinds")
