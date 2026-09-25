"""Variables and their binding times (design section 3).

A variable is a named quantity of a template with a domain, the binding
times it admits (`fixed`, `search`, `runtime`), an optional condition on
a parent variable, an optional condition per member on a sibling
variable, and an optional index set. `bind_variables` resolves a yaml
`variables:` block against the expanded variable list, and `space_json`
exports the bound feature model."""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field, replace
from typing import Any, Optional

from .domains import Domain, Enum, Set
from .errors import BindError

BINDING_TIMES = ("fixed", "search", "runtime")


class _Sentinel:
    def __init__(self, name):
        self.name = name

    def __repr__(self):
        return self.name


OPEN = _Sentinel("OPEN")        # a searched variable whose value nothing has decided yet
ABSENT = _Sentinel("ABSENT")    # a variable that is inactive here or does not exist


@dataclass
class Variable:
    name: str
    domain: Domain
    binding_times: frozenset = frozenset({"fixed"})
    when: Optional[tuple] = None          # (parent, member) or (parent, [members])
    indexed_by: Optional[str] = None      # an index set the elaboration provides
    requires: Optional[dict] = None       # member -> [requirement names]
    doc: str = ""
    template_name: Optional[str] = None   # the name with `*`, for an expanded member
    index: Optional[str] = None           # the index value of an expanded member
    index_domains: Optional[dict] = None  # index -> the domain of that index's member, where it differs
    search_domain: Optional[Domain] = None  # the domain a `search` binding narrows within, where narrower
    member_when: Optional[dict] = None    # member -> (sibling, allowed members[, doc]): the member is admissible
                                          # while the sibling holds one of them (design section 3.4)
    inactive_when: tuple = ()             # OR of AND clauses: ((sibling, members), ...)

    def __post_init__(self):
        self.binding_times = frozenset(self.binding_times)
        bad = self.binding_times - set(BINDING_TIMES)
        if bad or not self.binding_times:
            raise BindError(self.name, f"binding times {sorted(self.binding_times)} "
                                       f"(admitted: {BINDING_TIMES})")
        if "*" in self.name and not self.indexed_by:
            raise BindError(self.name, "a `*` in the name needs indexed_by")
        if self.index_domains and not self.indexed_by:
            raise BindError(self.name, "index_domains need indexed_by")
        if self.when is not None:
            parent, members = self.when
            if not isinstance(members, (list, tuple)):
                members = (members,)
            self.when = (parent, tuple(members))
        clauses = []
        for clause in self.inactive_when:
            if not clause:
                raise BindError(self.name, 'inactive_when needs nonempty clauses')
            tests = []
            for cond in clause:
                if not isinstance(cond, (tuple, list)) or len(cond) != 2 or not isinstance(cond[0], str):
                    raise BindError(self.name, 'inactive_when tests are (sibling, allowed members)')
                sibling, allowed = cond
                allowed = tuple(allowed) if isinstance(allowed, (tuple, list)) else (allowed,)
                if not allowed or sibling == self.name:
                    raise BindError(self.name, 'inactive_when needs a distinct sibling and nonempty members')
                tests.append((sibling, allowed))
            clauses.append(tuple(tests))
        self.inactive_when = tuple(clauses)
        if self.member_when:
            norm = {}
            for m, cond in self.member_when.items():
                if not isinstance(cond, (list, tuple)) or len(cond) not in (2, 3) or not isinstance(cond[0], str):
                    raise BindError(self.name, f"member_when[{m!r}]: (sibling variable, allowed members[, doc])")
                allowed = cond[1] if isinstance(cond[1], (list, tuple)) else (cond[1],)
                if not allowed:
                    raise BindError(self.name, f"member_when[{m!r}]: no allowed member of {cond[0]}")
                if not self.domain.contains(m):
                    raise BindError(self.name, f"member_when names {m!r}, which is outside {self.domain.describe()}")
                norm[m] = (cond[0], tuple(allowed), str(cond[2]) if len(cond) == 3 and cond[2] else "")
            self.member_when = norm
            for dom in [self.domain] + list((self.index_domains or {}).values()):
                # Disjoint family domains can condition every member while
                # still covering every value that opens this variable.
                covered = False
                if self.when is not None and dom.finite():
                    covered = all(
                        any(m == candidate and cond[0] == self.when[0] and parent in cond[1]
                            for m in dom.members() for candidate, cond in norm.items())
                        for parent in self.when[1])
                if dom.finite() and not covered and all(any(m == c for c in norm) for m in dom.members()):
                    raise BindError(self.name, f"every member of {dom.describe()} carries a member condition; "
                                               f"a condition on the variable's existence is `when`")

    @property
    def parent(self):
        return self.when[0] if self.when else None

    @property
    def siblings(self) -> list:
        """The variables the member conditions name, in member order."""
        out = []
        for sib, _allowed, _doc in (self.member_when or {}).values():
            if sib not in out:
                out.append(sib)
        for clause in self.inactive_when:
            for sib, _allowed in clause:
                if sib not in out:
                    out.append(sib)
        return out

    def inactive(self, lookup) -> bool:
        """Whether a complete inactivity clause holds under this assignment."""
        def holds(name, allowed):
            time, value = lookup(name)
            if time == 'absent' or value is ABSENT or value is OPEN:
                return False
            return all(_in(allowed, x) for x in value) if time == 'runtime' else _in(allowed, value)
        return any(all(holds(name, allowed) for name, allowed in clause) for clause in self.inactive_when)

    @property
    def searchable(self) -> Domain:
        """The domain a `search` binding narrows within: `search_domain`
        where the elaboration set one, else the domain itself."""
        return self.search_domain if self.search_domain is not None else self.domain

    def expand(self, index_values) -> list:
        """One variable per index value, `*` replaced in the name, in the
        condition's parent and in the member conditions' siblings; an
        index with a domain of its own in `index_domains` takes it."""
        if not self.indexed_by:
            return [self]
        out = []
        for ix in index_values:
            when = None
            if self.when:
                parent, members = self.when
                when = (parent.replace("*", str(ix)), members)
            member_when = None
            if self.member_when:
                member_when = {m: (sib.replace("*", str(ix)), allowed, doc)
                               for m, (sib, allowed, doc) in self.member_when.items()}
            domain = (self.index_domains or {}).get(str(ix), self.domain)
            out.append(replace(self, name=self.name.replace("*", str(ix)), domain=domain,
                               when=when, indexed_by=None, index_domains=None, template_name=self.name,
                               index=str(ix), member_when=member_when,
                               inactive_when=tuple(tuple((sib.replace('*', str(ix)), allowed)
                                                         for sib, allowed in clause) for clause in self.inactive_when)))
        return out

    def condition_holds(self, parent_value) -> bool:
        if self.when is None:
            return True
        return any(parent_value == m for m in self.when[1])


def _in(values, v) -> bool:
    return any(v == x for x in values)


def _pick(mapping: dict, v):
    """The entry of `mapping` whose key equals `v`, or None (a member may
    be unhashable)."""
    for k, x in mapping.items():
        if k == v:
            return x
    return None


def member_exclusions(var: Variable, domain, lookup) -> dict:
    """{member: reason} for the members of `domain` (the variable's own
    when None) that the member conditions exclude under the siblings'
    states. `lookup(name)` reports a sibling as `(time, value)`: a
    `fixed` value, the `runtime` members (every one must be allowed), a
    `search` value that is decided or OPEN (undecided: the member stays
    admissible), or `absent` (inactive or nonexistent: the member is
    inadmissible, as a child of an absent parent is inactive)."""
    out = {}
    dom = var.domain if domain is None else domain
    for m, (sib, allowed, doc) in (var.member_when or {}).items():
        if not dom.contains(m):
            continue
        time, value = lookup(sib)
        if time == "search" and value is OPEN:
            continue
        if time == "search" and value is ABSENT:
            time = "absent"
        if time == "absent":
            why = f"{sib} does not exist here"
        elif time == "runtime":
            if all(_in(allowed, x) for x in value):
                continue
            why = f"{sib} is selected at run time among {list(value)!r}"
        else:
            if _in(allowed, value):
                continue
            why = f"it is {value!r}"
        out[m] = f"{m!r} is admissible when {sib} is one of {list(allowed)!r}; {why}" + (f" ({doc})" if doc else "")
    return out


def admissible_members(var: Variable, domain, lookup) -> list:
    """The members of `domain` in its order, less the ones the member
    conditions exclude; every member of a domain that is not finite."""
    dom = var.domain if domain is None else domain
    if not dom.finite():
        return []
    excl = member_exclusions(var, dom, lookup) if var.member_when else {}
    return [m for m in dom.members() if not excl or _pick(excl, m) is None]


def default_under(var: Variable, domain, lookup):
    """The default of `domain` under the siblings' states: the first
    admissible member; the domain's own default without conditions."""
    dom = var.domain if domain is None else domain
    if not var.member_when or not dom.finite():
        return dom.default()
    members = admissible_members(var, dom, lookup)
    return members[0] if members else None


def binding_lookup(bindings, decided=None):
    """A `lookup` over bindings for `member_exclusions`: the sibling's
    binding gives the state, and `decided(name)` gives a searched
    sibling's value, OPEN or ABSENT (OPEN without `decided`)."""
    def lookup(name):
        b = bindings.get(name) if bindings is not None else None
        if b is None:
            return ("absent", None)
        if b.time == "fixed":
            return ("fixed", b.value)
        if b.time == "runtime":
            return ("runtime", list(b.members))
        return ("search", decided(name) if decided is not None else OPEN)
    return lookup


def _check_fixed_members(var: Variable, time: str, values: list, bindings, path: str):
    """A fixed value or a provisioned member the member conditions
    exclude under the bound siblings is an error naming the condition."""
    if not var.member_when:
        return
    excl = member_exclusions(var, var.domain, binding_lookup(bindings))
    bad = [why for v in values for why in [_pick(excl, v)] if why]
    if bad:
        raise BindError(path, f"{time}: " + "; ".join(bad))


@dataclass
class Binding:
    variable: Variable
    time: str
    value: Any = None            # fixed: one member
    domain: Optional[Domain] = None   # search: the narrowed domain
    members: Optional[list] = None    # runtime: the provisioned set
    spec_path: str = ""

    @property
    def name(self):
        return self.variable.name

    def to_json(self) -> dict:
        d = {"time": self.time}
        if self.time == "fixed":
            d["value"] = self.value
        elif self.time == "search":
            d["domain"] = self.domain.to_json()
        else:
            d["members"] = list(self.members)
        return d

    def possible_values(self) -> list:
        """Every value the variable may take under this binding (for
        activity of children and for disclosure)."""
        if self.time == "fixed":
            return [self.value]
        if self.time == "runtime":
            return list(self.members)
        return self.domain.members() if self.domain.finite() else []


def parse_spec(name: str, spec, path: str):
    if not isinstance(spec, dict) or len(spec) != 1:
        raise BindError(path, f"{name}: one of fixed | search | runtime | preset "
                              f"(got {spec!r})")
    (key, payload), = spec.items()
    if key not in BINDING_TIMES + ("preset",):
        raise BindError(path, f"{name}: unknown key {key!r} (fixed | search | runtime | preset)")
    return key, payload


def _topological(variables: list) -> list:
    """Parents before children, and the siblings of a member condition
    before the variable they condition."""
    by_name = {v.name: v for v in variables}
    out, seen, stack = [], set(), set()

    def visit(v):
        if v.name in seen:
            return
        if v.name in stack:
            raise BindError(v.name, "a cycle of conditions")
        stack.add(v.name)
        for before in ([v.parent] if v.parent else []) + v.siblings:
            if before in by_name:
                visit(by_name[before])
        stack.discard(v.name)
        seen.add(v.name)
        out.append(v)

    for v in variables:
        visit(v)
    return out


def expand_presets(specs: dict, presets: dict, path: str) -> dict:
    """A mapping with a `preset` key at a path prefix expands to its
    fixed bindings; a conflict with an explicit binding is an error."""
    out = {}
    for name, spec in specs.items():
        if isinstance(spec, dict) and set(spec) == {"preset"}:
            pname = spec["preset"]
            preset = presets.get(pname)
            if preset is None:
                raise BindError(f"{path}.{name}", f"unknown preset {pname!r} "
                                                  f"(registered: {sorted(presets)})")
            if preset.path and preset.path != name:
                raise BindError(f"{path}.{name}", f"preset {pname!r} applies at "
                                                  f"{preset.path!r}")
            for k, v in preset.bindings.items():
                full = f"{name}.{k}" if name else k
                if full in specs:
                    raise BindError(f"{path}.{full}", f"bound by preset {pname!r} and explicitly")
                out[full] = {"fixed": v}
        else:
            out[name] = spec
    return out


def spec_rank(spec_name: str, var: Variable):
    """How a spec name matches a variable, or None. A `*` in a spec
    stands for the index of an indexed variable (`core.adder.*.family`,
    `core.adder.m1.*.family`); a trailing `*` matches every variable
    below the prefix (`core.*`). Lower ranks are more specific: (0) the
    exact name, (1) an index pattern, (2) a trailing-star prefix; the
    longer spec wins within a rank."""
    if spec_name == var.name:
        return (0, -len(spec_name))
    if "*" not in spec_name:
        return None
    if var.template_name and "*" in var.template_name:
        prefix, suffix = var.template_name.split("*", 1)
        if spec_name.startswith(prefix) and spec_name.endswith(suffix) \
                and len(spec_name) >= len(prefix) + len(suffix):
            middle = spec_name[len(prefix):len(spec_name) - len(suffix)]
            if middle and fnmatch.fnmatchcase(var.index or "", middle):
                return (1, -len(spec_name))
    if spec_name.endswith("*") and fnmatch.fnmatchcase(var.name, spec_name):
        return (2, -len(spec_name))
    return None


def bind_variables(variables: list, specs: dict, path: str = "variables") -> dict:
    """Bindings for every active variable. Precedence: an exact name,
    then an index pattern, then a trailing-star prefix (`spec_rank`). An
    unbound active variable, a binding time the variable does not admit,
    a value outside the domain, a one-member `runtime` list, a binding on
    an inactive child of a `fixed` parent and an unknown name are
    errors."""
    used = set()
    bindings: dict = {}
    for var in _topological(variables):
        # activity under the parent's binding
        if var.when is not None:
            pb = bindings.get(var.parent)
            if pb is None:
                active = False
            elif pb.time == "fixed":
                active = var.condition_holds(pb.value)
            elif pb.time == "runtime":
                active = any(var.condition_holds(m) for m in pb.members)
            else:
                active = True
        else:
            active = True
        ranked = [(r, k) for k in specs if (r := spec_rank(k, var)) is not None]
        rank, spec_name = min(ranked) if ranked else (None, None)
        if spec_name is None:
            if active:
                raise BindError(f"{path}.{var.name}", "unbound (the loader has no defaults)")
            continue
        used.add(spec_name)
        if not active and rank[0] != 0:
            continue                       # a pattern also covers inactive variables; only an exact name is an error
        if not active:
            raise BindError(f"{path}.{var.name}",
                            f"bound, but inactive under {var.parent} = "
                            f"{bindings[var.parent].value!r}" if var.parent in bindings
                            else f"bound, but its parent {var.parent} is not bound")
        spec = specs[spec_name]
        p = f"{path}.{spec_name}"
        time, payload = parse_spec(var.name, spec, p)
        if time == "preset":
            raise BindError(p, "a preset applies at a path prefix, not on a variable")
        if time not in var.binding_times:
            raise BindError(p, f"{time} is not admitted (admitted: "
                               f"{sorted(var.binding_times)})")
        if time == "fixed":
            payload = fixed_payload(var, payload, bindings, p)
            if not var.domain.contains(payload):
                raise BindError(p, f"fixed: {payload!r} outside {var.domain.describe()}"
                                   f"{var.domain.outside_detail([payload])}")
            _check_fixed_members(var, "fixed", [payload], bindings, p)
            bindings[var.name] = Binding(var, "fixed", value=payload, spec_path=p)
        elif time == "search":
            dom = var.searchable.narrow(payload, p)
            bindings[var.name] = Binding(var, "search", domain=dom, spec_path=p)
        else:
            base = var.domain.base if isinstance(var.domain, Set) else var.domain
            if payload == "all":
                if not base.finite():
                    raise BindError(p, f"runtime: all over {base.describe()} is not finite")
                members = base.members()
            elif isinstance(payload, (list, tuple)):
                members = list(payload)
                bad = [m for m in members if not base.contains(m)]
                if bad:
                    raise BindError(p, f"runtime: {bad!r} outside {base.describe()}{base.outside_detail(bad)}")
            else:
                raise BindError(p, f"runtime: a list of members or `all` (got {payload!r})")
            if len(members) < 2:
                raise BindError(p, "runtime: one member; write fixed with that member")
            _check_fixed_members(var, "runtime", members, bindings, p)
            bindings[var.name] = Binding(var, "runtime", members=members, spec_path=p)
    unknown = set(specs) - used
    if unknown:
        raise BindError(path, f"unknown variables {sorted(unknown)} "
                              f"(known: {sorted(v.name for v in variables)[:20]}...)")
    return bindings


def bind_one(var: Variable, specs: dict, bindings: dict, path: str = "variables",
             exact_required: bool = False):
    """The binding of one expanded variable under `specs`, its parent's
    binding already in `bindings`: the spec of the best rank, or None
    when no spec names it (an error only when `exact_required`). A
    variable inactive under a fixed or runtime parent binds to nothing;
    under a search parent every child may become active, so it binds."""
    if var.when is not None:
        pb = bindings.get(var.parent) if hasattr(bindings, "get") else None
        if pb is None:
            active = False
        elif pb.time == "fixed":
            active = var.condition_holds(pb.value)
        elif pb.time == "runtime":
            active = any(var.condition_holds(m) for m in pb.members)
        else:
            active = True
    else:
        active = True
    ranked = [(r, k) for k in specs if (r := spec_rank(k, var)) is not None]
    rank, spec_name = min(ranked) if ranked else (None, None)
    if spec_name is None:
        if active and exact_required:
            raise BindError(f"{path}.{var.name}", "unbound (the loader has no defaults)")
        return None
    if not active:
        if rank[0] != 0:
            return None                    # a pattern also covers inactive variables
        raise BindError(f"{path}.{var.name}",
                        f"bound, but inactive under {var.parent} = {bindings[var.parent].value!r}"
                        if var.parent in bindings else f"bound, but its parent {var.parent} is not bound")
    spec = specs[spec_name]
    p = f"{path}.{spec_name}"
    time, payload = parse_spec(var.name, spec, p)
    if time == "preset":
        raise BindError(p, "a preset applies at a path prefix, not on a variable")
    if time not in var.binding_times:
        raise BindError(p, f"{time} is not admitted (admitted: {sorted(var.binding_times)})")
    if time == "fixed":
        payload = fixed_payload(var, payload, bindings, p)
        if not var.domain.contains(payload):
            raise BindError(p, f"fixed: {payload!r} outside {var.domain.describe()}"
                               f"{var.domain.outside_detail([payload])}")
        _check_fixed_members(var, "fixed", [payload], bindings, p)
        return Binding(var, "fixed", value=payload, spec_path=p)
    if time == "search":
        return Binding(var, "search", domain=var.searchable.narrow(payload, p), spec_path=p)
    base = var.domain.base if isinstance(var.domain, Set) else var.domain
    if payload == "all":
        if not base.finite():
            raise BindError(p, f"runtime: all over {base.describe()} is not finite")
        members = base.members()
    elif isinstance(payload, (list, tuple)):
        members = list(payload)
        bad = [m for m in members if not base.contains(m)]
        if bad:
            raise BindError(p, f"runtime: {bad!r} outside {base.describe()}{base.outside_detail(bad)}")
    else:
        raise BindError(p, f"runtime: a list of members or `all` (got {payload!r})")
    if len(members) < 2:
        raise BindError(p, "runtime: one member; write fixed with that member")
    _check_fixed_members(var, "runtime", members, bindings, p)
    return Binding(var, "runtime", members=members, spec_path=p)


DEFAULT = "@default"


def fixed_payload(var: Variable, payload, bindings, path: str):
    """`fixed: "@default"` fixes a variable at the value its template gives it by default (under the member
    conditions of its fixed siblings), so a pattern such as `core.*` can close every decision of a unit at the
    seed's own choices without naming them: a run with nothing to declare."""
    if payload != DEFAULT:
        return payload
    v = default_under(var, var.domain, binding_lookup(bindings if hasattr(bindings, "get") else None))
    if v is None:
        raise BindError(path, f"fixed: {DEFAULT}: {var.name} has no admissible default")
    return v


def default_view(b: Binding):
    """The value a binding stands at in the seed's view: the fixed value,
    the search domain's default, or None for a runtime set (a child is
    active under any member). A binding whose variable carries member
    conditions takes its default through `Bindings.default_of`, which
    knows the siblings."""
    if b.time == "fixed":
        return b.value
    if b.time == "search":
        return b.domain.default()
    return None


class VariableTree:
    """The template variables of an instance, static and indexed (with
    `*` in the name), with the index sets and the run file's specs: the
    source a lazy `Bindings` materializes from (design section 3.7)."""

    def __init__(self, templates: list, index_sets: dict, specs: dict, path: str = "variables"):
        self.templates = list(templates)
        self.index_sets = {k: [str(i) for i in v] for k, v in index_sets.items()}
        self.specs = specs
        self.path = path
        self.by_name = {v.name: v for v in self.templates}
        self.children: dict = {}
        for v in self.templates:
            if v.when is not None:
                self.children.setdefault(v.when[0], []).append(v)
        # the prefixes before `*` and the index values that may follow each: a
        # name resolves by its prefix and index, then by the template's own name
        self._prefixes: dict = {}
        for v in self.templates:
            if "*" in v.name:
                prefix = v.name.split("*", 1)[0]
                ixs = self._prefixes.setdefault(prefix, set())
                ixs.update(self.index_sets.get(v.indexed_by, ()))
        self._prefix_list = sorted(((p, sorted(ixs, key=len, reverse=True)) for p, ixs in self._prefixes.items()),
                                   key=lambda t: -len(t[0]))
        for v in self.templates:
            if v.indexed_by and v.indexed_by not in self.index_sets:
                raise BindError(f"{path}.{v.name}", f"indexed_by {v.indexed_by!r} is not an index set the "
                                                     f"elaboration provides (has: {sorted(self.index_sets)})")
            for sib in v.siblings:
                if sib not in self.by_name:
                    raise BindError(f"{path}.{v.name}", f"a member condition names {sib!r}, which is not a variable "
                                                         f"of the template")
                if "*" in sib and not v.indexed_by:
                    raise BindError(f"{path}.{v.name}", f"a member condition of a static variable names the indexed "
                                                         f"{sib!r}; the index has no value here")
        _topological(self.templates)          # a cycle of conditions is rejected at load

    def resolve(self, name: str):
        """The expanded variable a name denotes, or None: a static
        template by its name, an indexed one by the prefix, the index
        and the suffix of the name."""
        v = self.by_name.get(name)
        if v is not None and "*" not in v.name:
            return v
        for prefix, ixs in self._prefix_list:
            if not name.startswith(prefix):
                continue
            rest = name[len(prefix):]
            for ix in ixs:
                if rest.startswith(ix) and len(rest) > len(ix):
                    t = self.by_name.get(prefix + "*" + rest[len(ix):])
                    if t is not None and ix in self.index_sets.get(t.indexed_by, ()):
                        return t.expand([ix])[0]
        return None

    def children_of(self, name: str) -> list:
        """The expanded variables conditioned on the variable `name`
        (whatever the value); an indexed child of a static parent expands
        over its whole index set."""
        v = self.resolve(name)
        if v is None:
            return []
        out = []
        for t in self.children.get(v.template_name or v.name, []):
            if not t.indexed_by:
                out.append(t)
            elif v.index is not None:
                # the child at the parent's index, where the child's own index set holds it: two slots
                # indexed over different sets (a mode's multiply-add organization over every float mode,
                # its adder over the modes that add) share the index names, not the sets
                if v.index in self.index_sets.get(t.indexed_by, ()):
                    out.append(t.expand([v.index])[0])
            else:
                out += t.expand(self.index_sets.get(t.indexed_by, []))
        return out

    def roots(self) -> list:
        """The expanded variables without a condition."""
        out = []
        for t in self.templates:
            if t.when is None:
                out += t.expand(self.index_sets.get(t.indexed_by, [])) if t.indexed_by else [t]
        return out

    def matches_any(self, spec_name: str) -> bool:
        """Whether a spec names or covers some variable of the tree."""
        if self.resolve(spec_name) is not None:
            return True
        if "*" not in spec_name:
            return False
        for t in self.templates:
            if t.name == spec_name or fnmatch.fnmatchcase(t.name, spec_name):
                return True
            if t.indexed_by:
                for ix in self.index_sets.get(t.indexed_by, ()):
                    if spec_rank(spec_name, t.expand([ix])[0]) is not None:
                        return True
        return False

    def expand_all(self) -> list:
        """Every expanded variable, parents before children (the numeric
        backends' space)."""
        out = []
        for t in self.templates:
            out += t.expand(self.index_sets.get(t.indexed_by, [])) if t.indexed_by else [t]
        return _topological(out)


class Bindings(dict):
    """The bindings of an instance, materialized lazily from a
    VariableTree: the variables active under the defaults (a search
    parent at its domain's default) are bound at load, and any other
    variable of the tree is bound when named, its parents first. The
    dict holds the materialized ones."""

    def __init__(self, tree: VariableTree):
        super().__init__()
        self.tree = tree

    def materialize(self, name: str):
        if dict.__contains__(self, name):
            return dict.__getitem__(self, name)
        var = self.tree.resolve(name)
        if var is None:
            return None
        if var.when is not None:
            self.materialize(var.when[0])
        for sib in var.siblings:
            self.materialize(sib)
        b = bind_one(var, self.tree.specs, self, self.tree.path)
        if b is not None:
            dict.__setitem__(self, name, b)
        return b

    def __missing__(self, name):
        b = self.materialize(name)
        if b is None:
            raise KeyError(name)
        return b

    def get(self, name, default=None):
        b = self.materialize(name)
        return default if b is None else b

    def __contains__(self, name):
        return self.materialize(name) is not None

    def activate(self, values: dict):
        """Materialize every variable active under the given values (a
        declaration block): the children of each named variable that its
        value admits, recursively, the unnamed ones at their default
        view."""
        for name, value in list(values.items()):
            self.materialize(name)
            self._descend(name, value, values)

    def _descend(self, name: str, value, values: dict):
        for child in self.tree.children_of(name):
            if not child.condition_holds(value):
                continue
            b = self.materialize(child.name)
            if b is None:
                continue
            v = values[child.name] if child.name in values else self.default_of(child.name, values)
            if v is None:            # a runtime child: every member's children may be active
                for m in b.members:
                    self._descend(child.name, m, values)
            else:
                self._descend(child.name, v, values)

    def default_of(self, name: str, values: Optional[dict] = None):
        """The value a materialized variable stands at under `values` (a
        declaration's): the declared value, a fixed value, None for a
        runtime set, else the first member of the search domain that the
        member conditions admit, the siblings decided by the same rule."""
        b = self.materialize(name)
        if b is None:
            return None
        if values and name in values:
            return values[name]
        if b.time != "search":
            return default_view(b)
        if not b.variable.member_when:
            return b.domain.default()
        return default_under(b.variable, b.domain,
                             binding_lookup(self, lambda n: self.default_of(n, values)))

    def bind_defaults(self):
        """The load-time pass: the roots, then the children active under
        each binding's default view; an exact-name spec is materialized
        whatever the defaults."""
        for var in self.tree.roots():
            b = self.materialize(var.name)
            if b is None:
                raise BindError(f"{self.tree.path}.{var.name}", "unbound (the loader has no defaults)")
        for var in self.tree.roots():
            self._defaults_under(var.name)
        for spec_name in self.tree.specs:
            if "*" not in spec_name and self.tree.resolve(spec_name) is not None:
                var = self.tree.resolve(spec_name)
                if var.when is not None:
                    self.materialize(var.when[0])
                b = bind_one(var, self.tree.specs, self, self.tree.path, exact_required=True)
                if b is not None:
                    dict.__setitem__(self, var.name, b)
        unknown = [k for k in self.tree.specs if not self.tree.matches_any(k)]
        if unknown:
            raise BindError(self.tree.path, f"unknown variables {sorted(unknown)} "
                                            f"(known: {sorted(t.name for t in self.tree.templates)[:20]}...)")

    def _defaults_under(self, name: str):
        b = dict.get(self, name)
        if b is None:
            return
        v = self.default_of(name)
        values = b.members if v is None else [v]
        for child in self.tree.children_of(name):
            if not any(child.condition_holds(x) for x in values):
                continue
            cb = self.materialize(child.name)
            if cb is None:
                if child.when is not None and dict.__contains__(self, child.when[0]):
                    raise BindError(f"{self.tree.path}.{child.name}", "unbound (the loader has no defaults)")
                continue
            self._defaults_under(child.name)

    def variables(self) -> list:
        return [b.variable for b in self.values()]


def search_variables(bindings: dict) -> list:
    return [b.variable for b in bindings.values() if b.time == "search"]


def space_json(variables: list, bindings: dict) -> dict:
    """The bound feature model in ConfigSpace's shape, plus the binding
    time and the bound value of every variable."""
    hps, conds, forbids = [], [], []
    for var in _topological(variables):
        b = bindings.get(var.name)
        if b is None:
            continue
        dom = b.domain if b.time == "search" else var.domain
        hp = {"name": var.name, "binding_time": b.time, **dom.to_json(),
              "doc": var.doc}
        if b.time == "fixed":
            hp["value"] = b.value
        elif b.time == "runtime":
            hp["members"] = list(b.members)
        if var.requires:
            hp["requires"] = {str(k): list(v) for k, v in var.requires.items()}
        if var.inactive_when:
            hp['inactive_when'] = [[{'name': name, 'values': list(allowed)} for name, allowed in clause]
                                   for clause in var.inactive_when]
        hps.append(hp)
        if var.when:
            conds.append({"child": var.name, "parent": var.when[0],
                          "type": "IN", "values": list(var.when[1])})
        # a member condition in ConfigSpace's forbidden form: the member together with a sibling value
        # outside the allowed ones is forbidden
        for m, (sib, allowed, _doc) in (var.member_when or {}).items():
            sb = bindings.get(sib)
            if sb is None or not dom.contains(m):
                continue
            sdom = sb.domain if sb.time == "search" else sb.variable.domain
            if not sdom.finite():
                continue
            disallowed = [x for x in sdom.members() if not _in(allowed, x)]
            if disallowed:
                forbids.append({"type": "AND", "clauses": [{"name": var.name, "type": "EQUALS", "value": m},
                                                           {"name": sib, "type": "IN", "values": disallowed}]})
    return {"hyperparameters": hps, "conditions": conds, "forbiddens": forbids}
